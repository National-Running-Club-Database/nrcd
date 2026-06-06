"""Count outbound HTTP calls during enrich lookups (cache misses only)."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

# OpenWeather Air Pollution history: earliest date per provider docs.
AQI_HISTORY_AVAILABLE_FROM = dt.date(2020, 11, 27)
AQI_HISTORY_AVAILABLE_UNIX = int(
    dt.datetime(2020, 11, 27, 0, 0, tzinfo=dt.timezone.utc).timestamp()
)


@dataclass
class ApiUsage:
    """HTTP calls made during one enrich operation (not cache hits)."""

    openweather_geocode: int = 0
    """City/state → lat/lon (OpenWeather Geocoding API)."""
    openweather_timemachine: int = 0
    """Historical weather for the race hour (One Call 3.0 timemachine)."""
    openweather_aqi: int = 0
    """Historical air pollution for the race hour (may retry up to 3 times)."""
    timezonedb: int = 0
    """Lat/lon → IANA timezone (local race time → Unix)."""
    usgs_epqs: int = 0
    """Terrain altitude in feet (USGS EPQS; free, no API key)."""

    def record(self, name: str, count: int = 1) -> None:
        if count <= 0 or not hasattr(self, name):
            raise ValueError(f"unknown api usage field: {name}")
        setattr(self, name, getattr(self, name) + count)

    def add(self, other: ApiUsage) -> None:
        for fname in _USAGE_FIELDS:
            setattr(self, fname, getattr(self, fname) + getattr(other, fname))

    @property
    def total(self) -> int:
        return sum(getattr(self, f) for f in _USAGE_FIELDS)

    def to_dict(self) -> dict[str, int]:
        out = {f: getattr(self, f) for f in _USAGE_FIELDS}
        out["total"] = self.total
        return out

    @classmethod
    def from_dict(cls, data: dict[str, int]) -> ApiUsage:
        return cls(**{f: int(data.get(f, 0)) for f in _USAGE_FIELDS})


_USAGE_FIELDS = (
    "openweather_geocode",
    "openweather_timemachine",
    "openweather_aqi",
    "timezonedb",
    "usgs_epqs",
)


@dataclass
class EnrichResult:
    """Race context after API enrichment plus call accounting."""

    context: object
    api_usage: ApiUsage = field(default_factory=ApiUsage)
