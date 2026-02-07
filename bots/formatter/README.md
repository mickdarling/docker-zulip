# Zulip Formatter Bot

A bot that watches Zulip streams and reposts formatted versions of messages based on configurable rules. Perfect for transforming verbose webhook notifications into clean, emoji-rich summaries.

## Features

- **Stream watching**: Monitor any public stream for new messages
- **Pattern matching**: Match messages using regex patterns
- **Template formatting**: Transform messages using customizable templates with variable substitution
- **Emoji support**: Add emoji indicators for different message types
- **Flexible routing**: Post formatted messages to same or different streams/topics
- **Loop prevention**: Automatically ignores its own messages

## Quick Start

### 1. Create a Zulip Bot

1. Go to Zulip Settings → Personal settings → Bots
2. Click "Add a new bot"
3. Choose "Generic bot" as the bot type
4. Name it something like "Formatter Bot"
5. Save the API key

### 2. Configure Environment

```bash
cd bots/formatter
cp .env.example .env
# Edit .env with your bot credentials
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Rules

Edit `config.yaml` to define your formatting rules. See examples in the file.

### 5. Run the Bot

```bash
# Direct
python formatter_bot.py

# Or with Docker
docker build -t zulip-formatter .
docker run -d --env-file .env zulip-formatter
```

## Configuration

### Rules Structure

Each rule has:

```yaml
rules:
  - name: "rule-name" # Identifier for logging
    enabled: true # Toggle rule on/off
    source:
      stream: "github" # Stream to watch
      topic_pattern: ".*/checks" # Optional regex for topic filtering
    target:
      stream: "github" # Where to post (can be different)
      topic: "{source_topic}" # Topic template with variables
    match:
      patterns:
        - name: "success"
          pattern: "passed" # Regex to match
    format:
      success: "✅ {repo} passed" # Template for matched pattern
      default: null # null = don't repost unmatched
```

### Available Variables

Templates can use these variables:

| Variable          | Description                 |
| ----------------- | --------------------------- |
| `{source_topic}`  | Original message topic      |
| `{repo}`          | Extracted repository name   |
| `{branch}`        | Extracted branch name       |
| `{url}`           | First URL found in message  |
| `{number}`        | PR/issue number (from #123) |
| `{title}`         | Text in **bold**            |
| `{author}`        | Message sender name         |
| `{content}`       | Full message content        |
| `{short_summary}` | First 100 chars of content  |

## Example: GitHub Check Formatter

Transform this verbose GitHub notification:

```
[DollhouseMCP/mcp-server] check_run completed
All checks have passed for commit abc1234
Branch: develop
...lots more details...
```

Into this clean summary:

```
✅ **All checks passed** on `DollhouseMCP/mcp-server`
Branch: `develop` | [View Details](https://github.com/...)
```

## Running with Docker Compose

Add to your main `docker-compose.yml`:

```yaml
services:
  formatter-bot:
    build: ./bots/formatter
    restart: unless-stopped
    environment:
      - ZULIP_SITE=https://chat.dollhousemcp.com
      - ZULIP_EMAIL=${FORMATTER_BOT_EMAIL}
      - ZULIP_API_KEY=${FORMATTER_BOT_API_KEY}
```

## Troubleshooting

### Bot not seeing messages

- Ensure the bot is subscribed to the source streams
- Check that `all_public_streams` is supported on your Zulip instance

### Messages not matching

- Enable DEBUG logging to see pattern matching details
- Test your regex patterns separately

### Loop/duplicate messages

- The bot tracks processed message IDs to prevent duplicates
- It also ignores messages from its own email address
