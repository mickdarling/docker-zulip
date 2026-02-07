# Merview News Bot

A Zulip bot that monitors various web sources for news about Merview and posts updates to a Zulip stream.

## Features

- Monitors multiple sources:
  - Google News RSS feed
  - Hacker News (via Algolia API)
  - Reddit (multiple subreddits)
- Filters out references to the Thai person named "Merview"
- Categorizes news into topics:
  - Press Coverage
  - Social Media
  - Blog Posts
  - Technical Discussions
  - General
- Avoids duplicate posts using persistent state
- Configurable polling interval and source settings

## Setup

### 1. Create a Zulip Bot

1. Log into your Merview Zulip instance
2. Go to Settings > Your bots
3. Create a new bot named "Merview News Bot"
4. Copy the API key

### 2. Configure Environment Variables

Edit `.env` and set:

```bash
MERVIEW_BOT_API_KEY=your_actual_api_key_here
```

### 3. Update Configuration

Edit `config.yaml` and update the Zulip settings:

- `site`: Your Merview Zulip instance URL
- `email`: The bot's email address
- `stream`: The stream to post to (default: "news")

### 4. Run the Bot

#### Using Docker (recommended):

The bot is included in the main docker-compose.yml. Simply run:

```bash
docker-compose up -d merview-news-bot
```

#### Using Python directly:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot
python merview_news_bot.py

# Test mode (check once and exit)
python merview_news_bot.py --check-once
```

## Configuration

See `config.yaml` for all configuration options:

- `poll_interval_seconds`: How often to check sources (default: 3600 = 1 hour)
- `sources`: Enable/disable and configure each news source
- `categories`: Define categories and their keywords for topic classification
- `logging`: Configure log level and optional log file

## Thai Person Filtering

The bot includes logic to filter out references to a person from Thailand named Merview:

- Detects Thai language indicators
- Filters social media profile links
- Removes biographical content

This ensures the bot only posts news relevant to the Merview product/service.

## Data Persistence

The bot stores seen item IDs in `seen_items.json` to avoid duplicate posts. This file is created automatically and should be backed up or mounted as a volume in Docker.

## Logs

Logs are written to stdout by default. Configure `logging.file` in `config.yaml` to write to a file.

## License

Same as parent Zulip project.
