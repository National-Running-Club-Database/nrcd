"""Inverse standardization — convert a std time to expected raw time at a meet."""

from __future__ import annotations

import math

from nrcd.standardize.altitude import barometric_pressure_hpa_from_record, meet_altitude_factor
from nrcd.standardize.config import StandardizeConfig
from nrcd.standardize.context import RaceContext, XCRaceContext
from nrcd.standardize.events import parse_event_distance_m
from nrcd.standardize.factors import riegel_convert, weather_factor
from nrcd.standardize.grade import course_grade_factor
from nrcd.standardize.pipeline import (
    _resolve_target_distance_m,
    _resolve_time,
    _resolve_xc_distances,
)
from nrcd.standardize.sport import is_cross_country
from nrcd.standardize.time import parse_time
from nrcd.standardize.track import track_venue_factor
from nrcd.standardize.units import (
    DistanceUnit,
    GradeInput,
    TemperatureUnit,
    VenueElevationUnit,
    temperature_to_fahrenheit,
)
from nrcd.standardize.validation import (
    validate_distance_unit,
    validate_grade_input,
    validate_standardize_gender,
    validate_temp_unit,
    validate_venue_elevation_unit,
)
from nrcd.standardize.wind import (
    applies_wind_conversion,
    parse_wind_mps,
    wind_delta_seconds_at_speed,
)


def _divide_by_factor(time_sec: float, factor: float) -> float:
    if not math.isfinite(time_sec):
        return time_sec
    if factor == 0 or not math.isfinite(factor):
        return float("nan")
    if factor == 1.0:
        return time_sec
    return time_sec / factor


def _unstandardize_result_core(
    std_time: float | int | str,
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
    venue_reference: str | None = None,
    config: StandardizeConfig | None = None,
) -> float:
    """Apply inverse pipeline steps (reverse of :func:`~nrcd.standardize.standardize_result`)."""
    cfg = config or StandardizeConfig()
    validate_standardize_gender(gender)
    validate_temp_unit(temp_unit)
    validate_venue_elevation_unit(venue_elevation_unit)
    validate_grade_input(grade_input)

    t = _resolve_time(std_time)

    pb_hpa = barometric_pressure_hpa_from_record(
        {"barometric_pressure": barometric_pressure, "barometric_pressure_hpa": barometric_pressure_hpa}
    )
    if meet_elevation is not None:
        af = meet_altitude_factor(
            event_name,
            meet_elevation,
            gender,
            elevation_unit=venue_elevation_unit,
            barometric_pressure_hpa=pb_hpa,
        )
        t = _divide_by_factor(t, af)

    tvf = track_venue_factor(
        event_name,
        gender,
        lap_length_m=lap_length_m,
        banked=banked,
        sport_name=sport_name,
        venue_reference=venue_reference,
        config=cfg,
    )
    t = _divide_by_factor(t, tvf)

    if apply_course_grade and (elevation_gain is not None or elevation_loss is not None):
        d_course = course_distance_m
        if d_course is None:
            d_course = parse_event_distance_m(event_name)
        if d_course is not None and d_course > 0:
            gf = course_grade_factor(
                elevation_gain,
                elevation_loss,
                course_distance_m=d_course,
                grade_input=grade_input,
                config=cfg,
            )
            t = _divide_by_factor(t, gf)

    temp_f = temperature_to_fahrenheit(temperature, temp_unit)
    dew_f = temperature_to_fahrenheit(dew_point, temp_unit)
    wf = weather_factor(temp_f, dew_f, k=cfg.heat_k)
    t = _divide_by_factor(t, wf)

    if applies_wind_conversion(event_name, sport_name):
        w = parse_wind_mps(wind_mps)
        if w is not None:
            d = parse_event_distance_m(event_name)
            if d is not None:
                cap = cfg.wind_max_mps
                if abs(w) > cap:
                    w = math.copysign(cap, w)
                delta = wind_delta_seconds_at_speed(w, d, gender, cap_mps=cap)
                t = t - delta

    return t


