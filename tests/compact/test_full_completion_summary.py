"""Per-task summary fires on FULL play completion, not on the next task.

Under a free/host-pinned strategy the fastest host starts the next task
while slower hosts are still finishing the current one. The old trigger
(summary on the next task's first announcement) snapshotted the count at
that instant and undercounted — a 3-host task read "(1 ok)" then two
hosts straggled in. The summary now waits until every target host has a
terminal result, accepting that the line then lands out-of-order (below
the later task's header/output). At run end (stats or a cancel with no
stats) any still-incomplete task is force-flushed with whatever count it
reached.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from ansible_aom.compact.renderer import CompactRenderer
from ansible_aom.core.models import PlayDefinition


def _play_def(hosts: list[str]) -> PlayDefinition:
    return PlayDefinition(id="p1", name="P", hosts="all", resolved_hosts=list(hosts), tasks=[])


def _renderer(hosts: list[str]) -> CompactRenderer:
    r = CompactRenderer(is_tty=False)
    r.start("test.yml", [])
    r._colorize = False
    r._display = MagicMock()
    r.set_definitions([_play_def(hosts)])
    r.update_state({"_event": "v2_playbook_on_play_start", "play": {"id": "p1", "name": "P"}})
    return r


def _logged(r: CompactRenderer) -> list[str]:
    return [c.args[0] for c in r._display.print_log.call_args_list]


def _start(task_id: str, name: str, host: str, ts: str) -> dict:
    return {
        "_event": "v2_runner_on_start",
        "_timestamp": ts,
        "task": {"id": task_id, "name": name},
        "play": {"id": "p1"},
        "host": host,
    }


def _ok(task_id: str, name: str, host: str, ts: str) -> dict:
    return {
        "_event": "v2_runner_on_ok",
        "_timestamp": ts,
        "task": {"id": task_id, "name": name},
        "play": {"id": "p1"},
        "hosts": {host: {"changed": False}},
    }


def _summary_lines(r: CompactRenderer, name: str) -> list[str]:
    return [line for line in _logged(r) if name in line and " — " in line]


def test_free_strategy_summary_counts_all_targets_not_fast_cohort() -> None:
    r = _renderer(["a", "b", "c"])
    # All three start "First".
    r.update_state(_start("t1", "First", "a", "2026-05-11T10:00:00Z"))
    r.update_state(_start("t1", "First", "b", "2026-05-11T10:00:00Z"))
    r.update_state(_start("t1", "First", "c", "2026-05-11T10:00:00Z"))
    # Fast host a finishes and moves on to "Second" — announces its header.
    r.update_state(_ok("t1", "First", "a", "2026-05-11T10:00:01Z"))
    r.update_state(_start("t2", "Second", "a", "2026-05-11T10:00:01Z"))
    # First's summary must NOT have been emitted yet (b, c unfinished).
    assert not _summary_lines(r, "First"), _logged(r)
    # Stragglers land.
    r.update_state(_ok("t1", "First", "b", "2026-05-11T10:00:02Z"))
    r.update_state(_ok("t1", "First", "c", "2026-05-11T10:00:03Z"))
    # Now First is complete → summary emitted with the FULL count.
    lines = _summary_lines(r, "First")
    assert len(lines) == 1, _logged(r)
    assert "(3 ok)" in lines[0]


def test_free_strategy_summary_lands_after_later_task_header() -> None:
    r = _renderer(["a", "b"])
    r.update_state(_start("t1", "First", "a", "2026-05-11T10:00:00Z"))
    r.update_state(_start("t1", "First", "b", "2026-05-11T10:00:00Z"))
    r.update_state(_ok("t1", "First", "a", "2026-05-11T10:00:01Z"))
    r.update_state(_start("t2", "Second", "a", "2026-05-11T10:00:01Z"))
    r.update_state(_ok("t1", "First", "b", "2026-05-11T10:00:02Z"))  # completes First
    logged = _logged(r)
    header_idx = next(i for i, ln in enumerate(logged) if "TASK [Second]" in ln)
    summary_idx = next(i for i, ln in enumerate(logged) if "First" in ln and " — " in ln)
    assert summary_idx > header_idx, logged


def test_cancel_flushes_incomplete_task_with_partial_count() -> None:
    """A task that never completes on all hosts (run cancelled) still gets
    a summary at handle_completion, counting the hosts that did run it —
    and its duration is measured to the last host result, NOT to the later
    cancel moment."""
    r = _renderer(["a", "b", "c"])
    r.update_state(_start("t1", "First", "a", "2026-05-11T10:00:00Z"))
    r.update_state(_start("t1", "First", "b", "2026-05-11T10:00:00Z"))
    r.update_state(_ok("t1", "First", "a", "2026-05-11T10:00:01Z"))
    r.update_state(_ok("t1", "First", "b", "2026-05-11T10:00:02Z"))
    # a races ahead into a later task; c never runs First; then cancel.
    r.update_state(_start("t2", "Second", "a", "2026-05-11T10:00:05Z"))
    assert not _summary_lines(r, "First")  # not complete yet
    r.handle_completion(130, "crashed")
    lines = _summary_lines(r, "First")
    assert len(lines) == 1, _logged(r)
    assert "(2 ok)" in lines[0]
    # Duration = start (10:00:00) → last host result (10:00:02) = 2.0s,
    # not → the t2 start / cancel moment (10:00:05).
    assert "2.0s" in lines[0], lines[0]
    assert "5.0s" not in lines[0], lines[0]


def test_purely_inflight_task_gets_no_summary_at_cancel() -> None:
    """A task with zero terminal results at cancel produces no summary —
    a bare ``— 0.0s`` line would be noise, and the tree already shows it."""
    r = _renderer(["a", "b"])
    r.update_state(_start("t1", "First", "a", "2026-05-11T10:00:00Z"))
    r.update_state(_start("t1", "First", "b", "2026-05-11T10:00:00Z"))
    # Neither host reports a result — still in-flight when cancelled.
    r.handle_completion(130, "crashed")
    assert not _summary_lines(r, "First"), _logged(r)


def test_completed_task_summary_emitted_once() -> None:
    """A task summarised mid-run is not re-emitted at cancel/stats."""
    r = _renderer(["a", "b"])
    r.update_state(_start("t1", "First", "a", "2026-05-11T10:00:00Z"))
    r.update_state(_start("t1", "First", "b", "2026-05-11T10:00:00Z"))
    r.update_state(_ok("t1", "First", "a", "2026-05-11T10:00:01Z"))
    r.update_state(_ok("t1", "First", "b", "2026-05-11T10:00:02Z"))
    r.update_state(_start("t2", "Second", "a", "2026-05-11T10:00:03Z"))
    # First already complete → summarised at the t2 announce.
    assert len(_summary_lines(r, "First")) == 1
    r.handle_completion(0, "completed")
    assert len(_summary_lines(r, "First")) == 1, _logged(r)
