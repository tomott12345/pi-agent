---
name: digital-twin
description: |
  Researches and surfaces Digital Twin projects, innovations, case studies,
  standards, and ecosystem news across industries (manufacturing, smart cities,
  healthcare, energy, infrastructure, aerospace, and more). Aggregates from
  academic preprint servers (arXiv), industry blogs, standards bodies (ISO, IEC,
  Industrial Internet Consortium, Digital Twin Consortium), vendor news (Siemens,
  ANSYS, PTC, NVIDIA Omniverse, Azure Digital Twins, AWS IoT TwinMaker), and
  general tech news. Returns a structured briefing: top projects or innovations,
  a technology landscape summary, notable vendors or consortia, and a "so what"
  takeaway for practitioners. Use when asked about Digital Twins, the Digital Twin
  ecosystem, DT-related standards, real-world DT deployments, or emerging DT
  research. Also handles questions like "what's new in digital twins," "find DT
  use cases in [industry]," or "who are the key players in digital twin platforms."
license: MIT
compatibility: "Linux/macOS (requires Python 3; no external packages needed)"
metadata:
  author: "Thomas Ott"
  version: "1.0"
---

# Digital Twin Research Skill

Finds and synthesizes Digital Twin projects, innovations, standards, and ecosystem news across industries. Returns a structured briefing with a practitioner-focused "so what" takeaway.

## Invocation

```
/digital-twin
/digital-twin --industry manufacturing
/digital-twin --industry smart-cities
/digital-twin --topic standards
/digital-twin --topic platforms
/digital-twin --query "predictive maintenance aerospace"
/digital-twin --limit 8
```

Examples:
```
/digital-twin
/digital-twin --industry healthcare
/digital-twin --topic research
/digital-twin --query "NVIDIA Omniverse digital twin"
/digital-twin --industry energy --limit 10
```

## Flags reference

| Flag | Effect |
|---|---|
| *(none)* | Broad scan: all industries, all categories |
| `--industry <name>` | Focus on a specific vertical (see industry list below) |
| `--topic <name>` | Focus area: `standards`, `platforms`, `research`, `case-studies`, `funding` |
| `--query "<text>"` | Free-text search term appended to all queries |
| `--limit N` | Number of results to surface (default: 5) |
| `--hours N` | Lookback window in hours (default: 72) |

### Supported industries

`manufacturing` · `smart-cities` · `healthcare` · `energy` · `infrastructure`
`aerospace` · `automotive` · `construction` · `logistics` · `defense`

---

## Instructions for the model

### Step 1 — Run the fetch script

```bash
python3 scripts/fetch_digital_twin.py [--industry <name>] [--topic <name>] [--query "<text>"] [--limit N] [--hours N]
```

The script queries:
- **Hacker News** — community-ranked stories mentioning digital twin, DT, or related keywords
- **arXiv** (`cs.RO`, `cs.SY`, `eess.SY`) — preprints on cyber-physical systems, digital shadows, and simulation
- **RSS feeds** — IIC (Industrial Internet Consortium) Blog, Fierce Electronics, VentureBeat AI, MIT Tech Review
- **Vendor blogs** — Siemens, PTC, ANSYS, NVIDIA Omniverse, Microsoft Azure Digital Twins, AWS IoT TwinMaker

Stories are ranked: HN by score, arXiv by recency, RSS by feed position.

---

### Step 2 — Classify each result

For each result, tag it with:

**Category:**
- `PROJECT` — a deployed or in-progress real-world Digital Twin implementation
- `INNOVATION` — a research paper, prototype, or early-stage concept
- `PLATFORM` — a tool, SDK, or infrastructure announcement
- `STANDARD` — a specification, consortium initiative, or interoperability framework
- `FUNDING` — investment, acquisition, or partnership news
- `ANALYSIS` — market research, opinion, or industry overview

**Fidelity level** (for PROJECT and INNOVATION):
- `CONCEPT` — whitepaper or announcement only, no deployed system
- `PILOT` — limited real-world deployment or proof of concept
- `OPERATIONAL` — full production deployment with reported outcomes

**Spin level** (same scale as social-media-news):
- `LOW` — independent reporting, verifiable claims, multiple sources
- `MEDIUM` — mix of vendor messaging and independent content
- `HIGH` — press release or marketing-driven; claims unverified

