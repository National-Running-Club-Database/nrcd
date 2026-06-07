#!/usr/bin/env python3
"""Compare standardized times across two races (no NRCD dataset required)."""

from __future__ import annotations

from nrcd.standardize import format_time, parse_time, standardize_xc, xc_target_distance_m


def xc_std(time, *, gender, actual_distance_m, temperature, dew_point,
           elevation_gain=0, elevation_loss=0, meet_elevation=None):
    return standardize_xc(
        time,
        gender=gender,
        reported_distance_m=actual_distance_m,
        actual_distance_m=actual_distance_m,
        target_distance_m=xc_target_distance_m(gender),
        temperature=temperature,
        dew_point=dew_point,
        elevation_gain=elevation_gain,
        elevation_loss=elevation_loss,
        meet_elevation=meet_elevation,
    )


def main() -> None:
    races = [
        ("Meet 1 (cool, flat)", "27:00", 8100, 55, 50, 0, 0, 800),
        ("Meet 2 (hot, hilly, altitude)", "26:25", 7900, 82, 72, 3, 1, 4500),
    ]
    print("Cross-country improvement — your own results\n")
    print(f"{'Meet':<36} {'Raw':>10} {'Standardized':>14}")
    std_times = []
    for label, raw, dist, temp, dew, gain, loss, elev in races:
        std = xc_std(raw, gender="M", actual_distance_m=dist, temperature=temp, dew_point=dew,
                     elevation_gain=gain, elevation_loss=loss, meet_elevation=elev)
        std_times.append(std)
        print(f"{label:<36} {raw:>10} {format_time(std):>14}")
    if std_times[1] > std_times[0] and parse_time(races[1][1]) < parse_time(races[0][1]):
        print("\nRaw improved but standardized regressed — Meet 2 conditions were tougher.")


if __name__ == "__main__":
    main()
