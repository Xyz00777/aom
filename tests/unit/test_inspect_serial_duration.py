"""Serial batches reuse task IDs: sum their execution windows, excluding gaps.

Previously a new start was paired with the previous batch's result, producing
a negative duration until another result arrived, then losing earlier batches.
"""

import json
from datetime import timedelta
from pathlib import Path

import pytest

from ansible_aom.core.inspect_model import SessionIndexAccumulator, build_task_tree
from ansible_aom.session.index import build_index, load_structure


def _event(kind: str, second: int | None, *hosts: str) -> dict:
    event = {
        "_event": kind,
        "task": {"id": "deploy", "name": "Deploy"},
        "hosts": {host: {"changed": False} for host in hosts},
    }
    if second is not None:
        event["_timestamp"] = f"2026-07-01T10:{second // 60:02}:{second % 60:02}Z"
    return event


@pytest.mark.parametrize("second_result, expected", [(False, 2), (True, 5)])
def test_serial_batches_sum_execution_windows_in_memory_and_index(
    tmp_path: Path, second_result: bool, expected: int
) -> None:
    events = [
        _event("v2_playbook_on_task_start", 0),
        _event("v2_runner_on_ok", 1, "web1"),
        _event("v2_runner_on_failed", 2, "web2"),
        _event("v2_playbook_on_task_start", 60),
    ]
    if second_result:
        events.extend(
            [
                _event("v2_runner_on_ok", 61, "web3"),
                _event("v2_runner_on_unreachable", 63, "web4"),
                _event("v2_runner_on_ok", 90),  # No host outcome: no elapsed contribution.
            ]
        )

    tree = build_task_tree({"playbook": "site.yml", "events": events})
    assert tree.children[0].children[0].duration == timedelta(seconds=expected)

    (tmp_path / "events.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events))
    assert build_index(tmp_path)
    index = load_structure(tmp_path)
    assert index is not None
    assert index.tasks[0].duration == timedelta(seconds=expected)


def test_duration_snapshots_do_not_double_count_completed_batches() -> None:
    acc = SessionIndexAccumulator()
    for event in [
        _event("v2_playbook_on_task_start", 0),
        _event("v2_runner_on_ok", 2, "web1"),
        _event("v2_playbook_on_task_start", 60),
    ]:
        acc.feed(event)
    assert acc.finish().tasks[0].duration == timedelta(seconds=2)
    assert acc.finish().tasks[0].duration == timedelta(seconds=2)
    acc.feed(_event("v2_runner_on_skipped", 63, "web2"))
    assert acc.finish().tasks[0].duration == timedelta(seconds=5)
    acc.feed(_event("v2_playbook_on_task_start", 120))
    acc.feed(_event("v2_runner_on_ok", 124, "web3"))
    assert acc.finish().tasks[0].duration == timedelta(seconds=9)


def test_untimed_later_occurrence_keeps_previously_measured_duration() -> None:
    events = [
        _event("v2_playbook_on_task_start", 0),
        _event("v2_runner_on_ok", 2, "web1"),
        _event("v2_playbook_on_task_start", None),
        _event("v2_runner_on_ok", 63, "web2"),
    ]
    tree = build_task_tree({"events": events})
    assert tree.children[0].children[0].duration == timedelta(seconds=2)
    events.extend(
        [
            _event("v2_playbook_on_task_start", 120),
            _event("v2_runner_on_ok", 124, "web3"),
        ]
    )
    tree = build_task_tree({"events": events})
    assert tree.children[0].children[0].duration == timedelta(seconds=6)


@pytest.mark.parametrize("first_results, expected", [([0], 0), ([2, 1], 2)])
def test_occurrence_uses_latest_timestamp_and_retains_zero_duration(
    first_results: list[int], expected: int
) -> None:
    events = [_event("v2_playbook_on_task_start", 0)]
    events.extend(
        _event("v2_runner_on_ok", second, f"web{i}") for i, second in enumerate(first_results)
    )
    events.append(_event("v2_playbook_on_task_start", 60))
    tree = build_task_tree({"events": events})
    assert tree.children[0].children[0].duration == timedelta(seconds=expected)


def test_free_strategy_without_task_start_remains_untimed() -> None:
    events = [
        _event("v2_runner_on_start", 0),
        _event("v2_runner_on_ok", 2, "web1"),
        _event("v2_runner_on_start", 60),
        _event("v2_runner_on_ok", 63, "web2"),
    ]
    tree = build_task_tree({"events": events})
    assert tree.children[0].children[0].duration is None


def test_results_before_occurrence_start_cannot_subtract_completed_duration() -> None:
    acc = SessionIndexAccumulator()
    for event in [
        _event("v2_playbook_on_task_start", 0),
        _event("v2_runner_on_ok", 2, "web1"),
        _event("v2_playbook_on_task_start", 60),
        _event("v2_runner_on_ok", 59, "web2"),
    ]:
        acc.feed(event)
    assert acc.finish().tasks[0].duration == timedelta(seconds=2)
    acc.feed(_event("v2_playbook_on_task_start", 120))
    acc.feed(_event("v2_runner_on_ok", 124, "web3"))
    assert acc.finish().tasks[0].duration == timedelta(seconds=6)
