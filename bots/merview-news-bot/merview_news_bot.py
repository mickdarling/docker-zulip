#!/usr/bin/env python3
"""
Merview News Bot for Zulip

Monitors web sources for news about Merview and posts to Zulip.
Filters out references to the Thai person named Merview.
"""

import os
import sys
import time
import json
import logging
import argparse
import requests
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Set, Optional

import yaml
import zulip
from dotenv import load_dotenv

# Load .env file from script directory
load_dotenv(Path(__file__).parent / ".env")


class MerviewNewsBot:
    """Bot that monitors web sources for Merview news and posts to Zulip."""

    def __init__(self, config_path: str):
        self.script_dir = Path(__file__).parent
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.logger = logging.getLogger("merview_news_bot")
        self.zulip_client = self._create_zulip_client()
        self.seen_items = self._load_seen_items()

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        # Expand environment variables in config
        if "zulip" in config:
            api_key = config["zulip"].get("api_key", "")
            if api_key.startswith("${") and api_key.endswith("}"):
                env_var = api_key[2:-1]
                config["zulip"]["api_key"] = os.environ.get(env_var, "")

        return config

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

    def _create_zulip_client(self) -> zulip.Client:
        """Create authenticated Zulip client."""
        zulip_config = self.config.get("zulip", {})

        if not all(k in zulip_config for k in ["email", "api_key", "site"]):
            raise ValueError("Missing required Zulip configuration")

        client = zulip.Client(
            email=zulip_config["email"],
            api_key=zulip_config["api_key"],
            site=zulip_config["site"],
        )
        self.logger.info(f"Created Zulip client for {zulip_config['site']}")
        return client

    def _load_seen_items(self) -> Set[str]:
        """Load set of already-seen item IDs from disk."""
        seen_file = self.script_dir / "seen_items.json"
        if seen_file.exists():
            try:
                with open(seen_file, "r") as f:
                    data = json.load(f)
                    seen = set(data.get("items", []))
                    self.logger.info(f"Loaded {len(seen)} seen items from disk")
                    return seen
            except Exception as e:
                self.logger.warning(f"Failed to load seen items: {e}")
        return set()

    def _save_seen_items(self):
        """Save seen item IDs to disk."""
        seen_file = self.script_dir / "seen_items.json"
        try:
            # Keep only the most recent 2000 items to prevent unbounded growth
            items_to_save = list(self.seen_items)[-2000:]
            with open(seen_file, "w") as f:
                json.dump({"items": items_to_save, "last_updated": datetime.now(timezone.utc).isoformat()}, f, indent=2)
            self.logger.debug(f"Saved {len(items_to_save)} seen items to disk")
        except Exception as e:
            self.logger.error(f"Failed to save seen items: {e}")

    def _matches_keywords(self, text: str, keywords: List[str]) -> bool:
        """Check if text matches any of the keywords (case-insensitive)."""
        if not text:
            return False
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in keywords)

    def _is_thai_person_reference(self, text: str) -> bool:
        """Check if text appears to reference the Thai person named Merview."""
        if not text:
            return False

        text_lower = text.lower()

        # Thai language indicators
        thai_indicators = [
            "thailand",
            "thai",
            "bangkok",
            "\u0e00-\u0e7f",  # Thai Unicode range (will match if Thai characters present)
        ]

        # Other common person-related indicators
        person_indicators = [
            "profile",
            "biography",
            "personal",
            "linkedin",
            "facebook.com",
            "twitter.com",
            "instagram.com",
        ]

        # Check for Thai indicators
        for indicator in thai_indicators:
            if indicator in text_lower:
                self.logger.info(f"Filtered out Thai person reference (Thai indicator: {indicator})")
                return True

        # Check for person indicators combined with Merview
        if "merview" in text_lower:
            for indicator in person_indicators:
                if indicator in text_lower:
                    self.logger.info(f"Filtered out person reference (indicator: {indicator})")
                    return True

        return False

    def _categorize_item(self, title: str, body: str = "") -> str:
        """Determine category based on keywords in title/body."""
        combined = f"{title} {body}".lower()

        categories = self.config.get("categories", {})

        # Check each category's keywords
        for category_name, category_data in categories.items():
            keywords = category_data.get("keywords", [])
            if self._matches_keywords(combined, keywords):
                return category_name

        # Default category
        return self.config.get("default_category", "General")

    def _post_to_zulip(self, category: str, content: str):
        """Post news item to Zulip."""
        zulip_config = self.config.get("zulip", {})
        stream = zulip_config.get("stream", "news")

        # Get topic from category configuration
        categories = self.config.get("categories", {})
        topic = categories.get(category, {}).get("topic", category)

        result = self.zulip_client.send_message({
            "type": "stream",
            "to": stream,
            "topic": topic,
            "content": content,
        })

        if result.get("result") != "success":
            self.logger.error(f"Failed to send to Zulip: {result}")
        else:
            self.logger.info(f"Posted to #{stream} > {topic}")

    def check_hackernews(self):
        """Check Hacker News for stories matching keywords."""
        if not self.config.get("sources", {}).get("hackernews", {}).get("enabled", False):
            return

        hn_config = self.config["sources"]["hackernews"]
        keywords = hn_config.get("keywords", [])

        try:
            # Use Algolia HN Search API
            base_url = "https://hn.algolia.com/api/v1/search"

            for keyword in keywords:
                params = {
                    "query": keyword,
                    "tags": "story",
                    "hitsPerPage": 10,
                }

                response = requests.get(base_url, params=params, timeout=10)
                response.raise_for_status()

                data = response.json()

                for hit in data.get("hits", []):
                    story_id = f"hn_story_{hit['objectID']}"

                    if story_id in self.seen_items:
                        continue

                    title = hit.get("title", "")

                    # Filter out Thai person references
                    combined_text = f"{title} {hit.get('url', '')}"
                    if self._is_thai_person_reference(combined_text):
                        self.seen_items.add(story_id)
                        continue

                    # Check age - handle both date formats (with and without milliseconds)
                    created_at_str = hit["created_at"]
                    try:
                        # Try with milliseconds first
                        created_at = datetime.strptime(created_at_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
                    except ValueError:
                        # Fall back to format without milliseconds
                        created_at = datetime.strptime(created_at_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                    hours_old = (datetime.now(timezone.utc) - created_at).total_seconds() / 3600

                    max_age_hours = hn_config.get("max_age_hours", 48)
                    if hours_old > max_age_hours:
                        self.seen_items.add(story_id)
                        continue

                    # Format message
                    url = hit.get("url", f"https://news.ycombinator.com/item?id={hit['objectID']}")
                    points = hit.get("points", 0)
                    num_comments = hit.get("num_comments", 0)

                    category = self._categorize_item(title)

                    content = (
                        f"**Hacker News: {title}**\n"
                        f"**Score:** {points} points | {num_comments} comments\n"
                        f"**Posted:** {created_at.strftime('%Y-%m-%d %H:%M UTC')}\n"
                        f"**URL:** {url}\n"
                        f"**HN Discussion:** https://news.ycombinator.com/item?id={hit['objectID']}"
                    )

                    self._post_to_zulip(category, content)
                    self.seen_items.add(story_id)

                    # Rate limiting
                    time.sleep(2)

                # Delay between keyword searches
                time.sleep(1)

        except Exception as e:
            self.logger.error(f"Error checking Hacker News: {e}")

    def check_reddit(self):
        """Check Reddit for posts matching keywords."""
        if not self.config.get("sources", {}).get("reddit", {}).get("enabled", False):
            return

        reddit_config = self.config["sources"]["reddit"]
        subreddits = reddit_config.get("subreddits", [])
        keywords = reddit_config.get("keywords", [])

        for subreddit in subreddits:
            try:
                # Use Reddit JSON API (no auth required for public posts)
                url = f"https://www.reddit.com/r/{subreddit}/new.json"
                headers = {"User-Agent": "MerviewNewsBot/1.0"}

                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()

                data = response.json()

                for post in data["data"]["children"]:
                    post_data = post["data"]
                    post_id = f"reddit_post_{post_data['id']}"

                    if post_id in self.seen_items:
                        continue

                    # Check if post matches keywords
                    title = post_data.get("title", "")
                    selftext = post_data.get("selftext", "")

                    if not self._matches_keywords(f"{title} {selftext}", keywords):
                        self.seen_items.add(post_id)
                        continue

                    # Filter out Thai person references
                    combined_text = f"{title} {selftext}"
                    if self._is_thai_person_reference(combined_text):
                        self.seen_items.add(post_id)
                        continue

                    # Check age
                    created_utc = datetime.fromtimestamp(post_data["created_utc"], tz=timezone.utc)
                    hours_old = (datetime.now(timezone.utc) - created_utc).total_seconds() / 3600

                    max_age_hours = reddit_config.get("max_age_hours", 48)
                    if hours_old > max_age_hours:
                        self.seen_items.add(post_id)
                        continue

                    # Format message
                    category = self._categorize_item(title, selftext)

                    upvotes = post_data.get("ups", 0)
                    num_comments = post_data.get("num_comments", 0)
                    permalink = f"https://www.reddit.com{post_data['permalink']}"

                    content = (
                        f"**Reddit r/{subreddit}: {title}**\n"
                        f"**Score:** {upvotes} upvotes | {num_comments} comments\n"
                        f"**Posted:** {created_utc.strftime('%Y-%m-%d %H:%M UTC')}\n"
                        f"**URL:** {permalink}\n"
                    )

                    # Add preview of self text if available
                    if selftext:
                        preview = selftext[:300]
                        if len(selftext) > 300:
                            preview += "..."
                        content += f"\n**Preview:**\n{preview}"

                    self._post_to_zulip(category, content)
                    self.seen_items.add(post_id)

                    # Rate limiting
                    time.sleep(2)

                # Delay between subreddits
                time.sleep(3)

            except Exception as e:
                self.logger.error(f"Error checking Reddit r/{subreddit}: {e}")

    def check_google_news(self):
        """Check Google News RSS feed for Merview mentions."""
        if not self.config.get("sources", {}).get("google_news", {}).get("enabled", False):
            return

        try:
            # Google News RSS feed for "Merview" search
            url = "https://news.google.com/rss/search?q=Merview&hl=en-US&gl=US&ceid=US:en"

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # Parse RSS feed (simple XML parsing)
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)

            # Google News RSS uses standard RSS 2.0 format
            for item in root.findall(".//item"):
                title_elem = item.find("title")
                link_elem = item.find("link")
                pub_date_elem = item.find("pubDate")

                if title_elem is None or link_elem is None:
                    continue

                title = title_elem.text
                link = link_elem.text

                # Create unique ID
                news_id = f"google_news_{hash(link)}"

                if news_id in self.seen_items:
                    continue

                # Filter out Thai person references
                if self._is_thai_person_reference(title):
                    self.seen_items.add(news_id)
                    continue

                # Parse publication date
                if pub_date_elem is not None:
                    pub_date_str = pub_date_elem.text
                    try:
                        # RFC 2822 format: "Wed, 02 Oct 2002 13:00:00 GMT"
                        from email.utils import parsedate_to_datetime
                        pub_date = parsedate_to_datetime(pub_date_str)
                        hours_old = (datetime.now(timezone.utc) - pub_date).total_seconds() / 3600

                        max_age_hours = self.config["sources"]["google_news"].get("max_age_hours", 168)
                        if hours_old > max_age_hours:
                            self.seen_items.add(news_id)
                            continue

                        date_str = pub_date.strftime('%Y-%m-%d %H:%M UTC')
                    except Exception as e:
                        self.logger.warning(f"Failed to parse date: {e}")
                        date_str = "Unknown"
                else:
                    date_str = "Unknown"

                # Categorize
                category = self._categorize_item(title)

                content = (
                    f"**Google News: {title}**\n"
                    f"**Published:** {date_str}\n"
                    f"**URL:** {link}"
                )

                self._post_to_zulip(category, content)
                self.seen_items.add(news_id)

                # Rate limiting
                time.sleep(2)

        except Exception as e:
            self.logger.error(f"Error checking Google News: {e}")

    def check_all_sources(self):
        """Check all configured sources for new content."""
        self.logger.info("Checking all sources for new Merview news...")

        try:
            self.check_google_news()
            self.check_hackernews()
            self.check_reddit()

            # Save seen items after each check cycle
            self._save_seen_items()

        except Exception as e:
            self.logger.error(f"Error during source check: {e}")

    def run(self):
        """Main loop - poll sources and post to Zulip."""
        poll_interval = self.config.get("poll_interval_seconds", 3600)
        self.logger.info(f"Starting Merview News Bot (polling every {poll_interval}s)...")

        # Log enabled sources
        sources = self.config.get("sources", {})
        for source_name, source_config in sources.items():
            if source_config.get("enabled", False):
                self.logger.info(f"Monitoring source: {source_name}")

        while True:
            self.check_all_sources()
            self.logger.info(f"Sleeping for {poll_interval} seconds...")
            time.sleep(poll_interval)


def main():
    parser = argparse.ArgumentParser(description="Merview News Bot for Zulip")
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

    bot = MerviewNewsBot(str(config_path))

    if args.check_once:
        bot.check_all_sources()
        print("Single check completed!")
        sys.exit(0)

    bot.run()


if __name__ == "__main__":
    main()
