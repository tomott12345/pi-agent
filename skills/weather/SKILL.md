---
name: weather
description: |
  Provides current weather conditions and the day's forecast for any US zip
  code or location name (e.g. "Kinnelon, NJ", "Chicago, IL", "London, UK").
  Reports temperature, feels-like, humidity, wind, visibility, and an hourly
  outlook through the end of the day. Uses NWS for US locations and Open-Meteo
  for international ones. No API key required. Use when asked about the weather,
  current conditions, today's forecast, or hourly outlook for any location.
license: MIT
compatibility: "Linux/macOS (requires Python 3; no external packages needed)"
metadata:
  author: "Thomas Ott"
  version: "1.0"
---

# Weather Skill

## Data sources

| Coverage | Source | Key required |
|---|---|---|
| US locations | National Weather Service (api.weather.gov) | No |
| Non-US locations | Open-Meteo (api.open-meteo.com) | No |
| Geocoding (all) | Nominatim / OpenStreetMap | No |

## Invocation

```
/weather <zip code or location name>
```

Examples:
```
/weather 07405
/weather Kinnelon, NJ
/weather Chicago, IL
/weather London, UK
/weather Tokyo, Japan
```

## Instructions for the model

### Step 1 — Run the script

```bash
python3 scripts/forecast.py "<location>"
```

Pass the full location string as a single quoted argument.

### Step 2 — Present the output

Report the script's output directly. Then add a one- or two-sentence
interpretation covering:
- Whether conditions are notable (unusually warm/cold, active weather)
- The key thing to know about the rest of the day (e.g., rain arriving this afternoon, staying clear all day)

### Step 3 — Offer follow-up

After presenting the forecast, offer:
- Extended outlook ("Want the week ahead?")
- A comparison to seasonal norms if conditions are unusual
- Weather for a different location if relevant

## What the script returns

| Section | Contents |
|---|---|
| Current Conditions | Temperature, feels-like, humidity, wind, conditions, dewpoint, visibility, pressure, observation time |
| Today's Forecast | High, tonight low, precipitation chance, NWS detailed summary |
| Hourly Outlook | Next 12 hours: time, temp, rain %, wind speed, short conditions |

## Error handling

| Condition | Response |
|---|---|
| Location not found | Ask the user to check spelling or try a nearby city |
| NWS unavailable for a US location | Script falls back to Open-Meteo automatically |
| Network error | Report the error; suggest checking connectivity |
| Non-US zip code entered | Nominatim will geocode it if the format is recognizable; otherwise ask for city name |
