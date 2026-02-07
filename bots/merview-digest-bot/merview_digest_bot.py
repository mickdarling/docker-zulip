#!/usr/bin/env python3
"""
Merview Weekly Digest Bot for Zulip

Generates a weekly summary of Merview activity including GitHub stats,
news mentions, and Zulip discussions. Formatted for easy adaptation to LinkedIn posts.
"""

import os
import sys
import json
import logging
import argparse
import requests
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

import yaml
import zulip
from dotenv import load_dotenv

# Load .env file from script directory
load_dotenv(Path(__file__).parent / ".env")


class MerviewDigestBot:
    """Bot that generates weekly digests of Merview activity."""

    def __init__(self, config_path: str):
        self.script_dir = Path(__file__).parent
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.logger = logging.getLogger("merview_digest_bot")
        self.zulip_client = self._create_zulip_client()
        self.github_token = os.environ.get("GITHUB_TOKEN")

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

    def _get_week_range(self, date_str: Optional[str] = None) -> Tuple[datetime, datetime]:
        """
        Get start and end of week.

        Args:
            date_str: Optional date string in YYYY-MM-DD format. If not provided, uses current week.

        Returns:
            Tuple of (start_date, end_date) as datetime objects with UTC timezone.
        """
        if date_str:
            end_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        else:
            end_date = datetime.now(timezone.utc)

        # Go back to start of week (Monday)
        start_date = end_date - timedelta(days=end_date.weekday(), hours=end_date.hour,
                                          minutes=end_date.minute, seconds=end_date.second,
                                          microseconds=end_date.microsecond)

        # Set end to end of Sunday
        days_until_sunday = 6 - end_date.weekday()
        end_date = end_date + timedelta(days=days_until_sunday)
        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        return start_date, end_date

    def _fetch_github_stats(self, start_date: datetime, end_date: datetime) -> Dict:
        """Fetch GitHub statistics for configured repositories."""
        stats = {
            "repos": [],
            "total_stars": 0,
            "total_forks": 0,
            "total_releases": 0,
            "total_prs_merged": 0,
            "total_issues_closed": 0,
            "contributors": set(),
            "releases": [],
            "top_prs": [],
            "top_issues": [],
        }

        github_config = self.config.get("github", {})
        repos = github_config.get("repos", [])

        headers = {"Accept": "application/vnd.github.v3+json"}
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"

        for repo in repos:
            try:
                self.logger.info(f"Fetching GitHub stats for {repo}")

                # Get repo info
                repo_url = f"https://api.github.com/repos/{repo}"
                response = requests.get(repo_url, headers=headers, timeout=10)
                response.raise_for_status()
                repo_data = response.json()

                repo_stats = {
                    "name": repo,
                    "stars": repo_data.get("stargazers_count", 0),
                    "forks": repo_data.get("forks_count", 0),
                    "open_issues": repo_data.get("open_issues_count", 0),
                }

                stats["total_stars"] += repo_stats["stars"]
                stats["total_forks"] += repo_stats["forks"]

                # Get releases in date range
                releases_url = f"https://api.github.com/repos/{repo}/releases"
                response = requests.get(releases_url, headers=headers, timeout=10)
                response.raise_for_status()
                releases = response.json()

                for release in releases:
                    published_at = datetime.strptime(
                        release["published_at"], "%Y-%m-%dT%H:%M:%SZ"
                    ).replace(tzinfo=timezone.utc)

                    if start_date <= published_at <= end_date:
                        stats["total_releases"] += 1
                        stats["releases"].append({
                            "repo": repo,
                            "name": release["name"],
                            "tag": release["tag_name"],
                            "url": release["html_url"],
                            "published_at": published_at,
                        })

                # Get merged PRs in date range
                # Using search API for better filtering
                query = f"repo:{repo} is:pr is:merged merged:{start_date.strftime('%Y-%m-%d')}..{end_date.strftime('%Y-%m-%d')}"
                search_url = f"https://api.github.com/search/issues?q={query}&sort=updated&per_page=100"
                response = requests.get(search_url, headers=headers, timeout=10)
                response.raise_for_status()
                prs_data = response.json()

                pr_count = prs_data.get("total_count", 0)
                stats["total_prs_merged"] += pr_count

                for pr in prs_data.get("items", [])[:5]:  # Top 5 PRs
                    stats["top_prs"].append({
                        "repo": repo,
                        "title": pr["title"],
                        "url": pr["html_url"],
                        "user": pr["user"]["login"],
                        "comments": pr.get("comments", 0),
                    })
                    stats["contributors"].add(pr["user"]["login"])

                # Get closed issues in date range
                query = f"repo:{repo} is:issue is:closed closed:{start_date.strftime('%Y-%m-%d')}..{end_date.strftime('%Y-%m-%d')}"
                search_url = f"https://api.github.com/search/issues?q={query}&sort=updated&per_page=100"
                response = requests.get(search_url, headers=headers, timeout=10)
                response.raise_for_status()
                issues_data = response.json()

                issue_count = issues_data.get("total_count", 0)
                stats["total_issues_closed"] += issue_count

                for issue in issues_data.get("items", [])[:5]:  # Top 5 issues
                    stats["top_issues"].append({
                        "repo": repo,
                        "title": issue["title"],
                        "url": issue["html_url"],
                        "user": issue["user"]["login"],
                    })

                stats["repos"].append(repo_stats)

            except Exception as e:
                self.logger.error(f"Error fetching GitHub stats for {repo}: {e}")

        return stats

    def _fetch_news_items(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Fetch news items from merview-news-bot's seen items or Zulip messages."""
        news_items = []

        # Try to read from news bot's seen_items.json
        news_bot_path = self.script_dir.parent / "merview-news-bot" / "seen_items.json"
        if news_bot_path.exists():
            try:
                with open(news_bot_path, "r") as f:
                    data = json.load(f)
                    # If the seen_items structure includes timestamps and data
                    if isinstance(data, dict) and "items_with_data" in data:
                        for item in data["items_with_data"]:
                            if "timestamp" in item:
                                item_time = datetime.fromisoformat(item["timestamp"])
                                if start_date <= item_time <= end_date:
                                    news_items.append(item)
            except Exception as e:
                self.logger.warning(f"Could not read news bot data: {e}")

        # Also query Zulip news stream for messages in date range
        try:
            request = {
                "anchor": "newest",
                "num_before": 1000,
                "num_after": 0,
                "narrow": [
                    {"operator": "stream", "operand": "news"},
                ],
            }
            result = self.zulip_client.get_messages(request)

            if result["result"] == "success":
                for msg in result["messages"]:
                    msg_time = datetime.fromtimestamp(msg["timestamp"], tz=timezone.utc)
                    if start_date <= msg_time <= end_date:
                        news_items.append({
                            "title": msg["subject"],
                            "content": msg["content"],
                            "url": f"{self.config['zulip']['site']}/#narrow/stream/{msg['stream_id']}/topic/{msg['subject']}/near/{msg['id']}",
                            "timestamp": msg_time.isoformat(),
                        })
        except Exception as e:
            self.logger.warning(f"Could not fetch Zulip news messages: {e}")

        return news_items

    def _fetch_zulip_activity(self, start_date: datetime, end_date: datetime) -> Dict:
        """Fetch Zulip discussion activity summary."""
        activity = {
            "total_messages": 0,
            "active_streams": defaultdict(int),
            "top_topics": [],
            "active_users": set(),
        }

        streams_to_monitor = self.config.get("zulip_monitoring", {}).get("streams", [])

        for stream in streams_to_monitor:
            try:
                request = {
                    "anchor": "newest",
                    "num_before": 1000,
                    "num_after": 0,
                    "narrow": [
                        {"operator": "stream", "operand": stream},
                    ],
                }
                result = self.zulip_client.get_messages(request)

                if result["result"] == "success":
                    topic_counts = defaultdict(int)

                    for msg in result["messages"]:
                        msg_time = datetime.fromtimestamp(msg["timestamp"], tz=timezone.utc)
                        if start_date <= msg_time <= end_date:
                            activity["total_messages"] += 1
                            activity["active_streams"][stream] += 1
                            topic_counts[msg["subject"]] += 1
                            activity["active_users"].add(msg["sender_full_name"])

                    # Get top topics for this stream
                    for topic, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:3]:
                        activity["top_topics"].append({
                            "stream": stream,
                            "topic": topic,
                            "messages": count,
                        })

            except Exception as e:
                self.logger.warning(f"Could not fetch activity for stream {stream}: {e}")

        return activity

    def _format_digest(self, start_date: datetime, end_date: datetime,
                      github_stats: Dict, news_items: List[Dict],
                      zulip_activity: Dict) -> Tuple[str, str]:
        """
        Format the digest for Zulip posting and LinkedIn adaptation.

        Returns:
            Tuple of (zulip_content, linkedin_draft)
        """
        week_str = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"

        # Full Zulip digest
        zulip_content = f"# Merview Weekly Digest: {week_str}\n\n"

        # GitHub Summary
        zulip_content += "## GitHub Activity\n\n"

        if github_stats["total_releases"] > 0:
            zulip_content += f"### Releases ({github_stats['total_releases']})\n"
            for release in github_stats["releases"]:
                zulip_content += f"- **{release['repo']}** [{release['name']}]({release['url']}) - {release['published_at'].strftime('%b %d')}\n"
            zulip_content += "\n"

        if github_stats["total_prs_merged"] > 0:
            zulip_content += f"### Development\n"
            zulip_content += f"- **{github_stats['total_prs_merged']}** pull requests merged\n"
            zulip_content += f"- **{github_stats['total_issues_closed']}** issues closed\n"
            zulip_content += f"- **{len(github_stats['contributors'])}** active contributors\n\n"

            if github_stats["top_prs"]:
                zulip_content += "**Notable PRs:**\n"
                for pr in github_stats["top_prs"][:3]:
                    zulip_content += f"- [{pr['title']}]({pr['url']}) by @{pr['user']}\n"
                zulip_content += "\n"

        if github_stats["repos"]:
            zulip_content += f"### Repository Stats\n"
            for repo_stat in github_stats["repos"]:
                zulip_content += f"- **{repo_stat['name']}**: {repo_stat['stars']} stars, {repo_stat['forks']} forks\n"
            zulip_content += f"\n**Total across all repos:** {github_stats['total_stars']} stars, {github_stats['total_forks']} forks\n\n"

        # News & Mentions
        if news_items:
            zulip_content += f"## News & Mentions ({len(news_items)})\n\n"
            for item in news_items[:10]:  # Top 10 news items
                title = item.get("title", "Untitled")
                url = item.get("url", "")
                zulip_content += f"- [{title}]({url})\n"
            zulip_content += "\n"

        # Community Activity
        if zulip_activity["total_messages"] > 0:
            zulip_content += f"## Community Activity\n\n"
            zulip_content += f"- **{zulip_activity['total_messages']}** messages across {len(zulip_activity['active_streams'])} streams\n"
            zulip_content += f"- **{len(zulip_activity['active_users'])}** active community members\n\n"

            if zulip_activity["top_topics"]:
                zulip_content += "**Most Active Discussions:**\n"
                for topic in zulip_activity["top_topics"][:5]:
                    zulip_content += f"- **#{topic['stream']}** > {topic['topic']} ({topic['messages']} messages)\n"
                zulip_content += "\n"

        # LinkedIn Draft
        linkedin_draft = f"---\n\n## LinkedIn Draft\n\n"
        linkedin_draft += f"Weekly Update: {week_str}\n\n"

        highlights = []

        if github_stats["total_releases"] > 0:
            release_names = ", ".join([r["name"] for r in github_stats["releases"][:2]])
            highlights.append(f"Released {release_names}")

        if github_stats["total_prs_merged"] > 0:
            highlights.append(f"{github_stats['total_prs_merged']} PRs merged with {len(github_stats['contributors'])} contributors")

        if github_stats["total_issues_closed"] > 0:
            highlights.append(f"{github_stats['total_issues_closed']} issues resolved")

        if news_items:
            highlights.append(f"{len(news_items)} news mentions")

        if zulip_activity["total_messages"] > 0:
            highlights.append(f"{len(zulip_activity['active_users'])} active community members")

        if highlights:
            linkedin_draft += "This week at Merview:\n"
            for highlight in highlights[:5]:
                linkedin_draft += f"- {highlight}\n"
        else:
            linkedin_draft += "A quiet week as the team focuses on building.\n"

        linkedin_draft += "\n"
        linkedin_draft += "Want to learn more? Check out our GitHub or join our community.\n"
        linkedin_draft += "\n"
        linkedin_draft += "#Merview #OpenSource #WeeklyUpdate"

        return zulip_content + linkedin_draft, linkedin_draft

    def generate_digest(self, date_str: Optional[str] = None) -> bool:
        """
        Generate and post weekly digest.

        Args:
            date_str: Optional date string (YYYY-MM-DD) for specific week.
                     If not provided, generates digest for current week.

        Returns:
            True if digest was successfully posted, False otherwise.
        """
        try:
            start_date, end_date = self._get_week_range(date_str)
            week_str = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"

            self.logger.info(f"Generating digest for week of {week_str}")

            # Collect data
            github_stats = self._fetch_github_stats(start_date, end_date)
            news_items = self._fetch_news_items(start_date, end_date)
            zulip_activity = self._fetch_zulip_activity(start_date, end_date)

            # Format digest
            full_content, linkedin_draft = self._format_digest(
                start_date, end_date, github_stats, news_items, zulip_activity
            )

            # Post to Zulip
            stream = self.config["zulip"].get("digest_stream", "digest")
            topic = f"Week of {week_str}"

            request = {
                "type": "stream",
                "to": stream,
                "topic": topic,
                "content": full_content,
            }

            result = self.zulip_client.send_message(request)

            if result["result"] == "success":
                self.logger.info(f"Posted digest to #{stream} > {topic}")
                return True
            else:
                self.logger.error(f"Failed to post digest: {result}")
                return False

        except Exception as e:
            self.logger.error(f"Error generating digest: {e}", exc_info=True)
            return False

    def run(self, check_once: bool = False, date_str: Optional[str] = None):
        """
        Run the bot continuously or once.

        Args:
            check_once: If True, generate digest once and exit.
            date_str: Optional date string for specific week digest.
        """
        if check_once or date_str:
            self.logger.info("Running in single-check mode")
            success = self.generate_digest(date_str)
            sys.exit(0 if success else 1)

        # Continuous mode - run on schedule
        schedule_config = self.config.get("schedule", {})
        day = schedule_config.get("day", "sunday").lower()
        hour = schedule_config.get("hour", 18)

        self.logger.info(f"Running in scheduled mode: every {day} at {hour}:00")

        # Map day names to numbers (0=Monday, 6=Sunday)
        day_map = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }
        target_day = day_map.get(day, 6)

        last_run = None

        while True:
            now = datetime.now(timezone.utc)

            # Check if it's time to run
            is_target_day = now.weekday() == target_day
            is_target_hour = now.hour == hour

            # Only run once per day
            run_today = last_run is None or last_run.date() != now.date()

            if is_target_day and is_target_hour and run_today:
                self.logger.info(f"Scheduled digest time reached")
                self.generate_digest()
                last_run = now

            # Sleep for an hour before checking again
            import time
            time.sleep(3600)


def main():
    parser = argparse.ArgumentParser(
        description="Merview Weekly Digest Bot - Generate weekly activity summaries"
    )
    parser.add_argument(
        "--config",
        default=str(Path(__file__).parent / "config.yaml"),
        help="Path to configuration file",
    )
    parser.add_argument(
        "--check-once",
        action="store_true",
        help="Generate digest once and exit (for current week)",
    )
    parser.add_argument(
        "--date",
        help="Generate digest for specific week (YYYY-MM-DD format)",
    )

    args = parser.parse_args()

    bot = MerviewDigestBot(args.config)
    bot.run(check_once=args.check_once, date_str=args.date)


if __name__ == "__main__":
    main()
