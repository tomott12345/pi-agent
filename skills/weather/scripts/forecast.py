#!/usr/bin/env python3
"""
Weather forecast — current conditions and day outlook.

Usage:
    python3 forecast.py "Kinnelon, NJ"
    python3 forecast.py 07405
    python3 forecast.py "London, UK"

Data sources:
    Geocoding:  Nominatim (OpenStreetMap)   — no key required
    US weather: NWS (api.weather.gov)       — no key required
    Non-US:     Open-Meteo                  — no key required
"""

import json
import math
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Optional

UA = "pi-agent-weather-skill/1.0 (github.com/tomott12345/pi-agent)"


# ── HTTP helpers ─────────────────────────────────────────────────────────────

def _ctx() -> ssl.SSLContext:
    return ssl._create_unverified_context()


def get_json(url: str, headers: Optional[dict] = None, timeout: int = 20) -> Optional[dict]:
    req = urllib.request.Request(url, headers={**(headers or {}), "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, ssl.SSLError):
            try:
                with urllib.request.urlopen(req, context=_ctx(), timeout=timeout) as r:
                    return json.loads(r.read())
            except Exception:
                return None
        return None
    except Exception:
        return None


# ── Geocoding ─────────────────────────────────────────────────────────────────

def geocode(location: str) -> Optional[dict]:
    """
    Convert a location string (city name or US zip code) to lat/lon.
    Returns dict with keys: lat, lon, display_name, city, state, country_code
    """
    is_zip = location.strip().isdigit() and len(location.strip()) == 5

    params = {
        "q": location,
        "format": "json",
        "limit": "1",
        "addressdetails": "1",
    }
    if is_zip:
        params["countrycodes"] = "us"

    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(params)
    data = get_json(url, headers={"Accept-Language": "en"})

    if not data:
        return None

    r = data[0]
    addr = r.get("address", {})
    return {
        "lat": float(r["lat"]),
        "lon": float(r["lon"]),
        "display_name": r.get("display_name", location),
        "city": addr.get("city") or addr.get("town") or addr.get("village") or addr.get("county", ""),
        "state": addr.get("state", ""),
        "postcode": addr.get("postcode", ""),
        "country_code": addr.get("country_code", "").lower(),
    }


def format_location(geo: dict) -> str:
    parts = [geo["city"]]
    if geo["state"]:
        parts.append(geo["state"])
    if geo["country_code"] not in ("us", ""):
        parts.append(geo["country_code"].upper())
    label = ", ".join(p for p in parts if p)
    if geo["postcode"]:
        label += f"  ({geo['postcode']})"
    return label


# ── Unit conversions ──────────────────────────────────────────────────────────

def c_to_f(c) -> Optional[float]:
    return round(c * 9 / 5 + 32, 1) if c is not None else None


def ms_to_mph(ms) -> Optional[float]:
    return round(ms * 2.237, 1) if ms is not None else None


def pa_to_inhg(pa) -> Optional[float]:
    return round(pa / 3386.39, 2) if pa is not None else None


def m_to_miles(m) -> Optional[float]:
    return round(m / 1609.34, 1) if m is not None else None


def degrees_to_cardinal(deg) -> str:
    if deg is None:
        return "—"
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    return dirs[round(deg / 22.5) % 16]


def feels_like_f(temp_f: float, humidity: float, wind_mph: float) -> float:
    """Return heat index or wind chill as appropriate, or actual temp."""
    if temp_f >= 80 and humidity >= 40:
        # Rothfusz heat index
        hi = (-42.379 + 2.04901523 * temp_f + 10.14333127 * humidity
              - 0.22475541 * temp_f * humidity - 0.00683783 * temp_f ** 2
              - 0.05481717 * humidity ** 2 + 0.00122874 * temp_f ** 2 * humidity
              + 0.00085282 * temp_f * humidity ** 2
              - 0.00000199 * temp_f ** 2 * humidity ** 2)
        return round(hi, 1)
    elif temp_f <= 50 and wind_mph >= 3:
        # NWS wind chill
        wc = (35.74 + 0.6215 * temp_f - 35.75 * wind_mph ** 0.16
              + 0.4275 * temp_f * wind_mph ** 0.16)
        return round(wc, 1)
    return temp_f


# ── NWS (US) ──────────────────────────────────────────────────────────────────

NWS_HDR = {"Accept": "application/geo+json"}


def nws_get_grid(lat: float, lon: float) -> Optional[dict]:
    data = get_json(f"https://api.weather.gov/points/{lat:.4f},{lon:.4f}", NWS_HDR)
    if not data:
        return None
    return data.get("properties")


def nws_current(grid: dict) -> Optional[dict]:
    stations = get_json(grid["observationStations"], NWS_HDR)
    if not stations or not stations.get("features"):
        return None
    sid = stations["features"][0]["properties"]["stationIdentifier"]
    obs = get_json(f"https://api.weather.gov/stations/{sid}/observations/latest", NWS_HDR)
    if not obs:
        return None
    return obs.get("properties")


def nws_forecast(grid: dict) -> tuple[Optional[list], Optional[list]]:
    daily_data = get_json(grid["forecast"], NWS_HDR, timeout=30)
    hourly_data = get_json(grid["forecastHourly"], NWS_HDR, timeout=30)
    daily = daily_data["properties"]["periods"] if daily_data else None
    hourly = hourly_data["properties"]["periods"] if hourly_data else None
    return daily, hourly


# ── Open-Meteo (non-US fallback) ──────────────────────────────────────────────

WMO_CODES = {
    0: "Clear Sky", 1: "Mainly Clear", 2: "Partly Cloudy", 3: "Overcast",
    45: "Foggy", 48: "Icy Fog",
    51: "Light Drizzle", 53: "Moderate Drizzle", 55: "Dense Drizzle",
    61: "Slight Rain", 63: "Moderate Rain", 65: "Heavy Rain",
    71: "Slight Snow", 73: "Moderate Snow", 75: "Heavy Snow", 77: "Snow Grains",
    80: "Rain Showers", 81: "Moderate Showers", 82: "Violent Showers",
    85: "Snow Showers", 86: "Heavy Snow Showers",
    95: "Thunderstorm", 96: "Thunderstorm w/ Hail", 99: "Thunderstorm w/ Heavy Hail",
}


def open_meteo(lat: float, lon: float) -> Optional[dict]:
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
        "weather_code,wind_speed_10m,wind_direction_10m,surface_pressure"
        "&hourly=temperature_2m,precipitation_probability,weather_code,wind_speed_10m"
        "&daily=weather_code,temperature_2m_max,temperature_2m_min,"
        "precipitation_probability_max,wind_speed_10m_max"
        "&temperature_unit=fahrenheit&wind_speed_unit=mph&precipitation_unit=inch"
        "&timezone=auto&forecast_days=1"
    )
    return get_json(url, timeout=20)


# ── Formatting ────────────────────────────────────────────────────────────────

BAR = "─"
HDR = "━"

def section(title: str, width: int = 58) -> str:
    return f"\n{HDR * 3} {title} {HDR * (width - len(title) - 5)}"


def fmt_temp_f(f_val, show_c: bool = True) -> str:
    if f_val is None:
        return "N/A"
    c_val = round((f_val - 32) * 5 / 9)
    return f"{f_val:.0f}°F ({c_val}°C)" if show_c else f"{f_val:.0f}°F"


def fmt_temp_c(c_val, show_f: bool = True) -> str:
    if c_val is None:
        return "N/A"
    f_val = round(c_val * 9 / 5 + 32)
    return f"{f_val}°F ({c_val:.0f}°C)" if show_f else f"{c_val:.0f}°C"


def row(label: str, value: str, indent: int = 2) -> str:
    return f"{' ' * indent}{label:<18}{value}"


# ── NWS report ────────────────────────────────────────────────────────────────

def print_nws_report(location_label: str, obs, daily, hourly) -> None:
    now = datetime.now().astimezone()
    print(f"\nWeather for {location_label}")
    print(f"Source: National Weather Service  |  {now.strftime('%A, %B %-d, %Y  %-I:%M %p %Z')}")

    # Current conditions
    print(section("Current Conditions"))
    if obs:
        temp_c = obs.get("temperature", {}).get("value")
        temp_f = c_to_f(temp_c)
        dew_c  = obs.get("dewpoint", {}).get("value")
        hum    = obs.get("relativeHumidity", {}).get("value")
        wind_d = obs.get("windDirection", {}).get("value")
        wind_s = obs.get("windSpeed", {}).get("value")
        wind_mph = ms_to_mph(wind_s) or 0
        vis_m  = obs.get("visibility", {}).get("value")
        pres   = obs.get("seaLevelPressure", {}).get("value")
        desc   = obs.get("textDescription") or "—"
        ts     = obs.get("timestamp", "")

        # Feels like — prefer NWS heat index / wind chill if available
        hi_c = obs.get("heatIndex", {}).get("value")
        wc_c = obs.get("windChill", {}).get("value")
        if hi_c is not None:
            fl_f = c_to_f(hi_c)
        elif wc_c is not None:
            fl_f = c_to_f(wc_c)
        elif temp_f is not None and hum is not None:
            fl_f = feels_like_f(temp_f, hum, wind_mph)
        else:
            fl_f = temp_f

        wind_str = (f"{degrees_to_cardinal(wind_d)} {wind_mph:.0f} mph"
                    if wind_mph > 0 else "Calm")
        try:
            obs_time = datetime.fromisoformat(ts).astimezone().strftime("%-I:%M %p %Z")
        except Exception:
            obs_time = ts

        print(row("Temperature:", fmt_temp_f(temp_f)))
        print(row("Feels Like:", fmt_temp_f(fl_f)))
        if hum is not None:
            print(row("Humidity:", f"{hum:.0f}%"))
        print(row("Wind:", wind_str))
        print(row("Conditions:", desc))
        if dew_c is not None:
            print(row("Dewpoint:", fmt_temp_f(c_to_f(dew_c))))
        if vis_m is not None:
            print(row("Visibility:", f"{m_to_miles(vis_m)} mi"))
        if pres is not None:
            print(row("Pressure:", f"{pa_to_inhg(pres)} inHg"))
        print(row("Observed:", obs_time))
    else:
        print("  Current observations unavailable.")

    # Today's forecast
    print(section("Today's Forecast"))
    if daily:
        today   = daily[0]
        tonight = daily[1] if len(daily) > 1 else None
        precip_day   = (today.get("probabilityOfPrecipitation") or {}).get("value") or 0
        precip_night = ((tonight.get("probabilityOfPrecipitation") or {}).get("value") or 0
                        if tonight else 0)
        high = today["temperature"] if today.get("isDaytime") else None
        low  = tonight["temperature"] if tonight else None

        if high:
            print(row("High:", fmt_temp_f(high)))
        if low:
            print(row("Tonight Low:", fmt_temp_f(low)))
        print(row("Rain Chance:", f"{precip_day:.0f}% (day) / {precip_night:.0f}% (tonight)"))
        print(row("Summary:", today.get("detailedForecast", today.get("shortForecast", "—"))))
    else:
        print("  Forecast unavailable.")

    # Hourly outlook — remaining hours today (up to 12)
    print(section("Hourly Outlook"))
    if hourly:
        now_hour = datetime.now().astimezone()
        periods = [
            p for p in hourly
            if datetime.fromisoformat(p["startTime"]).astimezone() >= now_hour
        ][:12]

        print(f"  {'Time':<8}{'Temp':<8}{'Rain%':<7}{'Wind':<14}Conditions")
        print(f"  {BAR * 52}")
        for p in periods:
            t = datetime.fromisoformat(p["startTime"]).astimezone()
            time_str = t.strftime("%-I %p")
            temp_str = f"{p['temperature']}°F"
            precip   = (p.get("probabilityOfPrecipitation") or {}).get("value") or 0
            wind     = p.get("windSpeed", "—")
            cond     = p.get("shortForecast", "—")
            print(f"  {time_str:<8}{temp_str:<8}{precip:<7.0f}{wind:<14}{cond}")
    else:
        print("  Hourly data unavailable.")

    print()


# ── Open-Meteo report ─────────────────────────────────────────────────────────

def print_meteo_report(location_label: str, data: dict) -> None:
    now = datetime.now().astimezone()
    print(f"\nWeather for {location_label}")
    print(f"Source: Open-Meteo  |  {now.strftime('%A, %B %-d, %Y  %-I:%M %p %Z')}")

    cur = data.get("current", {})
    daily = data.get("daily", {})
    hourly = data.get("hourly", {})

    # Current
    print(section("Current Conditions"))
    temp_f  = cur.get("temperature_2m")
    fl_f    = cur.get("apparent_temperature")
    hum     = cur.get("relative_humidity_2m")
    wcode   = cur.get("weather_code")
    wind_s  = cur.get("wind_speed_10m")
    wind_d  = cur.get("wind_direction_10m")
    pres    = cur.get("surface_pressure")

    print(row("Temperature:", fmt_temp_f(temp_f)))
    print(row("Feels Like:", fmt_temp_f(fl_f)))
    if hum is not None:
        print(row("Humidity:", f"{hum}%"))
    wind_str = (f"{degrees_to_cardinal(wind_d)} {wind_s:.0f} mph"
                if wind_s and wind_s > 0 else "Calm")
    print(row("Wind:", wind_str))
    print(row("Conditions:", WMO_CODES.get(wcode, f"Code {wcode}")))
    if pres:
        inhg = round(pres * 0.02953, 2)
        print(row("Pressure:", f"{inhg} inHg"))

    # Today
    print(section("Today's Forecast"))
    high_f  = (daily.get("temperature_2m_max") or [None])[0]
    low_f   = (daily.get("temperature_2m_min") or [None])[0]
    precip  = (daily.get("precipitation_probability_max") or [None])[0]
    d_code  = (daily.get("weather_code") or [None])[0]

    if high_f: print(row("High:", fmt_temp_f(high_f)))
    if low_f:  print(row("Low:", fmt_temp_f(low_f)))
    if precip is not None: print(row("Rain Chance:", f"{precip}%"))
    if d_code is not None: print(row("Summary:", WMO_CODES.get(d_code, "—")))

    # Hourly
    print(section("Hourly Outlook"))
    times  = hourly.get("time", [])
    temps  = hourly.get("temperature_2m", [])
    precips = hourly.get("precipitation_probability", [])
    winds  = hourly.get("wind_speed_10m", [])
    wcodes = hourly.get("weather_code", [])

    now_ts = datetime.now(timezone.utc).astimezone()
    print(f"  {'Time':<8}{'Temp':<8}{'Rain%':<7}{'Wind':<10}Conditions")
    print(f"  {BAR * 50}")
    shown = 0
    for i, t_str in enumerate(times):
        t = datetime.fromisoformat(t_str).astimezone() if "+" in t_str or "T" in t_str else \
            datetime.strptime(t_str, "%Y-%m-%dT%H:%M").replace(tzinfo=timezone.utc).astimezone()
        if t < now_ts:
            continue
        time_label = t.strftime("%-I %p")
        temp_s = f"{temps[i]:.0f}°F" if i < len(temps) else "—"
        pr = precips[i] if i < len(precips) else 0
        ws = f"{winds[i]:.0f} mph" if i < len(winds) else "—"
        cond = WMO_CODES.get(wcodes[i] if i < len(wcodes) else None, "—")
        print(f"  {time_label:<8}{temp_s:<8}{pr:<7}{ws:<10}{cond}")
        shown += 1
        if shown >= 12:
            break

    print()


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: forecast.py <zip code or location>")
        print('  e.g. forecast.py "Kinnelon, NJ"')
        print("  e.g. forecast.py 07405")
        sys.exit(1)

    location = " ".join(sys.argv[1:])

    # Geocode
    geo = geocode(location)
    if not geo:
        print(f"Error: Could not find location '{location}'.", file=sys.stderr)
        print("Check the spelling or try a nearby city name.", file=sys.stderr)
        sys.exit(1)

    label = format_location(geo)
    lat, lon = geo["lat"], geo["lon"]

    # US: NWS
    if geo["country_code"] == "us":
        grid = nws_get_grid(lat, lon)
        if grid:
            obs          = nws_current(grid)
            daily, hourly = nws_forecast(grid)
            print_nws_report(label, obs, daily, hourly)
            return

    # Non-US or NWS failure: Open-Meteo
    data = open_meteo(lat, lon)
    if data:
        print_meteo_report(label, data)
    else:
        print("Error: Could not retrieve weather data.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
