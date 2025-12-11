# Session Notes - December 10, 2025 (Afternoon)

## Session Summary
Continued from morning session. Fixed Merview integration build issues, set up private email streams, created MCP News Bot, and documented everything in the infrastructure repository.

## Major Accomplishments

### 1. Merview Integration - FIXED AND WORKING
- **Root cause identified**: Dockerfile Stage 2 was copying custom files AFTER webpack compilation, overwriting the compiled bundles with uncompiled source
- **Fix applied**: Removed duplicate `COPY custom_zulip_files/` and `cp -rf` from Stage 2 (lines 63-74 in old Dockerfile)
- **Additional fix**: Task agent removed incorrect `markdown_audio.hbs` import that was causing webpack build failures
- **Verification**: `strings` command confirms "merview" code in compiled webpack bundles
- **Version tag**: Console shows `[Zulip Custom Build] merview-v2 | 2025-12-10`
- **Status**: Lozenge appears next to .md file attachments, links to Merview correctly
- **Note**: Merview itself needs whitelist updated to allow `chat.dollhousemcp.com` URLs

### 2. Private Email Streams Setup
**Changed email notification architecture from public to private:**

| Email Address | Stream | Visibility |
|--------------|--------|------------|
| `mick@dollhousemcp.com` | `#email-mick` | Private (just Mick) |
| `support@dollhousemcp.com` | `#email` | Public (team) |
| `sales@dollhousemcp.com` | `#email` | Public (team) |
| `info@dollhousemcp.com` | `#email` | Public (team) |
| `hello@dollhousemcp.com` | `#email` | Public (team) |
| `contact@dollhousemcp.com` | `#email` | Public (team) |

**Benefits:**
- Users can mute their email stream (vacation mode)
- Private emails stay private
- Team emails visible to all

**Config file**: `/Users/mick/Developer/ClaudeCodeProjects/Zulip/bots/email-notifier/config.yaml`

### 3. MCP News Bot - Created and Running
**Purpose**: Monitor MCP ecosystem news and post to `#mcp-news` channel

**Sources monitored:**
- GitHub releases (MCP repos, LangChain, CrewAI, AutoGPT, Zulip)
- Hacker News (keyword search via Algolia API)
- Reddit (r/LocalLLaMA, r/MachineLearning, r/artificial)

**Categories:**
- MCP Updates
- New Tools
- Dollhouse MCP
- Merview
- Zulip
- Anthropic
- AI Agents
- General

**Location**: `/Users/mick/Developer/ClaudeCodeProjects/Zulip/bots/mcp-news-bot/`

**Files created:**
- `mcp_news_bot.py` - Main bot (16KB)
- `config.yaml` - Configuration
- `requirements.txt` - Dependencies (zulip, pyyaml, requests, python-dotenv)
- `Dockerfile` - Container definition
- `README.md` - Documentation
- `.env` - Credentials (FORMATTER_BOT_API_KEY)

**Bugs fixed:**
- Date parsing for Hacker News (handle both formats with/without milliseconds)
- Removed non-existent GitHub repos from config
- Removed 404-returning Reddit subreddit

**Status**: Running in Docker, polling every hour

### 4. Gravatar Setup
- Added `mick@dollhousemcp.com` to Gravatar account
- Zulip will pull avatar from Gravatar automatically

### 5. Infrastructure Documentation
**Created comprehensive docs in DollhouseMCP/infrastructure:**

```
docs/
├── zulip-setup.md           # Complete setup guide
├── custom-zulip-builds.md   # How to customize Zulip
├── bots/
│   ├── README.md            # Bot overview, adding new bots
│   ├── email-notifier.md    # Email bot documentation
│   ├── formatter-bot.md     # Formatter bot documentation
│   └── mcp-news-bot.md      # MCP News bot documentation
└── integrations/
    └── merview.md           # Merview integration docs
```

**Total**: ~72 KB of documentation

