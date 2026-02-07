#!/usr/bin/env python3
"""
Twitter/X News Bot for Zulip

Monitors Twitter/X for content related to MCP, AI agents, and related topics,
then posts updates to a Zulip channel.

Since Twitter's official API is paid ($100+/month), this bot uses free
alternatives like RSS Bridge instances. These are less reliable but cost-free.
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


class TwitterNewsBot(BaseNewsBot):
    """Bot that monitors Twitter via RSS bridges and posts to Zulip."""

    GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"

    def __init__(self, config_path: str):
        super().__init__(config_path, bot_name="twitter_news_bot")

    def check_all_sources(self):
        """Check all configured sources."""
        self.logger.info("Checking for Twitter/X content...")

        sources = self.config.get("sources", {})

        if sources.get("rss_bridge", {}).get("enabled", False):
            self.check_rss_bridge()

        if sources.get("google_news_twitter", {}).get("enabled", False):
            self.check_google_news_twitter()

    def check_rss_bridge(self):
        """Search Twitter via RSS Bridge instances."""
        bridge_config = self.config["sources"]["rss_bridge"]
        instances = bridge_config.get("instances", [])
        queries = bridge_config.get("queries", [])
        max_age_hours = bridge_config.get("max_age_hours", 48)

        if not instances:
            self.logger.warning("No RSS Bridge instances configured")
            return

        for query in queries:
            success = False
            for instance in instances:
                try:
                    if self._search_rss_bridge(instance, query, max_age_hours):
                        success = True
                        break
                except Exception as e:
                    self.logger.debug(f"RSS Bridge instance {instance} failed for '{query}': {e}")
                    continue

            if not success:
                self.logger.warning(f"All RSS Bridge instances failed for query: {query}")

            # Rate limiting between queries
            time.sleep(3)

    def _search_rss_bridge(self, instance: str, query: str, max_age_hours: int) -> bool:
        """
        Search Twitter via a specific RSS Bridge instance.
        Returns True if successful, False otherwise.
        """
        # RSS Bridge TwitterSearch bridge format
        # See: https://github.com/RSS-Bridge/rss-bridge/blob/master/bridges/TwitterSearchBridge.php
        params = {
            "action": "display",
            "bridge": "TwitterSearch",
            "q": query,
            "format": "Atom"
        }

        url = f"{instance}/?{urllib.parse.urlencode(params)}"
        self.logger.debug(f"Trying RSS Bridge: {instance} for '{query}'")

        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "TwitterNewsBot/1.0 (Zulip Integration)"
            })
            with urllib.request.urlopen(req, timeout=30) as response:
                content = response.read()
        except Exception as e:
            raise Exception(f"Failed to fetch: {e}")

        # Parse Atom feed
        try:
            root = ET.fromstring(content)
        except ET.ParseError as e:
            raise Exception(f"Failed to parse feed: {e}")

        # Define namespaces for Atom
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        entries = root.findall("atom:entry", ns)
        if not entries:
            # Try without namespace (some bridges return plain RSS)
            entries = root.findall(".//item")

        processed = 0
        for entry in entries:
            try:
                if self._process_bridge_entry(entry, ns, query, max_age_hours):
                    processed += 1
            except Exception as e:
                self.logger.debug(f"Error processing entry: {e}")

        self.logger.debug(f"Processed {processed} entries from RSS Bridge for '{query}'")
        return True

    def _process_bridge_entry(self, entry, ns: dict, search_query: str, max_age_hours: int) -> bool:
        """Process a single entry from RSS Bridge. Returns True if posted."""
        # Try Atom format first, then RSS format
        title = self._get_text(entry, "atom:title", ns) or self._get_text(entry, "title", {})
        link = self._get_text(entry, "atom:link", ns, attr="href") or self._get_text(entry, "link", {})
        content_elem = entry.find("atom:content", ns) or entry.find("description")
        content_text = content_elem.text if content_elem is not None else ""
        updated = self._get_text(entry, "atom:updated", ns) or self._get_text(entry, "pubDate", {})
        author = self._get_text(entry, "atom:author/atom:name", ns) or ""

        if not title or not link:
            return False

        # Create unique ID
        item_id = f"twitter_bridge_{hash(link)}"

        if self.is_seen(item_id):
            return False

        # Parse and check date
        if updated:
            try:
                if "T" in updated:
                    # ISO format
                    pub_date = datetime.fromisoformat(updated.replace("Z", "+00:00"))
                else:
                    # RFC 2822 format
                    pub_date = parsedate_to_datetime(updated)

                if self.is_too_old(pub_date, max_age_hours):
                    self.mark_seen(item_id)
                    return False
                date_str = pub_date.strftime('%Y-%m-%d %H:%M UTC')
            except Exception:
                date_str = "Unknown"
        else:
            date_str = "Unknown"

        # Categorize
        category = self._categorize_item(title, content_text)

        # Format message
        message = f"**Twitter: {title}**\n"
        if author:
            message += f"**Author:** @{author}\n"
        message += f"**Posted:** {date_str}\n"
        message += f"**Search Term:** {search_query}\n"
        message += f"**URL:** {link}"

        if content_text:
            # Clean up HTML and truncate
            clean_content = content_text.replace("<br>", "\n").replace("<br/>", "\n")
            clean_content = clean_content.replace("<p>", "").replace("</p>", "\n")
            # Remove remaining HTML tags
            import re
            clean_content = re.sub(r'<[^>]+>', '', clean_content)
            clean_content = clean_content.strip()

            if clean_content and len(clean_content) > 20:
                if len(clean_content) > 500:
                    clean_content = clean_content[:500] + "..."
                message += f"\n\n{clean_content}"

        self._post_to_zulip(category, message)
        self.mark_seen(item_id)

        time.sleep(1)
        return True

    def _get_text(self, elem, path: str, ns: dict, attr: str = None):
        """Helper to get text from an element, handling namespaces."""
        found = elem.find(path, ns) if ns else elem.find(path)
        if found is not None:
            if attr:
                return found.get(attr)
            return found.text
        return None

    def check_google_news_twitter(self):
        """Search Google News for Twitter content as a backup."""
        source_config = self.config["sources"]["google_news_twitter"]
        queries = source_config.get("queries", [])
        max_age_hours = source_config.get("max_age_hours", 168)

        for query in queries:
            try:
                self._search_google_news(query, max_age_hours)
                time.sleep(2)
            except Exception as e:
                self.logger.error(f"Error searching Google News for '{query}': {e}")

    def _search_google_news(self, query: str, max_age_hours: int):
        """Search Google News for Twitter content."""
        # Combine query with site:twitter.com filter
        full_query = f"{query} site:twitter.com OR site:x.com"

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
                "User-Agent": "TwitterNewsBot/1.0 (Zulip Integration)"
            })
            with urllib.request.urlopen(req, timeout=30) as response:
                content = response.read()
        except Exception as e:
            self.logger.error(f"Failed to fetch Google News RSS: {e}")
            return

        try:
            root = ET.fromstring(content)
        except ET.ParseError as e:
            self.logger.error(f"Failed to parse RSS feed: {e}")
            return

        for item in root.findall(".//item"):
            try:
                self._process_google_news_item(item, query, max_age_hours)
            except Exception as e:
                self.logger.error(f"Error processing news item: {e}")

    def _process_google_news_item(self, item, search_query: str, max_age_hours: int):
        """Process a single item from Google News RSS."""
        title_elem = item.find("title")
        link_elem = item.find("link")
        pub_date_elem = item.find("pubDate")

        if title_elem is None or link_elem is None:
            return

        title = title_elem.text or ""
        link = link_elem.text or ""

        # Create unique ID
        item_id = f"twitter_gnews_{hash(link)}"

        if self.is_seen(item_id):
            return

        # Parse and check date
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

        # Verify it's actually a Twitter/X URL
        if "twitter.com" not in link.lower() and "x.com" not in link.lower():
            self.mark_seen(item_id)
            return

        # Categorize
        category = self._categorize_item(title)

        # Format message
        content = (
            f"**Twitter (via Google News): {title}**\n"
            f"**Published:** {date_str}\n"
            f"**Search Term:** {search_query}\n"
            f"**URL:** {link}"
        )

        self._post_to_zulip(category, content)
        self.mark_seen(item_id)

        time.sleep(1)


def main():
    parser = argparse.ArgumentParser(description="Twitter/X News Bot for Zulip")
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

    bot = TwitterNewsBot(str(config_path))

    if args.check_once:
        bot.run_once()
    else:
        bot.run()


if __name__ == "__main__":
    main()
