# Session Notes - December 9, 2025

## Overview
Extended session focused on Zulip infrastructure planning and GitHub issue creation. Built an email notification bot, then pivoted to comprehensive backlog planning for the infrastructure repository. Created 21 GitHub issues covering bots, integrations, and operational infrastructure.

---

## What Was Accomplished

### 1. Email Notification Bot (Completed)
- **Location:** `/Users/mick/Developer/ClaudeCodeProjects/Zulip/bots/email-notifier/`
- **Function:** Watches Gmail for emails to `*@dollhousemcp.com`, posts notifications to Zulip `#email` stream
- **Running:** Docker container `zulip-email-notifier-1`

#### Setup Completed:
- Google Cloud project: `email-notifications-480719`
- Gmail API OAuth credentials configured
- Token authenticated and saved
- Bot created via Zulip API: `email-bot-bot@chat.dollhousemcp.com`
- API key stored in `.env`: `EMAIL_BOT_API_KEY`

#### Files Created:
- `email_notifier.py` - Main bot code
- `config.yaml` - Configuration with environment variable support
- `Dockerfile` - Container config
- `requirements.txt` - Python dependencies
- `credentials.json` - Google OAuth credentials
- `token.json` - Authenticated Gmail token

### 2. Infrastructure Repository Issues (21 Total)

Created comprehensive backlog in https://github.com/DollhouseMCP/infrastructure

#### Bots & Integrations

| # | Title | Description |
|---|-------|-------------|
| #1 | Claude Bot (Epic) | Interactive AI assistant in Zulip - full Claude Code integration |
| #2 | Claude Bot Phase 1: MVP | Basic message relay between Zulip and Claude Code |
| #3 | Claude Bot Phase 2: Context | Conversation context and session management |
| #4 | Claude Bot Phase 3: Multi-env | Mac Studio + Docker sandbox environments |
| #5 | Claude Bot Phase 4: Advanced | Streaming, model switching, DollhouseMCP integration |
| #6 | Calendar Bot | Daily agenda and event notifications |
| #7 | Matterbridge: Discord | Self-hosted bridge for Discord ↔ Zulip |
| #8 | Cross-Project Status Bot | Daily summary of all projects (CI, PRs, issues) |
| #9 | TTS Alert Bot | Audible announcements via macOS `say` command |
| #10 | Local Meeting Transcription | Privacy-first transcription with Whisper |
| #11 | iMessage Bridge | Via Matrix + mautrix-imessage + Matterbridge |
| #12 | Google Chat Bridge | Creative workarounds (Gmail notifications in, API out) |
| #13 | Zoom Integration | Native video calls + meeting notifications |
| #21 | Merview Integration | Render Zulip markdown files in Merview |

#### Infrastructure & Operations

| # | Title | Description |
|---|-------|-------------|
| #14 | Health Monitoring | Uptime checks for all services |
| #15 | Backup & Recovery | Automated backups with verification |
| #16 | Secrets Management | Bitwarden/Vaultwarden self-hosted setup |
| #17 | Log Aggregation | Centralized logging with LLM-friendly parsing |
| #18 | Documentation & Runbooks | Operational knowledge base |
| #19 | Container Orchestration | Unified startup and management |
| #20 | Resource Dashboard | System monitoring and visualization |

### 3. Zulip Development Fork Created
- **Fork:** https://github.com/mickdarling/zulip
- **Local:** `/Users/mick/Developer/ClaudeCodeProjects/zulip-dev`
- **Purpose:** Explore codebase for Merview integration upstream contribution

---

## Key Decisions Made

### Claude Bot Architecture
- Bot is a **thin conduit** - doesn't need file access itself
- Claude Code runs separately with full capabilities
- Multi-environment support: Mac Studio (full power) + Docker sandbox (safe for demos)
- Security via Zulip channel permissions + user allowlist

### Secrets Management
- Going with **Vaultwarden** (lightweight Bitwarden server)
- Single instance for personal + work (separated via Organizations/Collections)
- Self-hosted, open source, works on macOS/iOS

### Merview Integration Path
- **Primary goal:** Submit as official Zulip integration
- Add "View in Merview" to message action menu for `.md` files
- Linkifiers won't work (can't create two links, can't change display text)
- Bot fallback is awkward but functional if needed

### Platform Bridges
- **iMessage:** Possible via mautrix-imessage → Matrix → Matterbridge → Zulip
- **Google Chat:** Limited - can post TO it, but can't pull FROM it (workarounds possible)
- **Discord:** Matterbridge supports natively
- **Zoom:** Native Zulip integration exists

---

## Current Running Services

```
# Dollhouse MCP Zulip (7 containers)
~/Developer/ClaudeCodeProjects/Zulip/
- zulip-database-1
- zulip-memcached-1
- zulip-rabbitmq-1
- zulip-redis-1
- zulip-zulip-1
- zulip-formatter-bot-1
- zulip-email-notifier-1  ← NEW

# Merview Zulip (still 6 containers)
~/Developer/ClaudeCodeProjects/Merview-Zulip/
- merview-zulip-database-1
- merview-zulip-memcached-1
- merview-zulip-rabbitmq-1
- merview-zulip-redis-1
- merview-zulip-zulip-1
- merview-zulip-formatter-bot-1
```

