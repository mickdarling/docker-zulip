# Claude Skills Bot

A specialized news monitoring bot that tracks mentions of Anthropic's "Agent Skills" / "Claude Skills" feature across the web.

## Purpose

This bot was created to monitor news and announcements about Anthropic's "Agent Skills" feature as part of tracking potential AGPL attribution issues related to the "Dollhouse Skills" project. Since "skills" is a generic term, this bot implements strict filtering to avoid noise from unrelated articles about job skills, learning skills, etc.

## Legal Context

The user believes Anthropic may have taken inspiration from their "Dollhouse Skills" project (licensed under AGPL) without proper attribution. Anthropic calls their feature "Agent Skills". This bot helps track public announcements and news about this feature.

## Features

### Strict Filtering Logic

The bot ONLY posts articles that meet ALL of these criteria:

1. **Must mention Anthropic or Claude**:
   - Anthropic (company)
   - Claude AI, Claude 3, Claude 4, Claude Opus, Claude Sonnet, Claude Haiku

2. **Must mention skills in AI context**:
   - "agent skills"
   - "claude skills"
   - "custom skills"
   - "AI skills"
   - "skill system"
   - "skills feature"
   - "skills API"
   - "skills framework"

3. **Must NOT be about**:
   - Job postings/careers/hiring
   - Resumes/CVs/employment
   - Learning/skill development
   - Professional/soft/hard skills
   - Generic "top 10 skills" articles

### Data Sources

1. **Google News**:
   - Searches for exact phrases like `"Anthropic" "agent skills"`
   - Uses specific search queries to minimize false positives
   - Max age: 168 hours (1 week)

2. **Hacker News**:
   - Monitors for discussions about Anthropic/Claude skills
   - Uses Algolia HN Search API
   - Max age: 168 hours (1 week)

3. **Anthropic's Website**:
   - Uses `site:anthropic.com skills` search
   - Direct content from Anthropic's website
   - Max age: 168 hours (1 week)

## Configuration

### Zulip Settings

- **Site**: `https://chat.dollhousemcp.com`
- **Stream**: `claude-skills-watch`
- **Topic**: `News & Updates`
- **Credentials**: Uses formatter-bot API key
- **Poll Interval**: 3600 seconds (1 hour)

### Search Queries (Google News)

- `"Anthropic" "agent skills"`
- `"Claude" "agent skills"`
- `"Anthropic skills" AI`
- `"Claude skills" AI`
- `"Claude" "custom skills"`
- `Anthropic "AI skills"`

### Hacker News Keywords

- `Anthropic skills`
- `Claude skills`
- `Claude agent skills`

## Setup

### Prerequisites

1. Create Zulip stream `claude-skills-watch`
2. Subscribe relevant users (e.g., user8@chat.dollhousemcp.com)
3. Ensure `FORMATTER_BOT_API_KEY` is set in environment

### Running with Docker Compose

The bot is configured in `docker-compose.yml`:

```yaml
claude-skills-bot:
  build: ./bots/claude-skills-bot
  restart: unless-stopped
  environment:
    FORMATTER_BOT_API_KEY: "${FORMATTER_BOT_API_KEY}"
  volumes:
    - ./bots/claude-skills-bot/seen_items.json:/app/seen_items.json:rw
  depends_on:
    - zulip
```

Start the bot:

```bash
docker-compose up -d claude-skills-bot
```

### Testing

Test the bot without running continuously:

```bash
cd bots/claude-skills-bot
python claude_skills_bot.py --check-once
```

### Logs

View bot logs:

```bash
docker-compose logs -f claude-skills-bot
```

## How It Works

1. **Every hour**, the bot checks all configured sources
2. For each article/story found:
   - Checks if it's already been seen (tracked in `seen_items.json`)
   - Applies strict filtering rules (see above)
   - If relevant, posts to Zulip with context
3. Seen items are persisted to disk to avoid duplicates across restarts
4. Rate limiting between checks to avoid API issues

## Message Format

Posts include:

- Article title
- Source (Google News, Hacker News, etc.)
- Publication date
- URL to article
- Context note: "_Tracking Anthropic's Agent Skills feature for potential AGPL attribution issues._"

## Filtering Philosophy

**Better to miss some articles than flood with irrelevant content.**

The filtering is intentionally strict because:

- "Skills" is an extremely generic term
- Most "skills" articles are about jobs, learning, or generic AI capabilities
- Legal tracking requires high signal-to-noise ratio
- False positives waste time and dilute important information

If an article passes all filters, it's very likely to be relevant to Anthropic's Agent Skills feature.

## Maintenance

### Adjusting Filters

If you're getting too many false positives, strengthen filters in `_is_relevant_skills_article()`:

- Add more exclusion patterns
- Require more specific terminology
- Increase minimum keyword matches

If you're missing relevant articles, relax filters:

- Add more inclusive keyword variations
- Reduce exclusion patterns
- Review filtered items in logs (set `level: "DEBUG"`)

### Adding Sources

To add new sources, implement a new `check_*()` method following the pattern:

1. Check if source is enabled in config
2. Fetch data from source
3. Apply `_is_relevant_skills_article()` filtering
4. Track seen items
5. Post to Zulip with appropriate context

## Files

- `claude_skills_bot.py` - Main bot logic with strict filtering
- `config.yaml` - Configuration (sources, keywords, Zulip settings)
- `requirements.txt` - Python dependencies
- `Dockerfile` - Container image definition
- `README.md` - This file
- `seen_items.json` - Persistent storage of seen articles (created at runtime)

## Dependencies

- Python 3.12+
- zulip >= 0.9.0
- PyYAML >= 6.0
- requests >= 2.31.0
- python-dotenv >= 1.0.0

## License

Part of the Zulip bot collection for chat.dollhousemcp.com
