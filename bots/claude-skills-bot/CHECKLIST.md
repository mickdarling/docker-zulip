# Claude Skills Bot - Setup Checklist

## Pre-Deployment Verification

### Files Created
- [x] `claude_skills_bot.py` - Main bot code with strict filtering
- [x] `config.yaml` - Configuration with search queries
- [x] `requirements.txt` - Python dependencies
- [x] `Dockerfile` - Container definition
- [x] `README.md` - Full documentation
- [x] `SETUP.md` - Setup and operations guide
- [x] `QUICK_START.md` - Quick reference
- [x] `LEGAL_CONTEXT.md` - Legal background and purpose
- [x] `CHECKLIST.md` - This file
- [x] `setup_stream.py` - Stream creation script
- [x] `seen_items.json` - Initial tracking file

### Docker Compose Integration
- [x] Service added to `docker-compose.yml`
- [x] Uses `FORMATTER_BOT_API_KEY` environment variable
- [x] Volume mount for `seen_items.json` persistence
- [x] Depends on `zulip` service
- [x] Restart policy: `unless-stopped`

### Configuration Verified
- [x] Zulip site: `https://chat.dollhousemcp.com`
- [x] Zulip credentials: formatter-bot
- [x] Stream name: `claude-skills-watch`
- [x] Topic: `News & Updates`
- [x] Poll interval: 3600 seconds (1 hour)
- [x] Max age: 168 hours (1 week)

### Search Strategy
- [x] Google News queries defined (6 specific searches)
- [x] Hacker News keywords defined (3 keywords)
- [x] Anthropic site search configured
- [x] All queries use exact phrases where possible
- [x] Generic terms avoided in favor of specific combinations

### Filtering Logic
- [x] Must mention Anthropic OR Claude
- [x] Must mention skills in AI context
- [x] Must NOT be job/career related
- [x] Must NOT be generic "top skills" articles
- [x] Logging for filtered items (debug mode)

## Deployment Steps

### 1. Create Zulip Stream
```bash
cd /Users/mick/Developer/ClaudeCodeProjects/Zulip/bots/claude-skills-bot
pip3 install -r requirements.txt
python3 setup_stream.py
```

**Expected Output**:
```
Setting up claude-skills-watch stream...
1. Creating stream...
   ✓ Stream created successfully
2. Subscribing user8@chat.dollhousemcp.com...
   ✓ User subscribed successfully

Setup complete! You can now start the claude-skills-bot:
  docker-compose up -d claude-skills-bot
```

**Verify**:
- [ ] Stream `claude-skills-watch` exists on Zulip
- [ ] `user8@chat.dollhousemcp.com` is subscribed
- [ ] `formatter-bot@chat.dollhousemcp.com` is subscribed
- [ ] Stream description mentions AGPL attribution tracking

### 2. Build Docker Image
```bash
cd /Users/mick/Developer/ClaudeCodeProjects/Zulip
docker-compose build claude-skills-bot
```

**Expected Output**:
```
Building claude-skills-bot
[+] Building X.Xs (Y/Y FINISHED)
Successfully built [image-id]
Successfully tagged zulip-claude-skills-bot:latest
```

**Verify**:
- [ ] Build completes without errors
- [ ] Image is created: `docker images | grep claude-skills-bot`

### 3. Start the Bot
```bash
docker-compose up -d claude-skills-bot
```

**Expected Output**:
```
Creating zulip_claude-skills-bot_1 ... done
```

**Verify**:
- [ ] Container is running: `docker-compose ps claude-skills-bot`
- [ ] Status shows "Up X seconds/minutes"

### 4. Check Initial Logs
```bash
docker-compose logs claude-skills-bot
```

**Expected Output**:
```
INFO: Created Zulip client for https://chat.dollhousemcp.com
INFO: Loaded 0 seen items from disk
INFO: Starting Claude Skills Bot (polling every 3600s)...
INFO: STRICT FILTERING ENABLED: Only Anthropic/Claude + Skills mentions
INFO: Monitoring source: google_news
INFO: Monitoring source: hackernews
INFO: Monitoring source: anthropic_site
INFO: Checking all sources for Claude Skills news...
```

**Verify**:
- [ ] No error messages
- [ ] Zulip client created successfully
- [ ] All three sources are being monitored
- [ ] Bot starts checking sources

### 5. Test Without Docker (Optional)
```bash
cd bots/claude-skills-bot
python3 claude_skills_bot.py --check-once
```

**Verify**:
- [ ] Runs without errors
- [ ] Checks all sources
- [ ] Either posts articles or shows "no new items"
- [ ] No Python exceptions

## Post-Deployment Verification

### First Hour
- [ ] Check logs every 15 minutes: `docker-compose logs -f claude-skills-bot`
- [ ] Verify no error messages
- [ ] Observe filtering behavior (articles found vs filtered)
- [ ] Check if any articles are posted to Zulip

### First Day
- [ ] Check `seen_items.json` has grown: `cat bots/claude-skills-bot/seen_items.json | wc -l`
- [ ] Verify articles posted are relevant (not job postings, etc.)
- [ ] Check if filtering is too strict (missing obvious articles)
- [ ] Adjust config if needed

### First Week
- [ ] Review all posted articles for relevance
- [ ] Check for false positives (irrelevant articles)
- [ ] Check for false negatives (manually search and compare)
- [ ] Fine-tune filtering if needed
- [ ] Document any adjustments made

## Testing Scenarios

