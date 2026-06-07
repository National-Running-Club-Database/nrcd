"""Fetch meet altitude and course weather from external APIs (optional).

Requires ``pip install nrcd[apis]`` (installs ``requests``).

**Geocoding:** US default is ``city,state,US``. International options: ``city`` + ``country`` on
``RaceContext``, ``geocode_query`` (e.g. ``London,GB``), ``EnrichConfig(geocode_country_suffix=...)``,
or env ``NRCD_GEOCODE_COUNTRY_SUFFIX``. ``lat``/``lon`` skips geocode (global weather).

**Meet altitude** uses USGS EPQS after geocoding — US-focused; pass ``meet_elevation`` for non-US venues.

API signup: :data:`nrcd.enrich.API_GUIDE`.
"""

from nrcd.enrich.altitude import (
    AltitudeResult,
    lookup_altitude_detail,
    lookup_altitude_ft,
    lookup_elevation_ft,
)
from nrcd.enrich.api_usage import (
    AQI_HISTORY_AVAILABLE_FROM,
    AQI_HISTORY_AVAILABLE_UNIX,
    ApiUsage,
    EnrichResult,
)
from nrcd.enrich.batch import EnrichJob, JobResult, run_enrich_jobs
from nrcd.enrich.cache import cache_stats, clear_enrich_cache
from nrcd.enrich.config import EnrichConfig, api_keys_from_env
from nrcd.enrich.context import enrich_race_context, enrich_race_context_result
from nrcd.enrich.geocode import build_geocode_query, geocode_location, geocode_us_city_state
from nrcd.enrich.guide import API_GUIDE
from nrcd.enrich.weather import WeatherData, fetch_weather

__all__ = [
    "API_GUIDE",
    "AQI_HISTORY_AVAILABLE_FROM",
    "AQI_HISTORY_AVAILABLE_UNIX",
    "AltitudeResult",
    "ApiUsage",
    "EnrichConfig",
    "EnrichResult",
    "WeatherData",
    "api_keys_from_env",
    "build_geocode_query",
    "geocode_location",
    "geocode_us_city_state",
    "EnrichJob",
    "JobResult",
    "cache_stats",
    "clear_enrich_cache",
    "enrich_race_context",
    "enrich_race_context_result",
    "run_enrich_jobs",
    "fetch_weather",
    "lookup_altitude_ft",
    "lookup_altitude_detail",
    "lookup_elevation_ft",
    "reset_throttle_state",
]
