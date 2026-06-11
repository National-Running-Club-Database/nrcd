# Changelog

## [0.1.2] - 2026-06-11

- Fix README Quick start imports (`format_time` from `nrcd.standardize`, not `nrcd`)
- Add regression tests for README example output times
- Remove stale `scripts/enrich_api.py` reference from enrich API guide
- Add tests for top-level package exports and `xc_target_distance_m` defaults
- Document `format_time` returning `""` for negative/NaN/inf input
- Add Python 3.13 to CI matrix and PyPI classifiers
- Add [CONTRIBUTING.md](CONTRIBUTING.md)
- Ship `examples/` in source distributions (sdist)
- `standardize_dataframe(df)` — batch standardize DataFrame rows via `RaceContext` (`pip install "nrcd[data]"`)
- `row_to_race_context`, `resolve_column_map`, `COLUMN_ALIASES` for NRCD-style column names
- Factor breakdown — `standardize_xc_detail`, `standardize_result_detail`, `standardize_seconds_detail`
- `StandardizeDetail` / `StandardizeStep` dataclasses (weather, grade, altitude, wind, Riegel steps)
- `enrich_dataframe` and `standardize_dataframe(..., enrich=True)` — batch API backfill with per-meet cache deduplication
- `return_usage=True` on batch enrich — returns `DataframeBatchResult` with aggregate `ApiUsage` (cache misses only; same meet → one OpenWeather lookup)
- `ApiUsage.openweather_total` and `openweather_total` in `to_dict()` for OpenWeather call tracking (geocode + timemachine + AQI)

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

[0.1.2]: https://github.com/National-Running-Club-Database/nrcd/releases/tag/v0.1.2
[0.1.1]: https://github.com/National-Running-Club-Database/nrcd/releases/tag/v0.1.1
[0.1.0]: https://github.com/National-Running-Club-Database/nrcd/releases/tag/v0.1.0
