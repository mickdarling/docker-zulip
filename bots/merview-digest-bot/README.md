# Merview Weekly Digest Bot

A Zulip bot that generates weekly summaries of Merview activity, perfect for creating LinkedIn blog posts. The bot compiles GitHub statistics, news mentions, and Zulip community discussions into a comprehensive, professionally formatted digest.

## Features

- **GitHub Activity Summary**
  - New releases with links and dates
  - Pull requests merged
  - Issues closed
  - Active contributor count
  - Repository statistics (stars, forks)
  - Notable PRs and issues highlighted

- **News & Mentions**
  - Aggregates news items from merview-news-bot
  - Includes news from Zulip #news stream
  - Chronological listing with links

- **Community Activity**
  - Message counts across monitored streams
  - Active user statistics
  - Most active discussion topics
  - Engagement metrics

- **LinkedIn-Ready Output**
  - Professional formatting suitable for public sharing
  - Condensed "LinkedIn Draft" section at the end
  - Highlight-focused summary
  - Appropriate hashtags and calls-to-action

## Setup

### 1. Create a Zulip Bot

1. Log into your Merview Zulip instance
2. Go to Settings > Your bots
3. Create a new bot named "Merview Digest Bot"
4. Copy the API key

### 2. Create the Digest Stream

1. In your Merview Zulip instance, create a new stream called `digest`
2. Set appropriate permissions (typically public or team-accessible)

### 3. Configure Environment Variables

Edit `.env` and set:

```bash
MERVIEW_DIGEST_BOT_API_KEY=your_actual_api_key_here

# Optional but recommended: GitHub token for higher API rate limits
GITHUB_TOKEN=your_github_token_here
```

To create a GitHub token:

- Go to https://github.com/settings/tokens
- Generate a new token (classic)
- Select scope: `public_repo` (for public repositories)
- Copy the token to your `.env` file

### 4. Update Configuration

Edit `config.yaml` and update:

```yaml
zulip:
  site: "https://chat.merview.com" # Your Merview Zulip URL
  email: "digest-bot@chat.merview.com" # Bot's email address
  digest_stream: "digest"

github:
  repos:
    - "merview/core"
    - "merview/client"
    # Add your actual repository names

zulip_monitoring:
  streams:
    - "general"
    - "development"
    - "news"
    # Add streams you want to monitor

schedule:
  day: "sunday" # When to generate digest
  hour: 18 # Hour in UTC (18 = 6pm UTC)
```

### 5. Run the Bot

#### Using Docker (Recommended)

The bot is included in the main docker-compose.yml:

```bash
# Build and start the bot
docker-compose up -d merview-digest-bot

# View logs
docker-compose logs -f merview-digest-bot

# Stop the bot
docker-compose stop merview-digest-bot
```

#### Using Python Directly

```bash
# Install dependencies
pip install -r requirements.txt

# Run in scheduled mode (runs continuously)
python merview_digest_bot.py

# Generate digest once for current week and exit
python merview_digest_bot.py --check-once

# Generate digest for a specific week (any date in that week)
python merview_digest_bot.py --date 2025-12-09
```

## Usage

### Scheduled Operation

By default, the bot runs continuously and generates a digest weekly on the configured day/time. The digest is posted to the `#digest` stream with a topic like "Week of Dec 9-15, 2025".

### Manual Digest Generation

To generate a digest manually:

```bash
# Current week
docker-compose exec merview-digest-bot python merview_digest_bot.py --check-once

# Specific week (provide any date within that week)
docker-compose exec merview-digest-bot python merview_digest_bot.py --date 2025-12-09
```

### Converting to LinkedIn Post

The digest includes a "LinkedIn Draft" section at the end with a condensed version ready for adaptation:

1. Copy the content from the digest post in Zulip
2. Focus on the "LinkedIn Draft" section
3. Customize with:
   - Personal voice/tone
   - Specific project highlights
   - Relevant images or screenshots
   - Appropriate links to your website/GitHub
4. Add relevant hashtags
5. Post to LinkedIn!

## Digest Format

The digest includes the following sections:

### GitHub Activity

- **Releases**: New versions released during the week
- **Development**: PR and issue statistics, contributor count
- **Notable PRs**: Top pull requests by activity
- **Repository Stats**: Current stars and forks

### News & Mentions

- Links to all news items discovered during the week
- Sourced from the merview-news-bot and news stream

### Community Activity

- Total message count across monitored streams
- Active user count
- Most active discussion topics with message counts

### LinkedIn Draft

- Condensed highlights perfect for social media
- Professional tone suitable for public sharing
- Pre-formatted with hashtags

## Configuration Options

See `config.yaml` for all available options:

- `schedule`: Configure when digests are generated
- `github.repos`: List of repositories to monitor
- `zulip_monitoring.streams`: Streams to analyze for community activity
- `digest`: Formatting options (max items to include)
- `logging`: Log level and optional log file

## Rate Limits

### GitHub API

- **Without token**: 60 requests/hour (may be insufficient for multiple repos)
- **With token**: 5000 requests/hour (recommended)

If you see GitHub API errors, add a `GITHUB_TOKEN` to your `.env` file.

### Zulip API

No rate limit concerns for typical usage.

## Troubleshooting

### Bot not posting

1. Check logs: `docker-compose logs merview-digest-bot`
2. Verify Zulip bot has permission to post to the digest stream
3. Confirm API key is correct in `.env`

### Missing GitHub data

1. Verify repository names in `config.yaml` are correct (format: `owner/repo`)
2. Check if repositories are public (or token has access if private)
3. Add a GitHub token to avoid rate limits

### Missing news items

1. Verify merview-news-bot is running and posting to #news stream
2. Check that news items exist for the week being digested
3. Ensure bot has read access to the news stream

### Digest appears empty

This is normal for weeks with minimal activity. The bot will still generate a digest noting the quiet week.

## Development

### Testing

Test digest generation without waiting for the scheduled time:

```bash
# Test with current week
python merview_digest_bot.py --check-once

# Test with specific historical week
python merview_digest_bot.py --date 2025-11-15
```

### Debugging

Enable debug logging in `config.yaml`:

```yaml
logging:
  level: "DEBUG"
  file: "digest_bot.log" # Optional: log to file
```

## Privacy & Security

- The bot only reads public GitHub data (or private repos if token has access)
- Only monitors Zulip streams it has explicit access to
- API keys should be kept secure and never committed to version control
- The `.gitignore` file protects `.env` from being committed

## License

Same as parent Zulip project.