---

### Step 3 — Build the briefing

Output a structured briefing in the following sections:

---

#### 🌐 Digital Twin Briefing — [Date]
*[Industry/topic focus if filtered; otherwise "All Industries"]*

---

**Top Findings** *(list up to N items, ranked by relevance + recency)*

For each item:
```
[CATEGORY | FIDELITY] Title — Source
  One sentence: what it is and what it does.
  Key detail: the most specific, useful fact (metric, partner, scale, standard).
  ⚠️ Spin: [MEDIUM|HIGH] — reason  ← omit if LOW
```

---

**Technology Landscape** *(1–2 short paragraphs)*

Summarize the pattern you see across findings:
- What technology approaches are most active right now (simulation coupling, IoT integration, AI/ML inference on twins, standards convergence, etc.)
- Which industries are seeing the most activity
- Any notable gaps — verticals or use cases underserved by current coverage

---

**Key Players Spotted** *(only players that appeared in this run's results)*

| Player | Type | Role in this briefing |
|---|---|---|
| e.g., Siemens | Vendor | Announced X for manufacturing DTs |
| e.g., Digital Twin Consortium | Standards body | Published interoperability framework |

---

**So What** *(2–3 sentences for a practitioner)*

What should a Digital Twin practitioner, engineer, or technology decision-maker take away from this briefing? Focus on:
- What's worth tracking closely
- What's still hype vs. what's showing real production evidence
- An actionable question to ask before adopting any of the above

---

### Step 4 — Format check

Before presenting, verify:
- [ ] Every item has a Category and (where applicable) Fidelity tag
- [ ] Spin level flagged for MEDIUM and HIGH items
- [ ] "Technology Landscape" synthesizes across results — not just a repeat of individual items
- [ ] "Key Players" table only includes players that actually appeared in results
- [ ] "So What" is practitioner-focused and grounded in the specific results, not generic advice
- [ ] No invented facts — every claim traces back to the fetch report

---

## Key concepts and vocabulary

Use these terms precisely when writing the briefing:

| Term | Meaning |
|---|---|
| Digital Twin | A dynamic virtual replica of a physical asset, process, or system that syncs with real-world data |
| Digital Shadow | One-way: real world → model (no feedback loop back to physical) |
| Digital Thread | The data lineage connecting design, manufacturing, and operational data across a product's lifecycle |
| Physics-based simulation | High-fidelity model grounded in physical laws (FEA, CFD, etc.) |
| Data-driven twin | Model built primarily from sensor data and ML, not physics equations |
| Hybrid twin | Combines physics-based and data-driven modeling |
| Cyber-physical system (CPS) | Physical system with embedded computational and networking elements |
| Interoperability | Ability for twins from different vendors/tools to exchange data (see: DTDL, AAS, IFC) |
| DTDL | Digital Twins Definition Language — Microsoft's open modeling language |
| AAS | Asset Administration Shell — Industry 4.0 standard from IEC/Plattform Industrie 4.0 |
| IFC | Industry Foundation Classes — BIM standard used in construction/infrastructure twins |

---

## Standards and consortia to watch

| Body | Focus |
|---|---|
| Digital Twin Consortium (DTC) | Cross-industry DT definitions, use cases, and interoperability |
| Industrial Internet Consortium (IIC) | IIoT + DT architecture for industrial systems |
| Plattform Industrie 4.0 | AAS standard; German-led, EU-aligned |
| ISO/IEC JTC 1 SC 41 | IoT and Digital Twin international standards |
| buildingSMART | BIM/IFC standards for infrastructure and construction twins |
| AIAA | Digital Twin standards for aerospace systems |

---

## Error handling

| Condition | Response |
|---|---|
| No results found | Broaden with `--hours 168` (1 week) or remove industry/topic filter |
| All RSS feeds returned 0 items | Note it; HN and arXiv results alone are sufficient |
| arXiv unavailable | Report it; continue with RSS and HN sources |
| Vendor blog fetch fails | Skip and note which vendor; don't block the briefing |
| All results are HIGH spin | Flag this explicitly in "So What" — it may mean the topic is in a hype cycle |
