#!/usr/bin/env python3
"""
Gmail Email Notification Bot for Zulip

Watches Gmail for new emails and posts notifications to Zulip.
Filters by recipient address to route to appropriate Zulip instances.
"""

import os
import sys
import time
import base64
import logging
import argparse
from pathlib import Path
from datetime import datetime, timezone

import yaml
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import zulip

# Gmail API scope - read-only access
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class EmailNotifier:
    """Bot that watches Gmail and posts notifications to Zulip."""

    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.logger = logging.getLogger("email_notifier")
        self.gmail = self._create_gmail_client()
        self.zulip_clients = self._create_zulip_clients()
        self.processed_ids: set[str] = set()
        self.last_check_time = datetime.now(timezone.utc)

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        with open(config_path, "r") as f:
            return yaml.safe_load(f)

    def _setup_logging(self):
        """Configure logging based on config."""
        log_config = self.config.get("logging", {})
        level = getattr(logging, log_config.get("level", "INFO").upper())

        handlers = [logging.StreamHandler()]
        if log_config.get("file"):
            handlers.append(logging.FileHandler(log_config["file"]))

        logging.basicConfig(
            level=level,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            handlers=handlers,
        )

    def _create_gmail_client(self):
        """Create authenticated Gmail API client."""
        creds = None
        config_dir = Path(__file__).parent
        token_path = config_dir / "token.json"
        credentials_path = config_dir / "credentials.json"

        # Load existing token
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                self.logger.info("Refreshing Gmail credentials...")
                creds.refresh(Request())
            else:
                if not credentials_path.exists():
                    raise FileNotFoundError(
                        f"Gmail credentials not found at {credentials_path}. "
                        "Download OAuth credentials from Google Cloud Console."
                    )
                self.logger.info("Starting OAuth flow...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(credentials_path), SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save the token
            with open(token_path, "w") as token:
                token.write(creds.to_json())
            self.logger.info(f"Saved Gmail token to {token_path}")

        return build("gmail", "v1", credentials=creds)

    def _create_zulip_clients(self) -> dict:
        """Create Zulip clients for each configured target."""
        clients = {}
        for target in self.config.get("targets", []):
            name = target["name"]
            # Support environment variable references in api_key (e.g., ${ZULIP_DOLLHOUSE_API_KEY})
            api_key = target["zulip_api_key"]
            if api_key.startswith("${") and api_key.endswith("}"):
                env_var = api_key[2:-1]
                api_key = os.environ.get(env_var)
                if not api_key:
                    raise ValueError(f"Environment variable {env_var} not set")

            clients[name] = zulip.Client(
                email=target["zulip_email"],
                api_key=api_key,
                site=target["zulip_site"],
            )
            self.logger.info(f"Created Zulip client for {name} -> {target['zulip_site']}")
        return clients

    def _get_target_for_recipient(self, to_address: str) -> dict | None:
        """Find the target config for a given recipient address."""
        to_lower = to_address.lower()
        for target in self.config.get("targets", []):
            for pattern in target.get("watch_addresses", []):
                # Support wildcards like *@dollhousemcp.com
                if pattern.startswith("*@"):
                    domain = pattern[2:].lower()
                    if to_lower.endswith(f"@{domain}"):
                        return target
                elif to_lower == pattern.lower():
                    return target
        return None

    def _extract_email_info(self, msg_data: dict) -> dict:
        """Extract relevant info from Gmail message."""
        headers = msg_data.get("payload", {}).get("headers", [])

        def get_header(name: str) -> str:
            for h in headers:
                if h["name"].lower() == name.lower():
                    return h["value"]
            return ""

        # Get snippet (preview text)
        snippet = msg_data.get("snippet", "")

        # Get all recipients (To, Cc)
        to_addresses = []
        for field in ["To", "Delivered-To", "X-Original-To"]:
            value = get_header(field)
            if value:
                # Parse out just the email addresses
                import re
                emails = re.findall(r'[\w\.-]+@[\w\.-]+', value)
                to_addresses.extend(emails)

        return {
            "id": msg_data["id"],
            "from": get_header("From"),
            "to": to_addresses,
            "subject": get_header("Subject") or "(no subject)",
            "date": get_header("Date"),
            "snippet": snippet,
            "thread_id": msg_data.get("threadId"),
        }

    def _format_notification(self, email_info: dict, target: dict, matched_address: str) -> str:
        """Format email info into a Zulip message."""
        template = target.get("message_template", self.config.get("default_template"))

        if template:
            return template.format(
                from_addr=email_info["from"],
                to_addr=matched_address,
                subject=email_info["subject"],
                snippet=email_info["snippet"][:200],
                date=email_info["date"],
            )

        # Default format
        return (
            f"**New Email**\n"
            f"**To:** `{matched_address}`\n"
            f"**From:** {email_info['from']}\n"
            f"**Subject:** {email_info['subject']}\n"
            f"**Preview:** {email_info['snippet'][:200]}..."
        )

    def _post_to_zulip(self, target: dict, content: str, email_info: dict):
        """Post notification to Zulip."""
        client = self.zulip_clients.get(target["name"])
        if not client:
            self.logger.error(f"No Zulip client for target: {target['name']}")
            return

        stream = target.get("stream", "email")
        # Topic can be static or based on sender/recipient
        topic_template = target.get("topic", "notifications")
        topic = topic_template.format(
            from_addr=email_info["from"],
            subject=email_info["subject"][:50],
        )

        result = client.send_message({
            "type": "stream",
            "to": stream,
            "topic": topic,
            "content": content,
        })

        if result.get("result") != "success":
            self.logger.error(f"Failed to send to Zulip: {result}")
        else:
            self.logger.info(f"Posted to {target['name']} #{stream} > {topic}")

    def check_new_emails(self):
        """Check for new emails and process them."""
        try:
            # Query for unread emails in inbox
            query = "is:unread in:inbox"

            # Add time filter to avoid processing old emails on startup
            poll_interval = self.config.get("poll_interval_seconds", 60)

            results = self.gmail.users().messages().list(
                userId="me",
                q=query,
                maxResults=20,
            ).execute()

            messages = results.get("messages", [])

            if not messages:
                self.logger.debug("No new messages")
                return

            for msg in messages:
                msg_id = msg["id"]

                # Skip already processed
                if msg_id in self.processed_ids:
                    continue

                # Get full message
                msg_data = self.gmail.users().messages().get(
                    userId="me",
                    id=msg_id,
                    format="metadata",
                    metadataHeaders=["From", "To", "Subject", "Date", "Delivered-To", "X-Original-To"],
                ).execute()

                email_info = self._extract_email_info(msg_data)
                self.processed_ids.add(msg_id)

                # Check each recipient against targets
                notified = False
                for to_addr in email_info["to"]:
                    target = self._get_target_for_recipient(to_addr)
                    if target:
                        content = self._format_notification(email_info, target, to_addr)
                        self._post_to_zulip(target, content, email_info)
                        notified = True
                        break  # Only notify once per email

                if notified:
                    self.logger.info(f"Processed email: {email_info['subject'][:50]}")
                else:
                    self.logger.debug(f"No target for email to: {email_info['to']}")

            # Limit memory usage
            if len(self.processed_ids) > 1000:
                self.processed_ids = set(list(self.processed_ids)[-500:])

        except Exception as e:
            self.logger.error(f"Error checking emails: {e}")

    def run(self):
        """Main loop - poll Gmail and post notifications."""
        poll_interval = self.config.get("poll_interval_seconds", 60)
        self.logger.info(f"Starting Email Notifier (polling every {poll_interval}s)...")

        # List watched addresses
        for target in self.config.get("targets", []):
            self.logger.info(f"Watching {target['watch_addresses']} -> {target['name']}")

        while True:
            self.check_new_emails()
            time.sleep(poll_interval)


def main():
    parser = argparse.ArgumentParser(description="Gmail Email Notification Bot for Zulip")
    parser.add_argument(
        "-c", "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)"
    )
    parser.add_argument(
        "--auth-only",
        action="store_true",
        help="Only perform Gmail authentication, then exit"
    )
    args = parser.parse_args()

    # Find config file
    config_path = Path(args.config)
    if not config_path.is_absolute():
        script_dir = Path(__file__).parent
        config_path = script_dir / args.config

    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}")
        sys.exit(1)

    bot = EmailNotifier(str(config_path))

    if args.auth_only:
        print("Gmail authentication successful!")
        sys.exit(0)

    bot.run()


if __name__ == "__main__":
    main()
