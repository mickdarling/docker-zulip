# Claude Skills Bot - Setup Guide

## Quick Start

### 1. Create the Zulip Stream

Run the setup script to create the stream and subscribe users:

```bash
cd /Users/mick/Developer/ClaudeCodeProjects/Zulip/bots/claude-skills-bot

# Install dependencies first (if not using Docker)
pip install -r requirements.txt

# Run setup
python3 setup_stream.py
```

This will:

- Create the `claude-skills-watch` stream
- Subscribe `user8@chat.dollhousemcp.com` to the stream
- Subscribe the formatter-bot (which posts the messages)

### 2. Build and Start the Bot

```bash
cd /Users/mick/Developer/ClaudeCodeProjects/Zulip

# Build the bot container
docker-compose build claude-skills-bot

# Start the bot
docker-compose up -d claude-skills-bot
```

### 3. Verify It's Running

Check the logs:

```bash
docker-compose logs -f claude-skills-bot
```

You should see:

```
Starting Claude Skills Bot (polling every 3600s)...
STRICT FILTERING ENABLED: Only Anthropic/Claude + Skills mentions
Monitoring source: google_news
Monitoring source: hackernews
Monitoring source: anthropic_site
Checking all sources for Claude Skills news...
```

## Testing

### Test Without Docker

Run a single check to test the bot without running it continuously:

```bash
cd /Users/mick/Developer/ClaudeCodeProjects/Zulip/bots/claude-skills-bot

# Install dependencies
pip install -r requirements.txt

# Run single check
python3 claude_skills_bot.py --check-once
```

This will:

