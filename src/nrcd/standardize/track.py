"""NCAA indoor track facility indexing (lap type, banking, venue reference)."""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Literal

from nrcd.standardize.config import StandardizeConfig
from nrcd.standardize.events import event_category, parse_event_distance_m
from nrcd.standardize.sport import is_indoor_track as is_indoor_sport

IndexKind = Literal["flat_to_banked", "undersized_to_flat", "undersized_to_banked"]

TrackVenueReference = Literal["banked_oversized", "indoor_flat", "outdoor_flat_400m"]

TrackSourceType = Literal["undersized", "flat", "banked_oversized", "outdoor_400_flat"]

TRACK_VENUE_REFERENCES: tuple[TrackVenueReference, ...] = (
    "banked_oversized",
    "indoor_flat",
    "outdoor_flat_400m",
)

# NCAA indoor conversion charts (USTFCCCA / NCAA facility indexing).
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
_UNDERSIZED_TO_BANKED: dict[str, tuple[tuple[int, float], ...]] = {
    "M": (
        (200, 0.9698),
        (400, 0.9746),
        (800, 0.9783),
        (1000, 0.9794),
        (1609, 0.9816),
        (3000, 0.9839),
        (5000, 0.9855),
    ),
    "F": (
        (200, 0.9749),
        (400, 0.9799),
        (800, 0.9838),
        (1000, 0.9850),
        (1609, 0.9871),
        (3000, 0.9896),
        (5000, 0.9913),
    ),
}

_INDOOR_REFERENCE_LAP_M = 200.0


def _gender_key(gender: str) -> str:
    return "F" if str(gender).upper() == "F" else "M"


def _nearest_row(distance_m: float, rows: tuple[tuple[int, float], ...]) -> float:
    return min(rows, key=lambda row: abs(row[0] - distance_m))[1]


def ncaa_index_multiplier(
    event_distance_m: float,
    gender: str,
    kind: IndexKind,
) -> float:
    """Return NCAA chart factor alpha for ``t_target = t_source * alpha``."""
    g = _gender_key(gender)
    if kind == "flat_to_banked":
        rows = _FLAT_TO_BANKED[g]
    elif kind == "undersized_to_flat":
        rows = _UNDERSIZED_TO_FLAT[g]
    else:
        rows = _UNDERSIZED_TO_BANKED[g]
    return _nearest_row(event_distance_m, rows)


def banked_oversized_to_flat_multiplier(event_distance_m: float, gender: str) -> float:
    """NCAA banked/oversized → indoor 200 m flat."""
    return 1.0 / ncaa_index_multiplier(event_distance_m, gender, "flat_to_banked")


def default_venue_reference(*, indoor: bool) -> TrackVenueReference:
    """Sport default: indoor → banked/oversized; outdoor → outdoor 400 m flat."""
    return "banked_oversized" if indoor else "outdoor_flat_400m"


def resolve_venue_reference(
    venue_reference: TrackVenueReference | str | None,
    *,
    indoor: bool,
) -> TrackVenueReference:
    if venue_reference is None:
        return default_venue_reference(indoor=indoor)
    ref = str(venue_reference).strip().lower()
    aliases = {
        "banked": "banked_oversized",
        "banked_oversized": "banked_oversized",
        "banked/oversized": "banked_oversized",
        "indoor_flat": "indoor_flat",
        "flat": "indoor_flat",
        "outdoor_flat": "outdoor_flat_400m",
        "outdoor_flat_400m": "outdoor_flat_400m",
        "outdoor_400m": "outdoor_flat_400m",
    }
    if ref not in aliases:
        raise ValueError(
            f"unknown venue_reference {venue_reference!r}; "
            f"use one of {list(TRACK_VENUE_REFERENCES)}"
        )
    return aliases[ref]  # type: ignore[return-value]


def _parse_banked(banked: object) -> bool:
    if banked is None:
        return False
    if isinstance(banked, bool):
        return banked
    s = str(banked).strip().lower()
    return s in ("1", "true", "yes", "y", "banked", "bt")


def infer_track_source_type(
    lap_length_m: float | None,
    *,
    banked: object = None,
    indoor: bool,
    outdoor_reference_lap_m: float = 400.0,
) -> TrackSourceType | None:
    """Infer NCAA track category from lap length and banking."""
    if lap_length_m is None or lap_length_m <= 0:
        return None
    lap = float(lap_length_m)
    if not indoor:
        if abs(lap - outdoor_reference_lap_m) <= 1e-9:
            return "outdoor_400_flat"
        if lap < _INDOOR_REFERENCE_LAP_M:
            return "undersized"
        return "banked_oversized"
    if lap < _INDOOR_REFERENCE_LAP_M:
        return "undersized"
    if lap <= _INDOOR_REFERENCE_LAP_M + 1e-9:
        return "banked_oversized" if _parse_banked(banked) else "flat"
    return "banked_oversized"


def venue_reference_factor(
    event_distance_m: float,
    gender: str,
    *,
    source_type: TrackSourceType,
    venue_reference: TrackVenueReference,
) -> float:
    """Convert from ``source_type`` venue to ``venue_reference`` (t_ref = t_raw * factor)."""
    u2b = ncaa_index_multiplier(event_distance_m, gender, "undersized_to_banked")
    u2f = ncaa_index_multiplier(event_distance_m, gender, "undersized_to_flat")
    f2b = ncaa_index_multiplier(event_distance_m, gender, "flat_to_banked")
    b2f = banked_oversized_to_flat_multiplier(event_distance_m, gender)

    matrix: dict[tuple[TrackSourceType, TrackVenueReference], float] = {
        ("undersized", "banked_oversized"): u2b,
        ("undersized", "indoor_flat"): u2f,
        ("undersized", "outdoor_flat_400m"): u2f,
        ("flat", "banked_oversized"): f2b,
        ("flat", "indoor_flat"): 1.0,
        ("flat", "outdoor_flat_400m"): 1.0,
        ("banked_oversized", "banked_oversized"): 1.0,
        ("banked_oversized", "indoor_flat"): b2f,
        ("banked_oversized", "outdoor_flat_400m"): b2f,
        ("outdoor_400_flat", "banked_oversized"): f2b,
        ("outdoor_400_flat", "indoor_flat"): b2f,
        ("outdoor_400_flat", "outdoor_flat_400m"): 1.0,
    }
    return matrix[(source_type, venue_reference)]


