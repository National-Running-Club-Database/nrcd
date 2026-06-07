"""Historical weather and air quality (OpenWeather)."""

from __future__ import annotations

import datetime as dt
from dataclasses import asdict, dataclass
from zoneinfo import ZoneInfo

from nrcd.enrich.api_usage import AQI_HISTORY_AVAILABLE_UNIX, ApiUsage
from nrcd.enrich.cache import get_or_fetch, weather_cache_key
from nrcd.enrich.config import EnrichConfig
from nrcd.enrich.geocode import geocode_location
from nrcd.enrich.http import get_with_retries
from nrcd.enrich.throttle import wait_for_provider
from nrcd.enrich.timezone_lookup import lookup_timezone_name


@dataclass(frozen=True)
class WeatherData:
    """Fields aligned with NRCD ``CourseDetails`` weather columns (imperial units)."""

    temperature: float | None = None
    real_feel: float | None = None
    dew_point: float | None = None
    humidity: float | None = None
    weather_conditions: str | None = None
    weather_description: str | None = None
    aqi: int | None = None
    aqi_co: float | None = None
    aqi_no: float | None = None
    aqi_no2: float | None = None
    aqi_o3: float | None = None
    aqi_so2: float | None = None
    aqi_pm2_5: float | None = None
    aqi_pm10: float | None = None
    aqi_nh3: float | None = None
    barometric_pressure: float | None = None
    """Race-time pressure (hPa); NRCD ``course_details.barometric_pressure`` (OpenWeather)."""
    lat: float | None = None
    lon: float | None = None
    openweather_dt_unix: int | None = None
    """Unix time of the hourly OpenWeather snapshot actually returned (not minute-precise)."""
    aqi_fetched: bool = False
    """True when an AQI history request was made (false if race predates provider history)."""

    def as_course_details_dict(self) -> dict:
        """Keys matching NRCD course_details column names."""
        skip = {"lat", "lon", "aqi_fetched"}
        return {k: v for k, v in asdict(self).items() if k not in skip and v is not None}


def _historical_weather(
    lat: float,
    lon: float,
    timestamp: int,
    api_key: str,
    *,
    config: EnrichConfig,
    usage: ApiUsage | None = None,
) -> tuple[float | None, ...]:
    wait_for_provider("openweather", config.openweather_min_interval_sec)
    if usage is not None:
        usage.record("openweather_timemachine")
    url = (
        "https://api.openweathermap.org/data/3.0/onecall/timemachine"
        f"?lat={lat}&lon={lon}&dt={timestamp}&appid={api_key}&units=imperial"
    )
    response = get_with_retries(url, timeout=config.http_timeout_sec, retries=config.http_retries)
    if response.status_code != 200:
        return (None,) * 8
    data = response.json()
    if "data" not in data or not data["data"]:
        return (None,) * 8
    w = data["data"][0]
    weather = w.get("weather") or [{}]
    main = weather[0]
    return (
        w.get("temp"),
        w.get("feels_like"),
        w.get("dew_point"),
        w.get("humidity"),
        main.get("main"),
        main.get("description"),
        w.get("pressure"),
        w.get("dt"),
    )


def _historical_aqi(
    lat: float,
    lon: float,
    start: int,
    api_key: str,
    *,
    config: EnrichConfig,
    usage: ApiUsage | None = None,
) -> tuple[int | float | None, ...]:
    adjustment_hours = 3600
    for attempt in range(3):
        wait_for_provider("openweather", config.openweather_min_interval_sec)
        if usage is not None:
            usage.record("openweather_aqi")
        adjusted_start = start - (attempt * adjustment_hours)
        adjusted_end = adjusted_start + adjustment_hours
        url = (
            "https://api.openweathermap.org/data/2.5/air_pollution/history"
            f"?lat={lat}&lon={lon}&start={adjusted_start}&end={adjusted_end}&appid={api_key}"
        )
        try:
            response = get_with_retries(
                url, timeout=config.http_timeout_sec, retries=config.http_retries
            )
            response.raise_for_status()
            data = response.json()
            if "list" in data and data["list"]:
                row = data["list"][0]
                comp = row["components"]
                return (
                    row["main"]["aqi"],
                    comp["co"],
                    comp["no"],
                    comp["no2"],
                    comp["o3"],
                    comp["so2"],
                    comp["pm2_5"],
                    comp["pm10"],
                    comp["nh3"],
                )
        except Exception:
            continue
    return (None,) * 9


def _resolve_coords(
    city: str,
    state: str,
    *,
    lat: float | None,
    lon: float | None,
    country: str | None,
    geocode_query: str | None,
    cfg: EnrichConfig,
    ow_key: str,
    use_cache: bool,
    usage: ApiUsage | None,
) -> tuple[float, float] | None:
    if lat is not None and lon is not None:
        return float(lat), float(lon)
    return geocode_location(
        city,
        state,
        country=country,
        geocode_query=geocode_query,
        config=cfg,
        api_key=ow_key,
        use_cache=use_cache,
        usage=usage,
    )


