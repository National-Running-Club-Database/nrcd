"""Course grade gain/loss (XC and road) — distinct from meet altitude."""

from __future__ import annotations

import math
import warnings

from nrcd.standardize.config import StandardizeConfig
from nrcd.standardize.factors import elevation_factor
from nrcd.standardize.units import GradeInput, resolve_grade_percent


def warn_one_sided_course_grade(
    elevation_gain: float | None,
    elevation_loss: float | None,
    *,
    stacklevel: int = 2,
) -> None:
    """Warn when only gain or only loss is set (implies all-uphill or all-downhill)."""

    def _active(x: float | None) -> bool:
        if x is None:
            return False
        try:
            v = float(x)
        except (TypeError, ValueError):
            return False
        return math.isfinite(v) and v != 0

    has_gain = _active(elevation_gain)
    has_loss = _active(elevation_loss)

    if has_gain and not has_loss:
        warnings.warn(
            "Only elevation_gain is set: the grade adjustment assumes the entire course "
            "is uphill (no downhill). Add elevation_loss for out-and-back or rolling courses.",
            UserWarning,
            stacklevel=stacklevel,
        )
    elif has_loss and not has_gain:
        warnings.warn(
            "Only elevation_loss is set: the grade adjustment assumes the entire course "
            "is downhill (no uphill). Add elevation_gain for balanced or rolling courses.",
            UserWarning,
            stacklevel=stacklevel,
        )


def course_grade_factor(
    elevation_gain: float | None,
    elevation_loss: float | None,
    *,
    course_distance_m: float,
    grade_input: GradeInput = "percent",
    config: StandardizeConfig | None = None,
) -> float:
    """Maurer grade multiplier for a course (1.0 when gain/loss omitted)."""
    if elevation_gain is None and elevation_loss is None:
        return 1.0
    cfg = config or StandardizeConfig()
    gain_pct, loss_pct = resolve_grade_percent(
        elevation_gain,
        elevation_loss,
        grade_input=grade_input,
        course_distance_m=course_distance_m,
    )
    if gain_pct is None and loss_pct is None:
        return 1.0
    return elevation_factor(
        gain_pct,
        loss_pct,
        gain_base=cfg.elevation_gain_base,
        loss_base=cfg.elevation_loss_base,
    )


def apply_course_grade_factor(
    time_sec: float,
    elevation_gain: float | None,
    elevation_loss: float | None,
    *,
    course_distance_m: float,
    grade_input: GradeInput = "percent",
    config: StandardizeConfig | None = None,
    warn_one_sided: bool = True,
) -> float:
    """Maurer grade factor for XC and road (percent grade by default)."""
    if not math.isfinite(time_sec):
        return time_sec
    if elevation_gain is None and elevation_loss is None:
        return time_sec
    if warn_one_sided:
        warn_one_sided_course_grade(elevation_gain, elevation_loss, stacklevel=3)
    f = course_grade_factor(
        elevation_gain,
        elevation_loss,
        course_distance_m=course_distance_m,
        grade_input=grade_input,
        config=config,
    )
    return time_sec * f
