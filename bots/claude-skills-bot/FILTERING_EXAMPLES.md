# Filtering Examples - What Gets Posted vs Filtered

## Understanding the Filtering Logic

The bot uses three-layer filtering to ensure only relevant articles are posted.

## Layer 1: Must Mention Anthropic/Claude

### PASSES Layer 1 ✓

- "Anthropic announces new AI features"
- "Claude 3 receives major update"
- "Interview with Anthropic CEO"
- "Claude Opus vs GPT-4 comparison"
- "Anthropic raises $500M funding round"

### FAILS Layer 1 ✗

- "OpenAI launches new agent framework" (no Anthropic/Claude)
- "Google DeepMind releases new model" (no Anthropic/Claude)
- "Top 10 AI assistants for 2024" (mentions many, but must specifically mention Anthropic/Claude)
- "How to build custom AI skills" (generic, no company mention)

## Layer 2: Must Mention Skills in AI Context

### PASSES Layer 2 ✓

- "Anthropic launches agent skills framework"
- "Claude gains custom skills support"
- "New Claude API enables skill extensions"
- "Anthropic's skill system for developers"
- "Claude skills marketplace announced"

### FAILS Layer 2 ✗

- "Anthropic raises funding" (no skills mention)
- "Claude 4 released" (no skills mention)
- "Interview with Anthropic CEO" (no skills mention)
- "Anthropic's approach to AI safety" (no skills mention)

## Layer 3: Must NOT Be Job/Career Related

### PASSES Layer 3 ✓

- "Anthropic launches agent skills API"
- "Claude's new custom skill framework"
- "How to build Claude skills for your app"
- "Anthropic's skill system enables X"

### FAILS Layer 3 ✗

- "Skills needed to work at Anthropic" (job skills)
- "How to get hired by Anthropic" (career advice)
- "Anthropic job posting: ML Engineer" (job posting)
- "AI skills for your resume in 2024" (learning/career)
- "Top skills Anthropic looks for in candidates" (hiring)

## Complete Examples

### Example 1: POSTED ✓✓✓

**Title**: "Anthropic Announces Agent Skills Framework for Claude"

**Analysis**:

- ✓ Layer 1: Mentions "Anthropic" and "Claude"
- ✓ Layer 2: Mentions "Agent Skills Framework" (AI capability)
- ✓ Layer 3: Not about jobs or careers

**Result**: **POSTED TO ZULIP**

---

### Example 2: FILTERED (No Skills) ✓✗✗

**Title**: "Anthropic Raises $500M in Series C Funding"

**Analysis**:

