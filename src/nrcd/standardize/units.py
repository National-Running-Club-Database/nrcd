"""Unit conventions and conversions for NRCD standardization."""

from __future__ import annotations

import math
import re
from typing import Literal

from nrcd.standardize.validation import (
    validate_distance_unit,
)

TemperatureUnit = Literal["F", "C"]
VenueElevationUnit = Literal["ft", "m"]
GradeInput = Literal["percent", "feet", "m"]
DistanceUnit = Literal["m", "km", "mi"]

METERS_PER_KM = 1000.0
METERS_PER_MILE = 1609.34


def c_to_f(celsius: float) -> float:
    return celsius * 9.0 / 5.0 + 32.0


def f_to_c(fahrenheit: float) -> float:
    return (fahrenheit - 32.0) * 5.0 / 9.0


def feet_to_meters(feet: float) -> float:
    return feet * 0.3048


def meters_to_feet(meters: float) -> float:
    return meters / 0.3048


def temperature_to_fahrenheit(value: float | None, unit: TemperatureUnit) -> float | None:
    if value is None or not math.isfinite(value):
        return None
    return float(value) if unit == "F" else c_to_f(float(value))


def venue_elevation_to_feet(value: float | None, unit: VenueElevationUnit) -> float | None:
    if value is None or not math.isfinite(value) or value < 0:
        return None
    return float(value) if unit == "ft" else meters_to_feet(float(value))


def grade_percent_from_feet(
    gain_feet: float | None,
    loss_feet: float | None,
    course_distance_m: float | None,
) -> tuple[float | None, float | None]:
    """Convert vertical feet over a course to average grade percent (100 × rise / run)."""
    if course_distance_m is None or course_distance_m <= 0:
        return None, None
    gain_pct = None
    loss_pct = None
    if gain_feet is not None and math.isfinite(gain_feet):
        gain_pct = 100.0 * feet_to_meters(float(gain_feet)) / float(course_distance_m)
    if loss_feet is not None and math.isfinite(loss_feet):
        loss_pct = 100.0 * feet_to_meters(float(loss_feet)) / float(course_distance_m)
    return gain_pct, loss_pct


def grade_percent_from_meters(
    gain_m: float | None,
    loss_m: float | None,
    course_distance_m: float | None,
) -> tuple[float | None, float | None]:
    """Convert vertical meters over a course to average grade percent (100 × rise / run)."""
    if course_distance_m is None or course_distance_m <= 0:
        return None, None
    gain_pct = None
    loss_pct = None
    if gain_m is not None and math.isfinite(gain_m):
        gain_pct = 100.0 * float(gain_m) / float(course_distance_m)
    if loss_m is not None and math.isfinite(loss_m):
        loss_pct = 100.0 * float(loss_m) / float(course_distance_m)
    return gain_pct, loss_pct


def resolve_grade_percent(
    gain: float | None,
    loss: float | None,
    *,
    grade_input: GradeInput,
    course_distance_m: float | None,
) -> tuple[float | None, float | None]:
    """Normalize gain/loss to percent grade for :func:`elevation_factor`."""
    if grade_input == "percent":
        return gain, loss
    if grade_input == "m":
        return grade_percent_from_meters(gain, loss, course_distance_m)
    return grade_percent_from_feet(gain, loss, course_distance_m)


_DISTANCE_HELP = (
    "use a positive number with distance_unit='m'|'km'|'mi', "
    "or a label like '5k', '8000m', '8', '5 mile'"
)


def distance_to_meters(value: float, unit: DistanceUnit) -> float:
    """Convert a numeric distance to meters."""
    validate_distance_unit(unit)
    v = float(value)
    if not math.isfinite(v) or v <= 0:
        raise ValueError(f"invalid distance {value!r}: must be a positive finite number")
    if unit == "km":
        return v * METERS_PER_KM
    if unit == "mi":
        return v * METERS_PER_MILE
    return v


def parse_distance(
    value: float | int | str | None,
    *,
    unit: DistanceUnit = "m",
) -> float:
    """Parse distance labels (``5k``, ``8000m``, ``8``, ``5 mile``) to meters.

    Numeric values use ``unit`` (``m``, ``km``, or ``mi``). String labels with an
    explicit suffix ignore ``unit`` (e.g. ``"5k"`` → 5000 m).

    Raises
    ------
    ValueError
        If ``value`` or ``unit`` is invalid.
    """
    validate_distance_unit(unit)
    if value is None:
        raise ValueError(f"distance is required; {_DISTANCE_HELP}")

    if isinstance(value, (int, float)):
        return distance_to_meters(float(value), unit)

    s = str(value).strip().lower()
    if not s:
        raise ValueError(f"invalid distance {value!r}: empty string; {_DISTANCE_HELP}")

    from nrcd.standardize.events import parse_event_distance_m

    parsed = parse_event_distance_m(s)
    if parsed is not None:
        return parsed

    m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*k(?:m)?", s)
    if m:
        return float(m.group(1)) * METERS_PER_KM
    m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*mi(?:le)?s?", s)
    if m:
        return float(m.group(1)) * METERS_PER_MILE
    m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*m", s)
    if m:
        return float(m.group(1))

    try:
        v = float(s)
    except ValueError as exc:
        raise ValueError(f"invalid distance {value!r}; {_DISTANCE_HELP}") from exc
    return distance_to_meters(v, unit)
