"""End-to-end standardization pipelines.

Entry points (one per sport)
----------------------------
``standardize_xc``
    Cross country. Weather, course grade, meet altitude, then **Riegel to NIRCA
    targets** (8000 m M / 6000 m F). **Required:** ``time``, ``gender``, reported
    distance.

``standardize_road``
    Road / marathon. Same weather, grade, and altitude corrections as XC, but
    distance from ``event_name`` and **no Riegel target conversion**.

``standardize_outdoor_track``
    Outdoor track. Sprint wind (when ``wind_mps`` set), weather, grade, meet
    altitude. **Required:** ``time``, ``gender``, ``event_name``.

``standardize_indoor_track``
    Indoor track. Lap length / banked venue factors, weather, grade, meet altitude.
    Wind is ignored. **Required:** ``time``, ``gender``, ``event_name``.

``standardize_result``
    Low-level path when you supply ``sport_name`` yourself (custom NRCD strings).

``standardize_seconds``
    Dispatches from :class:`~nrcd.standardize.context.RaceContext` using distances
    and sport.

Full parameter tables: :data:`nrcd.standardize.reference.PARAMETERS_DOC`.
"""

from __future__ import annotations

import math

from nrcd.standardize.altitude import apply_meet_altitude, barometric_pressure_hpa_from_record
from nrcd.standardize.config import StandardizeConfig
from nrcd.standardize.context import RaceContext, XCRaceContext
from nrcd.standardize.events import parse_event_distance_m
from nrcd.standardize.factors import riegel_convert, weather_factor
from nrcd.standardize.grade import apply_course_grade_factor
from nrcd.standardize.sport import is_cross_country
from nrcd.standardize.time import parse_time
from nrcd.standardize.track import apply_track_venue
from nrcd.standardize.units import (
    DistanceUnit,
    GradeInput,
    TemperatureUnit,
    VenueElevationUnit,
    parse_distance,
    temperature_to_fahrenheit,
)
from nrcd.standardize.validation import (
    validate_distance_unit,
    validate_grade_input,
    validate_positive_distance_m,
    validate_standardize_gender,
    validate_temp_unit,
    validate_venue_elevation_unit,
)
from nrcd.standardize.wind import apply_wind


def apply_factors(
    time_sec: float,
    *,
    weather: float = 1.0,
    elevation: float = 1.0,
    altitude: float = 1.0,
    track: float = 1.0,
    wind: float = 1.0,
) -> float:
    """Multiply time by each multiplicative factor (pass 1.0 to skip)."""
    if not math.isfinite(time_sec):
        return float("nan")
    t = time_sec
    for f in (weather, elevation, altitude, track, wind):
        t *= f
    return t


def _resolve_time(time: float | int | str) -> float:
    return parse_time(time)


_XC_DISTANCE_HELP = (
    "pass reported_distance_m=8000, reported_distance=5 with distance_unit='km', "
    "or reported_distance='5k'"
)


def _resolve_xc_distances(
    *,
    reported_distance_m: float | None,
    actual_distance_m: float | None,
    reported_distance: float | int | str | None,
    actual_distance: float | int | str | None,
    distance_unit: DistanceUnit,
) -> tuple[float, float]:
    if (
        reported_distance_m is None
        and actual_distance_m is None
        and reported_distance is None
        and actual_distance is None
    ):
        raise ValueError(f"reported distance is required; {_XC_DISTANCE_HELP}")

    d_reported = reported_distance_m
    if d_reported is not None:
        validate_positive_distance_m(d_reported, field="reported_distance_m")
    elif reported_distance is not None:
        d_reported = parse_distance(reported_distance, unit=distance_unit)

    d_actual = actual_distance_m
    if d_actual is not None:
        validate_positive_distance_m(d_actual, field="actual_distance_m")
    elif actual_distance is not None:
        d_actual = parse_distance(actual_distance, unit=distance_unit)
    elif d_actual is None:
        d_actual = d_reported

    if d_reported is None or d_actual is None:
        raise ValueError(f"reported distance is required; {_XC_DISTANCE_HELP}")
    return d_reported, d_actual


