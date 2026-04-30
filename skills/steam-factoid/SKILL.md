---
name: steam-factoid
description: |
  Finds a surprising, little-known factoid from the STEAM fields (Science,
  Technology, Engineering, Arts, Mathematics) for any keyword. Pass a broad
  field like "Math" or a narrow topic like "Rockets" and the skill searches
  Wikipedia for the most interesting historical fact or discovery — always
  with a working link. Use when asked for a fun fact, surprising history, or
  "tell me something cool about X" in any STEAM area.
license: MIT
compatibility: "Linux/macOS (requires Python 3; no external packages needed)"
metadata:
  author: "Thomas Ott"
  version: "1.0"
---

# STEAM Factoid Skill

## Invocation

```
/steam-factoid [keyword]
```

Examples:
```
/steam-factoid Math
/steam-factoid Space
/steam-factoid Engineering
/steam-factoid Cryptography
/steam-factoid Vaccines
/steam-factoid Aviation
/steam-factoid Robotics
```

Supported keyword families:
| Field | Keywords |
|---|---|
| **Science** | science, biology, chemistry, physics, geology, ecology, astronomy |
| **Technology** | technology, computing, computer, internet, robotics, aviation, electronics |
| **Engineering** | engineering, civil, mechanical, electrical, architecture |
| **Arts** | art, music, design, film, photography, animation |
| **Mathematics** | math, mathematics, geometry, algebra, statistics, cryptography |
| **Space** | space, nasa, rockets, planets, stars |
| **Medicine** | medicine, anatomy, vaccines, surgery |

Any other keyword also works — the script falls back to full-text Wikipedia search.

---

## Instructions for the model

### Step 1 — Run the search script

```bash
python3 /Users/ottt/.pi/agent/skills/steam-factoid/scripts/steam_search.py [keyword]
```

The script returns a list of Wikipedia articles with their intro extracts and
canonical URLs, combining full-text search results with category-sampled articles.

### Step 2 — Pick the most interesting factoid

Read every article extract returned and look for content in these "wow" categories:

| Category | What to look for |
|---|---|
| **Firsts & origins** | Who invented it, when, under what bizarre circumstances |
| **Failed attempts** | Famous wrong theories, costly mistakes, rejected discoveries |
| **Surprising people** | Unexpected inventors, self-taught pioneers, overlooked contributors |
| **Hidden connections** | Two unrelated fields secretly linked; discoveries from accidents |
| **Strange timelines** | Things invented far earlier (or later) than expected |
| **Near misses** | Discoveries almost lost, credit disputes, simultaneous independent invention |
| **Unintended consequences** | Invention designed for X, became famous for Y |
| **Scale & extremes** | Largest, fastest, oldest, strangest version of a thing |
| **Lost knowledge** | Techniques forgotten and rediscovered centuries later |
| **Women & minorities** | Overlooked contributors whose role was erased or minimized |

**Prefer facts that are:**
- Genuinely surprising ("I had no idea that…")
- Specific — a name, a date, an exact quantity beats vague generalities
- Vivid — tell a small story, not just a definition
- Verifiable — must be in the Wikipedia article (no hallucination)
- Linked — the URL must come from the script output, not reconstructed

**Avoid:**
- Definitions ("Mathematics is the study of…")
- Well-known textbook facts
- Anything that requires the URL to be guessed or reconstructed

### Step 3 — Present the factoid

Format the response as:

**⚗️ [Catchy title for the factoid]**

A 3–5 sentence write-up that tells the story engagingly. Set up why it matters,
deliver the surprising fact with specific details, then land on why it's remarkable.
Write like a science magazine sidebar, not a textbook.

> **Source:** [Full article title](URL)

### Step 4 — Offer runner-ups

If 2–3 other articles had genuinely compelling content, briefly mention them:

> **Also fascinating:**
> - [One-sentence tease] — [Article title](URL)
> - [One-sentence tease] — [Article title](URL)

### Step 5 — Nothing great found?

If no articles contain a genuinely surprising fact, say so and present the
best available:

> "The search for '[keyword]' didn't turn up anything truly surprising today.
> Here's the most notable thing I found: [best available fact + link]"

---

## Error handling

| Condition | Response |
|---|---|
| No articles returned | Try a broader keyword; report the failure |
| All extracts are definitions | Present the best one; note it's definitional |
| Network error | Report the error; suggest retrying |
| URL looks wrong | Always use the URL from the script output — never reconstruct |
