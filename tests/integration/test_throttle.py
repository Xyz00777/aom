"""Real-ansible throttle awareness test (RED — TDD failing test).

This test is **intentionally failing** as part of the OODA loop on aom's
``throttle:`` awareness. There is currently no ``wave_progress`` data on
``TaskRunState``, no ``throttle`` field on ``TaskDefinition``, and no
``WaveProgress`` class anywhere in ``src/ansible_aom/core/``. The
assertions below encode the **observable contract** the implementation
must satisfy, but they will hit ``AttributeError`` / missing attributes
today. The failing red bar is the deliverable for this commit.

## Why a behavioural contract and not a YAML-extraction spec?

The throttle evidence captured in
``.sisyphus/notepads/throttle-investigation/learnings.md`` shows that
the JSONL stream carries **zero structured signal** for
``throttle:``. The cap (2) is only visible indirectly, via burst
clustering of ``v2_runner_on_ok`` events. Three reasonable detection
strategies exist — YAML parse, stream inference, hybrid — and the user
hasn't yet picked one. This test asserts the observable end-state
(wave count, per-host wave assignment, throttle cap on the task def)
rather than any one extraction approach, so all three are free to
implement it.

## What the contract requires

For a 6-host, single-throttled-task playbook (``throttle: 2``):

1. The ``TaskDefinition`` for the throttled task must carry a
   ``throttle`` attribute whose value is ``2``.
2. ``RunState`` (or whatever aom exposes as the recorded session
   state) must record ``wave_progress`` after the run completes.
3. The number of waves must be ``3``.
4. Per-host wave assignment must be:
   - ``{h1, h2} -> wave 1``
   - ``{h3, h4} -> wave 2``
   - ``{h5, h6} -> wave 3``

The test runs real ``ansible-playbook`` (not a fake shim) against the
fixture in ``.sisyphus/test-fixtures/with_throttle.yml`` and asserts
against the recorded session.

Skips automatically when ``ansible-playbook`` or the
``ansible.posix`` collection isn't available — same gate as
``test_real_ansible.py``.
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

    Mirror of the helper in ``test_real_ansible.py``; kept local so this
    test file stands on its own when read in isolation. Redirecting
    ``HOME`` hides the user's
    ``~/.ansible/collections/ansible_collections`` from ansible-core's
    default search path, so we re-publish every collection path the
    local install knows about.
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
    """True if ``ansible.posix`` is installed and discoverable.

    Without it the JSONL callback won't load and the test would fail
    for the wrong reason.
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

    The fixture targets ``all`` on a comma-separated inventory of six
    hosts (``h1,h2,h3,h4,h5,h6,``). ``-c local`` keeps the run on the
    test host — the throttle timing is what matters, not the network.
    """
    env = os.environ.copy()
    env["HOME"] = str(home_dir)
    collection_paths = _ansible_collection_paths()
    if collection_paths:
        env["ANSIBLE_COLLECTIONS_PATH"] = ":".join(collection_paths)
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "ansible_aom",
            str(playbook),
            "-i",
            "h1,h2,h3,h4,h5,h6,",
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

    Same code path the live runner uses — guarantees the captured stream
    is parseable, not just present on disk.
    """
    stream = JsonLineStream()
    events: list[dict] = []
    for line in events_path.read_text().splitlines():
        events.extend(stream.feed_line(line))
    return events


