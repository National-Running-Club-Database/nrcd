# Changelog

## [0.1.1] - 2026-06-06

- README quick start shows sample **outputs** and optional XC **target distance** (commented alternatives)
- `standardize_xc` optional target distance (**breaking** vs 0.1.0 auto Riegel): `target_distance_m`, or `target_distance` + `target_distance_unit`, or labels like `"8k"`
- `xc_target_distance_m(gender)` config helper (8000m / 6000m defaults)
- Document `nrcd.enrich` geographic limits — global weather with coordinates; US-oriented city/state altitude
- International geocoding: `country`, `geocode_query`, `NRCD_GEOCODE_COUNTRY_SUFFIX`, `build_geocode_query`

## [0.1.0] - 2026-06-06

Initial release.

- Sport-specific entry points — `standardize_xc`, `standardize_road`, `standardize_outdoor_track`, `standardize_indoor_track` (plus low-level `standardize_result`)
- Clock-string times and flexible distance/units (m, km, mi; °F/°C; ft/m)
- `nrcd.enrich` — optional weather and meet-altitude API backfill
- `nrcd.data` — Zenodo CSV helpers (`pip install "nrcd[data]"`)
- Examples, docs, and tests

[0.1.1]: https://github.com/National-Running-Club-Database/nrcd/releases/tag/v0.1.1
[0.1.0]: https://github.com/National-Running-Club-Database/nrcd/releases/tag/v0.1.0
