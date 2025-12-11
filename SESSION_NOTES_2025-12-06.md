# Session Notes - December 6, 2025

## Overview
Productive session focused on setting up self-hosted collaboration tools for DollhouseMCP. Successfully deployed both Huly (project management) and Zulip (team chat) with Cloudflare Tunnel access.

---

## What Was Accomplished

### 1. Huly Setup (https://huly.dollhousemcp.com)
- Discovered existing Huly Docker deployment at `/Users/mick/Developer/ClaudeCodeProjects/Huly/huly-selfhost/`
- Configured Cloudflare Tunnel for external HTTPS access
- Set up email via Resend (noreply@dollhousemcp.com)
- Fixed ACCOUNTS_URL and FRONT_URL configuration for proper external access
- Reset admin password via MongoDB

**Security Assessment Completed:**
- Found 3 unpatched CVEs (XSS via SVG, SSRF via HTML uploads)
- Recommendation: Keep running but don't connect GitHub/Gmail until hardened
- Safe for internal use with trusted users only

### 2. Zulip Setup (https://chat.dollhousemcp.com)
- Installed via Docker at `/Users/mick/Developer/ClaudeCodeProjects/Zulip/`
- Configured for `chat.dollhousemcp.com`
- Set up email via Resend
- Fixed Cloudflare reverse proxy configuration (LOADBALANCER_IPS)
- Created organization "Dollhouse MCP"

**Configured via API:**
- Uploaded DollhouseMCP logo
- Created streams: #general, #development, #mcp-server, #collection, #github, #random
- Invited Todd (tdibble@gmail.com) - now joined
- Set up GitHub webhook integration

### 3. Cloudflare Tunnel (System Service)
- Single tunnel handles both services
- Runs as macOS system service (survives reboots)
- Config: `/etc/cloudflared/config.yml`
- Routes:
  - huly.dollhousemcp.com → localhost:80
  - chat.dollhousemcp.com → localhost:9080

### 4. Resend Email Configuration
- Domain verified: dollhousemcp.com
- API Key: re_EJRXKkNm_FbRtGjmmGHAtg4ZvC1SwgooH
- Used by both Huly and Zulip for transactional email

---

## Key Files & Locations

| Item | Location |
|------|----------|
| Huly Docker Compose | `/Users/mick/Developer/ClaudeCodeProjects/Huly/huly-selfhost/compose.yml` |
| Zulip Docker Compose | `/Users/mick/Developer/ClaudeCodeProjects/Zulip/docker-compose.yml` |
| Cloudflare Tunnel Config | `/etc/cloudflared/config.yml` |
| Tunnel Service Plist | `/Library/LaunchDaemons/com.cloudflare.cloudflared.plist` |
| Tunnel Logs | `/Library/Logs/com.cloudflare.cloudflared.err.log` |

---

## Credentials & API Keys

### Zulip
- **Admin Email:** mick@dollhousemcp.com
- **API Key:** bAWz1KRzmkHv7hJhS4HtToHDHiO3KROp
- **GitHub Bot API Key:** MlC5a9qq5rAdn1XqJ8jEooCnC3whiyZr

### Huly
- **Admin Email:** mick@mickdarling.com
- **Password:** HulyTemp123! (should be changed)

### GitHub Webhook URL
```
https://chat.dollhousemcp.com/api/v1/external/github?api_key=MlC5a9qq5rAdn1XqJ8jEooCnC3whiyZr&stream=github
```

---

## Useful Commands

### Restart Huly
```bash
cd /Users/mick/Developer/ClaudeCodeProjects/Huly/huly-selfhost
docker compose down && docker compose up -d
```

### Restart Zulip
```bash
cd /Users/mick/Developer/ClaudeCodeProjects/Zulip
docker compose down && docker compose up -d
```

### Restart Cloudflare Tunnel
```bash
sudo launchctl bootout system/com.cloudflare.cloudflared
sudo launchctl bootstrap system /Library/LaunchDaemons/com.cloudflare.cloudflared.plist
```

### Check Tunnel Logs
```bash
cat /Library/Logs/com.cloudflare.cloudflared.err.log | tail -30
```

### View Running Containers
```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```

---

## Mobile Apps

- **iOS/iPad:** Zulip app available on App Store - working
- **Android:** Zulip app available on Google Play Store (for Todd)
- **Server URL to enter:** https://chat.dollhousemcp.com

---

## Next Session Topics

1. **Explore Zulip Integrations** - what else can be connected
2. **Zulip API/MCP Server** - building automation capabilities
3. **Huly Security Hardening** - disable dangerous file uploads, potentially connect GitHub safely
4. **Consider building Zulip MCP server** for Claude Code integration

---

## Research Completed

### Transactional Email Services
- Evaluated: Resend, Brevo, Amazon SES, SendGrid, Mailgun, Postmark
- Chose Resend: 3,000 emails/month free, no surprise billing, easy setup

### Self-Hosted Slack Alternatives
- Evaluated: Mattermost, Rocket.Chat, Zulip, Element/Matrix
- Chose Zulip: Best security track record, 100% open source (Apache 2.0), excellent API, best data export

### Huly Security Audit
- Company: Hardcore Engineering (Monaco), founder from Russia
- 3 CVEs found (unpatched): CVE-2024-27706, CVE-2024-27707, CVE-2024-48450
- No SECURITY.md or formal vulnerability disclosure process
- Recommendation: Use with caution, don't connect sensitive integrations yet

---

## Architecture Diagram

```
Internet
    │
    ▼
Cloudflare (HTTPS)
    │
    ▼
Cloudflare Tunnel (cloudflared service)
    │
    ├─── huly.dollhousemcp.com ──► localhost:80 ──► Huly (13 containers)
    │
    └─── chat.dollhousemcp.com ──► localhost:9080 ──► Zulip (5 containers)
```

---

## Notes

- Zulip Docker image is amd64, running via emulation on ARM Mac (slightly slower but works)
- Both services configured to restart automatically (`restart: unless-stopped`)
- Tunnel service starts on boot via launchd
- Todd successfully joined Zulip and is active
