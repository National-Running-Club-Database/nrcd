"""Per-provider request spacing (matches NRCD backfill behavior)."""

from __future__ import annotations

import threading
import time

_lock = threading.Lock()
_last_call: dict[str, float] = {}


def wait_for_provider(provider: str, min_interval_sec: float) -> None:
    """Block until at least ``min_interval_sec`` since the last call for ``provider``.

    TimeZoneDB free tier: use 1.5s (same as ``utils.get_timezone`` in the NRCD app).
    Pass 0 to disable spacing for that provider.
    """
    if min_interval_sec <= 0:
        return
    with _lock:
        last = _last_call.get(provider)
        if last is not None:
            elapsed = time.time() - last
            if elapsed < min_interval_sec:
                time.sleep(min_interval_sec - elapsed)
        _last_call[provider] = time.time()


def reset_throttle_state() -> None:
    """Clear throttle timers (for tests)."""
    with _lock:
        _last_call.clear()
