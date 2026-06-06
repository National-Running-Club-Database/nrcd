"""Load optional local API keys from repo-root ``local_api_keys.env`` (gitignored)."""

from __future__ import annotations

import datetime as dt
import os
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_LOCAL_KEYS_FILE = _REPO_ROOT / "local_api_keys.env"

# OpenWeather Air Pollution history earliest date (also in nrcd.enrich.api_usage).
AQI_HISTORY_START = dt.date(2020, 11, 27)

_KEY_VARS = frozenset({"NRCD_OPENWEATHER_API_KEY", "NRCD_TIMEZONE_API_KEY"})

_PLACEHOLDER_VALUES = frozenset(
    {
        "",
        "your_key",
        "your_key_here",
        "paste_key_here",
        "your_openweather_key",
        "your_timezone_key",
        "changeme",
        "xxx",
    }
)


def _normalize_api_key(value: str | None) -> str | None:
    if value is None:
        return None
    key = value.strip().strip('"').strip("'")
    if not key or key.lower() in _PLACEHOLDER_VALUES:
        return None
    return key


def _parse_local_api_keys(path: Path | None = None) -> dict[str, str]:
    """Parse ``KEY=value`` lines; empty values are stored as ``""``."""
    env_path = path or _LOCAL_KEYS_FILE
    if not env_path.is_file():
        return {}
    out: dict[str, str] = {}
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key:
            out[key] = value.strip().strip('"').strip("'")
    return out


def load_local_api_keys(path: Path | None = None) -> dict[str, str]:
    """Non-empty key/value pairs only (for setting env defaults)."""
    return {k: v for k, v in _parse_local_api_keys(path).items() if _normalize_api_key(v)}


def apply_local_api_keys() -> None:
    """Set env vars from ``local_api_keys.env`` when not already defined."""
    for key, value in load_local_api_keys().items():
        os.environ.setdefault(key, value)


def _api_key(name: str) -> str | None:
    """Resolve an API key; ``local_api_keys.env`` overrides env when the file exists."""
    if _LOCAL_KEYS_FILE.is_file() and name in _parse_local_api_keys():
        return _normalize_api_key(_parse_local_api_keys()[name])
    return _normalize_api_key(os.environ.get(name))


def openweather_api_key() -> str | None:
    return _api_key("NRCD_OPENWEATHER_API_KEY")


def timezone_api_key() -> str | None:
    return _api_key("NRCD_TIMEZONE_API_KEY")


def live_api_keys_configured() -> bool:
    return openweather_api_key() is not None


def live_test_city() -> str:
    apply_local_api_keys()
    return os.environ.get("NRCD_LIVE_TEST_CITY", "Notre Dame")


def live_test_state() -> str:
    apply_local_api_keys()
    return os.environ.get("NRCD_LIVE_TEST_STATE", "IN")


def live_test_date() -> dt.date:
    apply_local_api_keys()
    raw = os.environ.get("NRCD_LIVE_TEST_DATE", "2024-10-12")
    return dt.date.fromisoformat(raw)


def live_test_time() -> dt.time:
    apply_local_api_keys()
    raw = os.environ.get("NRCD_LIVE_TEST_TIME", "10:00")
    hour, minute = raw.split(":", 1)
    return dt.time(int(hour), int(minute))
