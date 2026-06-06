"""Packaging metadata checks."""

import sys
from pathlib import Path


def test_py_typed_marker():
    root = Path(__file__).resolve().parents[1]
    assert (root / "src" / "nrcd" / "py.typed").is_file()


def test_data_import_without_pandas():
    for name in list(sys.modules):
        if name == "pandas" or name.startswith("pandas."):
            del sys.modules[name]
    import importlib

    import nrcd.data

    importlib.reload(nrcd.data)
    assert "pandas" not in sys.modules
    from nrcd.data.schema import derive_course_details_fields

    assert derive_course_details_fields({"temperature": 80, "dew_point": 70})["heat_index_f"] == 150.0
