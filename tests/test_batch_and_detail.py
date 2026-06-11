import datetime as dt

import pytest

from nrcd.enrich.cache import clear_enrich_cache
from nrcd.standardize import (
    DataframeBatchResult,
    RaceContext,
    StandardizeDetail,
    enrich_dataframe,
    standardize_dataframe,
    standardize_outdoor_track,
    standardize_result_detail,
    standardize_seconds_detail,
    standardize_xc,
    standardize_xc_detail,
)


def test_standardize_xc_detail_matches_standardize_xc():
    kwargs = dict(
        gender="M",
        reported_distance="5k",
        target_distance_m=8000,
        temperature=72,
        dew_point=65,
        elevation_gain=2.5,
        elevation_loss=2.5,
        meet_elevation=5200,
    )
    std = standardize_xc("27:30", **kwargs)
    detail = standardize_xc_detail("27:30", **kwargs)
    assert isinstance(detail, StandardizeDetail)
    assert detail.std_sec == pytest.approx(std)
    assert detail.raw_sec == pytest.approx(27 * 60 + 30)
    names = [s.name for s in detail.steps]
    assert names == ["weather", "grade", "altitude", "target_distance"]


def test_standardize_xc_detail_target_distance_step_note():
    detail = standardize_xc_detail(
        "22:15",
        gender="M",
        reported_distance="5k",
        target_distance_m=8000,
    )
    target = next(s for s in detail.steps if s.name == "target_distance")
    assert target.note is not None
    assert "8000" in target.note


def test_standardize_result_detail_wind_step():
    std = standardize_outdoor_track(
        "13.52", gender="F", event_name="100m", wind_mps=2.0,
    )
    detail = standardize_result_detail(
        "13.52",
        gender="F",
        event_name="100m",
        sport_name="Outdoor Track",
        wind_mps=2.0,
    )
    assert detail.std_sec == pytest.approx(std)
    wind = next(s for s in detail.steps if s.name == "wind")
    assert wind.applied
    assert wind.delta_sec == pytest.approx(wind.time_after_sec - wind.time_before_sec)


def test_standardize_seconds_detail_from_context():
    ctx = RaceContext(
        time_str="22:15",
        gender="M",
        sport_name="Cross Country",
        reported_distance="5k",
        target_distance_m=8000,
    )
    detail = standardize_seconds_detail(ctx)
    assert detail.std_sec == pytest.approx(
        standardize_xc("22:15", gender="M", reported_distance="5k", target_distance_m=8000)
    )


def test_standardize_dataframe_xc_rows():
    pd = pytest.importorskip("pandas")

    df = pd.DataFrame(
        [
            {
                "gender": "M",
                "result_time": "22:15",
                "sport_name": "Cross Country",
                "reported_distance": "5k",
                "target_distance_m": 8000,
            },
            {
                "gender": "F",
                "result_time": "24:30",
                "sport_name": "Cross Country",
                "reported_distance": "6k",
                "target_distance_m": 6000,
            },
        ]
    )
    out = standardize_dataframe(df)
    assert "std_time_sec" in out.columns
    assert out.loc[0, "std_time_sec"] == pytest.approx(
        standardize_xc("22:15", gender="M", reported_distance="5k", target_distance_m=8000)
    )
    assert out.loc[1, "std_time_sec"] == pytest.approx(
        standardize_xc("24:30", gender="F", reported_distance="6k", target_distance_m=6000)
    )


def test_standardize_dataframe_with_detail_column():
    pd = pytest.importorskip("pandas")

    df = pd.DataFrame(
        [
            {
                "gender": "M",
                "time_sec": 10.52,
                "event_name": "100m",
                "sport_name": "Outdoor Track",
                "wind_mps": 2.0,
            },
        ]
    )
    out = standardize_dataframe(df, detail=True)
    detail = out.loc[0, "std_detail"]
    assert isinstance(detail, StandardizeDetail)
    assert detail.factor("wind") is not None