### 6. GitHub Issues Created
| Issue | Title |
|-------|-------|
| #22 | MCP News Bot - Real-time news aggregation |
| #23 | Claude Bot - AI assistant integration |
| #24 | Daily/Weekly Digest Bot - Automated summaries |

## Files Modified This Session

### Dockerfile
- Removed duplicate custom file copy from Stage 2
- Custom files now only copied in Stage 1 (before webpack)

### docker-compose.yml
- Added `mcp-news-bot` service

### bots/email-notifier/config.yaml
- Changed from wildcard `*@dollhousemcp.com` to specific addresses
- Added `mick@dollhousemcp.com` → private `#email-mick`
- Added public catch-all addresses → `#email`

### bots/mcp-news-bot/ (NEW)
- Complete new bot created

### custom_zulip_files/web/src/rendered_markdown.ts
- Removed incorrect `markdown_audio.hbs` import
- Merview integration code intact

## Running Services
```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```
- zulip-zulip-1 (main Zulip)
- zulip-database-1 (PostgreSQL)
- zulip-redis-1
- zulip-rabbitmq-1
- zulip-memcached-1
- zulip-formatter-bot-1
- zulip-email-notifier-1
- zulip-mcp-news-bot-1 (NEW)

## Zulip Channels/Streams
- `#general` - General discussion
- `#github` - GitHub notifications
- `#email` - Public email catch-all
- `#email-mick` - Private (Mick's emails only)
- `#mcp-news` - MCP ecosystem news (NEW)

## Known Issues / Future Work

### Merview Whitelist
- Merview returns 404 for `chat.dollhousemcp.com` URLs
- Need to update Merview's URL whitelist to allow this domain
- The Zulip integration is working correctly

### Future Bot Development (Issues #22-24)
1. **Claude Bot** (#23) - AI assistant in Zulip
2. **Digest Bot** (#24) - Daily/weekly summaries
3. Both depend on Claude API integration

### MCP News Bot Enhancements
- Add more GitHub repos as they're created
- Phase 2: Claude-powered filtering and summarization
- Consider adding Twitter/X monitoring

## Security Discussion
- Discussed risks of inviting users from China to Zulip
- Main concern: Drawing attention to home server infrastructure
- Recommendation: Use established services for sensitive communications from monitored regions
- Content encryption is less of a concern than metadata exposure

## Commands Reference

### Rebuild Zulip (after custom file changes)
```bash
cd ~/Developer/ClaudeCodeProjects/Zulip
docker compose build --no-cache zulip
docker compose up -d --force-recreate zulip
```

### Verify Merview in bundles
```bash
docker exec zulip-zulip-1 bash -c 'strings /home/zulip/deployments/current/prod-static/serve/webpack-bundles/app.*.js | grep -i merview'
```

### Restart a bot
```bash
docker compose restart email-notifier
docker compose restart mcp-news-bot
```

### Check bot logs
```bash
docker logs zulip-mcp-news-bot-1
docker logs zulip-email-notifier-1
```

### Create private stream via API
```bash
curl -X POST "https://chat.dollhousemcp.com/api/v1/users/me/subscriptions" \
  -u "formatter-bot@chat.dollhousemcp.com:API_KEY" \
  -d 'subscriptions=[{"name": "stream-name", "description": "Description"}]' \
  -d 'invite_only=true' \
  -d 'principals=["user8@chat.dollhousemcp.com"]'
```

## Credentials Reference
- Formatter Bot: `formatter-bot@chat.dollhousemcp.com` (API key in .env)
- Email Bot: `email-bot-bot@chat.dollhousemcp.com`
- Your Zulip username: `user8@chat.dollhousemcp.com` (display: Mick Darling)

## Next Session Priorities
1. Update Merview whitelist to allow Zulip URLs
2. Test Merview integration end-to-end
3. Consider implementing Claude Bot for AI features
4. Monitor MCP News Bot performance
