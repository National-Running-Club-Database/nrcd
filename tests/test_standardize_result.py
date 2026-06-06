"""Track-specific standardization tests."""

import pytest

from nrcd.standardize import standardize_result


def test_indoor_venue_factor():
    raw = 21.80
    std = standardize_result(
        raw,
        gender="M",
        event_name="200m",
        sport_name="Indoor Track",
        lap_length_m=200,
        banked=True,
    )
    assert std > raw


def test_wind_outdoor_only():
    raw = 10.50
    outdoor = standardize_result(
        raw, gender="M", event_name="100m", sport_name="Outdoor Track", wind_mps=2.0,
    )
    indoor = standardize_result(
        raw, gender="M", event_name="100m", sport_name="Indoor Track", wind_mps=2.0,
    )
    assert outdoor != raw
    assert indoor == raw


def test_wind_scales_above_2mps():
    from nrcd.standardize.wind import wind_calm_equivalent_seconds

    raw = 10.50
    at_2 = wind_calm_equivalent_seconds(raw, 2.0, 100.0, "M")
    at_3 = wind_calm_equivalent_seconds(raw, 3.0, 100.0, "M")
    at_4 = wind_calm_equivalent_seconds(raw, 4.0, 100.0, "M")
    assert at_3 > at_2
    assert at_4 > at_3
