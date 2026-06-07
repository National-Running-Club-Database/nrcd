# API keys for `nrcd.enrich`

Optional — only needed if you want to **backfill weather or meet altitude** from external APIs. Standardization (`standardize_xc`, `standardize_road`, `standardize_outdoor_track`, `standardize_indoor_track`) does **not** require any keys.

```bash
pip install "nrcd[apis]"
```

## Quick setup

1. Sign up for [OpenWeather](https://home.openweathermap.org/users/sign_up) and create an API key at [API keys](https://home.openweathermap.org/api_keys).
2. (Weather only) Sign up for [TimeZoneDB](https://timezonedb.com/register) and copy your API key.
3. Set environment variables (or pass keys to `EnrichConfig`):

```bash
export NRCD_OPENWEATHER_API_KEY="your_openweather_key"
export NRCD_TIMEZONE_API_KEY="your_timezonedb_key"   # weather backfill only
```

**Local testing (gitignored):** copy [`local_api_keys.env.example`](../local_api_keys.env.example) to `local_api_keys.env` in the repo root, paste your keys, then run live tests:

```bash
cp local_api_keys.env.example local_api_keys.env
# edit local_api_keys.env — never commit this file
pytest -m live_api -v
```

Default live test date is **2024-10-12**. **AQI history** from OpenWeather starts **2020-11-27** (`nrcd.enrich.AQI_HISTORY_AVAILABLE_FROM`); use `NRCD_LIVE_TEST_DATE` on or after that when testing weather/AQI.

4. Use in Python — **city, state, date, and time go on `RaceContext`**, not on `enrich_race_context`:

```python
import datetime as dt

from nrcd.enrich import enrich_race_context
from nrcd.standardize import RaceContext

ctx = RaceContext(
    time_str="22:15",
    gender="M",
    sport_name="Cross Country",
    reported_distance="5k",
    city="Notre Dame",
    state="IN",
    event_date=dt.date(2024, 10, 12),
    event_time=dt.time(10, 0),
)
enrich_race_context(ctx)  # fills meet_elevation and/or weather when keys are set
```

In Python you can also print the full guide: `from nrcd.enrich import API_GUIDE; print(API_GUIDE)`.

---

## What each service does

| Service | API key? | Used for |
|---------|----------|----------|
| **OpenWeather** | Yes (`NRCD_OPENWEATHER_API_KEY`) | US city/state → coordinates; historical weather (°F); AQI |
| **USGS EPQS** | No (free) | Meet **altitude in feet** from lat/lon |
| **TimeZoneDB** | Yes (`NRCD_TIMEZONE_API_KEY`) | Local race time → Unix timestamp (weather only) |

**Important:** OpenWeather does **not** provide meet altitude. Altitude comes from USGS after OpenWeather geocodes the city.

**Course grade** (`elevation_gain` / `elevation_loss`) is separate from meet altitude — it describes the hill profile of the course, not the venue elevation.

### Geographic coverage

| Method | Example |
| ------ | ------- |
| US city + state | `city="Notre Dame"`, `state="IN"` → `Notre Dame,IN,US` |
| City + country | `city="London"`, `country="GB"` → `London,GB` |
| Free-form query | `geocode_query="Paris,FR"` |
| Default country | `EnrichConfig(geocode_country_suffix="CA")` or `export NRCD_GEOCODE_COUNTRY_SUFFIX=CA` |
| Coordinates | `latitude` / `longitude` on `RaceContext` (global weather) |

**Weather** works worldwide once coordinates are resolved. **Meet altitude** (USGS EPQS) is US-focused — set `meet_elevation` manually for non-US venues.

```python
import datetime as dt

from nrcd.enrich import EnrichConfig, enrich_race_context
from nrcd.standardize import RaceContext

ctx = RaceContext(
    time_str="15:30",
    gender="M",
    sport_name="Cross Country",
    reported_distance="10k",
    city="London",
    country="GB",
    event_date=dt.date(2024, 10, 12),
    event_time=dt.time(11, 0),
)
enrich_race_context(ctx, fetch_altitude=False)

# Or: ctx.geocode_query = "Paris,FR"
# Or: EnrichConfig(geocode_country_suffix="FR") with city + optional region in state
```

Environment variable (optional):

```bash
export NRCD_GEOCODE_COUNTRY_SUFFIX=GB
```

---

## OpenWeather (first time)

1. Create a free account: https://home.openweathermap.org/users/sign_up  
2. Open **API keys**: https://home.openweathermap.org/api_keys  
3. Copy the default key (activation can take up to ~2 hours on a new account).  
4. Export it:

```bash
export NRCD_OPENWEATHER_API_KEY="paste_key_here"
```

### OpenWeather products used by `nrcd.enrich`

| API | Purpose | Docs |
|-----|---------|------|
| Geocoding API | `city, state` → lat/lon | https://openweathermap.org/api/geocoding-api |
| One Call API 3.0 (timemachine) | Historical temp, dew point, humidity, pressure | https://openweathermap.org/api/one-call-3 |
| Air Pollution API | Historical AQI (from 2020-11-27 onward) | https://openweathermap.org/api/air-pollution |

**Note:** Historical timemachine weather may require a paid OpenWeather subscription tier. Check your plan at https://openweathermap.org/price. Geocoding and meet-altitude lookup (via USGS) may work on the free tier.

---

## TimeZoneDB (weather only)

Needed when backfilling **weather** for a specific local race date/time.

1. Register: https://timezonedb.com/register  
2. Copy your key from the dashboard.  
3. Export:

```bash
export NRCD_TIMEZONE_API_KEY="paste_key_here"
```

Free tier is rate-limited (~1 request/second). `nrcd.enrich` throttles TimeZoneDB calls by default.

---

## USGS EPQS (meet altitude — no signup)

Free public endpoint; no API key.

- Docs: https://epqs.nationalmap.gov/v1/docs  
- Returns terrain elevation in **feet** for coordinates from OpenWeather geocoding.

---

## Passing keys in code (instead of env vars)

```python
import datetime as dt

from nrcd.enrich import EnrichConfig, enrich_race_context
from nrcd.standardize import RaceContext

ctx = RaceContext(
    time_str="16:05",
    gender="M",
    sport_name="Cross Country",
    reported_distance="5k",
    city="Boulder",
    state="CO",
    event_date=dt.date(2024, 9, 14),
    event_time=dt.time(9, 0),
)
config = EnrichConfig(
    openweather_api_key="...",
    timezone_api_key="...",
)
enrich_race_context(ctx, config=config, fetch_altitude=False)
```

---

## Typical API usage per row

| Task | Calls (uncached) |
|------|------------------|
| Meet altitude (city/state) | 1× OpenWeather geocode + 1× USGS |
| Weather (city/state + date/time) | 1× geocode + 1× TimeZoneDB + 1× timemachine + 1× AQI |

`nrcd.enrich` caches results in-process during a batch run. Pass `usage=ApiUsage()` to count calls.

See also: [`nrcd.enrich.API_GUIDE`](../src/nrcd/enrich/guide.py) (full text in the package).
