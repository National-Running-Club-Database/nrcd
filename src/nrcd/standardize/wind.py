"""Outdoor sprint wind corrections (event-specific, not D/100 scaling)."""

from __future__ import annotations

import math

from nrcd.standardize.config import StandardizeConfig
from nrcd.standardize.events import event_category, parse_event_distance_m

_TAIL_GAIN_AT_2MPS: dict[tuple[int, str], float] = {
    (100, "M"): 0.101,
    (100, "F"): 0.110,
    (110, "M"): 0.190,
    (110, "F"): 0.200,
    (200, "M"): 0.112,
    (200, "F"): 0.123,
    (400, "M"): 0.090,
    (400, "F"): 0.100,
}

_HEAD_LOSS_AT_2MPS: dict[tuple[int, str], float] = {
    (100, "M"): 0.121,
    (100, "F"): 0.134,
    (110, "M"): 0.125,
    (110, "F"): 0.138,
    (200, "M"): 0.121,
    (200, "F"): 0.135,
    (400, "M"): 0.130,
    (400, "F"): 0.140,
}


def _gender_key(gender: str) -> str:
    return "F" if str(gender).upper() == "F" else "M"


def wind_event_bucket_m(event_distance_m: float) -> int:
    d = float(event_distance_m)
    if d <= 105:
        return 100
    if d <= 115:
        return 110
    if d <= 205:
        return 200
    return 400


def wind_delta_seconds_at_speed(
    wind_mps: float,
    event_distance_m: float,
    gender: str,
    *,
    cap_mps: float = 2.0,
) -> float:
    """Calm-equivalent Δt; linear in |w| with reference tables at 2 m/s, clamped to ±cap_mps."""
    if event_distance_m <= 0:
        return 0.0
    bucket = wind_event_bucket_m(event_distance_m)
    g = _gender_key(gender)
    w = float(wind_mps)
    if abs(w) > cap_mps:
        w = cap_mps if w > 0 else -cap_mps
    if w >= 0:
        return _TAIL_GAIN_AT_2MPS[(bucket, g)] * (w / 2.0)
    return _HEAD_LOSS_AT_2MPS[(bucket, g)] * (abs(w) / 2.0)


def parse_wind_mps(wind: object) -> float | None:
    """Parse wind (m/s); positive = tailwind."""
    if wind is None:
        return None
    if isinstance(wind, (int, float)):
        w = float(wind)
        return w if math.isfinite(w) else None
    s = str(wind).strip().replace("+", "")
    if not s or s.lower() in ("n/a", "na", "none"):
        return None
    try:
        w = float(s)
    except (TypeError, ValueError):
        return None
    return w if math.isfinite(w) else None


from nrcd.standardize.sport import is_outdoor_track  # noqa: F401 — re-export


def applies_wind_conversion(event_name: str | None, sport_name: str | None) -> bool:
    if not is_outdoor_track(sport_name):
        return False
    if event_name is None:
        return False
    return event_category(str(event_name)) == "sprint"


def wind_calm_equivalent_seconds(
    time_sec: float,
    wind_mps: float,
    event_distance_m: float,
    gender: str,
    *,
    config: StandardizeConfig | None = None,
) -> float:
    cfg = config or StandardizeConfig()
    if not math.isfinite(time_sec) or time_sec <= 0:
        return time_sec
    w = float(wind_mps)
    cap = cfg.wind_max_mps
    if abs(w) > cap:
        w = math.copysign(cap, w)
    delta = wind_delta_seconds_at_speed(w, event_distance_m, gender, cap_mps=cap)
    return float(time_sec) + delta


def apply_wind(
    time_sec: float,
    event_name: str | None,
    gender: str,
    wind_mps: object,
    sport_name: str | None = None,
    *,
    config: StandardizeConfig | None = None,
) -> float:
    if not applies_wind_conversion(event_name, sport_name):
        return time_sec
    w = parse_wind_mps(wind_mps)
    if w is None:
        return time_sec
    d = parse_event_distance_m(event_name)
    if d is None:
        return time_sec
    return wind_calm_equivalent_seconds(time_sec, w, d, gender, config=config)
