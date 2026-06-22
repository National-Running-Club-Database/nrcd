"""NCAA venue reference selection and comparison."""

import pytest

from nrcd.standardize import (
    compare_venue_references,
    standardize_indoor_track,
    standardize_outdoor_track,
    venue_reference_factor_table,
)
from nrcd.standardize.track import (
    TRACK_VENUE_REFERENCES,
    default_venue_reference,
    infer_indoor_track_type,
    ncaa_index_multiplier,
    resolve_venue_reference,
    track_venue_factor,
    venue_reference_factor,
)


def test_default_venue_reference_by_sport():
    assert default_venue_reference(indoor=True) == "banked_oversized"
    assert default_venue_reference(indoor=False) == "outdoor_flat_400m"


def test_infer_indoor_track_type_ncaa_categories():
    assert infer_indoor_track_type(180, banked=False) == "undersized"
    assert infer_indoor_track_type(200, banked=False) == "flat"
    assert infer_indoor_track_type(200, banked=True) == "banked_oversized"
    assert infer_indoor_track_type(220, banked=False) == "banked_oversized"


def test_ncaa_tables_match_charts_men_200m():
    assert ncaa_index_multiplier(200, "M", "flat_to_banked") == pytest.approx(0.9824)
    assert ncaa_index_multiplier(200, "M", "undersized_to_banked") == pytest.approx(0.9698)


def test_200m_flat_default_reference_men():
    raw = 22.97
    std = standardize_indoor_track(
        raw,
        gender="M",
        event_name="200m",
        lap_length_m=200,
        banked=False,
    )
    assert std == pytest.approx(raw * 0.9824)
    assert std < raw


def test_200m_flat_explicit_indoor_flat_reference():
    raw = 22.97
    std = standardize_indoor_track(
        raw,
        gender="M",
        event_name="200m",
        lap_length_m=200,
        banked=False,
        venue_reference="indoor_flat",
    )
    assert std == pytest.approx(raw)


def test_200m_banked_default_unchanged():
    raw = 22.97
    std = standardize_indoor_track(
        raw,
        gender="M",
        event_name="200m",
        lap_length_m=200,
        banked=True,
    )
    assert std == pytest.approx(raw)


def test_200m_banked_to_indoor_flat():
    raw = 22.97
    std = standardize_indoor_track(
        raw,
        gender="M",
        event_name="200m",
        lap_length_m=200,
        banked=True,
        venue_reference="indoor_flat",
    )
    assert std == pytest.approx(raw * 1.0179, rel=1e-3)


def test_oversized_lap_reference_unchanged():
    raw = 22.97
    std = standardize_indoor_track(
        raw,
        gender="M",
        event_name="200m",
        lap_length_m=400,
        banked=False,
    )
    assert std == pytest.approx(raw)


def test_compare_venue_references_200m_flat():
    raw = 22.97
    refs = compare_venue_references(
        raw,
        gender="M",
        event_name="200m",
        sport_name="Indoor Track",
        lap_length_m=200,
        banked=False,
    )
    assert set(refs) == set(TRACK_VENUE_REFERENCES)
    assert refs["banked_oversized"] == pytest.approx(raw * 0.9824)
    assert refs["indoor_flat"] == pytest.approx(raw)
    assert refs["outdoor_flat_400m"] == pytest.approx(raw)


def test_venue_reference_factor_table_matches_full_std_venue_only():
    raw = 22.97
    factors = venue_reference_factor_table(
        "200m",
        "M",
        lap_length_m=200,
        banked=False,
        sport_name="Indoor Track",
    )
    for ref, factor in factors.items():
        std = standardize_indoor_track(
            raw,
            gender="M",
            event_name="200m",
            lap_length_m=200,
            banked=False,
            venue_reference=ref,
        )
        assert std == pytest.approx(raw * factor)


def test_outdoor_400m_default_reference():
    raw = 10.52
    std = standardize_outdoor_track(
        raw,
        gender="M",
        event_name="100m",
        lap_length_m=400,
    )
    assert std == pytest.approx(raw)


def test_outdoor_400m_to_banked_reference():
    raw = 10.52
    std = standardize_outdoor_track(
        raw,
        gender="M",
        event_name="100m",
        lap_length_m=400,
        venue_reference="banked_oversized",
    )
    assert std == pytest.approx(raw * 0.9824, rel=1e-3)


def test_resolve_venue_reference_aliases():
    assert resolve_venue_reference("flat", indoor=True) == "indoor_flat"
    assert resolve_venue_reference("outdoor_400m", indoor=False) == "outdoor_flat_400m"


def test_track_venue_factor_flat_vs_oversized():
    flat_200 = track_venue_factor(
        "200m", "M", lap_length_m=200, banked=False, sport_name="Indoor Track",
    )
    oversized = track_venue_factor(
        "200m", "M", lap_length_m=400, banked=False, sport_name="Indoor Track",
    )
    assert flat_200 == pytest.approx(0.9824)
    assert oversized == pytest.approx(1.0)


def test_venue_reference_factor_matrix_roundtrip():
    f2b = venue_reference_factor(200, "M", source_type="flat", venue_reference="banked_oversized")
    b2f = venue_reference_factor(
        200, "M", source_type="banked_oversized", venue_reference="indoor_flat",
    )
    assert f2b * b2f == pytest.approx(1.0, rel=1e-6)


def test_undersized_to_banked_men_200m():
    raw = 23.50
    std = standardize_indoor_track(
        raw,
        gender="M",
        event_name="200m",
        lap_length_m=180,
        banked=False,
    )
    assert std == pytest.approx(raw * 0.9698, rel=1e-3)


def test_200m_flat_women():
    raw = 24.50
    std = standardize_indoor_track(
        raw,
        gender="F",
        event_name="200m",
        lap_length_m=200,
        banked=False,
    )
    assert std == pytest.approx(raw * 0.9847, rel=1e-3)


def test_compare_venue_references_subset():
    refs = compare_venue_references(
        22.97,
        gender="M",
        event_name="200m",
        sport_name="Indoor Track",
        lap_length_m=200,
        banked=False,
        references=["indoor_flat", "banked_oversized"],
    )
    assert set(refs) == {"indoor_flat", "banked_oversized"}


def test_resolve_venue_reference_unknown_raises():
    with pytest.raises(ValueError, match="unknown venue_reference"):
        resolve_venue_reference("not_a_venue", indoor=True)
