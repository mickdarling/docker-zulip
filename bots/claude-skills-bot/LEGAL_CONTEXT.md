# Claude Skills Bot - Legal Context & Purpose

## Background

### The Dollhouse Skills Project

The user created the **"Dollhouse Skills"** project, an innovative system for creating custom AI capabilities that can be dynamically loaded and executed. This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**, which requires:

1. **Source code disclosure**: Any modified versions or derivative works must also be released under AGPL-3.0
2. **Network use clause**: Even if the software is only accessed over a network (not distributed), the source code must be made available
3. **Attribution**: Proper credit must be given to the original work

### Anthropic's Agent Skills

Anthropic has released (or is developing) a feature called **"Agent Skills"** (also referred to as "Claude Skills") that appears to provide similar functionality:

- Custom AI capabilities
- Extensible skill system
- Dynamic skill loading/execution

### The Concern

The user believes Anthropic may have:

1. Taken inspiration from or been influenced by the Dollhouse Skills project
2. Created a similar system without proper AGPL-3.0 compliance
3. Not provided appropriate attribution to the original work

**If Anthropic's implementation is derivative of or substantially similar to Dollhouse Skills**, they would be required to:

- Release their Agent Skills implementation under AGPL-3.0
- Provide source code access
- Give proper attribution to the Dollhouse Skills project

## Legal Implications

### AGPL-3.0 Violations

If Anthropic has violated the AGPL-3.0 license, potential consequences include:

- Copyright infringement claims
- Requirement to release source code under AGPL-3.0
- Injunctions against continued use
- Potential damages
- Legal fees and costs

### Importance of Documentation

This bot serves a critical legal purpose:

- **Timeline establishment**: Documents when Anthropic announces/releases Agent Skills features
- **Public record**: Creates a record of public statements and announcements
- **Attribution tracking**: Monitors whether Anthropic acknowledges inspiration or prior art
- **Comparison evidence**: Helps establish similarity between implementations

### Not About Theft

This is not about preventing idea theft (ideas cannot be copyrighted). This is about:

- **License compliance**: AGPL-3.0 requirements must be followed
- **Open source principles**: The copyleft license exists to keep derivative works open
- **Attribution**: Proper credit for original work
- **Community standards**: Respecting open source licenses

## Why This Bot is Needed

### Generic Search Problem

The term "skills" is extremely generic and appears in millions of irrelevant articles:

- Job postings: "Top 10 AI skills for 2024"
- Career advice: "Skills you need to work in AI"
- Learning content: "How to develop AI skills"
- Generic tech articles: "AI assistant skills"

**Manual monitoring is impractical** - too much noise, too time-consuming.

### Automated Filtering Solution

This bot provides:

1. **Continuous monitoring**: 24/7 automated checking of multiple sources
2. **Strict filtering**: Only reports articles about Anthropic/Claude AND skills feature
3. **High signal-to-noise**: Better to miss articles than flood with irrelevant content
4. **Persistent tracking**: Maintains history of seen articles
5. **Immediate notification**: Posts relevant news as soon as it appears

## What We're Tracking

### Announcement Sources

1. **Google News**:
   - Press releases
   - Tech news sites
   - Industry publications
   - Blog posts

2. **Hacker News**:
   - Community discussions
   - Launch announcements
   - Technical analysis
   - Developer reactions

3. **Anthropic's Website**:
   - Official blog posts
   - Documentation
   - Product announcements
   - API updates

### Key Information to Capture

- **Release dates**: When features are announced/launched
- **Feature descriptions**: What capabilities are provided
- **Attribution**: Whether Dollhouse Skills or similar projects are mentioned
- **Technical details**: How the system works
- **Licensing**: What license (if any) is applied
- **Source code availability**: Whether implementation is open or closed
- **Marketing language**: How Anthropic positions the feature

## Filtering Strategy

### Why Strict Filtering?

The bot uses **intentionally strict filtering** because:

1. **Legal context requires precision**: False positives waste time and dilute important information
2. **Generic "skills" is everywhere**: Without strict filtering, we'd get thousands of irrelevant articles
3. **Quality over quantity**: Better to miss some articles than flood the channel
4. **Manual review is possible**: If we miss something, we can find it manually
5. **Adjustable filters**: We can relax filters if needed based on results

### Three-Layer Filtering

