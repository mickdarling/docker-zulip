# Merview GitHub Bot

A Zulip bot that monitors GitHub repositories and posts activity updates to the Merview Zulip instance.

## Features

This bot monitors GitHub repositories and posts notifications for:

- **Releases/Tags**: New releases and version tags
- **Issues**: Newly opened issues
- **Pull Requests**: Opened, merged, and closed PRs
- **Stars**: Milestone announcements (10, 50, 100, 250, 500, 1000, etc.)
- **Forks**: New repository forks
- **Commits**: Summarized commits to main/master branch (not every commit)

## Setup

### 1. Create a Zulip Bot Account

1. Go to your Merview Zulip instance: `https://chat.merview.com`
2. Navigate to **Settings** > **Your bots**
3. Click **Add a new bot**
4. Configure:
   - **Bot type**: Generic bot
   - **Full name**: Merview GitHub Bot
   - **Email**: `merview-github-bot@chat.merview.com` (or similar)
5. Copy the API key

### 2. Configure Environment Variables

Edit the `.env` file:

```bash
# REQUIRED: Zulip API key for the bot
MERVIEW_GITHUB_BOT_API_KEY=your_api_key_here

# OPTIONAL: GitHub Personal Access Token
# Increases rate limit from 60/hour to 5000/hour
# GITHUB_TOKEN=your_github_token_here
```

**GitHub Token (Optional but Recommended):**

- Without a token: 60 API requests/hour (may be insufficient)
- With a token: 5000 API requests/hour
- Create at: https://github.com/settings/tokens
- No special scopes needed for public repositories

### 3. Configure Repositories

Edit `config.yaml` and update the `repositories` list:

```yaml
repositories:
  - "merview/merview"
  - "merview/docs"
  - "merview/backend"
  # Add more repos as needed
```

### 4. Configure Zulip Connection

Update `config.yaml` with your Merview Zulip instance details:

```yaml
zulip:
  site: "https://chat.merview.com"
  email: "merview-github-bot@chat.merview.com"
  api_key: "${MERVIEW_GITHUB_BOT_API_KEY}"
  stream: "github"
```

Make sure the `github` stream exists in your Zulip instance.

### 5. Run with Docker Compose

The bot is already configured in the main `docker-compose.yml`. Just start it:

```bash
# From the main Zulip directory
docker-compose up -d merview-github-bot

# View logs
docker-compose logs -f merview-github-bot
```

### 6. Run Standalone (Development)

```bash
# Install dependencies
pip install -r requirements.txt

# Test (check once and exit)
python merview_github_bot.py --check-once

# Run continuously
python merview_github_bot.py
```

## Configuration

### Polling Interval

Default: 600 seconds (10 minutes)

```yaml
poll_interval_seconds: 600
```

### Event Types

Enable/disable different event types in `config.yaml`:

```yaml
events:
  releases:
    enabled: true
    max_age_hours: 168 # Only post releases from last week

  issues:
    enabled: true
    max_age_hours: 24 # Only post issues from last day

  pull_requests:
    enabled: true
    max_age_hours: 24

  stars:
    enabled: true
    milestones: [10, 50, 100, 250, 500, 1000, 2500, 5000, 10000]

  forks:
    enabled: true
    max_age_hours: 24

  commits:
    enabled: true
    max_age_hours: 24
    max_per_summary: 10 # Max commits to show in one message
```

### Topic Format

Control how topics are named:

```yaml
# Use just the repo name
topic_format: "{repo}"  # e.g., "merview"

# Use full owner/repo path
topic_format: "{owner}/{repo}"  # e.g., "merview/merview"
```

## How It Works

1. **Polling**: The bot checks configured repositories every 10 minutes (configurable)
2. **Deduplication**: Uses `seen_items.json` to track what's already been posted
3. **Rate Limiting**: Automatically respects GitHub API rate limits
4. **Persistence**: State is saved between restarts via volume mount

## Troubleshooting

### Rate Limiting

If you see "Rate limit exceeded" errors:

1. Add a GitHub token to `.env` (recommended)
2. Increase `poll_interval_seconds` in `config.yaml`
3. Monitor fewer repositories

### No Messages Appearing

1. Check the Zulip stream exists: `#github`
2. Verify the bot has permission to post to the stream
3. Run with `--check-once` flag to test
4. Check logs: `docker-compose logs merview-github-bot`

### Bot Not Starting

1. Verify `.env` file has correct API key
2. Check `config.yaml` syntax is valid
3. Ensure repositories exist and are accessible
4. View detailed logs with `docker-compose logs merview-github-bot`

## Example Messages

### Release

```
**New Release: v1.2.0**
**Tag:** v1.2.0
**Published by:** johndoe
**Date:** 2025-12-10 14:30 UTC
**URL:** https://github.com/merview/merview/releases/tag/v1.2.0

**Release Notes:**
Added new dashboard features...
```

### Pull Request Merged

```
**Pull Request Merged #42: Add dark mode support**
**Author:** janedoe
**Merged:** 2025-12-10 15:45 UTC
**URL:** https://github.com/merview/merview/pull/42
```

### Star Milestone

```
**Star Milestone Reached!**
**Repository:** merview/merview
**Stars:** 1000 ⭐
**Milestone:** 1000
**URL:** https://github.com/merview/merview
```

### Commit Summary

```
**New Commits to main**
**Repository:** merview/merview
**Count:** 5 new commits

- `a1b2c3d` Fix authentication bug - John Doe
- `e4f5g6h` Update dependencies - Jane Smith
- `i7j8k9l` Add unit tests - Bob Johnson
- `m1n2o3p` Improve documentation - Alice Williams
- `q4r5s6t` Refactor API client - Charlie Brown

**View all:** https://github.com/merview/merview/commits/main
```

## File Structure

```
merview-github-bot/
├── .env                      # Environment variables (API keys)
├── .gitignore               # Git ignore rules
├── config.yaml              # Bot configuration
├── Dockerfile               # Container image
├── merview_github_bot.py    # Main bot logic
├── README.md                # This file
├── requirements.txt         # Python dependencies
└── seen_items.json          # State (auto-generated)
```

## Support

For issues or questions:

1. Check the logs: `docker-compose logs merview-github-bot`
2. Test with: `python merview_github_bot.py --check-once`
3. Review GitHub API status: https://www.githubstatus.com/

## License

This bot is part of the Merview Zulip deployment.
