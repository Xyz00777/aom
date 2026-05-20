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


def _load_fixture(name: str) -> dict:
    """Helper: load a session fixture as load_session would return it."""
    src = Path(__file__).parent.parent / "fixtures" / "sessions" / name
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
        _load_fixture("clean_run"),       # 2026-05-19 18:02
        _load_fixture("failed_loop"),     # 2026-05-20 11:24
        _load_fixture("multi_host"),      # 2026-05-19 15:00
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
    assert any("curl" in line for line in block.session_stderr_tail)


def test_detail_block_unreachable():
    session = _load_fixture("unreachable")
    root = build_task_tree(session)
    play = root.children[0]
    group = play.children[0]
    task = group.children[0]
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
