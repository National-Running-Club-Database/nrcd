"""Race-time standardization (NRCD paper / dataset conventions).

Quick reference
---------------
**Required everywhere:** race ``time`` (seconds or ``"MM:SS"`` / ``"H:MM:SS"``), ``gender`` (``M`` / ``F``).

**Cross country** — :func:`standardize_xc`:
  required distance; weather, grade, meet altitude; optional ``target_distance_m`` (Riegel).

**Road** — :func:`standardize_road`:
  same weather / grade / altitude as XC; distance from ``event_name``; no Riegel target step.

**Outdoor track** — :func:`standardize_outdoor_track`:
  ``event_name``; optional ``wind_mps`` on sprints; weather, grade, meet altitude.

**Indoor track** — :func:`standardize_indoor_track`:
  ``event_name``; optional ``lap_length_m`` / ``banked``; no wind.

**Low-level** — :func:`standardize_result`: supply ``sport_name`` yourself.

**Units (defaults):** temp/dew °F (`temp_unit="C"` ok); meet elevation ft
(`venue_elevation_unit="m"` ok); grade gain/loss **%** (`grade_input="feet"` or `"m"` for vertical ft/m);
distances & lap m; wind m/s.

Full tables: :data:`reference.PARAMETERS_DOC` or ``help(nrcd.standardize.reference)``.

Examples
--------
>>> from nrcd.standardize import standardize_xc, PARAMETERS_DOC
>>> print(PARAMETERS_DOC[:80])
...
"""

from nrcd.standardize.altitude import (
    apply_meet_altitude,
    barometric_pressure_hpa_from_record,
    barometric_pressure_torr_from_hpa,
    parse_barometric_pressure_hpa,
    peronnet_f_alt,
    resolve_meet_altitude_inputs,
    sea_level_time_seconds,
)
from nrcd.standardize.batch import (
    COLUMN_ALIASES,
    DataframeBatchResult,
    enrich_dataframe,
    resolve_column_map,
    row_to_race_context,
    standardize_dataframe,
)
from nrcd.standardize.config import StandardizeConfig
from nrcd.standardize.context import RaceContext, XCRaceContext
from nrcd.standardize.detail import StandardizeDetail, StandardizeStep
from nrcd.standardize.factors import (
    elevation_factor,
    heat_index,
    heat_slowdown_percent,
    riegel_convert,
    riegel_exponent,
    weather_factor,
    xc_target_distance_m,
)
from nrcd.standardize.grade import (
    apply_course_grade_factor,
    warn_one_sided_course_grade,
)
from nrcd.standardize.pipeline import (
    apply_factors,
    standardize_indoor_track,
    standardize_outdoor_track,
    standardize_result,
    standardize_result_detail,
    standardize_road,
    standardize_seconds,
    standardize_seconds_detail,
    standardize_xc,
    standardize_xc_detail,
)
from nrcd.standardize.reference import (
    PARAMETER_SPECS,
    PARAMETERS_DOC,
    ParameterSpec,
    parameter_specs,
    required_for,
)
from nrcd.standardize.sport import (
    is_cross_country,
    is_indoor_track,
    is_outdoor_track,
    is_track,
    normalize_sport_name,
    pipeline_kind,
)
from nrcd.standardize.time import format_time, parse_time
from nrcd.standardize.units import (
    DistanceUnit,
    GradeInput,
    TemperatureUnit,
    VenueElevationUnit,
    c_to_f,
    distance_to_meters,
    f_to_c,
    feet_to_meters,
    grade_percent_from_feet,
    grade_percent_from_meters,
    meters_to_feet,
    parse_distance,
    resolve_grade_percent,
    temperature_to_fahrenheit,
    venue_elevation_to_feet,
)

__all__ = [
    "COLUMN_ALIASES",
    "DataframeBatchResult",
    "DistanceUnit",
    "GradeInput",
    "PARAMETERS_DOC",
    "PARAMETER_SPECS",
    "ParameterSpec",
    "RaceContext",
    "StandardizeDetail",
    "StandardizeStep",
    "StandardizeConfig",
    "TemperatureUnit",
    "VenueElevationUnit",
    "XCRaceContext",
    "apply_course_grade_factor",
    "apply_meet_altitude",
    "apply_factors",
    "barometric_pressure_hpa_from_record",
    "barometric_pressure_torr_from_hpa",
    "c_to_f",
    "distance_to_meters",
    "enrich_dataframe",
    "elevation_factor",
    "f_to_c",
    "feet_to_meters",
    "format_time",
    "grade_percent_from_feet",
    "grade_percent_from_meters",
    "heat_index",
    "heat_slowdown_percent",
    "is_cross_country",
    "is_indoor_track",
    "is_outdoor_track",
    "is_track",
    "meters_to_feet",
    "normalize_sport_name",
    "parameter_specs",
    "parse_barometric_pressure_hpa",
    "parse_distance",
    "parse_time",
    "pipeline_kind",
    "required_for",
    "resolve_grade_percent",
    "resolve_column_map",
    "resolve_meet_altitude_inputs",
    "row_to_race_context",
    "temperature_to_fahrenheit",
    "venue_elevation_to_feet",
    "warn_one_sided_course_grade",
    "peronnet_f_alt",
    "riegel_convert",
    "riegel_exponent",
    "sea_level_time_seconds",
    "standardize_dataframe",
    "standardize_indoor_track",
    "standardize_outdoor_track",
    "standardize_result",
    "standardize_result_detail",
    "standardize_road",
    "standardize_seconds",
    "standardize_seconds_detail",
    "standardize_xc",
    "standardize_xc_detail",
    "weather_factor",
    "xc_target_distance_m",
]
