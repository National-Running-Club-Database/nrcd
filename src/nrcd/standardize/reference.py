"""Parameter reference (required vs optional, units, sport gating).

Access the full text from Python::

    from nrcd.standardize import PARAMETERS_DOC, parameter_specs

    help(nrcd.standardize)  # module docstring + link here
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Applicability = Literal["all", "xc", "track", "road", "altitude", "weather", "wind", "venue"]


@dataclass(frozen=True)
class ParameterSpec:
    """One input field for standardization."""

    name: str
    required: Literal["always", "xc", "track", "conditional", "optional"]
    unit_default: str
    description: str
    applies_to: tuple[Applicability, ...]
    notes: str = ""


PARAMETER_SPECS: tuple[ParameterSpec, ...] = (
    ParameterSpec(
        "time",
        "always",
        "seconds or clock string",
        "Race time: seconds, 'MM:SS', or 'H:MM:SS'. On RaceContext use time_sec or time_str.",
        ("all",),
    ),
    ParameterSpec(
        "gender",
        "always",
        '"M" | "F" (also MIXED for altitude averaging)',
        "Sex category for Riegel exponent, wind tables, Peronnet, NCAA track charts.",
        ("all",),
    ),
    ParameterSpec(
        "sport_name",
        "conditional",
        "NRCD sport.name string",
        "Which corrections run. Cross Country → XC pipeline; "
        '"Outdoor Track" enables wind; "Indoor Track" enables lap/bank venue factors.',
        ("all", "wind", "venue"),
        'Examples: "Cross Country", "Outdoor Track", "Indoor Track". '
        "Wind needs both substrings outdoor + track. Venue banking needs indoor.",
    ),
    ParameterSpec(
        "event_name",
        "conditional",
        "free text",
        "Parsed for distance (e.g. 8000m, 110m Hurdles) and event category (sprint vs distance). "
        "Required for track wind, meet altitude, and when reported_distance_m is omitted on XC.",
        ("all", "xc", "track", "altitude", "wind"),
    ),
    ParameterSpec(
        "reported_distance_m",
        "xc",
        "meters",
        "Nominal event distance (e.g. 8000 m men / 6000 m women).",
        ("xc",),
        "May be omitted if reported_distance + distance_unit or event_name parses to a distance.",
    ),
    ParameterSpec(
        "reported_distance",
        "xc",
        "meters default (distance_unit)",
        "Nominal distance as number or label (e.g. 8000, '5k', '3.1mi').",
        ("xc",),
        "Alternative to reported_distance_m; use distance_unit for miles/km.",
    ),
    ParameterSpec(
        "actual_distance_m",
        "optional",
        "meters",
        "Measured course length; defaults to reported_distance_m.",
        ("xc",),
    ),
    ParameterSpec(
        "actual_distance",
        "optional",
        "meters default (distance_unit)",
        "Measured course length; alternative to actual_distance_m.",
        ("xc",),
    ),
    ParameterSpec(
        "distance_unit",
        "optional",
        '"m" | "km" | "mi"',
        "Unit for reported_distance and actual_distance when not in meters.",
        ("xc",),
    ),
    ParameterSpec(
        "target_distance_m",
        "optional",
        "meters",
        "Riegel-convert corrected time to this distance. Omit to keep the race distance.",
        ("xc",),
        "Alternative: target_distance='8k' or target_distance=8 with target_distance_unit='km'.",
    ),
    ParameterSpec(
        "target_distance",
        "optional",
        "meters default (target_distance_unit)",
        "Riegel target as number or label (e.g. '8k', 8 with unit='km').",
        ("xc",),
    ),
    ParameterSpec(
        "target_distance_unit",
        "optional",
        '"m" | "km" | "mi"',
        "Unit for numeric target_distance when not a label like '8k'.",
        ("xc",),
    ),
    ParameterSpec(
        "temperature",
        "optional",
        "°F default (temp_unit)",
        "Air temperature for Hadley-style heat slowdown.",
        ("xc", "weather"),
        "Both temperature and dew_point needed or weather step is skipped (factor 1.0).",
    ),
    ParameterSpec(
        "dew_point",
        "optional",
        "°F default (temp_unit)",
        "Dew point; heat index H = T + D in °F.",
        ("xc", "weather"),
    ),
    ParameterSpec(
        "temp_unit",
        "optional",
        '"F" | "C"',
        "Unit of temperature and dew_point. Default F (NRCD database).",
        ("weather",),
    ),
    ParameterSpec(
        "elevation_gain",
        "optional",
        "percent grade default",
        "Maurer uphill exponent base^g. XC and road. Not meet altitude; use grade_input for ft or m.",
        ("xc", "road"),
        "UserWarning if only gain is set (implies all-uphill course).",
    ),
    ParameterSpec(
        "elevation_loss",
        "optional",
        "percent grade default",
        "Maurer downhill exponent. XC and road.",
        ("xc", "road"),
    ),
    ParameterSpec(
        "grade_input",
        "optional",
        '"percent" | "feet" | "m"',
        "How to interpret elevation_gain / elevation_loss.",
        ("xc", "road"),
        "feet or m requires course_distance_m (or actual XC distance).",
    ),
    ParameterSpec(
        "course_distance_m",
        "conditional",
        "meters",
        "Run length for converting gain/loss feet → percent grade.",
        ("xc", "road"),
        "Required when grade_input is feet or m.",
    ),
    ParameterSpec(
        "meet_elevation",
        "optional",
        "feet default (venue_elevation_unit)",
        "Meet altitude (venue elevation) for Peronnet MAP(z) — not course gain/loss.",
        ("altitude", "xc", "track", "road"),
    ),
    ParameterSpec(
        "barometric_pressure",
        "optional",
        "hPa",
        "Race-time pressure at start (NRCD course_details / OpenWeather timemachine); refines f_alt rho.",
        ("altitude", "xc", "track", "road"),
        "Requires meet_elevation; ignored if elevation missing. When both set, refines rho only; "
        "when only elevation, P_b^race = P_b(z). Pressure alone is never applied.",
    ),
    ParameterSpec(
        "venue_elevation_unit",
        "optional",
        '"ft" | "m"',
        "Unit of meet_elevation. Default ft (NRCD meet.altitude).",
        ("altitude",),
    ),
    ParameterSpec(
        "lap_length_m",
        "conditional",
        "meters",
        "Indoor/oversized track lap length for NCAA f_len.",
        ("venue", "track"),
        "Needed for non-standard indoor tracks; outdoor 400 m lap → factor 1.0.",
    ),
    ParameterSpec(
        "banked",
        "optional",
        "bool or string",
        "Banked indoor track for NCAA f_bank.",
        ("venue", "track"),
        "Only applies when sport_name is indoor track.",
    ),
    ParameterSpec(
        "wind_mps",
        "optional",
        "m/s",
        "Recorded wind; positive = tailwind (TFRRS convention).",
        ("wind", "track"),
        "Only outdoor track sprints/hurdles (≤400 m); sport_name must match outdoor track. "
        "Linear scale to config.wind_max_mps (default 4.0) from 2 m/s tables.",
    ),
    ParameterSpec(
        "config",
        "optional",
        "StandardizeConfig",
        "Coefficients: heat_k, Riegel b, XC targets, wind cap, grade bases.",
        ("all",),
    ),
    ParameterSpec(
        "city",
        "conditional",
        "text",
        "Meet city for OpenWeather geocoding (weather / optional altitude backfill).",
        ("altitude", "weather"),
        "With state (US), country (international), or geocode_query. See nrcd.enrich.API_GUIDE.",
    ),
    ParameterSpec(
        "state",
        "conditional",
        "text",
        "Region or US state (e.g. CO, ENG). Optional when country or geocode_query is set.",
        ("altitude", "weather"),
    ),
    ParameterSpec(
        "country",
        "conditional",
        "ISO code",
        "Country for geocoding (e.g. GB, FR). Overrides EnrichConfig.geocode_country_suffix.",
        ("altitude", "weather"),
    ),
    ParameterSpec(
        "geocode_query",
        "conditional",
        "text",
        "Free-form OpenWeather geocode q string (e.g. London,GB).",
        ("altitude", "weather"),
    ),
    ParameterSpec(
        "event_date",
        "conditional",
        "date",
        "Required with event_time for historical weather/AQI fetch.",
        ("weather",),
    ),
    ParameterSpec(
        "event_time",
        "conditional",
        "time",
        "Local start time; TimeZoneDB converts to Unix for OpenWeather timemachine.",
        ("weather",),
    ),
)


PARAMETERS_DOC = """
nrcd.standardize — parameter reference
======================================

