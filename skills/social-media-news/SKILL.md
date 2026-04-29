---
name: social-media-news
description: |
  Searches the last 24 hours of top AI, technology, and engineering news from Hacker
  News and major tech RSS feeds (TechCrunch, Ars Technica, VentureBeat, The Verge,
  MIT Tech Review, Wired). Selects the single most popular or significant story and
  writes a ready-to-post 2-paragraph social media summary with source link. Requires
  no API keys. Supports optional category focus (--ai, --tech, --engineering) and
  configurable result count.
license: MIT
compatibility: "Linux/macOS (requires Python 3; no external packages needed)"
metadata:
  author: "Thomas Ott"
  version: "1.0"
---

# Social Media News Skill

## Invocation

```
/social-media-news
/social-media-news --ai
/social-media-news --tech
/social-media-news --engineering
/social-media-news --limit 10
```

Examples:
```
/social-media-news
/social-media-news --ai --limit 5
/social-media-news --engineering
```

## Instructions for the model

### Step 1 — Run the fetch script

```bash
python3 scripts/fetch_news.py [--ai | --tech | --engineering] [--limit N] [--hours N]
```

Default: top 5 stories across all categories from the last 24 hours.

The script fetches from:
- **Hacker News** — community-ranked score (higher score = more popular)
- **RSS feeds** — TechCrunch, Ars Technica, VentureBeat AI, The Verge, MIT Tech Review, Wired

Stories are ranked: HN stories by score first (descending), then RSS stories by feed position.

---

### Step 2 — Select the best story

From the fetch report, choose the **single most compelling story** using these criteria:

**Prefer stories that are:**
- High HN score (signals broad technical community interest)
- About a significant development (product launch, research breakthrough, policy shift, major acquisition)
- Relevant to a general tech-savvy audience on LinkedIn or Twitter/X
- Have a clear "why this matters" angle

**Prefer these topic categories:**
1. AI/ML breakthroughs or major product announcements
2. Significant security or privacy disclosures
3. Major industry moves (acquisitions, pivots, regulatory actions)
4. Engineering or science milestones

**Avoid:**
- Listicles, tutorials, or opinion pieces with no news hook
- Stories that are too niche or only interesting to specialists
- Duplicate coverage of the same underlying event — pick the best-sourced version

---

### Step 3 — Write the social media post

Write **exactly two paragraphs** — no headers, no bullet points, no hashtags unless requested.

**Paragraph 1 — What happened:**
- Open with the core news in the first sentence (who, what, when if relevant)
- Give the 2–3 key factual details that define the story
- Keep it grounded in specifics from the article summary — don't speculate
- Tone: clear, confident, informative — like a senior engineer summarizing for a colleague

**Paragraph 2 — Why it matters:**
- Explain the significance: what does this change, enable, or signal?
- Connect it to a broader trend or implication when relevant
- End with a forward-looking thought or open question (not a call to action)
- Tone: thoughtful analysis, not hype

**After the two paragraphs, on its own line:**
```
🔗 [Article title] — [URL]
```

**Total target length:** 120–180 words (excluding the link line).

---

### Step 4 — Format check

Before presenting, verify:
- [ ] Exactly two paragraphs
- [ ] No "In conclusion" or "In summary" openers
- [ ] No rhetorical questions as openers
- [ ] The link line uses the actual article title and full URL from the fetch report
- [ ] No invented facts — every claim is traceable to the fetch report summary

---

### Example output format

> OpenAI has announced that its models are now available through Amazon Bedrock, making
> GPT-4o and o3 accessible directly within AWS infrastructure. The partnership gives
> enterprise AWS customers a managed endpoint for OpenAI's flagship models alongside
> existing Bedrock providers like Anthropic, Mistral, and Meta — without requiring
> separate OpenAI API credentials.
>
> This signals a notable shift in how the major frontier labs are approaching
> distribution. Rather than competing solely through direct API access, OpenAI is
> meeting enterprise buyers where their existing cloud commitments already are. For
> teams already standardized on Bedrock's unified interface, the barrier to switching
> between model providers just dropped significantly.

🔗 OpenAI models coming to Amazon Bedrock — https://stratechery.com/...

---

## Flags reference

| Flag | Effect |
|---|---|
| *(none)* | All categories: AI, tech, engineering |
| `--ai` | AI/ML focus only |
| `--tech` | Broad technology focus |
| `--engineering` | Hardware, semiconductors, energy, aerospace |
| `--limit N` | Return top N stories (default: 5) |
| `--hours N` | Lookback window in hours (default: 24) |

## Error handling

| Condition | Response |
|---|---|
| No stories found | Suggest widening with `--hours 48` or removing category filter |
| All RSS feeds returned 0 items | Note this; HN stories alone are sufficient |
| Fetch script network error | Report which source failed; others may still work |
| Article summary is empty | Use the title and HN comment count to infer significance; note that full article wasn't accessible |
