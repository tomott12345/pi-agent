#!/usr/bin/env python3
"""
Fetch current conditions and today's forecast for any zip code or location.
APIs used: Nominatim (geocoding) + Open-Meteo (weather) — both free, no key required.
"""

import json
import ssl
import sys
import urllib.parse
import urllib.request
from datetime import datetime

# ── SSL context (handles macOS cert issues) ──────────────────────────────────
_ctx = ssl._create_unverified_context()


def _get(url: str, headers: dict | None = None) -> dict:
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, ssl.SSLError):
            with urllib.request.urlopen(req, timeout=15, context=_ctx) as r:
                return json.loads(r.read())
        raise


# ── WMO weather code descriptions ────────────────────────────────────────────
WMO = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Icy fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Heavy drizzle",
    56: "Light freezing drizzle", 57: "Heavy freezing drizzle",
    61: "Light rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Light freezing rain", 67: "Heavy freezing rain",
    71: "Light snow", 73: "Moderate snow", 75: "Heavy snow", 77: "Snow grains",
    80: "Light rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Light snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail",
}

WIND_DIRS = ["N","NNE","NE","ENE","E","ESE","SE","SSE",
             "S","SSW","SW","WSW","W","WNW","NW","NNW"]


def wind_dir(degrees: float) -> str:
    return WIND_DIRS[round(degrees / 22.5) % 16]


def geocode(location: str) -> tuple[float, float, str]:
    """Return (lat, lon, display_name) for a location string or zip code."""
    params = urllib.parse.urlencode({
        "q": location, "format": "json", "limit": 1, "countrycodes": "us"
    })
    results = _get(
        f"https://nominatim.openstreetmap.org/search?{params}",
        headers={"User-Agent": "pi-agent-weather/1.0"}
    )
    if not results:
        # Retry without country restriction
        params2 = urllib.parse.urlencode({"q": location, "format": "json", "limit": 1})
        results = _get(
            f"https://nominatim.openstreetmap.org/search?{params2}",
            headers={"User-Agent": "pi-agent-weather/1.0"}
        )
    if not results:
        print(f"Error: Could not geocode '{location}'", file=sys.stderr)
        sys.exit(1)
    r = results[0]
    return float(r["lat"]), float(r["lon"]), r["display_name"]


def fetch_weather(lat: float, lon: float) -> dict:
    params = urllib.parse.urlencode({
        "latitude": lat,
        "longitude": lon,
        "current": ",".join([
            "temperature_2m", "apparent_temperature", "relative_humidity_2m",
            "weather_code", "wind_speed_10m", "wind_direction_10m",
            "wind_gusts_10m", "precipitation", "cloud_cover",
        ]),
        "hourly": ",".join([
            "temperature_2m", "precipitation_probability", "weather_code",
            "wind_speed_10m",
        ]),
        "daily": ",".join([
            "weather_code", "temperature_2m_max", "temperature_2m_min",
            "apparent_temperature_max", "apparent_temperature_min",
            "precipitation_sum", "precipitation_probability_max",
            "wind_speed_10m_max", "wind_gusts_10m_max", "sunrise", "sunset",
        ]),
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "timezone": "auto",
        "forecast_days": "1",
        "forecast_hours": "12",
    })
    return _get(f"https://api.open-meteo.com/v1/forecast?{params}")


def format_report(location_name: str, w: dict) -> str:
    c = w["current"]
    d = w["daily"]
    h = w["hourly"]

    now_str = datetime.fromisoformat(c["time"]).strftime("%A, %b %d  %I:%M %p")
    condition = WMO.get(c["weather_code"], f"Code {c['weather_code']}")
    sunrise = datetime.fromisoformat(d["sunrise"][0]).strftime("%I:%M %p")
    sunset  = datetime.fromisoformat(d["sunset"][0]).strftime("%I:%M %p")

    lines = [
        f"Weather for {location_name.split(',')[0].strip()}",
        f"  ({', '.join(location_name.split(',')[1:3]).strip()})",
        f"  {now_str}",
        "",
        "── CURRENT CONDITIONS ──────────────────────────────",
        f"  Conditions:   {condition}",
        f"  Temperature:  {c['temperature_2m']:.0f}°F  (feels like {c['apparent_temperature']:.0f}°F)",
        f"  Humidity:     {c['relative_humidity_2m']}%",
        f"  Wind:         {c['wind_speed_10m']:.0f} mph {wind_dir(c['wind_direction_10m'])}",
    ]
    if c.get("wind_gusts_10m", 0) > c["wind_speed_10m"] + 5:
        lines.append(f"  Gusts:        {c['wind_gusts_10m']:.0f} mph")
    if c.get("precipitation", 0) > 0:
        lines.append(f"  Precip (1hr): {c['precipitation']:.2f}\"")

    lines += [
        "",
        "── TODAY'S OUTLOOK ─────────────────────────────────",
        f"  High / Low:   {d['temperature_2m_max'][0]:.0f}°F / {d['temperature_2m_min'][0]:.0f}°F",
        f"  Feels like:   {d['apparent_temperature_max'][0]:.0f}°F – {d['apparent_temperature_min'][0]:.0f}°F",
        f"  Conditions:   {WMO.get(d['weather_code'][0], '')}",
        f"  Rain chance:  {d['precipitation_probability_max'][0]}%",
    ]
    if d["precipitation_sum"][0] > 0:
        lines.append(f"  Precip total: {d['precipitation_sum'][0]:.2f}\"")
    lines += [
        f"  Max wind:     {d['wind_speed_10m_max'][0]:.0f} mph"
        + (f"  (gusts {d['wind_gusts_10m_max'][0]:.0f} mph)" if d.get("wind_gusts_10m_max") else ""),
        f"  Sunrise:      {sunrise}",
        f"  Sunset:       {sunset}",
    ]

    # Hourly snapshot for next 12 hours
    times  = h.get("time", [])
    temps  = h.get("temperature_2m", [])
    probs  = h.get("precipitation_probability", [])
    codes  = h.get("weather_code", [])

    if times:
        lines += ["", "── NEXT 12 HOURS ───────────────────────────────────",
                  f"  {'Hour':<8} {'Temp':>6} {'Rain%':>7}  Conditions"]
        now_dt = datetime.fromisoformat(c["time"])
        for i, t in enumerate(times):
            slot = datetime.fromisoformat(t)
            if slot <= now_dt:
                continue
            hr  = slot.strftime("%I %p").lstrip("0")
            tmp = f"{temps[i]:.0f}°F" if i < len(temps) else "—"
            pct = f"{probs[i]}%" if i < len(probs) else "—"
            cond = WMO.get(codes[i], "") if i < len(codes) else ""
            lines.append(f"  {hr:<8} {tmp:>6} {pct:>7}  {cond}")

    return "\n".join(lines)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: weather.py <zip code or location>", file=sys.stderr)
        sys.exit(1)

    location = " ".join(sys.argv[1:])
    lat, lon, display = geocode(location)
    w = fetch_weather(lat, lon)
    print(format_report(display, w))


if __name__ == "__main__":
    main()