def setup_function():
    clear_enrich_cache()


def test_enrich_dataframe_fills_weather_columns(monkeypatch):
    pd = pytest.importorskip("pandas")
    from nrcd.enrich.weather import WeatherData

    monkeypatch.setattr(
        "nrcd.enrich.context.fetch_weather",
        lambda *a, **k: WeatherData(temperature=68.0, dew_point=58.0),
    )
    df = pd.DataFrame(
        [
            {
                "gender": "M",
                "result_time": "22:15",
                "sport_name": "Cross Country",
                "reported_distance": "5k",
                "city": "Notre Dame",
                "state": "IN",
                "event_date": "2024-10-12",
                "event_time": "10:00",
            },
        ]
    )
    out = enrich_dataframe(
        df, fetch_altitude=False, config=_fake_enrich_config(),
    )
    assert out.loc[0, "temperature"] == 68.0
    assert out.loc[0, "dew_point"] == 58.0


def test_enrich_dataframe_dedupes_weather_per_meet(monkeypatch):
    pd = pytest.importorskip("pandas")
    from nrcd.enrich.weather import WeatherData

    calls = {"n": 0}

    def counting_uncached(*a, **k):
        calls["n"] += 1
        return WeatherData(temperature=70.0, dew_point=55.0)

    monkeypatch.setattr("nrcd.enrich.weather._fetch_weather_uncached", counting_uncached)

    base = {
        "sport_name": "Cross Country",
        "reported_distance": "5k",
        "city": "Notre Dame",
        "state": "IN",
        "event_date": dt.date(2024, 10, 12),
        "event_time": dt.time(10, 0),
    }
    rows = [
        {"gender": "M", "result_time": "22:15", **base},
        {"gender": "M", "result_time": "22:20", **base},
        {"gender": "F", "result_time": "24:30", **base},
    ]
    out = enrich_dataframe(
        pd.DataFrame(rows), fetch_altitude=False, config=_fake_enrich_config(),
    )
    assert calls["n"] == 1
    assert out["temperature"].tolist() == [70.0, 70.0, 70.0]


def test_enrich_dataframe_altitude_only_usgs(monkeypatch):
    pd = pytest.importorskip("pandas")
    from nrcd.enrich.altitude import AltitudeResult

    geocode_calls = {"n": 0}
    usgs_calls = {"n": 0}

    def fake_geocode(*a, **k):
        geocode_calls["n"] += 1
        return 41.66, -86.23

    def fake_usgs(*a, **k):
        usgs_calls["n"] += 1
        return AltitudeResult(
            altitude_ft=750.0,
            lat=41.66,
            lon=-86.23,
            city="Notre Dame",
            state="IN",
        )

    monkeypatch.setattr("nrcd.enrich.geocode._geocode_http", fake_geocode)
    monkeypatch.setattr("nrcd.enrich.altitude._altitude_from_coords", fake_usgs)

    rows = [
        {
            "gender": "M",
            "result_time": "22:15",
            "sport_name": "Cross Country",
            "reported_distance": "5k",
            "city": "Notre Dame",
            "state": "IN",
        },
        {
            "gender": "F",
            "result_time": "24:30",
            "sport_name": "Cross Country",
            "reported_distance": "6k",
            "city": "Notre Dame",
            "state": "IN",
        },
    ]
    out = enrich_dataframe(
        pd.DataFrame(rows),
        fetch_weather=False,
        config=_fake_enrich_config(),
    )
    assert out["meet_elevation"].tolist() == [750.0, 750.0]
    assert geocode_calls["n"] == 1
    assert usgs_calls["n"] == 1


