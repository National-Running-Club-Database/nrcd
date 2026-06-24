"""HTTP helpers (requires ``requests``)."""

from __future__ import annotations

import time
import warnings


def require_requests():
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL")
            import requests
    except ImportError as e:
        raise ImportError(
            "nrcd.enrich requires the requests package. Install with: pip install nrcd[apis]"
        ) from e
    return requests


def get_with_retries(url: str, *, timeout: float = 20.0, retries: int = 3):
    requests = require_requests()
    last_err = None
    for attempt in range(retries):
        try:
            return requests.get(url, timeout=timeout)
        except requests.RequestException as e:
            last_err = e
            if attempt + 1 < retries:
                time.sleep(min(2**attempt, 8))
    raise last_err
