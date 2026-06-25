"""Unit tests for include_tasks dynamic expansion.

TC-094 / TC-095 from TEST_SPECIFICATION.md Section 5.2.

When ansible-playbook emits a v2_playbook_on_task_start for a task that
does not appear in the pre-parsed --list-tasks output, AOM grafts a new
TaskDefinition under the most recently matched preflight task (which is
the parent include_tasks node — the only static task that fans out into
unknown children at runtime).

Each grafted definition carries:
- is_dynamic=True
- task_order=-1 (sentinel placing it after static siblings)
- A parent.children link to the include_tasks node
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ansible_aom.core.models import (
    PlayDefinition,
    RunState,
    TaskDefinition,
)


def _task_start(task_id: str, task_name: str, play_id: str = "play-uuid-1") -> dict:
    return {
        "_event": "v2_playbook_on_task_start",
        "_timestamp": "2026-04-20T10:00:00Z",
        "task": {"id": task_id, "name": task_name},
        "play": {"id": play_id},
    }


def _runner_start(task_id: str, task_name: str, host: str = "web1") -> dict:
    return {
        "_event": "v2_runner_on_start",
        "_timestamp": "2026-04-20T10:00:00Z",
        "task": {"id": task_id, "name": task_name},
        "host": host,
    }


def _play_start(play_id: str = "play-uuid-1", name: str = "Test play") -> dict:
    return {
        "_event": "v2_playbook_on_play_start",
        "_timestamp": "2026-04-20T10:00:00Z",
        "play": {"id": play_id, "name": name},
    }


def _task_start_with_path(
    task_id: str,
    task_name: str,
    task_path: str,
    play_id: str = "play-uuid-1",
) -> dict:
    return {
        "_event": "v2_playbook_on_task_start",
        "_timestamp": "2026-04-20T10:00:00Z",
        "task": {"id": task_id, "name": task_name, "path": task_path},
        "play": {"id": play_id},
    }


class TestDynamicExpansion:
    """TC-094 / TC-095: include_tasks dynamic expansion."""

    def test_unknown_task_grafted_as_child_of_last_matched_task(self) -> None:
        """TC-095: Unknown task becomes a child of the last matched preflight task."""
        parent = TaskDefinition(
            name="Include tasks file",
            role=None,
            tags=[],
            play_id="1",
            play_order=0,
            task_order=0,
        )
        defs = [
            PlayDefinition(
                id="1", name="Test", hosts="all", resolved_hosts=["web1"], tasks=[parent]
            )
        ]
        state = RunState(playbook="test.yml", definitions=defs)
        state.handle_event(_play_start())

        # Static include_tasks entry matches preflight; arrival sets parent.
        state.handle_event(_task_start("uuid-static", "Include tasks file"))

        # Unknown task fires next — must graft under the include_tasks node.
        state.handle_event(_task_start("uuid-dynamic", "Dynamic task A"))

        assert len(parent.children) == 1
        dyn = parent.children[0]
        assert dyn.name == "Dynamic task A"
        assert dyn.is_dynamic is True
        assert dyn.task_order == -1

    def test_dynamic_task_inherits_parent_play_fields(self) -> None:
        """Dynamic TaskDefinition copies play_id and play_order from the parent."""
        parent = TaskDefinition(
            name="Include tasks file",
            role=None,
            tags=[],
            play_id="1",
            play_order=7,
            task_order=0,
        )
        defs = [
            PlayDefinition(
                id="1", name="Test", hosts="all", resolved_hosts=["web1"], tasks=[parent]
            )
        ]
        state = RunState(playbook="test.yml", definitions=defs)
        state.handle_event(_play_start())
        state.handle_event(_task_start("uuid-static", "Include tasks file"))
        state.handle_event(_task_start("uuid-dynamic", "Dynamic task A"))

        dyn = parent.children[0]
        assert dyn.play_id == "1"
        assert dyn.play_order == 7

    def test_multiple_unknown_tasks_accumulate_under_same_parent(self) -> None:
        """TC-094: Several dynamic tasks under the same include_tasks parent."""
        parent = TaskDefinition(
            name="Include tasks file",
            role=None,
            tags=[],
            play_id="1",
            play_order=0,
            task_order=0,
        )
        defs = [
            PlayDefinition(
                id="1", name="Test", hosts="all", resolved_hosts=["web1"], tasks=[parent]
            )
        ]
        state = RunState(playbook="test.yml", definitions=defs)
        state.handle_event(_play_start())
        state.handle_event(_task_start("uuid-static", "Include tasks file"))
        state.handle_event(_task_start("uuid-a", "Dynamic task A"))
        state.handle_event(_task_start("uuid-b", "Dynamic task B"))

        assert [c.name for c in parent.children] == ["Dynamic task A", "Dynamic task B"]
        assert all(c.is_dynamic for c in parent.children)
        assert all(c.task_order == -1 for c in parent.children)

    def test_repeated_task_uuid_does_not_re_graft(self) -> None:
        """A second v2_runner_on_start for the same UUID must not graft twice."""
        parent = TaskDefinition(
            name="Include tasks file",
            role=None,
            tags=[],
            play_id="1",
            play_order=0,
            task_order=0,
        )
        defs = [
            PlayDefinition(
                id="1", name="Test", hosts="all", resolved_hosts=["web1"], tasks=[parent]
            )
        ]
        state = RunState(playbook="test.yml", definitions=defs)
        state.handle_event(_play_start())
        state.handle_event(_task_start("uuid-static", "Include tasks file"))
        state.handle_event(_task_start("uuid-dynamic", "Dynamic task A"))
        # Re-arriving event for the same task (e.g. retry under a different
        # phase) must not duplicate the dynamic child.
        state.handle_event(_runner_start("uuid-dynamic", "Dynamic task A"))

        assert len(parent.children) == 1

    def test_static_task_following_dynamic_resets_parent(self) -> None:
        """A subsequent matched preflight task replaces the parent cursor."""
        include_a = TaskDefinition(
            name="Include set A",
            role=None,
            tags=[],
            play_id="1",
            play_order=0,
            task_order=0,
        )
        include_b = TaskDefinition(
            name="Include set B",
            role=None,
            tags=[],
            play_id="1",
            play_order=0,
            task_order=1,
        )
        defs = [
            PlayDefinition(
                id="1",
                name="Test",
                hosts="all",
                resolved_hosts=["web1"],
                tasks=[include_a, include_b],
            )
        ]
        state = RunState(playbook="test.yml", definitions=defs)
        state.handle_event(_play_start())

        state.handle_event(_task_start("uuid-include-a", "Include set A"))
        state.handle_event(_task_start("uuid-a1", "Task A1"))
        state.handle_event(_task_start("uuid-include-b", "Include set B"))
        state.handle_event(_task_start("uuid-b1", "Task B1"))

        assert [c.name for c in include_a.children] == ["Task A1"]
        assert [c.name for c in include_b.children] == ["Task B1"]

    def test_orphan_dynamic_task_when_no_parent_seen_yet(self) -> None:
        """Unknown task before any preflight match is left orphan (no graft, no crash)."""
        sibling = TaskDefinition(
            name="Some other task",
            role=None,
            tags=[],
            play_id="1",
            play_order=0,
            task_order=0,
        )
        defs = [
            PlayDefinition(
                id="1", name="Test", hosts="all", resolved_hosts=["web1"], tasks=[sibling]
            )
        ]
        state = RunState(playbook="test.yml", definitions=defs)
        state.handle_event(_play_start())

        # No matched preflight task yet → unknown task has no parent. The
        # handler must accept the event without raising and without grafting
        # anywhere (no spurious child appears on unrelated definitions).
        state.handle_event(_task_start("uuid-orphan", "Mystery task"))

        assert sibling.children == []

    def test_grafting_works_under_v2_runner_on_start(self) -> None:
        """Free-strategy plays emit v2_runner_on_start instead of task_start.

        The grafting path must apply there too — otherwise free-strategy
        include_tasks dynamic children would never reach the definition tree.
        """
        parent = TaskDefinition(
            name="Include tasks file",
            role=None,
            tags=[],
            play_id="1",
            play_order=0,
            task_order=0,
        )
        defs = [
            PlayDefinition(
                id="1", name="Test", hosts="all", resolved_hosts=["web1"], tasks=[parent]
            )
        ]
        state = RunState(playbook="test.yml", definitions=defs)
        state.handle_event(_play_start())
        state.handle_event(_runner_start("uuid-static", "Include tasks file"))
        state.handle_event(_runner_start("uuid-dynamic", "Dynamic task A"))

        assert len(parent.children) == 1
        assert parent.children[0].name == "Dynamic task A"
        assert parent.children[0].is_dynamic is True
        assert parent.children[0].task_order == -1

    def test_no_grafting_without_definitions(self) -> None:
        """With no preflight definitions there's no parent to graft under."""
        state = RunState(playbook="test.yml")
        state.handle_event(_play_start())
        # No definitions: every task is "unknown" but there's nothing to
        # attach to. Must not raise.
        state.handle_event(_task_start("uuid-a", "Task A"))
        state.handle_event(_task_start("uuid-b", "Task B"))

        assert state.definitions == []


