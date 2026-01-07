#!/usr/bin/env python3
"""
Base class for Zulip news bots.

Provides common functionality for:
- Configuration loading (YAML with env var expansion)
- Logging setup
- Zulip client creation
- Seen items tracking (deduplication)
- Keyword matching and categorization
- Posting to Zulip
"""

import os
import json
import logging
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Set, Optional
from abc import ABC, abstractmethod

import yaml
import zulip
from dotenv import load_dotenv


class BaseNewsBot(ABC):
    """Base class for news aggregator bots."""

    def __init__(self, config_path: str, bot_name: str = "news_bot"):
        """
        Initialize the bot.

        Args:
            config_path: Path to the YAML configuration file
            bot_name: Name for logging purposes
        """
        self.bot_name = bot_name
        self.script_dir = Path(config_path).parent

        # Load .env from script directory
        load_dotenv(self.script_dir / ".env")

        self.config = self._load_config(config_path)
        self._setup_logging()
        self.logger = logging.getLogger(bot_name)
        self.zulip_client = self._create_zulip_client()
        self.seen_items = self._load_seen_items()

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file with env var expansion."""
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        # Expand environment variables in zulip config
        if "zulip" in config:
            for key in ["api_key", "email", "site"]:
                value = config["zulip"].get(key, "")
                if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                    env_var = value[2:-1]
                    config["zulip"][key] = os.environ.get(env_var, "")

        # Expand env vars in sources config
        if "sources" in config:
            config["sources"] = self._expand_env_vars(config["sources"])

        return config

    def _expand_env_vars(self, obj):
        """Recursively expand environment variables in config."""
        if isinstance(obj, dict):
            return {k: self._expand_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._expand_env_vars(item) for item in obj]
        elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
            env_var = obj[2:-1]
            return os.environ.get(env_var, "")
        return obj

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

        required_keys = ["email", "api_key", "site"]
        if not all(k in zulip_config and zulip_config[k] for k in required_keys):
            raise ValueError(f"Missing required Zulip configuration: {required_keys}")

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
                json.dump({
                    "items": items_to_save,
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }, f, indent=2)
            self.logger.debug(f"Saved {len(items_to_save)} seen items to disk")
        except Exception as e:
            self.logger.error(f"Failed to save seen items: {e}")

    def _matches_keywords(self, text: str, keywords: List[str]) -> bool:
        """Check if text matches any of the keywords (case-insensitive)."""
        if not text or not keywords:
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
            if keywords and self._matches_keywords(combined, keywords):
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

    def is_too_old(self, timestamp: datetime, max_age_hours: int) -> bool:
        """Check if a timestamp is older than the max age."""
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        hours_old = (datetime.now(timezone.utc) - timestamp).total_seconds() / 3600
        return hours_old > max_age_hours

    def mark_seen(self, item_id: str):
        """Mark an item as seen."""
        self.seen_items.add(item_id)

    def is_seen(self, item_id: str) -> bool:
        """Check if an item has been seen."""
        return item_id in self.seen_items

    @abstractmethod
    def check_all_sources(self):
        """Check all configured sources. Must be implemented by subclasses."""
        pass

    def run(self):
        """Main loop - poll sources and post to Zulip."""
        poll_interval = self.config.get("poll_interval_seconds", 3600)
        self.logger.info(f"Starting {self.bot_name} (polling every {poll_interval}s)...")

        # Log enabled sources
        sources = self.config.get("sources", {})
        for source_name, source_config in sources.items():
            if isinstance(source_config, dict) and source_config.get("enabled", False):
                self.logger.info(f"Monitoring source: {source_name}")

        while True:
            try:
                self.check_all_sources()
                self._save_seen_items()
            except Exception as e:
                self.logger.error(f"Error during source check: {e}")

            self.logger.info(f"Sleeping for {poll_interval} seconds...")
            time.sleep(poll_interval)

    def run_once(self):
        """Check sources once and exit (for testing)."""
        self.logger.info(f"Running single check for {self.bot_name}...")
        self.check_all_sources()
        self._save_seen_items()
        self.logger.info("Single check completed!")
