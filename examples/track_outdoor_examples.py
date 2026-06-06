#!/usr/bin/env python3
"""Outdoor track and road standardization examples (no NRCD dataset required)."""

from __future__ import annotations

from nrcd.standardize import format_time, parse_time, standardize_result


def show_sprint(label: str, raw: float, std: float) -> None:
    print(f"{label:<40} raw {raw:6.3f}s  →  std {std:6.3f}s")


def show_distance(label: str, raw, std: float) -> None:
    raw_display = raw if isinstance(raw, str) else format_time(raw)
    print(f"{label:<40} raw {raw_display:>10}  →  std {format_time(std):>10}")


def main() -> None:
    print("Outdoor track — standardize_result examples\n")
    print("Sprints (wind correction — sport_name must be Outdoor Track)\n")

    raw_100 = 10.50
    show_sprint(
        "100m — calm",
        raw_100,
        standardize_result(
            raw_100, gender="M", event_name="100m", sport_name="Outdoor Track",
        ),
    )
    show_sprint(
        "100m — +2.0 m/s tailwind",
        raw_100,
        standardize_result(
            raw_100, gender="M", event_name="100m", sport_name="Outdoor Track", wind_mps=2.0,
        ),
    )
    show_sprint(
        "100m — -1.5 m/s headwind",
        raw_100,
        standardize_result(
            raw_100, gender="M", event_name="100m", sport_name="Outdoor Track", wind_mps=-1.5,
        ),
    )

    print("\nHurdles & mid-distance\n")

    show_sprint(
        "110m Hurdles",
        14.20,
        standardize_result(
            14.20, gender="M", event_name="110m Hurdles", sport_name="Outdoor Track",
        ),
    )
    show_distance(
        "400m",
        "48.50",
        standardize_result(
            parse_time("48.50"), gender="M", event_name="400m", sport_name="Outdoor Track",
        ),
    )
    show_distance(
        "800m",
        "1:55.00",
        standardize_result(
            parse_time("1:55.00"), gender="M", event_name="800m", sport_name="Outdoor Track",
        ),
    )

    print("\nDistance — weather and meet altitude\n")

    show_distance(
        "1600m / Mile — cool, sea level",
        "4:12.00",
        standardize_result(
            parse_time("4:12.00"),
            gender="M",
            event_name="Mile",
            sport_name="Outdoor Track",
            temperature=55,
            dew_point=48,
            meet_elevation=500,
        ),
    )
    show_distance(
        "1600m — hot day",
        "4:12.00",
        standardize_result(
            parse_time("4:12.00"),
            gender="M",
            event_name="1600m",
            sport_name="Outdoor Track",
            temperature=88,
            dew_point=72,
        ),
    )
    show_distance(
        "5000m — altitude (ft)",
        "15:30.00",
        standardize_result(
            parse_time("15:30.00"),
            gender="M",
            event_name="5000m",
            sport_name="Outdoor Track",
            meet_elevation=5200,
        ),
    )
    show_distance(
        "5000m — altitude (m) + °C weather",
        "15:30.00",
        standardize_result(
            parse_time("15:30.00"),
            gender="F",
            event_name="5000m",
            sport_name="Outdoor Track",
            meet_elevation=1585,
            venue_elevation_unit="m",
            temperature=28,
            dew_point=16,
            temp_unit="C",
        ),
    )
    show_distance(
        "10000m",
        "32:45.00",
        standardize_result(
            parse_time("32:45.00"),
            gender="M",
            event_name="10000m",
            sport_name="Outdoor Track",
            meet_elevation=1200,
        ),
    )

    print("\nRoad-style course grade on a track meet\n")

    show_distance(
        "5000m — rolling course grade (%)",
        "16:05.00",
        standardize_result(
            parse_time("16:05.00"),
            gender="M",
            event_name="5000m",
            sport_name="Outdoor Track",
            elevation_gain=1.5,
            elevation_loss=1.5,
        ),
    )


if __name__ == "__main__":
    main()
