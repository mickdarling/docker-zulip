#!/usr/bin/env python3
"""
LinkedIn News Bot for Zulip

Monitors LinkedIn content via Google News RSS feeds (with site:linkedin.com filter)
for articles related to MCP, AI agents, and related topics.

Note: LinkedIn doesn't have a public API for content search, so we use
Google News as a workaround to find LinkedIn articles that appear in search results.
"""

import sys
import time
import argparse
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

# Add parent directory to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.base_bot import BaseNewsBot


class LinkedInNewsBot(BaseNewsBot):
    """Bot that monitors LinkedIn content via Google News and posts to Zulip."""

    GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"

    def __init__(self, config_path: str):
        super().__init__(config_path, bot_name="linkedin_news_bot")

    def check_all_sources(self):
        """Check all configured sources."""
        self.logger.info("Checking for LinkedIn content via Google News...")

        sources = self.config.get("sources", {})

        if sources.get("google_news_linkedin", {}).get("enabled", False):
            self.check_google_news_linkedin()

    def check_google_news_linkedin(self):
        """Search Google News for LinkedIn articles matching queries."""
        source_config = self.config["sources"]["google_news_linkedin"]
        queries = source_config.get("queries", [])
        max_age_hours = source_config.get("max_age_hours", 168)

        for query in queries:
            try:
                self._search_google_news(query, max_age_hours)
                # Rate limiting between queries
                time.sleep(2)
            except Exception as e:
                self.logger.error(f"Error searching Google News for '{query}': {e}")

    def _search_google_news(self, query: str, max_age_hours: int):
        """Execute a Google News search for LinkedIn content."""
        # Combine query with site:linkedin.com filter
        full_query = f"{query} site:linkedin.com"

        params = {
            "q": full_query,
            "hl": "en-US",
            "gl": "US",
            "ceid": "US:en"
        }

        url = f"{self.GOOGLE_NEWS_RSS_URL}?{urllib.parse.urlencode(params)}"
        self.logger.debug(f"Searching Google News: {full_query}")

        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "LinkedInNewsBot/1.0 (Zulip Integration)"
            })
            with urllib.request.urlopen(req, timeout=30) as response:
                content = response.read()
        except Exception as e:
            self.logger.error(f"Failed to fetch Google News RSS: {e}")
            return

        # Parse RSS feed
        try:
            root = ET.fromstring(content)
        except ET.ParseError as e:
            self.logger.error(f"Failed to parse RSS feed: {e}")
            return

        for item in root.findall(".//item"):
            try:
                self._process_news_item(item, query, max_age_hours)
            except Exception as e:
                self.logger.error(f"Error processing news item: {e}")

    def _process_news_item(self, item, search_query: str, max_age_hours: int):
        """Process a single news item from Google News RSS."""
        title_elem = item.find("title")
        link_elem = item.find("link")
        pub_date_elem = item.find("pubDate")
        source_elem = item.find("source")

        if title_elem is None or link_elem is None:
            return

        title = title_elem.text or ""
        link = link_elem.text or ""
        source = source_elem.text if source_elem is not None else "LinkedIn"

        # Create unique ID from link
        item_id = f"linkedin_gnews_{hash(link)}"

        if self.is_seen(item_id):
            return

        # Parse and check publication date
        if pub_date_elem is not None and pub_date_elem.text:
            try:
                pub_date = parsedate_to_datetime(pub_date_elem.text)
                if self.is_too_old(pub_date, max_age_hours):
                    self.mark_seen(item_id)
                    return
                date_str = pub_date.strftime('%Y-%m-%d %H:%M UTC')
            except Exception:
                date_str = "Unknown"
        else:
            date_str = "Unknown"

        # Verify it's actually a LinkedIn URL (Google News sometimes includes related articles)
        if "linkedin.com" not in link.lower():
            self.mark_seen(item_id)
            return

        # Categorize
        category = self._categorize_item(title)

        # Format message
        content = (
            f"**LinkedIn: {title}**\n"
            f"**Source:** {source}\n"
            f"**Published:** {date_str}\n"
            f"**Search Term:** {search_query}\n"
            f"**URL:** {link}"
        )

        self._post_to_zulip(category, content)
        self.mark_seen(item_id)

        # Small delay between posts
        time.sleep(1)


def main():
    parser = argparse.ArgumentParser(description="LinkedIn News Bot for Zulip")
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

    bot = LinkedInNewsBot(str(config_path))

    if args.check_once:
        bot.run_once()
    else:
        bot.run()


if __name__ == "__main__":
    main()
