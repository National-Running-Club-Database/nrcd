"""Batch standardization and enrichment for tabular data (pandas)."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any

from nrcd.standardize.context import RaceContext
from nrcd.standardize.detail import StandardizeDetail
from nrcd.standardize.pipeline import standardize_seconds, standardize_seconds_detail

# RaceContext fields that may be supplied from a DataFrame row.
_CONTEXT_FIELDS: tuple[str, ...] = (
    "gender",
    "time_sec",
    "time_str",
    "event_name",
    "sport_name",
    "temperature",
    "dew_point",
    "temp_unit",
    "elevation_gain",
    "elevation_loss",
    "grade_input",
    "course_distance_m",
    "meet_elevation",
    "venue_elevation_unit",
    "reported_distance_m",
    "actual_distance_m",
    "reported_distance",
    "actual_distance",
    "distance_unit",
    "target_distance_m",
    "target_distance",
    "target_distance_unit",
    "lap_length_m",
    "banked",
    "venue_reference",
    "wind_mps",
    "barometric_pressure",
    "barometric_pressure_hpa",
    "city",
    "state",
    "country",
    "geocode_query",
    "latitude",
    "longitude",
    "timezone_name",
    "event_date",
    "event_time",
)

# Fields written back to the DataFrame after :func:`enrich_dataframe`.
_ENRICH_OUTPUT_FIELDS: tuple[str, ...] = (
    "meet_elevation",
    "temperature",
    "dew_point",
    "humidity",
    "real_feel",
    "barometric_pressure",
    "weather_conditions",
    "weather_description",
    "aqi",
    "aqi_co",
    "aqi_no",
    "aqi_no2",
    "aqi_o3",
    "aqi_so2",
    "aqi_pm2_5",
    "aqi_pm10",
    "aqi_nh3",
)

# Default DataFrame column names tried when ``column_map`` omits a field.
COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
    "gender": ("gender",),
    "time_sec": ("time_sec",),
    "time_str": ("time_str", "result_time"),
    "event_name": ("event_name",),
    "sport_name": ("sport_name",),
    "temperature": ("temperature",),
    "dew_point": ("dew_point",),
    "elevation_gain": ("elevation_gain",),
    "elevation_loss": ("elevation_loss",),
    "meet_elevation": ("meet_elevation", "altitude", "elevation"),
    "reported_distance_m": ("reported_distance_m",),
    "reported_distance": ("reported_distance",),
    "actual_distance_m": ("actual_distance_m", "estimated_course_distance"),
    "wind_mps": ("wind_mps", "wind"),
    "lap_length_m": ("lap_length_m",),
    "banked": ("banked",),
    "venue_reference": ("venue_reference", "track_reference"),
    "barometric_pressure": ("barometric_pressure", "barometric_pressure_hpa"),
    "city": ("city", "meet_city"),
    "state": ("state", "meet_state"),
    "country": ("country", "meet_country"),
    "latitude": ("latitude", "meet_latitude"),
    "longitude": ("longitude", "meet_longitude"),
    "event_date": ("event_date", "meet_date", "date"),
    "event_time": ("event_time", "meet_time", "start_time"),
    "geocode_query": ("geocode_query",),
    "timezone_name": ("timezone_name",),
}


@dataclass(frozen=True)
class DataframeBatchResult:
    """DataFrame batch output with optional enrich API accounting."""

    dataframe: Any
    api_usage: Any | None = None
    """Aggregate :class:`~nrcd.enrich.ApiUsage` when enrichment ran; ``None`` otherwise."""


def _require_pandas() -> Any:
    try:
        import pandas as pd
    except ImportError as exc:
        raise ImportError(
            'dataframe helpers require pandas: pip install "nrcd[data]"'
        ) from exc
    return pd


def resolve_column_map(
    columns: Any,
    column_map: dict[str, str] | None = None,
) -> dict[str, str]:
    """Map :class:`RaceContext` field names to DataFrame column names."""
    explicit = column_map or {}
    resolved: dict[str, str] = {}
    col_set = set(columns)
    for field in _CONTEXT_FIELDS:
        if field in explicit:
            resolved[field] = explicit[field]
            continue
        if field in col_set:
            resolved[field] = field
            continue
        for alias in COLUMN_ALIASES.get(field, ()):
            if alias in col_set:
                resolved[field] = alias
                break
    return resolved


def _is_na(value: Any) -> bool:
    if value is None:
        return True
    try:
        import pandas as pd

        return bool(pd.isna(value))
    except ImportError:
        return False


def _coerce_context_value(field: str, value: Any) -> Any:
    if _is_na(value):
        return None
    if field == "event_date":
        if isinstance(value, dt.datetime):
            return value.date()
        if isinstance(value, dt.date):
            return value
        if hasattr(value, "date") and callable(value.date):
            return value.date()
        if isinstance(value, str):
            return dt.date.fromisoformat(value.strip()[:10])
    if field == "event_time":
        if isinstance(value, dt.datetime):
            return value.time()
        if isinstance(value, dt.time):
            return value
        if hasattr(value, "time") and callable(value.time) and hasattr(value, "hour"):
            return value.time()
        if isinstance(value, str):
            s = value.strip()
            parts = s.split(":")
            if len(parts) == 3:
                h, m, sec = map(int, parts)
                return dt.time(h, m, sec)
            if len(parts) == 2:
                h, m = map(int, parts)
                return dt.time(h, m)
    return value


def row_to_race_context(row: Any, column_map: dict[str, str]) -> RaceContext:
    """Build a :class:`RaceContext` from one DataFrame row."""
    fields: dict[str, Any] = {}
    for field, col in column_map.items():
        if col not in row.index:
            continue
        value = _coerce_context_value(field, row[col])
        if value is None:
            continue
        fields[field] = value

    if "time_sec" not in fields and "time_str" not in fields:
        raise ValueError("row is missing time: map time_sec or time_str (e.g. result_time)")

    if "gender" not in fields:
        raise ValueError("row is missing gender")

    return RaceContext(**fields)


def _ctx_has_location(ctx: RaceContext) -> bool:
    if ctx.latitude is not None and ctx.longitude is not None:
        return True
    if ctx.geocode_query and str(ctx.geocode_query).strip():
        return True
    if ctx.city and str(ctx.city).strip():
        return True
    return False


def _enrich_row_flags(
    ctx: RaceContext,
    *,
    fetch_altitude: bool,
    fetch_weather: bool,
) -> tuple[bool, bool]:
    do_altitude = fetch_altitude and ctx.meet_elevation is None and _ctx_has_location(ctx)
    needs_weather = ctx.temperature is None or ctx.dew_point is None
    do_weather = (
        fetch_weather
        and needs_weather
        and ctx.event_date is not None
        and ctx.event_time is not None
        and _ctx_has_location(ctx)
    )
    return do_altitude, do_weather


def _output_column(df: Any, field: str, column_map: dict[str, str]) -> str:
    """DataFrame column to write for an enriched ``RaceContext`` field."""
    if field in column_map:
        return column_map[field]
    if field in df.columns:
        return field
    return field


def _write_context_fields_to_df(
    df: Any,
    idx: Any,
    ctx: RaceContext,
    column_map: dict[str, str],
    *,
    fields: tuple[str, ...] = _ENRICH_OUTPUT_FIELDS,
) -> None:
    for field in fields:
        value = getattr(ctx, field, None)
        if value is None:
            continue
        col = _output_column(df, field, column_map)
        if col not in df.columns:
            df[col] = None
        df.at[idx, col] = value


def enrich_dataframe(
    df: Any,
    *,
    column_map: dict[str, str] | None = None,
    config: Any | None = None,
    fetch_altitude: bool = True,
    fetch_weather: bool = True,
    usage: Any | None = None,
    return_usage: bool = False,
) -> Any:
    """Backfill meet altitude and weather on each row via :mod:`nrcd.enrich`.

    Requires ``pip install "nrcd[data,apis]"`` and API keys for weather.

    Rows that share the same location and ``event_date`` / ``event_time`` reuse
    the in-process enrich cache — e.g. 100 results at one meet typically trigger
    one weather lookup, not 100.

    Parameters
    ----------
    df
        Input DataFrame. Location and schedule columns map via :data:`COLUMN_ALIASES`
        (``meet_city``, ``meet_date``, ``meet_latitude``, …).
    column_map
        Optional ``{RaceContext_field: dataframe_column}`` overrides.
    config
        :class:`~nrcd.enrich.EnrichConfig` or ``None`` for env defaults.
    fetch_altitude, fetch_weather
        Steps to run when row data and location are sufficient.
    usage
        Optional :class:`~nrcd.enrich.ApiUsage` accumulator (HTTP calls only).
    return_usage
        When True, return :class:`DataframeBatchResult` with ``api_usage`` (cache
        misses only — use ``api_usage.openweather_total`` for OpenWeather calls).

    Returns
    -------
    pandas.DataFrame or DataframeBatchResult
        Copy of ``df`` with enriched columns updated. With ``return_usage=True``,
        also includes aggregate :class:`~nrcd.enrich.ApiUsage`.
    """
    pd = _require_pandas()
    if not isinstance(df, pd.DataFrame):
        raise TypeError("enrich_dataframe expects a pandas DataFrame")

    from nrcd.enrich.api_usage import ApiUsage
    from nrcd.enrich.config import EnrichConfig, api_keys_from_env
    from nrcd.enrich.context import enrich_race_context

    cfg = config or api_keys_from_env()
    if not isinstance(cfg, EnrichConfig):
        raise TypeError("config must be an EnrichConfig instance")

    call_usage = usage if usage is not None else ApiUsage()
    mapping = resolve_column_map(df.columns, column_map)
    out = df.copy()

    for idx in out.index:
        row = out.loc[idx]
        ctx = row_to_race_context(row, mapping)
        do_altitude, do_weather = _enrich_row_flags(
            ctx, fetch_altitude=fetch_altitude, fetch_weather=fetch_weather
        )
        if not do_altitude and not do_weather:
            continue
        enriched = enrich_race_context(
            ctx,
            config=cfg,
            fetch_altitude=do_altitude,
            fetch_weather_fields=do_weather,
            inplace=True,
            usage=call_usage,
        )
        _write_context_fields_to_df(out, idx, enriched, mapping)

    if return_usage:
        return DataframeBatchResult(dataframe=out, api_usage=call_usage)
    return out


def standardize_dataframe(
    df: Any,
    *,
    column_map: dict[str, str] | None = None,
    std_col: str = "std_time_sec",
    detail: bool = False,
    detail_col: str = "std_detail",
    enrich: bool = False,
    enrich_config: Any | None = None,
    fetch_altitude: bool = True,
    fetch_weather: bool = True,
    enrich_usage: Any | None = None,
    return_usage: bool = False,
) -> Any:
    """Standardize each row — map columns → :class:`RaceContext` → ``std_time_sec``.

    Requires ``pip install "nrcd[data]"`` (pandas). Pass ``enrich=True`` to
    backfill missing weather/altitude before standardizing
    (``pip install "nrcd[data,apis]"``).

    Parameters
    ----------
    df
        Input DataFrame. Column names are matched to :class:`RaceContext` fields
        directly, or via :data:`COLUMN_ALIASES` (e.g. ``result_time`` → ``time_str``,
        ``altitude`` → ``meet_elevation``).
    column_map
        Optional explicit ``{RaceContext_field: dataframe_column}`` overrides.
    std_col
        Output column name for standardized seconds (default ``std_time_sec``).
    detail
        When True, also store :class:`StandardizeDetail` per row in ``detail_col``.
    detail_col
        Column name for detail objects when ``detail=True``.
    enrich
        When True, run :func:`enrich_dataframe` on a copy before standardizing.
    enrich_config
        :class:`~nrcd.enrich.EnrichConfig` for enrichment (env keys if omitted).
    fetch_altitude, fetch_weather
        Passed to enrichment when ``enrich=True``.
    enrich_usage
        Optional :class:`~nrcd.enrich.ApiUsage` for enrichment HTTP accounting.
    return_usage
        When True, return :class:`DataframeBatchResult`. ``api_usage`` is set only
        when ``enrich=True`` (otherwise ``None``).

    Returns
    -------
    pandas.DataFrame or DataframeBatchResult
        Copy of ``df`` with ``std_col`` (and optionally ``detail_col``) appended.
    """
    pd = _require_pandas()
    if not isinstance(df, pd.DataFrame):
        raise TypeError("standardize_dataframe expects a pandas DataFrame")

    out = df.copy()
    batch_usage = None
    if enrich:
        if return_usage:
            enrich_out = enrich_dataframe(
                out,
                column_map=column_map,
                config=enrich_config,
                fetch_altitude=fetch_altitude,
                fetch_weather=fetch_weather,
                usage=enrich_usage,
                return_usage=True,
            )
            out = enrich_out.dataframe
            batch_usage = enrich_out.api_usage
        else:
            out = enrich_dataframe(
                out,
                column_map=column_map,
                config=enrich_config,
                fetch_altitude=fetch_altitude,
                fetch_weather=fetch_weather,
                usage=enrich_usage,
            )

    mapping = resolve_column_map(out.columns, column_map)
    std_values: list[float] = []
    detail_values: list[StandardizeDetail | None] = []

    for _, row in out.iterrows():
        ctx = row_to_race_context(row, mapping)
        if detail:
            d = standardize_seconds_detail(ctx)
            std_values.append(d.std_sec)
            detail_values.append(d)
        else:
            std_values.append(standardize_seconds(ctx))

    out[std_col] = std_values
    if detail:
        out[detail_col] = detail_values
    if return_usage:
        return DataframeBatchResult(dataframe=out, api_usage=batch_usage)
    return out
