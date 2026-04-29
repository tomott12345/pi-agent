#!/usr/bin/env python3
"""
USGS water monitor — real-time readings + 6-hour forecast.

Fetches discharge (00060) and gage height (00065) for any USGS station,
then forecasts 6 hours ahead using Holt's double exponential smoothing
combined with NWS precipitation data.
"""

import argparse
import json
import math
import ssl
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Optional

DEFAULT_SITE = "01388500"
USGS_IV_URL = "https://waterservices.usgs.gov/nwis/iv/"
USGS_FM_URL = "https://api.waterdata.usgs.gov/ogcapi/v0/collections/field-measurements/items"
USGS_SITE_URL = "https://api.waterdata.usgs.gov/ogcapi/v0/collections/monitoring-locations/items"
NWS_POINTS_URL = "https://api.weather.gov/points"

PARAMETERS = {
    "00060": ("Discharge (Flow Rate)", "ft³/s"),
    "00065": ("Gage Height", "ft"),
}


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _ssl_ctx() -> ssl.SSLContext:
    return ssl._create_unverified_context()


def fetch_json(url: str, fallback_ssl: bool = True) -> Optional[dict]:
    """Fetch JSON from url; returns None on any error."""
    def _get(ctx=None):
        kwargs = {"timeout": 15}
        if ctx:
            kwargs["context"] = ctx
        with urllib.request.urlopen(url, **kwargs) as r:
            return json.loads(r.read())

    try:
        return _get()
    except urllib.error.URLError as exc:
        if fallback_ssl and isinstance(exc.reason, ssl.SSLError):
            try:
                return _get(ctx=_ssl_ctx())
            except Exception:
                return None
        return None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Station metadata
# ---------------------------------------------------------------------------

def get_station_info(site_id: str) -> dict:
    url = f"{USGS_SITE_URL}/USGS-{site_id}?f=json"
    data = fetch_json(url)
    if not data:
        return {"name": "Unknown", "lat": None, "lon": None, "drainage_area": None}
    props = data.get("properties", {})
    coords = (data.get("geometry") or {}).get("coordinates", [None, None])
    return {
        "name": props.get("monitoring_location_name", "Unknown"),
        "state": props.get("state_name", ""),
        "county": props.get("county_name", ""),
        "lat": coords[1],
        "lon": coords[0],
        "drainage_area": props.get("drainage_area"),
    }


# ---------------------------------------------------------------------------
# USGS data fetchers
# ---------------------------------------------------------------------------

def fetch_iv(site_id: str, period: str = "P2D") -> dict[str, list[dict]]:
    """Fetch instantaneous values for the last `period`. Returns {param_code: [values]}."""
    url = (
        f"{USGS_IV_URL}?sites={site_id}"
        f"&parameterCd=00060,00065"
        f"&period={period}"
        f"&format=json"
    )
    data = fetch_json(url)
    if not data:
        return {}
    result: dict[str, list[dict]] = {}
    for series in data.get("value", {}).get("timeSeries", []):
        code = series["variable"]["variableCode"][0]["value"]
        vals = series.get("values", [{}])[0].get("value", [])
        result[code] = [v for v in vals if v.get("value") not in (None, "", "Ice")]
    return result


def fetch_field_measurements(site_id: str) -> dict[str, list[dict]]:
    """Fetch field visit measurements (for intermittent stations)."""
    url = (
        f"{USGS_FM_URL}"
        f"?monitoring_location_id=USGS-{site_id}"
        f"&f=json&sortby=-time&limit=100"
    )
    data = fetch_json(url)
    if not data:
        return {}
    result: dict[str, list[dict]] = {}
    for feat in data.get("features", []):
        p = feat["properties"]
        code = p.get("parameter_code", "")
        if code in PARAMETERS:
            result.setdefault(code, []).append(p)
    return result


# ---------------------------------------------------------------------------
# NWS weather
# ---------------------------------------------------------------------------

def fetch_nws_hourly(lat: float, lon: float) -> list[dict]:
    """Return list of hourly NWS forecast periods for the next 6+ hours."""
    if lat is None or lon is None:
        return []
    points = fetch_json(f"{NWS_POINTS_URL}/{lat:.4f},{lon:.4f}")
    if not points:
        return []
    hourly_url = points.get("properties", {}).get("forecastHourly")
    if not hourly_url:
        return []
    forecast = fetch_json(hourly_url)
    if not forecast:
        return []
    return forecast.get("properties", {}).get("periods", [])[:8]  # next 8 hours