REQUIRED (every call)
---------------------
  time              Seconds or clock string ('22:15', '4:12.00', '10.52').
                    RaceContext: time_sec or time_str instead of the time argument.
  gender            "M" or "F" on all standardize_* entry points.
                    "MIXED" only on Peronnet helpers (apply_meet_altitude, peronnet_f_alt);
                    standardize_xc / standardize_result raise if gender is MIXED.

REQUIRED by pipeline
--------------------
  Cross country (standardize_xc)
    reported distance   reported_distance_m, or reported_distance + distance_unit,
                        or labels like '5k' / '8000m'.
    target_distance_m   optional Riegel output distance (meters). Omit to keep race distance.
                        Alternatives: target_distance='8k', target_distance=8 with
                        target_distance_unit='km', or target_distance=4.97 with target_distance_unit='mi'.

  Road (standardize_road)
    event_name          e.g. "5k", "10k", "5000m", "Half Marathon", "Marathon" —
                        same weather/grade/altitude as XC,
                        but no Riegel target conversion.

  Outdoor track (standardize_outdoor_track)
    event_name          e.g. "100m", "Mile" — wind on sprints when wind_mps set.

  Indoor track (standardize_indoor_track)
    event_name          e.g. "200m", "Mile" — lap_length_m / banked venue factors; no wind.

  Low-level (standardize_result)
    event_name, sport_name   Use sport-specific helpers above when possible.
                             sport_name gates wind (outdoor+track) and venue (indoor).

