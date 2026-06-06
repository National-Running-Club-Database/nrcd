import warnings

import pytest

from nrcd.standardize import apply_course_grade_factor, standardize_xc
from nrcd.standardize.grade import warn_one_sided_course_grade


def test_warn_one_sided_gain_only():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        warn_one_sided_course_grade(2.0, None)
        assert len(w) == 1
        assert "elevation_loss" in str(w[0].message).lower()


def test_no_warn_when_both_sides():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        warn_one_sided_course_grade(2.0, 1.0)
        assert len(w) == 0


def test_apply_course_grade_factor():
    out = apply_course_grade_factor(1000.0, 2.0, 1.0, course_distance_m=8000)
    assert out == pytest.approx(1000.0 * (1.04**2) * 0.9633)


def test_standardize_xc_one_sided_grade_warns():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        standardize_xc(
            1500.0, gender="M", reported_distance_m=8000, elevation_gain=3.0
        )
        assert any("elevation_loss" in str(x.message).lower() for x in w)


def test_standardize_result_grade_on_road():
    from nrcd.standardize import standardize_road

    t_grade = standardize_road(
        1200.0,
        gender="M",
        event_name="5000m",
        sport_name="Road Race",
        elevation_gain=2.0,
        elevation_loss=2.0,
    )
    assert t_grade != 1200.0
