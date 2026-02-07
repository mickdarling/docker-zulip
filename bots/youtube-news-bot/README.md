# YouTube News Bot for Zulip

A Python bot that monitors YouTube for videos related to MCP, AI agents, and related topics, then posts updates to a Zulip channel.

## Features

- **YouTube Data API Search**: Searches for videos matching configurable queries
- **Smart Categorization**: Automatically categorizes videos into topics
- **Deduplication**: Tracks seen videos to avoid duplicate posts
- **Rate Limiting**: Respectful of YouTube API quotas
- **Age Filtering**: Only posts recent videos (configurable)

## Topics Monitored

The bot monitors and categorizes videos related to:

- **MCP Updates**: Model Context Protocol, tool use, function calling
- **Dollhouse MCP**: DollhouseMCP specific content
- **Merview**: Merview specific content
- **Anthropic**: Claude, Anthropic API tutorials
- **AI Agents**: LangChain, CrewAI, AutoGPT, agent frameworks
- **Tutorials**: How-to guides and walkthroughs

## Setup

### 1. Get a YouTube Data API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Navigate to **APIs & Services** > **Library**
4. Search for "YouTube Data API v3" and enable it
5. Go to **Credentials** > **Create Credentials** > **API Key**
6. Copy your API key

**Note**: The free tier provides 10,000 units/day. Each search costs 100 units, so you can do ~100 searches per day.

### 2. Create a Zulip Bot Account

1. Go to your Zulip instance
2. Navigate to **Settings** > **Your bots**
3. Click **Add a new bot**
4. Configure the bot and copy the API key

### 3. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your credentials:
# - FORMATTER_BOT_API_KEY (Zulip)
# - YOUTUBE_API_KEY (Google Cloud)
```

### 4. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 5. Run the Bot

```bash
# Run continuously
python youtube_news_bot.py

# Or test with a single check
python youtube_news_bot.py --check-once
```

## Configuration

Edit `config.yaml` to customize:

- Poll interval
- Search queries
- Maximum video age
- Category definitions

## Docker

Build and run with Docker:

```bash
# From the bots/ directory
docker build -f youtube-news-bot/Dockerfile -t youtube-news-bot .
docker run -d --env-file youtube-news-bot/.env youtube-news-bot
```

## API Quotas

YouTube Data API v3 has a daily quota of 10,000 units (free tier):

| Operation     | Cost      |
| ------------- | --------- |
| Search        | 100 units |
| Video details | 1 unit    |

With 10 search queries running hourly, you'd use: 10 _ 100 _ 24 = 24,000 units/day (over quota).

**Recommendation**: Run every 2-4 hours instead of hourly, or reduce the number of search queries.
