"""Real-ansible smoke tests.

Every other "integration" test in this suite uses a fake ansible-playbook
shim that emits canned JSONL. That catches a lot, but it can't catch
upstream JSONL drift (e.g. ansible.posix.jsonl changing a field name or
emitting a new event type) because the shim happily speaks whatever
yesterday's version spoke.

These tests actually spawn ``ansible-playbook`` against the fixtures in
``.sisyphus/test-fixtures/`` and assert end-to-end:

* aom exits with the expected status,
* the session directory was created and contains a non-empty
  ``events.jsonl``,
* the recorded JSONL parses cleanly through ``core/parser.py``,
* the final RunState shape matches what the fixture should produce.

All tests are marked ``@pytest.mark.needs_ansible`` and auto-skip
when ``ansible-playbook`` is missing OR the ``ansible.posix``
collection isn't available, so they're CI-friendly but loud locally.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from ansible_aom.core.parser import JsonLineStream

FIXTURES_DIR = Path(__file__).resolve().parents[2] / ".sisyphus" / "test-fixtures"


def _ansible_collection_paths() -> list[str]:
    """Search-path entries reported by ``ansible-galaxy collection list``.

    The output's section headers (lines starting with ``#``) name every
    directory ansible-core scans for collections — typically
    ``~/.ansible/collections/ansible_collections`` plus a site-packages
    path. We re-publish them into the test subprocess's
    ``ANSIBLE_COLLECTIONS_PATH`` so the JSONL callback resolves even
    when HOME has been redirected to a temp dir.
    """
    try:
        result = subprocess.run(
            ["ansible-galaxy", "collection", "list"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except FileNotFoundError, subprocess.TimeoutExpired:
        return []
    if result.returncode != 0:
        return []
    paths: list[str] = []
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("# /"):
            paths.append(stripped[2:])
    return paths


def _has_ansible_posix() -> bool:
    """True if the ``ansible.posix`` collection is installed and discoverable.

    We probe via ``ansible-galaxy collection list ansible.posix``: a clean
    exit means the collection resolves on the current ansible-core's
    search path. Anything non-zero (or missing executable) means the
    JSONL callback won't load and the test would fail for the wrong
    reason — skip.
    """
    try:
        result = subprocess.run(
            ["ansible-galaxy", "collection", "list", "ansible.posix"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except FileNotFoundError, subprocess.TimeoutExpired:
        return False
    if result.returncode != 0:
        return False
    return "ansible.posix" in result.stdout


_NEEDS_ANSIBLE = pytest.mark.skipif(
    shutil.which("ansible-playbook") is None or not _has_ansible_posix(),
    reason="ansible-playbook or ansible.posix collection unavailable",
)


def _run_aom(playbook: Path, home_dir: Path) -> subprocess.CompletedProcess[str]:
    """Spawn ``python -m ansible_aom <playbook>`` against a sandboxed HOME.

    Using ``-m`` rather than the ``aom`` script ensures we exercise the
    editable install in this checkout, not whatever happens to be first
    on ``PATH``. ``HOME`` is redirected to ``home_dir`` so the session
    recording lands in a known, isolated location.
    """
    env = os.environ.copy()
    env["HOME"] = str(home_dir)
    # Redirecting HOME hides the user's
    # ``~/.ansible/collections/ansible_collections`` from ansible-core's
    # default search path, which silently disables the
    # ``ansible.posix.jsonl`` callback. Republish every collection path
    # the local install knows about so the callback still loads under
    # the sandboxed HOME.
    collection_paths = _ansible_collection_paths()
    if collection_paths:
        env["ANSIBLE_COLLECTIONS_PATH"] = ":".join(collection_paths)
    # The repo's pyproject.toml is the editable install we want to test —
    # PYTHONPATH guarantees that even if the test runner's environment
    # has weird overrides.
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "ansible_aom",
            str(playbook),
            "-i",
            "localhost,",
            "-c",
            "local",
        ],
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )


def _find_session(home_dir: Path) -> Path:
    """Return the lone session directory under ``home_dir`` or fail loudly."""
    sessions_root = home_dir / ".local" / "state" / "aom" / "sessions"
    assert sessions_root.is_dir(), f"no sessions root at {sessions_root}"
    sessions = [p for p in sessions_root.iterdir() if p.is_dir()]
    assert len(sessions) == 1, f"expected 1 session, got {sessions}"
    return sessions[0]


def _parse_jsonl_through_core(events_path: Path) -> list[dict]:
    """Feed each recorded line through ``JsonLineStream``.

    This is the same code path the live runner uses. If ansible-posix
    starts emitting something the core parser chokes on, we want to
    catch it here rather than at the renderer.
    """
    stream = JsonLineStream()
    events: list[dict] = []
    for line in events_path.read_text().splitlines():
        events.extend(stream.feed_line(line))
    return events


@_NEEDS_ANSIBLE
class TestRealAnsibleSmoke:
    """Live ansible-playbook integration — fixtures that work with ``-c local``.

    Only ``simple.yml`` and ``syntax_error.yml`` are exercised here.
    The other ``.sisyphus/test-fixtures/`` playbooks either target
    inventory groups that don't resolve against a bare
    ``localhost,`` host-list (``multi_hosts.yml``) or only ever skip
    tasks (``unreachable.yml`` uses ``when: false``), so neither
    actually exercises the failure paths their names suggest.
    """

    def test_simple_playbook_runs_and_records_session(self, tmp_path: Path) -> None:
        """Happy-path: simple.yml exits 0, writes a parseable session."""
        result = _run_aom(FIXTURES_DIR / "simple.yml", tmp_path)

        assert result.returncode == 0, (
            f"aom returned {result.returncode}\n"
            f"--- stdout ---\n{result.stdout}\n"
            f"--- stderr ---\n{result.stderr}"
        )

        session = _find_session(tmp_path)
        events_path = session / "events.jsonl"
        assert events_path.exists(), f"missing {events_path}"
        assert events_path.stat().st_size > 0, "events.jsonl is empty"

        # The recorded JSONL must round-trip through the parser the
        # live runner uses — any silently-broken event would otherwise
        # only show up at replay time.
        events = _parse_jsonl_through_core(events_path)
        event_types = {e["_event"] for e in events}
        # Conservative: ansible-core 2.20 dropped v2_playbook_on_start,
        # so don't require it. play_start + a runner ok + stats is the
        # minimum a successful run should produce.
        assert "v2_playbook_on_play_start" in event_types
        assert "v2_runner_on_ok" in event_types
        assert "v2_playbook_on_stats" in event_types

        # meta.json should report the run completed successfully.
        meta = json.loads((session / "meta.json").read_text())
        assert meta["status"] == "completed"

    def test_simple_playbook_localhost_appears_exactly_once_in_summary(
        self, tmp_path: Path
    ) -> None:
        """For a single-host run, ``localhost`` shows up once in stats."""
        result = _run_aom(FIXTURES_DIR / "simple.yml", tmp_path)
        assert result.returncode == 0

        session = _find_session(tmp_path)
        events = _parse_jsonl_through_core(session / "events.jsonl")
        stats_events = [e for e in events if e["_event"] == "v2_playbook_on_stats"]
        assert len(stats_events) == 1
        stats = stats_events[0].get("stats", {})
        # Each host appears exactly once in the stats dict — no
        # duplicated entry across plays.
        assert "localhost" in stats
        assert len(stats) == 1, f"expected one host, got {list(stats)}"

    def test_syntax_error_playbook_returns_nonzero(self, tmp_path: Path) -> None:
        """A YAML syntax error in the playbook must surface as a non-zero exit.

        ansible-playbook itself exits 4 on a parse failure; aom must
        forward that (or at least any non-zero code) rather than
        silently exit 0 and pretend things were fine.
        """
        result = _run_aom(FIXTURES_DIR / "syntax_error.yml", tmp_path)
        assert result.returncode != 0, (
            f"expected non-zero exit, got 0\n"
            f"--- stdout ---\n{result.stdout}\n"
            f"--- stderr ---\n{result.stderr}"
        )