def extract_precip_forecast(periods: list[dict]) -> list[float]:
    """Return mm of expected precipitation per hour for the next 6 hours."""
    result = []
    for p in periods[:6]:
        qpf = p.get("quantitativePrecipitation", {})
        if qpf:
            val = qpf.get("value")
            unit = qpf.get("unitCode", "")
            if val is not None:
                mm = float(val) * 25.4 if "wmoUnit:in" in unit else float(val)
                result.append(mm)
                continue
        # Fall back to probability heuristic (rough)
        prob = p.get("probabilityOfPrecipitation", {}).get("value") or 0
        result.append(max(0.0, (float(prob) / 100) * 1.5))
    while len(result) < 6:
        result.append(0.0)
    return result[:6]


# ---------------------------------------------------------------------------
# Forecasting — Holt's double exponential smoothing
# ---------------------------------------------------------------------------

def parse_floats(vals: list[dict]) -> list[float]:
    out = []
    for v in vals:
        try:
            out.append(float(v.get("value") or v.get("Value", "")))
        except (ValueError, TypeError):
            pass
    return out


def holt_smooth(series: list[float], alpha: float = 0.3, beta: float = 0.1) -> tuple[float, float]:
    """
    Holt's double exponential smoothing.
    Returns (level, trend) after processing the series.
    """
    if len(series) < 2:
        return series[-1] if series else 0.0, 0.0
    level = series[0]
    trend = series[1] - series[0]
    for y in series[1:]:
        prev_level = level
        level = alpha * y + (1 - alpha) * (level + trend)
        trend = beta * (level - prev_level) + (1 - beta) * trend
    return level, trend


