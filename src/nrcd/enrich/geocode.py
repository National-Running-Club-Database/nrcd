"""OpenWeather geocoding (US city + state by default; international options)."""

from __future__ import annotations

from urllib.parse import quote

from nrcd.enrich.api_usage import ApiUsage
from nrcd.enrich.cache import geocode_cache_key, get_or_fetch
from nrcd.enrich.config import EnrichConfig
from nrcd.enrich.http import get_with_retries
from nrcd.enrich.throttle import wait_for_provider


def build_geocode_query(
    *,
    city: str = "",
    state: str = "",
    country: str | None = None,
    geocode_query: str | None = None,
    default_country: str = "US",
) -> str | None:
    """Build an OpenWeather Geocoding API ``q`` string.

    Priority: ``geocode_query`` → ``city,state,country`` → ``city,country`` → ``city,state``.
    """
    if geocode_query and geocode_query.strip():
        return geocode_query.strip()
    city = (city or "").strip()
    state = (state or "").strip()
    country_code = (country or default_country or "").strip()
    if not city:
        return None
    if state and country_code:
        return f"{city},{state},{country_code}"
    if country_code:
        return f"{city},{country_code}"
    if state:
        return f"{city},{state}"
    return city


def _geocode_http(
    query: str,
    *,
    cfg: EnrichConfig,
    api_key: str,
    usage: ApiUsage | None = None,
) -> tuple[float, float] | None:
    wait_for_provider("openweather", cfg.openweather_min_interval_sec)
    if usage is not None:
        usage.record("openweather_geocode")
    q = quote(query, safe=",")
    url = f"https://api.openweathermap.org/geo/1.0/direct?q={q}&limit=1&appid={api_key}"
    response = get_with_retries(url, timeout=cfg.http_timeout_sec, retries=cfg.http_retries)
    if response.status_code != 200:
        return None
    data = response.json()
    if not data:
        return None
    return float(data[0]["lat"]), float(data[0]["lon"])


def geocode_location(
    city: str = "",
    state: str = "",
    *,
    country: str | None = None,
    geocode_query: str | None = None,
    config: EnrichConfig | None = None,
    api_key: str | None = None,
    use_cache: bool | None = None,
    usage: ApiUsage | None = None,
) -> tuple[float, float] | None:
    """Return (lat, lon) from OpenWeather geocoding, or None. Requires API key."""
    cfg = config or EnrichConfig()
    key = api_key or cfg.openweather_api_key
    if not key:
        raise ValueError(
            "openweather_api_key required (argument, EnrichConfig, or NRCD_OPENWEATHER_API_KEY)"
        )
    query = build_geocode_query(
        city=city,
        state=state,
        country=country,
        geocode_query=geocode_query,
        default_country=cfg.geocode_country_suffix,
    )
    if not query:
        return None

    country_for_cache = (country or cfg.geocode_country_suffix or "US").upper()
    cache_on = cfg.cache_enabled if use_cache is None else use_cache
    cache_key = geocode_cache_key(
        city,
        state,
        country_for_cache,
        geocode_query=geocode_query,
    )

    def fetch():
        return _geocode_http(query, cfg=cfg, api_key=key, usage=usage)

    return get_or_fetch(cache_key, fetch, ttl_sec=cfg.geocode_ttl_sec, enabled=cache_on)


def geocode_us_city_state(
    city: str,
    state: str,
    *,
    country: str | None = None,
    geocode_query: str | None = None,
    config: EnrichConfig | None = None,
    api_key: str | None = None,
    use_cache: bool | None = None,
    usage: ApiUsage | None = None,
) -> tuple[float, float] | None:
    """Return (lat, lon) or None. Alias for :func:`geocode_location` (US defaults)."""
    return geocode_location(
        city,
        state,
        country=country,
        geocode_query=geocode_query,
        config=config,
        api_key=api_key,
        use_cache=use_cache,
        usage=usage,
    )
