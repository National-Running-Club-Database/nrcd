"""Live OpenWeather / USGS tests (optional — skipped without valid keys).

Copy ``local_api_keys.env.example`` → ``local_api_keys.env`` and set
``NRCD_OPENWEATHER_API_KEY``. Run::

    pytest -m live_api -v

Empty or placeholder keys in ``local_api_keys.env`` skip live HTTP tests (no failure).
AQI history requires ``event_date`` on or after **2020-11-27**
(``nrcd.enrich.AQI_HISTORY_AVAILABLE_FROM``). Default live test date is 2024-10-12.
"""

from __future__ import annotations

import datetime as dt

import pytest

from nrcd.enrich.api_usage import AQI_HISTORY_AVAILABLE_FROM, ApiUsage
from nrcd.standardize import RaceContext

from live_api_config import (
    live_test_city,
    live_test_date,
    live_test_state,
    live_test_time,
    openweather_api_key,
    timezone_api_key,
)

pytestmark = pytest.mark.live_api


def _require_openweather() -> str:
    key = openweather_api_key()
    if not key:
        pytest.skip(
            "No valid NRCD_OPENWEATHER_API_KEY — set it in local_api_keys.env "
            "(copy from local_api_keys.env.example) or export in the shell"
        )
    return key


@pytest.fixture
def ow_key() -> str:
    return _require_openweather()


def test_live_geocode_us_city_state(ow_key: str):
    from nrcd.enrich.geocode import geocode_us_city_state

    usage = ApiUsage()
    coords = geocode_us_city_state(
        live_test_city(),
        live_test_state(),
        api_key=ow_key,
        use_cache=False,
        usage=usage,
    )
    if coords is None:
        pytest.skip("OpenWeather geocode returned no result — check API key or plan")
    lat, lon = coords
    assert -90 <= lat <= 90
    assert -180 <= lon <= 180
    assert usage.openweather_geocode >= 1


def test_live_lookup_altitude_ft(ow_key: str):
    from nrcd.enrich.altitude import lookup_altitude_ft

    usage = ApiUsage()
    ft = lookup_altitude_ft(
        live_test_city(),
        live_test_state(),
        openweather_api_key=ow_key,
        use_cache=False,
        usage=usage,
    )
    if ft is None:
        pytest.skip("Altitude lookup failed — geocode or USGS unavailable")
    assert ft > 0
    assert usage.openweather_geocode >= 1
    assert usage.usgs_epqs >= 1


def test_live_enrich_race_context_altitude(ow_key: str):
    from nrcd.enrich import enrich_race_context_result

    ctx = RaceContext(
        time_str="22:15",
        gender="M",
        sport_name="Cross Country",
        reported_distance="5k",
        city=live_test_city(),
        state=live_test_state(),
    )
    result = enrich_race_context_result(
        ctx,
        openweather_api_key=ow_key,
        fetch_altitude=True,
        fetch_weather_fields=False,
    )
    if result.context.meet_elevation is None:
        pytest.skip("enrich_race_context did not resolve meet_elevation")
    assert result.context.meet_elevation > 0
    assert result.api_usage.openweather_geocode >= 1
    assert result.api_usage.usgs_epqs >= 1


def test_live_fetch_weather(ow_key: str):
    tz_key = timezone_api_key()
    if not tz_key:
        pytest.skip(
            "No valid NRCD_TIMEZONE_API_KEY — set it in local_api_keys.env for weather tests"
        )

    from nrcd.enrich.weather import fetch_weather

    event_date = live_test_date()
    assert event_date >= AQI_HISTORY_AVAILABLE_FROM, (
        f"event_date must be on or after AQI start {AQI_HISTORY_AVAILABLE_FROM}"
    )

    usage = ApiUsage()
    wx = fetch_weather(
        live_test_city(),
        live_test_state(),
        event_date,
        live_test_time(),
        openweather_api_key=ow_key,
        timezone_api_key=tz_key,
        use_cache=False,
        usage=usage,
    )
    if wx is None or wx.temperature is None or wx.dew_point is None:
        pytest.skip(
            "Weather fetch incomplete — check OpenWeather One Call 3.0 subscription "
            "and TimeZoneDB key"
        )
    assert usage.openweather_geocode >= 1
    assert usage.timezonedb >= 1
    assert usage.openweather_timemachine >= 1
    if event_date >= dt.date(2020, 11, 27):
        assert usage.openweather_aqi >= 1


def test_aqi_start_date_documented():
    assert AQI_HISTORY_AVAILABLE_FROM == dt.date(2020, 11, 27)


def test_live_enrich_dataframe_batch_usage(ow_key: str):
    pd = pytest.importorskip("pandas")
    tz_key = timezone_api_key()
    if not tz_key:
        pytest.skip(
            "No valid NRCD_TIMEZONE_API_KEY — set it in local_api_keys.env for weather tests"
        )

    from nrcd.enrich.cache import clear_enrich_cache
    from nrcd.enrich.config import EnrichConfig
    from nrcd.standardize import DataframeBatchResult, enrich_dataframe

    clear_enrich_cache()
    event_date = live_test_date()
    assert event_date >= AQI_HISTORY_AVAILABLE_FROM

    rows = [
        {
            "gender": "M",
            "result_time": "22:15",
            "sport_name": "Cross Country",
            "reported_distance": "5k",
            "city": live_test_city(),
            "state": live_test_state(),
            "event_date": event_date.isoformat(),
            "event_time": live_test_time().strftime("%H:%M"),
        }
        for _ in range(3)
    ]
    result = enrich_dataframe(
        pd.DataFrame(rows),
        fetch_altitude=False,
        config=EnrichConfig(
            openweather_api_key=ow_key,
            timezone_api_key=tz_key,
        ),
        return_usage=True,
    )
    assert isinstance(result, DataframeBatchResult)
    if result.dataframe.loc[0, "temperature"] is None:
        pytest.skip("Weather enrich incomplete — check OpenWeather / TimeZoneDB keys")

    usage = result.api_usage
    assert usage is not None
    assert usage.openweather_geocode == 1
    assert usage.openweather_timemachine == 1
    assert usage.openweather_total >= 2
    assert usage.to_dict()["openweather_total"] == usage.openweather_total
