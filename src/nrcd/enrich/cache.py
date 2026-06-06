"""In-memory TTL cache for enrich API responses (backfill-style deduplication)."""

from __future__ import annotations

import datetime as dt
import threading
import time
from typing import Any, Callable, TypeVar

T = TypeVar("T")

_lock = threading.Lock()
_store: dict[str, tuple[Any, float | None]] = {}
_stats = {"hits": 0, "misses": 0}


def _normalize_city_state(city: str, state: str) -> tuple[str, str]:
    return (city or "").strip().lower(), (state or "").strip().lower()


def geocode_cache_key(city: str, state: str, country: str = "US") -> str:
    c, s = _normalize_city_state(city, state)
    return f"geocode:{c}:{s}:{country.upper()}"


def altitude_cache_key(city: str, state: str, country: str = "US") -> str:
    c, s = _normalize_city_state(city, state)
    return f"altitude:{c}:{s}:{country.upper()}"


def timezone_cache_key(lat: float, lon: float) -> str:
    return f"tz:{round(lat, 4)}:{round(lon, 4)}"


def weather_cache_key(
    city: str,
    state: str,
    event_date: dt.date,
    event_time: dt.time,
    country: str = "US",
) -> str:
    c, s = _normalize_city_state(city, state)
    return f"weather:{c}:{s}:{country.upper()}:{event_date.isoformat()}:{event_time.isoformat()}"


def get_cached(key: str) -> Any | None:
    """Return cached value if present and not expired."""
    now = time.time()
    with _lock:
        entry = _store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if expires_at is not None and now >= expires_at:
            del _store[key]
            return None
        _stats["hits"] += 1
        return value


def set_cached(key: str, value: Any, ttl_sec: float | None) -> None:
    expires_at = None if ttl_sec is None else time.time() + ttl_sec
    with _lock:
        _store[key] = (value, expires_at)


def get_or_fetch(
    key: str,
    fetch: Callable[[], T],
    *,
    ttl_sec: float | None,
    enabled: bool = True,
) -> T:
    """Return cached value or call ``fetch``, store, and return."""
    if enabled:
        cached = get_cached(key)
        if cached is not None:
            return cached
    with _lock:
        _stats["misses"] += 1
    value = fetch()
    if enabled and value is not None:
        set_cached(key, value, ttl_sec)
    return value


def clear_enrich_cache() -> None:
    """Drop all cached enrich responses (tests / manual refresh)."""
    with _lock:
        _store.clear()
        _stats["hits"] = 0
        _stats["misses"] = 0


def cache_stats() -> dict[str, int]:
    with _lock:
        return {"hits": _stats["hits"], "misses": _stats["misses"], "entries": len(_store)}
