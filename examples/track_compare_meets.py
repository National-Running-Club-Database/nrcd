#!/usr/bin/env python3
"""Compare the same track performance across meets (wind, heat, altitude)."""

from __future__ import annotations

from nrcd.standardize import format_time, parse_time, standardize_result


def std_100m(raw: float, *, wind_mps: float | None = None, temperature: float | None = None,
             dew_point: float | None = None, meet_elevation: float | None = None) -> float:
    return standardize_result(
        raw,
        gender="M",
        event_name="100m",
        sport_name="Outdoor Track",
        wind_mps=wind_mps,
        temperature=temperature,
        dew_point=dew_point,
        meet_elevation=meet_elevation,
    )


def std_5k(raw, *, temperature: float | None = None, dew_point: float | None = None,
           meet_elevation: float | None = None) -> float:
    t = parse_time(raw) if isinstance(raw, str) else float(raw)
    return standardize_result(
        t,
        gender="M",
        event_name="5000m",
        sport_name="Outdoor Track",
        temperature=temperature,
        dew_point=dew_point,
        meet_elevation=meet_elevation,
    )


def main() -> None:
    print("Track meet comparison — same raw time, different conditions\n")

    raw_sprint = 10.52
    print("100m — raw {:.2f}s across three meets\n".format(raw_sprint))
    meets_100 = [
        ("Home (calm, cool)", None, 58, 50, 600),
        ("Away (+2.1 tailwind)", 2.1, 70, 62, 400),
        ("Altitude invite", None, 65, 55, 5200),
    ]
    std_sprints = []
    for label, wind, temp, dew, elev in meets_100:
        std = std_100m(raw_sprint, wind_mps=wind, temperature=temp, dew_point=dew, meet_elevation=elev)
        std_sprints.append(std)
        print(f"  {label:<28} standardized {std:.3f}s")

    best = min(std_sprints)
    worst = max(std_sprints)
    print(f"\n  Spread: {worst - best:.3f}s — conditions matter even at the same raw time.")

    print("\n5000m — season progression (raw improves, conditions vary)\n")
    races_5k = [
        ("Early season (cool)", "16:20.00", 48, 42, 800),
        ("Conference (hot)", "16:05.00", 85, 70, 900),
        ("Championship (altitude)", "15:58.00", 62, 48, 4500),
    ]
    std_5ks = []
    for label, clock, temp, dew, elev in races_5k:
        std = std_5k(clock, temperature=temp, dew_point=dew, meet_elevation=elev)
        std_5ks.append(std)
        print(f"  {label:<30} raw {clock:>10}  std {format_time(std):>10}")

    if std_5ks[-1] < std_5ks[0]:
        print("\n  Standardized time improved — raw PR plus fairer conditions at the end.")
    elif races_5k[-1][1] < races_5k[0][1] and std_5ks[-1] > std_5ks[0]:
        print("\n  Raw improved but standardized regressed — late-season meet was tougher.")


if __name__ == "__main__":
    main()
