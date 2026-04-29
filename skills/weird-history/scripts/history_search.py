#!/usr/bin/env python3
"""
Search for weird or cool historical facts near a zip code or location.
APIs: Nominatim (geocoding) + Wikipedia (geosearch + extracts) — free, no key.
"""

import json
import ssl
import sys
import urllib.parse
import urllib.request

_ctx = ssl._create_unverified_context()
_UA  = "pi-agent-weird-history/1.0"


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


def geocode(location: str) -> tuple[float, float, str]:
    params = urllib.parse.urlencode({
        "q": location, "format": "json", "limit": 1, "countrycodes": "us"
    })
    results = _get(f"https://nominatim.openstreetmap.org/search?{params}")
    if not results:
        params2 = urllib.parse.urlencode({"q": location, "format": "json", "limit": 1})
        results = _get(f"https://nominatim.openstreetmap.org/search?{params2}")
    if not results:
        print(f"Error: Could not geocode '{location}'", file=sys.stderr)
        sys.exit(1)
    r = results[0]
    return float(r["lat"]), float(r["lon"]), r["display_name"]


def nearby_articles(lat: float, lon: float, radius_km: int = 10) -> list[dict]:
    """
    Return up to 50 Wikipedia articles near the coordinates.
    Tries progressively larger radii if few results are found.
    """
    for radius in [radius_km * 1000, 10000]:
        params = urllib.parse.urlencode({
            "action": "query", "list": "geosearch",
            "gscoord": f"{lat}|{lon}",
            "gsradius": min(radius, 10000),
            "gslimit": "50",
            "format": "json",
        })
        data = _get(f"https://en.wikipedia.org/w/api.php?{params}")
        articles = data.get("query", {}).get("geosearch", [])
        if len(articles) >= 5:
            return articles
    return articles


def fetch_extracts(page_ids: list[int]) -> dict[int, dict]:
    """Fetch intro extracts and canonical URLs for a list of page IDs."""
    results = {}
    # Wikipedia API accepts up to 50 titles/ids at once
    chunk_size = 50
    for i in range(0, len(page_ids), chunk_size):
        chunk = page_ids[i : i + chunk_size]
        params = urllib.parse.urlencode({
            "action": "query",
            "prop": "extracts|info|categories",
            "exintro": "1",
            "explaintext": "1",
            "exchars": "1500",
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
        print("Usage: history_search.py <zip code or location>", file=sys.stderr)
        sys.exit(1)

    location = " ".join(sys.argv[1:])
    lat, lon, display = geocode(location)

    # Shorten display name for output
    short = ", ".join(p.strip() for p in display.split(",")[:3])
    print(f"Searching for historical facts near: {short}")
    print(f"Coordinates: {lat:.4f}, {lon:.4f}")
    print(f"Radius: 10 km\n")

    articles = nearby_articles(lat, lon)
    if not articles:
        print("No Wikipedia articles found near this location.")
        sys.exit(0)

    print(f"Found {len(articles)} nearby Wikipedia articles. Fetching content...\n")
    page_ids = [a["pageid"] for a in articles]
    pages    = fetch_extracts(page_ids)

    # Build distance lookup
    dist_map = {a["pageid"]: a["dist"] for a in articles}

    # Output all articles sorted by distance
    for article in sorted(articles, key=lambda a: a["dist"]):
        pid   = article["pageid"]
        page  = pages.get(pid, {})
        title = page.get("title", article["title"])
        url   = page.get("fullurl", f"https://en.wikipedia.org/?curid={pid}")
        dist  = dist_map.get(pid, 0)
        extract = page.get("extract", "").strip()

        if not extract:
            continue

        cats = [c["title"].replace("Category:", "") for c in page.get("categories", [])]

        print(f"{'='*70}")
        print(f"TITLE:    {title}")
        print(f"DISTANCE: {dist:.0f} m from {short.split(',')[0].strip()}")
        print(f"URL:      {url}")
        if cats:
            print(f"TAGS:     {', '.join(cats[:5])}")
        print(f"\n{extract}\n")


if __name__ == "__main__":
    main()
