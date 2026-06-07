"""Input records for standardization (explicit unit fields).

See :data:`nrcd.standardize.reference.PARAMETERS_DOC` for the full required/optional
matrix and sport gating rules.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from nrcd.standardize.config import StandardizeConfig
from nrcd.standardize.sport import is_cross_country, pipeline_kind
from nrcd.standardize.units import (
    DistanceUnit,
    GradeInput,
    TemperatureUnit,
    VenueElevationUnit,
)


@dataclass
class RaceContext:
    """One race result and its environment.

    **Always required:** ``gender`` and either ``time_sec`` or ``time_str``.

    **Required for road** (``standardize_road``): ``event_name``.

    **Required for outdoor track** (``standardize_outdoor_track``): ``event_name``.

    **Required for indoor track** (``standardize_indoor_track``): ``event_name``.

    **Low-level** (``standardize_result``): ``event_name`` and ``sport_name``.

    **Required for XC** (``standardize_xc`` / ``XCRaceContext``):
    ``reported_distance_m``, ``reported_distance`` (+ ``distance_unit``), or an
    ``event_name`` that parses to a distance (e.g. ``8000m``). Use
    ``sport_name="Cross Country"`` so :func:`~nrcd.standardize.pipeline.standardize_seconds`
    selects the XC pipeline.

    All weather, grade, altitude, lap, bank, and wind fields are **optional**; missing
    values leave that factor at 1.0 (no adjustment).
    """

    # --- required ---
    gender: str
    """``M`` or ``F`` (Riegel, wind tables, Peronnet, NCAA charts)."""

    time_sec: float | None = None
    """Race time in seconds."""

    time_str: str | None = None
    """Alternative to ``time_sec`` (``H:MM:SS`` or ``MM:SS``)."""

    # --- required for track; recommended everywhere ---
    event_name: str | None = None
    """e.g. ``8000m``, ``100m``, ``110m Hurdles`` — distance parse + sprint vs distance."""

    sport_name: str | None = None
    """NRCD ``sport.name`` — **gates wind and track venue**. Examples: ``Cross Country``,
    ``Outdoor Track``, ``Indoor Track``."""

    # --- optional: weather (both T and D needed; default °F) ---
    temperature: float | None = None
    dew_point: float | None = None
    temp_unit: TemperatureUnit = "F"

    # --- optional: course grade profile — XC and road (default %, not ft) ---
    elevation_gain: float | None = None
    """Average uphill grade (%); not meet altitude. Warns if set without elevation_loss."""

    elevation_loss: float | None = None
    """Average downhill grade (%). Warns if set without elevation_gain."""

    grade_input: GradeInput = "percent"
    course_distance_m: float | None = None

    # --- optional: meet altitude / venue elevation (default ft; Peronnet) ---
    meet_elevation: float | None = None
    """Meet altitude in feet (NRCD column ``meet.altitude``). From city/state via USGS, not gain/loss."""

    venue_elevation_unit: VenueElevationUnit = "ft"

    # --- optional: XC distances ---
    reported_distance_m: float | None = None
    actual_distance_m: float | None = None
    reported_distance: float | int | str | None = None
    """Like :func:`~nrcd.standardize.pipeline.standardize_xc` ``reported_distance``."""
    actual_distance: float | int | str | None = None
    distance_unit: DistanceUnit = "m"

    target_distance_m: float | None = None
    """Optional Riegel output distance in meters."""

    target_distance: float | int | str | None = None
    """Like ``reported_distance`` — alternative to ``target_distance_m`` (e.g. ``'8k'``, ``8`` + unit)."""

    target_distance_unit: DistanceUnit = "m"
    """Unit for numeric ``target_distance`` when not a label like ``'8k'``."""

    # --- optional: track venue (indoor sport + lap_length_m / banked) ---
    lap_length_m: float | None = None
    banked: bool | str | None = None

    # --- optional: outdoor track wind (m/s, tailwind positive) ---
    wind_mps: float | None = None

    # --- optional: location → meet altitude / weather via nrcd.enrich (OpenWeather geocode) ---
    city: str | None = None
    """Meet city; with ``state`` or ``country``, geocodes via OpenWeather."""

    state: str | None = None
    """Region or US state (e.g. ``CO``, ``ENG``). Optional when ``country`` or ``geocode_query`` is set."""

    country: str | None = None
    """ISO country code for geocoding (e.g. ``GB``, ``FR``). Overrides ``EnrichConfig.geocode_country_suffix``."""

    geocode_query: str | None = None
    """Free-form OpenWeather geocode query (e.g. ``London,GB``). Skips city/state/country assembly."""

    latitude: float | None = None
    """Meet latitude (NRCD ``meet.meet_latitude``); skips OpenWeather geocode when set with longitude."""

    longitude: float | None = None
    """Meet longitude (NRCD ``meet.meet_longitude``)."""

    timezone_name: str | None = None
    """IANA timezone (e.g. ``America/Denver``); skips TimeZoneDB when set."""

    event_date: dt.date | None = None
    """Race date — required for OpenWeather historical fetch via :mod:`nrcd.enrich`."""

    event_time: dt.time | None = None
    """Race start time (local, resolved via TimeZoneDB)."""

    # --- optional: weather / AQI (°F; filled manually or by nrcd.enrich) ---
    real_feel: float | None = None
    humidity: float | None = None
    weather_conditions: str | None = None
    weather_description: str | None = None
    aqi: int | None = None
    aqi_co: float | None = None
    aqi_no: float | None = None
    aqi_no2: float | None = None
    aqi_o3: float | None = None
    aqi_so2: float | None = None
    aqi_pm2_5: float | None = None
    aqi_pm10: float | None = None
    aqi_nh3: float | None = None
    barometric_pressure: float | None = None
    """Race-time pressure in hPa (NRCD ``course_details.barometric_pressure``, OpenWeather)."""

    barometric_pressure_hpa: float | None = None
    """Deprecated alias for :attr:`barometric_pressure`."""

    config: StandardizeConfig = field(default_factory=StandardizeConfig)

    def pipeline(self) -> str:
        """``xc`` | ``track`` | ``road`` | ``other`` from ``sport_name``."""
        from nrcd.standardize.events import parse_event_distance_m
        from nrcd.standardize.units import parse_distance

        has_distance = self.reported_distance_m is not None
        if not has_distance and self.reported_distance is not None:
            has_distance = parse_distance(self.reported_distance, self.distance_unit) is not None
        if not has_distance and self.event_name:
            has_distance = parse_event_distance_m(self.event_name) is not None
        if has_distance and (
            is_cross_country(self.sport_name)
            or self.reported_distance_m is not None
            or self.reported_distance is not None
        ):
            return "xc"
        return pipeline_kind(self.sport_name)


@dataclass
class XCRaceContext(RaceContext):
    """Cross country — same fields as :class:`RaceContext`.

    Prefer ``sport_name="Cross Country"``. If ``reported_distance_m`` is omitted,
    ``event_name`` must parse (e.g. ``8000m``).
    """

    def reported_or_event_m(self) -> float | None:
        if self.reported_distance_m is not None:
            return self.reported_distance_m
        if self.reported_distance is not None:
            from nrcd.standardize.units import parse_distance

            return parse_distance(self.reported_distance, self.distance_unit)
        if self.event_name:
            from nrcd.standardize.events import parse_event_distance_m

            return parse_event_distance_m(self.event_name)
        return None

    def actual_or_reported_m(self) -> float | None:
        if self.actual_distance_m is not None:
            return self.actual_distance_m
        return self.reported_or_event_m()
