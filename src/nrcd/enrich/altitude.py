"""Meet **altitude** (venue elevation) from US city/state.

OpenWeather is used **only to geocode** city/state → lat/lon. Terrain **altitude in feet**
comes from the free USGS EPQS service (not OpenWeather).
"""

from __future__ import annotations

from dataclasses import dataclass

from nrcd.enrich.api_usage import ApiUsage
from nrcd.enrich.cache import altitude_cache_key, get_or_fetch
from nrcd.enrich.config import EnrichConfig
from nrcd.enrich.geocode import geocode_us_city_state
from nrcd.enrich.http import get_with_retries
from nrcd.enrich.throttle import wait_for_provider


@dataclass(frozen=True)
class AltitudeResult:
    """Venue altitude lookup result."""

    altitude_ft: int
    lat: float
    lon: float
    city: str
    state: str


def _altitude_from_coords(
    lat: float,
    lon: float,
    city: str,
    state: str,
    *,
    cfg: EnrichConfig,
    usage: ApiUsage | None = None,
) -> AltitudeResult | None:
    wait_for_provider("usgs", cfg.usgs_min_interval_sec)
    if usage is not None:
        usage.record("usgs_epqs")
    url = (
        "https://epqs.nationalmap.gov/v1/json"
        f"?x={lon}&y={lat}&units=Feet&includeDate=false"
    )
    response = get_with_retries(url, timeout=10.0, retries=cfg.http_retries)
    response.raise_for_status()
    data = response.json()
    value = data.get("value")
    if value is None:
        return None
    return AltitudeResult(
        altitude_ft=int(round(float(value))),
        lat=lat,
        lon=lon,
        city=city,
        state=state,
    )


def lookup_altitude_ft(
    city: str,
    state: str,
    *,
    config: EnrichConfig | None = None,
    openweather_api_key: str | None = None,
    use_cache: bool | None = None,
    lat: float | None = None,
    lon: float | None = None,
    usage: ApiUsage | None = None,
) -> int | None:
    """Meet altitude in feet for a US city/state (NRCD ``meet.altitude`` column)."""
    result = lookup_altitude_detail(
        city,
        state,
        config=config,
        openweather_api_key=openweather_api_key,
        use_cache=use_cache,
        lat=lat,
        lon=lon,
        usage=usage,
    )
    return None if result is None else result.altitude_ft


def lookup_altitude_detail(
    city: str,
    state: str,
    *,
    config: EnrichConfig | None = None,
    openweather_api_key: str | None = None,
    use_cache: bool | None = None,
    lat: float | None = None,
    lon: float | None = None,
    usage: ApiUsage | None = None,
) -> AltitudeResult | None:
    cfg = config or EnrichConfig()
    if openweather_api_key:
        cfg = EnrichConfig(
            openweather_api_key=openweather_api_key,
            timezone_api_key=cfg.timezone_api_key,
            geocode_country_suffix=cfg.geocode_country_suffix,
            http_timeout_sec=cfg.http_timeout_sec,
            http_retries=cfg.http_retries,
            cache_enabled=cfg.cache_enabled,
            geocode_ttl_sec=cfg.geocode_ttl_sec,
            altitude_ttl_sec=cfg.altitude_ttl_sec,
            timezone_ttl_sec=cfg.timezone_ttl_sec,
            weather_ttl_sec=cfg.weather_ttl_sec,
            timezone_min_interval_sec=cfg.timezone_min_interval_sec,
            openweather_min_interval_sec=cfg.openweather_min_interval_sec,
            usgs_min_interval_sec=cfg.usgs_min_interval_sec,
        )
    city = (city or "").strip()
    state = (state or "").strip()
    if lat is not None and lon is not None:
        return _altitude_from_coords(lat, lon, city, state, cfg=cfg, usage=usage)
    if not city or not state:
        return None

    cache_on = cfg.cache_enabled if use_cache is None else use_cache
    cache_key = altitude_cache_key(city, state, cfg.geocode_country_suffix)

    def fetch():
        coords = geocode_us_city_state(
            city, state, config=cfg, use_cache=cache_on, usage=usage
        )
        if coords is None:
            return None
        lat_v, lon_v = coords
        return _altitude_from_coords(lat_v, lon_v, city, state, cfg=cfg, usage=usage)

    return get_or_fetch(cache_key, fetch, ttl_sec=cfg.altitude_ttl_sec, enabled=cache_on)


lookup_elevation_ft = lookup_altitude_ft
lookup_elevation_detail = lookup_altitude_detail
ElevationResult = AltitudeResult
