"""Apply API lookups to :class:`~nrcd.standardize.context.RaceContext`."""

from __future__ import annotations

from dataclasses import replace

from nrcd.enrich.altitude import lookup_altitude_ft
from nrcd.enrich.api_usage import ApiUsage, EnrichResult
from nrcd.enrich.config import EnrichConfig, api_keys_from_env
from nrcd.enrich.geocode import build_geocode_query
from nrcd.enrich.weather import WeatherData, fetch_weather
from nrcd.standardize.context import RaceContext


def _has_geocode_location(ctx: RaceContext, cfg: EnrichConfig) -> bool:
    lat = getattr(ctx, "latitude", None)
    lon = getattr(ctx, "longitude", None)
    if lat is not None and lon is not None:
        return True
    city = getattr(ctx, "city", None)
    return build_geocode_query(
        city=city or "",
        state=getattr(ctx, "state", None) or "",
        country=getattr(ctx, "country", None),
        geocode_query=getattr(ctx, "geocode_query", None),
        default_country=cfg.geocode_country_suffix,
    ) is not None


def enrich_race_context(
    ctx: RaceContext,
    *,
    config: EnrichConfig | None = None,
    openweather_api_key: str | None = None,
    timezone_api_key: str | None = None,
    fetch_altitude: bool = True,
    fetch_weather_fields: bool = True,
    inplace: bool = True,
    usage: ApiUsage | None = None,
) -> RaceContext:
    """Fill meet altitude and weather from location (+ date/time).

    **Meet altitude** (``meet_elevation``, feet): geocode via ``city``/``state``,
    ``city``/``country``, ``geocode_query``, or ``latitude``/``longitude`` + USGS EPQS.

    **Weather + AQI:** same location fields plus ``event_date``, ``event_time``, and API keys.
    Pass ``latitude``/``longitude`` (and optionally ``timezone_name``) for global coords.

    Pass ``usage`` to accumulate :class:`~nrcd.enrich.ApiUsage` (HTTP calls only,
    not cache hits). See :func:`enrich_race_context_result` for context + usage
    in one object.

    See :data:`nrcd.enrich.API_GUIDE` for signup links.
    """
    result = enrich_race_context_result(
        ctx,
        config=config,
        openweather_api_key=openweather_api_key,
        timezone_api_key=timezone_api_key,
        fetch_altitude=fetch_altitude,
        fetch_weather_fields=fetch_weather_fields,
        inplace=inplace,
        usage=usage,
    )
    return result.context


def enrich_race_context_result(
    ctx: RaceContext,
    *,
    config: EnrichConfig | None = None,
    openweather_api_key: str | None = None,
    timezone_api_key: str | None = None,
    fetch_altitude: bool = True,
    fetch_weather_fields: bool = True,
    inplace: bool = True,
    usage: ApiUsage | None = None,
) -> EnrichResult:
    """Like :func:`enrich_race_context` but always returns context and API usage."""
    cfg = config or api_keys_from_env()
    if openweather_api_key:
        cfg = replace(cfg, openweather_api_key=openweather_api_key)
    if timezone_api_key:
        cfg = replace(cfg, timezone_api_key=timezone_api_key)

    call_usage = usage if usage is not None else ApiUsage()
    city = getattr(ctx, "city", None)
    state = getattr(ctx, "state", None)
    country = getattr(ctx, "country", None)
    geocode_query = getattr(ctx, "geocode_query", None)
    lat = getattr(ctx, "latitude", None)
    lon = getattr(ctx, "longitude", None)
    tz_name = getattr(ctx, "timezone_name", None)
    updates: dict = {}

    if fetch_altitude and ctx.meet_elevation is None:
        if lat is None or lon is None:
            if not _has_geocode_location(ctx, cfg):
                raise ValueError(
                    "meet altitude lookup requires city and state, city and country, "
                    "geocode_query, or latitude and longitude on RaceContext"
                )
        alt_ft = lookup_altitude_ft(
            city or "",
            state or "",
            config=cfg,
            openweather_api_key=cfg.openweather_api_key,
            lat=lat,
            lon=lon,
            country=country,
            geocode_query=geocode_query,
            usage=call_usage,
        )
        if alt_ft is not None:
            updates["meet_elevation"] = float(alt_ft)

    event_date = getattr(ctx, "event_date", None)
    event_time = getattr(ctx, "event_time", None)
    if fetch_weather_fields and (ctx.temperature is None or ctx.dew_point is None):
        if not event_date or not event_time:
            raise ValueError(
                "weather lookup requires event_date and event_time on RaceContext "
                "(datetime.date and datetime.time)"
            )
        if not _has_geocode_location(ctx, cfg):
            raise ValueError(
                "weather lookup requires city and state, city and country, geocode_query, "
                "or latitude and longitude on RaceContext"
            )
        wx = fetch_weather(
            city or "",
            state or "",
            event_date,
            event_time,
            config=cfg,
            openweather_api_key=cfg.openweather_api_key,
            timezone_api_key=cfg.timezone_api_key,
            lat=lat,
            lon=lon,
            country=country,
            geocode_query=geocode_query,
            timezone_name=tz_name,
            usage=call_usage,
        )
        if wx:
            _apply_weather(updates, wx, ctx)

    if not updates:
        out_ctx = ctx
    elif inplace:
        for k, v in updates.items():
            setattr(ctx, k, v)
        out_ctx = ctx
    else:
        out_ctx = replace(ctx, **updates)

    return EnrichResult(context=out_ctx, api_usage=call_usage)


def _apply_weather(updates: dict, wx: WeatherData, ctx: RaceContext) -> None:
    mapping = {
        "temperature": "temperature",
        "real_feel": "real_feel",
        "dew_point": "dew_point",
        "humidity": "humidity",
        "weather_conditions": "weather_conditions",
        "weather_description": "weather_description",
        "aqi": "aqi",
        "aqi_co": "aqi_co",
        "aqi_no": "aqi_no",
        "aqi_no2": "aqi_no2",
        "aqi_o3": "aqi_o3",
        "aqi_so2": "aqi_so2",
        "aqi_pm2_5": "aqi_pm2_5",
        "aqi_pm10": "aqi_pm10",
        "aqi_nh3": "aqi_nh3",
        "barometric_pressure": "barometric_pressure",
    }
    for src, attr in mapping.items():
        if getattr(ctx, attr, None) is not None:
            continue
        val = getattr(wx, src, None)
        if val is not None:
            updates[attr] = val
