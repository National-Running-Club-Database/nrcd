"""Round-trip and scenario tests for unstandardize_*."""

import pytest

from nrcd.standardize import (
    RaceContext,
    standardize_indoor_track,
    standardize_outdoor_track,
    standardize_result,
    standardize_road,
    standardize_seconds,
    standardize_xc,
    unstandardize_indoor_track,
    unstandardize_outdoor_track,
    unstandardize_result,
    unstandardize_road,
    unstandardize_seconds,
    unstandardize_xc,
)


def test_unstandardize_xc_roundtrip_mild_conditions():
    raw = 1650.0
    kwargs = dict(
        gender="M",
        reported_distance="5k",
        target_distance_m=8000,
        temperature=55,
        dew_point=48,
        elevation_gain=1.0,
        elevation_loss=1.0,
        meet_elevation=200,
    )
    std = standardize_xc(raw, **kwargs)
    back = unstandardize_xc(std, **kwargs)
    assert back == pytest.approx(raw, rel=1e-9)


def test_unstandardize_xc_hot_weather_slower_than_mild():
    raw = 1650.0
    base = dict(gender="M", reported_distance="5k", target_distance_m=8000)
    std = standardize_xc(
        raw,
        **base,
        temperature=55,
        dew_point=48,
    )
    hot = unstandardize_xc(
        std,
        **base,
        temperature=90,
        dew_point=70,
    )
    mild = unstandardize_xc(
        std,
        **base,
        temperature=55,
        dew_point=48,
    )
    assert hot > mild


def test_unstandardize_road_roundtrip():
    raw = 5100.0
    kwargs = dict(
        gender="F",
        event_name="Half Marathon",
        temperature=60,
        dew_point=50,
        elevation_gain=1.5,
        elevation_loss=1.5,
        meet_elevation=1500,
    )
    std = standardize_road(raw, **kwargs)
    back = unstandardize_road(std, **kwargs)
    assert back == pytest.approx(raw, rel=1e-9)


def test_unstandardize_outdoor_track_wind_roundtrip():
    raw = 13.52
    kwargs = dict(
        gender="F",
        event_name="100m",
        wind_mps=2.0,
    )
    std = standardize_outdoor_track(raw, **kwargs)
    back = unstandardize_outdoor_track(std, **kwargs)
    assert back == pytest.approx(raw, rel=1e-9)


def test_unstandardize_indoor_track_venue_roundtrip():
    raw = 22.97
    kwargs = dict(
        gender="M",
        event_name="200m",
        lap_length_m=200,
        banked=False,
        venue_reference="banked_oversized",
    )
    std = standardize_indoor_track(raw, **kwargs)
    back = unstandardize_indoor_track(std, **kwargs)
    assert back == pytest.approx(raw, rel=1e-9)


def test_unstandardize_result_matches_sport_helper():
    std = standardize_result(
        27.0,
        gender="M",
        event_name="100m",
        sport_name="Outdoor Track",
        temperature=72,
        dew_point=65,
    )
    a = unstandardize_result(
        std,
        gender="M",
        event_name="100m",
        sport_name="Outdoor Track",
        temperature=72,
        dew_point=65,
    )
    b = unstandardize_outdoor_track(
        std,
        gender="M",
        event_name="100m",
        temperature=72,
        dew_point=65,
    )
    assert a == pytest.approx(b)


def test_unstandardize_seconds_from_race_context():
    ctx = RaceContext(
        time_str="27:30",
        gender="M",
        sport_name="Cross Country",
        reported_distance="8k",
        temperature=72,
        dew_point=65,
        elevation_gain=2.5,
        elevation_loss=2.5,
        meet_elevation=5200,
        target_distance_m=8000,
    )
    std = standardize_seconds(ctx)
    ctx.time_sec = std
    ctx.time_str = None
    back = unstandardize_seconds(ctx)
    assert back == pytest.approx(27 * 60 + 30, rel=1e-9)
