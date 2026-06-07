"""National Running Club Database — performance standardization library."""

from nrcd.standardize import (
    PARAMETERS_DOC,
    RaceContext,
    XCRaceContext,
    standardize_indoor_track,
    standardize_outdoor_track,
    standardize_result,
    standardize_road,
    standardize_seconds,
    standardize_xc,
)

__version__ = "0.1.1"

__all__ = [
    "PARAMETERS_DOC",
    "RaceContext",
    "XCRaceContext",
    "standardize_indoor_track",
    "standardize_outdoor_track",
    "standardize_result",
    "standardize_road",
    "standardize_seconds",
    "standardize_xc",
    "__version__",
]
