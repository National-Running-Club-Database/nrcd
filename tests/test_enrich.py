import datetime as dt

import pytest

from nrcd.standardize import XCRaceContext


def test_api_guide_nonempty():
    from nrcd.enrich import API_GUIDE

    assert "OpenWeather" in API_GUIDE
    assert "USGS" in API_GUIDE


def test_lookup_altitude_mock(monkeypatch):
    from nrcd.enrich.altitude import AltitudeResult, lookup_altitude_ft

    monkeypatch.setattr("nrcd.enrich.geocode._geocode_http", lambda *a, **k: (40.0, -105.0))
    monkeypatch.setattr(
        "nrcd.enrich.altitude._altitude_from_coords",
        lambda *a, **k: AltitudeResult(altitude_ft=5400, lat=40.0, lon=-105.0, city="Boulder", state="CO"),
    )
    ft = lookup_altitude_ft("Boulder", "CO", openweather_api_key="k")
    assert ft == 5400


def test_fetch_weather_mock(monkeypatch):
    from nrcd.enrich.api_usage import ApiUsage
    from nrcd.enrich.weather import fetch_weather, WeatherData

    monkeypatch.setattr(
        "nrcd.enrich.weather._fetch_weather_uncached",
        lambda *a, **k: WeatherData(
            temperature=70.0, dew_point=50.0, real_feel=72.0,
            barometric_pressure=850.0, openweather_dt_unix=1_700_000_000,
        ),
    )
    usage = ApiUsage()
    wx = fetch_weather(
        "Boulder", "CO",
        event_date=dt.date(2024, 9, 1),
        event_time=dt.time(9, 0),
        openweather_api_key="k",
        timezone_api_key="tz",
        usage=usage,
    )
    assert wx.temperature == 70.0


def test_fetch_weather_skips_geocode_with_coords(monkeypatch):
    from nrcd.enrich.api_usage import ApiUsage
    from nrcd.enrich.weather import fetch_weather, WeatherData

    geocode_calls = {"n": 0}

    def fake_geocode(*a, **k):
        geocode_calls["n"] += 1
        return 40.0, -105.0

    monkeypatch.setattr("nrcd.enrich.weather.geocode_location", fake_geocode)
    monkeypatch.setattr(
        "nrcd.enrich.weather._fetch_weather_uncached",
        lambda *a, **k: WeatherData(temperature=65.0, dew_point=45.0),
    )
    fetch_weather(
        "Boulder", "CO",
        event_date=dt.date(2024, 9, 1),
        event_time=dt.time(9, 0),
        openweather_api_key="k",
        timezone_api_key="tz",
        lat=40.015,
        lon=-105.27,
        timezone_name="America/Denver",
        usage=ApiUsage(),
    )
    assert geocode_calls["n"] == 0


def test_enrich_race_context_result_altitude(monkeypatch):
    from nrcd.enrich import enrich_race_context_result
    from nrcd.enrich.api_usage import ApiUsage

    monkeypatch.setattr("nrcd.enrich.context.lookup_altitude_ft", lambda *a, **k: 5200)
    ctx = XCRaceContext(
        gender="M", time_str="25:00", reported_distance_m=8000,
        sport_name="Cross Country", city="Boulder", state="CO",
    )
    result = enrich_race_context_result(
        ctx, openweather_api_key="k", fetch_weather_fields=False
    )
    assert result.context.meet_elevation == 5200.0
    assert isinstance(result.api_usage, ApiUsage)


def test_enrich_race_context_weather(monkeypatch):
    from nrcd.enrich import enrich_race_context_result
    from nrcd.enrich.weather import WeatherData

    monkeypatch.setattr(
        "nrcd.enrich.context.fetch_weather",
        lambda *a, **k: WeatherData(temperature=80.0, dew_point=60.0, barometric_pressure=840.0),
    )
    ctx = XCRaceContext(
        gender="M", time_str="25:00", reported_distance_m=8000,
        sport_name="Cross Country", city="Boulder", state="CO",
        event_date=dt.date(2024, 9, 1), event_time=dt.time(9, 0),
    )
    out = enrich_race_context_result(
        ctx, openweather_api_key="k", timezone_api_key="tz", fetch_altitude=False
    ).context
    assert out.temperature == 80.0


def test_enrich_race_context_result_returns_usage():
    from nrcd.enrich import enrich_race_context_result

    ctx = XCRaceContext(
        gender="M", time_str="25:00", reported_distance_m=8000,
        sport_name="Cross Country",
    )
    result = enrich_race_context_result(ctx, fetch_altitude=False, fetch_weather_fields=False)
    assert result.api_usage.total == 0


def test_enrich_altitude_requires_location():
    from nrcd.enrich import enrich_race_context_result

    ctx = XCRaceContext(gender="M", time_str="25:00", reported_distance_m=8000)
    with pytest.raises(ValueError, match="city and state"):
        enrich_race_context_result(ctx, openweather_api_key="k", fetch_weather_fields=False)


def test_http_requires_requests():
    from nrcd.enrich.http import require_requests

    try:
        require_requests()
    except ImportError:
        pass