def _unstandardize_xc_core(
    std_time: float | int | str,
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
    target_distance_m: float | None = None,
    target_distance: float | int | str | None = None,
    target_distance_unit: DistanceUnit = "m",
    config: StandardizeConfig | None = None,
) -> float:
    """Apply inverse XC pipeline (reverse of :func:`~nrcd.standardize.standardize_xc`)."""
    cfg = config or StandardizeConfig()
    validate_standardize_gender(gender)
    validate_distance_unit(distance_unit)
    validate_distance_unit(target_distance_unit)
    validate_temp_unit(temp_unit)
    validate_venue_elevation_unit(venue_elevation_unit)
    validate_grade_input(grade_input)

    t = _resolve_time(std_time)
    d_reported, d_actual = _resolve_xc_distances(
        reported_distance_m=reported_distance_m,
        actual_distance_m=actual_distance_m,
        reported_distance=reported_distance,
        actual_distance=actual_distance,
        distance_unit=distance_unit,
    )
    b = cfg.riegel_b(gender)

    d_target = _resolve_target_distance_m(
        target_distance_m=target_distance_m,
        target_distance=target_distance,
        target_distance_unit=target_distance_unit,
    )
    if d_target is not None:
        t = riegel_convert(t, d_target, d_actual, b)

    if d_reported > 0 and d_actual > 0 and abs(d_actual - d_reported) > 1:
        t = riegel_convert(t, d_reported, d_actual, b)

    pb_hpa = barometric_pressure_hpa_from_record(
        {"barometric_pressure": barometric_pressure, "barometric_pressure_hpa": barometric_pressure_hpa}
    )
    if apply_meet_altitude_correction and meet_elevation is not None:
        alt_event = event_name or f"{int(d_reported)}m"
        af = meet_altitude_factor(
            alt_event,
            meet_elevation,
            gender,
            elevation_unit=venue_elevation_unit,
            barometric_pressure_hpa=pb_hpa,
        )
        t = _divide_by_factor(t, af)

    if apply_elevation_grade and (elevation_gain is not None or elevation_loss is not None):
        gf = course_grade_factor(
            elevation_gain,
            elevation_loss,
            course_distance_m=course_distance_m or d_actual,
            grade_input=grade_input,
            config=cfg,
        )
        t = _divide_by_factor(t, gf)

    if apply_weather:
        temp_f = temperature_to_fahrenheit(temperature, temp_unit)
        dew_f = temperature_to_fahrenheit(dew_point, temp_unit)
        wf = weather_factor(temp_f, dew_f, k=cfg.heat_k)
        t = _divide_by_factor(t, wf)

    return t


def unstandardize_result(
    std_time: float | int | str,
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
    venue_reference: str | None = None,
    config: StandardizeConfig | None = None,
) -> float:
    """Predict clock time at a meet from a standardized time.

    Use when you have a std time (past result or fitness level) and want the
    **expected raw time** at another meet or an upcoming race — pass that
    meet's weather, course grade, altitude, wind, and track venue
    (``lap_length_m``, ``banked``, ``venue_reference`` on indoor/outdoor track).

    Inverse of :func:`~nrcd.standardize.standardize_result`. Keep
    ``target_distance_m`` and distance fields aligned with how ``std_time`` was
    computed.
    """
    return _unstandardize_result_core(
        std_time,
        gender=gender,
        event_name=event_name,
        sport_name=sport_name,
        temperature=temperature,
        dew_point=dew_point,
        elevation_gain=elevation_gain,
        elevation_loss=elevation_loss,
        meet_elevation=meet_elevation,
        barometric_pressure=barometric_pressure,
        barometric_pressure_hpa=barometric_pressure_hpa,
        lap_length_m=lap_length_m,
        banked=banked,
        wind_mps=wind_mps,
        temp_unit=temp_unit,
        venue_elevation_unit=venue_elevation_unit,
        grade_input=grade_input,
        course_distance_m=course_distance_m,
        apply_course_grade=apply_course_grade,
        venue_reference=venue_reference,
        config=config,
    )


