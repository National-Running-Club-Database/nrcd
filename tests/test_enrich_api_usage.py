from nrcd.enrich.api_usage import AQI_HISTORY_AVAILABLE_FROM, ApiUsage
from nrcd.enrich.geocode import geocode_us_city_state


def test_api_usage_to_dict():
    u = ApiUsage(openweather_geocode=1, usgs_epqs=2)
    d = u.to_dict()
    assert d["openweather_geocode"] == 1
    assert d["usgs_epqs"] == 2


def test_api_usage_add():
    a = ApiUsage(openweather_geocode=1)
    b = ApiUsage(openweather_timemachine=2)
    a.add(b)
    assert a.openweather_geocode == 1
    assert a.openweather_timemachine == 2


def test_aqi_history_cutoff():
    assert AQI_HISTORY_AVAILABLE_FROM.year == 2020


def test_geocode_mock(monkeypatch):
    monkeypatch.setattr(
        "nrcd.enrich.geocode._geocode_http",
        lambda *a, **k: (40.0, -105.0),
    )
    lat, lon = geocode_us_city_state("Boulder", "CO", api_key="k")
    assert lat == 40.0 and lon == -105.0
