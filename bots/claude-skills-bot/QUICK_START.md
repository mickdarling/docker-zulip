# Claude Skills Bot - Quick Start

## What This Bot Does

Monitors Google News, Hacker News, and Anthropic's website for mentions of **"Agent Skills" / "Claude Skills"** - Anthropic's AI capabilities feature. Uses strict filtering to avoid generic "skills" articles (job postings, learning skills, etc.).

**Legal Context**: Tracking potential AGPL attribution issues related to "Dollhouse Skills" project.

## Setup (One Time)

```bash
cd /Users/mick/Developer/ClaudeCodeProjects/Zulip

# 1. Create the Zulip stream and subscribe users
cd bots/claude-skills-bot
pip3 install -r requirements.txt
python3 setup_stream.py

# 2. Build and start the bot
cd ../..
docker-compose build claude-skills-bot
docker-compose up -d claude-skills-bot

# 3. Check logs
docker-compose logs -f claude-skills-bot
```

## Daily Operations

```bash
# View logs
docker-compose logs -f claude-skills-bot

# Restart
docker-compose restart claude-skills-bot

# Stop
docker-compose stop claude-skills-bot

# Check status
docker-compose ps claude-skills-bot
```

## Testing

```bash
# Test without Docker (check once and exit)
cd bots/claude-skills-bot
python3 claude_skills_bot.py --check-once
```

## Configuration

- **Stream**: `claude-skills-watch`
- **Topic**: `News & Updates`
- **Poll Interval**: Every hour
- **Max Age**: 1 week
- **Credentials**: Uses `FORMATTER_BOT_API_KEY` from `.env`

## Search Queries

The bot searches for:

- `"Anthropic" "agent skills"`
- `"Claude" "agent skills"`
- `"Anthropic skills" AI`
- `"Claude skills" AI`
- `"Claude" "custom skills"`
- `Anthropic "AI skills"`

Plus Hacker News keywords:

- `Anthropic skills`
- `Claude skills`
- `Claude agent skills`

## Filtering Rules

**ONLY posts articles that**:

1. Mention Anthropic OR Claude (company/product)
2. AND mention skills in AI context (agent skills, claude skills, etc.)
3. AND are NOT about jobs/careers/learning/resumes

**Better to miss articles than flood with noise.**

## Key Files

- `claude_skills_bot.py` - Main bot with strict filtering
- `config.yaml` - Search queries and settings
- `seen_items.json` - Tracks posted articles
- `README.md` - Full documentation
- `SETUP.md` - Detailed setup guide

## Need Help?

1. Check logs: `docker-compose logs -f claude-skills-bot`
2. Test manually: `python3 claude_skills_bot.py --check-once`
3. Enable debug logging in `config.yaml` (level: "DEBUG")
4. Read `SETUP.md` for troubleshooting

## Modifying Behavior

**Add search queries**: Edit `config.yaml`, restart bot
**Change poll interval**: Edit `config.yaml` (poll_interval_seconds)
**Adjust filtering**: Edit `claude_skills_bot.py`, rebuild container
**Change max age**: Edit `config.yaml` (max_age_hours)