def infer_indoor_track_type(
    lap_length_m: float | None,
    *,
    banked: object = None,
) -> TrackSourceType | None:
    """Indoor-only wrapper for :func:`infer_track_source_type`."""
    return infer_track_source_type(lap_length_m, banked=banked, indoor=True)


def indoor_track_type_factor(
    event_distance_m: float,
    gender: str,
    track_type: TrackSourceType,
    *,
    venue_reference: TrackVenueReference = "banked_oversized",
) -> float:
    return venue_reference_factor(
        event_distance_m,
        gender,
        source_type=track_type,
        venue_reference=venue_reference,
    )


def track_venue_factor(
    event_name: str | None,
    gender: str,
    *,
    lap_length_m: float | None = None,
    banked: object = None,
    sport_name: str | None = None,
    venue_reference: TrackVenueReference | str | None = None,
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
    ref = resolve_venue_reference(venue_reference, indoor=indoor)
    source = infer_track_source_type(
        lap_length_m,
        banked=banked,
        indoor=indoor,
        outdoor_reference_lap_m=cfg.track_outdoor_reference_lap_m,
    )
    if source is None:
        return 1.0
    return venue_reference_factor(
        d,
        gender,
        source_type=source,
        venue_reference=ref,
    )


def track_length_factor(
    event_distance_m: float,
    gender: str,
    *,
    lap_length_m: float | None,
    indoor: bool,
    outdoor_reference_lap_m: float = 400.0,
    banked: object = None,
    venue_reference: TrackVenueReference | str | None = None,
) -> float:
    """Venue factor for lap length; delegates to :func:`track_venue_factor` logic."""
    sport_name = "Indoor Track" if indoor else "Outdoor Track"
    event = f"{event_distance_m:g}m"
    return track_venue_factor(
        event,
        gender,
        lap_length_m=lap_length_m,
        banked=banked,
        sport_name=sport_name,
        venue_reference=venue_reference,
    )


def track_banking_factor(
    event_distance_m: float,
    gender: str,
    *,
    banked: object,
    indoor: bool,
) -> float:
    """Banking is encoded in :func:`infer_track_source_type`; no separate multiplier."""
    return 1.0


def apply_track_venue(
    time_sec: float,
    event_name: str | None,
    gender: str,
    *,
    lap_length_m: float | None = None,
    banked: object = None,
    sport_name: str | None = None,
    venue_reference: TrackVenueReference | str | None = None,
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
        venue_reference=venue_reference,
        config=config,
    )
    return time_sec * f


def compare_venue_references(
    time: float | int | str,
    *,
    gender: str,
    event_name: str,
    sport_name: str,
    references: Sequence[TrackVenueReference | str] | None = None,
    lap_length_m: float | None = None,
    banked: object = None,
    config: StandardizeConfig | None = None,
    **standardize_kwargs: object,
) -> dict[str, float]:
    """Standardize the same result to multiple venue references for comparison.

    Returns a dict keyed by reference name, e.g.::

        {
            "banked_oversized": 22.565,
            "indoor_flat": 22.97,
            "outdoor_flat_400m": 22.97,
        }

    Pass ``references`` to compare a subset; default is all
    :data:`TRACK_VENUE_REFERENCES`.
    """
    from nrcd.standardize.pipeline import standardize_result

    refs = list(references) if references is not None else list(TRACK_VENUE_REFERENCES)
    out: dict[str, float] = {}
    for ref in refs:
        key = resolve_venue_reference(ref, indoor=is_indoor_sport(sport_name))
        out[key] = standardize_result(
            time,
            gender=gender,
            event_name=event_name,
            sport_name=sport_name,
            lap_length_m=lap_length_m,
            banked=banked,
            venue_reference=key,
            config=config,
            **standardize_kwargs,  # type: ignore[arg-type]
        )
    return out


def venue_reference_factor_table(
    event_name: str,
    gender: str,
    *,
    lap_length_m: float | None,
    banked: object = None,
    sport_name: str,
    references: Sequence[TrackVenueReference | str] | None = None,
    config: StandardizeConfig | None = None,
) -> dict[str, float]:
    """Venue-only multipliers (no weather/grade/altitude) per reference."""
    cfg = config or StandardizeConfig()
    refs = list(references) if references is not None else list(TRACK_VENUE_REFERENCES)
    d = parse_event_distance_m(event_name)
    if d is None:
        raise ValueError(f"cannot parse event distance from {event_name!r}")
    indoor = is_indoor_sport(sport_name)
    source = infer_track_source_type(
        lap_length_m,
        banked=banked,
        indoor=indoor,
        outdoor_reference_lap_m=cfg.track_outdoor_reference_lap_m,
    )
    if source is None:
        return {resolve_venue_reference(r, indoor=indoor): 1.0 for r in refs}
    return {
        resolve_venue_reference(r, indoor=indoor): venue_reference_factor(
            d,
            gender,
            source_type=source,
            venue_reference=resolve_venue_reference(r, indoor=indoor),
        )
        for r in refs
    }
