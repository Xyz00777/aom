"""``aom inspect prune --days N`` is an age-only policy (issue #16).

It must not silently apply a session-count cap: more than 100 recent
sessions all survive, while sessions older than the threshold are removed.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ansible_aom.inspect.cli import main as inspect_main
from ansible_aom.session.store import cleanup_old_sessions


def _write_sessions(state_dir: Path, count: int, age: timedelta, prefix: str) -> None:
    start = (datetime.now(timezone.utc) - age).isoformat()
    for i in range(count):
        session = state_dir / f"{prefix}-{i:03d}"
        session.mkdir()
        (session / "meta.json").write_text(json.dumps({"start_time": start}))


def test_prune_days_keeps_more_than_100_recent_sessions(tmp_path: Path, capsys) -> None:
    _write_sessions(tmp_path, 101, timedelta(minutes=1), "recent")

    assert inspect_main(["--state-dir", str(tmp_path), "prune", "--days", "30"]) == 0

    assert len(list(tmp_path.iterdir())) == 101
    assert "Pruned 0 session(s)" in capsys.readouterr().out


def test_prune_days_removes_only_sessions_older_than_threshold(tmp_path: Path) -> None:
    _write_sessions(tmp_path, 101, timedelta(minutes=1), "recent")
    _write_sessions(tmp_path, 3, timedelta(days=31), "old")

    inspect_main(["--state-dir", str(tmp_path), "prune", "--days", "30"])

    remaining = {p.name for p in tmp_path.iterdir()}
    assert len(remaining) == 101
    assert all(name.startswith("recent-") for name in remaining)


def test_cleanup_without_keep_count_applies_no_count_cap(tmp_path: Path) -> None:
    _write_sessions(tmp_path, 105, timedelta(minutes=1), "recent")

    assert cleanup_old_sessions(tmp_path, keep_days=30) == 0
    assert len(list(tmp_path.iterdir())) == 105
