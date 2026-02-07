# Twitter/X News Bot for Zulip

A Python bot that monitors Twitter/X for content related to MCP, AI agents, and related topics, then posts updates to a Zulip channel.

## How It Works

Since Twitter's official API is now paid ($100+/month for Basic tier), this bot uses free alternatives:

1. **RSS Bridge** (Primary): Open-source project that provides RSS feeds for Twitter search
2. **Google News** (Backup): Searches for tweets that appear in Google News

### Limitations

**RSS Bridge**:
- Public instances may be slow or unavailable
- Twitter may block requests from known bridge IPs
- Results are less comprehensive than official API
- Consider self-hosting for reliability

**Google News**:
- Only finds tweets that are indexed by Google News
- Very limited coverage

## Features

- **RSS Bridge Integration**: Multiple fallback instances for reliability
- **Google News Backup**: Additional source when RSS bridges fail
- **Smart Categorization**: Automatically categorizes content into topics
- **Deduplication**: Tracks seen tweets to avoid duplicates
- **Rate Limiting**: Respectful of service limits
- **No API Key Required**: Uses free public services

## Topics Monitored

The bot monitors and categorizes content related to:

- **MCP Updates**: Model Context Protocol, tool use
- **Dollhouse MCP**: DollhouseMCP specific content
- **Merview**: Merview specific content
- **Anthropic**: Claude, Anthropic
- **AI Agents**: LangChain, CrewAI, AutoGPT

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
python twitter_news_bot.py

# Or test with a single check
python twitter_news_bot.py --check-once
```

## Configuration

Edit `config.yaml` to customize:

- Poll interval
- RSS Bridge instances (add your own self-hosted instance for reliability)
- Search queries
- Maximum content age
- Category definitions

### Self-Hosting RSS Bridge

For more reliable Twitter monitoring, consider self-hosting RSS Bridge:

```bash
# Using Docker
docker run -d -p 3000:80 rssbridge/rss-bridge

# Then update config.yaml:
# instances:
#   - "http://localhost:3000"
#   - "https://rss-bridge.org/bridge01"  # fallback
```

See: https://github.com/RSS-Bridge/rss-bridge

## Docker

Build and run with Docker:

```bash
# From the bots/ directory
docker build -f twitter-news-bot/Dockerfile -t twitter-news-bot .
docker run -d --env-file twitter-news-bot/.env twitter-news-bot
```

## Data Sources

- **RSS Bridge**: https://github.com/RSS-Bridge/rss-bridge
- **Google News RSS**: `https://news.google.com/rss/search?q=...`

## Upgrading to Official Twitter API

If you decide to pay for Twitter API access ($100+/month), you can:

1. Get a Bearer Token from the Twitter Developer Portal
2. Add `TWITTER_BEARER_TOKEN` to your `.env`
3. Modify `twitter_news_bot.py` to use the official API

The Twitter API v2 search endpoint provides much more comprehensive and reliable results.
