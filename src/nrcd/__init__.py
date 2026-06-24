"""National Running Club Database — performance standardization library."""

from nrcd.standardize import (
    PARAMETERS_DOC,
    TRACK_VENUE_REFERENCES,
    RaceContext,
    XCRaceContext,
    compare_venue_references,
    standardize_indoor_track,
    standardize_outdoor_track,
    standardize_result,
    standardize_road,
    standardize_seconds,
    standardize_xc,
    unstandardize_result,
    unstandardize_xc,
    venue_reference_factor_table,
)

__version__ = "0.1.5"

__all__ = [
    "PARAMETERS_DOC",
    "RaceContext",
    "TRACK_VENUE_REFERENCES",
    "XCRaceContext",
    "compare_venue_references",
    "standardize_indoor_track",
    "standardize_outdoor_track",
    "standardize_result",
    "standardize_road",
    "standardize_seconds",
    "standardize_xc",
    "unstandardize_result",
    "unstandardize_xc",
    "venue_reference_factor_table",
    "__version__",
]
