#!/usr/bin/env python3
"""
Fetch Digital Twin projects, innovations, standards, and ecosystem news.
Sources (no API key required):
  - Hacker News API (ranked by community score)
  - arXiv (cs.RO, cs.SY, eess.SY — cyber-physical systems, control, robotics)
  - RSS feeds: IIC Blog, Fierce Electronics, VentureBeat AI, MIT Tech Review

Usage:
    python3 fetch_digital_twin.py
    python3 fetch_digital_twin.py --industry manufacturing
    python3 fetch_digital_twin.py --topic standards
    python3 fetch_digital_twin.py --query "predictive maintenance"
    python3 fetch_digital_twin.py --limit 8
    python3 fetch_digital_twin.py --hours 168
"""

import argparse
import html as html_module
import html.parser
import json
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

# ── HTTP ──────────────────────────────────────────────────────────────────────

_ctx = ssl._create_unverified_context()


def _get(url: str, headers: dict | None = None) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; pi-agent-dt/1.0)", **(headers or {})},
    )
    try:
        with urllib.request.urlopen(req, timeout=14) as r:
            return r.read().decode("utf-8", errors="ignore")
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, ssl.SSLError):
            with urllib.request.urlopen(req, timeout=14, context=_ctx) as r:
                return r.read().decode("utf-8", errors="ignore")
        raise


def _get_json(url: str) -> dict | list:
    return json.loads(_get(url))


# ── Keyword sets ──────────────────────────────────────────────────────────────

# Core DT terms — must match to be included at all
DT_CORE = [
    "digital twin", "digital twins", "digital shadow", "digital thread",
    "cyber-physical", "cyber physical", "asset administration shell",
    "industrial iot", "iiot", "physics-based model", "simulation model",
    "virtual replica", "virtual model", "omniverse", "azure digital twin",
    "aws iot twinmaker", "twinmaker", "dtdl", "asset twin",
]

INDUSTRY_KEYWORDS: dict[str, list[str]] = {
    "manufacturing":  ["manufacturing", "factory", "production line", "cnc", "industry 4.0",
                       "additive manufacturing", "quality control", "assembly", "plc", "scada"],
    "smart-cities":   ["smart city", "smart cities", "urban", "infrastructure", "traffic",
                       "water network", "building management", "bim", "ifc", "city planning"],
    "healthcare":     ["healthcare", "hospital", "patient", "medical device", "surgical",
                       "organ", "clinical", "pharma", "drug discovery", "biomedical"],
    "energy":         ["energy", "grid", "power plant", "wind turbine", "solar farm",
                       "battery storage", "oil and gas", "pipeline", "substation", "utility"],
    "infrastructure": ["bridge", "tunnel", "road", "railway", "port", "airport",
                       "construction", "structural health", "civil engineering"],
    "aerospace":      ["aerospace", "aircraft", "satellite", "rocket", "nasa", "esa",
                       "drone", "uav", "avionics", "propulsion", "airframe"],
    "automotive":     ["automotive", "vehicle", "car", "ev ", "electric vehicle",
                       "autonomous driving", "powertrain", "fleet"],
    "construction":   ["construction", "building", "bim", "ifc", "facility management",
                       "structural", "hvac", "mep"],
    "logistics":      ["logistics", "supply chain", "warehouse", "shipping", "port",
                       "cold chain", "last mile", "inventory"],
    "defense":        ["defense", "military", "naval", "army", "weapon system",
                       "simulation training", "mission planning"],
}

TOPIC_KEYWORDS: dict[str, list[str]] = {
    "standards":      ["standard", "specification", "interoperability", "iso ", "iec ",
                       "dtdl", "aas", "ifc", "consortium", "framework", "protocol"],
    "platforms":      ["platform", "sdk", "api", "cloud", "saas", "omniverse", "azure",
                       "aws", "siemens", "ptc", "ansys", "dassault", "ge digital",
                       "bentley", "hexagon", "rockwell"],
    "research":       ["arxiv", "preprint", "paper", "study", "algorithm", "model",
                       "ml ", "machine learning", "neural", "reinforcement", "simulation"],
    "case-studies":   ["case study", "deployment", "implementation", "pilot", "production",
                       "real-world", "result", "outcome", "roi", "saved"],
    "funding":        ["funding", "investment", "series a", "series b", "raised",
                       "acquisition", "merger", "partnership", "contract", "award"],
}

ALL_DT = DT_CORE + [kw for kws in INDUSTRY_KEYWORDS.values() for kw in kws]


