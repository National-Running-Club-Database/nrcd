import time

from nrcd.enrich.cache import clear_enrich_cache, cache_stats
from nrcd.enrich.throttle import reset_throttle_state


def setup_function():
    clear_enrich_cache()
    reset_throttle_state()


def test_cache_dedupes_geocode(monkeypatch):
    calls = {"n": 0}

    def fake_http(*a, **k):
        calls["n"] += 1
        return (1.0, 2.0)

    monkeypatch.setattr("nrcd.enrich.geocode._geocode_http", fake_http)
    from nrcd.enrich.geocode import geocode_us_city_state

    geocode_us_city_state("A", "CO", api_key="k")
    geocode_us_city_state("A", "CO", api_key="k")
    assert calls["n"] == 1


def test_altitude_cache(monkeypatch):
    from nrcd.enrich.altitude import AltitudeResult

    monkeypatch.setattr("nrcd.enrich.geocode._geocode_http", lambda *a, **k: (1.0, 2.0))
    monkeypatch.setattr(
        "nrcd.enrich.altitude._altitude_from_coords",
        lambda *a, **k: AltitudeResult(altitude_ft=5000, lat=1.0, lon=2.0, city="Boulder", state="CO"),
    )
    from nrcd.enrich.altitude import lookup_altitude_ft

    lookup_altitude_ft("Boulder", "CO", openweather_api_key="k")
    lookup_altitude_ft("Boulder", "CO", openweather_api_key="k")
    assert cache_stats()["entries"] >= 1


def test_throttle_waits(monkeypatch):
    from nrcd.enrich.throttle import wait_for_provider

    t0 = time.monotonic()
    wait_for_provider("test_provider", 0.05)
    wait_for_provider("test_provider", 0.05)
    assert time.monotonic() - t0 >= 0.04


def test_fetch_weather_requires_key():
    from nrcd.enrich.weather import fetch_weather
    import datetime as dt

    try:
        fetch_weather(
            "Boulder", "CO",
            event_date=dt.date(2024, 1, 1),
            event_time=dt.time(12, 0),
            openweather_api_key=None,
            timezone_api_key=None,
        )
        assert False, "expected error"
    except ValueError:
        pass