def standardize_xc(
    time: float | int | str,
    *,
    gender: str,
    reported_distance_m: float | None = None,
    actual_distance_m: float | None = None,
    reported_distance: float | int | str | None = None,
    actual_distance: float | int | str | None = None,
    distance_unit: DistanceUnit = "m",
    temperature: float | None = None,
    dew_point: float | None = None,
    elevation_gain: float | None = None,
    elevation_loss: float | None = None,
    meet_elevation: float | None = None,
    barometric_pressure: float | None = None,
    barometric_pressure_hpa: float | None = None,
    event_name: str | None = None,
    temp_unit: TemperatureUnit = "F",
    venue_elevation_unit: VenueElevationUnit = "ft",
    grade_input: GradeInput = "percent",
    course_distance_m: float | None = None,
    apply_weather: bool = True,
    apply_elevation_grade: bool = True,
    apply_meet_altitude_correction: bool = True,
    config: StandardizeConfig | None = None,
) -> float:
    """Cross-country pipeline: weather → grade → altitude → Riegel to NIRCA distance.

    XC and :func:`standardize_road` share weather, course grade, and meet-altitude
    steps. Only XC applies Riegel normalization to NIRCA reference distances
    (8000 m men / 6000 m women). Road uses :func:`standardize_road` instead.

    Required
    --------
    time, gender, and a reported distance (``reported_distance_m`` or
    ``reported_distance`` + ``distance_unit``).

    ``time`` may be seconds or a clock string (``"22:15"``, ``"1:10:13"``).
    Distances accept meters (default), kilometers, or miles via ``distance_unit``,
    or string labels like ``"5k"`` and ``"8000m"``.

    Optional (factor = 1.0 if omitted)
    --------------------------------
    actual_distance_m / actual_distance, temperature, dew_point,
    elevation_gain, elevation_loss, meet_elevation, event_name,
    temp_unit, venue_elevation_unit, grade_input, course_distance_m,
    apply_* flags, config.

    Units (defaults match the NRCD database)
    ----------------------------------------
    temperature, dew_point     °F — pass ``temp_unit="C"`` for Celsius
    meet_elevation             feet (venue altitude) — ``venue_elevation_unit="m"`` for meters
    elevation_gain/loss        % average grade — ``grade_input="feet"`` or ``"m"`` for
                               vertical feet or meters over the course (not meet altitude)

    ``sport_name`` is not a parameter here; set it on :class:`RaceContext` when using
    :func:`standardize_seconds`. This function does not apply track wind or venue factors.
    """
    cfg = config or StandardizeConfig()
    validate_standardize_gender(gender)
    validate_distance_unit(distance_unit)
    validate_temp_unit(temp_unit)
    validate_venue_elevation_unit(venue_elevation_unit)
    validate_grade_input(grade_input)

    t = _resolve_time(time)
    d_reported, d_actual = _resolve_xc_distances(
        reported_distance_m=reported_distance_m,
        actual_distance_m=actual_distance_m,
        reported_distance=reported_distance,
        actual_distance=actual_distance,
        distance_unit=distance_unit,
    )

    b = cfg.riegel_b(gender)
    target = cfg.xc_target_m(gender)

    if apply_weather:
        temp_f = temperature_to_fahrenheit(temperature, temp_unit)
        dew_f = temperature_to_fahrenheit(dew_point, temp_unit)
        t *= weather_factor(temp_f, dew_f, k=cfg.heat_k)

    if apply_elevation_grade:
        t = apply_course_grade_factor(
            t,
            elevation_gain,
            elevation_loss,
            course_distance_m=course_distance_m or d_actual,
            grade_input=grade_input,
            config=cfg,
        )

    pb_hpa = barometric_pressure_hpa_from_record(
        {"barometric_pressure": barometric_pressure, "barometric_pressure_hpa": barometric_pressure_hpa}
    )
    if apply_meet_altitude_correction and meet_elevation is not None:
        alt_event = event_name or f"{int(d_reported)}m"
        t = apply_meet_altitude(
            t,
            alt_event,
            meet_elevation,
            gender,
            elevation_unit=venue_elevation_unit,
            barometric_pressure_hpa=pb_hpa,
        )

    if d_reported > 0 and d_actual > 0 and abs(d_actual - d_reported) > 1:
        t = riegel_convert(t, d_actual, d_reported, b)

    return riegel_convert(t, d_actual, target, b)


