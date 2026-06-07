#!/usr/bin/env python3
"""Minimal one-liner XC + track calls — see other examples for more scenarios."""

from nrcd.standardize import format_time, standardize_outdoor_track, standardize_xc


def main() -> None:
    xc_std = standardize_xc(
        "22:15",
        gender="M",
        reported_distance="5k",
        temperature=72,
        dew_point=65,
        meet_elevation=1200,
        target_distance_m=8000,  # 8000m
    )
    print(f"XC 5K standardized for 8000m: {format_time(xc_std)}")

    track_std = standardize_outdoor_track(
        "10.50",
        gender="M",
        event_name="100m",
        wind_mps=2.0,
    )
    print(f"100m standardized: {track_std:.3f} s")


if __name__ == "__main__":
    main()