- ✓ Layer 1: Mentions "Anthropic"
- ✗ Layer 2: No mention of skills
- N/A Layer 3: (doesn't reach this layer)

**Result**: **FILTERED OUT** (Reason: no skills mention)

---

### Example 3: FILTERED (Job Related) ✓✓✗

**Title**: "Top Skills You Need to Land a Job at Anthropic"

**Analysis**:

- ✓ Layer 1: Mentions "Anthropic"
- ✓ Layer 2: Mentions "skills"
- ✗ Layer 3: About job skills/career

**Result**: **FILTERED OUT** (Reason: job/career related)

---

### Example 4: FILTERED (No Anthropic) ✗✗✗

**Title**: "Building Custom Agent Skills for AI Assistants"

**Analysis**:

- ✗ Layer 1: No mention of Anthropic or Claude
- N/A Layer 2: (doesn't reach this layer)
- N/A Layer 3: (doesn't reach this layer)

**Result**: **FILTERED OUT** (Reason: no Anthropic/Claude mention)

---

### Example 5: POSTED ✓✓✓

**Title**: "Claude Gains Custom Skills API in Latest Update"

**Analysis**:

- ✓ Layer 1: Mentions "Claude"
- ✓ Layer 2: Mentions "Custom Skills API" (AI capability)
- ✓ Layer 3: Not about jobs or careers

**Result**: **POSTED TO ZULIP**

---

### Example 6: FILTERED (Generic) ✓✗✗

**Title**: "10 Skills Claude AI Can Help You Learn"

**Analysis**:

- ✓ Layer 1: Mentions "Claude"
- ✗ Layer 2: "Skills to learn" (not about Claude's skills feature)
- ✗ Layer 3: About learning skills

**Result**: **FILTERED OUT** (Reason: generic skills article)

---

### Example 7: POSTED ✓✓✓

**Title**: "Anthropic's Skill System: Extending Claude with Custom Capabilities"

**Analysis**:

- ✓ Layer 1: Mentions "Anthropic" and "Claude"
- ✓ Layer 2: Mentions "Skill System" and "Custom Capabilities" (AI feature)
- ✓ Layer 3: Not about jobs or careers

**Result**: **POSTED TO ZULIP**

---

### Example 8: FILTERED (Wrong Context) ✓✗✗

**Title**: "How Anthropic Trained Claude: The Skills Behind the Model"

**Analysis**:

- ✓ Layer 1: Mentions "Anthropic" and "Claude"
- ✗ Layer 2: "Skills" refers to training methods, not a features
- N/A Layer 3: (might pass, but already filtered)

**Result**: **FILTERED OUT** (Reason: "skills" not in feature context)

---

### Example 9: POSTED ✓✓✓

**Title**: "site:anthropic.com - Introducing Claude Skills for Developers"

**Analysis**:

- ✓ Layer 1: Mentions "Claude"
- ✓ Layer 2: "Claude Skills" (AI capability feature)
- ✓ Layer 3: Developer feature, not job/career

**Result**: **POSTED TO ZULIP**

---

### Example 10: FILTERED (Generic "Skills") ✓✗✗

**Title**: "Essential Skills for Working with Claude AI"

**Analysis**:

- ✓ Layer 1: Mentions "Claude"
- ✗ Layer 2: User skills, not Claude's skills feature
- ✗ Layer 3: Learning/education content

**Result**: **FILTERED OUT** (Reason: about user skills, not AI feature)

## Keyword Detection Details

### Anthropic/Claude Keywords (Layer 1)

The article must contain at least one of:

- "anthropic"
- "claude ai"
- "claude 3"
- "claude 4"
- "claude opus"
- "claude sonnet"
- "claude haiku"

### Skills Keywords (Layer 2)

The article must contain at least one of:

- "agent skills"
- "claude skills"
- "custom skills"
- "ai skills" (in context with Anthropic/Claude)
- "skill system"
- "skills feature"
- "skills api"
- "skills framework"

### Job/Career Exclusions (Layer 3)

The article must NOT contain:

- "job opening"
- "job posting"
- "career"
- "hiring"
- "resume"
- "cv "
- "employment"
- "learn skills"
- "skill development"
- "professional skills"
- "soft skills"
- "hard skills"
- "technical skills interview"
- "job skills"

## Edge Cases

### Case 1: Ambiguous Context

**Title**: "Claude's skills at reasoning improve"

**Analysis**:

- ✓ Layer 1: Mentions "Claude"
- ⚠️ Layer 2: "skills at reasoning" - is this the feature or capability?
- This is a judgment call - current logic would likely filter it

**Why**: "Skills at X" usually means capability/ability, not the "skills feature"

**Adjustment**: If we see relevant articles being filtered this way, we can relax Layer 2 to catch these

---

### Case 2: Multiple Mentions

**Title**: "Anthropic's Claude vs ChatGPT: Agent Skills Comparison"

**Analysis**:

- ✓ Layer 1: Mentions "Anthropic" and "Claude"
- ✓ Layer 2: Mentions "Agent Skills"
- ✓ Layer 3: Not job/career

**Result**: **POSTED** - Even though ChatGPT is mentioned, Anthropic/Claude are also mentioned

---

### Case 3: Indirect Reference

**Title**: "How the Claude Team Built Their Skills Framework"

**Analysis**:

- ✓ Layer 1: Mentions "Claude"
- ✓ Layer 2: Mentions "Skills Framework"
- ✓ Layer 3: Not about jobs (it's about the technical implementation)

**Result**: **POSTED** - "Team" doesn't trigger job filters

---

### Case 4: Site Search Results

**Title**: "Anthropic Careers: Join Our Skills Team"

**Analysis**:

- ✓ Layer 1: Mentions "Anthropic"
- ⚠️ Layer 2: Mentions "Skills Team" (could be the skills feature team)
- ✗ Layer 3: "Careers" triggers job filter

**Result**: **FILTERED OUT** - Jobs are excluded even if genuinely about the skills team

**Trade-off**: We might miss articles about who's working on the skills feature, but that's acceptable to avoid job posting spam

## Adjusting Filters

### If Too Strict (Missing Articles)

Add more variations to Layer 2:

```python
has_skills_mention = any(term in combined for term in [
    "agent skills",
    "claude skills",
    "custom skills",
    "ai skills",
    "skill system",
    "skills feature",
    "skills api",
    "skills framework",
    # NEW additions:
    "skill extension",
    "skill plugin",
    "skill marketplace",
])
```

### If Too Loose (Too Many False Positives)

Add more exclusions to Layer 3:

```python
job_related = any(term in combined for term in [
    "job opening",
    "job posting",
    # ... existing ...
    # NEW additions:
    "recruiting",
    "talent acquisition",
    "interview process",
])
```

### Custom Search Queries

In `config.yaml`, make searches more specific:

```yaml
search_queries:
  - '"Anthropic" "agent skills" "framework"' # More specific
  - '"Claude" "skills" "API"' # More specific
```

## Testing Filtering

To test the filtering logic:

1. **Enable debug logging** in `config.yaml`:

   ```yaml
   logging:
     level: "DEBUG"
   ```

2. **Run a single check**:

   ```bash
   python3 claude_skills_bot.py --check-once
   ```

3. **Review logs** for filtering decisions:

   ```
   DEBUG: Filtered out - no Anthropic/Claude mention: Title Here
   DEBUG: Filtered out - no relevant skills mention: Title Here
   DEBUG: Filtered out - job/career related: Title Here
   INFO: MATCH FOUND: Relevant Article Title
   ```

4. **Adjust filters** based on results in `claude_skills_bot.py`

5. **Retest** until balance is achieved

## Success Metrics

### Good Filtering Performance

- **Precision** (posted articles are relevant): >90%
- **Recall** (relevant articles are found): >80%
- **False Positive Rate**: <10%
- **False Negative Rate**: <20%

### Signs of Good Filtering

- Few or no job postings make it through
- Generic "AI skills" articles are filtered out
- Actual Anthropic/Claude skills feature news is posted
- Manual review confirms relevance

### Signs of Over-Filtering

- Known relevant articles don't appear
- Debug logs show many matches being filtered
- Manually searching finds more than bot finds
- Need to relax Layer 2 or Layer 3

### Signs of Under-Filtering

- Job postings appearing in stream
- Generic skill articles appearing
- "How to learn AI" articles appearing
- Need to strengthen Layer 3 exclusions

## Conclusion

The filtering strategy is designed to be **conservative** - better to miss some articles than flood the stream with noise. The filters can be adjusted based on real-world performance, but the three-layer approach ensures high signal-to-noise ratio for this critical legal monitoring task.
