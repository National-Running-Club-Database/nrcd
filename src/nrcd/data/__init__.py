"""NRCD CSV column names and derived field helpers.

Requires ``pip install "nrcd[data]"`` (pandas).
"""

from nrcd.data.schema import (
    derive_course_details_fields,
    meet_altitude_column,
    meet_altitude_ft_from_record,
)

__all__ = [
    "derive_course_details_fields",
    "meet_altitude_column",
    "meet_altitude_ft_from_record",
]
