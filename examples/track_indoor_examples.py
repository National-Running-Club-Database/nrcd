#!/usr/bin/env python3
"""Indoor track venue examples — lap length and banking (no dataset required)."""

from __future__ import annotations

from nrcd.standardize import standardize_result


def show(label: str, raw: float, std: float) -> None:
    delta = std - raw
    sign = "+" if delta >= 0 else ""
    print(f"{label:<44} raw {raw:6.3f}s  →  std {std:6.3f}s  ({sign}{delta:.3f}s)")


def main() -> None:
    print("Indoor track — venue factors (sport_name must be Indoor Track)\n")

    raw = 21.80

    show(
        "200m — standard 200 m lap, flat",
        raw,
        standardize_result(
            raw,
            gender="M",
            event_name="200m",
            sport_name="Indoor Track",
            lap_length_m=200,
            banked=False,
        ),
    )
    show(
        "200m — standard 200 m lap, banked",
        raw,
        standardize_result(
            raw,
            gender="M",
            event_name="200m",
            sport_name="Indoor Track",
            lap_length_m=200,
            banked=True,
        ),
    )
    show(
        "200m — oversized 220 m lap, flat",
        raw,
        standardize_result(
            raw,
            gender="M",
            event_name="200m",
            sport_name="Indoor Track",
            lap_length_m=220,
            banked=False,
        ),
    )
    show(
        "200m — oversized 220 m lap, banked",
        raw,
        standardize_result(
            raw,
            gender="M",
            event_name="200m",
            sport_name="Indoor Track",
            lap_length_m=220,
            banked=True,
        ),
    )

    print("\nWind is ignored indoors (same time with wind_mps set)\n")

    calm = standardize_result(
        raw, gender="M", event_name="200m", sport_name="Indoor Track", lap_length_m=200,
    )
    with_wind = standardize_result(
        raw,
        gender="M",
        event_name="200m",
        sport_name="Indoor Track",
        lap_length_m=200,
        wind_mps=2.0,
    )
    show("200m indoor — no wind", raw, calm)
    show("200m indoor — wind ignored", raw, with_wind)


if __name__ == "__main__":
    main()
