"""Integration: skipped meta tasks in non-lockstep strategies must not fail callback dispatch.

When a playbook runs under a non-lockstep strategy (e.g. ``strategy: free``),
Ansible executes ``meta`` tasks (such as ``flush_handlers``) inline via
``_execute_meta`` rather than scheduling them through ``_queue_task``. As a
result, ``v2_runner_on_start`` is never dispatched for the meta task and
no entry is created in the callback's internal ``_task_map``.

If the meta task has a conditional (``when:``) that evaluates to ``False``,
Ansible calls ``v2_runner_on_skipped``. Upstream ``ansible.posix.jsonl``
attempts ``del self._task_map[key]`` in non-lockstep mode, raising a
``KeyError: (host, task_uuid)`` and causing Ansible to log:
    [WARNING]: Callback dispatch 'v2_runner_on_skipped' failed for plugin 'aom_jsonl'
and silently drop the skipped event.

These tests assert that:
1. No callback dispatch warning is logged to stderr.
2. The ``v2_runner_on_skipped`` event is properly emitted with the meta task's
   own name and id (not corrupted by whatever task ran previously).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ansible_aom.ansible.callback.aom_jsonl import CallbackModule

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


_FREE_META_PLAYBOOK = """\
- hosts: localhost
  gather_facts: false
  strategy: free
  tasks:
    - name: Regular task before
      ansible.builtin.debug:
        msg: "before"
    - name: Flush handlers meta task
      ansible.builtin.meta: flush_handlers
      when: false
    - name: Regular task after
      ansible.builtin.debug:
        msg: "after"
"""


def _run_meta_playbook(tmp_path: Path) -> tuple[int, str, list[dict]]:
    playbook = tmp_path / "free_meta.yml"
    playbook.write_text(_FREE_META_PLAYBOOK)
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
    events: list[dict] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return result.returncode, result.stderr, events


@_NEEDS_ANSIBLE
class TestFreeStrategySkippedMetaTask:
    def test_skipped_meta_task_emits_event_without_warning(self, tmp_path: Path) -> None:
        rc, stderr, events = _run_meta_playbook(tmp_path)
        assert rc == 0
        assert "Callback dispatch 'v2_runner_on_skipped' failed" not in stderr

        skipped_events = [e for e in events if e.get("_event") == "v2_runner_on_skipped"]
        assert len(skipped_events) == 1, f"expected 1 skipped event, got: {skipped_events}"

        meta_event = skipped_events[0]
        assert meta_event["task"]["name"] == "Flush handlers meta task"
        assert meta_event["hosts"]["localhost"]["action"] == "ansible.builtin.meta"
        assert meta_event["hosts"]["localhost"]["skipped"] is True

        # Ensure task IDs are distinct — the meta task must not reuse the prior task's ID
        task_ids = {e["task"]["id"] for e in events if "task" in e and "id" in e["task"]}
        assert len(task_ids) == 3

    def test_end_to_end_state_tree_records_skipped_meta_task(self, tmp_path: Path) -> None:
        from ansible_aom.core.models import RunState, Status

        rc, stderr, events = _run_meta_playbook(tmp_path)
        assert rc == 0
        state = RunState(playbook="free_meta.yml")
        for event in events:
            state.handle_event(event)

        play = list(state.plays.values())[0]
        skipped_tasks = [t for t in play.tasks.values() if t.name == "Flush handlers meta task"]
        assert len(skipped_tasks) == 1
        meta_task = skipped_tasks[0]
        assert meta_task.status == Status.COMPLETED
        assert "localhost" in meta_task.hosts
        assert meta_task.hosts["localhost"].status == Status.SKIPPED


class TestCallbackModuleDirect:
    """Direct unit tests for CallbackModule handling tasks unstarted in _task_map."""

    def _make_callback(self, lockstep: bool = False) -> CallbackModule:
        with (
            patch.object(CallbackModule, "set_options"),
            patch.object(CallbackModule, "get_option", return_value=0),
        ):
            cb = CallbackModule()
            cb._display = MagicMock()
            cb._is_lockstep = lockstep
            cb.results = [{"play": {"duration": {"start": "2026-10-27T00:00:00Z"}}, "tasks": []}]
            return cb

    def test_find_result_task_creates_new_task_when_not_in_task_map(self) -> None:
        cb = self._make_callback(lockstep=False)

        host = MagicMock()
        host.get_name.return_value = "ipa1"
        host.name = "ipa1"

        task = MagicMock()
        task._uuid = "meta-uuid-1"
        task.get_name.return_value = "Flush handlers"
        task.get_path.return_value = "playbook.yml:10"
        task.action = "ansible.builtin.meta"

        # Prior task in results to ensure it is not mistakenly picked up
        cb.results[-1]["tasks"].append({"task": {"id": "prior-uuid", "name": "Prior"}})

        task_result = cb._find_result_task(host, task)
        assert task_result["task"]["id"] == "meta-uuid-1"
        assert task_result["task"]["name"] == "Flush handlers"

    def test_record_task_result_does_not_raise_key_error_when_unstarted(self) -> None:
        cb = self._make_callback(lockstep=False)

        host = MagicMock()
        host.get_name.return_value = "ipa1"
        host.name = "ipa1"

        task = MagicMock()
        task._uuid = "meta-uuid-2"
        task.get_name.return_value = "Flush handlers"
        task.get_path.return_value = "playbook.yml:10"
        task.action = "ansible.builtin.meta"

        result = MagicMock()
        result._host = host
        result._task = task
        result._result = {"skipped": True, "skip_reason": "Conditional was False"}

        # Prior task in results with valid duration structure
        cb.results[-1]["tasks"].append(
            {
                "task": {"id": "prior-uuid", "duration": {"start": "2026-10-27T00:00:00Z"}},
                "hosts": {},
            }
        )

        # Must not raise KeyError: ('ipa1', 'meta-uuid-2')
        cb.v2_runner_on_skipped(result)

        # Ensure _write_event was called with the correct task
        cb._display.display.assert_called_once()
        written_json = json.loads(cb._display.display.call_args[0][0])
        assert written_json["_event"] == "v2_runner_on_skipped"
        assert written_json["task"]["id"] == "meta-uuid-2"
        assert written_json["task"]["name"] == "Flush handlers"
        assert written_json["hosts"]["ipa1"]["skipped"] is True