@_NEEDS_ANSIBLE
class TestThrottleAwareness:
    """Behavioural contract: aom must surface ``throttle:`` and wave progress.

    Runs ``with_throttle.yml`` (6 hosts, ``throttle: 2``, single task
    taking ~1s per host) against a real ``ansible-playbook`` and asserts
    that the recorded session carries throttle awareness:

    * ``TaskDefinition.throttle`` is populated for the throttled task.
    * ``RunState.wave_progress`` (or the recorded equivalent) records
      exactly 3 waves.
    * Hosts are assigned to waves correctly: ``{h1,h2}``, ``{h3,h4}``,
      ``{h5,h6}``.

    These attributes and concepts do not exist in ``core/`` yet; the
    test will surface an ``AttributeError`` or ``ImportError`` on the
    first assertion that touches them. That is the red bar.
    """

    def test_throttle_cap_recorded_on_task_definition(self, tmp_path: Path) -> None:
        """``TaskDefinition.throttle == 2`` for the throttled task after the run.

        Spec: the recorded session must expose ``TaskDefinition.throttle``
        populated with the playbook's cap. Strategy-agnostic — YAML
        parse, runtime inference, or hybrid all satisfy this.
        """
        from ansible_aom.core.models import TaskDefinition  # noqa: F401

        result = _run_aom(FIXTURES_DIR / "with_throttle.yml", tmp_path)
        assert result.returncode == 0, (
            f"aom returned {result.returncode}\n"
            f"--- stdout ---\n{result.stdout}\n"
            f"--- stderr ---\n{result.stderr}"
        )

        session = _find_session(tmp_path)
        meta = json.loads((session / "meta.json").read_text())

        # RunState may be persisted under one of several keys (the
        # schema isn't fixed yet — this test should drive that
        # decision). Probe a few plausible locations; whichever the
        # implementation chooses must carry the throttle def.
        run_state = meta.get("run_state") or meta.get("definitions") or meta.get("preflight")

        assert run_state is not None, (
            f"meta.json has no run_state/definitions/preflight payload: {list(meta)}"
        )

        task_defs: list[TaskDefinition] = []
        for play in run_state.get("plays", []):
            for tdef in play.get("tasks", []):
                if isinstance(tdef, dict):
                    task_defs.append(TaskDefinition(**tdef))
                else:
                    task_defs.append(tdef)

        throttled = [td for td in task_defs if "Throttled task" in (td.name or "")]
        assert len(throttled) == 1, (
            f"expected exactly one throttled task def, got {len(throttled)}: "
            f"{[td.name for td in task_defs]}"
        )

        assert getattr(throttled[0], "throttle") == 2

    def test_wave_progress_records_three_waves(self, tmp_path: Path) -> None:
        """``RunState.wave_progress.wave_count == 3`` for 6 hosts @ throttle 2.

        6 hosts / 2-cap = 3 waves. The recorded session must surface
        this count.
        """
        result = _run_aom(FIXTURES_DIR / "with_throttle.yml", tmp_path)
        assert result.returncode == 0, (
            f"aom returned {result.returncode}\n"
            f"--- stdout ---\n{result.stdout}\n"
            f"--- stderr ---\n{result.stderr}"
        )

        session = _find_session(tmp_path)
        meta = json.loads((session / "meta.json").read_text())

        run_state = meta.get("run_state") or {}
        wave_progress = run_state.get("wave_progress")

        assert wave_progress is not None, (
            "recorded session has no wave_progress; throttle awareness is not yet implemented"
        )
        assert wave_progress.get("wave_count") == 3

    def test_wave_assignment_matches_host_bursts(self, tmp_path: Path) -> None:
        """``RunState.wave_progress.per_host`` matches the observed burst pattern.

        Derives expected wave assignment from the recorded JSONL burst
        pattern (500ms gap threshold), then asserts the recorded
        ``per_host`` map carries that assignment for every host.
        """
        result = _run_aom(FIXTURES_DIR / "with_throttle.yml", tmp_path)
        assert result.returncode == 0, (
            f"aom returned {result.returncode}\n"
            f"--- stdout ---\n{result.stdout}\n"
            f"--- stderr ---\n{result.stderr}"
        )

        session = _find_session(tmp_path)
        events = _parse_jsonl_through_core(session / "events.jsonl")

        ok_events: list[tuple[str, str]] = []
        for e in events:
            if e.get("_event") != "v2_runner_on_ok":
                continue
            for host in e.get("hosts", {}):
                ok_events.append((host, e.get("_timestamp", "")))

        from datetime import datetime

        def _parse_ts(ts: str) -> datetime:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))

        expected_wave: dict[str, int] = {}
        current_wave = 1
        prev_ts: datetime | None = None
        for host, ts in ok_events:
            parsed = _parse_ts(ts)
            if prev_ts is not None and (parsed - prev_ts).total_seconds() > 0.5:
                current_wave += 1
            expected_wave[host] = current_wave
            prev_ts = parsed

        assert sorted(expected_wave.values()) == [1, 1, 2, 2, 3, 3], (
            f"observed burst pattern did not produce 3 waves of 2: {expected_wave}"
        )

        meta = json.loads((session / "meta.json").read_text())
        run_state = meta.get("run_state") or {}
        wave_progress = run_state.get("wave_progress") or {}

        per_host = wave_progress.get("per_host") or {}
        assert per_host, "wave_progress.per_host missing — per-host assignment is not yet recorded"

        for host, expected in expected_wave.items():
            assert per_host.get(host) == expected, (
                f"host {host}: expected wave {expected}, got "
                f"{per_host.get(host)} (full assignment: {per_host})"
            )
