"""Geocoding query building and international location options."""

from nrcd.enrich.config import api_keys_from_env
from nrcd.enrich.geocode import build_geocode_query, geocode_location


def test_build_geocode_query_us_city_state():
    assert build_geocode_query(city="Boulder", state="CO", default_country="US") == "Boulder,CO,US"


def test_build_geocode_query_city_country():
    assert build_geocode_query(city="London", country="GB") == "London,GB"


def test_build_geocode_query_freeform():
    assert build_geocode_query(geocode_query="Paris,FR") == "Paris,FR"


def test_build_geocode_query_city_only_uses_default_country():
    assert build_geocode_query(city="Toronto", default_country="CA") == "Toronto,CA"


def test_api_keys_from_env_country_suffix(monkeypatch):
    monkeypatch.setenv("NRCD_GEOCODE_COUNTRY_SUFFIX", "gb")
    cfg = api_keys_from_env()
    assert cfg.geocode_country_suffix == "GB"


def test_geocode_location_city_country_mock(monkeypatch):
    captured = {}

    def fake_http(query, **kwargs):
        captured["query"] = query
        return 51.5074, -0.1278

    monkeypatch.setattr("nrcd.enrich.geocode._geocode_http", fake_http)
    coords = geocode_location("London", "", country="GB", api_key="k")
    assert coords == (51.5074, -0.1278)
    assert captured["query"] == "London,GB"


def test_geocode_location_geocode_query_mock(monkeypatch):
    captured = {}

    def fake_http(query, **kwargs):
        captured["query"] = query
        return 48.8566, 2.3522

    monkeypatch.setattr("nrcd.enrich.geocode._geocode_http", fake_http)
    coords = geocode_location("", "", geocode_query="Paris,FR", api_key="k")
    assert coords == (48.8566, 2.3522)
    assert captured["query"] == "Paris,FR"


def test_fetch_weather_city_country_mock(monkeypatch):
    import datetime as dt

    from nrcd.enrich.cache import clear_enrich_cache
    from nrcd.enrich.weather import fetch_weather

    captured = {}

    def fake_geocode(city, state, **kwargs):
        captured["city"] = city
        captured["country"] = kwargs.get("country")
        return 51.5074, -0.1278

    monkeypatch.setattr("nrcd.enrich.weather.geocode_location", fake_geocode)
    monkeypatch.setattr(
        "nrcd.enrich.weather._historical_weather",
        lambda *a, **k: (60.0, 62.0, 50.0, 70.0, "Clear", "clear", 1013.0, 1_700_000_000),
    )
    monkeypatch.setattr("nrcd.enrich.weather._historical_aqi", lambda *a, **k: (None,) * 9)
    clear_enrich_cache()
    wx = fetch_weather(
        "London",
        "",
        event_date=dt.date(2024, 10, 12),
        event_time=dt.time(11, 0),
        country="GB",
        openweather_api_key="k",
        timezone_api_key="tz",
        timezone_name="Europe/London",
        use_cache=False,
    )
    assert wx is not None
    assert wx.temperature == 60.0
    assert captured["city"] == "London"
    assert captured["country"] == "GB"
