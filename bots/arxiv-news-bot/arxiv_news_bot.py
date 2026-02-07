#!/usr/bin/env python3
"""
arXiv News Bot for Zulip

Monitors arXiv for academic papers related to MCP, AI agents, and LLMs,
then posts updates to a Zulip channel.
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


class ArxivNewsBot(BaseNewsBot):
    """Bot that monitors arXiv for relevant papers and posts to Zulip."""

    ARXIV_API_URL = "http://export.arxiv.org/api/query"
    ARXIV_RSS_URL = "http://export.arxiv.org/rss/{category}"

    def __init__(self, config_path: str):
        super().__init__(config_path, bot_name="arxiv_news_bot")

    def check_all_sources(self):
        """Check all configured arXiv sources."""
        self.logger.info("Checking arXiv for new papers...")

        sources = self.config.get("sources", {})

        if sources.get("arxiv_api", {}).get("enabled", False):
            self.check_arxiv_api()

        if sources.get("arxiv_rss", {}).get("enabled", False):
            self.check_arxiv_rss()

    def check_arxiv_api(self):
        """Search arXiv API for papers matching queries."""
        api_config = self.config["sources"]["arxiv_api"]
        queries = api_config.get("queries", [])
        max_results = api_config.get("max_results", 50)
        max_age_hours = api_config.get("max_age_hours", 168)

        for query in queries:
            try:
                # Build API query
                params = {
                    "search_query": f"all:{query}",
                    "start": 0,
                    "max_results": max_results,
                    "sortBy": "submittedDate",
                    "sortOrder": "descending"
                }
                url = f"{self.ARXIV_API_URL}?{urllib.parse.urlencode(params)}"

                self.logger.debug(f"Querying arXiv API: {query}")

                # Make request
                with urllib.request.urlopen(url, timeout=30) as response:
                    content = response.read()

                # Parse Atom feed
                root = ET.fromstring(content)
                ns = {"atom": "http://www.w3.org/2005/Atom"}

                for entry in root.findall("atom:entry", ns):
                    self._process_arxiv_entry(entry, ns, max_age_hours, f"search:{query}")

                # Rate limiting between queries
                time.sleep(3)

            except Exception as e:
                self.logger.error(f"Error querying arXiv API for '{query}': {e}")

    def check_arxiv_rss(self):
        """Check arXiv RSS feeds for new papers in configured categories."""
        rss_config = self.config["sources"]["arxiv_rss"]
        categories = rss_config.get("categories", [])
        max_age_hours = rss_config.get("max_age_hours", 72)
        filter_keywords = rss_config.get("filter_keywords", [])

        for category in categories:
            try:
                url = self.ARXIV_RSS_URL.format(category=category)
                self.logger.debug(f"Checking arXiv RSS: {category}")

                with urllib.request.urlopen(url, timeout=30) as response:
                    content = response.read()

                # Parse RSS feed
                root = ET.fromstring(content)

                for item in root.findall(".//item"):
                    title = item.find("title")
                    link = item.find("link")
                    description = item.find("description")

                    if title is None or link is None:
                        continue

                    title_text = title.text or ""
                    link_text = link.text or ""
                    desc_text = description.text if description is not None else ""

                    # Filter by keywords
                    combined_text = f"{title_text} {desc_text}"
                    if filter_keywords and not self._matches_keywords(combined_text, filter_keywords):
                        continue

                    # Create unique ID from link
                    paper_id = f"arxiv_rss_{hash(link_text)}"

                    if self.is_seen(paper_id):
                        continue

                    # Extract arxiv ID from link
                    arxiv_id = link_text.split("/")[-1] if link_text else "unknown"

                    # Categorize
                    category_name = self._categorize_item(title_text, desc_text)

                    # Format message
                    content = (
                        f"**arXiv [{category}]: {title_text}**\n"
                        f"**Category:** {category}\n"
                        f"**arXiv ID:** {arxiv_id}\n"
                        f"**URL:** {link_text}\n"
                    )

                    if desc_text:
                        # Clean up description (often has HTML)
                        clean_desc = desc_text.replace("<p>", "").replace("</p>", "\n").strip()
                        if len(clean_desc) > 500:
                            clean_desc = clean_desc[:500] + "..."
                        content += f"\n**Abstract:**\n{clean_desc}"

                    self._post_to_zulip(category_name, content)
                    self.mark_seen(paper_id)

                    time.sleep(2)

                # Rate limiting between categories
                time.sleep(3)

            except Exception as e:
                self.logger.error(f"Error checking arXiv RSS for {category}: {e}")

    def _process_arxiv_entry(self, entry, ns: dict, max_age_hours: int, source: str):
        """Process a single arXiv API entry."""
        try:
            # Extract fields
            id_elem = entry.find("atom:id", ns)
            title_elem = entry.find("atom:title", ns)
            summary_elem = entry.find("atom:summary", ns)
            published_elem = entry.find("atom:published", ns)
            updated_elem = entry.find("atom:updated", ns)

            if id_elem is None or title_elem is None:
                return

            arxiv_url = id_elem.text
            arxiv_id = arxiv_url.split("/")[-1] if arxiv_url else "unknown"
            title = title_elem.text.replace("\n", " ").strip() if title_elem.text else ""
            summary = summary_elem.text.replace("\n", " ").strip() if summary_elem is not None and summary_elem.text else ""

            # Create unique ID
            paper_id = f"arxiv_api_{arxiv_id}"

            if self.is_seen(paper_id):
                return

            # Check age
            date_str = published_elem.text if published_elem is not None else (updated_elem.text if updated_elem is not None else None)
            if date_str:
                try:
                    # arXiv uses ISO format
                    pub_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    if self.is_too_old(pub_date, max_age_hours):
                        self.mark_seen(paper_id)
                        return
                    date_display = pub_date.strftime('%Y-%m-%d')
                except Exception:
                    date_display = "Unknown"
            else:
                date_display = "Unknown"

            # Get authors
            authors = []
            for author in entry.findall("atom:author", ns):
                name = author.find("atom:name", ns)
                if name is not None and name.text:
                    authors.append(name.text)
            authors_str = ", ".join(authors[:5])
            if len(authors) > 5:
                authors_str += f" et al. ({len(authors)} authors)"

            # Get categories
            categories = []
            for cat in entry.findall("atom:category", ns):
                term = cat.get("term")
                if term:
                    categories.append(term)
            categories_str = ", ".join(categories[:5])

            # Categorize
            category = self._categorize_item(title, summary)

            # Format message
            content = (
                f"**arXiv: {title}**\n"
                f"**Authors:** {authors_str}\n"
                f"**Published:** {date_display}\n"
                f"**Categories:** {categories_str}\n"
                f"**arXiv ID:** {arxiv_id}\n"
                f"**URL:** {arxiv_url}\n"
            )

            if summary:
                truncated = summary[:500]
                if len(summary) > 500:
                    truncated += "..."
                content += f"\n**Abstract:**\n{truncated}"

            self._post_to_zulip(category, content)
            self.mark_seen(paper_id)

        except Exception as e:
            self.logger.error(f"Error processing arXiv entry: {e}")


def main():
    parser = argparse.ArgumentParser(description="arXiv News Bot for Zulip")
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

    bot = ArxivNewsBot(str(config_path))

    if args.check_once:
        bot.run_once()
    else:
        bot.run()


if __name__ == "__main__":
    main()