def standardize_result(
    time: float | int | str,
    *,
    gender: str,
    event_name: str,
    sport_name: str,
    temperature: float | None = None,
    dew_point: float | None = None,
    elevation_gain: float | None = None,
    elevation_loss: float | None = None,
    meet_elevation: float | None = None,
    barometric_pressure: float | None = None,
    barometric_pressure_hpa: float | None = None,
    lap_length_m: float | None = None,
    banked: bool | str | None = None,
    wind_mps: float | None = None,
    temp_unit: TemperatureUnit = "F",
    venue_elevation_unit: VenueElevationUnit = "ft",
    grade_input: GradeInput = "percent",
    course_distance_m: float | None = None,
    apply_course_grade: bool = True,
    config: StandardizeConfig | None = None,
) -> float:
    """Low-level pipeline: wind → weather → course grade → track venue → meet altitude.

    Prefer the sport-specific helpers — :func:`standardize_road`,
    :func:`standardize_outdoor_track`, :func:`standardize_indoor_track` — instead of
    passing ``sport_name`` yourself. Cross country uses :func:`standardize_xc`.

    Required
    --------
    time, gender, event_name, sport_name

    ``time`` may be seconds (``10.5``), a clock string (``"4:12.00"``, ``"15:30.00"``),
    or a numeric string (``"10.52"``).

    ``sport_name`` controls which steps run:

    - **Outdoor Track** (contains ``outdoor`` and ``track``): sprint wind when ``wind_mps`` set.
    - **Indoor Track** (contains ``indoor``): ``lap_length_m`` / ``banked`` venue factors; no wind.
    - **Road** (contains ``road`` or ``marathon``): weather, grade, altitude only.

    Optional
    --------
    temperature + dew_point (both required for weather step),
    elevation_gain / elevation_loss (road and XC-style courses; % grade default),
    meet_elevation (venue altitude ft), lap_length_m, banked, wind_mps,
    grade_input, course_distance_m (defaults from event_name distance), config.
    """
    cfg = config or StandardizeConfig()
    validate_standardize_gender(gender)
    validate_temp_unit(temp_unit)
    validate_venue_elevation_unit(venue_elevation_unit)
    validate_grade_input(grade_input)

    t = _resolve_time(time)
    t = apply_wind(t, event_name, gender, wind_mps, sport_name, config=cfg)

    temp_f = temperature_to_fahrenheit(temperature, temp_unit)
    dew_f = temperature_to_fahrenheit(dew_point, temp_unit)
    t *= weather_factor(temp_f, dew_f, k=cfg.heat_k)

    if apply_course_grade and (elevation_gain is not None or elevation_loss is not None):
        d_course = course_distance_m
        if d_course is None:
            d_course = parse_event_distance_m(event_name)
        if d_course is not None and d_course > 0:
            t = apply_course_grade_factor(
                t,
                elevation_gain,
                elevation_loss,
                course_distance_m=d_course,
                grade_input=grade_input,
                config=cfg,
            )

    t = apply_track_venue(
        t,
        event_name,
        gender,
        lap_length_m=lap_length_m,
        banked=banked,
        sport_name=sport_name,
        config=cfg,
    )

    pb_hpa = barometric_pressure_hpa_from_record(
        {"barometric_pressure": barometric_pressure, "barometric_pressure_hpa": barometric_pressure_hpa}
    )
    if meet_elevation is not None:
        t = apply_meet_altitude(
            t,
            event_name,
            meet_elevation,
            gender,
            elevation_unit=venue_elevation_unit,
            barometric_pressure_hpa=pb_hpa,
        )

    return t


def standardize_road(
    time: float | int | str,
    *,
    gender: str,
    event_name: str,
    sport_name: str = "Road",
    **kwargs: object,
) -> float:
    """Road / marathon: weather → course grade → meet altitude.

    Same weather, grade, and altitude corrections as :func:`standardize_xc`, but
    distance comes from ``event_name`` and there is **no Riegel step** to NIRCA
    XC targets. Use :func:`standardize_xc` for cross country.
    """
    kwargs.pop("sport_name", None)
    return standardize_result(
        time,
        gender=gender,
        event_name=event_name,
        sport_name=sport_name,
        **kwargs,  # type: ignore[arg-type]
    )


def standardize_outdoor_track(
    time: float | int | str,
    *,
    gender: str,
    event_name: str,
    **kwargs: object,
) -> float:
    """Outdoor track: wind → weather → grade → meet altitude.

    Sprint wind applies when ``wind_mps`` is set and ``event_name`` is a sprint
    (≤400 m). Indoor venue and wind corrections never run here — use
    :func:`standardize_indoor_track` for indoor meets.
    """
    kwargs.pop("sport_name", None)
    return standardize_result(
        time,
        gender=gender,
        event_name=event_name,
        sport_name="Outdoor Track",
        **kwargs,  # type: ignore[arg-type]
    )