---

## New Credentials Created

### Email Bot (DollhouseMCP)
| Item | Value |
|------|-------|
| Bot Email | email-bot-bot@chat.dollhousemcp.com |
| API Key | ucXGUZxU8kRzvcdzsGAKEovqaNq64NbJ |
| Stored in | `.env` as `EMAIL_BOT_API_KEY` |

### Google Cloud (Gmail API)
| Item | Value |
|------|-------|
| Project | email-notifications-480719 |
| Client ID | 153283565876-luuq5rjvmhqjmdthf54tde8bl18qrg3d.apps.googleusercontent.com |
| Credentials | `bots/email-notifier/credentials.json` |
| Token | `bots/email-notifier/token.json` |

---

## New Zulip Streams Created

- `#email` - Email notifications (DollhouseMCP)

---

## Research Findings

### Matterbridge
- Self-hosted Go application
- Bridges: Discord, Slack, Telegram, IRC, Matrix, Teams, Zulip, WhatsApp, Keybase, Gitter, Twitch, Nextcloud Talk, Mumble, VK, Harmony, and more
- GitHub: https://github.com/42wim/matterbridge
- Configuration via TOML file defining "gateways"

### Zulip Security
- TLS everywhere (in transit)
- Self-hosted = you control the server
- Not E2E encrypted, but data only unencrypted in server memory (which you control)

