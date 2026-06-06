from nrcd.data.schema import (
    derive_course_details_fields,
    meet_altitude_column,
    meet_altitude_ft_from_record,
)


def test_meet_altitude_column_prefers_altitude():
    import pandas as pd

    assert meet_altitude_column(pd.DataFrame({"altitude": [1]})) == "altitude"
    assert meet_altitude_column(pd.DataFrame({"elevation": [1]})) == "elevation"


def test_meet_altitude_ft_from_record():
    assert meet_altitude_ft_from_record({"altitude": 5200}) == 5200.0
    assert meet_altitude_ft_from_record({"elevation": 100}, {"altitude": 200}) == 100.0
    assert meet_altitude_ft_from_record({}, {"altitude": 300}) == 300.0
    assert meet_altitude_ft_from_record({"altitude": 0}) == 0.0


def test_derive_course_details_fields():
    derived = derive_course_details_fields(
        {
            "temperature": 80,
            "dew_point": 70,
            "openweather_dt_unix": 1_700_000_000,
            "sunrise_unix": 1_699_990_000,
            "sunset_unix": 1_700_010_000,
        }
    )
    assert derived["heat_index_f"] == 150.0
    assert derived["is_daylight"] is True
    assert derived["minutes_after_sunrise"] > 0
