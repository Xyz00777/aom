"""Per-host overview renders as a column-aligned table rather than a
flat row of count cells. Matches nom's `Done / Building / Waiting`
header style: numbers in fixed-width columns under labelled headers.

Columns: ``host | ok | changed | failed | current task``.
``unreachable`` is added as an extra column only when at least one host
has an unreachable count — keeps the common multi-host case tight.
"""

from __future__ import annotations

from ansible_aom.compact.format import _strip_sgr, format_host_rows
from ansible_aom.core.models import (
    HostRunState,
    PlayDefinition,
    PlayRunState,
    RunState,
    Status,
    TaskRunState,
)
from ansible_aom.core.tree import TreeProjection


def _state(hosts: list[str]) -> RunState:
    state = RunState(playbook="site.yml")
    state.definitions = [
        PlayDefinition(
            id="1",
            name="deploy",
            hosts="all",
            resolved_hosts=hosts,
            tasks=[],
        )
    ]
    return state


def _add_results(
    state: RunState,
    hostname: str,
    ok: int = 0,
    changed: int = 0,
    failed: int = 0,
    unreachable: int = 0,
) -> None:
    """Synthesise OK/CHANGED/FAILED/UNREACHABLE results for a host."""
    play = state.plays.setdefault(
        "p1",
        PlayRunState(play_id="p1", name="deploy", status=Status.RUNNING),
    )
    base = len(play.tasks)
    for status, count in (
        (Status.OK, ok),
        (Status.CHANGED, changed),
        (Status.FAILED, failed),
        (Status.UNREACHABLE, unreachable),
    ):
        for i in range(count):
            tid = f"{hostname}-{status.name}-{base + i}"
            task = TaskRunState(task_id=tid, name=f"t-{tid}", status=Status.OK)
            task.hosts[hostname] = HostRunState(hostname=hostname, status=status)
            play.tasks[tid] = task


def _rows(rows: list[str]) -> list[list[str]]:
    """Split rows on whitespace runs after stripping SGR — coarse but
    enough to assert column position."""
    return [_strip_sgr(r).split() for r in rows]


def test_header_row_present() -> None:
    state = _state(["web1"])
    _add_results(state, "web1", ok=2)
    p = TreeProjection.from_run_state(state)
    rows = format_host_rows(p, width=120, ascii_mode=False, colorize=False)
    # First row carries the column headers.
    header = _strip_sgr(rows[0])
    for label in ("host", "ok", "changed", "failed"):
        assert label in header, header


def test_unreachable_column_hidden_when_no_unreachable() -> None:
    state = _state(["web1", "web2"])
    _add_results(state, "web1", ok=3, changed=1)
    _add_results(state, "web2", ok=5)
    p = TreeProjection.from_run_state(state)
    rows = format_host_rows(p, width=120, ascii_mode=False, colorize=False)
    header = _strip_sgr(rows[0])
    assert "unreachable" not in header, header


def test_unreachable_column_visible_when_any_host_has_unreachable() -> None:
    state = _state(["web1", "web2"])
    _add_results(state, "web1", ok=3)
    _add_results(state, "web2", ok=2, unreachable=1)
    p = TreeProjection.from_run_state(state)
    rows = format_host_rows(p, width=120, ascii_mode=False, colorize=False)
    header = _strip_sgr(rows[0])
    assert "unreachable" in header, header


def test_columns_align_across_rows() -> None:
    state = _state(["web1", "longhostname-2"])
    _add_results(state, "web1", ok=3, changed=1)
    _add_results(state, "longhostname-2", ok=23, failed=1)
    p = TreeProjection.from_run_state(state)
    rows = format_host_rows(p, width=120, ascii_mode=False, colorize=False)

    # The "ok" column should land at the same character index across
    # the header row and every data row.
    header = _strip_sgr(rows[0])
    ok_col = header.index("ok")
    for data in rows[1:]:
        plain = _strip_sgr(data)
        # The digit at ok_col (or near it, within the right-aligned
        # column) belongs to the OK count cell. Allow the digit to land
        # at or just before ok_col + 2 since numbers right-align.
        # Just assert SOME digit is in the expected slice.
        window = plain[max(0, ok_col - 2) : ok_col + 3]
        assert any(c.isdigit() for c in window), (header, plain, window)


def test_idle_host_shows_idle_marker() -> None:
    state = _state(["web1"])
    _add_results(state, "web1", ok=2)
    p = TreeProjection.from_run_state(state)
    rows = format_host_rows(p, width=120, ascii_mode=False, colorize=False)
    plain = _strip_sgr(rows[1])
    assert "idle" in plain.lower(), plain


def test_running_host_shows_current_task() -> None:
    state = _state(["web1"])
    play = PlayRunState(play_id="p1", name="deploy", status=Status.RUNNING)
    task = TaskRunState(task_id="t-cur", name="Install nginx", status=Status.RUNNING)
    task.hosts["web1"] = HostRunState(hostname="web1", status=Status.RUNNING)
    play.tasks["t-cur"] = task
    state.plays["p1"] = play

    p = TreeProjection.from_run_state(state)
    rows = format_host_rows(p, width=120, ascii_mode=False, colorize=False)
    plain = _strip_sgr(rows[1])
    assert "Install nginx" in plain, plain
