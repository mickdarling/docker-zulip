#!/usr/bin/env python3
"""
YouTube News Bot for Zulip

Monitors YouTube for videos related to MCP, AI agents, and related topics,
then posts updates to a Zulip channel.
"""

import sys
import time
import argparse
import urllib.request
import urllib.parse
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Add parent directory to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.base_bot import BaseNewsBot


class YouTubeNewsBot(BaseNewsBot):
    """Bot that monitors YouTube for relevant videos and posts to Zulip."""

    YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
    YOUTUBE_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"

    def __init__(self, config_path: str):
        super().__init__(config_path, bot_name="youtube_news_bot")
        self.api_key = self.config.get("sources", {}).get("youtube_api", {}).get("api_key", "")

    def check_all_sources(self):
        """Check all configured YouTube sources."""
        self.logger.info("Checking YouTube for new videos...")

        sources = self.config.get("sources", {})

        if sources.get("youtube_api", {}).get("enabled", False):
            if not self.api_key:
                self.logger.warning("YouTube API key not configured. Set YOUTUBE_API_KEY environment variable.")
                return
            self.check_youtube_api()

    def check_youtube_api(self):
        """Search YouTube API for videos matching queries."""
        api_config = self.config["sources"]["youtube_api"]
        queries = api_config.get("queries", [])
        max_results = api_config.get("max_results", 25)
        max_age_hours = api_config.get("max_age_hours", 168)

        # Calculate publishedAfter date
        published_after = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        published_after_str = published_after.strftime("%Y-%m-%dT%H:%M:%SZ")

        for query in queries:
            try:
                self._search_youtube(query, max_results, published_after_str, max_age_hours)
                # Rate limiting between queries (YouTube quota is limited)
                time.sleep(2)
            except Exception as e:
                self.logger.error(f"Error searching YouTube for '{query}': {e}")

    def _search_youtube(self, query: str, max_results: int, published_after: str, max_age_hours: int):
        """Execute a YouTube search and process results."""
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "order": "date",
            "maxResults": max_results,
            "publishedAfter": published_after,
            "key": self.api_key,
        }

        url = f"{self.YOUTUBE_SEARCH_URL}?{urllib.parse.urlencode(params)}"
        self.logger.debug(f"Searching YouTube: {query}")

        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                data = json.loads(response.read())
        except urllib.error.HTTPError as e:
            if e.code == 403:
                self.logger.error(f"YouTube API quota exceeded or API key invalid: {e}")
                return
            raise

        for item in data.get("items", []):
            try:
                self._process_video(item, query, max_age_hours)
            except Exception as e:
                self.logger.error(f"Error processing video: {e}")

    def _process_video(self, item: dict, search_query: str, max_age_hours: int):
        """Process a single YouTube video result."""
        video_id = item.get("id", {}).get("videoId")
        if not video_id:
            return

        snippet = item.get("snippet", {})
        title = snippet.get("title", "")
        channel_title = snippet.get("channelTitle", "")
        description = snippet.get("description", "")
        published_at_str = snippet.get("publishedAt", "")
        thumbnail = snippet.get("thumbnails", {}).get("high", {}).get("url", "")

        # Create unique ID
        item_id = f"youtube_{video_id}"

        if self.is_seen(item_id):
            return

        # Parse and check publish date
        if published_at_str:
            try:
                published_at = datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
                if self.is_too_old(published_at, max_age_hours):
                    self.mark_seen(item_id)
                    return
                date_str = published_at.strftime('%Y-%m-%d')
            except Exception:
                date_str = "Unknown"
        else:
            date_str = "Unknown"

        # Categorize
        category = self._categorize_item(title, description)

        # Build video URL
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        # Format message
        content = (
            f"**YouTube: {title}**\n"
            f"**Channel:** {channel_title}\n"
            f"**Published:** {date_str}\n"
            f"**Search Term:** {search_query}\n"
            f"**URL:** {video_url}\n"
        )

        if description:
            # Truncate description
            desc_preview = description[:300]
            if len(description) > 300:
                desc_preview += "..."
            content += f"\n**Description:**\n{desc_preview}"

        self._post_to_zulip(category, content)
        self.mark_seen(item_id)

        # Small delay between posts
        time.sleep(1)


def main():
    parser = argparse.ArgumentParser(description="YouTube News Bot for Zulip")
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

    bot = YouTubeNewsBot(str(config_path))

    if args.check_once:
        bot.run_once()
    else:
        bot.run()


if __name__ == "__main__":
    main()