def standardize_indoor_track(
    time: float | int | str,
    *,
    gender: str,
    event_name: str,
    **kwargs: object,
) -> float:
    """Indoor track: weather → grade → lap/bank venue → meet altitude.

    ``lap_length_m`` and ``banked`` control NCAA venue factors. Wind is ignored
    even if passed. Use :func:`standardize_outdoor_track` for outdoor meets.
    """
    kwargs.pop("sport_name", None)
    return standardize_result(
        time,
        gender=gender,
        event_name=event_name,
        sport_name="Indoor Track",
        **kwargs,  # type: ignore[arg-type]
    )


def standardize_seconds(ctx: RaceContext) -> float:
    """Standardize from :class:`RaceContext` — XC, road, or track."""
    validate_standardize_gender(ctx.gender)
    t = ctx.time_sec
    if t is None and ctx.time_str is not None:
        t = parse_time(ctx.time_str)
    if t is None:
        raise ValueError("time is required: set time_sec or time_str on RaceContext")

    use_xc = isinstance(ctx, XCRaceContext) or (
        ctx.reported_distance_m is not None
        or ctx.reported_distance is not None
        or (is_cross_country(ctx.sport_name) and ctx.event_name)
    )

    if use_xc:
        xc_kwargs: dict = {
            "reported_distance_m": ctx.reported_distance_m,
            "actual_distance_m": ctx.actual_distance_m,
            "reported_distance": ctx.reported_distance,
            "actual_distance": ctx.actual_distance,
            "distance_unit": ctx.distance_unit,
        }
        if isinstance(ctx, XCRaceContext):
            d_rep = ctx.reported_or_event_m()
            if d_rep is not None:
                xc_kwargs["reported_distance_m"] = d_rep
                xc_kwargs["actual_distance_m"] = ctx.actual_or_reported_m()
                xc_kwargs["reported_distance"] = None
                xc_kwargs["actual_distance"] = None
        elif xc_kwargs["reported_distance_m"] is None and xc_kwargs["reported_distance"] is None and ctx.event_name:
            parsed = parse_event_distance_m(ctx.event_name)
            if parsed is not None:
                xc_kwargs["reported_distance_m"] = parsed

        has_xc_distance = (
            xc_kwargs["reported_distance_m"] is not None
            or xc_kwargs["reported_distance"] is not None
        )
        if has_xc_distance:
            return standardize_xc(
                t,
                gender=ctx.gender,
                temperature=ctx.temperature,
                dew_point=ctx.dew_point,
                elevation_gain=ctx.elevation_gain,
                elevation_loss=ctx.elevation_loss,
                meet_elevation=ctx.meet_elevation,
                barometric_pressure=ctx.barometric_pressure,
                barometric_pressure_hpa=ctx.barometric_pressure_hpa,
                event_name=ctx.event_name,
                temp_unit=ctx.temp_unit,
                venue_elevation_unit=ctx.venue_elevation_unit,
                grade_input=ctx.grade_input,
                course_distance_m=ctx.course_distance_m,
                config=ctx.config,
                **xc_kwargs,
            )
        if is_cross_country(ctx.sport_name) or isinstance(ctx, XCRaceContext):
            raise ValueError(
                "cannot resolve XC distance: set reported_distance_m, reported_distance "
                "(e.g. '5k'), or an event_name that parses to meters"
            )

    if ctx.event_name and ctx.sport_name:
        return standardize_result(
            t,
            gender=ctx.gender,
            event_name=ctx.event_name,
            sport_name=ctx.sport_name,
            temperature=ctx.temperature,
            dew_point=ctx.dew_point,
            meet_elevation=ctx.meet_elevation,
            barometric_pressure=ctx.barometric_pressure,
            barometric_pressure_hpa=ctx.barometric_pressure_hpa,
            lap_length_m=ctx.lap_length_m,
            banked=ctx.banked,
            wind_mps=ctx.wind_mps,
            elevation_gain=ctx.elevation_gain,
            elevation_loss=ctx.elevation_loss,
            grade_input=ctx.grade_input,
            course_distance_m=ctx.course_distance_m,
            temp_unit=ctx.temp_unit,
            venue_elevation_unit=ctx.venue_elevation_unit,
            config=ctx.config,
        )

    raise ValueError(
        "cannot standardize RaceContext: for XC set reported_distance_m, reported_distance, "
        "or event_name with sport_name='Cross Country'; for road/outdoor/indoor track set "
        "event_name and sport_name (or use standardize_road / standardize_outdoor_track / "
        "standardize_indoor_track directly)"
    )
