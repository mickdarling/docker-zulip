# AI News Bot for Zulip

A Python bot that monitors web sources for broader AI ecosystem news and posts updates to a Zulip channel. This bot focuses on general AI research, product launches, industry news, and breakthroughs across the AI landscape.

## Features

- **RSS Feed Monitoring**: Tracks blogs from Hugging Face, OpenAI, and Google DeepMind
- **Hacker News Integration**: Searches for AI-related stories matching keywords
- **Google News Monitoring**: Watches for news about AI breakthroughs and developments
- **Smart Categorization**: Automatically categorizes news into topics
- **Deduplication**: Tracks seen items to avoid duplicate posts
- **Rate Limiting**: Respectful of API rate limits
- **Configurable**: Easy YAML-based configuration

## Topics Monitored

The bot monitors and categorizes content related to:

- **Research**: Papers, studies, benchmarks, algorithms
- **Product Launches**: New models (GPT, Claude, Gemini, Llama), releases
- **Open Source**: GitHub projects, Hugging Face, PyTorch, TensorFlow
- **Industry News**: Partnerships, funding, acquisitions, regulations
- **Tutorials**: Guides, walkthroughs, implementation examples
- **General**: Other AI-related news

## Data Sources

### RSS Feeds
- **Hugging Face Blog**: Latest open-source models and tools
- **OpenAI Blog**: GPT updates and research announcements
- **Google DeepMind**: Research breakthroughs and model releases
- Configurable max age (default: 1 week)

Note: Anthropic and Meta AI/FAIR do not provide public RSS feeds.

### Hacker News
- Searches stories using Algolia HN API
- Keywords: GPT, LLM, transformer, neural network, deep learning, etc.
- Configurable max age (default: 48 hours)

### Google News
- Monitors news for AI-related search terms
- Keywords: artificial intelligence, large language model, GPT-4, Claude AI, etc.
- Configurable max age (default: 1 week)

## Installation

### Prerequisites

- Python 3.12+
- Zulip account and API credentials
- (Optional) GitHub Personal Access Token for higher rate limits

### Setup

1. **Clone or navigate to the bot directory:**
   ```bash
   cd /Users/mick/Developer/ClaudeCodeProjects/Zulip/bots/ai-news-bot
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
   - Create a stream called `#ai-news` on your Zulip instance
   - Ensure the bot has permission to post to this stream

## Usage

### Run Locally

```bash
# Run the bot (continuous monitoring)
python ai_news_bot.py

# Test with a single check
python ai_news_bot.py --check-once

# Use custom config file
python ai_news_bot.py -c /path/to/config.yaml
```

### Run with Docker

```bash
# Build the image
docker build -t ai-news-bot .

# Run the container
docker run -d \
  --name ai-news-bot \
  --env-file .env \
  ai-news-bot
```

### Run with Docker Compose

Add to your `docker-compose.yml`:

```yaml
services:
  ai-news-bot:
    build: ./bots/ai-news-bot
    container_name: ai-news-bot
    environment:
      FORMATTER_BOT_API_KEY: "${FORMATTER_BOT_API_KEY}"
    volumes:
      - ./bots/ai-news-bot/seen_items.json:/app/seen_items.json:rw
    restart: unless-stopped
    depends_on:
      - zulip
```

## Configuration

### Environment Variables

- `FORMATTER_BOT_API_KEY`: Zulip bot API key (required)
- `GITHUB_TOKEN`: GitHub Personal Access Token (optional, for higher rate limits)

### config.yaml Structure

```yaml
poll_interval_seconds: 3600  # Check every hour

zulip:
  site: "https://chat.dollhousemcp.com"
  email: "formatter-bot@chat.dollhousemcp.com"
  api_key: "${FORMATTER_BOT_API_KEY}"
  stream: "ai-news"

categories:
  "Research":
    topic: "Research"
    keywords: ["research", "paper", "arxiv", "study"]
  # ... more categories

sources:
  rss_feeds:
    enabled: true
    max_age_hours: 168
    feeds:
      "Hugging Face Blog": "https://huggingface.co/blog/feed.xml"
      "OpenAI Blog": "https://openai.com/blog/rss.xml"
      "Google DeepMind": "https://deepmind.google/blog/rss.xml"

  hackernews:
    enabled: true
    max_age_hours: 48
    keywords: ["GPT", "LLM", "transformer"]

  google_news:
    enabled: true
    max_age_hours: 168
    keywords: ["artificial intelligence", "GPT-4"]
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
ai-news-bot/
├── ai_news_bot.py       # Main bot script
├── config.yaml          # Configuration
├── requirements.txt     # Python dependencies
├── Dockerfile          # Container definition
├── .env.example        # Environment variable template
├── .gitignore          # Git ignore patterns
├── seen_items.json     # Tracking file (auto-generated)
└── README.md           # This file
```

## Output Examples

### RSS Feed Post
```
**Hugging Face Blog: Introducing Llama 3.2**
**Published:** 2025-12-10 14:30 UTC
**URL:** https://huggingface.co/blog/llama-3.2
```

### Hacker News Post
```
**Hacker News: GPT-4 Beats Humans on Common Sense Reasoning**
**Score:** 256 points | 89 comments
**Posted:** 2025-12-10 10:15 UTC
**URL:** https://example.com/article
**HN Discussion:** https://news.ycombinator.com/item?id=12345678
```

### Google News Post
```
**Google News: OpenAI Announces Major Breakthrough in AI Safety**
**Search Term:** artificial intelligence
**Published:** 2025-12-10 08:45 UTC
**URL:** https://news.google.com/...
```

## Troubleshooting

### No posts appearing

1. Check that the bot has permission to post to the Zulip stream
2. Verify API credentials are correct
3. Run with `--check-once` to test
4. Check logs for errors (set `logging.level: DEBUG` in config)

### Rate limiting issues

1. Increase `poll_interval_seconds` to reduce API calls
2. Reduce the number of monitored keywords

### Duplicate posts

1. Delete `seen_items.json` and restart (will repost recent items once)
2. Check that the bot isn't running multiple instances

## Future Enhancements

- Twitter/X integration for AI researchers and companies
- Discord monitoring
- AI-powered content summarization
- Sentiment analysis
- Trending topic detection
- Newsletter aggregation
- RSS feeds from individual AI researchers (when available)

## Support

For issues or questions:
- Check the logs (set `logging.level: DEBUG`)
- Review the configuration file
- Ensure API credentials are valid
- Verify network connectivity to external APIs

## License

Part of the Dollhouse MCP Zulip project.
