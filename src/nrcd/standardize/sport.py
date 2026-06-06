"""Sport name conventions (NRCD ``sport.name`` strings).

Wind and track-venue corrections **only apply when ``sport_name`` matches** the
expected substring rules below. Missing or wrong ``sport_name`` silently skips
those steps (factor = 1.0), which is a common integration bug.
"""

from __future__ import annotations

from typing import Literal

PipelineKind = Literal["xc", "track", "road", "other"]


def normalize_sport_name(sport_name: str | None) -> str:
    return "" if sport_name is None else str(sport_name).strip()


def is_cross_country(sport_name: str | None) -> bool:
    """True for NRCD Cross Country (``sport_id`` 1 in exports)."""
    s = normalize_sport_name(sport_name).lower()
    return ("cross" in s and "country" in s) or s == "xc"


def is_indoor_track(sport_name: str | None) -> bool:
    """True when NCAA lap/bank indexing may apply."""
    return "indoor" in normalize_sport_name(sport_name).lower()


def is_outdoor_track(sport_name: str | None) -> bool:
    """True when sprint wind correction may apply."""
    s = normalize_sport_name(sport_name).lower()
    return "outdoor" in s and "track" in s


def is_track(sport_name: str | None) -> bool:
    s = normalize_sport_name(sport_name).lower()
    return "track" in s


def pipeline_kind(sport_name: str | None) -> PipelineKind:
    """Which high-level standardization path to use."""
    if is_cross_country(sport_name):
        return "xc"
    if is_track(sport_name):
        return "track"
    s = normalize_sport_name(sport_name).lower()
    if "road" in s or "marathon" in s:
        return "road"
    return "other"
