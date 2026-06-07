"""API keys for enrichment (pass explicitly or via environment)."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class EnrichConfig:
    """Credentials for :mod:`nrcd.enrich`."""

    openweather_api_key: str | None = None
    timezone_api_key: str | None = None
    geocode_country_suffix: str = "US"
    http_timeout_sec: float = 20.0
    http_retries: int = 3

    # In-memory TTL cache (NRCD backfill dedupes by city/state per batch).
    cache_enabled: bool = True
    geocode_ttl_sec: float = 7 * 86400
    altitude_ttl_sec: float = 30 * 86400
    timezone_ttl_sec: float = 365 * 86400
    weather_ttl_sec: float = 86400

    # Provider spacing (seconds between HTTP calls, per process).
    timezone_min_interval_sec: float = 1.5  # TimeZoneDB free tier (~1 req/s)
    openweather_min_interval_sec: float = 0.0
    usgs_min_interval_sec: float = 0.0


def api_keys_from_env() -> EnrichConfig:
    """Read ``NRCD_OPENWEATHER_API_KEY``, ``NRCD_TIMEZONE_API_KEY``, ``NRCD_GEOCODE_COUNTRY_SUFFIX``."""
    suffix = os.environ.get("NRCD_GEOCODE_COUNTRY_SUFFIX")
    country = "US"
    if suffix and suffix.strip():
        country = suffix.strip().upper()
    return EnrichConfig(
        openweather_api_key=os.environ.get("NRCD_OPENWEATHER_API_KEY") or None,
        timezone_api_key=os.environ.get("NRCD_TIMEZONE_API_KEY") or None,
        geocode_country_suffix=country,
    )