def unstandardize_xc(
    std_time: float | int | str,
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
    target_distance_m: float | None = None,
    target_distance: float | int | str | None = None,
    target_distance_unit: DistanceUnit = "m",
    config: StandardizeConfig | None = None,
) -> float:
    """Predict raw XC clock time at a meet from a standardized time.

    Pass the **upcoming meet's** forecast temperature, course profile, meet
    elevation, and race distance. Inverse of :func:`~nrcd.standardize.standardize_xc`.
    """
    return _unstandardize_xc_core(
        std_time,
        gender=gender,
        reported_distance_m=reported_distance_m,
        actual_distance_m=actual_distance_m,
        reported_distance=reported_distance,
        actual_distance=actual_distance,
        distance_unit=distance_unit,
        temperature=temperature,
        dew_point=dew_point,
        elevation_gain=elevation_gain,
        elevation_loss=elevation_loss,
        meet_elevation=meet_elevation,
        barometric_pressure=barometric_pressure,
        barometric_pressure_hpa=barometric_pressure_hpa,
        event_name=event_name,
        temp_unit=temp_unit,
        venue_elevation_unit=venue_elevation_unit,
        grade_input=grade_input,
        course_distance_m=course_distance_m,
        apply_weather=apply_weather,
        apply_elevation_grade=apply_elevation_grade,
        apply_meet_altitude_correction=apply_meet_altitude_correction,
        target_distance_m=target_distance_m,
        target_distance=target_distance,
        target_distance_unit=target_distance_unit,
        config=config,
    )


def unstandardize_road(
    std_time: float | int | str,
    *,
    gender: str,
    event_name: str,
    sport_name: str = "Road",
    **kwargs: object,
) -> float:
    """Road / marathon — expected raw time at a meet from a std time."""
    kwargs.pop("sport_name", None)
    return unstandardize_result(
        std_time,
        gender=gender,
        event_name=event_name,
        sport_name=sport_name,
        **kwargs,  # type: ignore[arg-type]
    )


def unstandardize_outdoor_track(
    std_time: float | int | str,
    *,
    gender: str,
    event_name: str,
    **kwargs: object,
) -> float:
    """Outdoor track — expected raw time at a meet (wind, weather, venue, altitude)."""
    kwargs.pop("sport_name", None)
    return unstandardize_result(
        std_time,
        gender=gender,
        event_name=event_name,
        sport_name="Outdoor Track",
        **kwargs,  # type: ignore[arg-type]
    )


def unstandardize_indoor_track(
    std_time: float | int | str,
    *,
    gender: str,
    event_name: str,
    **kwargs: object,
) -> float:
    """Indoor track — expected raw time at a meet (lap length, banking, venue ref)."""
    kwargs.pop("sport_name", None)
    return unstandardize_result(
        std_time,
        gender=gender,
        event_name=event_name,
        sport_name="Indoor Track",
        **kwargs,  # type: ignore[arg-type]
    )


def unstandardize_seconds(ctx: RaceContext) -> float:
    """Predict meet clock time from a std time on ``RaceContext`` fields."""
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
            return unstandardize_xc(
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
                target_distance_m=ctx.target_distance_m,
                target_distance=ctx.target_distance,
                target_distance_unit=ctx.target_distance_unit,
                config=ctx.config,
                **xc_kwargs,
            )
        if is_cross_country(ctx.sport_name) or isinstance(ctx, XCRaceContext):
            raise ValueError(
                "cannot resolve XC distance: set reported_distance_m, reported_distance "
                "(e.g. '5k'), or an event_name that parses to meters"
            )

    if ctx.event_name and ctx.sport_name:
        return unstandardize_result(
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
            venue_reference=ctx.venue_reference,
            elevation_gain=ctx.elevation_gain,
            elevation_loss=ctx.elevation_loss,
            grade_input=ctx.grade_input,
            course_distance_m=ctx.course_distance_m,
            temp_unit=ctx.temp_unit,
            venue_elevation_unit=ctx.venue_elevation_unit,
            config=ctx.config,
        )

    raise ValueError(
        "cannot unstandardize RaceContext: for XC set reported_distance_m, reported_distance, "
        "or event_name with sport_name='Cross Country'; for road/outdoor/indoor track set "
        "event_name and sport_name"
    )
