#!/usr/bin/env python3
"""Indoor track venue examples — lap length, banking, and reference comparison."""

from __future__ import annotations

from nrcd.standardize import (
    compare_venue_references,
    standardize_result,
    venue_reference_factor_table,
)


def show(label: str, raw: float, std: float) -> None:
    delta = std - raw
    sign = "+" if delta >= 0 else ""
    print(f"{label:<44} raw {raw:6.3f}s  →  std {std:6.3f}s  ({sign}{delta:.3f}s)")


def main() -> None:
    print("Indoor track — venue factors (sport_name must be Indoor Track)\n")

    raw = 21.80

    show(
        "200m — 200 m flat (→ banked/oversized NCAA ref)",
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
        "200m — 200 m banked (NCAA reference)",
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
        "200m flat — explicit indoor_flat reference",
        raw,
        standardize_result(
            raw,
            gender="M",
            event_name="200m",
            sport_name="Indoor Track",
            lap_length_m=200,
            banked=False,
            venue_reference="indoor_flat",
        ),
    )

    print("\nCompare all venue references (22.97 s on 200 m flat):\n")
    refs = compare_venue_references(
        22.97,
        gender="M",
        event_name="200m",
        sport_name="Indoor Track",
        lap_length_m=200,
        banked=False,
    )
    for name, std in refs.items():
        show(f"  → {name}", 22.97, std)

    print("\nVenue-only NCAA factors (no weather):\n")
    factors = venue_reference_factor_table(
        "200m",
        "M",
        lap_length_m=200,
        banked=False,
        sport_name="Indoor Track",
    )
    for name, factor in factors.items():
        print(f"  {name:<22} × {factor:.4f}")

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