def _text_matches(text: str, keywords: list[str]) -> bool:
    t = text.lower()
    return any(k in t for k in keywords)


def is_dt_relevant(text: str) -> bool:
    return _text_matches(text, DT_CORE)


def matches_industry(text: str, industry: str) -> bool:
    if industry == "all":
        return True
    return _text_matches(text, INDUSTRY_KEYWORDS.get(industry, []))


def matches_topic(text: str, topic: str) -> bool:
    if topic == "all":
        return True
    return _text_matches(text, TOPIC_KEYWORDS.get(topic, []))


def tag_industries(text: str) -> list[str]:
    t = text.lower()
    return [ind for ind, kws in INDUSTRY_KEYWORDS.items() if any(k in t for k in kws)] or ["general"]


def tag_topics(text: str) -> list[str]:
    t = text.lower()
    return [top for top, kws in TOPIC_KEYWORDS.items() if any(k in t for k in kws)] or ["innovation"]


# ── Meta description extractor ────────────────────────────────────────────────

class _MetaParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.og_desc = self.desc = ""
        self._done = False

    def handle_starttag(self, tag, attrs):
        if self._done or tag != "meta":
            return
        d = dict(attrs)
        prop = (d.get("property") or d.get("name") or "").lower()
        content = html_module.unescape(d.get("content", ""))
        if prop == "og:description":
            self.og_desc = content
        elif prop in ("description", "twitter:description") and not self.desc:
            self.desc = content
        if self.og_desc and self.desc:
            self._done = True


def fetch_meta(url: str) -> str:
    try:
        raw = _get(url)[:12_000]
        p = _MetaParser()
        p.feed(raw)
        return p.og_desc or p.desc or ""
    except Exception:
        return ""


# ── RSS helper ────────────────────────────────────────────────────────────────

_NS = {
    "atom":    "http://www.w3.org/2005/Atom",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc":      "http://purl.org/dc/elements/1.1/",
}


def _rss_text(el, tag: str) -> str:
    node = el.find(tag)
    if node is None:
        node = el.find(f"atom:{tag}", _NS)
    if node is None:
        return ""
    text = (node.text or "").strip()
    return html_module.unescape(re.sub(r"<[^>]+>", "", text)).strip()


def _parse_date(raw: str) -> datetime | None:
    raw = raw.strip()
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S GMT",
                "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            dt = datetime.strptime(raw, fmt)
            return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
        except ValueError:
            continue
    return None


RSS_FEEDS = [
    ("IIC Blog",               "https://feeds.feedburner.com/IndustrialInternetConsortium"),
    ("Fierce Electronics",     "https://www.fierceelectronics.com/rss/xml"),
    ("VentureBeat AI",         "https://venturebeat.com/category/ai/feed/"),
    ("MIT Tech Review",        "https://www.technologyreview.com/feed/"),
]


def fetch_rss(source: str, url: str, cutoff: datetime,
              industry: str, topic: str, query: str) -> list[dict]:
    stories = []
    try:
        raw = _get(url)
        root = ET.fromstring(raw)
        items = root.findall(".//item") or root.findall(".//atom:entry", _NS)
        for item in items[:30]:
            title = _rss_text(item, "title")
            link  = _rss_text(item, "link")
            desc  = _rss_text(item, "description") or _rss_text(item, "summary")
            combined = f"{title} {desc}"

            if not link:
                link_el = item.find("atom:link", _NS)
                if link_el is not None:
                    link = link_el.get("href", "")

            pub = _parse_date(_rss_text(item, "pubDate") or _rss_text(item, "published"))
            if pub and pub < cutoff:
                continue
            if not link:
                continue

            if not is_dt_relevant(combined):
                continue
            if not matches_industry(combined, industry):
                continue
            if not matches_topic(combined, topic):
                continue
            if query and query.lower() not in combined.lower():
                continue

            stories.append({
                "title":      title,
                "url":        link,
                "source":     source,
                "score":      0,
                "comments":   0,
                "published":  pub.strftime("%Y-%m-%d %H:%M UTC") if pub else "recent",
                "description": desc[:500] if desc else "",
                "industries": tag_industries(combined),
                "topics":     tag_topics(combined),
                "hn_id":      None,
            })
    except Exception as exc:
        print(f"  RSS {source}: {exc}", file=sys.stderr)
    return stories


# ── Hacker News ───────────────────────────────────────────────────────────────

HN_BASE = "https://hacker-news.firebaseio.com/v0"


