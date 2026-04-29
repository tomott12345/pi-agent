---
name: coc-investigator
description: |
  Research tool for Call of Cthulhu Keepers. Given any US location (zip code or city
  name), searches Wikipedia for nearby history and targeted occult/crime/mystery
  content, cross-references with real 1920s occult organizations, historical figures,
  and regional Mythos entity data, then produces a Keeper's Dossier: atmospheric
  location description, persons of interest, forbidden knowledge, dark history,
  Mythos connections, and scenario hooks. Use when building a CoC scenario, populating
  a 1920s location, or looking for weird local history with a Lovecraftian spin.
license: MIT
compatibility: "Linux/macOS (requires Python 3; no external packages needed)"
metadata:
  author: "Thomas Ott"
  version: "1.0"
---

# Call of Cthulhu Investigator Skill
### *"That is not dead which can eternal lie, and with strange aeons even death may die."*

## Overview

Researches any US location for use in a Roaring '20s Call of Cthulhu campaign.
Combines real Wikipedia history with curated Mythos reference data (regional entities,
real occult organizations, historical NPC seeds, forbidden tomes, period context) and
presents it as a structured Keeper's Dossier.

## Invocation

```
/coc-investigator <location>
/coc-investigator <location> --occult
/coc-investigator <location> --crime
/coc-investigator --reference
/coc-investigator --reference --region <state>
```

Examples:
```
/coc-investigator New Orleans, LA
/coc-investigator Chicago, IL --crime
/coc-investigator Providence, RI --occult
/coc-investigator 07405
/coc-investigator --reference
/coc-investigator --reference --region MA
```

## Instructions for the Keeper (model)

### Step 1 — Run the research script

```bash
python3 scripts/investigate.py <location> [--occult] [--crime]
```

For reference data only:
```bash
python3 scripts/investigate.py --reference [--region <state>]
```

### Step 2 — Build the Keeper's Dossier

Using the raw research output, construct a dossier with these sections.
Write in a terse, atmospheric style — like a 1920s investigative journalist's
confidential report. Every claim should trace back to a real article or the
provided reference data.

---

#### 📍 SECTION 1: THE LOCATION

Write 2–3 paragraphs describing the location as investigators would find it in
the early 1920s. Include:

- **Geography and atmosphere** — What does it look, smell, and feel like?
- **Population and character** — Who lives here? What industries? What tensions?
- **Period-specific flavor** — How does Prohibition affect it? What social fault lines exist?
- **The surface and what lies beneath** — Present the normal face of the place, then hint at what the research suggests may be wrong.

Draw from the Wikipedia extracts, regional Mythos flavor text, and period context
(newspapers, transportation, social tensions from the reference data).

---

#### 👥 SECTION 2: PERSONS OF INTEREST

Generate 3–5 NPC seeds. Mix:

1. **Historical figures** who could plausibly be in or connected to the area
   (draw from the HISTORICAL_NPCS reference data; adjust location if needed)
2. **Locally-rooted characters** suggested by the Wikipedia articles
   (politicians, criminals, asylum directors, newspaper editors, dock foremen, clergy)
3. **One clearly compromised figure** — someone who has already made contact with
   the wrong thing and doesn't know it, or does know and is in denial

For each NPC provide:
- Name, age, occupation
- Where to find them
- What they know / what they're hiding
- Suggested CoC skills (3–4 key ones with approximate values)
- Whether they are **Ally / Neutral / Antagonist / Unknowing Pawn**

---

#### 📚 SECTION 3: FORBIDDEN KNOWLEDGE

Identify any tome, document, or source of dangerous knowledge that could
plausibly be found here. Draw from:
- The FORBIDDEN_TOMES reference data
- Wikipedia articles about libraries, universities, private collections, or
  estate sales in the area
- Any occult organization with local presence

For each source:
- Where it is (specific building or institution from the research)
- What it contains / what it will do to the reader
- How the investigators might gain access
- What guardian or obstacle stands in the way

---

#### 🏚 SECTION 4: DARK HISTORY

Select the **3 most Mythos-relevant facts** from the Wikipedia articles.

**Scoring criteria — prefer:**
- Violent or unexplained events (murders, disappearances, disasters)
- Institutions with unusual histories (asylums, prisons, old churches, strange private clubs)
- Events with no satisfying official explanation
- Connections to the 1900–1930 period
- Anything involving water, underground spaces, or astronomical events

For each selected fact:
- State the real history in 2–3 sentences (with Wikipedia link)
- Provide the **Mythos explanation** — what actually happened, in CoC terms
- Suggest a **Sanity check** rating: `(0/1d3)`, `(0/1d6)`, `(1/1d8)`, `(1d3/1d10)`
- Note any physical evidence investigators might find