class TestRuntimeIncludeDiscovery:
    """TC-094h / TC-094i: runtime include cache discovery from task.path."""

    def test_task_path_populates_include_cache(self, tmp_path: Path) -> None:
        """TC-094h: An unknown task.path triggers include cache population."""
        from ansible_aom.core.models import TaskDefinition

        include_file = tmp_path / "site.yml"
        include_file.write_text(
            "- name: Alpha\n  debug:\n    msg: a\n- name: Beta\n  debug:\n    msg: b\n"
        )
        parent = TaskDefinition(
            name="Include site",
            role=None,
            tags=[],
            play_id="1",
            play_order=0,
            task_order=0,
        )
        defs = [
            PlayDefinition(
                id="1",
                name="Test",
                hosts="all",
                resolved_hosts=["web1"],
                tasks=[parent],
            )
        ]
        playbook_path = str(tmp_path / "play.yml")
        state = RunState(playbook=playbook_path, definitions=defs)
        state.handle_event(_play_start())
        state.handle_event(
            _task_start_with_path(
                "uuid-include",
                "Include site",
                f"{include_file.name}:2",
            )
        )

        cache_key = str(include_file.resolve())
        assert cache_key in state._include_cache
        assert state._include_cache[cache_key].task_names == ["Alpha", "Beta"]

    def test_runtime_cache_reuses_preflight_entry(self, tmp_path: Path) -> None:
        """TC-094i: A second task hitting the same path reuses the cache."""
        from datetime import datetime, timezone

        from ansible_aom.core.models import IncludeCacheEntry, TaskDefinition

        include_file = tmp_path / "site.yml"
        include_file.write_text("- name: Beta\n  debug:\n    msg: b\n")
        cache_key = str(include_file.resolve())
        preflight_entry = IncludeCacheEntry(
            path=cache_key,
            task_names=["Beta"],
            role=None,
            parsed_at=datetime.now(timezone.utc),
        )
        parent = TaskDefinition(
            name="Include site",
            role=None,
            tags=[],
            play_id="1",
            play_order=0,
            task_order=0,
        )
        defs = [
            PlayDefinition(
                id="1",
                name="Test",
                hosts="all",
                resolved_hosts=["web1"],
                tasks=[parent],
            )
        ]
        playbook_path = str(tmp_path / "play.yml")
        state = RunState(playbook=playbook_path, definitions=defs)
        state._include_cache[cache_key] = preflight_entry

        state.handle_event(_play_start())
        state.handle_event(
            _task_start_with_path(
                "uuid-include",
                "Include site",
                f"{include_file.name}:2",
            )
        )

        assert state._include_cache[cache_key] is preflight_entry
