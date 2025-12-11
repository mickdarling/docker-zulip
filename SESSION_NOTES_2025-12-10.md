# Session Notes - December 10, 2025

## Overview
Continued work on Merview integration for Zulip. Fixed critical Dockerfile issue where custom files were being copied AFTER webpack compilation. Rebuilt and deployed, but integration still not visually working despite code being confirmed in bundles.

---

## What Was Accomplished

### 1. Diagnosed Why First Build Didn't Work
- **Problem:** The `custom_zulip_files/` mechanism copied files AFTER the webpack build
- **Root cause:** Dockerfile structure:
  1. Stage 1 builds tarball with pre-compiled webpack bundles
  2. Stage 2 extracts tarball, THEN copies custom files
  3. Custom files overwrite source but compiled bundles already exist
- **Result:** Source files had our code, but compiled JS/CSS bundles didn't

### 2. Fixed Dockerfile
Modified `/Users/mick/Developer/ClaudeCodeProjects/Zulip/Dockerfile` to inject custom files BEFORE webpack build:

```dockerfile
# BEFORE (broken):
# Stage 1: clone -> provision -> build tarball
# Stage 2: extract tarball -> copy custom files (TOO LATE!)

# AFTER (fixed):
# Stage 1: clone -> COPY custom files -> provision -> build tarball
```

Key change at line 37-42:
```dockerfile
# Copy custom files BEFORE building (so they get compiled into webpack bundles)
COPY --chown=zulip:zulip custom_zulip_files/ /tmp/custom_zulip/
RUN if [ -d /tmp/custom_zulip ] && [ "$(ls -A /tmp/custom_zulip 2>/dev/null)" ]; then \
        cp -rf /tmp/custom_zulip/* /home/zulip/zulip/ && \
        echo "Custom files applied before build"; \
    fi && rm -rf /tmp/custom_zulip
```

### 3. Rebuilt with --no-cache
- Build took ~1 hour
- Confirmed "Custom files applied before build" in build log
- Build completed successfully

### 4. Verified Code is in Compiled Bundles
```bash
# Both returned "Found!"
docker exec zulip-zulip-1 sh -c 'grep -l "merview.com" /home/zulip/prod-static/webpack-bundles/*.js'
docker exec zulip-zulip-1 sh -c 'grep -l "merview" /home/zulip/prod-static/webpack-bundles/*.css'
```

### 5. Deployed and Sent Notification
- Used `docker compose up -d --force-recreate zulip`
- Zulip came back up (HTTP 200)
- Sent notification to #general > Merview Integration

---

## Current State: NOT WORKING (But Code IS There)

**The mystery:**
- Merview code IS in the compiled webpack bundles
- Merview CSS IS in the compiled CSS bundles
- But the "Merview" link is NOT appearing next to .md file uploads

**Possible issues to investigate:**
1. **Browser cache** - User may need hard refresh (Cmd+Shift+R)
2. **Code logic issue** - The selector `a[href*='/user_uploads/']` may not match
3. **File extension check** - The `.md` regex may not be matching
4. **Timing issue** - Code may run before attachments are rendered
5. **Console errors** - Need to check browser dev tools for JS errors

---

## Files Modified This Session

| File | Change |
|------|--------|
| `Dockerfile` | Added custom file injection BEFORE webpack build |

---

## Docker Memory Increased
- User increased Docker Desktop memory from 7.5GB to 14GB
- This prevents OOM kills during builds
- CPU remains at 10 (max for this machine)

---

## Next Session Tasks

### High Priority - Debug Merview Integration
1. **Add version identifier to UI** - So we can visually confirm which build is running
   - Could add to footer, settings page, or console.log on load
   - Example: `console.log("Zulip Custom Build: merview-v1 - 2025-12-10")`

2. **Test with browser cache cleared** - Hard refresh or incognito mode

3. **Check browser console** - Look for JS errors when viewing a message with .md attachment

4. **Test the selector** - In browser console:
   ```javascript
   document.querySelectorAll("a[href*='/user_uploads/']")
   ```

5. **Verify attachment URL format** - Upload a .md file and inspect the HTML to see exact href format

6. **Check if `rendered_markdown.ts` code runs** - Add a console.log to verify

### Code Changes to Consider
```typescript
// Add at start of Merview block in rendered_markdown.ts:
console.log("Merview integration: scanning for .md files...");

// Add after finding links:
console.log("Found attachment links:", $content.find("a[href*='/user_uploads/']").length);
```

---

## Key Files & Locations

| Item | Location |
|------|----------|
| Dockerfile (modified) | `~/Developer/ClaudeCodeProjects/Zulip/Dockerfile` |
| Custom TS | `~/Developer/ClaudeCodeProjects/Zulip/custom_zulip_files/web/src/rendered_markdown.ts` |
| Custom CSS | `~/Developer/ClaudeCodeProjects/Zulip/custom_zulip_files/web/styles/rendered_markdown.css` |
| Build log | `~/Developer/ClaudeCodeProjects/Zulip/build.log` |
| Session notes | `~/Developer/ClaudeCodeProjects/Zulip/SESSION_NOTES_2025-12-10.md` |

---

## Useful Commands

### Verify Merview Code in Running Container
```bash
# Check if code is in compiled bundles
docker exec zulip-zulip-1 sh -c 'grep -l "merview.com" /home/zulip/prod-static/webpack-bundles/*.js'
docker exec zulip-zulip-1 sh -c 'grep -l "merview" /home/zulip/prod-static/webpack-bundles/*.css'

# Check source file
docker exec zulip-zulip-1 grep "merview" /home/zulip/deployments/current/web/src/rendered_markdown.ts
```

### Rebuild (if needed)
```bash
cd ~/Developer/ClaudeCodeProjects/Zulip
docker compose build --no-cache zulip
docker compose up -d --force-recreate zulip
```

### Check Container Status
```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}" | grep zulip
```

---

## GitHub Issues (mickdarling/zulip fork)

| # | Title |
|---|-------|
| #1 | Extensible Message Action Icons |
| #2 | Open in Merview for .md attachments |

---

## Notes

- The Merview integration code pattern follows `rendered_markdown.ts` existing patterns (like audio processing, code playgrounds)
- Code searches for `a[href*='/user_uploads/']` links ending in `.md`
- Creates a styled link to `https://merview.com/view?url=<encoded-attachment-url>`
- CSS provides light blue pill styling with dark mode support
- Zulip notification system works - successfully sent message to #general stream
