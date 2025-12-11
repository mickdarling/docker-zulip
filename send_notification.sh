#!/bin/bash

MESSAGE='## Zulip Build & Deployment - SUCCESS ✅

**Date/Time:** 2025-12-10 15:20:00 UTC

### Build Status
- ✅ Docker build completed successfully
- ✅ Fixed Dockerfile issue (removed duplicate custom file copy)
- ✅ Fixed custom rendered_markdown.ts (removed incorrect audio template import)
- ✅ Webpack compilation succeeded without errors

### Deployment Status
- ✅ Container deployed and running (zulip-zulip-1)
- ✅ All services healthy and operational

### Verification Results
- ✅ **Merview code found in webpack bundles**
- ✅ **Version tag `merview-v2` confirmed in bundles**
- ✅ Build date: 2025-12-10

### Fix Applied
The Dockerfile had a duplicate COPY command in Stage 2 that was overwriting the custom files from Stage 1. This has been removed. Additionally, the custom `rendered_markdown.ts` file had an incorrect import for `markdown_audio.hbs` template that doesnt exist in Zulip 11.4. This import and related audio rendering code have been removed while preserving the Merview integration functionality.

The Merview integration is now properly compiled into the production webpack bundles and will appear in the browser console as: **`[Zulip Custom Build] merview-v2 | 2025-12-10 | Build includes Merview integration`**

🎉 All systems operational!'

curl -X POST https://chat.dollhousemcp.com/api/v1/messages \
  -u "formatter-bot@chat.dollhousemcp.com:Fz1wWRga1Z9WCREUp8317qKnMAI1VE1l" \
  -d "type=stream" \
  -d "to=general" \
  -d "topic=Merview Integration" \
  -d "content=$MESSAGE"
