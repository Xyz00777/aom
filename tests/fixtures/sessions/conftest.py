"""Loaders for curated session fixtures.

Each subdirectory under ``tests/fixtures/sessions/`` is named by its
``session_id`` (UUIDv7) — matching the on-disk layout the runner
produces, which is what ``list_sessions`` keys off. Friendly names like
``"failed_loop"`` are accepted by the loaders via the ``ALIASES`` map.

Tests load a fixture via:
  - ``load_session_dict("failed_loop")`` — returns a dict shaped like
    ``load_session()`` output (events list parsed, stderr split, etc).
  - ``copy_session_fixture("failed_loop")`` — copies the fixture into a
    ``tmp_path/sessions/<uuid>/`` so tests can mutate freely.
"""

import json
import shutil
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent

ALIASES: dict[str, str] = {
    "clean_run": "019e4000-0000-7000-8000-000000000001",
    "failed_loop": "019e4520-fa64-7000-a627-000000000002",
    "multi_host": "019e4100-0000-7000-8000-000000000003",
    "unreachable": "019e4200-0000-7000-8000-000000000004",
    "running": "019e4300-0000-7000-8000-000000000005",
}


def _resolve(name: str) -> Path:
    """Map a friendly name or raw session_id to its fixture directory."""
    sid = ALIASES.get(name, name)
    return FIXTURES_DIR / sid


def load_session_dict(name: str) -> dict:
    """Load a curated session fixture as a dict matching load_session()."""
    src = _resolve(name)
    meta = json.loads((src / "meta.json").read_text())
    events = [
        json.loads(line) for line in (src / "events.jsonl").read_text().splitlines() if line.strip()
    ]
    stderr_file = src / "stderr.log"
    stderr = stderr_file.read_text().splitlines() if stderr_file.exists() else []
    return {
        **meta,
        "events": events,
        "stderr": stderr,
        "session_id": meta["session_id"],
        "malformed_lines": 0,
    }


@pytest.fixture
def session_fixtures_dir() -> Path:
    """Path to the curated session fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture
def copy_session_fixture(tmp_path: Path):
    """Return a callable that copies a curated session into tmp_path/sessions/."""

    def _copy(name: str) -> Path:
        src = _resolve(name)
        dst = tmp_path / "sessions" / src.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dst)
        return dst

    return _copy
