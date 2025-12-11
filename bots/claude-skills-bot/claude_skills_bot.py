#!/usr/bin/env python3
"""
Claude Skills Bot for Zulip

Monitors web sources specifically for news about Anthropic's "Agent Skills" / "Claude Skills" feature.
This bot uses strict filtering to avoid generic "skills" articles (job skills, learning skills, etc.)
and focuses only on Anthropic/Claude's AI capabilities feature.

Context: Tracking potential AGPL attribution issues related to "Dollhouse Skills" project.
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


class ClaudeSkillsBot:
    """Bot that monitors web sources for Anthropic Agent Skills news and posts to Zulip."""

    def __init__(self, config_path: str):
        self.script_dir = Path(__file__).parent
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.logger = logging.getLogger("claude_skills_bot")
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

    def _is_relevant_skills_article(self, title: str, body: str = "") -> bool:
        """
        Strict filtering: ONLY include articles that mention BOTH:
        1. Anthropic OR Claude (the company/product)
        2. AND skills/agent skills in the context of AI capabilities

        EXCLUDE generic articles about:
        - Job skills, learning skills, human skills
        - Resumes/careers
        - Generic AI assistant capabilities without specific "skills" feature mention
        """
        combined = f"{title} {body}".lower()

        # Must mention Anthropic or Claude (as a product, not as a name)
        has_anthropic = any(term in combined for term in [
            "anthropic",
            "claude's",  # possessive implies the product
            "claude ai",
            "claude 3",
            "claude 4",
            "claude opus",
            "claude sonnet",
            "claude haiku",
        ])

        # Also check if "claude" appears near AI-related terms
        if not has_anthropic and "claude" in combined:
            ai_context = any(term in combined for term in [
                "ai", "agent", "skill", "workflow", "llm", "model", "chatbot", "assistant"
            ])
            if ai_context:
                has_anthropic = True

        if not has_anthropic:
            self.logger.debug(f"Filtered out - no Anthropic/Claude mention: {title}")
            return False

        # Must mention skills in AI context - be more permissive
        has_skills_mention = any(term in combined for term in [
            "agent skills",
            "claude skills",
            "custom skills",
            "ai skills",
            "skill system",
            "skills feature",
            "skills api",
            "skills framework",
            "skills for claude",
            "skills to claude",
            " skills",  # space before to catch "new skills", "mad skills", etc.
        ])

        if not has_skills_mention:
            self.logger.debug(f"Filtered out - no relevant skills mention: {title}")
            return False

        # Exclude generic job/career/learning content
        job_related = any(term in combined for term in [
            "job opening",
            "job posting",
            "career",
            "hiring",
            "resume",
            "cv ",
            "employment",
            "learn skills",
            "skill development",
            "professional skills",
            "soft skills",
            "hard skills",
            "technical skills interview",
            "job skills",
        ])

        if job_related:
            self.logger.debug(f"Filtered out - job/career related: {title}")
            return False

        # Additional quality filters - exclude if title is too generic
        generic_patterns = [
            "10 skills",
            "5 skills",
            "essential skills",
            "must-have skills",
            "skills you need",
            "skills to learn",
            "top skills",
            "best skills",
        ]

        title_lower = title.lower()
        if any(pattern in title_lower for pattern in generic_patterns):
            self.logger.debug(f"Filtered out - generic skills article: {title}")
            return False

        return True

    def _post_to_zulip(self, content: str):
        """Post news item to Zulip."""
        zulip_config = self.config.get("zulip", {})
        stream = zulip_config.get("stream", "claude-skills-watch")
        topic = zulip_config.get("topic", "News & Updates")

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

    def check_google_news(self):
        """Check Google News RSS feed for configured search terms."""
        if not self.config.get("sources", {}).get("google_news", {}).get("enabled", False):
            return

        google_config = self.config["sources"]["google_news"]
        search_queries = google_config.get("search_queries", [])

        for query in search_queries:
            try:
                # Google News RSS feed for search term
                import urllib.parse
                encoded_query = urllib.parse.quote(query)
                url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"

                self.logger.info(f"Checking Google News for: {query}")
                response = requests.get(url, timeout=10)
                response.raise_for_status()

                # Parse RSS feed
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.content)

                # Google News RSS uses standard RSS 2.0 format
                for item in root.findall(".//item"):
                    title_elem = item.find("title")
                    link_elem = item.find("link")
                    pub_date_elem = item.find("pubDate")
                    description_elem = item.find("description")

                    if title_elem is None or link_elem is None:
                        continue

                    title = title_elem.text
                    link = link_elem.text
                    description = description_elem.text if description_elem is not None else ""

                    # Create unique ID
                    news_id = f"google_news_{hash(link)}"

                    if news_id in self.seen_items:
                        continue

                    # STRICT FILTERING - must pass relevance check
                    if not self._is_relevant_skills_article(title, description):
                        self.seen_items.add(news_id)
                        continue

                    # Parse publication date
                    if pub_date_elem is not None:
                        pub_date_str = pub_date_elem.text
                        try:
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

                    # Format message with legal context
                    content = (
                        f"**NEW: {title}**\n"
                        f"**Search Query:** `{query}`\n"
                        f"**Published:** {date_str}\n"
                        f"**URL:** {link}\n\n"
                        f"_Tracking Anthropic's Agent Skills feature for potential AGPL attribution issues._"
                    )

                    self.logger.info(f"POSTING: {title}")
                    self._post_to_zulip(content)
                    self.seen_items.add(news_id)

                    # Rate limiting
                    time.sleep(2)

                # Delay between searches
                time.sleep(1)

            except Exception as e:
                self.logger.error(f"Error checking Google News for '{query}': {e}")

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
                self.logger.info(f"Checking Hacker News for: {keyword}")
                params = {
                    "query": keyword,
                    "tags": "story",
                    "hitsPerPage": 20,  # Get more hits since we're filtering heavily
                }

                response = requests.get(base_url, params=params, timeout=10)
                response.raise_for_status()

                data = response.json()

                for hit in data.get("hits", []):
                    story_id = f"hn_story_{hit['objectID']}"

                    if story_id in self.seen_items:
                        continue

                    title = hit.get("title", "")

                    # STRICT FILTERING - must pass relevance check
                    # For HN, we don't have body text, so just use title
                    if not self._is_relevant_skills_article(title, ""):
                        self.seen_items.add(story_id)
                        continue

                    # Check age
                    created_at_str = hit["created_at"]
                    try:
                        created_at = datetime.strptime(created_at_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
                    except ValueError:
                        created_at = datetime.strptime(created_at_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                    hours_old = (datetime.now(timezone.utc) - created_at).total_seconds() / 3600

                    max_age_hours = hn_config.get("max_age_hours", 168)
                    if hours_old > max_age_hours:
                        self.seen_items.add(story_id)
                        continue

                    # Format message
                    url = hit.get("url", f"https://news.ycombinator.com/item?id={hit['objectID']}")
                    points = hit.get("points", 0)
                    num_comments = hit.get("num_comments", 0)

                    content = (
                        f"**NEW: {title}**\n"
                        f"**Source:** Hacker News\n"
                        f"**Score:** {points} points | {num_comments} comments\n"
                        f"**Posted:** {created_at.strftime('%Y-%m-%d %H:%M UTC')}\n"
                        f"**URL:** {url}\n"
                        f"**Discussion:** https://news.ycombinator.com/item?id={hit['objectID']}\n\n"
                        f"_Tracking Anthropic's Agent Skills feature for potential AGPL attribution issues._"
                    )

                    self.logger.info(f"POSTING: {title}")
                    self._post_to_zulip(content)
                    self.seen_items.add(story_id)

                    # Rate limiting
                    time.sleep(2)

                # Delay between keyword searches
                time.sleep(1)

        except Exception as e:
            self.logger.error(f"Error checking Hacker News: {e}")

    def check_anthropic_site(self):
        """Check Anthropic's website for skills-related content using site: search."""
        if not self.config.get("sources", {}).get("anthropic_site", {}).get("enabled", False):
            return

        site_config = self.config["sources"]["anthropic_site"]

        try:
            # Use Google News RSS with site: operator
            import urllib.parse
            query = "site:anthropic.com skills"
            encoded_query = urllib.parse.quote(query)
            url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"

            self.logger.info(f"Checking Anthropic site for skills mentions")
            response = requests.get(url, timeout=10)
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
                description = description_elem.text if description_elem is not None else ""

                # Create unique ID
                news_id = f"anthropic_site_{hash(link)}"

                if news_id in self.seen_items:
                    continue

                # For anthropic.com content, we're more lenient but still filter
                if not self._is_relevant_skills_article(title, description):
                    self.seen_items.add(news_id)
                    continue

                # Parse publication date
                if pub_date_elem is not None:
                    pub_date_str = pub_date_elem.text
                    try:
                        from email.utils import parsedate_to_datetime
                        pub_date = parsedate_to_datetime(pub_date_str)
                        hours_old = (datetime.now(timezone.utc) - pub_date).total_seconds() / 3600

                        max_age_hours = site_config.get("max_age_hours", 168)
                        if hours_old > max_age_hours:
                            self.seen_items.add(news_id)
                            continue

                        date_str = pub_date.strftime('%Y-%m-%d %H:%M UTC')
                    except Exception as e:
                        self.logger.warning(f"Failed to parse date: {e}")
                        date_str = "Unknown"
                else:
                    date_str = "Unknown"

                content = (
                    f"**ANTHROPIC.COM UPDATE: {title}**\n"
                    f"**Published:** {date_str}\n"
                    f"**URL:** {link}\n\n"
                    f"_Direct content from Anthropic's website mentioning skills._"
                )

                self.logger.info(f"POSTING: {title}")
                self._post_to_zulip(content)
                self.seen_items.add(news_id)

                # Rate limiting
                time.sleep(2)

        except Exception as e:
            self.logger.error(f"Error checking Anthropic site: {e}")

    def check_all_sources(self):
        """Check all configured sources for new content."""
        self.logger.info("Checking all sources for Claude Skills news...")

        try:
            self.check_google_news()
            self.check_hackernews()
            self.check_anthropic_site()

            # Save seen items after each check cycle
            self._save_seen_items()

        except Exception as e:
            self.logger.error(f"Error during source check: {e}")

    def run(self):
        """Main loop - poll sources and post to Zulip."""
        poll_interval = self.config.get("poll_interval_seconds", 3600)
        self.logger.info(f"Starting Claude Skills Bot (polling every {poll_interval}s)...")
        self.logger.info("STRICT FILTERING ENABLED: Only Anthropic/Claude + Skills mentions")

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
    parser = argparse.ArgumentParser(description="Claude Skills Bot for Zulip")
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

    bot = ClaudeSkillsBot(str(config_path))

    if args.check_once:
        bot.check_all_sources()
        print("Single check completed!")
        sys.exit(0)

    bot.run()


if __name__ == "__main__":
    main()
