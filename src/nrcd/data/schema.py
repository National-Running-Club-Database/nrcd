"""NRCD export column resolution and derived ``course_details`` fields."""

from __future__ import annotations

import math
from typing import Any, Mapping

from nrcd.standardize.factors import heat_index


def _is_na(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    try:
        import pandas as pd

        return bool(pd.isna(value))
    except ImportError:
        return False


def meet_altitude_column(df: Any) -> str:
    """Return meet-table altitude column name (``altitude`` or legacy ``elevation``)."""
    import pandas as pd

    if not isinstance(df, pd.DataFrame):
        raise TypeError("meet_altitude_column expects a pandas DataFrame")
    if "altitude" in df.columns:
        return "altitude"
    if "elevation" in df.columns:
        return "elevation"
    raise KeyError("meet table missing altitude/elevation column")


def _finite_altitude_ft(value: Any) -> float | None:
    if value is None:
        return None
    try:
        z = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(z) or z < 0:
        return None
    return z


def meet_altitude_ft_from_record(
    row: Mapping[str, Any] | Any,
    course_details: Mapping[str, Any] | None = None,
) -> float | None:
    """Meet venue altitude (ft) from merged result row or ``course_details.altitude``."""
    elev = None
    if hasattr(row, "get"):
        elev = row.get("altitude")
        if _is_na(elev):
            elev = row.get("elevation")
    if _is_na(elev):
        if course_details:
            elev = course_details.get("altitude") or course_details.get("meet_elevation")
            if elev is None:
                elev = course_details.get("elevation")
    return _finite_altitude_ft(elev)


def derive_course_details_fields(record: Mapping[str, Any]) -> dict[str, Any]:
    """Compute analysis fields not stored on ``course_details`` export rows."""
    out: dict[str, Any] = {}

    t = record.get("temperature")
    d = record.get("dew_point")
    h = heat_index(t, d)
    if h is not None:
        out["heat_index_f"] = h

    race_unix = record.get("openweather_dt_unix")
    sunrise = record.get("sunrise_unix")
    sunset = record.get("sunset_unix")
    if race_unix is not None and sunrise is not None and sunset is not None:
        try:
            race_u = int(race_unix)
            rise_u = int(sunrise)
            set_u = int(sunset)
        except (TypeError, ValueError):
            race_u = rise_u = set_u = None
        if race_u is not None:
            out["is_daylight"] = rise_u <= race_u <= set_u
            if rise_u is not None:
                out["minutes_after_sunrise"] = max(0.0, (race_u - rise_u) / 60.0)
            if set_u is not None:
                out["minutes_before_sunset"] = max(0.0, (set_u - race_u) / 60.0)

    return out
