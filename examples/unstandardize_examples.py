#!/usr/bin/env python3
"""Unstandardize examples — std fitness → expected clock time at a meet."""

from __future__ import annotations

from nrcd.standardize import format_time, standardize_xc, unstandardize_xc


def show(label: str, raw: float) -> None:
    print(f"{label:<44} →  {format_time(raw)}")


def main() -> None:
    print("Unstandardize — std time → expected clock time at a meet\n")
    print("Past result standardized; upcoming meet conditions passed to unstandardize_xc.\n")

    # Mild 8K: 400 ft gain + 400 ft loss over 8000 m, meet at 5200 ft
    race = dict(
        gender="M",
        reported_distance_m=8000,
        elevation_gain=400,
        elevation_loss=400,
        grade_input="feet",
        meet_elevation=5200,
        target_distance_m=8000,
        temperature=55,
        dew_point=48,
    )
    raw = "26:40"
    std = standardize_xc(raw, **race)

    show("Past meet — raw", 26 * 60 + 40)
    show("Std fitness level", std)

    upcoming_hot = dict(**race, temperature=85, dew_point=70)
    show("Upcoming meet — hot forecast", unstandardize_xc(std, **upcoming_hot))

    upcoming_flat = dict(**race, elevation_gain=50, elevation_loss=50)
    show("Upcoming meet — flatter course", unstandardize_xc(std, **upcoming_flat))

    upcoming_low = dict(**race, meet_elevation=500)
    show("Upcoming meet — low altitude (500 ft)", unstandardize_xc(std, **upcoming_low))

    show("Round-trip (same meet as std)", unstandardize_xc(std, **race))


if __name__ == "__main__":
    main()
