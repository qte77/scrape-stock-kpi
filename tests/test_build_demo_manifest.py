"""Tests for scripts/build_demo_manifest.py."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build_demo_manifest.py"


def _run(directory: Path) -> subprocess.CompletedProcess[str]:
    # S603 noqa: subprocess invokes a hardcoded local script with the running
    # interpreter; no external input flows into argv.
    return subprocess.run(  # noqa: S603
        [sys.executable, str(_SCRIPT), str(directory)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_writes_manifest_for_dated_snapshots(tmp_path: Path) -> None:
    (tmp_path / "2026-05-10.json").write_text("[]\n")
    (tmp_path / "2026-05-17.json").write_text("[]\n")
    (tmp_path / "2026-05-24.json").write_text("[]\n")

    result = _run(tmp_path)
    assert result.returncode == 0, result.stderr

    manifest = json.loads((tmp_path / "index.json").read_text())
    assert manifest["universe"] == tmp_path.name
    assert manifest["latest"] == "2026-05-24"
    assert manifest["dates"] == ["2026-05-10", "2026-05-17", "2026-05-24"]
    assert manifest["updated_at"].endswith("Z")


def test_skips_non_dated_files(tmp_path: Path) -> None:
    (tmp_path / "2026-05-10.json").write_text("[]\n")
    (tmp_path / "not-a-date.json").write_text("[]\n")
    (tmp_path / "index.json").write_text("{}\n")  # pre-existing index ignored

    result = _run(tmp_path)
    assert result.returncode == 0, result.stderr

    manifest = json.loads((tmp_path / "index.json").read_text())
    assert manifest["dates"] == ["2026-05-10"]
    assert manifest["latest"] == "2026-05-10"


def test_empty_directory_exits_nonzero(tmp_path: Path) -> None:
    result = _run(tmp_path)
    assert result.returncode == 1


def test_missing_directory_exits_nonzero(tmp_path: Path) -> None:
    result = _run(tmp_path / "does-not-exist")
    assert result.returncode == 1
