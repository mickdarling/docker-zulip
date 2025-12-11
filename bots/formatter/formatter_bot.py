#!/usr/bin/env python3
"""
Zulip Formatter Bot

Watches source streams and reposts formatted versions based on configurable rules.
Useful for transforming verbose webhook output into clean, emoji-rich notifications.
"""

import os
import re
import sys
import time
import logging
import argparse
from typing import Optional
from pathlib import Path

import yaml
import zulip


class FormatterBot:
    """Bot that watches streams and reposts formatted messages."""

    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.client = self._create_client()
        self.processed_ids: set[int] = set()  # Track processed message IDs
        self.logger = logging.getLogger("formatter_bot")

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

    def _create_client(self) -> zulip.Client:
        """Create Zulip client from config or environment."""
        zulip_config = self.config.get("zulip", {})

        # Environment variables take precedence
        email = os.environ.get("ZULIP_EMAIL", zulip_config.get("email"))
        api_key = os.environ.get("ZULIP_API_KEY", zulip_config.get("api_key"))
        site = os.environ.get("ZULIP_SITE", zulip_config.get("site"))

        if not all([email, api_key, site]):
            raise ValueError(
                "Missing Zulip credentials. Set ZULIP_EMAIL, ZULIP_API_KEY, "
                "and ZULIP_SITE environment variables or in config.yaml"
            )

        return zulip.Client(email=email, api_key=api_key, site=site)

    def _get_enabled_rules(self) -> list[dict]:
        """Get list of enabled formatting rules."""
        return [r for r in self.config.get("rules", []) if r.get("enabled", True)]

    def _matches_source(self, message: dict, rule: dict) -> bool:
        """Check if message matches rule's source criteria."""
        source = rule.get("source", {})

        # Check stream
        if source.get("stream") and message.get("display_recipient") != source["stream"]:
            return False

        # Check topic pattern
        topic_pattern = source.get("topic_pattern")
        if topic_pattern:
            if not re.search(topic_pattern, message.get("subject", ""), re.IGNORECASE):
                return False

        return True

    def _extract_variables(self, message: dict) -> dict:
        """Extract common variables from message for template substitution."""
        content = message.get("content", "")
        subject = message.get("subject", "")

        # Parse topic for repo info (e.g., "DollhouseMCP/mcp-server/checks")
        topic_parts = subject.split("/")
        repo = "/".join(topic_parts[:2]) if len(topic_parts) >= 2 else subject

        # Try to extract branch from content
        branch_match = re.search(r"branch[:\s]+[`\"]?([^`\"\s]+)[`\"]?", content, re.IGNORECASE)
        branch = branch_match.group(1) if branch_match else "unknown"

        # Try to extract URL
        url_match = re.search(r"https?://[^\s\)]+", content)
        url = url_match.group(0) if url_match else ""

        # Try to extract PR info
        pr_match = re.search(r"#(\d+)", content)
        pr_number = pr_match.group(1) if pr_match else ""

        # Try to extract title (usually in bold or after certain keywords)
        title_match = re.search(r"\*\*([^*]+)\*\*", content)
        title = title_match.group(1) if title_match else ""

        # Author
        author = message.get("sender_full_name", "")

        return {
            "source_topic": subject,
            "repo": repo,
            "branch": branch,
            "url": url,
            "number": pr_number,
            "title": title,
            "author": author,
            "content": content,
            "short_summary": content[:100] + "..." if len(content) > 100 else content,
        }

    def _match_pattern(self, content: str, rule: dict) -> Optional[str]:
        """Find which pattern matches the content, return pattern name."""
        match_config = rule.get("match", {})
        patterns = match_config.get("patterns", [])

        for pattern_def in patterns:
            pattern = pattern_def.get("pattern", "")
            if re.search(pattern, content, re.IGNORECASE):
                return pattern_def.get("name")

        return None

    def _format_message(self, message: dict, rule: dict) -> Optional[str]:
        """Apply formatting rule to message, return formatted content or None."""
        content = message.get("content", "")

        # Find matching pattern
        pattern_name = self._match_pattern(content, rule)

        # Get format template
        format_config = rule.get("format", {})
        if pattern_name:
            template = format_config.get(pattern_name)
        else:
            template = format_config.get("default")

        # None means don't repost
        if template is None:
            return None

        # Extract variables and substitute
        variables = self._extract_variables(message)
        try:
            formatted = template.format(**variables)
            return formatted.strip()
        except KeyError as e:
            self.logger.warning(f"Missing template variable: {e}")
            return None

    def _get_target(self, message: dict, rule: dict) -> tuple[str, str]:
        """Get target stream and topic for reformatted message."""
        target = rule.get("target", {})
        variables = self._extract_variables(message)

        stream = target.get("stream", message.get("display_recipient"))
        topic = target.get("topic", "{source_topic}").format(**variables)

        return stream, topic

    def _post_formatted(self, stream: str, topic: str, content: str):
        """Post formatted message to target stream/topic."""
        result = self.client.send_message({
            "type": "stream",
            "to": stream,
            "topic": topic,
            "content": content,
        })

        if result.get("result") != "success":
            self.logger.error(f"Failed to send message: {result}")
        else:
            self.logger.info(f"Posted to #{stream} > {topic}")

    def process_message(self, message: dict):
        """Process a single message through all rules."""
        msg_id = message.get("id")

        # Skip if already processed
        if msg_id in self.processed_ids:
            return
        self.processed_ids.add(msg_id)

        # Limit memory usage
        if len(self.processed_ids) > 10000:
            self.processed_ids = set(list(self.processed_ids)[-5000:])

        # Skip messages from self (prevent loops)
        if message.get("sender_email") == os.environ.get("ZULIP_EMAIL"):
            return

        # Try each rule
        for rule in self._get_enabled_rules():
            if not self._matches_source(message, rule):
                continue

            self.logger.debug(f"Rule '{rule.get('name')}' matched message {msg_id}")

            formatted = self._format_message(message, rule)
            if formatted:
                stream, topic = self._get_target(message, rule)
                self._post_formatted(stream, topic, formatted)
                # Only apply first matching rule
                break

    def run(self):
        """Main event loop - watch for messages and process them."""
        self.logger.info("Starting Formatter Bot...")

        # Get streams to watch
        streams_to_watch = set()
        for rule in self._get_enabled_rules():
            source_stream = rule.get("source", {}).get("stream")
            if source_stream:
                streams_to_watch.add(source_stream)

        self.logger.info(f"Watching streams: {streams_to_watch}")

        # Register event queue
        # We'll use all_public_streams for simplicity, filtered by our rules
        result = self.client.register(
            event_types=["message"],
            all_public_streams=True,
        )

        if result.get("result") != "success":
            self.logger.error(f"Failed to register queue: {result}")
            sys.exit(1)

        queue_id = result["queue_id"]
        last_event_id = result["last_event_id"]

        self.logger.info(f"Registered queue: {queue_id}")

        # Event loop
        while True:
            try:
                events = self.client.get_events(
                    queue_id=queue_id,
                    last_event_id=last_event_id,
                    dont_block=False,
                )

                if events.get("result") != "success":
                    self.logger.error(f"Failed to get events: {events}")
                    time.sleep(5)
                    continue

                for event in events.get("events", []):
                    last_event_id = max(last_event_id, event.get("id", last_event_id))

                    if event.get("type") == "message":
                        message = event.get("message", {})
                        # Only process stream messages
                        if message.get("type") == "stream":
                            self.process_message(message)
                    elif event.get("type") == "heartbeat":
                        self.logger.debug("Heartbeat received")

            except Exception as e:
                self.logger.error(f"Error in event loop: {e}")
                time.sleep(5)


def main():
    parser = argparse.ArgumentParser(description="Zulip Formatter Bot")
    parser.add_argument(
        "-c", "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)"
    )
    args = parser.parse_args()

    # Find config file
    config_path = Path(args.config)
    if not config_path.is_absolute():
        # Check relative to script location
        script_dir = Path(__file__).parent
        config_path = script_dir / args.config

    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}")
        sys.exit(1)

    bot = FormatterBot(str(config_path))
    bot.run()


if __name__ == "__main__":
    main()