def fetch_hn(cutoff: datetime, industry: str, topic: str,
             query: str, max_fetch: int = 120) -> list[dict]:
    stories = []
    ids = _get_json(f"{HN_BASE}/topstories.json")[:max_fetch]
    for sid in ids:
        try:
            s = _get_json(f"{HN_BASE}/item/{sid}.json")
        except Exception:
            continue
        if not s or s.get("type") != "story" or s.get("dead") or s.get("deleted"):
            continue
        ts = datetime.fromtimestamp(s.get("time", 0), tz=timezone.utc)
        if ts < cutoff:
            continue
        title = s.get("title", "")
        url   = s.get("url", f"https://news.ycombinator.com/item?id={sid}")
        combined = title

        if not is_dt_relevant(combined):
            continue
        if not matches_industry(combined, industry):
            continue
        if not matches_topic(combined, topic):
            continue
        if query and query.lower() not in combined.lower():
            continue

        stories.append({
            "title":      title,
            "url":        url,
            "source":     "Hacker News",
            "score":      s.get("score", 0),
            "comments":   s.get("descendants", 0),
            "published":  ts.strftime("%Y-%m-%d %H:%M UTC"),
            "description": "",
            "industries": tag_industries(combined),
            "topics":     tag_topics(combined),
            "hn_id":      sid,
        })
        time.sleep(0.03)
    return stories


# ── arXiv ─────────────────────────────────────────────────────────────────────

ARXIV_CATEGORIES = ["cs.RO", "cs.SY", "eess.SY", "cs.ET"]
ARXIV_BASE = "http://export.arxiv.org/api/query"

ARXIV_SEARCH_TERMS = [
    "digital twin", "cyber-physical system", "digital shadow",
    "asset administration shell", "industrial IoT simulation",
]


def fetch_arxiv(cutoff: datetime, industry: str, topic: str,
                query: str, max_results: int = 30) -> list[dict]:
    # Only fetch from arXiv when topic is research/all or no topic filter
    if topic not in ("all", "research"):
        return []

    search_query = query if query else " OR ".join(f'"{t}"' for t in ARXIV_SEARCH_TERMS)
    cat_filter   = " OR ".join(f"cat:{c}" for c in ARXIV_CATEGORIES)
    full_query   = f"({search_query}) AND ({cat_filter})"

    params = urllib.parse.urlencode({
        "search_query": full_query,
        "start":        0,
        "max_results":  max_results,
        "sortBy":       "submittedDate",
        "sortOrder":    "descending",
    })

    stories = []
    try:
        raw  = _get(f"{ARXIV_BASE}?{params}")
        root = ET.fromstring(raw)
        ns   = {"atom": "http://www.w3.org/2005/Atom"}

        for entry in root.findall("atom:entry", ns):
            title   = (entry.findtext("atom:title", "", ns) or "").replace("\n", " ").strip()
            summary = (entry.findtext("atom:summary", "", ns) or "").replace("\n", " ").strip()
            link_el = entry.find("atom:id", ns)
            url     = (link_el.text or "").strip() if link_el is not None else ""
            pub_raw = entry.findtext("atom:published", "", ns) or ""
            combined = f"{title} {summary}"

            pub = _parse_date(pub_raw)
            if pub and pub < cutoff:
                continue

            if not is_dt_relevant(combined):
                continue
            if not matches_industry(combined, industry):
                continue
            if query and query.lower() not in combined.lower():
                continue

            # Build author string
            authors = [
                a.findtext("atom:name", "", ns)
                for a in entry.findall("atom:author", ns)
            ]
            author_str = ", ".join(authors[:3])
            if len(authors) > 3:
                author_str += " et al."

            stories.append({
                "title":      title,
                "url":        url,
                "source":     "arXiv",
                "score":      0,
                "comments":   0,
                "published":  pub.strftime("%Y-%m-%d %H:%M UTC") if pub else "recent",
                "description": summary[:500],
                "industries": tag_industries(combined),
                "topics":     ["research"],
                "hn_id":      None,
                "authors":    author_str,
            })
    except Exception as exc:
        print(f"  arXiv: {exc}", file=sys.stderr)
    return stories


# ── Dedup + rank ──────────────────────────────────────────────────────────────

def _norm_url(url: str) -> str:
    try:
        p = urllib.parse.urlparse(url)
        return f"{p.netloc}{p.path}".rstrip("/").lower()
    except Exception:
        return url.lower()


