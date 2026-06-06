"""OpenWeather geocoding (US city + state by default)."""

from __future__ import annotations

from urllib.parse import quote

from nrcd.enrich.api_usage import ApiUsage
from nrcd.enrich.cache import geocode_cache_key, get_or_fetch
from nrcd.enrich.config import EnrichConfig
from nrcd.enrich.http import get_with_retries
from nrcd.enrich.throttle import wait_for_provider


def _geocode_http(
    city: str,
    state: str,
    *,
    cfg: EnrichConfig,
    api_key: str,
    usage: ApiUsage | None = None,
) -> tuple[float, float] | None:
    wait_for_provider("openweather", cfg.openweather_min_interval_sec)
    if usage is not None:
        usage.record("openweather_geocode")
    q = quote(f"{city},{state},{cfg.geocode_country_suffix}", safe=",")
    url = f"https://api.openweathermap.org/geo/1.0/direct?q={q}&limit=1&appid={api_key}"
    response = get_with_retries(url, timeout=cfg.http_timeout_sec, retries=cfg.http_retries)
    if response.status_code != 200:
        return None
    data = response.json()
    if not data:
        return None
    return float(data[0]["lat"]), float(data[0]["lon"])


def geocode_us_city_state(
    city: str,
    state: str,
    *,
    config: EnrichConfig | None = None,
    api_key: str | None = None,
    use_cache: bool | None = None,
    usage: ApiUsage | None = None,
) -> tuple[float, float] | None:
    """Return (lat, lon) or None. Requires OpenWeather API key."""
    cfg = config or EnrichConfig()
    key = api_key or cfg.openweather_api_key
    if not key:
        raise ValueError(
            "openweather_api_key required (argument, EnrichConfig, or NRCD_OPENWEATHER_API_KEY)"
        )
    city = (city or "").strip()
    state = (state or "").strip()
    if not city or not state:
        return None

    cache_on = cfg.cache_enabled if use_cache is None else use_cache
    cache_key = geocode_cache_key(city, state, cfg.geocode_country_suffix)

    def fetch():
        return _geocode_http(city, state, cfg=cfg, api_key=key, usage=usage)

    return get_or_fetch(cache_key, fetch, ttl_sec=cfg.geocode_ttl_sec, enabled=cache_on)
