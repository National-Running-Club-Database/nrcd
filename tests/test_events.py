"""Event name parsing tests."""

import pytest

from nrcd.standardize.events import applies_altitude_conversion, parse_event_distance_m
from nrcd.standardize import standardize_road


def test_parse_event_distance_m_hurdles_and_marathons():
    assert parse_event_distance_m("110m Hurdles") == 110.0
    assert parse_event_distance_m("Half Marathon") == pytest.approx(21097.5)
    assert parse_event_distance_m("Marathon") == pytest.approx(42195.0)
    assert parse_event_distance_m("8000m") == 8000.0
    assert parse_event_distance_m("5k") == pytest.approx(5000.0)
    assert parse_event_distance_m("10k") == pytest.approx(10000.0)
    assert parse_event_distance_m("3k Steeple") == pytest.approx(3000.0)
    assert parse_event_distance_m("Ultra Marathon") is None


def test_applies_altitude_conversion_for_half_marathon():
    assert applies_altitude_conversion("Half Marathon") is True
    assert applies_altitude_conversion("5k") is True
    assert applies_altitude_conversion("Team Score") is False


def test_standardize_road_half_marathon_grade_applies():
    raw = 5130.0
    no_grade = standardize_road(
        raw,
        gender="F",
        event_name="Half Marathon",
        temperature=55,
        dew_point=48,
    )
    with_grade = standardize_road(
        raw,
        gender="F",
        event_name="Half Marathon",
        temperature=55,
        dew_point=48,
        elevation_gain=1.2,
        elevation_loss=1.2,
    )
    assert with_grade != no_grade
    assert with_grade > no_grade


def test_mixed_gender_raises_on_standardize_road():
    with pytest.raises(ValueError, match="MIXED"):
        standardize_road("1:25:30", gender="MIXED", event_name="Half Marathon")


def test_standardize_road_5k_grade_applies():
    raw = 1200.0
    no_grade = standardize_road(raw, gender="M", event_name="5k")
    with_grade = standardize_road(
        raw, gender="M", event_name="5k", elevation_gain=2.0, elevation_loss=2.0,
    )
    assert with_grade != no_grade


def test_xc_race_context_event_name_5k():
    from nrcd import XCRaceContext, standardize_seconds

    std = standardize_seconds(
        XCRaceContext(time_str="22:15", gender="M", event_name="5k"),
    )
    assert std > 0
