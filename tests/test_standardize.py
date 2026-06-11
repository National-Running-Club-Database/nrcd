import pytest

from nrcd.standardize import (
    StandardizeConfig,
    c_to_f,
    elevation_factor,
    grade_percent_from_feet,
    grade_percent_from_meters,
    heat_index,
    parse_distance,
    parse_time,
    peronnet_f_alt,
    standardize_result,
    standardize_xc,
    temperature_to_fahrenheit,
    weather_factor,
    xc_target_distance_m,
)
from nrcd.standardize.units import resolve_grade_percent


def test_heat_index_fahrenheit():
    assert heat_index(80, 70) == 150


def test_weather_no_adjustment_below_100():
    assert weather_factor(50, 40) == 1.0


def test_weather_slowdown_above_100():
    f = weather_factor(90, 20)
    assert 0 < f < 1.0


def test_temperature_c_to_f_for_weather():
    temp_f = temperature_to_fahrenheit(22, "C")
    dew_f = temperature_to_fahrenheit(18, "C")
    assert temp_f == pytest.approx(c_to_f(22))
    assert weather_factor(temp_f, dew_f) == weather_factor(c_to_f(22), c_to_f(18))


def test_elevation_factor_percent_grade():
    assert elevation_factor(0, 0) == 1.0
    assert elevation_factor(1, 1) == pytest.approx(1.04 * 0.9633)


def test_grade_feet_to_percent():
    gain, loss = grade_percent_from_feet(400, 400, 8000)
    assert gain == pytest.approx(1.524)
    assert loss == pytest.approx(1.524)
    g, l = resolve_grade_percent(400, 400, grade_input="feet", course_distance_m=8000)
    assert elevation_factor(g, l) == elevation_factor(1.524, 1.524)


def test_grade_meters_to_percent():
    gain, loss = grade_percent_from_meters(120, 120, 8000)
    assert gain == pytest.approx(1.5)
    assert loss == pytest.approx(1.5)
    g, l = resolve_grade_percent(120, 120, grade_input="m", course_distance_m=8000)
    assert elevation_factor(g, l) == elevation_factor(1.5, 1.5)


def test_standardize_xc_riegel_to_target():
    cfg = StandardizeConfig()
    raw = 1600.0
    std = standardize_xc(
        raw,
        gender="M",
        reported_distance_m=8000,
        actual_distance_m=8000,
        target_distance_m=cfg.xc_target_men_m,
        apply_weather=False,
        apply_elevation_grade=False,
        apply_meet_altitude_correction=False,
        config=cfg,
    )
    b = cfg.riegel_b_men
    expected = raw * (cfg.xc_target_men_m / 8000) ** b
    assert std == pytest.approx(expected)


def test_peronnet_high_altitude_f_alt_below_one():
    f = peronnet_f_alt(5000, 7000, "M")
    assert 0 < f < 1.0


def test_invalid_time_raises():
    with pytest.raises(ValueError, match="invalid time"):
        standardize_xc(float("nan"), gender="M", reported_distance_m=8000)
    with pytest.raises(ValueError, match="invalid time string"):
        parse_time("not-a-time")
    with pytest.raises(ValueError, match="invalid time"):
        standardize_result("bad", gender="M", event_name="100m", sport_name="Outdoor Track")


def test_invalid_distance_raises():
    with pytest.raises(ValueError, match="reported distance is required"):
        standardize_xc("22:15", gender="M")
    with pytest.raises(ValueError, match="invalid distance"):
        parse_distance("five miles")
    with pytest.raises(ValueError, match="invalid distance_unit"):
        parse_distance(5, unit="feet")  # type: ignore[arg-type]


def test_invalid_unit_kwargs_raise():
    with pytest.raises(ValueError, match="invalid temp_unit"):
        standardize_xc("22:15", gender="M", reported_distance="5k", temp_unit="K")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="invalid grade_input"):
        standardize_xc("22:15", gender="M", reported_distance="5k", grade_input="yards")  # type: ignore[arg-type]


def test_parse_time_formats():
    assert parse_time("22:15") == pytest.approx(22 * 60 + 15)
    assert parse_time("1:10:13") == pytest.approx(3600 + 10 * 60 + 13)


def test_parse_distance_units():
    assert parse_distance(5, unit="km") == pytest.approx(5000)
    assert parse_distance(8, unit="mi") == pytest.approx(8 * 1609.34)
    assert parse_distance("5k") == pytest.approx(5000)
    assert parse_distance("8000m") == pytest.approx(8000)


def test_xc_target_distance_m_defaults():
    assert xc_target_distance_m("M") == 8000.0
    assert xc_target_distance_m("F") == 6000.0


