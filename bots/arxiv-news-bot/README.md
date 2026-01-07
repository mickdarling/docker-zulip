# arXiv News Bot for Zulip

A Python bot that monitors arXiv for academic papers related to MCP, AI agents, LLMs, and related topics, then posts updates to a Zulip channel.

## Features

- **arXiv API Search**: Searches for papers matching configurable queries
- **arXiv RSS Feeds**: Monitors specific categories (cs.AI, cs.CL, cs.LG, cs.MA)
- **Smart Categorization**: Automatically categorizes papers into topics
- **Keyword Filtering**: Only posts papers matching relevant keywords
- **Deduplication**: Tracks seen papers to avoid duplicate posts
- **Rate Limiting**: Respectful of arXiv API rate limits

## Topics Monitored

The bot monitors and categorizes papers related to:

- **MCP Updates**: Model Context Protocol, tool use, function calling
- **AI Agents**: Autonomous agents, multi-agent systems, reasoning
- **Anthropic**: Claude, Constitutional AI, RLHF
- **Language Models**: LLMs, transformers, fine-tuning
- **Retrieval & RAG**: RAG, embeddings, knowledge bases
- **Code & Programming**: Code generation, software engineering

## Setup

### 1. Create a Zulip Bot Account

1. Go to your Zulip instance
2. Navigate to **Settings** > **Your bots**
3. Click **Add a new bot**
4. Configure the bot and copy the API key

### 2. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your credentials
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
python arxiv_news_bot.py

# Or test with a single check
python arxiv_news_bot.py --check-once
```

## Configuration

Edit `config.yaml` to customize:

- Poll interval
- Search queries
- arXiv categories to monitor
- Filter keywords
- Category definitions

## Docker

Build and run with Docker:

```bash
# From the bots/ directory
docker build -f arxiv-news-bot/Dockerfile -t arxiv-news-bot .
docker run -d --env-file arxiv-news-bot/.env arxiv-news-bot
```

## Data Sources

- **arXiv API**: https://arxiv.org/help/api
- **arXiv RSS**: http://export.arxiv.org/rss/

No API key required - arXiv is freely accessible.
