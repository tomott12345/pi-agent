---
name: usgs-water-monitor
description: |
  Queries any USGS stream monitoring station for real-time discharge (flow rate,
  ft³/s) and gage height (ft), then generates a 6-hour forecast using Holt's
  double exponential smoothing on recent 15-minute readings combined with NWS
  precipitation forecasts. Falls back to field-visit data for intermittent
  stations. Labels any unavailable parameter as "data not available." Use when
  asked about current or forecasted river flow, water levels, or stream conditions
  at any USGS monitoring station.
license: MIT
compatibility: "Linux/macOS (requires Python 3; numpy optional but recommended)"
metadata:
  author: "Thomas Ott"
  version: "2.0"
---

# USGS Water Monitor Skill

## Default station

| Field | Value |
|---|---|
| Site ID | 01388500 |
| Name | Pompton River at Pompton Plains NJ |
| Location | Passaic County, New Jersey |
| Drainage area | 355 sq mi |
| Data type | Continuous real-time (15-min intervals) |

Any USGS station ID can be passed as an argument.

## Invocation

```
/usgs-water-monitor                          # default station, current + forecast
/usgs-water-monitor <station_id>             # specific station
/usgs-water-monitor <station_id> --history   # full measurement history
/usgs-water-monitor <station_id> --no-forecast  # skip forecast, current only
```

Examples:
```
/usgs-water-monitor 01388500
/usgs-water-monitor 01382700
/usgs-water-monitor 01388500 --history
```

## Instructions for the model

### Step 1 — Run the query script

```bash
python3 scripts/query.py [station_id] [--history] [--no-forecast]
```

Default station is `01388500` if no ID is given.

### Step 2 — Present current readings

Always report:
- **Station name, ID, and location**
- **Discharge (flow rate)** — value in ft³/s with timestamp, or "data not available"
- **Gage height** — value in ft with timestamp, or "data not available"
- **Data type note** — real-time continuous vs. intermittent field visits
- **Approval status** of each reading

### Step 3 — Present the forecast

After current readings, present the 6-hour forecast table produced by the script.
The table shows hourly values for discharge and gage height, with confidence
intervals. Also include:
- Which forecasting method was used (Holt's smoothing / linear trend)
- Whether NWS precipitation data influenced the forecast
- Any caveats (e.g., forecast based on few data points, intermittent station)

### Step 4 — Add brief context

- Is the current flow high, normal, or low for this stream?
- Is the trend rising, falling, or stable?
- If rain is forecast, flag whether the stream is expected to rise significantly.
- For flood context: if gage height is available, note whether it is approaching
  or above typical bank-full stage.

## Error handling

| Condition | Response |
|---|---|
| Station not found | Report the ID and suggest verifying at waterdata.usgs.gov |
| Parameter not recorded | Label that parameter "data not available" |
| No real-time data, only field visits | Show most recent field measurement; note it may be old |
| NWS weather fetch fails | Produce flow-only forecast without precipitation adjustment |
| Fewer than 6 IV readings available | Use linear trend; note limited forecast confidence |
| Network error | Report the error and suggest checking connectivity |
