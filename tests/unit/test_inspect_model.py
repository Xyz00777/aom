"""Unit tests for core.inspect_model — pure builders over session dicts."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ansible_aom.core.inspect_model import (
    DetailBlock,  # noqa: F401  (re-exported for downstream tests)
    LoopItem,  # noqa: F401
    RunSummary,
    StatusCounts,
    TaskTreeNode,  # noqa: F401
    build_detail_block,
    build_run_summaries,
    build_run_summary,
    build_task_tree,
)

_ALIASES = {
    "clean_run": "019e4000-0000-7000-8000-000000000001",
    "failed_loop": "019e4520-fa64-7000-a627-000000000002",
    "multi_host": "019e4100-0000-7000-8000-000000000003",
    "unreachable": "019e4200-0000-7000-8000-000000000004",
    "running": "019e4300-0000-7000-8000-000000000005",
    "real_shape": "019e4600-0000-7000-8000-000000000006",
}


def _load_fixture(name: str) -> dict:
    """Helper: load a session fixture as load_session would return it."""
    sid = _ALIASES.get(name, name)
    src = Path(__file__).parent.parent / "fixtures" / "sessions" / sid
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


# ── StatusCounts ─────────────────────────────────────────────────────────────


def test_statuscounts_starts_empty():
    counts = StatusCounts()
    assert counts.ok == 0
    assert counts.changed == 0
    assert counts.failed == 0
    assert counts.skipped == 0
    assert counts.unreachable == 0
    assert counts.total == 0


def test_statuscounts_add_event_ok():
    counts = StatusCounts().add_event("v2_runner_on_ok", changed=False)
    assert counts.ok == 1
    assert counts.changed == 0
    assert counts.total == 1


def test_statuscounts_add_event_changed():
    counts = StatusCounts().add_event("v2_runner_on_ok", changed=True)
    assert counts.ok == 0
    assert counts.changed == 1


def test_statuscounts_add_event_failed():
    assert StatusCounts().add_event("v2_runner_on_failed", changed=False).failed == 1


def test_statuscounts_add_event_skipped():
    assert StatusCounts().add_event("v2_runner_on_skipped", changed=False).skipped == 1


def test_statuscounts_add_event_unreachable():
    assert StatusCounts().add_event("v2_runner_on_unreachable", changed=False).unreachable == 1


def test_statuscounts_merge():
    a = StatusCounts(ok=2, failed=1)
    b = StatusCounts(ok=3, changed=4)
    merged = a.merge(b)
    assert merged.ok == 5
    assert merged.changed == 4
    assert merged.failed == 1
    assert merged.total == 10


def test_statuscounts_is_all_ok():
    assert StatusCounts(ok=5, changed=2).is_all_ok() is True
    assert StatusCounts(ok=5, failed=1).is_all_ok() is False
    assert StatusCounts(ok=5, unreachable=1).is_all_ok() is False
    assert StatusCounts().is_all_ok() is True


# ── RunSummary ───────────────────────────────────────────────────────────────


def test_run_summary_clean():
    session = _load_fixture("clean_run")
    summary = build_run_summary(session)
    assert summary.session_id == "019e4000-0000-7000-8000-000000000001"
    assert summary.short_id == "019e4000"
    assert summary.playbook == "ansible/site.yml"
    assert summary.status == "completed"
    assert summary.start_time == datetime(2026, 5, 19, 18, 2, 0, tzinfo=timezone.utc)
    assert summary.end_time == datetime(2026, 5, 19, 18, 2, 42, tzinfo=timezone.utc)
    assert summary.duration == timedelta(seconds=42)
    assert summary.failed_task_count == 0
    assert summary.host_counts == {"web1": StatusCounts(ok=1, changed=1)}


def test_run_summary_failed_loop():
    session = _load_fixture("failed_loop")
    summary = build_run_summary(session)
    assert summary.status == "failed"
    assert summary.failed_task_count == 1
    assert summary.host_counts == {"caeli": StatusCounts(ok=1, failed=1)}


def test_run_summary_running_has_no_end():
    session = _load_fixture("running")
    summary = build_run_summary(session)
    assert summary.status == "running"
    assert summary.end_time is None
    assert summary.duration is None


def test_run_summaries_sorted_newest_first():
    sessions = [
        _load_fixture("clean_run"),  # 2026-05-19 18:02
        _load_fixture("failed_loop"),  # 2026-05-20 11:24
        _load_fixture("multi_host"),  # 2026-05-19 15:00
    ]
    summaries = build_run_summaries(sessions)
    assert [s.short_id for s in summaries] == ["019e4520", "019e4000", "019e4100"]


# ── TaskTree ─────────────────────────────────────────────────────────────────


def test_task_tree_clean_run_groups_by_role():
    session = _load_fixture("clean_run")
    root = build_task_tree(session)
    assert root.kind == "run"
    assert len(root.children) == 1
    play = root.children[0]
    assert play.kind == "play"
    assert play.label == "all"
    assert play.stats == StatusCounts(ok=1, changed=1)
    assert len(play.children) == 1
    group = play.children[0]
    assert group.kind == "group"
    assert group.label == "common"
    assert group.stats == StatusCounts(ok=1, changed=1)
    task_labels = [c.label for c in group.children]
    assert task_labels == ["common : ping", "common : echo"]


def test_task_tree_failed_loop_marks_failure_path():
    session = _load_fixture("failed_loop")
    root = build_task_tree(session)
    play = root.children[0]
    group = play.children[0]
    assert group.label == "os_macos"
    assert group.stats == StatusCounts(ok=1, failed=1)
    failed_task = next(c for c in group.children if c.stats.failed > 0)
    assert failed_task.label == "os_macos : Install brew casks"
    assert failed_task.path == "roles/os_macos/tasks/main.yml:42"
    assert len(failed_task.children) == 1
    host_node = failed_task.children[0]
    assert host_node.kind == "host"
    assert host_node.label == "caeli"
    assert host_node.stats == StatusCounts(failed=1)


def test_task_tree_real_event_shape():
    """Real ansible.posix.jsonl events DON'T carry ``play`` or ``role``.

    The model must track the current play during iteration and derive
    role from ``task.path`` (regex ``roles/<name>/``). Absolute paths
    must be handled too.
    """
    session = _load_fixture("real_shape")
    root = build_task_tree(session)
    assert len(root.children) == 1
    play = root.children[0]
    assert play.label == "all"  # NOT "(orphan tasks)" or "unknown"
    labels = {c.label for c in play.children}
    # Gathering Facts is top-level → flat under the play (no group).
    assert "Gathering Facts" in labels
    # The role tasks should be nested under an "os_macos" group node.
    role_groups = [c for c in play.children if c.kind == "group" and c.label == "os_macos"]
    assert len(role_groups) == 1
    role_task_labels = {c.label for c in role_groups[0].children}
    assert role_task_labels == {"Update brew", "Install brew casks"}


def _runner_ok(tid: str, name: str, path: str, host: str = "localhost") -> dict:
    return {
        "_event": "v2_runner_on_ok",
        "task": {"id": tid, "name": name, "path": path},
        "hosts": {host: {"changed": False}},
    }


def _nested_include_session() -> dict:
    """A play with two levels of dynamic ``include_tasks``.

    Mirrors the real ``ansible.posix.jsonl`` shape: the include directive
    itself emits a ``v2_runner_on_ok``, and tasks pulled in from the
    included file carry a ``task.path`` rooted in that file. Nesting is
    therefore recoverable purely from the ``task.path`` transitions.
    """
    pb = "/pb/site.yml"
    l1 = "/pb/level1.yml"
    l2 = "/pb/level2.yml"
    events = [
        {"_event": "v2_playbook_on_play_start", "play": {"id": "p1", "name": "nested"}},
        _runner_ok("t1", "Direct task", f"{pb}:6"),
        _runner_ok("t2", "Level 1 include", f"{pb}:9"),
        _runner_ok("t3", "Level 1 task", f"{l1}:2"),
        _runner_ok("t4", "Level 2 include", f"{l1}:5"),
        _runner_ok("t5", "Level 2 task A", f"{l2}:2"),
        _runner_ok("t6", "Level 2 task B", f"{l2}:5"),
        {"_event": "v2_playbook_on_stats"},
    ]
    return {"playbook": "site.yml", "events": events, "session_id": "nested-1"}


def test_task_tree_nests_dynamic_include_tasks_under_directive():
    """Tasks pulled in by include_tasks nest under the directive that ran them."""
    root = build_task_tree(_nested_include_session())
    play = root.children[0]
    top_labels = [c.label for c in play.children]
    assert top_labels == ["Direct task", "Level 1 include"]

    l1_include = play.children[1]
    nested_l1 = [c for c in l1_include.children if c.kind == "task"]
    assert [c.label for c in nested_l1] == ["Level 1 task", "Level 2 include"]
    # The directive itself still carries its own host result.
    assert any(c.kind == "host" for c in l1_include.children)

    l2_include = next(c for c in nested_l1 if c.label == "Level 2 include")
    nested_l2 = [c.label for c in l2_include.children if c.kind == "task"]
    assert nested_l2 == ["Level 2 task A", "Level 2 task B"]


def test_task_tree_rolls_up_nested_include_stats_to_directive():
    """A failure inside an included file is reflected in the directive's stats.

    This is what lets the TUI auto-expand a collapsed include row when one
    of its nested tasks failed, and the failure walkers descend into it.
    """
    pb = "/pb/site.yml"
    inc = "/pb/included.yml"
    events = [
        {"_event": "v2_playbook_on_play_start", "play": {"id": "p1", "name": "nested"}},
        _runner_ok("t1", "Include things", f"{pb}:3"),
        _runner_ok("t2", "Inner ok", f"{inc}:2"),
        {
            "_event": "v2_runner_on_failed",
            "task": {"id": "t3", "name": "Inner boom", "path": f"{inc}:5"},
            "hosts": {"localhost": {"msg": "kaboom"}},
        },
        {"_event": "v2_playbook_on_stats"},
    ]
    session = {"playbook": "site.yml", "events": events, "session_id": "n2"}
    root = build_task_tree(session)
    play = root.children[0]
    directive = play.children[0]
    assert directive.label == "Include things"
    # 2 ok (directive + inner ok) and 1 failed (inner boom) roll up.
    assert directive.stats == StatusCounts(ok=2, failed=1)


def test_task_tree_multi_host_per_host_breakdown():
    session = _load_fixture("multi_host")
    root = build_task_tree(session)
    play = root.children[0]
    assert play.per_host == {
        "web1": StatusCounts(changed=1),
        "web2": StatusCounts(failed=1),
        "web3": StatusCounts(changed=1),
    }


# ── DetailBlock ──────────────────────────────────────────────────────────────


def test_detail_block_loop_failure():
    session = _load_fixture("failed_loop")
    root = build_task_tree(session)
    play = root.children[0]
    group = play.children[0]
    failed_task = next(c for c in group.children if c.stats.failed > 0)
    host_node = failed_task.children[0]
    block = build_detail_block(session, failed_task, host_node)
    assert block.task_name == "os_macos : Install brew casks"
    assert block.host == "caeli"
    assert block.file_line == "roles/os_macos/tasks/main.yml:42"
    assert block.status == "failed"
    assert block.msg == "One or more items failed"
    assert len(block.failed_items) == 2
    assert block.failed_items[0].label == "karabiner-elements"
    assert "404" in (block.failed_items[0].stderr or "")
    assert len(block.ok_items) == 1
    assert block.ok_items[0].label == "amethyst"
    # Per-task detail no longer carries the session-wide stderr.log
    # (that was misleading because it didn't change between tasks).
    assert block.action == "community.general.homebrew_cask"


def test_detail_block_unreachable():
    session = _load_fixture("unreachable")
    root = build_task_tree(session)
    play = root.children[0]
    # New _group_key: no "roles/" in path → task is flat under the play.
    task = play.children[0]
    host_node = task.children[0]
    block = build_detail_block(session, task, host_node)
    assert block.status == "unreachable"
    assert "Connection refused" in (block.msg or "")


def test_detail_block_ok_task_no_failure_items():
    session = _load_fixture("clean_run")
    root = build_task_tree(session)
    play = root.children[0]
    group = play.children[0]
    task = group.children[0]
    host_node = task.children[0]
    block = build_detail_block(session, task, host_node)
    assert block.status == "ok"
    assert block.failed_items == ()
    assert block.ok_items == ()


# ── String task field (bugfix) ────────────────────────────────────────────────


def test_run_summary_string_task_field():
    """build_run_summary must not crash when event['task'] is a string."""
    session = {
        "session_id": "test-0000-0000-string-task",
        "playbook": "test.yml",
        "start_time": "2026-01-01T00:00:00Z",
        "end_time": "2026-01-01T00:00:10Z",
        "duration_seconds": 10.0,
        "version": "1.2",
        "status": "completed",
        "events": [
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-01-01T00:00:00Z"},
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-01-01T00:00:01Z",
                "play": {"id": "p1", "name": "test play"},
            },
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-01-01T00:00:02Z",
                "task": {"id": "t1", "name": "Task 1", "path": "test.yml:1"},
                "play": {"id": "p1"},
            },
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-01-01T00:00:03Z",
                "task": {"id": "t1", "name": "Task 1", "path": "test.yml:1"},
                "play": {"id": "p1"},
                "hosts": {"web1": {"changed": False}},
            },
            # This event has task as a STRING — the bug
            {
                "_event": "v2_runner_on_unreachable",
                "_timestamp": "2026-01-01T00:00:04Z",
                "task": "t2",
                "play": {"id": "p1"},
                "hosts": {"foreman": {"changed": False}},
            },
        ],
        "stderr": [],
        "malformed_lines": 0,
    }
    summary = build_run_summary(session)
    assert summary.session_id == "test-0000-0000-string-task"
    # The string-task event's hosts are still counted (the fix only guards
    # task_id extraction, not host iteration).
    assert summary.host_counts == {
        "web1": StatusCounts(ok=1),
        "foreman": StatusCounts(unreachable=1),
    }


def test_task_tree_string_task_field():
    """build_task_tree must not crash when event['task'] is a string."""
    session = {
        "session_id": "test-0000-0000-string-task",
        "playbook": "test.yml",
        "start_time": "2026-01-01T00:00:00Z",
        "end_time": "2026-01-01T00:00:10Z",
        "duration_seconds": 10.0,
        "version": "1.2",
        "status": "completed",
        "events": [
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-01-01T00:00:00Z"},
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-01-01T00:00:01Z",
                "play": {"id": "p1", "name": "test play"},
            },
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-01-01T00:00:02Z",
                "task": {"id": "t1", "name": "Task 1", "path": "test.yml:1"},
                "play": {"id": "p1"},
            },
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-01-01T00:00:03Z",
                "task": {"id": "t1", "name": "Task 1", "path": "test.yml:1"},
                "play": {"id": "p1"},
                "hosts": {"web1": {"changed": False}},
            },
            # This event has task as a STRING — the bug
            {
                "_event": "v2_runner_on_unreachable",
                "_timestamp": "2026-01-01T00:00:04Z",
                "task": "t2",
                "play": {"id": "p1"},
                "hosts": {"foreman": {"changed": False}},
            },
        ],
        "stderr": [],
        "malformed_lines": 0,
    }
    root = build_task_tree(session)
    assert root.kind == "run"
    assert len(root.children) == 1
    play = root.children[0]
    assert play.label == "test play"
    task_labels = [c.label for c in play.children]
    assert task_labels == ["Task 1"]
    assert play.stats == StatusCounts(ok=1)
