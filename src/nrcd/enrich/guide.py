"""How to obtain API keys used by :mod:`nrcd.enrich`."""

API_GUIDE = """
External APIs for nrcd.enrich
=============================

Terminology
-----------
  • **Meet altitude** (city/state lookup) — venue elevation in feet (Peronnet model).
    OpenWeather provides coordinates only; USGS EPQS returns the altitude.
  • **elevation_gain / elevation_loss** — course grade profile (% by default), used on
    cross country and road. Not the same as meet altitude.

1. OpenWeather (geocoding + weather + AQI — NOT altitude)
---------------------------------------------------------
Sign up: https://home.openweathermap.org/users/sign_up
API keys: https://home.openweathermap.org/api_keys

  • Geocoding API — US city/state → lat/lon (needed before USGS altitude lookup)
    https://openweathermap.org/api/geocoding-api
    GET https://api.openweathermap.org/geo/1.0/direct?q={city},{state},US&appid=KEY

  • One Call API 3.0 — timemachine historical weather (°F, units=imperial)
    https://openweathermap.org/api/one-call-3
    Timemachine may require a paid subscription tier.

  • Air Pollution API — historical AQI and component concentrations
    https://openweathermap.org/api/air-pollution
    Historical AQI from 27 November 2020 onward (OpenWeather docs).

Environment variable: NRCD_OPENWEATHER_API_KEY

2. USGS National Map EPQS — meet altitude in feet (free, no API key)
---------------------------------------------------------------------
This is the **altitude** source for city/state lookup (not OpenWeather).

  https://epqs.nationalmap.gov/v1/docs
  GET https://epqs.nationalmap.gov/v1/json?x={lon}&y={lat}&units=Feet&includeDate=false

Coordinates come from OpenWeather geocoding; USGS returns terrain altitude.

3. TimeZoneDB (weather only — local race time → Unix timestamp)
---------------------------------------------------------------
Sign up: https://timezonedb.com/register

Environment variable: NRCD_TIMEZONE_API_KEY

Weather fields (NRCD course_details)
------------------------------------
  temperature, real_feel, dew_point, humidity, barometric_pressure (hPa, OpenWeather timemachine)
  weather_conditions, weather_description, openweather_dt_unix
  aqi, aqi_co, aqi_no, aqi_no2, aqi_o3, aqi_so2, aqi_pm2_5, aqi_pm10, aqi_nh3 (if race >= 2020-11-27)

Hourly snapshots (not minute-precise)
------------------------------------
  Timemachine weather and AQI history return the **hour containing** the local race
  start time. ``openweather_dt_unix`` is the snapshot hour returned by OpenWeather.

API call accounting (ApiUsage)
------------------------------
  Pass ``usage=ApiUsage()`` to fetch_weather / lookup_altitude_ft / enrich_race_context.
  Or use enrich_race_context_result() to get context + usage together.

  Typical HTTP calls per **fresh** (uncached) row:
    • Weather: geocode (city→lat/lon) + TimeZoneDB + timemachine + AQI = 4 OpenWeather + 1 TimeZoneDB
    • Meet altitude: geocode + USGS EPQS = 1 OpenWeather + 1 USGS

  Skip geocode when ``lat``/``lon`` are known (e.g. meet.meet_latitude / meet_longitude):
    weather drops to TimeZoneDB + timemachine + AQI; altitude drops to USGS only.
  In-process TTL cache avoids repeat calls for the same city/state or coordinates.

Meet altitude lookup sets meet.altitude in feet (NRCD meet table column).

Caching and throttling (nrcd.enrich defaults)
---------------------------------------------
  • TTL cache: only within one Python process / one batch script run (not shared across users).
    Helps when many rows share the same city/state. Single one-off lookups do not benefit.
  • TimeZoneDB: minimum 1.5s between requests (EnrichConfig.timezone_min_interval_sec).
  • Batch enrichment: run_enrich_jobs() with EnrichJob callables (parallel=1 by default).
    Each job returns a JobResult; failures are recorded without stopping the run.
"""
