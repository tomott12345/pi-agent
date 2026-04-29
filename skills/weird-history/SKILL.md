---
name: weird-history
description: |
  Searches for weird, surprising, or fascinating historical facts near any US zip
  code or location name (e.g., "07405", "Butler, NJ"). Geocodes the location, finds
  nearby Wikipedia articles, and uses the LLM to identify the most interesting or
  unusual historical fact — something most people wouldn't know. Always includes a
  direct Wikipedia link. Use when asked about local history, unusual facts, hidden
  history, or "what's interesting about X."
license: MIT
compatibility: "Linux/macOS (requires Python 3; no external packages needed)"
metadata:
  author: "Thomas Ott"
  version: "1.0"
---

# Weird History Skill

## Invocation

```
/weird-history <zip code or location>
```

Examples:
```
/weird-history Butler, NJ
/weird-history 07405
/weird-history Pompton Lakes, NJ
/weird-history Kinnelon, New Jersey
```

## Instructions for the model

### Step 1 — Run the search script

```bash
python3 scripts/history_search.py <location>
```

The script geocodes the location and returns all nearby Wikipedia articles (within
10 km) with their full introductory extracts and URLs.

### Step 2 — Find the most interesting fact

Read through all returned article extracts and look for content that falls into one
or more of these "weird or cool" categories:

| Category | What to look for |
|---|---|
| **Crimes & mysteries** | Notable murders, unsolved cases, heists, scandals |
| **Famous people** | Surprising birthplaces, childhood homes, deaths |
| **Disasters** | Floods, fires, explosions, industrial accidents |
| **Strange buildings** | Odd architecture, abandoned places, haunted sites |
| **World records** | Largest, first, oldest, smallest of anything |
| **Military history** | Battles, forts, POW camps, weapon testing |
| **Industry & invention** | First factories, unusual products, lost industries |
| **Natural oddities** | Geological anomalies, strange flora/fauna, weather events |
| **Legends & folklore** | Local myths, ghost stories, Native American history |
| **Political intrigue** | Riots, protests, unusual laws, political drama |

**Scoring guidance — prefer facts that are:**
- Surprising ("I had no idea that happened here")
- Specific ("On March 4, 1902..." beats "In the early 1900s...")
- Dramatic or vivid
- Little-known outside the local community
- Connected to a larger story

**Avoid:**
- Generic founding dates ("incorporated in 1901")
- Population statistics
- School district information
- Anything that is obviously well-known

### Step 3 — Present the finding

Structure the response as:

**🏛️ [Catchy title for the fact]**

A 2–4 sentence write-up that tells the story engagingly — set the scene, give
the specific details, and land on what makes it weird or remarkable. Write it
like a local history newsletter, not an encyclopedia entry.

> **Learn more:** [Full Wikipedia article title](URL)

### Step 4 — Offer runner-ups

If 2–3 other articles had genuinely interesting content, briefly mention them:

> **Also interesting nearby:**
> - [Short 1-sentence tease] — [Article title](URL)
> - [Short 1-sentence tease] — [Article title](URL)

### Step 5 — Nothing weird found?

If no articles contain genuinely unusual content (everything is generic town/school
descriptions), say so honestly:
> "The area around [location] doesn't have many Wikipedia articles with unusual history
> within 10 km. Here's the most notable thing I found: [best available fact + link]"

## Error handling

| Condition | Response |
|---|---|
| Location not found | Ask the user to clarify (add state or country) |
| No Wikipedia articles nearby | Report this; suggest a nearby larger town |
| Only generic civic articles returned | Present the best available and note the limitation |
| Network error | Report the error; suggest retrying |
