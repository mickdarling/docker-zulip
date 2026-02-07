#!/usr/bin/env python3
"""
MCP News Bot for Zulip

Monitors web sources for news about the MCP ecosystem and posts to Zulip.
Phase 1: GitHub releases, Hacker News, and Reddit monitoring.
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


class MCPNewsBot:
    """Bot that monitors web sources for MCP news and posts to Zulip."""

    def __init__(self, config_path: str):
        self.script_dir = Path(__file__).parent
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.logger = logging.getLogger("mcp_news_bot")
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
        stream = zulip_config.get("stream", "mcp-news")

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

    def check_glama_rss(self):
        """Check Glama.ai blog RSS feed for MCP news."""
        if not self.config.get("sources", {}).get("glama", {}).get("enabled", False):
            return

        glama_config = self.config["sources"]["glama"]
        rss_url = glama_config.get("rss_url", "https://glama.ai/blog/rss.xml")

        try:
            # Use httpx instead of requests - handles HTTP 103 Early Hints properly
            import httpx
            headers = {"User-Agent": "MCPNewsBot/1.0 (Zulip Integration)"}
            with httpx.Client(http2=True, follow_redirects=True) as client:
                response = client.get(rss_url, headers=headers, timeout=30)
                response.raise_for_status()

            # Parse RSS feed
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)

            for item in root.findall(".//item"):
                title_elem = item.find("title")
                link_elem = item.find("link")
                pub_date_elem = item.find("pubDate")
                description_elem = item.find("description")

                if title_elem is None or link_elem is None:
                    continue

                title = title_elem.text
                link = link_elem.text

                # Create unique ID
                item_id = f"glama_blog_{hash(link)}"

                if item_id in self.seen_items:
                    continue

                # Parse publication date
                if pub_date_elem is not None:
                    pub_date_str = pub_date_elem.text
                    try:
                        from email.utils import parsedate_to_datetime
                        pub_date = parsedate_to_datetime(pub_date_str)
                        hours_old = (datetime.now(timezone.utc) - pub_date).total_seconds() / 3600

                        max_age_hours = glama_config.get("max_age_hours", 168)
                        if hours_old > max_age_hours:
                            self.seen_items.add(item_id)
                            continue

                        date_str = pub_date.strftime('%Y-%m-%d %H:%M UTC')
                    except Exception as e:
                        self.logger.warning(f"Failed to parse Glama date: {e}")
                        date_str = "Unknown"
                else:
                    date_str = "Unknown"

                # Categorize based on title
                category = self._categorize_item(title, description_elem.text if description_elem is not None else "")

                content = (
                    f"**Glama.ai Blog: {title}**\n"
                    f"**Published:** {date_str}\n"
                    f"**URL:** {link}"
                )

                self._post_to_zulip(category, content)
                self.seen_items.add(item_id)

                # Rate limiting
                time.sleep(2)

        except Exception as e:
            self.logger.error(f"Error checking Glama RSS: {e}")

    def check_github_releases(self):
        """Check GitHub for new releases related to MCP."""
        if not self.config.get("sources", {}).get("github", {}).get("enabled", False):
            return

        github_config = self.config["sources"]["github"]
        repos = github_config.get("repos", [])

        for repo in repos:
            try:
                # Use GitHub API to check releases
                url = f"https://api.github.com/repos/{repo}/releases"
                headers = {"Accept": "application/vnd.github.v3+json"}

                # Add GitHub token if available
                github_token = os.environ.get("GITHUB_TOKEN")
                if github_token:
                    headers["Authorization"] = f"token {github_token}"

                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()

                releases = response.json()

                # Check most recent releases
                for release in releases[:5]:  # Only check last 5 releases
                    release_id = f"github_release_{repo}_{release['id']}"

                    if release_id in self.seen_items:
                        continue

                    # Check if release is recent (within configured timeframe)
                    published_at = datetime.strptime(release["published_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                    hours_old = (datetime.now(timezone.utc) - published_at).total_seconds() / 3600

                    max_age_hours = github_config.get("max_age_hours", 168)  # Default 1 week
                    if hours_old > max_age_hours:
                        self.seen_items.add(release_id)
                        continue

                    # Format message
                    category = self._categorize_item(release["name"], release.get("body", ""))

                    content = (
                        f"**New GitHub Release: {repo}**\n"
                        f"**Version:** {release['name']}\n"
                        f"**Published:** {published_at.strftime('%Y-%m-%d %H:%M UTC')}\n"
                        f"**URL:** {release['html_url']}\n\n"
                    )

                    if release.get("body"):
                        # Truncate release notes if too long
                        notes = release["body"][:500]
                        if len(release["body"]) > 500:
                            notes += "..."
                        content += f"**Release Notes:**\n{notes}"

                    self._post_to_zulip(category, content)
                    self.seen_items.add(release_id)

                    # Rate limiting
                    time.sleep(2)

                # Small delay between repos
                time.sleep(1)

            except Exception as e:
                self.logger.error(f"Error checking GitHub releases for {repo}: {e}")

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
                    title = hit.get("title", "")
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
                headers = {"User-Agent": "MCPNewsBot/1.0"}

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
        """Check Google News RSS feed for configured search terms."""
        if not self.config.get("sources", {}).get("google_news", {}).get("enabled", False):
            return

        google_config = self.config["sources"]["google_news"]
        keywords = google_config.get("keywords", [])

        for keyword in keywords:
            try:
                # Google News RSS feed for search term
                # URL encode the keyword for the query
                import urllib.parse
                encoded_keyword = urllib.parse.quote(keyword)
                url = f"https://news.google.com/rss/search?q={encoded_keyword}&hl=en-US&gl=US&ceid=US:en"

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

                    # Parse publication date
                    if pub_date_elem is not None:
                        pub_date_str = pub_date_elem.text
                        try:
                            # RFC 2822 format: "Wed, 02 Oct 2002 13:00:00 GMT"
                            from email.utils import parsedate_to_datetime
                            pub_date = parsedate_to_datetime(pub_date_str)
                            hours_old = (datetime.now(timezone.utc) - pub_date).total_seconds() / 3600

                            max_age_hours = google_config.get("max_age_hours", 168)
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
                        f"**Search Term:** {keyword}\n"
                        f"**Published:** {date_str}\n"
                        f"**URL:** {link}"
                    )

                    self._post_to_zulip(category, content)
                    self.seen_items.add(news_id)

                    # Rate limiting
                    time.sleep(2)

                # Delay between keyword searches
                time.sleep(1)

            except Exception as e:
                self.logger.error(f"Error checking Google News for '{keyword}': {e}")

    def check_all_sources(self):
        """Check all configured sources for new content."""
        self.logger.info("Checking all sources for new MCP news...")

        try:
            self.check_glama_rss()
            self.check_github_releases()
            self.check_hackernews()
            self.check_reddit()
            self.check_google_news()

            # Save seen items after each check cycle
            self._save_seen_items()

        except Exception as e:
            self.logger.error(f"Error during source check: {e}")

    def run(self):
        """Main loop - poll sources and post to Zulip."""
        poll_interval = self.config.get("poll_interval_seconds", 3600)
        self.logger.info(f"Starting MCP News Bot (polling every {poll_interval}s)...")

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
    parser = argparse.ArgumentParser(description="MCP News Bot for Zulip")
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

    bot = MCPNewsBot(str(config_path))

    if args.check_once:
        bot.check_all_sources()
        print("Single check completed!")
        sys.exit(0)

    bot.run()


if __name__ == "__main__":
    main()
