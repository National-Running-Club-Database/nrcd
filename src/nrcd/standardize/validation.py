"""Input validation helpers with clear error messages."""

from __future__ import annotations

import math
from typing import TypeVar

T = TypeVar("T")


def _validate_choice(name: str, value: str, allowed: set[str]) -> None:
    if value not in allowed:
        opts = ", ".join(f"'{x}'" for x in sorted(allowed))
        raise ValueError(f"invalid {name} {value!r}: use {opts}")


def validate_distance_unit(unit: str) -> None:
    _validate_choice("distance_unit", unit, {"m", "km", "mi"})


def validate_temp_unit(unit: str) -> None:
    _validate_choice("temp_unit", unit, {"F", "C"})


def validate_venue_elevation_unit(unit: str) -> None:
    _validate_choice("venue_elevation_unit", unit, {"ft", "m"})


def validate_grade_input(grade_input: str) -> None:
    _validate_choice("grade_input", grade_input, {"percent", "feet", "m"})


def validate_positive_distance_m(value: float, *, field: str) -> None:
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"invalid {field} {value!r}: must be a positive finite distance in meters")


def validate_gender(gender: str) -> None:
    g = str(gender).strip().upper()
    if g not in ("M", "F", "MIXED"):
        raise ValueError(
            f"invalid gender {gender!r}: use 'M', 'F', or 'MIXED' (altitude averaging only)"
        )


def validate_standardize_gender(gender: str) -> None:
    """Require M or F for full standardization pipelines."""
    validate_gender(gender)
    if str(gender).strip().upper() == "MIXED":
        raise ValueError(
            "gender 'MIXED' is only supported for meet-altitude (Peronnet) helpers, "
            "not standardize_xc / standardize_result; use 'M' or 'F'"
        )
