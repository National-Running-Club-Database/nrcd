#!/usr/bin/env python3
"""Use RaceContext to standardize from a dict or dataframe row."""

from __future__ import annotations

from nrcd.standardize import RaceContext, format_time, standardize_seconds


def main() -> None:
    print("RaceContext — one object for XC or track rows\n")

    xc_row = {
        "time_str": "22:15",
        "gender": "M",
        "sport_name": "Cross Country",
        "reported_distance": "5k",
        "temperature": 68,
        "dew_point": 58,
        "meet_elevation": 1200,
    }
    ctx_xc = RaceContext(
        time_str=xc_row["time_str"],
        gender=xc_row["gender"],
        sport_name=xc_row["sport_name"],
        reported_distance=xc_row["reported_distance"],
        temperature=xc_row["temperature"],
        dew_point=xc_row["dew_point"],
        meet_elevation=xc_row["meet_elevation"],
    )
    std_xc = standardize_seconds(ctx_xc)
    print(f"XC 5K  raw {xc_row['time_str']}  →  std {format_time(std_xc)}")

    track_row = {
        "time_str": "10.52",
        "gender": "M",
        "sport_name": "Outdoor Track",
        "event_name": "100m",
        "wind_mps": 1.8,
        "temperature": 75,
        "dew_point": 65,
    }
    ctx_track = RaceContext(
        time_str=track_row["time_str"],
        gender=track_row["gender"],
        sport_name=track_row["sport_name"],
        event_name=track_row["event_name"],
        wind_mps=track_row["wind_mps"],
        temperature=track_row["temperature"],
        dew_point=track_row["dew_point"],
    )
    std_track = standardize_seconds(ctx_track)
    print(f"100m   raw {track_row['time_str']}s  →  std {std_track:.3f}s")

    indoor_row = {
        "time_sec": 21.80,
        "gender": "F",
        "sport_name": "Indoor Track",
        "event_name": "200m",
        "lap_length_m": 200,
        "banked": True,
    }
    ctx_indoor = RaceContext(**indoor_row)
    std_indoor = standardize_seconds(ctx_indoor)
    print(f"200m indoor  raw {indoor_row['time_sec']:.2f}s  →  std {std_indoor:.3f}s")


if __name__ == "__main__":
    main()