OPTIONAL (step skipped if missing)
----------------------------------
  actual_distance_m     XC measured length (defaults to reported).
  temperature, dew_point  Both needed for weather; default unit °F (temp_unit="C" ok).
  elevation_gain/loss   Course grade % (XC + road); warns if only gain or only loss.
  meet_elevation        Meet altitude (venue); default unit feet — not gain/loss.
  barometric_pressure    OpenWeather race-time pressure (hPa); only with meet_elevation (refines rho).
  lap_length_m, banked  Indoor track venue (with Indoor Track sport).
  wind_mps              Outdoor track sprints only.
  config                Override paper coefficients.

UNIT DEFAULTS (NRCD database)
-----------------------------
  temperature, dew_point     °F  (heat index H = T + D, threshold 100°F)
  meet_elevation             ft  (Peronnet; use venue_elevation_unit="m" if needed)
  elevation_gain/loss        % grade  (grade_input="feet" or "m" for vertical ft/m)
  distances, lap_length      m
  wind                       m/s  (positive = tailwind)

StandardizeConfig coefficients
------------------------------
  heat_k=0.0016              Quadratic heat slowdown above 100°F H
  riegel_b_men=1.055         Riegel exponent (men)
  riegel_b_women=1.08        Riegel exponent (women)
  xc_target_men_m=8000       Default men XC Riegel target (StandardizeConfig)
  xc_target_women_m=6000       Default women XC Riegel target (StandardizeConfig)
  elevation_gain_base=1.04   Maurer uphill
  elevation_loss_base=0.9633 Maurer downhill
  wind_max_mps=4.0           Wind clamp; linear scale from 2 m/s reference tables
  track_outdoor_reference_lap_m=400

Entry points (NRCD sport names)
-------------------------------
  standardize_xc              Cross Country — optional target_distance_m (Riegel)
  standardize_road            Road / marathon — weather, grade, altitude only
  standardize_outdoor_track   Outdoor Track — wind (sprints), weather, grade, altitude
  standardize_indoor_track    Indoor Track — venue lap/bank, weather, grade, altitude
  standardize_result          Any sport_name string (advanced)

API enrichment (nrcd.enrich — optional, pip install nrcd[apis])
---------------------------------------------------------------
  city + state (US)   → geocode city,state,US (default suffix)
  city + country      → geocode city,CC (e.g. London,GB)
  geocode_query       → free-form OpenWeather q string
  lat + lon           → skip geocode; weather global; altitude via USGS (US-focused)
  city + state + event_date + event_time + API keys
                      → temperature, dew_point, humidity, real_feel, weather_*, aqi_*
  Keys: NRCD_OPENWEATHER_API_KEY, NRCD_TIMEZONE_API_KEY, NRCD_GEOCODE_COUNTRY_SUFFIX
"""


def parameter_specs() -> tuple[ParameterSpec, ...]:
    """Structured parameter metadata."""
    return PARAMETER_SPECS


def required_for(
    pipeline: Literal["xc", "road", "outdoor_track", "indoor_track", "track", "result"],
) -> list[str]:
    """Minimal field names for each entry-point."""
    common = ["time", "gender"]
    if pipeline == "xc":
        return common + [
            "reported_distance_m or reported_distance (+ distance_unit if not meters)",
        ]
    if pipeline in ("road", "outdoor_track", "indoor_track"):
        return common + ["event_name"]
    if pipeline == "track":
        return common + ["event_name", "sport_name (prefer outdoor_track / indoor_track helpers)"]
    return common + ["event_name", "sport_name"]