### Zulip Extensibility
- No plugin system for custom message actions
- Linkifiers can auto-link patterns but limited (one link, can't change display text)
- Custom integrations via bots, webhooks, or PRs to upstream

### Voice Tools Researched
- **Talon Voice + Cursorless** - Voice-controlled coding (system-wide)
- **Wispr Flow** - Voice dictation for chat
- User already has SuperWhisper for dictation
- TTS possible via macOS `say` command

---

## Key Files & Locations

| Item | Location |
|------|----------|
| Dollhouse Zulip | `~/Developer/ClaudeCodeProjects/Zulip/` |
| Merview Zulip | `~/Developer/ClaudeCodeProjects/Merview-Zulip/` |
| Email Notifier Bot | `~/Developer/ClaudeCodeProjects/Zulip/bots/email-notifier/` |
| Formatter Bot | `~/Developer/ClaudeCodeProjects/Zulip/bots/formatter/` |
| Zulip Dev Fork | `~/Developer/ClaudeCodeProjects/zulip-dev/` |
| Infrastructure Repo | `~/Developer/DollhouseMCP Org/Active/infrastructure/` |
| Cloudflare Tunnel Config | `/etc/cloudflared/config.yml` |
| Gmail Credentials | `bots/email-notifier/credentials.json` |

---

## Next Session Tasks

### High Priority
1. **Explore Zulip codebase** for Merview integration (how Zoom integration works)
2. **Draft proposal issue** for zulip/zulip repo
3. **Start Claude Bot MVP** (#2)

### When Ready
4. Set up Vaultwarden (#16)
5. Set up health monitoring (#14)
6. Set up backup system (#15)
7. Configure Matterbridge for Discord (#7)

---

## Useful Commands

### Email Notifier Bot
```bash
# View logs
docker logs zulip-email-notifier-1 -f

# Restart
cd ~/Developer/ClaudeCodeProjects/Zulip
docker compose restart email-notifier

# Rebuild after changes
docker compose build email-notifier && docker compose up -d email-notifier
```

### View All Infrastructure Issues
```bash
gh issue list --repo DollhouseMCP/infrastructure
```

### Zulip API (create bots, streams, etc.)
```bash
# Create bot
curl -X POST "https://chat.dollhousemcp.com/api/v1/bots" \
  -u "mick@dollhousemcp.com:bAWz1KRzmkHv7hJhS4HtToHDHiO3KROp" \
  -d "full_name=Bot Name" \
  -d "short_name=bot-name"

# Create stream
curl -X POST "https://chat.dollhousemcp.com/api/v1/users/me/subscriptions" \
  -u "mick@dollhousemcp.com:bAWz1KRzmkHv7hJhS4HtToHDHiO3KROp" \
  -d 'subscriptions=[{"name":"stream-name","description":"Description"}]'
```

---

## Notes

- Email notifier watches Gmail inbox for unread emails - once read, won't re-notify
- All email from dollhousemcp.com and merview.com forwards to mick@mickdarling.com
- Merview.com uses Cloudflare Email Routing (forwards to Gmail)
- Dollhouse MCP uses Google Workspace
- Runbook = step-by-step instructions for specific operations (like a recipe)
- Vaultwarden = lightweight self-hosted Bitwarden server (50MB RAM vs 2-4GB)
- Single Vaultwarden instance works for personal + work (use Organizations to separate)

---

## Session Stats
- Duration: Extended session
- Issues created: 21
- Bots deployed: 1 (email-notifier)
- Repos forked: 1 (zulip)
- Research completed: Slack/chat integrations, voice tools, platform bridges

---

# Evening Session - December 9, 2025 (continued)

## Overview
Explored Zulip codebase for Merview integration. Implemented "Open in Merview" feature for `.md` file attachments. Learned hard lesson about Docker build resource consumption.

---

## What Was Accomplished

### 1. Zulip Codebase Research (Completed)
Used Task agents to explore the zulip-dev fork. Key findings:

**Architecture:**
- Zulip uses jQuery + Handlebars (not React/Vue)
- Frontend: TypeScript modules in `/web/src/`
- Templates: Handlebars in `/web/templates/`
- Backend: Django/Python in `/zerver/`

**Key Files for Message Actions:**
| File | Purpose |
|------|---------|
| `web/src/rendered_markdown.ts` | Client-side post-processing of rendered messages |
| `web/src/message_actions_popover.ts` | The "..." menu handlers |
| `web/templates/message_controls.hbs` | Inline action icons (emoji, star, etc.) |
| `web/src/popover_menus_data.ts` | Context data for conditional menu items |

**Attachment Detection:**
- Attachments are links with `href` starting with `/user_uploads/`
- Pattern: `<a href="/user_uploads/path/filename.ext">filename.ext</a>`

### 2. GitHub Issues Created on mickdarling/zulip Fork

| Issue | Title | Description |
|-------|-------|-------------|
| #1 | Extensible Message Action Icons | Proposal to make inline message icons configurable |
| #2 | Open in Merview for .md attachments | Implementation plan for Merview link injection |

**Issue #1 (Extensibility)** proposes three approaches:
- Option A: Configuration-based JSON settings
- Option B: JavaScript plugin system (`zulip.message_actions.register()`)
- Option C: Linkifier-style admin UI

### 3. Merview Integration Implementation (Code Complete)

Created custom overlay files for Docker build:

**Files Created:**
```
custom_zulip_files/
├── web/
│   ├── src/
│   │   └── rendered_markdown.ts  # Modified with Merview link injection
│   └── styles/
│       └── rendered_markdown.css  # Styling for .merview-link class
```

**How it works:**
- Finds all `<a href="/user_uploads/...">` links ending in `.md`
- Injects "Merview" link after each one pointing to `https://merview.com/view?url=...`
- Styled as a light blue pill button, with dark mode support

**docker-compose.yml updated:**
- Changed from `image: zulip/docker-zulip:11.4-0` to `build: .`
- This triggers the custom_zulip_files overlay during build

### 4. Lesson Learned: Docker Build Resource Consumption

**The Incident:**
Started `docker compose build zulip` which compiles Zulip from source (TypeScript, Webpack, etc.). The build consumed so much CPU/RAM that it caused the running Zulip container's processes to get OOM-killed (SIGKILL). chat.dollhousemcp.com went down briefly.

**Root Cause:**
- Docker build runs Webpack compilation of ~800 TypeScript files
- This consumed 400%+ CPU and multiple GB of RAM
- Linux OOM killer started terminating processes in the running Zulip container
- `zulip-tornado` (real-time events) kept getting killed and restarting

**Symptoms in logs:**
```
WARN exited: zulip-tornado (terminated by SIGKILL; not expected)
INFO spawned: 'zulip-tornado' with pid XXXX
```

**Resolution:**
- Killed the build process
- Zulip recovered immediately (HTTP 200)

**Prevention for future:**
```bash
# Option 1: Limit build resources
DOCKER_BUILDKIT_CPU_QUOTA=50000 docker compose build zulip

# Option 2: Run overnight when system is idle

# Option 3: Build on a different machine
```

---

## Updated Key Files & Locations

| Item | Location |
|------|----------|
| Merview Integration Code | `~/Developer/ClaudeCodeProjects/Zulip/custom_zulip_files/` |
| Fork Issues | https://github.com/mickdarling/zulip/issues |

---

## Next Steps

### Immediate (Overnight Build)
1. Restart Docker build with resource limits
2. Build completes overnight without impacting services

### After Build Completes
1. Run `docker compose up -d zulip` to deploy
2. Test by uploading a `.md` file to Zulip
3. Verify "Merview" link appears and works

### Future
1. Submit upstream PR to zulip/zulip if integration works well
2. Propose extensibility system (Issue #1) to Zulip maintainers

---

## Useful Commands

### Resource-Limited Docker Build
```bash
cd ~/Developer/ClaudeCodeProjects/Zulip

# Build with CPU limit (runs slower but doesn't starve other containers)
docker compose build --progress=plain zulip 2>&1 | tee build.log

# After build completes
docker compose up -d zulip
```

### Check Build Progress
```bash
# If running in background
tail -f build.log
```

---

## Notes

- Docker builds that compile source code (TypeScript, Webpack) are resource-intensive
- Always consider resource limits when building on a production server
- The `custom_zulip_files/` mechanism overlays files during Docker build
- Build must complete fully before the new image can be used
- Running containers are NOT affected by build... unless resource exhaustion occurs
