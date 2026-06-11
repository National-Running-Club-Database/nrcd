"""README Quick start examples — imports and documented output times."""

from nrcd.standardize import (
    format_time,
    standardize_indoor_track,
    standardize_outdoor_track,
    standardize_road,
    standardize_xc,
)


def test_readme_xc_5k_target_8000m():
    std = standardize_xc(
        "22:15",
        gender="M",
        reported_distance="5k",
        target_distance_m=8000,
    )
    assert format_time(std) == "36:31.94"


def test_readme_xc_8km_with_conditions():
    std = standardize_xc(
        "27:30",
        gender="M",
        reported_distance=8,
        distance_unit="km",
        actual_distance=8.01,
        temperature=72,
        dew_point=65,
        elevation_gain=2.5,
        elevation_loss=2.5,
        meet_elevation=5200,
        target_distance_m=8000,
    )
    assert format_time(std) == "26:42.19"


def test_readme_outdoor_track_100m():
    std = standardize_outdoor_track(
        "13.52",
        gender="F",
        event_name="100m",
        wind_mps=2.0,
    )
    assert f"{std:.3f} s" == "13.630 s"


def test_readme_indoor_track_200m():
    std = standardize_indoor_track(
        "21.80",
        gender="M",
        event_name="200m",
        lap_length_m=200,
        banked=True,
    )
    assert f"{std:.3f} s" == "22.588 s"


def test_readme_road_half_marathon():
    std = standardize_road(
        "1:25:30",
        gender="F",
        event_name="Half Marathon",
        temperature=55,
        dew_point=48,
        elevation_gain=1.2,
        elevation_loss=1.2,
    )
    assert format_time(std) == "1:25:40.54"