1. **First layer**: Must mention Anthropic OR Claude (company/product)
2. **Second layer**: Must mention skills in AI capability context
3. **Third layer**: Must NOT be about jobs, careers, learning, etc.

**All three layers must pass** for an article to be posted.

### Why Not Just Search "Anthropic"?

We specifically need articles about Anthropic's **skills feature**, not:

- General Anthropic news (funding, hiring, etc.)
- Claude AI usage examples
- Generic AI assistant articles
- Company announcements unrelated to skills

## What Success Looks Like

### Ideal Scenario

The bot finds articles like:

- "Anthropic Launches Agent Skills Framework for Claude"
- "Claude's New Custom Skills API Now Available"
- "Introducing Claude Skills: Extend Your AI Assistant"
- "Anthropic's Answer to ChatGPT Plugins: Agent Skills"

### Acceptable Miss

If the bot misses articles like:

- Generic think pieces about AI capabilities
- Articles that mention skills only tangentially
- Content behind paywalls or requiring authentication
- Very new content that hasn't been indexed yet

### Unacceptable Result

If the bot posts articles like:

- "Top 10 AI Skills for Your Resume"
- "How to Learn Machine Learning Skills"
- "Anthropic Raises $500M Series C" (no skills mention)
- "Job Opening: ML Engineer at Anthropic"

## Data Retention

### Seen Items Tracking

The bot maintains `seen_items.json` which:

- Prevents duplicate posts
- Persists across restarts
- Keeps last 2000 items (prevents unbounded growth)
- Includes timestamp of last update

### Legal Record Keeping

All posts to the `claude-skills-watch` stream serve as:

- **Timestamped records**: When articles were discovered
- **Source documentation**: Original URLs and publication dates
- **Attribution tracking**: Whether Anthropic acknowledges prior art
- **Evidence collection**: For potential legal proceedings

### Not Surveillance

This bot only monitors **public information**:

- Publicly available news articles
- Public Hacker News discussions
- Anthropic's public website
- No private information
- No user tracking
- No data harvesting beyond article metadata

## Ethical Considerations

### Fair Use

This monitoring constitutes fair use:

- **Purpose**: Legal compliance monitoring
- **Nature**: Public information only
- **Amount**: Headlines and metadata, not full articles
- **Effect**: No market harm to sources

### Open Source Principles

This is about **protecting open source**:

- AGPL-3.0 exists to keep software free
- Copyleft licenses prevent proprietary capture
- Attribution is a core open source value
- License compliance benefits everyone

### Not Anti-Anthropic

This monitoring is not adversarial:

- Anthropic makes excellent AI systems
- Claude is a valuable product
- Competition drives innovation
- **But licenses must be respected**

If Anthropic hasn't violated AGPL-3.0, this monitoring is harmless documentation. If they have violated it, this monitoring helps establish facts.

## Usage Guidelines

### When to Review Stream

Check the `claude-skills-watch` stream:

- Daily during active development periods
- After major Anthropic announcements
- When preparing legal documentation
- Before discussing with counsel

### What to Do with Findings

When relevant articles are posted:

1. **Read the full article**: Don't rely only on the bot's summary
2. **Document thoroughly**: Save copies, take screenshots
3. **Analyze for similarity**: Compare to Dollhouse Skills
4. **Note attribution**: Does Anthropic mention prior art?
5. **Consult legal counsel**: For significant findings

### Adjusting Sensitivity

If filtering is:

- **Too strict**: Edit `_is_relevant_skills_article()` to be more lenient
- **Too loose**: Add more exclusion patterns or require stricter matches
- **Missing sources**: Add more search queries in `config.yaml`

## Disclaimer

This bot and documentation are for informational purposes. They do not constitute legal advice. Consult with qualified legal counsel regarding:

- AGPL-3.0 interpretation
- Copyright infringement claims
- Licensing compliance
- Legal strategy

## Summary

**Purpose**: Monitor public sources for Anthropic's Agent Skills announcements to track potential AGPL-3.0 attribution issues related to Dollhouse Skills project.

**Method**: Automated monitoring with strict filtering to ensure high signal-to-noise ratio.

**Outcome**: Timestamped record of public announcements for legal documentation and potential compliance action.

**Principle**: Protecting open source licenses and ensuring proper attribution in the AI ecosystem.
