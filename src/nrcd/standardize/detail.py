"""Step-by-step standardization breakdown."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StandardizeStep:
    """One correction applied during standardization."""

    name: str
    time_before_sec: float
    time_after_sec: float
    factor: float | None = None
    """Multiplicative factor (``time_after / time_before``) when meaningful."""

    delta_sec: float | None = None
    """Additive change in seconds (e.g. wind calm-equivalent adjustment)."""

    note: str | None = None

    @property
    def applied(self) -> bool:
        if self.delta_sec is not None and self.delta_sec != 0:
            return True
        if self.factor is not None and self.factor != 1.0:
            return True
        return self.time_before_sec != self.time_after_sec


@dataclass(frozen=True)
class StandardizeDetail:
    """Raw time, standardized time, and ordered pipeline steps."""

    raw_sec: float
    std_sec: float
    steps: tuple[StandardizeStep, ...]

    def factor(self, name: str) -> float | None:
        """Return the factor for the first step with ``name``, if any."""
        for step in self.steps:
            if step.name == name:
                return step.factor
        return None


def _step_multiplicative(
    name: str,
    time_before: float,
    time_after: float,
    *,
    note: str | None = None,
) -> StandardizeStep:
    factor = time_after / time_before if time_before > 0 else None
    return StandardizeStep(
        name=name,
        time_before_sec=time_before,
        time_after_sec=time_after,
        factor=factor,
        delta_sec=time_after - time_before,
        note=note,
    )


def _step_additive(
    name: str,
    time_before: float,
    time_after: float,
    *,
    note: str | None = None,
) -> StandardizeStep:
    factor = time_after / time_before if time_before > 0 else None
    return StandardizeStep(
        name=name,
        time_before_sec=time_before,
        time_after_sec=time_after,
        factor=factor,
        delta_sec=time_after - time_before,
        note=note,
    )
