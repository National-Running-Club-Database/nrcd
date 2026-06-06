"""Event name parsing and classification."""

from __future__ import annotations

import re

_MARATHON_M = 42195.0
_HALF_MARATHON_M = 21097.5
_METERS_PER_KM = 1000.0
_METERS_PER_MILE = 1609.34


def event_category(event_name: str) -> str:
    """sprint | mid_distance | distance | relay | field | other."""
    n = str(event_name).lower()

    if any(k in n for k in ("4x", "relay", "smr", "dmr", "swedish")):
        return "relay"

    if any(k in n for k in ("jump", "put", "throw", "vault", "discus", "javelin", "hammer")):
        return "field"

    if "hurdle" in n:
        return "sprint"

    if "steeple" in n:
        return "distance"

    if any(k in n for k in ("marathon", "half marathon", "10 mile", "14 mile")):
        return "distance"
    if re.search(r"\d+\s*mile|4 mile|5 mile|2 mile", n):
        return "distance"

    dist_m = re.search(r"(\d+)m", n)
    if dist_m:
        d = int(dist_m.group(1))
        if d <= 400:
            return "sprint"
        if d <= 1000:
            return "mid_distance"
        return "distance"

    if n in ("mile", "2 mile", "4 mile", "5 mile"):
        return "distance"

    if re.search(r"\d+(?:\.\d+)?\s*k(?:m)?\b", n):
        return "distance"

    return "other"


def parse_event_distance_m(event_name: str | None) -> float | None:
    """Distance in meters from event label (e.g. ``8000m``, ``110m Hurdles``)."""
    if event_name is None:
        return None
    event_name = str(event_name)
    lower = event_name.lower()
    if event_name.endswith("m"):
        try:
            return float(event_name.replace("m", "").strip())
        except ValueError:
            pass
    m = re.search(r"(\d+(?:\.\d+)?)\s*m", event_name, re.I)
    if m:
        return float(m.group(1))
    if lower in ("mile", "1 mile", "1600m"):
        return _METERS_PER_MILE
    if lower == "4 mile":
        return 4 * _METERS_PER_MILE
    if lower == "5 mile":
        return 5 * _METERS_PER_MILE
    if lower == "2 mile":
        return 2 * _METERS_PER_MILE
    if "half marathon" in lower:
        return _HALF_MARATHON_M
    if "ultra" in lower and "marathon" in lower:
        return None
    if "marathon" in lower:
        return _MARATHON_M
    k_match = re.search(r"(\d+(?:\.\d+)?)\s*k(?:m)?\b", lower)
    if k_match:
        return float(k_match.group(1)) * _METERS_PER_KM
    return None


def applies_altitude_conversion(event_name: str | None) -> bool:
    if event_name is None:
        return False
    if parse_event_distance_m(event_name) is None:
        return False
    cat = event_category(str(event_name))
    return cat not in ("field", "relay")
