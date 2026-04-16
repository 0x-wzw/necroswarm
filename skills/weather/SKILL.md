---
name: weather
description: Get current weather and forecasts via wttr.in or Open-Meteo. Use when Z asks about weather, temperature, or forecasts for any location. No API key needed. Can also get air quality, UV index, and astronomical data.
---

# Weather Skill

Get weather data for any location — no API key required.

## Quick Usage

```bash
# Current weather
curl "https://wttr.in/London?format=j1"

# 3-day forecast
curl "https://wttr.in/Tokyo?format=j1"

# Specific location with lat/lon
curl "https://wttr.in/Kuala+Lumpur?0&T&m"

# Moon phase
curl "wttr.in/Moon"
```

## Open-Meteo (More Data)

```bash
# Current + hourly forecast
curl "https://api.open-meteo.com/v1/forecast?latitude=3.1&longitude=101.5&current=temperature_2m,relative_humidity_2m,weather_code&hourly=temperature_2m,precipitation_probability&timezone=auto"

# Air quality
curl "https://air-quality-api.open-meteo.com/v1/air-quality?latitude=3.1&longitude=101.5&current=us_aqi,pm2_5,european_aqi"
```

## Use Cases

### Location with Context

```bash
# Weather + what to wear
curl "wttr.in/Singapore?format=%c%t\nFeels+like+%f\nHumidity=%h"
```

### Multi-City Comparison

```bash
for city in London Tokyo "New York"; do
  echo "$city: $(curl -s wttr.in/$city?format=%t)"
done
```

## Notes

- wttr.in: no key needed, works globally
- Open-Meteo: no key needed, richer data, metric only
- Both are free for non-commercial use
