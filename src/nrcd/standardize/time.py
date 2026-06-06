"""Parse and format race clock strings."""

from __future__ import annotations

import math

_TIME_HELP = "use H:MM:SS, MM:SS, or seconds (e.g. '22:15', '4:12.00', '10.52')"


def parse_time(time_str: str | float | int | None) -> float:
    """Parse H:MM:SS, MM:SS, or numeric seconds.

    Raises
    ------
    ValueError
        If ``time_str`` is missing, empty, or not a valid race time.
    """
    if time_str is None:
        raise ValueError(f"time is required; {_TIME_HELP}")
    if isinstance(time_str, (int, float)):
        t = float(time_str)
        if not math.isfinite(t) or t < 0:
            raise ValueError(f"invalid time {time_str!r}: must be a non-negative finite number of seconds")
        return t

    s = str(time_str).strip()
    if not s:
        raise ValueError(f"invalid time {time_str!r}: empty string; {_TIME_HELP}")

    parts = s.split(":")
    try:
        if len(parts) == 3:
            h, m, sec = map(float, parts)
            if h < 0 or m < 0 or sec < 0:
                raise ValueError
            return h * 3600.0 + m * 60.0 + sec
        if len(parts) == 2:
            m, sec = map(float, parts)
            if m < 0 or sec < 0:
                raise ValueError
            return m * 60.0 + sec
        if len(parts) == 1:
            t = float(s)
            if not math.isfinite(t) or t < 0:
                raise ValueError
            return t
    except ValueError as exc:
        if exc.args and "invalid time" in str(exc.args[0]):
            raise
        raise ValueError(f"invalid time string {time_str!r}; {_TIME_HELP}") from exc

    raise ValueError(f"invalid time string {time_str!r}; {_TIME_HELP}")


def format_time(seconds: float) -> str:
    if not math.isfinite(seconds) or seconds < 0:
        return ""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    sec = seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{sec:05.2f}"
    if minutes > 0:
        return f"{minutes}:{sec:05.2f}"
    return f"{sec:05.2f}"
