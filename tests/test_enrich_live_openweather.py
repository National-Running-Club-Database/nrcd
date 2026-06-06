"""Live OpenWeather / USGS tests (optional — skipped without ``local_api_keys.env``).

Copy ``local_api_keys.env.example`` → ``local_api_keys.env`` and set
``NRCD_OPENWEATHER_API_KEY``. Run::

    pytest -m live_api -v

AQI history requires ``event_date`` on or after **2020-11-27**
(``nrcd.enrich.AQI_HISTORY_AVAILABLE_FROM``). Default live test date is 2024-10-12.
Historical timemachine weather may require a paid OpenWeather plan; geocode and meet
altitude (USGS) usually work on the free tier.
"""

from __future__ import annotations

import datetime as dt

import pytest

from nrcd.enrich.api_usage import AQI_HISTORY_AVAILABLE_FROM, ApiUsage
from nrcd.standardize import RaceContext

from tests.live_api_config import (
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
            "Set NRCD_OPENWEATHER_API_KEY in local_api_keys.env "
            "(copy from local_api_keys.env.example)"
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
    assert coords is not None
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
    assert ft is not None
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
    assert result.context.meet_elevation is not None
    assert result.context.meet_elevation > 0
    assert result.api_usage.openweather_geocode >= 1
    assert result.api_usage.usgs_epqs >= 1


def test_live_fetch_weather(ow_key: str):
    tz_key = timezone_api_key()
    if not tz_key:
        pytest.skip(
            "Set NRCD_TIMEZONE_API_KEY in local_api_keys.env for live weather tests"
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
    assert wx.temperature is not None
    assert wx.dew_point is not None
    assert usage.openweather_geocode >= 1
    assert usage.timezonedb >= 1
    assert usage.openweather_timemachine >= 1
    if event_date >= dt.date(2020, 11, 27):
        assert usage.openweather_aqi >= 1


def test_aqi_start_date_documented():
    assert AQI_HISTORY_AVAILABLE_FROM == dt.date(2020, 11, 27)
