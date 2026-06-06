#!/usr/bin/env python3
"""Optional: load Zenodo CSVs from data/ and standardize one XC row."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

from nrcd.data import meet_altitude_column, meet_altitude_ft_from_record
from nrcd.standardize import parse_time, standardize_xc

XC_DISTANCE_M = {"M": 8000.0, "F": 6000.0}


def main() -> None:
    needed = ["result.csv", "meet.csv", "sport.csv", "athlete.csv", "running_event.csv", "course_details.csv"]
    missing = [f for f in needed if not (DATA / f).exists()]
    if missing:
        print("WARNING: NRCD Zenodo CSVs not found — this example cannot run.", file=sys.stderr)
        print("  The nrcd package does NOT require this dataset.", file=sys.stderr)
        print("  Download: https://zenodo.org/records/17917357", file=sys.stderr)
        print("  Requires: pip install \"nrcd[data]\"", file=sys.stderr)
        print("  Or run: python examples/compare_improvement.py", file=sys.stderr)
        sys.exit(1)

    result = pd.read_csv(DATA / "result.csv", low_memory=False)
    meet = pd.read_csv(DATA / "meet.csv")
    sport = pd.read_csv(DATA / "sport.csv")
    athlete = pd.read_csv(DATA / "athlete.csv")
    running_event = pd.read_csv(DATA / "running_event.csv")
    course_details = pd.read_csv(DATA / "course_details.csv")

    alt_col = meet_altitude_column(meet)
    df = result.merge(meet[["meet_id", "sport_id", alt_col]].rename(columns={alt_col: "altitude"}), on="meet_id")
    df = df.merge(sport, on="sport_id").merge(athlete[["athlete_id", "gender"]], on="athlete_id")
    df = df.merge(running_event, on="running_event_id")

    xc = df[df["sport_name"] == "Cross Country"].head(1)
    if xc.empty:
        print("No XC rows found.")
        return

    row = xc.iloc[0]
    cd = course_details[
        (course_details["meet_id"] == row["meet_id"])
        & (course_details["running_event_id"] == row["running_event_id"])
        & (course_details["gender"] == row["gender"])
    ]
    cd = cd.iloc[0].to_dict() if len(cd) else {}
    raw = parse_time(row["result_time"])
    d_reported = XC_DISTANCE_M.get(row["gender"], 8000.0)
    d_actual = cd.get("estimated_course_distance") or d_reported
    std = standardize_xc(
        raw, gender=row["gender"], reported_distance_m=d_reported, actual_distance_m=d_actual,
        temperature=cd.get("temperature"), dew_point=cd.get("dew_point"),
        elevation_gain=cd.get("elevation_gain"), elevation_loss=cd.get("elevation_loss"),
        meet_elevation=meet_altitude_ft_from_record(row, cd),
        barometric_pressure=cd.get("barometric_pressure") or cd.get("barometric_pressure_hpa"),
    )
    print(f"raw {raw:.1f}s  standardized {std:.1f}s")


if __name__ == "__main__":
    main()
