#!/usr/bin/env python3
"""
Mastodon News Bot for Zulip

Monitors Mastodon instances for posts related to MCP, AI agents, and LLMs,
then posts updates to a Zulip channel.
"""

import sys
import time
import argparse
import urllib.request
import urllib.parse
import json
import re
from pathlib import Path
from datetime import datetime, timezone
from html.parser import HTMLParser

# Add parent directory to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.base_bot import BaseNewsBot


class HTMLStripper(HTMLParser):
    """Simple HTML to text converter."""

    def __init__(self):
        super().__init__()
        self.result = []

    def handle_data(self, data):
        self.result.append(data)

    def handle_starttag(self, tag, attrs):
        if tag == "br":
            self.result.append("\n")
        elif tag == "p":
            self.result.append("\n")

    def get_text(self):
        return "".join(self.result).strip()


def strip_html(html: str) -> str:
    """Strip HTML tags and return plain text."""
    stripper = HTMLStripper()
    stripper.feed(html)
    return stripper.get_text()


class MastodonNewsBot(BaseNewsBot):
    """Bot that monitors Mastodon for relevant posts and posts to Zulip."""

    def __init__(self, config_path: str):
        super().__init__(config_path, bot_name="mastodon_news_bot")

    def check_all_sources(self):
        """Check all configured Mastodon sources."""
        self.logger.info("Checking Mastodon for new posts...")

        sources = self.config.get("sources", {})

        if sources.get("mastodon_search", {}).get("enabled", False):
            self.check_mastodon_search()

        if sources.get("mastodon_hashtags", {}).get("enabled", False):
            self.check_mastodon_hashtags()

    def check_mastodon_search(self):
        """Search Mastodon instances for posts matching queries."""
        search_config = self.config["sources"]["mastodon_search"]
        instances = search_config.get("instances", ["mastodon.social"])
        queries = search_config.get("queries", [])
        max_results = search_config.get("max_results", 20)
        max_age_hours = search_config.get("max_age_hours", 72)

        for instance in instances:
            for query in queries:
                try:
                    # Build API query - Mastodon v2 search API
                    params = {
                        "q": query,
                        "type": "statuses",
                        "limit": max_results
                    }
                    url = f"https://{instance}/api/v2/search?{urllib.parse.urlencode(params)}"

                    self.logger.debug(f"Querying {instance}: {query}")

                    # Make request
                    req = urllib.request.Request(url)
                    req.add_header("Accept", "application/json")
                    req.add_header("User-Agent", "MastodonNewsBot/1.0")

                    with urllib.request.urlopen(req, timeout=30) as response:
                        data = json.loads(response.read().decode())

                    statuses = data.get("statuses", [])
                    self.logger.info(f"Found {len(statuses)} posts on {instance} for query: {query}")

                    for status in statuses:
                        self._process_status(status, max_age_hours, instance)

                    # Rate limiting between queries
                    time.sleep(2)

                except urllib.error.HTTPError as e:
                    self.logger.warning(f"HTTP error querying {instance} for '{query}': {e.code} {e.reason}")
                except Exception as e:
                    self.logger.error(f"Error querying {instance} for '{query}': {e}")

            # Rate limiting between instances
            time.sleep(3)

    def check_mastodon_hashtags(self):
        """Check Mastodon instances for specific hashtags."""
        hashtag_config = self.config["sources"]["mastodon_hashtags"]
        instances = hashtag_config.get("instances", ["mastodon.social"])
        hashtags = hashtag_config.get("hashtags", [])
        max_results = hashtag_config.get("max_results", 20)
        max_age_hours = hashtag_config.get("max_age_hours", 72)

        for instance in instances:
            for hashtag in hashtags:
                try:
                    # Remove # if present
                    tag = hashtag.lstrip("#")

                    # Hashtag timeline API
                    params = {"limit": max_results}
                    url = f"https://{instance}/api/v1/timelines/tag/{tag}?{urllib.parse.urlencode(params)}"

                    self.logger.debug(f"Checking #{tag} on {instance}")

                    req = urllib.request.Request(url)
                    req.add_header("Accept", "application/json")
                    req.add_header("User-Agent", "MastodonNewsBot/1.0")

                    with urllib.request.urlopen(req, timeout=30) as response:
                        statuses = json.loads(response.read().decode())

                    self.logger.info(f"Found {len(statuses)} posts for #{tag} on {instance}")

                    for status in statuses:
                        self._process_status(status, max_age_hours, instance)

                    # Rate limiting between hashtags
                    time.sleep(2)

                except urllib.error.HTTPError as e:
                    self.logger.warning(f"HTTP error checking #{tag} on {instance}: {e.code} {e.reason}")
                except Exception as e:
                    self.logger.error(f"Error checking #{tag} on {instance}: {e}")

            # Rate limiting between instances
            time.sleep(3)

    def _process_status(self, status: dict, max_age_hours: int, instance: str):
        """Process a single Mastodon status."""
        try:
            # Extract status data
            status_id = status.get("id", "")
            uri = status.get("uri", "")
            url = status.get("url", "")
            content = status.get("content", "")
            created_at = status.get("created_at", "")
            account = status.get("account", {})

            # Skip reblogs (boosts)
            if status.get("reblog"):
                return

            # Create unique ID
            post_id = f"mastodon_{instance}_{status_id}"

            if self.is_seen(post_id):
                return

            # Check age
            if created_at:
                try:
                    post_date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    if self.is_too_old(post_date, max_age_hours):
                        self.mark_seen(post_id)
                        return
                    date_display = post_date.strftime('%Y-%m-%d %H:%M UTC')
                except Exception:
                    date_display = "Unknown"
            else:
                date_display = "Unknown"

            # Get author info
            author_acct = account.get("acct", "unknown")
            author_display = account.get("display_name", author_acct)

            # Full handle includes instance if not already present
            if "@" not in author_acct:
                author_acct = f"{author_acct}@{instance}"

            # Strip HTML from content
            text = strip_html(content)
            if not text:
                return

            # Get engagement stats
            favourites_count = status.get("favourites_count", 0)
            reblogs_count = status.get("reblogs_count", 0)
            replies_count = status.get("replies_count", 0)

            # Categorize
            category = self._categorize_item(text)

            # Format message
            msg_content = (
                f"**Mastodon: @{author_acct}**\n"
                f"**Author:** {author_display}\n"
                f"**Posted:** {date_display}\n"
                f"**URL:** {url or uri}\n"
            )

            if favourites_count or reblogs_count or replies_count:
                msg_content += f"**Engagement:** {favourites_count} favorites, {reblogs_count} boosts, {replies_count} replies\n"

            # Truncate long posts
            if len(text) > 500:
                text = text[:500] + "..."
            msg_content += f"\n{text}"

            self._post_to_zulip(category, msg_content)
            self.mark_seen(post_id)

        except Exception as e:
            self.logger.error(f"Error processing Mastodon status: {e}")


def main():
    parser = argparse.ArgumentParser(description="Mastodon News Bot for Zulip")
    parser.add_argument(
        "-c", "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)"
    )
    parser.add_argument(
        "--check-once",
        action="store_true",
        help="Check sources once and exit (for testing)"
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

    bot = MastodonNewsBot(str(config_path))

    if args.check_once:
        bot.run_once()
    else:
        bot.run()


if __name__ == "__main__":
    main()
