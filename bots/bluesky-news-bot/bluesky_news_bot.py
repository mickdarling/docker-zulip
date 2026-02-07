#!/usr/bin/env python3
"""
Bluesky News Bot for Zulip

Monitors Bluesky (AT Protocol) for posts related to MCP, AI agents, and LLMs,
then posts updates to a Zulip channel.
"""

import sys
import time
import argparse
import urllib.request
import urllib.parse
import json
from pathlib import Path
from datetime import datetime, timezone

# Add parent directory to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.base_bot import BaseNewsBot


class BlueskyNewsBot(BaseNewsBot):
    """Bot that monitors Bluesky for relevant posts and posts to Zulip."""

    # Bluesky API endpoints
    PUBLIC_API_URL = "https://public.api.bsky.app"
    BSKY_API_URL = "https://bsky.social"

    def __init__(self, config_path: str):
        super().__init__(config_path, bot_name="bluesky_news_bot")
        self.access_token = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Bluesky using app password if credentials provided."""
        bluesky_config = self.config.get("sources", {}).get("bluesky_search", {})
        identifier = bluesky_config.get("identifier")
        app_password = bluesky_config.get("app_password")

        if not identifier or not app_password:
            self.logger.info("No Bluesky credentials provided, will try public API")
            return

        try:
            url = f"{self.BSKY_API_URL}/xrpc/com.atproto.server.createSession"
            data = json.dumps({
                "identifier": identifier,
                "password": app_password
            }).encode("utf-8")

            req = urllib.request.Request(url, data=data, method="POST")
            req.add_header("Content-Type", "application/json")
            req.add_header("User-Agent", "BlueskyNewsBot/1.0")

            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode())
                self.access_token = result.get("accessJwt")
                self.logger.info(f"Authenticated with Bluesky as {identifier}")

        except Exception as e:
            self.logger.warning(f"Failed to authenticate with Bluesky: {e}")
            self.logger.info("Will try public API without auth")

    def check_all_sources(self):
        """Check all configured Bluesky sources."""
        self.logger.info("Checking Bluesky for new posts...")

        sources = self.config.get("sources", {})

        if sources.get("bluesky_search", {}).get("enabled", False):
            self.check_bluesky_search()

    def check_bluesky_search(self):
        """Search Bluesky for posts matching queries."""
        search_config = self.config["sources"]["bluesky_search"]
        queries = search_config.get("queries", [])
        max_results = search_config.get("max_results", 25)
        max_age_hours = search_config.get("max_age_hours", 72)

        # Use authenticated API if we have a token, otherwise public API
        if self.access_token:
            base_url = f"{self.BSKY_API_URL}/xrpc/app.bsky.feed.searchPosts"
        else:
            base_url = f"{self.PUBLIC_API_URL}/xrpc/app.bsky.feed.searchPosts"

        for query in queries:
            try:
                # Build API query
                params = {
                    "q": query,
                    "limit": max_results,
                    "sort": "latest"
                }
                url = f"{base_url}?{urllib.parse.urlencode(params)}"

                self.logger.debug(f"Querying Bluesky: {query}")

                # Make request
                req = urllib.request.Request(url)
                req.add_header("Accept", "application/json")
                req.add_header("User-Agent", "BlueskyNewsBot/1.0 (Zulip integration)")

                # Add auth header if authenticated
                if self.access_token:
                    req.add_header("Authorization", f"Bearer {self.access_token}")

                with urllib.request.urlopen(req, timeout=30) as response:
                    data = json.loads(response.read().decode())

                posts = data.get("posts", [])
                self.logger.info(f"Found {len(posts)} posts for query: {query}")

                for post in posts:
                    self._process_post(post, max_age_hours, query)

                # Rate limiting between queries
                time.sleep(2)

            except urllib.error.HTTPError as e:
                self.logger.error(f"HTTP error querying Bluesky for '{query}': {e.code} {e.reason}")
                # If auth failed, try to re-authenticate
                if e.code == 401 and self.access_token:
                    self.logger.info("Token expired, re-authenticating...")
                    self._authenticate()
            except Exception as e:
                self.logger.error(f"Error querying Bluesky for '{query}': {e}")

    def _process_post(self, post: dict, max_age_hours: int, query: str):
        """Process a single Bluesky post."""
        try:
            # Extract post data
            uri = post.get("uri", "")
            cid = post.get("cid", "")
            author = post.get("author", {})
            record = post.get("record", {})
            indexed_at = post.get("indexedAt", "")

            # Create unique ID
            post_id = f"bluesky_{cid}" if cid else f"bluesky_{hash(uri)}"

            if self.is_seen(post_id):
                return

            # Check age
            if indexed_at:
                try:
                    # Parse ISO format
                    post_date = datetime.fromisoformat(indexed_at.replace("Z", "+00:00"))
                    if self.is_too_old(post_date, max_age_hours):
                        self.mark_seen(post_id)
                        return
                    date_display = post_date.strftime('%Y-%m-%d %H:%M UTC')
                except Exception:
                    date_display = "Unknown"
            else:
                date_display = "Unknown"

            # Get author info
            author_handle = author.get("handle", "unknown")
            author_display = author.get("displayName", author_handle)

            # Get post text
            text = record.get("text", "")
            if not text:
                return

            # Build web URL from URI
            # URI format: at://did:plc:xxx/app.bsky.feed.post/yyy
            # Web URL: https://bsky.app/profile/handle/post/yyy
            post_rkey = uri.split("/")[-1] if uri else ""
            web_url = f"https://bsky.app/profile/{author_handle}/post/{post_rkey}"

            # Get engagement stats
            like_count = post.get("likeCount", 0)
            repost_count = post.get("repostCount", 0)
            reply_count = post.get("replyCount", 0)

            # Categorize
            category = self._categorize_item(text)

            # Format message
            content = (
                f"**Bluesky: @{author_handle}**\n"
                f"**Author:** {author_display}\n"
                f"**Posted:** {date_display}\n"
                f"**URL:** {web_url}\n"
            )

            if like_count or repost_count or reply_count:
                content += f"**Engagement:** {like_count} likes, {repost_count} reposts, {reply_count} replies\n"

            # Truncate long posts
            if len(text) > 500:
                text = text[:500] + "..."
            content += f"\n{text}"

            self._post_to_zulip(category, content)
            self.mark_seen(post_id)

        except Exception as e:
            self.logger.error(f"Error processing Bluesky post: {e}")


def main():
    parser = argparse.ArgumentParser(description="Bluesky News Bot for Zulip")
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

    bot = BlueskyNewsBot(str(config_path))

    if args.check_once:
        bot.run_once()
    else:
        bot.run()


if __name__ == "__main__":
    main()
