# Contributing to nrcd

Thanks for helping improve the NRCD standardization library.

## Development setup

Requires Python 3.10+.

```bash
git clone https://github.com/National-Running-Club-Database/nrcd
cd nrcd
pip install -e ".[dev]"
```

Optional extras:

```bash
pip install -e ".[dev,apis]"   # live enrich API tests
pip install -e ".[dev,data]"   # Zenodo CSV example
```

## Running tests

```bash
pytest -m "not live_api"   # same as CI (skips optional live OpenWeather tests)
ruff check src tests examples
```

Runnable examples (no dataset download required):

```bash
python examples/xc_examples.py
python examples/standardize_one_result.py
```

See [examples/README.md](examples/README.md) for the full list.

### Live API tests (optional)

Copy `local_api_keys.env.example` → `local_api_keys.env` (gitignored), add your OpenWeather key, then:

```bash
pytest -m live_api -v
```

Skipped automatically when keys are missing. See [docs/API_KEYS.md](docs/API_KEYS.md).

## Pull requests

1. Branch from `main`.
2. Add or update tests for behavior changes.
3. Keep README / `PARAMETERS_DOC` in sync when public API or defaults change.
4. Run `pytest` and `ruff check src tests examples` before opening the PR.

## Reporting issues

Use [GitHub Issues](https://github.com/National-Running-Club-Database/nrcd/issues). Include Python version, input values, and expected vs actual standardized output when reporting formula bugs.

## Citation

If you use this software in research, please cite the NRCD paper (see [README.md](README.md) and [CITATION.cff](CITATION.cff)).
