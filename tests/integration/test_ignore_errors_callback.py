"""Integration: the bundled ``aom_jsonl`` callback emits ``ignore_errors``.

Ansible passes ``ignore_errors`` as a parameter to the
``v2_runner_on_failed`` callback, but the ``ansible.posix.jsonl`` parent
discards it — so a task that failed with ``ignore_errors: true`` looks
identical on the wire to a real failure. The bundled callback re-injects
the flag into the emitted host result so the state machine can classify
the task as tolerated (OK) rather than failed.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "ansible"
CALLBACK_DIR = Path(__file__).resolve().parents[2] / "src" / "ansible_aom" / "ansible" / "callback"


def _has_ansible_posix() -> bool:
    if shutil.which("ansible-galaxy") is None:
        return False
    try:
        result = subprocess.run(
            ["ansible-galaxy", "collection", "list", "ansible.posix"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.SubprocessError, OSError:
        return False
    return "ansible.posix" in result.stdout


_NEEDS_ANSIBLE = pytest.mark.skipif(
    shutil.which("ansible-playbook") is None or not _has_ansible_posix(),
    reason="ansible-playbook or ansible.posix collection unavailable",
)


def _run_playbook(playbook: Path) -> list[dict]:
    env = os.environ.copy()
    env["ANSIBLE_CALLBACK_PLUGINS"] = str(CALLBACK_DIR)
    env["ANSIBLE_STDOUT_CALLBACK"] = "aom_jsonl"
    result = subprocess.run(
        ["ansible-playbook", str(playbook), "-i", "localhost,", "-c", "local"],
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )
    # ignore_errors keeps the run green even though a task failed.
    assert result.returncode == 0, (
        f"ansible-playbook returned {result.returncode}\n"
        f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
    )
    events: list[dict] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


@_NEEDS_ANSIBLE
class TestIgnoreErrorsCallback:
    def test_failed_event_carries_ignore_errors_marker(self) -> None:
        events = _run_playbook(FIXTURES_DIR / "ignore_errors.yml")
        failed = [e for e in events if e.get("_event") == "v2_runner_on_failed"]
        assert len(failed) == 1, f"expected one failed event, got {len(failed)}"
        host_result = failed[0]["hosts"]["localhost"]
        assert host_result.get("failed") is True
        assert host_result.get("ignore_errors") is True

    def test_ok_event_has_no_ignore_errors_marker(self) -> None:
        # The following debug task succeeds — it must not gain the flag.
        events = _run_playbook(FIXTURES_DIR / "ignore_errors.yml")
        ok = [e for e in events if e.get("_event") == "v2_runner_on_ok"]
        assert ok, "expected at least one ok event"
        for e in ok:
            for host_result in e.get("hosts", {}).values():
                assert "ignore_errors" not in host_result

    def test_end_to_end_tally_counts_ignored_failure_as_ok(self) -> None:
        """Producer + consumer compose: the ignored failure lands as OK in the
        state tree, so the status-bar tally shows zero failed."""
        from ansible_aom.core.models import RunState
        from ansible_aom.core.tree import run_state_status_counts

        events = _run_playbook(FIXTURES_DIR / "ignore_errors.yml")
        state = RunState(playbook="ignore_errors.yml")
        for event in events:
            state.handle_event(event)

        counts = run_state_status_counts(state)
        assert counts.failed == 0, f"ignored failure should not count as failed: {counts}"
        assert counts.ok >= 1