- Check all sources once
- Apply filtering logic
- Post any relevant articles to Zulip
- Exit (won't run continuously)

### Check Filtering Logic

Enable debug logging to see what's being filtered:

1. Edit `config.yaml`:

   ```yaml
   logging:
     level: "DEBUG"
   ```

2. Run a test:
   ```bash
   python3 claude_skills_bot.py --check-once
   ```

You'll see logs like:

```
DEBUG: Filtered out - no Anthropic/Claude mention: Some Generic Article
DEBUG: Filtered out - no relevant skills mention: Anthropic Raises Funding
DEBUG: Filtered out - job/career related: AI Skills You Need for Your Resume
INFO: MATCH FOUND: Anthropic Launches Agent Skills Framework
```

## Manual Stream Creation (Alternative)

If you prefer to create the stream manually via the Zulip web UI:

1. Go to https://chat.dollhousemcp.com
2. Click the gear icon (Settings)
3. Select "Manage streams"
4. Click "Create stream"
5. Fill in:
   - **Stream name**: `claude-skills-watch`
   - **Description**: `Monitoring news about Anthropic's Agent Skills / Claude Skills feature for AGPL attribution tracking`
   - **Who can access**: Choose appropriate visibility
6. Click "Create"
7. Subscribe users:
   - Click on the stream
   - Click "Add subscribers"
   - Add: `user8@chat.dollhousemcp.com`

## Configuration

### Environment Variables

The bot requires `FORMATTER_BOT_API_KEY` to be set. This is already configured in:

- `.env` file (for manual runs)
- `docker-compose.yml` (for Docker runs)

### Adjusting Search Queries

Edit `config.yaml` to modify search behavior:

```yaml
sources:
  google_news:
    search_queries:
      - '"Anthropic" "agent skills"' # Add more queries
      - '"Claude" "custom skills"' # Or modify existing ones
```

### Adjusting Poll Interval

Change how often the bot checks for news:

```yaml
poll_interval_seconds: 3600 # 1 hour (default)
# poll_interval_seconds: 1800  # 30 minutes
# poll_interval_seconds: 7200  # 2 hours
```

### Adjusting Max Age

Control how old articles can be before they're ignored:

```yaml
sources:
  google_news:
    max_age_hours: 168 # 1 week (default)
    # max_age_hours: 336  # 2 weeks
    # max_age_hours: 72   # 3 days
```

## Troubleshooting

### Bot Not Posting Anything

1. **Check if it's filtering everything out**:

   ```bash
   # Enable debug logging in config.yaml
   docker-compose restart claude-skills-bot
   docker-compose logs -f claude-skills-bot
   ```

2. **Test with a single check**:

   ```bash
   docker-compose exec claude-skills-bot python claude_skills_bot.py --check-once
   ```

3. **Verify stream exists**:
   - Go to https://chat.dollhousemcp.com
   - Check if `claude-skills-watch` stream exists
   - Verify formatter-bot is subscribed

### Bot Can't Connect to Zulip

1. **Check API key**:

   ```bash
   grep FORMATTER_BOT_API_KEY .env
   ```

2. **Verify network connectivity**:

   ```bash
   docker-compose exec claude-skills-bot ping -c 3 chat.dollhousemcp.com
   ```

3. **Check Zulip service is running**:
   ```bash
   docker-compose ps zulip
   ```

### Too Many False Positives

If the bot is posting irrelevant articles:

1. **Review what's being posted** and identify patterns
2. **Strengthen filters** in `claude_skills_bot.py`:
   - Add exclusion patterns to `_is_relevant_skills_article()`
   - Example: Add `"job interview"` to job-related exclusions
3. **Rebuild and restart**:
   ```bash
   docker-compose build claude-skills-bot
   docker-compose restart claude-skills-bot
   ```

### Not Finding Relevant Articles

If the bot is missing articles you know exist:

1. **Check if they're too old**:
   - Increase `max_age_hours` in `config.yaml`

2. **Check if filters are too strict**:
   - Review `_is_relevant_skills_article()` logic
   - Add more keyword variations

3. **Add more search queries**:
   - Edit `config.yaml` and add search terms
   - Restart: `docker-compose restart claude-skills-bot`

## Monitoring

### View Logs

```bash
# Real-time logs
docker-compose logs -f claude-skills-bot

# Last 100 lines
docker-compose logs --tail=100 claude-skills-bot
```

### Check Seen Items

The bot tracks seen articles in `seen_items.json`:

```bash
cat bots/claude-skills-bot/seen_items.json | python3 -m json.tool | head -20
```

### Check Bot Status

```bash
docker-compose ps claude-skills-bot
```

Should show:

```
NAME                  STATUS         PORTS
claude-skills-bot     Up X minutes
```

## Stopping/Starting

```bash
# Stop the bot
docker-compose stop claude-skills-bot

# Start the bot
docker-compose start claude-skills-bot

# Restart the bot
docker-compose restart claude-skills-bot

# Stop and remove (seen_items.json persists)
docker-compose down claude-skills-bot

# Rebuild after code changes
docker-compose build claude-skills-bot
docker-compose up -d claude-skills-bot
```

## Maintenance

### Clearing Seen Items

If you want to reset and see all articles again:

```bash
# Backup first
cp bots/claude-skills-bot/seen_items.json bots/claude-skills-bot/seen_items.json.bak

# Reset
echo '{"items": [], "last_updated": null}' > bots/claude-skills-bot/seen_items.json

# Restart bot
docker-compose restart claude-skills-bot
```

### Updating Search Queries

1. Edit `bots/claude-skills-bot/config.yaml`
2. Restart: `docker-compose restart claude-skills-bot`
3. No rebuild needed (config is mounted at runtime)

### Updating Bot Code

1. Edit `bots/claude-skills-bot/claude_skills_bot.py`
2. Rebuild: `docker-compose build claude-skills-bot`
3. Restart: `docker-compose up -d claude-skills-bot`

## Files Overview

```
bots/claude-skills-bot/
├── claude_skills_bot.py    # Main bot code with filtering logic
├── config.yaml             # Configuration (search queries, intervals, etc.)
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container image definition
├── README.md              # Documentation and design philosophy
├── SETUP.md               # This file - setup and operations guide
├── setup_stream.py        # Script to create Zulip stream
└── seen_items.json        # Persistent storage (created at runtime)
```

## Next Steps

After setup:

1. Monitor the logs for the first few hours to verify filtering is working
2. Adjust search queries or filters as needed
3. Subscribe additional users to the stream if needed
4. Consider adjusting poll interval based on expected news volume

## Support

For issues or questions:

- Check logs: `docker-compose logs -f claude-skills-bot`
- Review filtering logic in `claude_skills_bot.py`
- Consult `README.md` for filtering philosophy
- Test with `--check-once` flag for debugging