def merge_and_rank(hn: list[dict], rss_all: list[dict],
                   arxiv: list[dict]) -> list[dict]:
    seen: dict[str, dict] = {}

    for s in sorted(hn, key=lambda x: x["score"], reverse=True):
        seen[_norm_url(s["url"])] = s

    for i, s in enumerate(rss_all):
        key = _norm_url(s["url"])
        if key not in seen:
            s["_rss_rank"] = i
            seen[key] = s

    for s in arxiv:
        key = _norm_url(s["url"])
        if key not in seen:
            seen[key] = s

    combined = list(seen.values())
    combined.sort(key=lambda s: (-s["score"], s.get("_rss_rank", 9999)))
    return combined


# ── Output ────────────────────────────────────────────────────────────────────

def print_story(i: int, s: dict) -> None:
    industries = ", ".join(s["industries"]).upper()
    topics     = ", ".join(s["topics"]).upper()

    if s["score"] > 0:
        score_info = f"HN score: {s['score']}, {s['comments']} comments"
    elif s["source"] == "arXiv":
        score_info = f"arXiv preprint"
    else:
        score_info = f"RSS: {s['source']}"

    print(f"\n{'─' * 72}")
    print(f"RESULT #{i}  [INDUSTRY: {industries}]  [TOPIC: {topics}]")
    print(f"Title:    {s['title']}")
    print(f"Source:   {s['source']}  ({score_info})")
    print(f"URL:      {s['url']}")
    print(f"Posted:   {s['published']}")
    if s.get("authors"):
        print(f"Authors:  {s['authors']}")
    if s.get("description"):
        desc = re.sub(r"\s+", " ", s["description"]).strip()
        print(f"Summary:  {desc[:500]}")
    if s.get("hn_id"):
        print(f"HN Discussion: https://news.ycombinator.com/item?id={s['hn_id']}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch Digital Twin news and research")
    parser.add_argument("--industry", default="all",
                        choices=["all"] + list(INDUSTRY_KEYWORDS.keys()),
                        help="Industry vertical to focus on (default: all)")
    parser.add_argument("--topic", default="all",
                        choices=["all"] + list(TOPIC_KEYWORDS.keys()),
                        help="Topic area to focus on (default: all)")
    parser.add_argument("--query",  default="", help="Free-text search term")
    parser.add_argument("--limit",  type=int, default=5, help="Number of results (default: 5)")
    parser.add_argument("--hours",  type=int, default=72,
                        help="Lookback window in hours (default: 72)")
    args = parser.parse_args()

    cutoff  = datetime.now(timezone.utc) - timedelta(hours=args.hours)
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    print("=" * 72)
    print(f"DIGITAL TWIN FETCH REPORT  |  Generated: {now_str}")
    print(f"Window: last {args.hours}h  |  Industry: {args.industry.upper()}"
          f"  |  Topic: {args.topic.upper()}"
          + (f"  |  Query: \"{args.query}\"" if args.query else ""))
    print("=" * 72)

    print("\nFetching Hacker News...", end=" ", flush=True)
    hn_stories = fetch_hn(cutoff, args.industry, args.topic, args.query)
    print(f"{len(hn_stories)} matching stories")

    rss_all = []
    for name, url in RSS_FEEDS:
        print(f"Fetching {name}...", end=" ", flush=True)
        items = fetch_rss(name, url, cutoff, args.industry, args.topic, args.query)
        print(f"{len(items)} items")
        rss_all.extend(items)
        time.sleep(0.3)

    print("Fetching arXiv...", end=" ", flush=True)
    arxiv_stories = fetch_arxiv(cutoff, args.industry, args.topic, args.query)
    print(f"{len(arxiv_stories)} preprints")

    all_results = merge_and_rank(hn_stories, rss_all, arxiv_stories)

    if not all_results:
        print("\nNo matching results found.")
        print("Try: --hours 168  (extend to 1 week)")
        print("     remove --industry or --topic filters")
        print("     broaden or remove --query")
        sys.exit(0)

    # Fetch meta descriptions for top candidates
    top = all_results[: args.limit + 3]
    print(f"\nFetching article summaries for top {len(top)} candidates...")
    for s in top:
        if not s["description"] and s["source"] not in ("arXiv",):
            s["description"] = fetch_meta(s["url"])[:500]
            time.sleep(0.2)

    print(f"\n{'=' * 72}")
    print(f"TOP RESULTS ({min(args.limit, len(all_results))} of {len(all_results)} found)")
    print(f"{'=' * 72}")

    for i, s in enumerate(all_results[: args.limit], 1):
        print_story(i, s)

    print(f"\n{'=' * 72}")
    print("END OF FETCH REPORT")
    print("Next: classify each result, score for spin, and build the DT briefing.")
    print(f"{'=' * 72}\n")


if __name__ == "__main__":
    main()
