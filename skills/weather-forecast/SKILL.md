---
name: weather-forecast
description: |
  Fetches current weather conditions and today's outlook for any US zip code or
  location name (e.g., "07405", "Kinnelon, NJ", "Butler, New Jersey"). Uses
  Nominatim for geocoding (US locations) and Open-Meteo for weather data — no API
  key required. Reports temperature, humidity, wind, precipitation chance, hourly
  breakdown, and a plain-English summary. Use when asked about current weather,
  today's forecast, or whether to bring an umbrella. For international locations
  or more detailed NWS data, use the /weather skill instead.
license: MIT
compatibility: "Linux/macOS (requires Python 3; no external packages needed)"
metadata:
  author: "Thomas Ott"
  version: "1.0"
---

# Weather Forecast Skill

## Invocation

```
/weather-forecast [zip code or location]
```

Examples:
```
/weather-forecast 07405
/weather-forecast Kinnelon, NJ
/weather-forecast Butler, New Jersey
/weather-forecast New York City
```

## Instructions for the model

### Step 1 — Run the script

```bash
python3 scripts/weather.py <location>
```

Pass the full location string the user provided, quoted if it contains spaces.

### Step 2 — Present the results

Read the script output and present it to the user in a clean, conversational format:

1. **Location and time** — confirm what location was resolved and the local time
2. **Current conditions** — temperature (with feels-like), sky condition, humidity, wind
3. **Today's outlook** — high/low, precipitation chance, any notable weather
4. **12-hour hourly breakdown** — highlight any hours with meaningful rain chance (>20%)
   or significant temperature swings

### Step 3 — Add a one-line bottom line

Always end with a plain-English takeaway, e.g.:
> "Mostly cloudy today with a chance of light rain this afternoon — consider bringing a jacket."
> "Clear and sunny all day, great for being outside."
> "Heavy rain expected between 2–6 PM, winds gusting to 25 mph."

### Step 4 — Weather alerts (if notable)

If the data shows any of the following, call it out clearly:
- Rain probability ≥ 60% → mention umbrella / rain gear
- Max wind gusts ≥ 30 mph → flag wind advisory
- Temperature feels-like ≤ 20°F → flag wind chill
- Temperature ≥ 95°F feels-like → flag heat index
- Thunderstorm weather code (95, 96, 99) → flag storm risk

## Error handling

| Condition | Response |
|---|---|
| Location not found | Ask the user to clarify; try adding the state or country |
| API timeout | Report the error; suggest retrying |
| Ambiguous location | Report which location was resolved; ask to confirm |