---

#### 🐙 SECTION 5: MYTHOS CONNECTIONS

Based on the region's entity profile and the dark history findings, identify:

**The Primary Threat** — What Great Old One, Outer God, or major entity has
influence here? Why this location? What does it want?

**The Local Cult** — Name, approximate membership, where they meet, what they
are actually doing (vs. what they think they are doing). Use a real organization
from the area with a Mythos twist, or draw from the regional cult list.

**Physical Evidence of Mythos Activity** — 2–3 concrete things investigators
could find:
- An architectural anomaly (non-Euclidean angles, too many rooms, wrong shadows)
- A biological anomaly (fish-smell where there are no fish, unusual mold, dead animals)
- A documentary anomaly (newspaper article that contradicts itself, diary that ends mid-sentence)

---

#### 🎭 SECTION 6: SCENARIO HOOKS

Provide 3 complete scenario seeds, each with:

**Hook name** (evocative title)
- **The call:** What draws investigators to this location? (newspaper article,
  telegram from a missing colleague, letter from a relative, Miskatonic faculty request)
- **The surface mystery:** What does it look like at first glance?
- **The truth:** What is actually going on in Mythos terms?
- **The point of no return:** What moment makes this impossible to simply walk away from?
- **Potential endings:** One good outcome, one bad outcome, one *worse* outcome

---

#### 📋 KEEPER'S NOTES

Brief practical notes:
- **Recommended pre-generated investigators:** What backgrounds fit this location?
  (e.g., "A reporter from the Chicago Tribune, a Miskatonic anthropologist, a
  Prohibition agent who has seen too much")
- **Tone:** Cosmic horror / noir / folk horror / body horror — what fits best here?
- **Session count:** Rough estimate (one-shot / 2–3 sessions / campaign arc)
- **Connections to other locations:** What nearby cities or known Mythos sites
  could this link to?

---

### Step 3 — Cite your sources

Every fact in Sections 1–4 should link back to a Wikipedia article from the
research output OR be flagged as `[Mythos interpretation]` or `[Reference data]`.

### Step 4 — Tone guidelines

**Do:**
- Write in present tense for descriptions ("The old Grunewald Hotel *stands*...")
- Use specific details (street names, dates, names) from the research
- Let the horror be implied before it is stated
- Make the mundane strange before introducing the overtly supernatural

**Don't:**
- Invent historical facts not in the research output
- Make every NPC a cultist (most people are innocent bystanders)
- Resolve the mystery — leave threads for the players to pull
- Describe Mythos entities directly; suggest, imply, hint

---

## Quick Reference — Regional Entities

| Region | Primary Entities | Notes |
|---|---|---|
| New England | Deep Ones, Shoggoths, Nightgaunts | Lovecraft's home; fishing villages hide the worst |
| Mid-Atlantic | Dimensional Shamblers, Byakhee, Dark Young | Immigrant cities; dockside cults; corrupt politicians |
| Deep South | Lloigor, Dark Young, Star Vampires | Bayous; voodoo-adjacent; jazz as ritual |
| Midwest | Ithaqua, Fire Vampires, Mi-Go | Flat horizons; isolated farms; Chicago slaughterhouses |
| Mountain West | Mi-Go, Elder Things, Chthonians | Ancient mines; vanishing survey parties |
| Pacific Coast | Star Spawn, Deep Ones, Mi-Go | Pacific sleep; Chinatown mysteries; California cults |
| Southwest | Cthugha, Chthonians, Formless Spawn | Desert seals; oil drilling disasters |

## Quick Reference — Real Occult Organizations (1920s)

| Organization | US Base | Mythos Hook |
|---|---|---|
| Ordo Templi Orientis | NY, SF, Detroit | Crowley cell with genuine Mythos text |
| Theosophical Society | Wheaton IL (HQ) | Mi-Go posing as Mahatmas |
| AMORC (Rosicrucians) | San Jose CA | Built on anomalous land; corrupted teachings |
| Society for Psychical Research | Boston, NY | Filed three genuine Mythos incidents |
| KKK (Second Era) | Nationwide | Accidental ritual elements; something answered |
| Spiritualist Movement | Lily Dale NY, Camp Chesterfield IN | Channels not to the dead, but to things that pretend |

## Error handling

| Condition | Response |
|---|---|
| Location not found | Ask the user to add a state name or zip code |
| No Wikipedia articles nearby | Report it; suggest a larger nearby city |
| Only generic civic articles | Use reference data and historical seeds; note the gap |
| Rate limit from Wikipedia | Script retries automatically with a short delay |
| Network error | Report and suggest retrying |
