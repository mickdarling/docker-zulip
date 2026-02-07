# LinkedIn News Bot for Zulip

A Python bot that monitors LinkedIn content for articles related to MCP, AI agents, and related topics, then posts updates to a Zulip channel.

## How It Works

LinkedIn doesn't provide a public API for content search, so this bot uses a workaround:

1. Searches Google News RSS feeds with `site:linkedin.com` filter
2. Finds LinkedIn articles that appear in Google News search results
3. Posts matching articles to Zulip

**Limitations**: This approach only finds LinkedIn articles that are indexed by Google News, which typically includes:

- LinkedIn blog posts
- Public articles and newsletters
- Trending posts from influencers

It will **not** find:

- Private posts
- Most regular user posts
- Content behind login walls

## Features

- **Google News Integration**: Searches for LinkedIn content via Google News RSS
- **Smart Categorization**: Automatically categorizes articles into topics
- **Deduplication**: Tracks seen articles to avoid duplicate posts
- **Rate Limiting**: Respectful of Google News rate limits
- **No API Key Required**: Uses public RSS feeds

## Topics Monitored

The bot monitors and categorizes articles related to:

- **MCP Updates**: Model Context Protocol, tool use
- **Dollhouse MCP**: DollhouseMCP specific content
- **Merview**: Merview specific content
- **Anthropic**: Claude, Anthropic
- **AI Agents**: LangChain, CrewAI, AutoGPT
- **Industry News**: Startups, funding, partnerships

## Setup

### 1. Create a Zulip Bot Account

1. Go to your Zulip instance
2. Navigate to **Settings** > **Your bots**
3. Click **Add a new bot**
4. Configure the bot and copy the API key

### 2. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your Zulip bot credentials
```

### 3. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Run the Bot

```bash
# Run continuously
python linkedin_news_bot.py

# Or test with a single check
python linkedin_news_bot.py --check-once
```

## Configuration

Edit `config.yaml` to customize:

- Poll interval
- Search queries
- Maximum article age
- Category definitions

## Docker

Build and run with Docker:

```bash
# From the bots/ directory
docker build -f linkedin-news-bot/Dockerfile -t linkedin-news-bot .
docker run -d --env-file linkedin-news-bot/.env linkedin-news-bot
```

## Data Sources

- **Google News RSS**: `https://news.google.com/rss/search?q=...`

No API key required - Google News RSS feeds are publicly accessible.
