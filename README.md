# nrcd

Python library for **[National Running Club Database (NRCD)](https://github.com/National-Running-Club-Database/nrcd)** performance standardization (cross country, track, road race). Implements the formulas documented in the NRCD resource paper.

[![GitHub](https://img.shields.io/badge/GitHub-National--Running--Club--Database%2Fnrcd-181717?logo=github)](https://github.com/National-Running-Club-Database/nrcd)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/badge/PyPI-nrcd-3775A9?logo=pypi&logoColor=white)](https://pypi.org/project/nrcd/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/National-Running-Club-Database/nrcd/actions/workflows/ci.yml/badge.svg)](https://github.com/National-Running-Club-Database/nrcd/actions/workflows/ci.yml)

Use this to **standardize your own race results** — no NRCD dataset download required.

## Quick start

Times can be **seconds** or clock strings (`"22:15"`, `"4:12.00"`, `"10.52"`). XC distances accept **m/km/mi** or labels like `"5k"`. Invalid time, distance, or unit strings raise **ValueError** with a short hint (they do not return NaN silently).

**Cross country** — pass a **target distance** when you want a Riegel conversion (e.g. 8000m). Without it, the standardized time stays at the race distance.

**Cross country — 5K in 22:15, target distance 8000m**

```python
from nrcd import format_time, standardize_xc

std = standardize_xc(
    "22:15",
    gender="M",
    reported_distance="5k",
    target_distance_m=8000,  # 8000m
    # target_distance="8k",
    # target_distance=8, target_distance_unit="km",
    # target_distance=4.97, target_distance_unit="mi",  # ~8000m
)
print(format_time(std))
# → 36:31.94
```

**Cross country — 8 km with weather, grade, altitude, target distance 8000m**

```python
from nrcd import format_time, standardize_xc

std = standardize_xc(
    "27:30",
    gender="M",
    reported_distance=8,
    distance_unit="km",
    actual_distance=8.01,
    temperature=72,          # °F (default)
    dew_point=65,
    elevation_gain=2.5,      # % grade (default)
    elevation_loss=2.5,
    meet_elevation=5200,     # feet (default)
    target_distance_m=8000,  # 8000m
)
print(format_time(std))
# → 26:42.19
```

**Outdoor track — 100m with wind**

```python
from nrcd import standardize_outdoor_track

std = standardize_outdoor_track(
    "13.52",
    gender="F",
    event_name="100m",
    wind_mps=2.0,
)
print(f"{std:.3f} s")
# → 13.630 s
```

**Indoor track — 200m on a banked 200m oval**

```python
from nrcd import standardize_indoor_track

std = standardize_indoor_track(
    "21.80",
    gender="M",
    event_name="200m",
    lap_length_m=200,
    banked=True,
)
print(f"{std:.3f} s")
# → 22.588 s
```

**Road — half marathon with weather and grade**

```python
from nrcd import format_time, standardize_road

std = standardize_road(
    "1:25:30",
    gender="F",
    event_name="Half Marathon",
    temperature=55,
    dew_point=48,
    elevation_gain=1.2,
    elevation_loss=1.2,
)
print(format_time(std))
# → 1:25:40.54 (same event distance; no Riegel target conversion)
```

### Pipelines


| Sport         | Function                    | What differs                                                                            |
| ------------- | --------------------------- | --------------------------------------------------------------------------------------- |
| Cross country | `standardize_xc`            | Weather, grade, altitude; optional **Riegel** to a target distance (e.g. 8000m)       |
| Road          | `standardize_road`          | Same weather / grade / altitude as XC; distance from `event_name`; **no Riegel target** |
| Outdoor track | `standardize_outdoor_track` | Sprint **wind**, weather, grade, altitude                                               |
| Indoor track  | `standardize_indoor_track`  | **Lap/bank venue** factors; no wind                                                     |


`standardize_result` remains available when you need a custom `sport_name` string.

**Unit switches** (optional kwargs on all pipelines):


| Field                              | Default     | Alternative                   |
| ---------------------------------- | ----------- | ----------------------------- |
| `temperature`, `dew_point`         | **°F**      | `temp_unit="C"`               |
| `meet_elevation`                   | **feet**    | `venue_elevation_unit="m"`    |
| `elevation_gain`, `elevation_loss` | **% grade** | `grade_input="feet"` or `"m"` |


### More examples

Runnable scripts in [examples/](examples/):


|       | Script                                                                                                                                                                                          |
| ----- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| XC    | [xc_examples.py](examples/xc_examples.py), [compare_improvement.py](examples/compare_improvement.py), [standardize_one_result.py](examples/standardize_one_result.py) |
| Track | [track_outdoor_examples.py](examples/track_outdoor_examples.py), [track_indoor_examples.py](examples/track_indoor_examples.py), [track_compare_meets.py](examples/track_compare_meets.py) |
| Both  | [race_context_example.py](examples/race_context_example.py), [load_dataset_example.py](examples/load_dataset_example.py) |


`load_dataset_example.py` exits with code 1 if Zenodo CSVs are not in `data/` — that is expected without the optional dataset.

```bash
pip install nrcd
python examples/xc_examples.py
python examples/track_outdoor_examples.py
```

## Install

Requires Python 3.10+.

```bash
pip install nrcd              # after first PyPI release
pip install "nrcd[apis]"      # optional: weather / elevation APIs
pip install "nrcd[data]"      # optional: Zenodo CSV helpers (pandas)
```

Until the package is on PyPI, install from source:

```bash
git clone https://github.com/National-Running-Club-Database/nrcd
cd nrcd
pip install -e .
```

From source (development):

```bash
git clone https://github.com/National-Running-Club-Database/nrcd
cd nrcd
pip install -e ".[dev]"
pip install -e ".[dev,apis]"
```

### API keys (optional — `nrcd.enrich` only)

Standardization does **not** need API keys. Use enrichment only when backfilling **weather** or **meet altitude** from city/state.

1. `pip install "nrcd[apis]"`
2. [![OpenWeather](https://img.shields.io/badge/OpenWeather-sign%20up-EE7023?logo=openweathermap)](https://home.openweathermap.org/users/sign_up) → [![API keys](https://img.shields.io/badge/OpenWeather-API%20keys-EE7023?logo=openweathermap)](https://home.openweathermap.org/api_keys) → set `NRCD_OPENWEATHER_API_KEY`
3. For **weather** at a race date/time, also [![TimeZoneDB](https://img.shields.io/badge/TimeZoneDB-register-0066CC)](https://timezonedb.com/register) → `NRCD_TIMEZONE_API_KEY`
4. **Meet altitude** uses free USGS EPQS (no key) after OpenWeather geocodes the city

```bash
export NRCD_OPENWEATHER_API_KEY="your_key"
export NRCD_TIMEZONE_API_KEY="your_key"   # weather only
export NRCD_GEOCODE_COUNTRY_SUFFIX=US     # optional; ISO country for geocoding
```

**Live tests (optional):** copy `local_api_keys.env.example` → `local_api_keys.env` (gitignored), add your OpenWeather key, then `pytest -m live_api -v`. AQI history starts **2020-11-27**; default test date is **2024-10-12**.

**Full walkthrough:** [![API keys guide](https://img.shields.io/badge/docs-API__KEYS-0366d6?logo=readthedocs)](docs/API_KEYS.md). In Python: `from nrcd.enrich import API_GUIDE; print(API_GUIDE)`.

Historical OpenWeather timemachine weather may require a **paid** OpenWeather plan; geocoding + USGS altitude often work on the free tier.

### Geographic coverage (`nrcd.enrich`)

| Method | Example | Weather | Altitude (USGS) |
| ------ | ------- | ------- | ---------------- |
| **US city + state** | `city="Notre Dame"`, `state="IN"` | ✅ | ✅ (US) |
| **City + country** | `city="London"`, `country="GB"` | ✅ | ⚠️ set `meet_elevation` non-US |
| **Free-form query** | `geocode_query="Paris,FR"` | ✅ | ⚠️ same |
| **Config / env default country** | `EnrichConfig(geocode_country_suffix="CA")` or `NRCD_GEOCODE_COUNTRY_SUFFIX=CA` | ✅ | ⚠️ same |
| **Lat/lon** | `latitude=51.5`, `longitude=-0.12` | ✅ global | ⚠️ US-focused EPQS |

```python
import datetime as dt
from nrcd.enrich import EnrichConfig, enrich_race_context
from nrcd.standardize import RaceContext

# International weather — city + country (no US state required)
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
enrich_race_context(ctx, fetch_altitude=False)  # skip USGS outside US

# Or free-form geocode query
ctx.geocode_query = "Paris,FR"
```

Standardization has no geographic limit — only optional enrichment does.

## Do you need the NRCD dataset?


| Use case                                | Zenodo CSVs needed? |
| --------------------------------------- | ------------------- |
| Standardize your own results            | **No**              |
| `examples/` scripts                     | **No**              |
| `nrcd.enrich` API backfill              | **No**              |
| `examples/load_dataset_example.py` only | **Yes** (optional)  |


Optional public export: [![Zenodo dataset](https://img.shields.io/badge/Zenodo-NRCD%20dataset-1682D4?logo=zenodo)](https://zenodo.org/records/17917357) (see [![data/README.md](https://img.shields.io/badge/data-README-lightgrey)](data/README.md)).

## API

Full parameter tables: `from nrcd import PARAMETERS_DOC` or `help(nrcd.standardize)`.

### Entry points


| Function                    | Use for                                                                 |
| --------------------------- | ----------------------------------------------------------------------- |
| `standardize_xc`            | Cross country — optional target distance (`target_distance_m`, `target_distance` + unit, or `"8k"`) |
| `standardize_road`          | Road / marathon — `event_name`; weather, grade, altitude                |
| `standardize_outdoor_track` | Outdoor track — `event_name`; wind on sprints                           |
| `standardize_indoor_track`  | Indoor track — `event_name`; lap length / banking                       |
| `standardize_result`        | Low-level — any `sport_name` (advanced)                                 |
| `standardize_seconds`       | Dispatch from a `RaceContext` / `XCRaceContext` row                     |
| `enrich_race_context`       | Fill missing weather/altitude on a context (`pip install "nrcd[apis]"`) |


### `nrcd.standardize` — pipelines & context


| Name                                                             | Description                                                      |
| ---------------------------------------------------------------- | ---------------------------------------------------------------- |
| `RaceContext`                                                    | Dataclass for one result (XC or track); `time_str` or `time_sec` |
| `XCRaceContext`                                                  | XC-focused `RaceContext` subclass                                |
| `StandardizeConfig`                                              | Paper coefficients (Riegel exponents, heat k, grade bases, …)    |
| `PARAMETERS_DOC`                                                 | Full required/optional parameter reference (text)                |
| `PARAMETER_SPECS`                                                | Same metadata as structured `ParameterSpec` tuples               |
| `parameter_specs()`                                              | Return `PARAMETER_SPECS`                                         |
| `required_for("xc" | "road" | "outdoor_track" | "indoor_track")` | Minimal field names per pipeline                                 |


### `nrcd.standardize` — time, distance, units


| Name                               | Description                                                       |
| ---------------------------------- | ----------------------------------------------------------------- |
| `parse_time`                       | `"22:15"`, `"1:10:13"`, or seconds → float seconds                |
| `format_time`                      | Seconds → clock string                                            |
| `parse_distance`                   | `"5k"`, `8`, `"8000m"` + unit → meters                            |
| `distance_to_meters`               | Numeric distance with `distance_unit` (`m` / `km` / `mi`)         |
| `c_to_f`, `f_to_c`                 | Temperature conversion                                            |
| `feet_to_meters`, `meters_to_feet` | Length conversion                                                 |
| `temperature_to_fahrenheit`        | Value + `temp_unit` (`F` / `C`) → °F                              |
| `venue_elevation_to_feet`          | Meet altitude + `venue_elevation_unit` (`ft` / `m`) → ft          |
| `grade_percent_from_feet`          | Vertical ft over course → % grade                                 |
| `grade_percent_from_meters`        | Vertical m over course → % grade                                  |
| `resolve_grade_percent`            | Normalize gain/loss with `grade_input` (`percent` / `feet` / `m`) |


### `nrcd.standardize` — factors & sport helpers


| Name                                                                  | Description                                                |
| --------------------------------------------------------------------- | ---------------------------------------------------------- |
| `weather_factor`                                                      | Heat slowdown multiplier from temp + dew point (°F)        |
| `heat_index`, `heat_slowdown_percent`                                 | Hadley-style heat index components                         |
| `elevation_factor`                                                    | Maurer grade multiplier from % gain/loss                   |
| `apply_course_grade_factor`                                           | Grade step on a race time                                  |
| `warn_one_sided_course_grade`                                         | Warn when only gain or only loss is set                    |
| `apply_meet_altitude`                                                 | Peronnet meet-altitude correction                          |
| `peronnet_f_alt`, `sea_level_time_seconds`                            | Altitude factor and sea-level equivalent                   |
| `resolve_meet_altitude_inputs`                                        | Parse elevation + barometric pressure from a record        |
| `barometric_pressure_hpa_from_record`                                 | hPa from row fields                                        |
| `barometric_pressure_torr_from_hpa`, `parse_barometric_pressure_hpa`  | Pressure unit helpers                                      |
| `riegel_convert`, `riegel_exponent`                                   | Distance conversion                                        |
| `xc_target_distance_m`                                                | Config helper for target distance in meters (8000m M / 6000m F) |
| `apply_factors`                                                       | Multiply time by weather/grade/altitude/track/wind factors |
| `is_cross_country`, `is_track`, `is_outdoor_track`, `is_indoor_track` | Sport name checks                                          |
| `normalize_sport_name`, `pipeline_kind`                               | Sport string normalization / `xc` vs `track`               |


### `nrcd.data` — Zenodo CSV helpers


| Name                           | Description                                           |
| ------------------------------ | ----------------------------------------------------- |
| `meet_altitude_column`         | Altitude column name in a meet DataFrame              |
| `meet_altitude_ft_from_record` | Meet altitude (ft) from a merged row + course details |
| `derive_course_details_fields` | Derived weather/grade fields from course details      |


### `nrcd.enrich` — optional APIs (`pip install "nrcd[apis]"`)


| Name                                                                  | Description                                                               |
| --------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| `API_GUIDE`                                                           | Full signup guide (text); see also [![API keys guide](https://img.shields.io/badge/docs-API__KEYS-0366d6?logo=readthedocs)](docs/API_KEYS.md) |
| `EnrichConfig`                                                        | Throttle intervals, cache TTL, API keys                                   |
| `api_keys_from_env`                                                   | Load keys from environment                                                |
| `fetch_weather`                                                       | Temperature, dew point, humidity, AQI — global with `lat`/`lon`; US city/state by default |
| `lookup_altitude_ft`, `lookup_altitude_detail`, `lookup_elevation_ft` | Meet altitude (USGS EPQS, ft) — US city/state path; set `meet_elevation` for non-US |
| `enrich_race_context`, `enrich_race_context_result`                   | Backfill a `RaceContext` in place                                         |
| `run_enrich_jobs`, `EnrichJob`, `JobResult`                           | Batch enrichment with thread pool                                         |
| `EnrichResult`, `ApiUsage`, `WeatherData`, `AltitudeResult`           | Result / usage dataclasses                                                |
| `cache_stats`, `clear_enrich_cache`, `reset_throttle_state`           | Cache and rate-limit controls                                             |
| `AQI_HISTORY_AVAILABLE_FROM`, `AQI_HISTORY_AVAILABLE_UNIX`            | AQI history window constants                                              |


## Citation

> **NRCD: An Open Database of Collegiate Running with Unified Performance Standardization**  
> Jonathan A. Karr Jr, Ryan M. Fryer, Ben Darden, Nicholas Pell, Kayla Ambrose, Evan Hall, Ramzi K. Bualuan, and Nitesh V. Chawla.  
> arXiv preprint (forthcoming).

Dataset (if using Zenodo export): [![Zenodo dataset](https://img.shields.io/badge/Zenodo-NRCD%20dataset-1682D4?logo=zenodo)](https://zenodo.org/records/17917357)

## Author

[![Jonathan Karr ORCID](https://img.shields.io/badge/Jonathan%20Karr-ORCID-a6ce39?logo=orcid)](https://orcid.org/0009-0000-1600-6122)
[![Email](https://img.shields.io/badge/jkarr%40nd.edu-Email-D14836?logo=gmail)](mailto:jkarr@nd.edu)

## Development

```bash
pytest
```

See [![Changelog](https://img.shields.io/badge/Changelog-CHANGELOG.md-blue)](CHANGELOG.md). Package version: [![src/nrcd/__init__.py](https://img.shields.io/badge/version-src%2Fnrcd%2F__init__.py-lightgrey)](src/nrcd/__init__.py) (`__version__`).

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)