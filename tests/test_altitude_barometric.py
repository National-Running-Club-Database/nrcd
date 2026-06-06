import pytest

from nrcd.standardize.altitude import (
    apply_meet_altitude,
    barometric_pressure_hpa_from_record,
    barometric_pressure_torr_from_hpa,
    peronnet_f_alt,
    resolve_meet_altitude_inputs,
)


def test_f_alt_race_pressure_differs_from_venue_default():
    f_venue = peronnet_f_alt(5000, 7000, "M")
    pb_torr = barometric_pressure_torr_from_hpa(800.0)
    f_race = peronnet_f_alt(5000, 7000, "M", barometric_pressure_torr=pb_torr)
    assert 0 < f_venue < 1.0
    assert f_race != f_venue


def test_f_alt_missing_race_pressure_matches_venue_pb():
    f_default = peronnet_f_alt(5000, 7000, "M")
    f_explicit_none = peronnet_f_alt(5000, 7000, "M", barometric_pressure_torr=None)
    assert f_default == f_explicit_none


def test_barometric_from_record_prefers_nrcd_column():
    assert barometric_pressure_hpa_from_record({"barometric_pressure": 850.0}) == 850.0
    assert barometric_pressure_hpa_from_record({"barometric_pressure_hpa": 840.0}) == 840.0


def test_resolve_meet_altitude_orphan_pressure():
    elev, pb = resolve_meet_altitude_inputs(None, 850.0, warn_on_orphan_pressure=False)
    assert elev is None and pb is None


def test_apply_meet_altitude_with_pressure():
    t = apply_meet_altitude(1500.0, "8000m", 5200, "M", barometric_pressure_hpa=800.0)
    assert t != 1500.0


def test_apply_meet_altitude_pressure_only_unchanged():
    t = apply_meet_altitude(
        1500.0, "8000m", None, "M", barometric_pressure_hpa=800.0, warn_on_orphan_pressure=False
    )
    assert t == 1500.0


def test_peronnet_f_alt_mixed_averages_m_and_f():
    mixed = peronnet_f_alt(5000, 5200, "MIXED")
    m = peronnet_f_alt(5000, 5200, "M")
    f = peronnet_f_alt(5000, 5200, "F")
    assert mixed == pytest.approx((m + f) / 2.0)
