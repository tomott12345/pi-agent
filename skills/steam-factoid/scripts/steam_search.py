#!/usr/bin/env python3
"""
steam_search.py — Find a surprising STEAM factoid for a given keyword.

Usage:
    python3 steam_search.py <keyword>
    python3 steam_search.py Math
    python3 steam_search.py "Space exploration"
    python3 steam_search.py Engineering

APIs used (no API key required):
    - Wikipedia full-text search (action=query&list=search)
    - Wikipedia random article within a STEAM category
    - Wikipedia extracts API (action=query&prop=extracts|info)

Output:
    A set of candidate articles with their intro extracts and canonical URLs,
    ready for the LLM to select the most interesting factoid.
"""

import json
import random
import ssl
import sys
import urllib.parse
import urllib.request

_UA  = "pi-agent-steam-factoid/1.0"
_ctx = ssl._create_unverified_context()

# ---------------------------------------------------------------------------
# STEAM keyword → Wikipedia category seeds
# Maps broad user keywords to specific Wikipedia categories for deeper pulls
# ---------------------------------------------------------------------------
_CATEGORY_SEEDS = {
    # Science
    "science":       ["History of science", "Scientific discoveries"],
    "biology":       ["History of biology", "Biology discoveries"],
    "chemistry":     ["History of chemistry", "Chemical discoveries"],
    "physics":       ["History of physics", "Physics discoveries"],
    "geology":       ["History of geology"],
    "ecology":       ["Ecology"],
    "astronomy":     ["History of astronomy", "Astronomical discoveries"],

    # Technology
    "technology":    ["History of technology", "Inventions"],
    "computing":     ["History of computing", "Computer science"],
    "computer":      ["History of computing", "Computer science"],
    "internet":      ["History of the Internet", "Web technology"],
    "robotics":      ["Robotics", "History of robots"],
    "aviation":      ["History of aviation", "Aircraft"],
    "electronics":   ["History of electronics"],
    "telecommunications": ["History of telecommunication"],

    # Engineering
    "engineering":   ["History of engineering", "Civil engineering"],
    "civil":         ["History of civil engineering", "Bridges"],
    "mechanical":    ["History of mechanical engineering"],
    "electrical":    ["History of electrical engineering"],
    "architecture":  ["History of architecture", "Architectural history"],

    # Arts
    "art":           ["Art history", "Visual arts"],
    "music":         ["Music history", "History of music"],
    "design":        ["Design history", "Industrial design"],
    "film":          ["History of film", "Cinema history"],
    "photography":   ["History of photography"],
    "animation":     ["History of animation"],

    # Mathematics
    "math":          ["History of mathematics", "Mathematicians"],
    "mathematics":   ["History of mathematics", "Mathematical discoveries"],
    "geometry":      ["History of geometry", "Geometers"],
    "algebra":       ["History of algebra"],
    "statistics":    ["History of statistics"],
    "cryptography":  ["History of cryptography", "Ciphers"],

    # Space / Astronomy (common shortcut)
    "space":         ["History of astronomy", "Space exploration", "Astronomical discoveries"],
    "nasa":          ["NASA", "Space exploration", "Moon landing"],
    "rockets":       ["History of rockets", "Rocketry", "Space launch vehicles"],
    "planets":       ["Planetary science", "Solar System"],
    "stars":         ["Stars", "History of astronomy"],

    # Medicine / Health (S-T-E-A-M variant)
    "medicine":      ["History of medicine", "Medical discoveries"],
    "anatomy":       ["History of anatomy"],
    "vaccines":      ["History of vaccination", "Vaccines"],
    "surgery":       ["History of surgery"],
}

# Fallback categories when no keyword matches
_DEFAULT_CATEGORIES = [
    "History of science",
    "History of technology",
    "History of mathematics",
    "Scientific discoveries",
    "Inventions",
]


def _get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, ssl.SSLError):
            with urllib.request.urlopen(req, timeout=15, context=_ctx) as r:
                return json.loads(r.read())
        raise


