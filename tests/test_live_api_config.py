"""Unit tests for live API key loading (no HTTP)."""

from live_api_config import _normalize_api_key, openweather_api_key, timezone_api_key


def test_normalize_api_key_rejects_empty_and_placeholders():
    assert _normalize_api_key("") is None
    assert _normalize_api_key("   ") is None
    assert _normalize_api_key("your_key_here") is None
    assert _normalize_api_key("abc123") == "abc123"


def test_empty_keys_in_local_file_skip_not_fail(monkeypatch, tmp_path):
    env_file = tmp_path / "local_api_keys.env"
    env_file.write_text(
        "NRCD_OPENWEATHER_API_KEY=\nNRCD_TIMEZONE_API_KEY=\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("NRCD_OPENWEATHER_API_KEY", "stale-from-shell")
    monkeypatch.setenv("NRCD_TIMEZONE_API_KEY", "stale-tz")
    monkeypatch.setattr("live_api_config._LOCAL_KEYS_FILE", env_file)

    assert openweather_api_key() is None
    assert timezone_api_key() is None
