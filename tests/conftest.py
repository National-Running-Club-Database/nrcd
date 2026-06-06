"""Pytest hooks — load gitignored ``local_api_keys.env`` before tests run."""

from live_api_config import apply_local_api_keys


def pytest_configure(config) -> None:
    apply_local_api_keys()
