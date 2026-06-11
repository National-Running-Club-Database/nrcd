"""Packaging metadata checks."""

import subprocess
import sys
import tarfile
from pathlib import Path

import pytest


def test_top_level_exports():
    import nrcd

    for name in nrcd.__all__:
        assert hasattr(nrcd, name)


def test_format_time_not_on_top_level():
    with pytest.raises(ImportError):
        from nrcd import format_time  # noqa: F401


def test_py_typed_marker():
    root = Path(__file__).resolve().parents[1]
    assert (root / "src" / "nrcd" / "py.typed").is_file()


def test_sdist_includes_examples(tmp_path):
    root = Path(__file__).resolve().parents[1]
    subprocess.run(
        [sys.executable, "-m", "build", "--sdist", "-o", str(tmp_path)],
        cwd=root,
        check=True,
        capture_output=True,
    )
    sdist = next(tmp_path.glob("*.tar.gz"))
    with tarfile.open(sdist, "r:gz") as archive:
        names = archive.getnames()
    assert any(name.startswith("nrcd-") and "/examples/" in name for name in names)
    assert any(name.endswith("examples/xc_examples.py") for name in names)


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
