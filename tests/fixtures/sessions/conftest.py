"""Loaders for curated session fixtures.

Each subdirectory under ``tests/fixtures/sessions/`` is a self-contained
session (events.jsonl + meta.json + optional stderr.log) matching the
on-disk layout the runner produces. Tests load them via the
``copy_session_fixture`` fixture which copies a curated session into a
``tmp_path`` so tests can mutate freely without dirtying the checkout.
"""

import json
import shutil
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent


def load_session_dict(name: str) -> dict:
    """Load a curated session fixture as a dict matching load_session()."""
    src = FIXTURES_DIR / name
    meta = json.loads((src / "meta.json").read_text())
    events = [
        json.loads(line)
        for line in (src / "events.jsonl").read_text().splitlines()
        if line.strip()
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
        dst = tmp_path / "sessions" / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(FIXTURES_DIR / name, dst)
        return dst

    return _copy
