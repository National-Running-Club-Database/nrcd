"""Multiplicative adjustment factors (weather, grade, Riegel)."""

from __future__ import annotations

import math

from nrcd.standardize.config import StandardizeConfig

_DEFAULT = StandardizeConfig()


def _finite_or_none(x: float | None) -> float | None:
    if x is None:
        return None
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def heat_index(temp_f: float | None, dew_f: float | None) -> float | None:
    """Heat index H = T + D (both in °F), used by NRCD weather model."""
    t = _finite_or_none(temp_f)
    d = _finite_or_none(dew_f)
    if t is None or d is None:
        return None
    return t + d


def heat_slowdown_percent(
    heat_index_f: float,
    *,
    threshold_f: float = _DEFAULT.heat_index_threshold_f,
    k: float = _DEFAULT.heat_k,
) -> float:
    """Percent slowdown above threshold: k × (H − 100)²."""
    if heat_index_f <= threshold_f:
        return 0.0
    return k * (heat_index_f - threshold_f) ** 2


def weather_factor(
    temp_f: float | None,
    dew_f: float | None,
    *,
    k: float | None = None,
    threshold_f: float = _DEFAULT.heat_index_threshold_f,
) -> float:
    """Multiplicative factor; < 1 when H = T + D (°F) exceeds 100."""
    h = heat_index(temp_f, dew_f)
    if h is None or h <= threshold_f:
        return 1.0
    coeff = _DEFAULT.heat_k if k is None else k
    pct = heat_slowdown_percent(h, threshold_f=threshold_f, k=coeff)
    return 1.0 - pct / 100.0


def elevation_factor(
    gain_pct: float | None,
    loss_pct: float | None,
    *,
    gain_base: float = _DEFAULT.elevation_gain_base,
    loss_base: float = _DEFAULT.elevation_loss_base,
) -> float:
    """Maurer (2018): f = gain_base^g × loss_base^l with g, l in **percent grade**."""
    g = 0.0 if gain_pct is None else float(gain_pct)
    l = 0.0 if loss_pct is None else float(loss_pct)
    if not math.isfinite(g):
        g = 0.0
    if not math.isfinite(l):
        l = 0.0
    return (gain_base**g) * (loss_base**l)


def riegel_convert(
    seconds: float,
    d_actual: float,
    d_target: float,
    b: float,
) -> float:
    if not math.isfinite(seconds) or d_actual <= 0 or d_target <= 0:
        return float("nan")
    return seconds * (d_target / d_actual) ** b


def riegel_exponent(gender: str, config: StandardizeConfig | None = None) -> float:
    cfg = config or _DEFAULT
    return cfg.riegel_b(gender)


def xc_target_distance_m(gender: str, config: StandardizeConfig | None = None) -> float:
    cfg = config or _DEFAULT
    return cfg.xc_target_m(gender)