def test_standardize_xc_target_distance_label():
    raw = parse_time("22:15")
    std_m = standardize_xc(
        "22:15",
        gender="M",
        reported_distance="5k",
        target_distance_m=8000,
        apply_weather=False,
        apply_elevation_grade=False,
        apply_meet_altitude_correction=False,
    )
    std_k = standardize_xc(
        "22:15",
        gender="M",
        reported_distance="5k",
        target_distance="8k",
        apply_weather=False,
        apply_elevation_grade=False,
        apply_meet_altitude_correction=False,
    )
    std_unit = standardize_xc(
        "22:15",
        gender="M",
        reported_distance="5k",
        target_distance=8,
        target_distance_unit="km",
        apply_weather=False,
        apply_elevation_grade=False,
        apply_meet_altitude_correction=False,
    )
    assert std_m == pytest.approx(std_k)
    assert std_m == pytest.approx(std_unit)
    assert std_m > raw


def test_standardize_xc_target_distance_conflict_raises():
    with pytest.raises(ValueError, match="not both"):
        standardize_xc(
            "22:15",
            gender="M",
            reported_distance="5k",
            target_distance_m=8000,
            target_distance="8k",
        )


def test_standardize_xc_no_target_skips_riegel():
    raw = parse_time("22:15")
    std = standardize_xc(
        "22:15",
        gender="M",
        reported_distance="5k",
        apply_weather=False,
        apply_elevation_grade=False,
        apply_meet_altitude_correction=False,
    )
    assert std == pytest.approx(raw)


def test_standardize_xc_time_string_and_km():
    cfg = StandardizeConfig()
    raw = parse_time("22:15")
    std = standardize_xc(
        "22:15",
        gender="M",
        reported_distance=5,
        distance_unit="km",
        apply_weather=False,
        apply_elevation_grade=False,
        apply_meet_altitude_correction=False,
        config=cfg,
    )
    expected = standardize_xc(
        raw,
        gender="M",
        reported_distance_m=5000,
        apply_weather=False,
        apply_elevation_grade=False,
        apply_meet_altitude_correction=False,
        config=cfg,
    )
    assert std == pytest.approx(expected)


def test_standardize_xc_miles():
    cfg = StandardizeConfig()
    raw = parse_time("1:10:13")
    std = standardize_xc(
        "1:10:13",
        gender="M",
        reported_distance=8,
        distance_unit="mi",
        apply_weather=False,
        apply_elevation_grade=False,
        apply_meet_altitude_correction=False,
        config=cfg,
    )
    expected = standardize_xc(
        raw,
        gender="M",
        reported_distance_m=8 * 1609.34,
        apply_weather=False,
        apply_elevation_grade=False,
        apply_meet_altitude_correction=False,
        config=cfg,
    )
    assert std == pytest.approx(expected)


def test_invalid_gender_raises():
    with pytest.raises(ValueError, match="invalid gender"):
        standardize_xc("22:15", gender="Male", reported_distance="5k")


def test_mixed_gender_raises_on_standardize_xc():
    with pytest.raises(ValueError, match="MIXED"):
        standardize_xc("22:15", gender="MIXED", reported_distance="5k")


def test_format_time_round_trip():
    from nrcd.standardize import format_time

    assert format_time(1335.0) == "22:15.00"
    assert format_time(10.5) == "10.50"


def test_format_time_invalid_returns_empty_string():
    from nrcd.standardize import format_time

    assert format_time(-1.0) == ""
    assert format_time(float("nan")) == ""
    assert format_time(float("inf")) == ""


def test_meet_elevation_zero_sea_level():
    raw = 930.0
    std = standardize_result(
        raw,
        gender="M",
        event_name="5000m",
        sport_name="Outdoor Track",
        meet_elevation=0,
    )
    assert std == pytest.approx(raw)


def test_standardize_seconds_xc_and_track():
    from nrcd.standardize import RaceContext, standardize_seconds

    xc = standardize_seconds(
        RaceContext(time_str="22:15", gender="M", sport_name="Cross Country", reported_distance="5k")
    )
    assert xc > 0
    track = standardize_seconds(
        RaceContext(
            time_str="10.52", gender="M", event_name="100m", sport_name="Outdoor Track",
        )
    )
    assert track > 0


def test_standardize_seconds_incomplete_raises():
    from nrcd.standardize import RaceContext, standardize_seconds

    with pytest.raises(ValueError, match="cannot standardize"):
        standardize_seconds(RaceContext(time_str="22:15", gender="M"))


def test_standardize_seconds_xc_no_distance_raises():
    from nrcd.standardize import RaceContext, standardize_seconds

    with pytest.raises(ValueError, match="cannot resolve XC distance"):
        standardize_seconds(
            RaceContext(
                time_str="22:15",
                gender="M",
                sport_name="Cross Country",
                event_name="Team Score",
            )
        )


def test_standardize_seconds_xc_race_context():
    from nrcd.standardize import XCRaceContext, standardize_seconds

    expected = standardize_xc("22:15", gender="M", reported_distance_m=8000)
    std = standardize_seconds(
        XCRaceContext(time_str="22:15", gender="M", event_name="8000m")
    )
    assert std == pytest.approx(expected)