def _fetch_weather_uncached(
    city: str,
    state: str,
    event_date: dt.date,
    event_time: dt.time,
    *,
    cfg: EnrichConfig,
    ow_key: str,
    tz_key: str,
    use_cache: bool,
    lat: float | None = None,
    lon: float | None = None,
    country: str | None = None,
    geocode_query: str | None = None,
    timezone_name: str | None = None,
    usage: ApiUsage | None = None,
) -> WeatherData | None:
    coords = _resolve_coords(
        city,
        state,
        lat=lat,
        lon=lon,
        country=country,
        geocode_query=geocode_query,
        cfg=cfg,
        ow_key=ow_key,
        use_cache=use_cache,
        usage=usage,
    )
    if coords is None:
        return None
    lat_v, lon_v = coords

    tz_name = timezone_name
    if not tz_name:
        tz_name = lookup_timezone_name(
            lat_v,
            lon_v,
            config=cfg,
            timezone_api_key=tz_key,
            use_cache=use_cache,
            usage=usage,
        )
    if not tz_name:
        return None
    local = dt.datetime.combine(event_date, event_time, tzinfo=ZoneInfo(tz_name))
    timestamp = int(local.timestamp())

    temp, feel, dew, hum, cond, desc, pressure_hpa, weather_dt = _historical_weather(
        lat_v, lon_v, timestamp, ow_key, config=cfg, usage=usage
    )

    aqi_parts: tuple[int | float | None, ...] = (None,) * 9
    aqi_fetched = False
    if timestamp >= AQI_HISTORY_AVAILABLE_UNIX:
        aqi_parts = _historical_aqi(
            lat_v, lon_v, timestamp, ow_key, config=cfg, usage=usage
        )
        aqi_fetched = True

    return WeatherData(
        temperature=temp,
        real_feel=feel,
        dew_point=dew,
        humidity=hum,
        weather_conditions=cond,
        weather_description=desc,
        barometric_pressure=pressure_hpa,
        aqi=int(aqi_parts[0]) if aqi_parts[0] is not None else None,
        aqi_co=aqi_parts[1],
        aqi_no=aqi_parts[2],
        aqi_no2=aqi_parts[3],
        aqi_o3=aqi_parts[4],
        aqi_so2=aqi_parts[5],
        aqi_pm2_5=aqi_parts[6],
        aqi_pm10=aqi_parts[7],
        aqi_nh3=aqi_parts[8],
        lat=lat_v,
        lon=lon_v,
        openweather_dt_unix=int(weather_dt) if weather_dt is not None else None,
        aqi_fetched=aqi_fetched,
    )


def fetch_weather(
    city: str,
    state: str,
    event_date: dt.date,
    event_time: dt.time,
    *,
    config: EnrichConfig | None = None,
    openweather_api_key: str | None = None,
    timezone_api_key: str | None = None,
    use_cache: bool | None = None,
    lat: float | None = None,
    lon: float | None = None,
    country: str | None = None,
    geocode_query: str | None = None,
    timezone_name: str | None = None,
    usage: ApiUsage | None = None,
) -> WeatherData | None:
    """Fetch historical weather (+ AQI when available) for the race start hour.

    **Geocoding:** pass ``lat``/``lon`` (global), ``geocode_query`` (e.g. ``London,GB``),
    ``city`` + ``country`` (ISO code), or US-style ``city`` + ``state`` (with
    ``EnrichConfig.geocode_country_suffix`` default ``US``).

    **Hourly snapshots:** OpenWeather timemachine and AQI history return the
    **hour containing** ``event_time``, not a minute-level reading. The actual
    snapshot Unix time is on :attr:`WeatherData.openweather_dt_unix`.

    **AQI history** is only requested for races on or after
    :data:`~nrcd.enrich.AQI_HISTORY_AVAILABLE_FROM` (2020-11-27 per OpenWeather).

    Pass ``lat``/``lon`` (e.g. from ``meet.meet_latitude`` / ``meet_longitude``)
    to skip the geocode call when enriching many ``course_details`` rows for one
    meet. Optional ``timezone_name`` skips the TimeZoneDB call when reused.

    Set ``usage`` to an :class:`~nrcd.enrich.ApiUsage` instance to count HTTP
    calls (cache misses only). Typical fresh weather row: geocode + timezone +
    timemachine + AQI = 4 calls; with ``lat``/``lon`` and cache: 2–3.
    """
    cfg = config or EnrichConfig()
    ow_key = openweather_api_key or cfg.openweather_api_key
    tz_key = timezone_api_key or cfg.timezone_api_key
    if not ow_key:
        raise ValueError("openweather_api_key required")
    if not tz_key and not timezone_name:
        raise ValueError("timezone_api_key required unless timezone_name is set")

    cache_on = cfg.cache_enabled if use_cache is None else use_cache
    country_for_cache = (country or cfg.geocode_country_suffix or "US").upper()
    cache_key = weather_cache_key(
        city,
        state,
        event_date,
        event_time,
        country_for_cache,
        geocode_query=geocode_query,
    )
    if lat is not None and lon is not None:
        cache_key = (
            f"wx:coords:{lat:.5f},{lon:.5f}:{event_date.isoformat()}:"
            f"{event_time.isoformat()}:{timezone_name or ''}"
        )

    def fetch():
        return _fetch_weather_uncached(
            city,
            state,
            event_date,
            event_time,
            cfg=cfg,
            ow_key=ow_key,
            tz_key=tz_key,
            use_cache=cache_on,
            lat=lat,
            lon=lon,
            country=country,
            geocode_query=geocode_query,
            timezone_name=timezone_name,
            usage=usage,
        )

    return get_or_fetch(cache_key, fetch, ttl_sec=cfg.weather_ttl_sec, enabled=cache_on)
