"""Fetch meet altitude and course weather from external APIs (optional).

Requires ``pip install nrcd[apis]`` (installs ``requests``).

**Meet altitude** (city/state): OpenWeather geocodes; **USGS EPQS** returns feet.
OpenWeather does **not** supply altitude — only weather, AQI, and coordinates.

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
from nrcd.enrich.guide import API_GUIDE
from nrcd.enrich.throttle import reset_throttle_state
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
