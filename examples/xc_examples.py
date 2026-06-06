#!/usr/bin/env python3
"""Cross-country standardization examples (no NRCD dataset required)."""

from __future__ import annotations

from nrcd.standardize import format_time, standardize_xc


def show(label: str, raw, std: float) -> None:
    raw_display = raw if isinstance(raw, str) else format_time(raw)
    print(f"{label:<42} raw {raw_display:>10}  →  std {format_time(std):>10}")


def main() -> None:
    print("Cross country — standardize_xc examples\n")

    # 5K clock string
    show(
        "5K (men)",
        "22:15",
        standardize_xc("22:15", gender="M", reported_distance="5k"),
    )

    # Women's 6K
    show(
        "6K (women)",
        "24:30",
        standardize_xc("24:30", gender="F", reported_distance="6k"),
    )

    # 8-mile XC with weather, grade, and meet altitude (°F / feet defaults)
    show(
        "8 mi — hot, hilly, altitude",
        "1:10:13",
        standardize_xc(
            "1:10:13",
            gender="M",
            reported_distance=8,
            distance_unit="mi",
            actual_distance=8.03,
            temperature=72,
            dew_point=65,
            elevation_gain=2.5,
            elevation_loss=2.5,
            meet_elevation=5200,
        ),
    )

    # Same race — Celsius weather, meet elevation in meters
    show(
        "8 mi — metric units",
        "1:10:13",
        standardize_xc(
            "1:10:13",
            gender="M",
            reported_distance=8,
            distance_unit="mi",
            temperature=22,
            dew_point=18,
            temp_unit="C",
            meet_elevation=1585,
            venue_elevation_unit="m",
        ),
    )

    # Course grade as vertical meters (not % and not meet altitude)
    show(
        "8K — grade in vertical meters",
        "26:40",
        standardize_xc(
            "26:40",
            gender="M",
            reported_distance="8k",
            elevation_gain=120,
            elevation_loss=120,
            grade_input="m",
        ),
    )

    # Course grade as vertical feet
    show(
        "8K — grade in vertical feet",
        "26:40",
        standardize_xc(
            "26:40",
            gender="M",
            reported_distance_m=8000,
            elevation_gain=400,
            elevation_loss=400,
            grade_input="feet",
        ),
    )

    # Long course — actual distance longer than reported (Riegel adjust)
    show(
        "8K — course ran long",
        "27:00",
        standardize_xc(
            "27:00",
            gender="M",
            reported_distance_m=8000,
            actual_distance_m=8120,
            apply_weather=False,
            apply_elevation_grade=False,
            apply_meet_altitude_correction=False,
        ),
    )

    # Classic meters-only call
    show(
        "8K — seconds + meters",
        1560.0,
        standardize_xc(
            1560.0,
            gender="M",
            reported_distance_m=8000,
            actual_distance_m=8050,
        ),
    )


if __name__ == "__main__":
    main()