def test_enrich_dataframe_return_usage(monkeypatch):
    pd = pytest.importorskip("pandas")
    from nrcd.enrich.weather import WeatherData

    monkeypatch.setattr(
        "nrcd.enrich.context.fetch_weather",
        lambda *a, **k: WeatherData(temperature=68.0, dew_point=58.0),
    )
    rows = [
        {
            "gender": "M",
            "result_time": "22:15",
            "sport_name": "Cross Country",
            "reported_distance": "5k",
            "city": "Notre Dame",
            "state": "IN",
            "event_date": "2024-10-12",
            "event_time": "10:00",
        },
    ]
    result = enrich_dataframe(
        pd.DataFrame(rows),
        fetch_altitude=False,
        config=_fake_enrich_config(),
        return_usage=True,
    )
    assert isinstance(result, DataframeBatchResult)
    assert result.dataframe.loc[0, "temperature"] == 68.0
    assert result.api_usage is not None
    usage_dict = result.api_usage.to_dict()
    assert "openweather_total" in usage_dict
    assert "openweather_geocode" in usage_dict


def test_standardize_dataframe_with_enrich(monkeypatch):
    pd = pytest.importorskip("pandas")
    from nrcd.enrich.weather import WeatherData

    monkeypatch.setattr(
        "nrcd.enrich.context.fetch_weather",
        lambda *a, **k: WeatherData(temperature=68.0, dew_point=58.0),
    )
    df = pd.DataFrame(
        [
            {
                "gender": "M",
                "result_time": "22:15",
                "sport_name": "Cross Country",
                "reported_distance": "5k",
                "city": "Notre Dame",
                "state": "IN",
                "event_date": "2024-10-12",
                "event_time": "10:00",
            },
        ]
    )
    out = standardize_dataframe(
        df, enrich=True, fetch_altitude=False, enrich_config=_fake_enrich_config(),
    )
    assert out.loc[0, "temperature"] == 68.0
    assert out.loc[0, "std_time_sec"] == pytest.approx(
        standardize_xc(
            "22:15",
            gender="M",
            reported_distance="5k",
            temperature=68.0,
            dew_point=58.0,
        )
    )


def test_standardize_dataframe_enrich_and_detail(monkeypatch):
    pd = pytest.importorskip("pandas")
    from nrcd.enrich.weather import WeatherData

    monkeypatch.setattr(
        "nrcd.enrich.context.fetch_weather",
        lambda *a, **k: WeatherData(temperature=72.0, dew_point=65.0),
    )
    df = pd.DataFrame(
        [
            {
                "gender": "M",
                "result_time": "27:30",
                "sport_name": "Cross Country",
                "reported_distance": 8,
                "distance_unit": "km",
                "elevation_gain": 2.5,
                "elevation_loss": 2.5,
                "meet_elevation": 5200,
                "target_distance_m": 8000,
                "city": "Notre Dame",
                "state": "IN",
                "event_date": "2024-10-12",
                "event_time": "10:00",
            },
        ]
    )
    out = standardize_dataframe(
        df,
        enrich=True,
        detail=True,
        fetch_altitude=False,
        enrich_config=_fake_enrich_config(),
    )
    detail = out.loc[0, "std_detail"]
    assert isinstance(detail, StandardizeDetail)
    assert out.loc[0, "std_time_sec"] == pytest.approx(detail.std_sec)
    assert out.loc[0, "std_time_sec"] == pytest.approx(
        standardize_xc_detail(
            "27:30",
            gender="M",
            reported_distance=8,
            distance_unit="km",
            temperature=72.0,
            dew_point=65.0,
            elevation_gain=2.5,
            elevation_loss=2.5,
            meet_elevation=5200,
            target_distance_m=8000,
        ).std_sec
    )
    assert [s.name for s in detail.steps] == [
        "weather", "grade", "altitude", "target_distance",
    ]


def _fake_enrich_config():
    from nrcd.enrich.config import EnrichConfig

    return EnrichConfig(openweather_api_key="k", timezone_api_key="tz")


def test_standardize_dataframe_requires_pandas(monkeypatch):
    import builtins

    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "pandas":
            raise ImportError("no pandas")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    from nrcd.standardize.batch import standardize_dataframe as sdf

    with pytest.raises(ImportError, match="pandas"):
        sdf({"a": 1})  # type: ignore[arg-type]