def search_articles(keyword: str, limit: int = 40) -> list[dict]:
    """
    Full-text Wikipedia search for the keyword, biased toward history /
    discovery articles by appending context terms.
    """
    queries = [
        f"{keyword} history discovery invention",
        f"{keyword} first discovery scientist",
        f"{keyword} surprising fact origin",
    ]
    seen_ids = set()
    results = []
    for query in queries:
        params = urllib.parse.urlencode({
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": "20",
            "srnamespace": "0",          # article namespace only
            "format": "json",
        })
        data = _get(f"https://en.wikipedia.org/w/api.php?{params}")
        for hit in data.get("query", {}).get("search", []):
            pid = hit["pageid"]
            if pid not in seen_ids:
                seen_ids.add(pid)
                results.append(hit)
        if len(results) >= limit:
            break
    return results[:limit]


def random_category_articles(keyword: str, limit: int = 20) -> list[dict]:
    """
    Pull random articles from Wikipedia categories associated with the keyword.
    This surfaces less-obvious gems compared to pure text search.
    """
    lk = keyword.lower()
    cats = _CATEGORY_SEEDS.get(lk)
    if not cats:
        # Fuzzy match: check if any seed key is contained in the keyword
        for key, val in _CATEGORY_SEEDS.items():
            if key in lk or lk in key:
                cats = val
                break
    if not cats:
        cats = _DEFAULT_CATEGORIES

    results = []
    random.shuffle(cats)
    for cat in cats[:2]:            # fetch from up to 2 categories
        params = urllib.parse.urlencode({
            "action": "query",
            "list": "categorymembers",
            "cmtitle": f"Category:{cat}",
            "cmlimit": "50",
            "cmtype": "page",
            "format": "json",
        })
        data = _get(f"https://en.wikipedia.org/w/api.php?{params}")
        members = data.get("query", {}).get("categorymembers", [])
        random.shuffle(members)
        results.extend(members[:limit // 2])

    return results


def fetch_extracts(page_ids: list[int]) -> dict[int, dict]:
    """Fetch intro extracts and canonical URLs for a list of page IDs."""
    results = {}
    for i in range(0, len(page_ids), 50):
        chunk = page_ids[i : i + 50]
        params = urllib.parse.urlencode({
            "action": "query",
            "prop": "extracts|info|categories",
            "exintro": "1",
            "explaintext": "1",
            "exchars": "2000",
            "inprop": "url",
            "pageids": "|".join(str(p) for p in chunk),
            "cllimit": "10",
            "format": "json",
        })
        data = _get(f"https://en.wikipedia.org/w/api.php?{params}")
        for pid, page in data.get("query", {}).get("pages", {}).items():
            results[int(pid)] = page
    return results


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: steam_search.py <keyword>", file=sys.stderr)
        print("Example: steam_search.py Math", file=sys.stderr)
        sys.exit(1)

    keyword = " ".join(sys.argv[1:])
    print(f"STEAM Factoid Search — keyword: \"{keyword}\"")
    print(f"{'='*70}\n")

    # Two retrieval strategies — blend search + category sampling
    print("Searching Wikipedia full-text...")
    search_hits = search_articles(keyword, limit=30)
    search_ids  = [h["pageid"] for h in search_hits]

    print("Sampling Wikipedia categories...")
    cat_members = random_category_articles(keyword, limit=20)
    cat_ids     = [m["pageid"] for m in cat_members if "pageid" in m]

    all_ids = list(dict.fromkeys(search_ids + cat_ids))  # dedup, preserve order
    print(f"Fetching extracts for {len(all_ids)} candidate articles...\n")

    pages = fetch_extracts(all_ids)

    # Build a title→pageid map for quick lookup
    title_map = {h["title"]: h["pageid"] for h in search_hits}
    title_map.update({m["title"]: m["pageid"] for m in cat_members if "pageid" in m})

    # Print all candidates for the LLM to evaluate
    printed = 0
    for pid in all_ids:
        page = pages.get(pid, {})
        extract = page.get("extract", "").strip()
        if not extract or len(extract) < 100:
            continue

        title = page.get("title", "")
        url   = page.get("fullurl", f"https://en.wikipedia.org/?curid={pid}")
        cats  = [c["title"].replace("Category:", "") for c in page.get("categories", [])]

        print(f"{'='*70}")
        print(f"TITLE:  {title}")
        print(f"URL:    {url}")
        if cats:
            print(f"TAGS:   {', '.join(cats[:6])}")
        print(f"\n{extract}\n")
        printed += 1

    if printed == 0:
        print("No articles with sufficient content found.")
        print("Try a broader keyword (e.g. 'Mathematics', 'Physics', 'Technology').")


if __name__ == "__main__":
    main()
