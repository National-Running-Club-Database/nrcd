"""TimeZoneDB lookup for localizing race date/time."""

from __future__ import annotations

from nrcd.enrich.api_usage import ApiUsage
from nrcd.enrich.cache import get_or_fetch, timezone_cache_key
from nrcd.enrich.config import EnrichConfig
from nrcd.enrich.http import get_with_retries
from nrcd.enrich.throttle import wait_for_provider


def _timezone_http(
    lat: float,
    lon: float,
    *,
    cfg: EnrichConfig,
    api_key: str,
    usage: ApiUsage | None = None,
) -> str | None:
    wait_for_provider("timezonedb", cfg.timezone_min_interval_sec)
    if usage is not None:
        usage.record("timezonedb")
    url = (
        "http://api.timezonedb.com/v2.1/get-time-zone"
        f"?key={api_key}&format=json&by=position&lat={lat}&lng={lon}"
    )
    response = get_with_retries(url, timeout=cfg.http_timeout_sec, retries=cfg.http_retries)
    if response.status_code != 200:
        return None
    data = response.json()
    if data.get("status") == "OK":
        return data.get("zoneName")
    return None


def lookup_timezone_name(
    lat: float,
    lon: float,
    *,
    config: EnrichConfig | None = None,
    timezone_api_key: str | None = None,
    use_cache: bool | None = None,
    usage: ApiUsage | None = None,
) -> str | None:
    """IANA timezone name (e.g. America/Denver) for lat/lon."""
    cfg = config or EnrichConfig()
    key = timezone_api_key or cfg.timezone_api_key
    if not key:
        raise ValueError(
            "timezone_api_key required (argument, EnrichConfig, or NRCD_TIMEZONE_API_KEY)"
        )

    cache_on = cfg.cache_enabled if use_cache is None else use_cache
    cache_key = timezone_cache_key(lat, lon)

    def fetch():
        return _timezone_http(lat, lon, cfg=cfg, api_key=key, usage=usage)

    return get_or_fetch(cache_key, fetch, ttl_sec=cfg.timezone_ttl_sec, enabled=cache_on)