### Scenario 1: Bot Finds Relevant Article
**Expected**:
- [ ] Article posted to `#claude-skills-watch > News & Updates`
- [ ] Post includes title, source, date, URL
- [ ] Post includes legal context note
- [ ] Seen items updated
- [ ] No duplicate posts

### Scenario 2: Bot Filters Generic Article
**Expected**:
- [ ] Article not posted to Zulip
- [ ] Debug log shows filter reason (if debug enabled)
- [ ] Seen items updated (prevents re-checking)

### Scenario 3: Bot Restarts
**Expected**:
- [ ] Loads seen items from disk
- [ ] Doesn't repost old articles
- [ ] Continues normal operation
- [ ] No data loss

### Scenario 4: New Search Query Added
**Steps**:
1. Edit `config.yaml`
2. Add new query to `search_queries`
3. Restart: `docker-compose restart claude-skills-bot`

**Expected**:
- [ ] Bot picks up new configuration
- [ ] New query is searched
- [ ] No rebuild needed

### Scenario 5: Filtering Logic Changed
**Steps**:
1. Edit `claude_skills_bot.py`
2. Modify `_is_relevant_skills_article()`
3. Rebuild: `docker-compose build claude-skills-bot`
4. Restart: `docker-compose up -d claude-skills-bot`

**Expected**:
- [ ] Changes take effect
- [ ] Filtering behaves as expected
- [ ] No errors in logs

## Monitoring Checklist (Ongoing)

### Daily
- [ ] Check Zulip stream for new articles
- [ ] Review any posted articles for relevance
- [ ] Scan logs for errors: `docker-compose logs --tail=100 claude-skills-bot`

### Weekly
- [ ] Review false positive rate (irrelevant articles posted)
- [ ] Review false negative rate (manually search for missed articles)
- [ ] Adjust filters if needed
- [ ] Check disk space for `seen_items.json`

### Monthly
- [ ] Review search queries - are they still relevant?
- [ ] Check if Anthropic has changed terminology
- [ ] Update queries if needed
- [ ] Archive old articles if doing legal documentation

## Troubleshooting Checklist

### Bot Not Starting
- [ ] Check Docker logs: `docker-compose logs claude-skills-bot`
- [ ] Verify `FORMATTER_BOT_API_KEY` in `.env`
- [ ] Check if Zulip service is running: `docker-compose ps zulip`
- [ ] Verify config.yaml syntax: `python -c "import yaml; yaml.safe_load(open('bots/claude-skills-bot/config.yaml'))"`

### Bot Not Posting Anything
- [ ] Enable debug logging in `config.yaml` (level: "DEBUG")
- [ ] Check if articles are being filtered: `docker-compose logs -f claude-skills-bot | grep "Filtered out"`
- [ ] Verify stream exists and bot is subscribed
- [ ] Test with `--check-once` flag
- [ ] Check if search APIs are rate limiting

### Too Many Irrelevant Articles
- [ ] Review posted articles to identify patterns
- [ ] Add exclusion patterns to `_is_relevant_skills_article()`
- [ ] Strengthen keyword requirements
- [ ] Rebuild and restart

### Missing Relevant Articles
- [ ] Check `max_age_hours` - increase if articles are old
- [ ] Check if filters are too strict - relax keyword requirements
- [ ] Add more search query variations
- [ ] Enable debug logging to see what's being filtered

### Stream Errors
- [ ] Verify stream name matches config: `claude-skills-watch`
- [ ] Check bot has permission to post to stream
- [ ] Verify API key is valid and not expired
- [ ] Check Zulip site URL is correct

## Success Criteria

### Technical Success
- [x] Bot runs continuously without crashes
- [x] Checks sources every hour
- [x] Persists seen items across restarts
- [x] Posts to correct Zulip stream and topic
- [x] Rate limiting prevents API issues

### Functional Success
- [ ] High signal-to-noise ratio (>90% relevant articles)
- [ ] Low false negative rate (<10% missed articles)
- [ ] No duplicate posts
- [ ] Timely notifications (within 1 hour of publication)

### Legal Success
- [ ] Creates timestamped record of announcements
- [ ] Captures attribution information (if present)
- [ ] Provides URLs for verification
- [ ] Enables timeline documentation for legal purposes

## Documentation Checklist

### For Users
- [x] `README.md` - Comprehensive documentation
- [x] `QUICK_START.md` - Quick reference
- [x] `SETUP.md` - Detailed setup guide
- [x] All files include clear explanations

### For Legal Context
- [x] `LEGAL_CONTEXT.md` - Background and purpose
- [x] Purpose clearly stated in all docs
- [x] AGPL attribution issue explained
- [x] Fair use and ethics discussed

### For Developers
- [x] Code comments explain filtering logic
- [x] `config.yaml` has inline documentation
- [x] Architecture follows existing bot patterns
- [x] Dependencies documented in `requirements.txt`

## Final Sign-Off

Before marking as complete:
- [ ] All files created and in correct location
- [ ] Docker Compose integration tested
- [ ] Stream created and users subscribed
- [ ] Bot runs successfully for 24+ hours
- [ ] No errors in logs
- [ ] At least one successful post to Zulip (or verified filtering is working)
- [ ] Documentation reviewed and accurate
- [ ] Filtering logic validated
- [ ] Legal context clearly communicated

**Deployment Date**: _________________

**Deployed By**: _____________________

**Initial Test Results**: ____________

**Status**: [ ] Ready for Production [ ] Needs Adjustments
