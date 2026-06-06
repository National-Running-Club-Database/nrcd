# Examples

Runnable scripts — **no NRCD Zenodo download** required except `load_dataset_example.py`.

## Cross country

| Script | What it shows |
|--------|----------------|
| [`standardize_one_result.py`](standardize_one_result.py) | Minimal XC + track one-liners |
| [`xc_examples.py`](xc_examples.py) | 5K/6K/8mi, clock strings, °F/°C, ft/m altitude, grade %/ft/m |
| [`compare_improvement.py`](compare_improvement.py) | Two meets — raw vs standardized improvement |

## Track

| Script | What it shows |
|--------|----------------|
| [`track_outdoor_examples.py`](track_outdoor_examples.py) | 100m wind, hurdles, 400m–10K, weather, altitude, course grade |
| [`track_indoor_examples.py`](track_indoor_examples.py) | Lap length, banked vs flat, wind ignored indoors |
| [`track_compare_meets.py`](track_compare_meets.py) | Same raw time across meets (wind, heat, altitude) |

## Both / advanced

| Script | What it shows |
|--------|----------------|
| [`race_context_example.py`](race_context_example.py) | `RaceContext` + `standardize_seconds` for XC and track rows |
| [`load_dataset_example.py`](load_dataset_example.py) | Optional Zenodo CSV workflow (`pip install "nrcd[data]"`); exits 1 without CSVs in `data/` |

## Run

```bash
pip install -e ".[dev]"
python examples/xc_examples.py
python examples/track_outdoor_examples.py
python examples/track_indoor_examples.py
python examples/track_compare_meets.py
python examples/compare_improvement.py
python examples/race_context_example.py
python examples/standardize_one_result.py
```

From the repo root with an editable install or `PYTHONPATH=src`.
