from nrcd.standardize import (
    PARAMETERS_DOC,
    required_for,
    standardize_indoor_track,
    standardize_outdoor_track,
    standardize_result,
    standardize_road,
)
from nrcd.standardize.sport import pipeline_kind
from nrcd.standardize.wind import applies_wind_conversion


def test_parameters_doc_nonempty():
    assert "sport_name" in PARAMETERS_DOC
    assert "Required" in PARAMETERS_DOC or "REQUIRED" in PARAMETERS_DOC


def test_required_for_sport_helpers():
    assert required_for("outdoor_track") == ["time", "gender", "event_name"]
    assert required_for("indoor_track") == ["time", "gender", "event_name"]
    assert required_for("road") == ["time", "gender", "event_name"]
    assert any("sport_name" in field for field in required_for("track"))


def test_wind_gated_by_outdoor_track_sport():
    assert applies_wind_conversion("100m", "Outdoor Track")
    assert not applies_wind_conversion("100m", "Indoor Track")
    assert not applies_wind_conversion("100m", None)


def test_wind_only_applied_with_sport():
    t = 10.5
    with_wind = standardize_result(
        t, gender="M", event_name="100m", sport_name="Outdoor Track", wind_mps=2.0
    )
    no_sport_wrong = standardize_result(
        t, gender="M", event_name="100m", sport_name="Indoor Track", wind_mps=2.0
    )
    assert with_wind != t
    assert no_sport_wrong == t


def test_standardize_result_accepts_clock_string():
    t = 252.0  # 4:12.00
    std_num = standardize_result(
        t, gender="M", event_name="Mile", sport_name="Outdoor Track",
    )
    std_clock = standardize_result(
        "4:12.00", gender="M", event_name="Mile", sport_name="Outdoor Track",
    )
    assert std_clock == std_num


def test_pipeline_kind():
    assert pipeline_kind("Cross Country") == "xc"
    assert pipeline_kind("Outdoor Track") == "track"


def test_sport_entry_points_match_result():
    t = 10.5
    outdoor = standardize_outdoor_track(
        t, gender="M", event_name="100m", wind_mps=2.0,
    )
    indoor = standardize_indoor_track(
        t, gender="M", event_name="100m", wind_mps=2.0,
    )
    assert outdoor == standardize_result(
        t, gender="M", event_name="100m", sport_name="Outdoor Track", wind_mps=2.0,
    )
    assert indoor == standardize_result(
        t, gender="M", event_name="100m", sport_name="Indoor Track", wind_mps=2.0,
    )


def test_standardize_road_matches_result():
    t = 3600.0
    road = standardize_road(
        t, gender="M", event_name="5000m", elevation_gain=1.0, elevation_loss=1.0,
    )
    assert road == standardize_result(
        t,
        gender="M",
        event_name="5000m",
        sport_name="Road",
        elevation_gain=1.0,
        elevation_loss=1.0,
    )


def test_standardize_indoor_track_matches_result():
    from nrcd.standardize import standardize_indoor_track

    t = 21.80
    indoor = standardize_indoor_track(
        t, gender="M", event_name="200m", lap_length_m=200, banked=True,
    )
    assert indoor == standardize_result(
        t,
        gender="M",
        event_name="200m",
        sport_name="Indoor Track",
        lap_length_m=200,
        banked=True,
    )
