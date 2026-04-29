#!/usr/bin/env python3
"""
Fetch last 24 hours of top AI, technology, and engineering news.
Sources (no API key required):
  - Hacker News API (ranked by community score)
  - RSS feeds: TechCrunch, Ars Technica, VentureBeat AI, The Verge, MIT Tech Review

Usage:
    python3 fetch_news.py               # top stories, all categories
    python3 fetch_news.py --ai          # AI/ML focus
    python3 fetch_news.py --tech        # broad technology
    python3 fetch_news.py --engineering # engineering/hardware focus
    python3 fetch_news.py --limit 10    # return top N stories (default 5)
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

# ── HTTP ─────────────────────────────────────────────────────────────────────

_ctx = ssl._create_unverified_context()


def _get(url: str, headers: dict | None = None, decode: bool = True):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; pi-agent-news/1.0)", **(headers or {})},
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            raw = r.read()
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, ssl.SSLError):
            with urllib.request.urlopen(req, timeout=12, context=_ctx) as r:
                raw = r.read()
        else:
            raise
    return raw.decode("utf-8", errors="ignore") if decode else raw


def _get_json(url: str) -> dict | list:
    return json.loads(_get(url))


# ── Keyword sets ─────────────────────────────────────────────────────────────

CATEGORY_KEYWORDS = {
    "ai": [
        "artificial intelligence", "machine learning", " ai ", "llm", "large language",
        "gpt", "claude", "gemini", "openai", "anthropic", "deepmind", "mistral",
        "neural network", "deep learning", "robotics", "chatbot", "generative",
        "diffusion model", "transformer", "inference", "fine-tun", "agent",
    ],
    "tech": [
        "software", "hardware", "startup", "silicon valley", "big tech", "cloud",
        "cybersecurity", "data breach", "open source", "programming", "developer",
        "app", "platform", "api", "database", "internet", "broadband", "5g",
    ],
    "engineering": [
        "engineering", "semiconductor", "chip", "processor", "quantum", "battery",
        "energy storage", "nuclear", "aerospace", "drone", "satellite", "materials",
        "biotech", "crispr", "gene", "fusion", "solar", "electric vehicle", "ev ",
    ],
}

ALL_KEYWORDS = [kw for kws in CATEGORY_KEYWORDS.values() for kw in kws]


def categorize(text: str) -> list[str]:
    t = text.lower()
    cats = []
    for cat, kws in CATEGORY_KEYWORDS.items():
        if any(k in t for k in kws):
            cats.append(cat)
    return cats or ["tech"]


def matches(text: str, focus: str) -> bool:
    t = text.lower()
    if focus == "all":
        return any(k in t for k in ALL_KEYWORDS)
    return any(k in t for k in CATEGORY_KEYWORDS.get(focus, ALL_KEYWORDS))


# ── Meta description extractor ────────────────────────────────────────────────

class _MetaParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.og_desc = self.desc = self.og_title = ""
        self._done = False

    def handle_starttag(self, tag, attrs):
        if self._done or tag not in ("meta", "title"):
            return
        d = dict(attrs)
        prop = (d.get("property") or d.get("name") or "").lower()
        content = html_module.unescape(d.get("content", ""))
        if prop == "og:description":
            self.og_desc = content
        elif prop in ("description", "twitter:description") and not self.desc:
            self.desc = content
        elif prop == "og:title":
            self.og_title = content
        if self.og_desc and self.desc and self.og_title:
            self._done = True


def fetch_meta(url: str) -> str:
    """Return og:description or meta description from an article URL."""
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
    ("TechCrunch",       "https://techcrunch.com/feed/"),
    ("Ars Technica",     "https://feeds.arstechnica.com/arstechnica/technology-lab"),
    ("VentureBeat AI",   "https://venturebeat.com/category/ai/feed/"),
    ("The Verge",        "https://www.theverge.com/rss/index.xml"),
    ("MIT Tech Review",  "https://www.technologyreview.com/feed/"),
    ("Wired",            "https://www.wired.com/feed/rss"),
]


def fetch_rss(source: str, url: str, cutoff: datetime, focus: str) -> list[dict]:
    stories = []
    try:
        raw = _get(url)
        root = ET.fromstring(raw)
        items = root.findall(".//item") or root.findall(".//atom:entry", _NS)
        for item in items[:20]:
            title = _rss_text(item, "title")
            link  = _rss_text(item, "link")
            desc  = _rss_text(item, "description") or _rss_text(item, "summary")

            # Atom <link href="...">
            if not link:
                link_el = item.find("atom:link", _NS)
                if link_el is not None:
                    link = link_el.get("href", "")

            pub = _parse_date(_rss_text(item, "pubDate") or _rss_text(item, "published"))

            if pub and pub < cutoff:
                continue
            if not matches(f"{title} {desc}", focus):
                continue
            if not link:
                continue

            stories.append({
                "title":   title,
                "url":     link,
                "source":  source,
                "score":   0,          # RSS has no score; ranked by position
                "comments": 0,
                "published": pub.strftime("%Y-%m-%d %H:%M UTC") if pub else "recent",
                "description": desc[:400] if desc else "",
                "categories": categorize(f"{title} {desc}"),
                "hn_id": None,
            })
    except Exception as exc:
        print(f"  RSS {source}: {exc}", file=sys.stderr)
    return stories


# ── Hacker News source ────────────────────────────────────────────────────────

HN_BASE = "https://hacker-news.firebaseio.com/v0"


def fetch_hn(cutoff: datetime, focus: str, max_fetch: int = 80) -> list[dict]:
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
        if not matches(title, focus):
            continue
        stories.append({
            "title":       title,
            "url":         url,
            "source":      "Hacker News",
            "score":       s.get("score", 0),
            "comments":    s.get("descendants", 0),
            "published":   ts.strftime("%Y-%m-%d %H:%M UTC"),
            "description": "",
            "categories":  categorize(title),
            "hn_id":       sid,
        })
        time.sleep(0.03)
    return stories


# ── Dedup + rank ──────────────────────────────────────────────────────────────

def _norm_url(url: str) -> str:
    try:
        p = urllib.parse.urlparse(url)
        return f"{p.netloc}{p.path}".rstrip("/").lower()
    except Exception:
        return url.lower()


def merge_and_rank(hn: list[dict], rss_all: list[dict]) -> list[dict]:
    """Merge sources, deduplicate by URL, rank HN by score then RSS by feed order."""
    seen: dict[str, dict] = {}

    # HN first (has scores)
    for s in sorted(hn, key=lambda x: x["score"], reverse=True):
        key = _norm_url(s["url"])
        seen[key] = s

    # RSS — add if not already present from HN
    for i, s in enumerate(rss_all):
        key = _norm_url(s["url"])
        if key not in seen:
            s["_rss_rank"] = i
            seen[key] = s

    # Final sort: HN stories (score > 0) by score desc, then RSS by original order
    combined = list(seen.values())
    combined.sort(key=lambda s: (-s["score"], s.get("_rss_rank", 9999)))
    return combined


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch last 24h top tech news")
    parser.add_argument("--ai",          action="store_true")
    parser.add_argument("--tech",        action="store_true")
    parser.add_argument("--engineering", action="store_true")
    parser.add_argument("--limit",       type=int, default=5)
    parser.add_argument("--hours",       type=int, default=24, help="Lookback window in hours")
    args = parser.parse_args()

    focus = "ai" if args.ai else "engineering" if args.engineering else \
            "tech" if args.tech else "all"

    cutoff = datetime.now(timezone.utc) - timedelta(hours=args.hours)
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    print("=" * 72)
    print(f"NEWS FETCH REPORT  |  Generated: {now_str}")
    print(f"Window: last {args.hours} hours  |  Focus: {focus.upper()}")
    print("=" * 72)

    # 1. Hacker News
    print("\nFetching Hacker News...", end=" ", flush=True)
    hn_stories = fetch_hn(cutoff, focus)
    print(f"{len(hn_stories)} matching stories")

    # 2. RSS feeds
    rss_all = []
    for name, url in RSS_FEEDS:
        print(f"Fetching {name}...", end=" ", flush=True)
        items = fetch_rss(name, url, cutoff, focus)
        print(f"{len(items)} items")
        rss_all.extend(items)
        time.sleep(0.3)

    # 3. Merge and rank
    all_stories = merge_and_rank(hn_stories, rss_all)

    if not all_stories:
        print("\nNo matching stories found. Try expanding --hours or removing focus filter.")
        sys.exit(0)

    # 4. Fetch meta descriptions for top candidates (up to limit + 3 as buffer)
    top = all_stories[: args.limit + 3]
    print(f"\nFetching article descriptions for top {len(top)} candidates...")
    for s in top:
        if not s["description"]:
            s["description"] = fetch_meta(s["url"])[:500]
            time.sleep(0.2)

    # 5. Print dossier
    print(f"\n{'=' * 72}")
    print(f"TOP STORIES ({min(args.limit, len(all_stories))} of {len(all_stories)} found)")
    print(f"{'=' * 72}")

    for i, s in enumerate(all_stories[: args.limit], 1):
        cats = ", ".join(s["categories"]).upper()
        score_info = (
            f"HN score: {s['score']}, {s['comments']} comments"
            if s["score"] > 0
            else f"RSS: {s['source']}"
        )
        print(f"\n{'─' * 72}")
        print(f"STORY #{i}  [{cats}]")
        print(f"Title:    {s['title']}")
        print(f"Source:   {s['source']}  ({score_info})")
        print(f"URL:      {s['url']}")
        print(f"Posted:   {s['published']}")
        if s["description"]:
            # Clean up description
            desc = re.sub(r"\s+", " ", s["description"]).strip()
            print(f"Summary:  {desc[:400]}")
        if s["hn_id"]:
            print(f"HN Discussion: https://news.ycombinator.com/item?id={s['hn_id']}")

    print(f"\n{'=' * 72}")
    print("END OF FETCH REPORT")
    print("Next: select the top story above and write the social media post.")
    print(f"{'=' * 72}\n")


if __name__ == "__main__":
    main()
