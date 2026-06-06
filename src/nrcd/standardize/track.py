"""NCAA track venue indexing (lap length, banking)."""

from __future__ import annotations

import math
from typing import Literal

from nrcd.standardize.config import StandardizeConfig
from nrcd.standardize.events import event_category, parse_event_distance_m

IndexKind = Literal["flat_to_banked", "undersized_to_flat"]

_FLAT_TO_BANKED: dict[str, tuple[tuple[int, float], ...]] = {
    "M": (
        (200, 0.9824),
        (300, 0.9835),
        (400, 0.9843),
        (500, 0.9848),
        (600, 0.9852),
        (800, 0.9859),
        (1000, 0.9864),
        (1500, 0.9872),
        (1609, 0.9874),
        (3000, 0.9885),
        (5000, 0.9894),
    ),
    "F": (
        (200, 0.9847),
        (300, 0.9860),
        (400, 0.9869),
        (500, 0.9874),
        (600, 0.9879),
        (800, 0.9886),
        (1000, 0.9892),
        (1500, 0.9901),
        (1609, 0.9902),
        (3000, 0.9915),
        (5000, 0.9924),
    ),
}
_UNDERSIZED_TO_FLAT: dict[str, tuple[tuple[int, float], ...]] = {
    "M": (
        (200, 0.9872),
        (400, 0.9901),
        (800, 0.9923),
        (1000, 0.9929),
        (1609, 0.9941),
        (3000, 0.9953),
        (5000, 0.9961),
    ),
    "F": (
        (200, 0.9900),
        (400, 0.9929),
        (800, 0.9951),
        (1000, 0.9958),
        (1609, 0.9969),
        (3000, 0.9981),
        (5000, 0.9989),
    ),
}


def _gender_key(gender: str) -> str:
    return "F" if str(gender).upper() == "F" else "M"


def _nearest_row(distance_m: float, rows: tuple[tuple[int, float], ...]) -> float:
    return min(rows, key=lambda row: abs(row[0] - distance_m))[1]


def ncaa_index_multiplier(
    event_distance_m: float,
    gender: str,
    kind: IndexKind,
) -> float:
    g = _gender_key(gender)
    rows = _FLAT_TO_BANKED[g] if kind == "flat_to_banked" else _UNDERSIZED_TO_FLAT[g]
    return _nearest_row(event_distance_m, rows)


def oversized_to_flat_multiplier(event_distance_m: float, gender: str) -> float:
    return 1.0 / ncaa_index_multiplier(event_distance_m, gender, "flat_to_banked")


def _parse_banked(banked: object) -> bool:
    if banked is None:
        return False
    if isinstance(banked, bool):
        return banked
    s = str(banked).strip().lower()
    return s in ("1", "true", "yes", "y", "banked", "bt")


from nrcd.standardize.sport import is_indoor_track as is_indoor_sport


def track_length_factor(
    event_distance_m: float,
    gender: str,
    *,
    lap_length_m: float | None,
    indoor: bool,
    outdoor_reference_lap_m: float = 400.0,
) -> float:
    """f_len: NCAA α(D); unity on standard outdoor 400 m lap."""
    if event_distance_m <= 0 or lap_length_m is None or lap_length_m <= 0:
        return 1.0
    if not indoor and lap_length_m == outdoor_reference_lap_m:
        return 1.0
    d = float(event_distance_m)
    if lap_length_m < 200.0:
        c_us = ncaa_index_multiplier(d, gender, "undersized_to_flat")
        return 1.0 / c_us
    return oversized_to_flat_multiplier(d, gender)


def track_banking_factor(
    event_distance_m: float,
    gender: str,
    *,
    banked: object,
    indoor: bool,
) -> float:
    if event_distance_m <= 0 or not _parse_banked(banked) or not indoor:
        return 1.0
    c_fb = ncaa_index_multiplier(float(event_distance_m), gender, "flat_to_banked")
    return 1.0 / c_fb


def track_venue_factor(
    event_name: str | None,
    gender: str,
    *,
    lap_length_m: float | None = None,
    banked: object = None,
    sport_name: str | None = None,
    config: StandardizeConfig | None = None,
) -> float:
    cfg = config or StandardizeConfig()
    if event_name is None:
        return 1.0
    if event_category(str(event_name)) in ("field", "relay", "other"):
        return 1.0
    d = parse_event_distance_m(event_name)
    if d is None:
        return 1.0
    indoor = is_indoor_sport(sport_name)
    f_len = track_length_factor(
        d,
        gender,
        lap_length_m=lap_length_m,
        indoor=indoor,
        outdoor_reference_lap_m=cfg.track_outdoor_reference_lap_m,
    )
    f_bank = track_banking_factor(d, gender, banked=banked, indoor=indoor)
    return f_len * f_bank


def apply_track_venue(
    time_sec: float,
    event_name: str | None,
    gender: str,
    *,
    lap_length_m: float | None = None,
    banked: object = None,
    sport_name: str | None = None,
    config: StandardizeConfig | None = None,
) -> float:
    if not math.isfinite(time_sec) or time_sec <= 0:
        return time_sec
    f = track_venue_factor(
        event_name,
        gender,
        lap_length_m=lap_length_m,
        banked=banked,
        sport_name=sport_name,
        config=config,
    )
    return time_sec * f
