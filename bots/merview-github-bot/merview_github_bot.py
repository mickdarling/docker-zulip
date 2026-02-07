#!/usr/bin/env python3
"""
Merview GitHub Bot for Zulip

Monitors GitHub repositories for activity and posts to Zulip.
Tracks releases, issues, PRs, stars, forks, and commits.
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
from typing import Dict, List, Set, Optional, Any

import yaml
import zulip
from dotenv import load_dotenv

# Load .env file from script directory
load_dotenv(Path(__file__).parent / ".env")


class GitHubBot:
    """Bot that monitors GitHub repositories and posts to Zulip."""

    def __init__(self, config_path: str):
        self.script_dir = Path(__file__).parent
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.logger = logging.getLogger("merview_github_bot")
        self.zulip_client = self._create_zulip_client()
        self.seen_items = self._load_seen_items()
        self.github_token = os.environ.get("GITHUB_TOKEN")

        # Track star milestones per repo
        self.star_milestones = self._load_star_milestones()

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
            # Keep only the most recent 5000 items to prevent unbounded growth
            items_to_save = list(self.seen_items)[-5000:]
            with open(seen_file, "w") as f:
                json.dump({
                    "items": items_to_save,
                    "star_milestones": self.star_milestones,
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }, f, indent=2)
            self.logger.debug(f"Saved {len(items_to_save)} seen items to disk")
        except Exception as e:
            self.logger.error(f"Failed to save seen items: {e}")

    def _load_star_milestones(self) -> Dict[str, int]:
        """Load last recorded star milestones for each repo."""
        seen_file = self.script_dir / "seen_items.json"
        if seen_file.exists():
            try:
                with open(seen_file, "r") as f:
                    data = json.load(f)
                    return data.get("star_milestones", {})
            except Exception as e:
                self.logger.warning(f"Failed to load star milestones: {e}")
        return {}

    def _get_github_headers(self) -> dict:
        """Get headers for GitHub API requests."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "MerviewGitHubBot/1.0"
        }
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
        return headers

    def _post_to_zulip(self, topic: str, content: str):
        """Post message to Zulip."""
        zulip_config = self.config.get("zulip", {})
        stream = zulip_config.get("stream", "github")

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

    def _get_star_milestone(self, stars: int) -> Optional[int]:
        """
        Determine if current star count is a milestone.
        Returns the milestone value if it is one, None otherwise.
        """
        milestones = self.config.get("events", {}).get("stars", {}).get("milestones", [])

        for milestone in milestones:
            if stars >= milestone and stars < milestone + 10:
                return milestone

        # Check for multiples of milestone values
        for milestone in [10, 50, 100, 500, 1000, 5000, 10000]:
            if stars % milestone == 0 or (stars >= milestone and stars < milestone + 10):
                return milestone

        return None

    def check_repository(self, repo: str):
        """Check a single repository for all configured events."""
        self.logger.info(f"Checking repository: {repo}")

        try:
            # Get basic repo info
            repo_url = f"https://api.github.com/repos/{repo}"
            response = requests.get(repo_url, headers=self._get_github_headers(), timeout=10)
            response.raise_for_status()
            repo_data = response.json()

            # Check each event type
            events = self.config.get("events", {})

            if events.get("releases", {}).get("enabled", True):
                self.check_releases(repo, repo_data)

            if events.get("issues", {}).get("enabled", True):
                self.check_issues(repo, repo_data)

            if events.get("pull_requests", {}).get("enabled", True):
                self.check_pull_requests(repo, repo_data)

            if events.get("stars", {}).get("enabled", True):
                self.check_stars(repo, repo_data)

            if events.get("forks", {}).get("enabled", True):
                self.check_forks(repo, repo_data)

            if events.get("commits", {}).get("enabled", True):
                self.check_commits(repo, repo_data)

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                self.logger.error(f"Repository not found: {repo}")
            elif e.response.status_code == 403:
                self.logger.error(f"Rate limit exceeded or access forbidden for {repo}")
            else:
                self.logger.error(f"HTTP error checking {repo}: {e}")
        except Exception as e:
            self.logger.error(f"Error checking repository {repo}: {e}")

    def check_releases(self, repo: str, repo_data: dict):
        """Check for new releases."""
        try:
            url = f"https://api.github.com/repos/{repo}/releases"
            response = requests.get(url, headers=self._get_github_headers(), timeout=10)
            response.raise_for_status()

            releases = response.json()
            max_age_hours = self.config.get("events", {}).get("releases", {}).get("max_age_hours", 168)

            for release in releases[:5]:  # Check last 5 releases
                release_id = f"release_{repo}_{release['id']}"

                if release_id in self.seen_items:
                    continue

                # Check age
                published_at = datetime.strptime(release["published_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                hours_old = (datetime.now(timezone.utc) - published_at).total_seconds() / 3600

                if hours_old > max_age_hours:
                    self.seen_items.add(release_id)
                    continue

                # Format message
                tag_name = release.get("tag_name", "")
                release_name = release.get("name", tag_name)
                author = release.get("author", {}).get("login", "unknown")
                body = release.get("body", "")

                # Truncate body if too long
                if body and len(body) > 500:
                    body = body[:500] + "..."

                content = (
                    f"**New Release: {release_name}**\n"
                    f"**Tag:** {tag_name}\n"
                    f"**Published by:** {author}\n"
                    f"**Date:** {published_at.strftime('%Y-%m-%d %H:%M UTC')}\n"
                    f"**URL:** {release['html_url']}\n"
                )

                if body:
                    content += f"\n**Release Notes:**\n{body}"

                topic = self.config.get("topic_format", "{repo}").format(repo=repo.split('/')[-1])
                self._post_to_zulip(topic, content)
                self.seen_items.add(release_id)

                time.sleep(1)

        except Exception as e:
            self.logger.error(f"Error checking releases for {repo}: {e}")

    def check_issues(self, repo: str, repo_data: dict):
        """Check for new issues."""
        try:
            url = f"https://api.github.com/repos/{repo}/issues"
            params = {"state": "open", "sort": "created", "direction": "desc", "per_page": 10}
            response = requests.get(url, headers=self._get_github_headers(), params=params, timeout=10)
            response.raise_for_status()

            issues = response.json()
            max_age_hours = self.config.get("events", {}).get("issues", {}).get("max_age_hours", 24)

            for issue in issues:
                # Skip pull requests (they show up in issues endpoint too)
                if "pull_request" in issue:
                    continue

                issue_id = f"issue_{repo}_{issue['id']}"

                if issue_id in self.seen_items:
                    continue

                # Check age
                created_at = datetime.strptime(issue["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                hours_old = (datetime.now(timezone.utc) - created_at).total_seconds() / 3600

                if hours_old > max_age_hours:
                    self.seen_items.add(issue_id)
                    continue

                # Format message
                title = issue.get("title", "")
                author = issue.get("user", {}).get("login", "unknown")
                labels = ", ".join([label["name"] for label in issue.get("labels", [])])
                body = issue.get("body", "")

                # Truncate body if too long
                if body and len(body) > 300:
                    body = body[:300] + "..."

                content = (
                    f"**New Issue #{issue['number']}: {title}**\n"
                    f"**Opened by:** {author}\n"
                    f"**Date:** {created_at.strftime('%Y-%m-%d %H:%M UTC')}\n"
                )

                if labels:
                    content += f"**Labels:** {labels}\n"

                content += f"**URL:** {issue['html_url']}\n"

                if body:
                    content += f"\n**Description:**\n{body}"

                topic = self.config.get("topic_format", "{repo}").format(repo=repo.split('/')[-1])
                self._post_to_zulip(topic, content)
                self.seen_items.add(issue_id)

                time.sleep(1)

        except Exception as e:
            self.logger.error(f"Error checking issues for {repo}: {e}")

    def check_pull_requests(self, repo: str, repo_data: dict):
        """Check for new and recently merged/closed pull requests."""
        try:
            # Check open PRs
            url = f"https://api.github.com/repos/{repo}/pulls"
            params = {"state": "open", "sort": "created", "direction": "desc", "per_page": 10}
            response = requests.get(url, headers=self._get_github_headers(), params=params, timeout=10)
            response.raise_for_status()

            prs = response.json()
            max_age_hours = self.config.get("events", {}).get("pull_requests", {}).get("max_age_hours", 24)

            for pr in prs:
                pr_id = f"pr_opened_{repo}_{pr['id']}"

                if pr_id in self.seen_items:
                    continue

                # Check age
                created_at = datetime.strptime(pr["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                hours_old = (datetime.now(timezone.utc) - created_at).total_seconds() / 3600

                if hours_old > max_age_hours:
                    self.seen_items.add(pr_id)
                    continue

                # Format message
                title = pr.get("title", "")
                author = pr.get("user", {}).get("login", "unknown")
                body = pr.get("body", "")

                # Truncate body if too long
                if body and len(body) > 300:
                    body = body[:300] + "..."

                content = (
                    f"**New Pull Request #{pr['number']}: {title}**\n"
                    f"**Opened by:** {author}\n"
                    f"**Date:** {created_at.strftime('%Y-%m-%d %H:%M UTC')}\n"
                    f"**URL:** {pr['html_url']}\n"
                )

                if body:
                    content += f"\n**Description:**\n{body}"

                topic = self.config.get("topic_format", "{repo}").format(repo=repo.split('/')[-1])
                self._post_to_zulip(topic, content)
                self.seen_items.add(pr_id)

                time.sleep(1)

            # Check recently closed PRs (to catch merged ones)
            params = {"state": "closed", "sort": "updated", "direction": "desc", "per_page": 10}
            response = requests.get(url, headers=self._get_github_headers(), params=params, timeout=10)
            response.raise_for_status()

            closed_prs = response.json()

            for pr in closed_prs:
                # Check if merged or just closed
                if pr.get("merged_at"):
                    pr_id = f"pr_merged_{repo}_{pr['id']}"
                    status = "merged"
                    date_field = "merged_at"
                else:
                    pr_id = f"pr_closed_{repo}_{pr['id']}"
                    status = "closed"
                    date_field = "closed_at"

                if pr_id in self.seen_items:
                    continue

                # Check age
                if pr.get(date_field):
                    action_date = datetime.strptime(pr[date_field], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                    hours_old = (datetime.now(timezone.utc) - action_date).total_seconds() / 3600

                    if hours_old > max_age_hours:
                        self.seen_items.add(pr_id)
                        continue

                    date_str = action_date.strftime('%Y-%m-%d %H:%M UTC')
                else:
                    continue

                # Format message
                title = pr.get("title", "")
                author = pr.get("user", {}).get("login", "unknown")

                content = (
                    f"**Pull Request {status.capitalize()} #{pr['number']}: {title}**\n"
                    f"**Author:** {author}\n"
                    f"**{status.capitalize()}:** {date_str}\n"
                    f"**URL:** {pr['html_url']}"
                )

                topic = self.config.get("topic_format", "{repo}").format(repo=repo.split('/')[-1])
                self._post_to_zulip(topic, content)
                self.seen_items.add(pr_id)

                time.sleep(1)

        except Exception as e:
            self.logger.error(f"Error checking pull requests for {repo}: {e}")

    def check_stars(self, repo: str, repo_data: dict):
        """Check for star milestones."""
        try:
            current_stars = repo_data.get("stargazers_count", 0)
            last_milestone = self.star_milestones.get(repo, 0)

            # Get milestone configuration
            milestones = self.config.get("events", {}).get("stars", {}).get("milestones", [])

            # Check if we've hit a new milestone
            for milestone in sorted(milestones):
                if current_stars >= milestone and last_milestone < milestone:
                    # New milestone!
                    milestone_id = f"stars_{repo}_{milestone}"

                    if milestone_id not in self.seen_items:
                        content = (
                            f"**Star Milestone Reached!**\n"
                            f"**Repository:** {repo}\n"
                            f"**Stars:** {current_stars} :star:\n"
                            f"**Milestone:** {milestone}\n"
                            f"**URL:** {repo_data['html_url']}"
                        )

                        topic = self.config.get("topic_format", "{repo}").format(repo=repo.split('/')[-1])
                        self._post_to_zulip(topic, content)
                        self.seen_items.add(milestone_id)
                        self.star_milestones[repo] = milestone

                        time.sleep(1)

        except Exception as e:
            self.logger.error(f"Error checking stars for {repo}: {e}")

    def check_forks(self, repo: str, repo_data: dict):
        """Check for new forks."""
        try:
            url = f"https://api.github.com/repos/{repo}/forks"
            params = {"sort": "newest", "per_page": 5}
            response = requests.get(url, headers=self._get_github_headers(), params=params, timeout=10)
            response.raise_for_status()

            forks = response.json()
            max_age_hours = self.config.get("events", {}).get("forks", {}).get("max_age_hours", 24)

            for fork in forks:
                fork_id = f"fork_{repo}_{fork['id']}"

                if fork_id in self.seen_items:
                    continue

                # Check age
                created_at = datetime.strptime(fork["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                hours_old = (datetime.now(timezone.utc) - created_at).total_seconds() / 3600

                if hours_old > max_age_hours:
                    self.seen_items.add(fork_id)
                    continue

                # Format message
                owner = fork.get("owner", {}).get("login", "unknown")

                content = (
                    f"**New Fork**\n"
                    f"**Repository:** {repo}\n"
                    f"**Forked by:** {owner}\n"
                    f"**Date:** {created_at.strftime('%Y-%m-%d %H:%M UTC')}\n"
                    f"**Fork URL:** {fork['html_url']}"
                )

                topic = self.config.get("topic_format", "{repo}").format(repo=repo.split('/')[-1])
                self._post_to_zulip(topic, content)
                self.seen_items.add(fork_id)

                time.sleep(1)

        except Exception as e:
            self.logger.error(f"Error checking forks for {repo}: {e}")

    def check_commits(self, repo: str, repo_data: dict):
        """Check for commits to main/master branch (summarized)."""
        try:
            # Get default branch
            default_branch = repo_data.get("default_branch", "main")

            url = f"https://api.github.com/repos/{repo}/commits"
            params = {"sha": default_branch, "per_page": 20}
            response = requests.get(url, headers=self._get_github_headers(), params=params, timeout=10)
            response.raise_for_status()

            commits = response.json()
            max_age_hours = self.config.get("events", {}).get("commits", {}).get("max_age_hours", 24)

            # Group commits by time period (daily summaries)
            new_commits = []

            for commit in commits:
                commit_sha = commit["sha"]
                commit_id = f"commit_{repo}_{commit_sha}"

                if commit_id in self.seen_items:
                    continue

                # Check age
                commit_date_str = commit["commit"]["author"]["date"]
                commit_date = datetime.strptime(commit_date_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                hours_old = (datetime.now(timezone.utc) - commit_date).total_seconds() / 3600

                if hours_old > max_age_hours:
                    self.seen_items.add(commit_id)
                    continue

                new_commits.append({
                    "sha": commit_sha[:7],
                    "message": commit["commit"]["message"].split('\n')[0],  # First line only
                    "author": commit["commit"]["author"]["name"],
                    "date": commit_date,
                    "url": commit["html_url"],
                    "id": commit_id
                })

            # If we have new commits, post a summary
            if new_commits:
                # Limit to most recent commits
                max_commits = self.config.get("events", {}).get("commits", {}).get("max_per_summary", 10)
                new_commits = new_commits[:max_commits]

                content = (
                    f"**New Commits to {default_branch}**\n"
                    f"**Repository:** {repo}\n"
                    f"**Count:** {len(new_commits)} new commit{'s' if len(new_commits) != 1 else ''}\n\n"
                )

                for commit in new_commits:
                    content += f"- `{commit['sha']}` {commit['message']} - {commit['author']}\n"
                    self.seen_items.add(commit['id'])

                content += f"\n**View all:** {repo_data['html_url']}/commits/{default_branch}"

                topic = self.config.get("topic_format", "{repo}").format(repo=repo.split('/')[-1])
                self._post_to_zulip(topic, content)

                time.sleep(1)

        except Exception as e:
            self.logger.error(f"Error checking commits for {repo}: {e}")

    def check_all_repositories(self):
        """Check all configured repositories."""
        repos = self.config.get("repositories", [])

        if not repos:
            self.logger.warning("No repositories configured!")
            return

        self.logger.info(f"Checking {len(repos)} repositories...")

        for repo in repos:
            self.check_repository(repo)
            # Rate limiting between repos
            time.sleep(2)

        # Save seen items after checking all repos
        self._save_seen_items()

    def run(self):
        """Main loop - poll repositories and post to Zulip."""
        poll_interval = self.config.get("poll_interval_seconds", 600)
        self.logger.info(f"Starting Merview GitHub Bot (polling every {poll_interval}s)...")

        # Log configuration
        repos = self.config.get("repositories", [])
        self.logger.info(f"Monitoring {len(repos)} repositories:")
        for repo in repos:
            self.logger.info(f"  - {repo}")

        if self.github_token:
            self.logger.info("Using GitHub token for authentication (higher rate limits)")
        else:
            self.logger.warning("No GitHub token provided - using lower rate limits")

        while True:
            try:
                self.check_all_repositories()
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")

            self.logger.info(f"Sleeping for {poll_interval} seconds...")
            time.sleep(poll_interval)


def main():
    parser = argparse.ArgumentParser(description="Merview GitHub Bot for Zulip")
    parser.add_argument(
        "-c", "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)"
    )
    parser.add_argument(
        "--check-once",
        action="store_true",
        help="Check repositories once and exit (for testing)"
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

    bot = GitHubBot(str(config_path))

    if args.check_once:
        bot.check_all_repositories()
        print("Single check completed!")
        sys.exit(0)

    bot.run()


if __name__ == "__main__":
    main()
