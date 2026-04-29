#!/usr/bin/env python3
"""
CoC Investigator — research script for the Call of Cthulhu Mythos Investigator skill.
Geocodes a US location, searches Wikipedia for nearby and thematically relevant
articles, and outputs a structured research dossier for the Keeper to interpret.

Usage:
    python3 investigate.py <location>
    python3 investigate.py <location> --occult
    python3 investigate.py <location> --crime
    python3 investigate.py --reference            # Print Mythos reference data
    python3 investigate.py --reference --region <state>
"""

import argparse
import json
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# ── HTTP helper ───────────────────────────────────────────────────────────────

_ctx = ssl._create_unverified_context()
_UA  = "coc-investigator/1.0 (call-of-cthulhu research tool)"


def _get(url: str, headers: dict | None = None) -> dict:
    req = urllib.request.Request(url, headers={**{"User-Agent": _UA}, **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, ssl.SSLError):
            with urllib.request.urlopen(req, timeout=15, context=_ctx) as r:
                return json.loads(r.read())
        raise


# ── Geocoding ────────────────────────────────────────────────────────────────

def geocode(location: str) -> tuple[float, float, str, str]:
    """Return (lat, lon, display_name, state_abbr)."""
    params = urllib.parse.urlencode({
        "q": location, "format": "json", "limit": 1,
        "countrycodes": "us", "addressdetails": "1",
    })
    results = _get(
        f"https://nominatim.openstreetmap.org/search?{params}",
        headers={"User-Agent": _UA},
    )
    if not results:
        params2 = urllib.parse.urlencode({"q": location, "format": "json", "limit": 1, "addressdetails": "1"})
        results = _get(f"https://nominatim.openstreetmap.org/search?{params2}", headers={"User-Agent": _UA})
    if not results:
        print(f"Error: Could not geocode '{location}'", file=sys.stderr)
        sys.exit(1)
    r = results[0]
    addr = r.get("address", {})
    state_abbr = addr.get("ISO3166-2-lvl4", "US-NY").split("-")[-1]
    return float(r["lat"]), float(r["lon"]), r["display_name"], state_abbr


# ── Wikipedia helpers ─────────────────────────────────────────────────────────

def wiki_geosearch(lat: float, lon: float, radius: int = 10000, limit: int = 50) -> list[dict]:
    params = urllib.parse.urlencode({
        "action": "query", "list": "geosearch",
        "gscoord": f"{lat}|{lon}",
        "gsradius": min(radius, 10000),
        "gslimit": limit,
        "format": "json",
    })
    data = _get(f"https://en.wikipedia.org/w/api.php?{params}")
    return data.get("query", {}).get("geosearch", [])


def wiki_search(query: str, limit: int = 6) -> list[dict]:
    """Full-text Wikipedia search. Returns list of {pageid, title, snippet}."""
    params = urllib.parse.urlencode({
        "action": "query", "list": "search",
        "srsearch": query, "srlimit": limit,
        "srprop": "snippet", "format": "json",
    })
    try:
        data = _get(f"https://en.wikipedia.org/w/api.php?{params}")
        return data.get("query", {}).get("search", [])
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            time.sleep(2)
            data = _get(f"https://en.wikipedia.org/w/api.php?{params}")
            return data.get("query", {}).get("search", [])
        return []


def fetch_extracts(page_ids: list[int]) -> dict[int, dict]:
    """Fetch intro extracts and URLs for page IDs (max 50 per call)."""
    results = {}
    for i in range(0, len(page_ids), 50):
        chunk = page_ids[i : i + 50]
        params = urllib.parse.urlencode({
            "action": "query", "prop": "extracts|info",
            "exintro": "1", "explaintext": "1", "exchars": "2000",
            "inprop": "url",
            "pageids": "|".join(str(p) for p in chunk),
            "format": "json",
        })
        data = _get(f"https://en.wikipedia.org/w/api.php?{params}")
        for pid, page in data.get("query", {}).get("pages", {}).items():
            results[int(pid)] = page
        if i + 50 < len(page_ids):
            time.sleep(0.5)
    return results


# ── Main research function ────────────────────────────────────────────────────

def run_investigation(location: str, focus: str = "all") -> None:
    sys.path.insert(0, __import__("os").path.dirname(__file__))
    from mythos_data import region_data, HISTORICAL_SEED_EVENTS, OCCULT_ORGS, HISTORICAL_NPCS

    print("=" * 72)
    print("KEEPER'S DOSSIER — FIELD RESEARCH REPORT")
    print("Call of Cthulhu Investigation: Roaring '20s")
    print("=" * 72)

    # 1. Geocode
    lat, lon, display, state = geocode(location)
    city = display.split(",")[0].strip()
    short_loc = ", ".join(p.strip() for p in display.split(",")[:3])
    print(f"\nLOCATION RESOLVED: {short_loc}")
    print(f"COORDINATES:       {lat:.4f}, {lon:.4f}")
    print(f"STATE:             {state}")

    # 2. Regional Mythos context
    region = region_data(state)
    print(f"\n{'─'*72}")
    print(f"REGIONAL MYTHOS PROFILE: {region.get('region_name', 'Unknown Region')}")
    print(f"{'─'*72}")
    print(f"Likely entities:  {', '.join(region.get('entities', []))}")
    print(f"Known cults:      {', '.join(region.get('cults', []))}")
    print(f"\nKeeper flavor:")
    print(f"  {region.get('flavor', '')}")

    # 3. Wikipedia geosearch
    print(f"\n{'─'*72}")
    print(f"WIKIPEDIA GEOSEARCH — 10km radius around {city}")
    print(f"{'─'*72}")
    geo_articles = wiki_geosearch(lat, lon)
    print(f"Found {len(geo_articles)} nearby articles.")

    # 4. Targeted text searches
    search_results: list[dict] = []
    queries = []

    if focus in ("all", "occult"):
        queries += [
            f"{city} occult secret society",
            f"{city} haunted mystery",
        ]
    if focus in ("all", "crime"):
        queries += [
            f"{city} unsolved murder disappearance",
            f"{city} prohibition gangster",
        ]
    if focus == "all":
        queries += [
            f"{city} history legend folklore",
            f"{city} asylum sanitarium",
        ]

    if queries:
        print(f"\n{'─'*72}")
        print(f"TARGETED SEARCHES")
        print(f"{'─'*72}")
        seen_ids = {a["pageid"] for a in geo_articles}
        for q in queries:
            print(f"  Searching: {q!r}")
            hits = wiki_search(q, limit=5)
            for h in hits:
                if h["pageid"] not in seen_ids:
                    search_results.append(h)
                    seen_ids.add(h["pageid"])
            time.sleep(0.75)  # rate limit

    # 5. Fetch extracts for all found pages
    all_ids = [a["pageid"] for a in geo_articles] + [s["pageid"] for s in search_results]
    unique_ids = list(dict.fromkeys(all_ids))  # preserve order, deduplicate

    print(f"\nFetching extracts for {len(unique_ids)} articles...")
    pages = fetch_extracts(unique_ids)

    # Distance lookup for geo articles
    dist_map = {a["pageid"]: a["dist"] for a in geo_articles}

    # 6. Output all articles
    print(f"\n{'=' * 72}")
    print(f"RAW RESEARCH ARTICLES ({len(pages)} total)")
    print(f"{'=' * 72}")
    print("(Keeper: read these and identify the most Mythos-relevant material)\n")

    # Sort: geo articles by distance first, then text search results
    def sort_key(pid):
        if pid in dist_map:
            return (0, dist_map[pid])
        return (1, 0)

    for pid in sorted(pages.keys(), key=sort_key):
        page = pages[pid]
        if not page.get("extract", "").strip():
            continue
        title   = page.get("title", "")
        url     = page.get("fullurl", f"https://en.wikipedia.org/?curid={pid}")
        extract = page["extract"].strip()
        dist    = dist_map.get(pid)
        source  = f"{dist:.0f}m from {city}" if dist is not None else "text search result"

        print(f"{'─' * 72}")
        print(f"TITLE:   {title}")
        print(f"SOURCE:  {source}")
        print(f"URL:     {url}")
        print(f"\n{extract}\n")

    # 7. Historical seed events relevant to region
    relevant_seeds = [
        e for e in HISTORICAL_SEED_EVENTS
        if state in e.get("location", "") or "Nationwide" in e.get("location", "")
    ]
    if relevant_seeds:
        print(f"\n{'=' * 72}")
        print(f"HISTORICAL SEED EVENTS — {state} / National")
        print(f"{'=' * 72}")
        for seed in relevant_seeds:
            print(f"\n📅 {seed['event']} ({seed['date']}) — {seed['location']}")
            print(f"   HISTORY:  {seed['real_facts']}")
            print(f"   MYTHOS:   {seed['mythos_angle']}")

    # 8. Active occult organizations in the area
    print(f"\n{'=' * 72}")
    print(f"ACTIVE OCCULT ORGANIZATIONS (1920s — Nationwide)")
    print(f"{'=' * 72}")
    for org in OCCULT_ORGS:
        print(f"\n🕯  {org['name']} (est. {org['founded']})")
        print(f"   US presence:   {org['us_presence']}")
        print(f"   Real purpose:  {org['real_activities']}")
        print(f"   Mythos angle:  {org['mythos_twist']}")
        print(f"   Wikipedia:     https://en.wikipedia.org/wiki/{urllib.parse.quote(org['wiki_search'].replace(' ','_'))}")

    # 9. Key NPCs
    print(f"\n{'=' * 72}")
    print(f"PERSONS OF INTEREST — KNOWN OCCULTISTS & INVESTIGATORS")
    print(f"{'=' * 72}")
    for npc in HISTORICAL_NPCS:
        print(f"\n👤 {npc['name']} ({npc['born']}–{npc['died']})")
        print(f"   Role:         {npc['occupation']}")
        print(f"   Location:     {npc['location_1920s']}")
        print(f"   CoC purpose:  {npc['coc_role']}")
        if "skills" in npc:
            print(f"   Key skills:   {', '.join(npc['skills'])}")

    print(f"\n{'=' * 72}")
    print(f"END OF FIELD RESEARCH REPORT")
    print(f"Keeper: use the articles above to build the dossier sections below.")
    print(f"{'=' * 72}\n")


# ── Reference mode ───────────────────────────────────────────────────────────

def print_reference(state: str | None = None) -> None:
    sys.path.insert(0, __import__("os").path.dirname(__file__))
    from mythos_data import (
        REGIONAL_ENTITIES, FORBIDDEN_TOMES, PERIOD_CONTEXT,
        region_data
    )

    if state:
        r = region_data(state.upper())
        print(f"REGIONAL MYTHOS DATA: {r.get('region_name')} (state: {state.upper()})")
        print(f"Entities:  {', '.join(r.get('entities', []))}")
        print(f"Cults:     {', '.join(r.get('cults', []))}")
        print(f"Flavor:    {r.get('flavor', '')}")
    else:
        print("FORBIDDEN TOMES OF THE 1920s")
        print("─" * 60)
        for tome in FORBIDDEN_TOMES:
            print(f"\n📖 {tome['title']}")
            print(f"   Author:     {tome['author']}")
            print(f"   Language:   {tome['language']}")
            print(f"   Found at:   {tome['where_found']}")
            print(f"   CoC stats:  {tome['coc_stats']}")
            if "note" in tome:
                print(f"   Note:       {tome['note']}")

        print(f"\n{'─' * 60}")
        print("PERIOD CONTEXT")
        print("─" * 60)
        print(f"\nNewspapers: {', '.join(PERIOD_CONTEXT['newspapers'])}")
        print(f"\nSocial tensions:")
        for t in PERIOD_CONTEXT["social_tensions"]:
            print(f"  • {t}")
        print(f"\nTransportation:")
        for t in PERIOD_CONTEXT["transportation"]:
            print(f"  • {t}")

        print(f"\n{'─' * 60}")
        print("ALL REGIONAL ENTITIES")
        print("─" * 60)
        for region, data in REGIONAL_ENTITIES.items():
            print(f"\n{region} ({', '.join(data['states'])})")
            print(f"  Entities: {', '.join(data['entities'])}")
            print(f"  Cults:    {', '.join(data['cults'])}")


# ── Entry point ──────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="CoC Investigator — research a US location for Keeper material"
    )
    parser.add_argument("location", nargs="*", help="City name or zip code")
    parser.add_argument("--occult",    action="store_true", help="Focus on occult/mystery searches")
    parser.add_argument("--crime",     action="store_true", help="Focus on crime/disappearance searches")
    parser.add_argument("--reference", action="store_true", help="Print Mythos reference data and exit")
    parser.add_argument("--region",    help="State abbreviation for regional reference (use with --reference)")
    args = parser.parse_args()

    if args.reference:
        print_reference(args.region)
        return

    if not args.location:
        parser.print_help()
        sys.exit(1)

    location = " ".join(args.location)
    focus = "occult" if args.occult else "crime" if args.crime else "all"
    run_investigation(location, focus)


if __name__ == "__main__":
    main()
