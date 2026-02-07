# MCP News Bot for Zulip

A Python bot that monitors web sources for news about the MCP (Model Context Protocol) ecosystem and posts updates to a Zulip channel.

## Features

### Phase 1 Implementation

- **GitHub Release Monitoring**: Tracks new releases from MCP-related repositories
- **Hacker News Integration**: Searches for stories matching MCP-related keywords
- **Reddit Monitoring**: Watches relevant subreddits for MCP discussions
- **Smart Categorization**: Automatically categorizes news into topics
- **Deduplication**: Tracks seen items to avoid duplicate posts
- **Rate Limiting**: Respectful of API rate limits
- **Configurable**: Easy YAML-based configuration

## Topics Monitored

The bot monitors and categorizes content related to:

- MCP Specification and Model Context Protocol
- MCP Servers
- Dollhouse MCP (all variations)
- Merview
- Zulip
- Claude and Anthropic
- AI Agents (LangChain, CrewAI, AutoGPT)

## Data Sources

### GitHub

- Monitors releases from configured repositories
- Checks MCP core repos, Dollhouse MCP, AI agent frameworks, and Zulip
- Configurable max age for releases (default: 1 week)

### Hacker News

- Searches stories using Algolia HN API
- Keyword-based filtering
- Configurable max age (default: 48 hours)

### Reddit

- Monitors r/LocalLLaMA, r/MachineLearning, and other AI subreddits
- Keyword-based filtering
- Uses public JSON API (no authentication required)
- Configurable max age (default: 48 hours)

## Installation

### Prerequisites

- Python 3.12+
- Zulip account and API credentials
- (Optional) GitHub Personal Access Token for higher rate limits

### Setup

1. **Clone or navigate to the bot directory:**

   ```bash
   cd /Users/mick/Developer/ClaudeCodeProjects/Zulip/bots/mcp-news-bot
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**

   ```bash
   cp .env.example .env
   # Edit .env and add your credentials
   ```

4. **Edit config.yaml:**
   - Update Zulip credentials
   - Adjust keywords and sources as needed
   - Configure poll interval

5. **Create the Zulip stream:**
   - Create a stream called `#mcp-news` on your Zulip instance
   - Ensure the bot has permission to post to this stream

## Usage

### Run Locally

```bash
# Run the bot (continuous monitoring)
python mcp_news_bot.py

# Test with a single check
python mcp_news_bot.py --check-once

# Use custom config file
python mcp_news_bot.py -c /path/to/config.yaml
```

### Run with Docker

```bash
# Build the image
docker build -t mcp-news-bot .

# Run the container
docker run -d \
  --name mcp-news-bot \
  --env-file .env \
  mcp-news-bot
```

### Run with Docker Compose

Add to your `docker-compose.yml`:

```yaml
services:
  mcp-news-bot:
    build: ./bots/mcp-news-bot
    container_name: mcp-news-bot
    env_file:
      - ./bots/mcp-news-bot/.env
    volumes:
      - ./bots/mcp-news-bot/seen_items.json:/app/seen_items.json
    restart: unless-stopped
```

## Configuration

### Environment Variables

- `MCP_NEWS_BOT_API_KEY`: Zulip bot API key (required)
- `GITHUB_TOKEN`: GitHub Personal Access Token (optional, for higher rate limits)

### config.yaml Structure

```yaml
poll_interval_seconds: 3600 # Check every hour

zulip:
  site: "https://chat.dollhousemcp.com"
  email: "mcp-news-bot@chat.dollhousemcp.com"
  api_key: "${MCP_NEWS_BOT_API_KEY}"
  stream: "mcp-news"

categories:
  "MCP Updates":
    topic: "MCP Updates"
    keywords: ["MCP Specification", "Model Context Protocol"]
  # ... more categories

sources:
  github:
    enabled: true
    max_age_hours: 168
    repos:
      - "modelcontextprotocol/specification"
      # ... more repos

  hackernews:
    enabled: true
    max_age_hours: 48
    keywords: ["MCP", "Claude", "Anthropic"]

  reddit:
    enabled: true
    max_age_hours: 48
    subreddits: ["LocalLLaMA", "MachineLearning"]
    keywords: ["MCP", "Claude", "AI Agent"]
```

## How It Works

1. **Polling**: The bot runs on a configurable interval (default: 1 hour)
2. **Source Checking**: Each enabled source is checked for new content
3. **Keyword Matching**: Content is filtered based on configured keywords
4. **Categorization**: Matched items are categorized based on their content
5. **Deduplication**: Each item's unique ID is tracked in `seen_items.json`
6. **Posting**: New items are posted to Zulip in the appropriate topic
7. **Rate Limiting**: Delays between API calls to respect rate limits

## File Structure

```
mcp-news-bot/
├── mcp_news_bot.py      # Main bot script
├── config.yaml          # Configuration
├── requirements.txt     # Python dependencies
├── Dockerfile          # Container definition
├── .env.example        # Environment variable template
├── seen_items.json     # Tracking file (auto-generated)
└── README.md           # This file
```

## Output Examples

### GitHub Release

```
**New GitHub Release: modelcontextprotocol/specification**
**Version:** v1.2.0
**Published:** 2025-12-10 14:30 UTC
**URL:** https://github.com/modelcontextprotocol/specification/releases/tag/v1.2.0

**Release Notes:**
Added support for streaming responses...
```

### Hacker News

```
**Hacker News: Building AI Agents with Model Context Protocol**
**Score:** 156 points | 42 comments
**Posted:** 2025-12-10 10:15 UTC
**URL:** https://example.com/article
**HN Discussion:** https://news.ycombinator.com/item?id=12345678
```

### Reddit

```
**Reddit r/LocalLLaMA: New MCP server for RAG workflows**
**Score:** 89 upvotes | 23 comments
**Posted:** 2025-12-10 08:45 UTC
**URL:** https://reddit.com/r/LocalLLaMA/comments/...

**Preview:**
I just released a new MCP server that makes it easy to...
```

## Troubleshooting

### No posts appearing

1. Check that the bot has permission to post to the Zulip stream
2. Verify API credentials are correct
3. Run with `--check-once` to test
4. Check logs for errors (set `logging.level: DEBUG` in config)

### Rate limiting issues

1. Add a GitHub Personal Access Token (increases rate limit from 60 to 5000/hour)
2. Increase `poll_interval_seconds` to reduce API calls
3. Reduce the number of monitored repos/keywords

### Duplicate posts

1. Delete `seen_items.json` and restart (will repost recent items once)
2. Check that the bot isn't running multiple instances

## Future Enhancements (Phase 2+)

- RSS feed monitoring for AI blogs
- Twitter/X integration
- Discord monitoring
- AI-powered content summarization
- Sentiment analysis
- Trending topic detection
- Web scraping for specific sites
- Newsletter aggregation

## Support

For issues or questions:

- Check the logs (set `logging.level: DEBUG`)
- Review the configuration file
- Ensure API credentials are valid
- Verify network connectivity to external APIs

## License

Part of the Dollhouse MCP project.