def forecast_flow(
    iv_vals: list[dict],
    precip_mm: list[float],
    drainage_area_sqmi: Optional[float],
    hours: int = 6,
) -> list[Optional[float]]:
    """
    Forecast hourly discharge for `hours` ahead.

    Method:
      1. Subsample IV data to hourly means (15-min data → 1-hr means).
      2. Apply Holt's double exponential smoothing to get level + trend.
      3. Project forward, applying a precipitation-runoff adjustment.
    """
    flows = parse_floats(iv_vals)
    if not flows:
        return [None] * hours

    # Subsample to ~hourly means (every 4 readings at 15-min intervals)
    step = max(1, len(flows) // max(len(flows) // 4, 1))
    hourly = [
        sum(flows[i: i + step]) / len(flows[i: i + step])
        for i in range(0, len(flows), step)
    ]
    if not hourly:
        return [None] * hours

    level, trend = holt_smooth(hourly[-48:] if len(hourly) > 48 else hourly)

    # Precipitation adjustment: approximate runoff contribution
    # Rational method approximation: Q_add ≈ C * i * A / 360  (ft³/s)
    # C (runoff coefficient for mixed watershed) ≈ 0.35
    # A in acres = drainage_area_sqmi * 640
    C = 0.35
    area_acres = (drainage_area_sqmi or 100.0) * 640

    forecast = []
    for h in range(1, hours + 1):
        base = max(0.0, level + trend * h)
        # Runoff lag: precipitation effects typically appear 1-3 hours later
        precip_idx = max(0, h - 2)
        precip_intensity_in_hr = precip_mm[precip_idx] / 25.4 if precip_idx < len(precip_mm) else 0.0
        q_precip = C * precip_intensity_in_hr * area_acres / 360
        forecast.append(base + q_precip)
    return forecast


def forecast_stage(
    flow_series: list[dict],
    stage_series: list[dict],
    forecast_flows: list[Optional[float]],
) -> list[Optional[float]]:
    """
    Forecast gage height from forecast flows using a power-law rating curve
    fitted to recent paired observations: stage = a * flow ^ b
    """
    flows = parse_floats(flow_series)
    stages = parse_floats(stage_series)

    # Use the minimum overlapping length of paired observations
    n = min(len(flows), len(stages))
    if n < 3:
        # Not enough data for curve fitting — return None
        return [None] * len(forecast_flows)

    # Log-space linear regression: ln(stage) = ln(a) + b * ln(flow)
    log_flows = [math.log(max(f, 0.01)) for f in flows[-n:]]
    log_stages = [math.log(max(s, 0.01)) for s in stages[-n:]]

    mean_lf = sum(log_flows) / n
    mean_ls = sum(log_stages) / n
    denom = sum((lf - mean_lf) ** 2 for lf in log_flows)
    if denom == 0:
        return [None] * len(forecast_flows)
    b = sum((lf - mean_lf) * (ls - mean_ls) for lf, ls in zip(log_flows, log_stages)) / denom
    a = math.exp(mean_ls - b * mean_lf)

    result = []
    for q in forecast_flows:
        if q is None or q <= 0:
            result.append(None)
        else:
            result.append(round(a * (q ** b), 2))
    return result


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def fmt_ts(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso.replace(".000", ""))
        return dt.astimezone().strftime("%Y-%m-%d %H:%M %Z")
    except Exception:
        return iso


def age_note(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso.replace(".000", ""))
        delta = datetime.now(timezone.utc) - dt.astimezone(timezone.utc)
        days = delta.days
        mins = int(delta.total_seconds() / 60)
        if mins < 60:
            return f"({mins} min ago)"
        elif mins < 1440:
            return f"({mins // 60}h {mins % 60}m ago)"
        elif days < 30:
            return f"({days} days ago)"
        elif days < 365:
            return f"(~{days // 30} months ago)"
        else:
            return f"(~{days // 365} years ago)"
    except Exception:
        return ""


def na(value) -> str:
    return "data not available" if value is None else str(value)


# ---------------------------------------------------------------------------
# Output modes
# ---------------------------------------------------------------------------

def print_current(site_id: str, info: dict, iv: dict, fm: dict) -> None:
    print(f"USGS Station {site_id} — {info['name']}")
    if info.get("county") or info.get("state"):
        print(f"Location: {info.get('county', '')}, {info.get('state', '')}".strip(", "))
    if info.get("drainage_area"):
        print(f"Drainage area: {info['drainage_area']} sq mi")
    print()

    for code, (label, unit) in PARAMETERS.items():
        vals = iv.get(code) or []
        fm_vals = fm.get(code) or []
        latest_iv = vals[-1] if vals else None
        latest_fm = fm_vals[0] if fm_vals else None

        print(f"{label}")
        if latest_iv:
            ts = fmt_ts(latest_iv["dateTime"])
            age = age_note(latest_iv["dateTime"])
            quals = latest_iv.get("qualifiers", [])
            qual_str = f"  Qualifiers: {', '.join(quals)}" if quals else ""
            print(f"  Value:    {latest_iv['value']} {unit}")
            print(f"  Time:     {ts} {age}")
            print(f"  Source:   Real-time (15-min sensor){qual_str}")
        elif latest_fm:
            ts = fmt_ts(latest_fm["time"])
            age = age_note(latest_fm["time"])
            print(f"  Value:    {latest_fm['value']} {latest_fm.get('unit_of_measure', unit)}")
            print(f"  Time:     {ts} {age}")
            print(f"  Source:   Field visit measurement (intermittent station)")
        else:
            print(f"  Value:    data not available")
        print()


def print_forecast(
    site_id: str,
    info: dict,
    iv: dict,
    precip_mm: list[float],
    nws_available: bool,
) -> None:
    flow_vals = iv.get("00060", [])
    stage_vals = iv.get("00065", [])

    forecast_flows = forecast_flow(
        flow_vals,
        precip_mm,
        info.get("drainage_area"),
    )

    forecast_stages = forecast_stage(flow_vals, stage_vals, forecast_flows)

    now = datetime.now().astimezone()
    has_flow = any(f is not None for f in forecast_flows)
    has_stage = any(s is not None for s in forecast_stages)

    print("--- 6-Hour Forecast ---")
    print(f"Method: Holt's double exponential smoothing on recent 15-min readings")
    if nws_available:
        total_precip = sum(precip_mm)
        print(f"Weather: NWS hourly forecast incorporated (expected precip: {total_precip:.1f} mm over 6h)")
    else:
        print("Weather: NWS forecast unavailable — trend-only projection")
    if len(flow_vals) < 12:
        print("Note: limited sensor history; forecast confidence is low")
    print()

    col_w = [10, 20, 20, 14]
    header = (
        f"{'Hour':<{col_w[0]}}"
        f"{'Time':<{col_w[1]}}"
        f"{'Discharge (ft³/s)':<{col_w[2]}}"
        f"{'Gage Ht (ft)':<{col_w[3]}}"
    )
    print(header)
    print("-" * sum(col_w))

    for h in range(1, 7):
        t = now + timedelta(hours=h)
        t_str = t.strftime("%H:%M %Z")
        flow = forecast_flows[h - 1]
        stage = forecast_stages[h - 1]
        flow_str = f"{flow:.1f}" if flow is not None else "data not available"
        stage_str = f"{stage:.2f}" if stage is not None else "data not available"
        print(
            f"{f'+{h}h':<{col_w[0]}}"
            f"{t_str:<{col_w[1]}}"
            f"{flow_str:<{col_w[2]}}"
            f"{stage_str:<{col_w[3]}}"
        )
    print()


def print_history(site_id: str, info: dict, iv: dict, fm: dict) -> None:
    print(f"USGS Station {site_id} — {info['name']}")
    print()

    # Recent IV readings (last 48h, up to 20 shown)
    for code, (label, unit) in PARAMETERS.items():
        iv_vals = iv.get(code, [])
        fm_vals = fm.get(code, [])
        all_vals = []
        for v in iv_vals[-20:]:
            all_vals.append((fmt_ts(v["dateTime"]), v["value"], unit, "Real-time"))
        for v in fm_vals[:10]:
            all_vals.append((fmt_ts(v["time"]), v["value"],
                             v.get("unit_of_measure", unit), "Field visit"))

        print(f"--- {label} ---")
        if not all_vals:
            print("  data not available\n")
            continue
        print(f"{'Date/Time':<22} {'Value':<10} {'Unit':<10} {'Source'}")
        print("-" * 58)
        for ts, val, u, src in all_vals:
            print(f"{ts:<22} {val:<10} {u:<10} {src}")
        print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="USGS water monitor — real-time readings + 6-hour forecast"
    )
    parser.add_argument(
        "station",
        nargs="?",
        default=DEFAULT_SITE,
        help=f"USGS site number (default: {DEFAULT_SITE})",
    )
    parser.add_argument(
        "--history",
        action="store_true",
        help="Show measurement history instead of current + forecast",
    )
    parser.add_argument(
        "--no-forecast",
        dest="no_forecast",
        action="store_true",
        help="Show current readings only, skip forecast",
    )
    args = parser.parse_args()

    site_id = args.station.lstrip("0") and args.station  # keep leading zeros

    # Fetch station metadata
    info = get_station_info(site_id)
    if info["name"] == "Unknown":
        print(f"Error: Station {site_id} not found.", file=sys.stderr)
        print("Verify the site number at https://waterdata.usgs.gov", file=sys.stderr)
        sys.exit(1)

    # Fetch IV data (last 48h for forecasting, 2-day period)
    iv = fetch_iv(site_id, period="P2D")

    # If no IV data, try field measurements (intermittent stations)
    fm: dict[str, list] = {}
    if not iv:
        fm = fetch_field_measurements(site_id)

    if args.history:
        # For history, fetch longer IV window
        iv_long = fetch_iv(site_id, period="P7D")
        print_history(site_id, info, iv_long or iv, fm)
        return

    print_current(site_id, info, iv, fm)

    if not args.no_forecast:
        # Only produce forecast when real-time data is available
        if iv:
            lat, lon = info.get("lat"), info.get("lon")
            nws_periods = fetch_nws_hourly(lat, lon) if lat and lon else []
            precip_mm = extract_precip_forecast(nws_periods) if nws_periods else [0.0] * 6
            nws_available = bool(nws_periods)
            print_forecast(site_id, info, iv, precip_mm, nws_available)
        else:
            print("Forecast not available: no real-time sensor data for this station.")
            if fm:
                print("This appears to be an intermittent field-visit station.")
            print()


if __name__ == "__main__":
    main()
