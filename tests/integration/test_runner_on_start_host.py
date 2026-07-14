"""Integration: ``v2_runner_on_start`` must identify which host started.

``ansible.posix.jsonl`` emits ``v2_runner_on_start`` (non-lockstep
strategies only) with ``hosts: {}`` and no ``host`` field — the host
name lives only in the callback's internal ``_task_map``. AOM's state
machine reads ``event["host"]`` to mark that host RUNNING, so with the
stock shape no host is ever marked running under ``strategy: free``:
tasks keep empty host maps, the tree falls back to rendering every play
target as RUNNING with a single shared timer, and streamed ok results
appear to be ignored (observed 2026-07-14/15 on a 20-host AIDE playbook
run with a non-lockstep strategy plugin).

The bundled ``aom_jsonl`` callback therefore annotates the event with
``host``. These tests run a real ``ansible-playbook`` under
``strategy: free`` with two hosts and assert the annotation.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

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


_FREE_PLAYBOOK = """\
- hosts: all
  gather_facts: false
  strategy: free
  tasks:
    - name: free-strategy task
      ansible.builtin.command: sleep 0.2
      changed_when: false
"""


def _run_free_playbook(tmp_path: Path) -> list[dict]:
    playbook = tmp_path / "free.yml"
    playbook.write_text(_FREE_PLAYBOOK)
    env = os.environ.copy()
    env["ANSIBLE_CALLBACK_PLUGINS"] = str(CALLBACK_DIR)
    env["ANSIBLE_STDOUT_CALLBACK"] = "aom_jsonl"
    result = subprocess.run(
        ["ansible-playbook", str(playbook), "-i", "h1,h2", "-c", "local"],
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )
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
class TestRunnerOnStartCarriesHost:
    def test_every_runner_on_start_names_its_host(self, tmp_path) -> None:
        events = _run_free_playbook(tmp_path)
        starts = [e for e in events if e.get("_event") == "v2_runner_on_start"]
        # strategy: free is non-lockstep, so per-host start events MUST
        # be emitted at all.
        assert starts, f"no v2_runner_on_start events emitted:\n{events}"
        hosts_seen = {e.get("host") for e in starts}
        assert hosts_seen == {"h1", "h2"}, (
            f"expected every start event to carry its host, got hosts={hosts_seen}\n{starts}"
        )
