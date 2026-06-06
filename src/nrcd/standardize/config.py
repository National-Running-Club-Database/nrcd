"""Default coefficients (CIKM resource paper / analysis repo)."""

from __future__ import annotations

from dataclasses import dataclass

from nrcd.standardize.units import GradeInput, TemperatureUnit, VenueElevationUnit


@dataclass(frozen=True)
class StandardizeConfig:
    """Tunable coefficients (optional on every entry-point).

    Attributes
    ----------
    heat_k : float
        Quadratic heat slowdown coefficient; slowdown % = heat_k × (H − 100)²
        with H = temp + dew in °F.
    heat_index_threshold_f : float
        No weather penalty at or below this H (default 100°F).
    riegel_b_men, riegel_b_women : float
        Riegel exponents for distance conversion (XC and course-length adjust).
    xc_target_men_m, xc_target_women_m : float
        NIRCA reference XC distances (8000 / 6000 m).
    elevation_gain_base, elevation_loss_base : float
        Maurer grade factors (1.04^g × 0.9633^l); g, l in percent grade.
    wind_max_mps : float
        Absolute wind clamp when applying outdoor sprint corrections.
    track_outdoor_reference_lap_m : float
        Standard outdoor lap (400 m); no length factor when lap matches.
    default_temp_unit, default_venue_elevation_unit, default_grade_input
        Documented input defaults; pass explicitly on functions if not using
        :class:`~nrcd.standardize.context.RaceContext`.
    """

    heat_k: float = 0.0016
    heat_index_threshold_f: float = 100.0
    riegel_b_men: float = 1.055
    riegel_b_women: float = 1.08
    xc_target_men_m: float = 8000.0
    xc_target_women_m: float = 6000.0
    elevation_gain_base: float = 1.04
    elevation_loss_base: float = 0.9633
    wind_max_mps: float = 4.0
    track_outdoor_reference_lap_m: float = 400.0
    default_temp_unit: TemperatureUnit = "F"
    default_venue_elevation_unit: VenueElevationUnit = "ft"
    default_grade_input: GradeInput = "percent"

    def riegel_b(self, gender: str) -> float:
        return self.riegel_b_women if str(gender).upper() == "F" else self.riegel_b_men

    def xc_target_m(self, gender: str) -> float:
        return (
            self.xc_target_women_m
            if str(gender).upper() == "F"
            else self.xc_target_men_m
        )
