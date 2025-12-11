# Session Notes - December 11, 2025

## Overview
Continuation of Zulip infrastructure work. Major focus on Merview integration fix and news bot updates from previous session.

---

## Completed Work

### 1. Merview URL Format Fix (DEPLOYED)
**Problem:** Merview links were using wrong URL format (`/view?url=` with URL encoding)
**Solution:** Changed to correct format (`/?url=` with plain URLs)

**Files Changed:**
- `/Users/mick/Developer/ClaudeCodeProjects/Zulip/custom_zulip_files/web/src/rendered_markdown.ts`

**Changes:**
- Line ~44: Added configurable constant `MERVIEW_BASE_URL = "https://merview.com/"`
- Line ~385: Changed URL construction to use the constant
- Version bumped to `merview-v2.2`

**Commit:** `20527ab` on branch `fix/merview-url-format` (merged to main)
**Status:** Built and deployed

---

### 2. Merview Temporary URL Integration (READY TO BUILD)
**Problem:** Merview can't access `/user_uploads/` files because they require Zulip authentication
**Solution:** Use Zulip's built-in temporary URL API

**How it works:**
1. User clicks "Merview" link on a `.md` attachment
2. JavaScript calls `/json/user_uploads/{path}` API
3. API returns temporary URL valid for 60 seconds (no auth required)
4. Opens Merview with the temporary URL

**Files Changed:**
- `/Users/mick/Developer/ClaudeCodeProjects/Zulip/custom_zulip_files/web/src/rendered_markdown.ts`

**Key code change (lines ~375-420):**
```typescript
$merviewLink.on("click", async function(e) {
    e.preventDefault();
    const pathMatch = href.match(/\/user_uploads\/(.+)/);
    if (!pathMatch) return;
    const filePath = pathMatch[1];

    const response = await fetch(`/json/user_uploads/${filePath}`);
    const data = await response.json();

    if (data.result === "success" && data.url) {
        const fullTempUrl = new URL(data.url, window.location.origin).href;
        const merviewUrl = `${MERVIEW_BASE_URL}?url=${encodeURIComponent(fullTempUrl)}`;
        window.open(merviewUrl, '_blank', 'noopener,noreferrer');
    }
});
```

**Commit:** `9b8a4ea`
**Version:** `merview-v2.3`
**Status:** NEEDS REBUILD - run `docker compose build zulip && docker compose up -d zulip`

---

## News Bots Status (from Dec 10 session)

### Dollhouse MCP Zulip (chat.dollhousemcp.com)

| Bot | Stream | Status |
|-----|--------|--------|
| MCP News Bot | `#mcp-news` | Running - monitors Glama.ai, Google News, HN, Reddit |
| AI News Bot | `#ai-news` | Running - HuggingFace, OpenAI, DeepMind RSS + Google News |
| Claude Skills Bot | `#claude-skills-watch` | Running - tracks Anthropic Agent Skills (legal monitoring) |

### Merview Zulip (chat.merview.com)

| Bot | Stream | Status |
|-----|--------|--------|
| News Bot | `#news` | Configured - monitors for Merview mentions |
| GitHub Bot | `#github` | Configured - needs repo names |
| Digest Bot | `#digest` | Configured - weekly LinkedIn-ready summaries |

**Merview Bot API Keys (in .env):**
- `MERVIEW_NEWS_BOT_API_KEY`
- `MERVIEW_GITHUB_BOT_API_KEY`
- `MERVIEW_DIGEST_BOT_API_KEY`

---

## Key File Locations

### Custom Zulip Build
- Source: `/Users/mick/Developer/ClaudeCodeProjects/Zulip/custom_zulip_files/web/src/rendered_markdown.ts`
- Merview constant at top of file: `MERVIEW_BASE_URL`
- Version tag in console.log around line 40

### Bot Configurations
- MCP News: `/Users/mick/Developer/ClaudeCodeProjects/Zulip/bots/mcp-news-bot/`
- AI News: `/Users/mick/Developer/ClaudeCodeProjects/Zulip/bots/ai-news-bot/`
- Claude Skills: `/Users/mick/Developer/ClaudeCodeProjects/Zulip/bots/claude-skills-bot/`
- Merview News: `/Users/mick/Developer/ClaudeCodeProjects/Zulip/bots/merview-news-bot/`
- Merview GitHub: `/Users/mick/Developer/ClaudeCodeProjects/Zulip/bots/merview-github-bot/`
- Merview Digest: `/Users/mick/Developer/ClaudeCodeProjects/Zulip/bots/merview-digest-bot/`

### Environment
- Main .env: `/Users/mick/Developer/ClaudeCodeProjects/Zulip/.env`
- Docker memory: 18GB (bumped this session for faster builds)
- Build time: ~12 minutes with 18GB

---

## Next Steps

### Immediate
1. **REBUILD ZULIP** to deploy v2.3 with temporary URL support:
   ```bash
   cd /Users/mick/Developer/ClaudeCodeProjects/Zulip
   docker compose build zulip
   docker compose up -d zulip
   ```

2. **TEST** the Merview integration:
   - Upload a .md file to a Zulip stream
   - Click the "Merview" link
   - Verify it opens in Merview with rendered content

### Future Considerations
- Merview GitHub bots need actual repository names configured
- Consider extending temporary URL validity if 60 seconds is too short
- Claude Skills bot filtering may need tuning based on results

---

## Technical Notes

### Zulip Temporary URL API
- Endpoint: `/json/user_uploads/{realm_id}/{path}/{filename}`
- Returns: `{"result": "success", "url": "/user_uploads/temporary/{token}/{filename}"}`
- Token validity: 60 seconds (configurable in Zulip settings)
- No authentication required for temporary URLs

### Merview URL Format
- Correct: `https://merview.com/?url=https://example.com/file.md`
- The URL parameter should be URL-encoded when using temporary URLs (contain special chars)
- Plain URLs with normal slashes work fine for public URLs

### Docker Build Notes
- Builds are cached - only changed layers rebuild
- Full rebuild: ~30-45 min
- Cached rebuild with custom file changes: ~12 min
- Memory requirement: 16GB+ recommended, 18GB optimal
