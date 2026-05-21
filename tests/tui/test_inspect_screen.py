"""Pilot tests for the Inspect TUI screen — three-pane browser."""

import shutil
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent.parent / "fixtures" / "sessions"

_ALIASES = {
    "clean_run": "019e4000-0000-7000-8000-000000000001",
    "failed_loop": "019e4520-fa64-7000-a627-000000000002",
    "multi_host": "019e4100-0000-7000-8000-000000000003",
    "unreachable": "019e4200-0000-7000-8000-000000000004",
}


@pytest.fixture
def state_dir(tmp_path: Path) -> Path:
    state = tmp_path / "sessions"
    state.mkdir()
    for name, sid in _ALIASES.items():
        shutil.copytree(FIXTURES / sid, state / sid)
    return state


@pytest.mark.asyncio
async def test_runs_pane_lists_newest_first(state_dir: Path):
    from ansible_aom.tui.screens.inspect import InspectApp

    app = InspectApp(state_dir=state_dir)
    async with app.run_test() as pilot:
        await pilot.pause()
        listview = app.query_one("#runs-list")
        # 4 fixture sessions; expect 4 rows.
        assert len(listview.children) == 4
        # Newest first: failed_loop (2026-05-20 11:24) pre-selected.
        assert app.selected_session_id == _ALIASES["failed_loop"]


@pytest.mark.asyncio
async def test_runs_pane_failed_filter(state_dir: Path):
    from ansible_aom.tui.screens.inspect import InspectApp

    app = InspectApp(state_dir=state_dir)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("f")
        await pilot.pause()
        listview = app.query_one("#runs-list")
        # clean_run is the only "completed" session; the other 3 are "failed".
        assert len(listview.children) == 3


@pytest.mark.asyncio
async def test_tab_cycles_focus_between_panes(state_dir: Path):
    from ansible_aom.tui.screens.inspect import InspectApp

    app = InspectApp(state_dir=state_dir, initial_session_id=_ALIASES["failed_loop"])
    async with app.run_test() as pilot:
        await pilot.pause()
        # Start: Tab should move focus toward the Tasks pane.
        await pilot.press("tab")
        await pilot.pause()
        focused = app.focused
        # The focused widget should be (or live inside) #tasks-tree.
        node = focused
        ids = []
        while node is not None:
            ids.append(getattr(node, "id", None))
            node = getattr(node, "parent", None)
        assert "tasks-tree" in ids, f"Expected focus on tasks-tree, got chain {ids!r}"


@pytest.mark.asyncio
async def test_run_row_renders_local_timezone(state_dir: Path, monkeypatch):
    """Run-row date string respects the local timezone, not UTC.

    The fixture's ``start_time`` is recorded as UTC ``11:24`` in the
    ``failed_loop`` session. With a Europe/Berlin (+02:00) timezone the
    display should read ``13:24``. We force a known TZ and check.
    """
    monkeypatch.setenv("TZ", "Europe/Berlin")
    # ``time.tzset`` is the cross-fixture way to pick up the new TZ env
    # var on POSIX systems; without it the cached zone stays UTC.
    import time as _time

    if hasattr(_time, "tzset"):
        _time.tzset()

    from ansible_aom.tui.screens.inspect import InspectApp, _render_run_lines, _RunRow

    app = InspectApp(state_dir=state_dir)
    async with app.run_test() as pilot:
        await pilot.pause()
        listview = app.query_one("#runs-list")
        row = listview.children[0]
        assert isinstance(row, _RunRow)
        line1, _line2, _line3 = _render_run_lines(row.summary)
        # 2026-05-20T11:24:09Z in CEST → 2026-05-20 13:24
        assert "13:24" in line1
        assert "11:24" not in line1


@pytest.mark.asyncio
async def test_run_row_renders_multi_line_content(state_dir: Path):
    """Each Runs-pane entry should render 3 distinct lines of info."""
    from ansible_aom.tui.screens.inspect import InspectApp, _RunRow

    app = InspectApp(state_dir=state_dir)
    async with app.run_test() as pilot:
        await pilot.pause()
        listview = app.query_one("#runs-list")
        first = listview.children[0]
        assert isinstance(first, _RunRow)
        labels = list(first.query("Label"))
        # 3 label widgets per row (line1, line2, line3).
        assert len(labels) == 3


@pytest.mark.asyncio
async def test_tasks_pane_shows_tree_for_selected_run(state_dir: Path):
    from ansible_aom.tui.screens.inspect import InspectApp

    app = InspectApp(state_dir=state_dir, initial_session_id=_ALIASES["failed_loop"])
    async with app.run_test() as pilot:
        await pilot.pause()
        tree = app.query_one("#tasks-tree")
        # Root has at least one play node ("all").
        labels = [str(n.label) for n in tree.root.children]
        assert any("all" in lbl for lbl in labels)


@pytest.mark.asyncio
async def test_detail_pane_shows_failure_msg(state_dir: Path):
    from ansible_aom.tui.screens.inspect import InspectApp

    app = InspectApp(state_dir=state_dir, initial_session_id=_ALIASES["failed_loop"])
    async with app.run_test() as pilot:
        await pilot.pause()
        # Auto-jump to first failure means the failed-loop task detail is shown.
        body = app._detail_text
        assert "Install brew casks" in body
        assert "One or more items failed" in body
        assert "karabiner-elements" in body


@pytest.mark.asyncio
async def test_r_copies_rerun_command(state_dir: Path, monkeypatch):
    copied: list[str] = []
    monkeypatch.setattr(
        "ansible_aom.tui.screens.inspect._copy_to_clipboard",
        lambda text: copied.append(text),
    )
    from ansible_aom.tui.screens.inspect import InspectApp

    app = InspectApp(state_dir=state_dir, initial_session_id=_ALIASES["failed_loop"])
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("R")
        await pilot.pause()
    assert copied, "Expected R to copy a rerun command"
    assert "aom rerun" in copied[0]
    assert "--limit" in copied[0]
    assert "Install brew casks" in copied[0]


@pytest.mark.asyncio
async def test_n_and_shift_n_cycle_through_failures(state_dir: Path):
    """`n` and `N` walk forward / backward through the run's failure list.

    The failed_loop fixture has exactly 1 failure; we add multi_host
    (1 failure on web2) and unreachable (1 unreachable on web2) into the
    state dir already, but the tree is per-session — so we exercise the
    wrap-around: `n` from the only failure should land on the same one
    again (after a wrap), with a toast.
    """
    from ansible_aom.tui.screens.inspect import InspectApp

    app = InspectApp(state_dir=state_dir, initial_session_id=_ALIASES["failed_loop"])
    async with app.run_test() as pilot:
        await pilot.pause()
        initial_task_id = app._focused_task.task_id  # type: ignore[union-attr]
        await pilot.press("n")
        await pilot.pause()
        # Only one failure in this run → wraps back to itself.
        assert app._focused_task is not None
        assert app._focused_task.task_id == initial_task_id
        await pilot.press("N")
        await pilot.pause()
        assert app._focused_task is not None
        assert app._focused_task.task_id == initial_task_id


@pytest.mark.asyncio
async def test_highlighting_successful_task_updates_detail(state_dir: Path):
    """Navigating to a non-failed task must still populate the Detail pane.

    Confirms users can inspect OK / changed / skipped task logs too, not
    just failures.
    """
    from ansible_aom.core.inspect_model import TaskTreeNode, build_task_tree
    from ansible_aom.session.store import load_session
    from ansible_aom.tui.screens.inspect import InspectApp

    app = InspectApp(state_dir=state_dir, initial_session_id=_ALIASES["failed_loop"])
    async with app.run_test() as pilot:
        await pilot.pause()
        # Find the OK task in the tree (the "os_macos : update brew" task).
        session = load_session(_ALIASES["failed_loop"], state_dir)
        assert session is not None
        model = build_task_tree(session)

        def find_first_ok_task(node: TaskTreeNode) -> TaskTreeNode | None:
            if node.kind == "task" and node.stats.ok > 0 and node.stats.failed == 0:
                return node
            for c in node.children:
                hit = find_first_ok_task(c)
                if hit is not None:
                    return hit
            return None

        ok_task = find_first_ok_task(model)
        assert ok_task is not None, "Fixture should contain at least one OK task"

        # Simulate highlighting the OK task by setting focused_task/host
        # directly and triggering the detail update (Pilot can't easily
        # arrow-navigate Tree without exact node coordinates).
        app._focused_task = ok_task
        app._focused_host = ok_task.children[0] if ok_task.children else None
        app._update_detail()
        body = app._detail_text
        assert ok_task.label in body
        # Status is rendered with Rich markup, so the literal status
        # name still appears in the body string.
        assert "ok" in body or "changed" in body
        assert "STATUS" in body


@pytest.mark.asyncio
async def test_enter_on_run_row_focuses_tasks_pane(state_dir: Path):
    """Pressing Enter on a Runs row drills into the Tasks pane."""
    from ansible_aom.tui.screens.inspect import InspectApp

    app = InspectApp(state_dir=state_dir, initial_session_id=_ALIASES["failed_loop"])
    async with app.run_test() as pilot:
        await pilot.pause()
        # Focus the runs ListView first so Enter is routed to it.
        app.focus_runs()
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        # Focus should now be inside the Tasks pane.
        node = app.focused
        ids: list[str | None] = []
        while node is not None:
            ids.append(getattr(node, "id", None))
            node = getattr(node, "parent", None)
        assert "tasks-tree" in ids, f"Expected focus to land in tasks-tree, got {ids!r}"


@pytest.mark.asyncio
async def test_enter_on_task_focuses_detail_pane(state_dir: Path):
    """Pressing Enter on a Task tree node drills into the Detail pane."""
    from ansible_aom.tui.screens.inspect import InspectApp

    app = InspectApp(state_dir=state_dir, initial_session_id=_ALIASES["failed_loop"])
    async with app.run_test() as pilot:
        await pilot.pause()
        app.focus_tasks()
        await pilot.pause()
        # The tree auto-jumped its cursor to the first failure; pressing
        # Enter triggers Tree.action_select_cursor, which fires our
        # on_tree_node_selected → focus_detail().
        await pilot.press("enter")
        await pilot.pause()
        node = app.focused
        ids: list[str | None] = []
        while node is not None:
            ids.append(getattr(node, "id", None))
            node = getattr(node, "parent", None)
        assert "detail-body" in ids or "detail-pane" in ids, (
            f"Expected focus to land in detail pane, got {ids!r}"
        )


@pytest.mark.asyncio
async def test_e_expands_all_and_c_collapses_all(state_dir: Path):
    """`e` expands every node in the tree; `c` collapses everything.

    Use the multi_host fixture (3 hosts under one task) so we can
    observe the task→host level toggle.
    """
    from ansible_aom.tui.screens.inspect import InspectApp, _NavTree

    app = InspectApp(state_dir=state_dir, initial_session_id=_ALIASES["multi_host"])
    async with app.run_test() as pilot:
        await pilot.pause()
        tree = app.query_one("#tasks-tree")
        assert isinstance(tree, _NavTree)
        tree.focus()
        await pilot.pause()

        await pilot.press("e")
        await pilot.pause()

        def walk(n):
            yield n
            for c in n.children:
                yield from walk(c)

        expandables = [n for n in walk(tree.root) if n is not tree.root and n.allow_expand]
        assert expandables, "fixture should have at least one expandable node"
        assert all(n.is_expanded for n in expandables), (
            "After `e`, every expandable node should be expanded"
        )

        await pilot.press("c")
        await pilot.pause()
        assert all(not n.is_expanded for n in expandables), (
            "After `c`, every expandable node should be collapsed"
        )


@pytest.mark.asyncio
async def test_left_does_not_steal_focus_to_detail_pane(state_dir: Path):
    """Pressing Left in the Tasks pane must not move focus to the Detail pane.

    Regression: ``_NavTree.action_shallower`` used to call
    ``select_node(parent)`` which posts ``NodeSelected``. The App's
    Enter-handler interprets that message as "drill into Detail" and
    moved focus there — so collapsing a role / walking up the tree
    silently jumped focus to the Detail pane. ``move_cursor`` doesn't
    post the message.
    """
    from ansible_aom.tui.screens.inspect import InspectApp, _NavTree

    app = InspectApp(state_dir=state_dir, initial_session_id=_ALIASES["failed_loop"])
    async with app.run_test() as pilot:
        await pilot.pause()
        tree = app.query_one("#tasks-tree")
        assert isinstance(tree, _NavTree)
        tree.focus()
        await pilot.pause()
        # Position the cursor on a host node under the *failing* task —
        # that path is auto-expanded so the host node is visible (and
        # therefore has a valid line index for move_cursor).
        host_node = None
        play = tree.root.children[0]
        for group in play.children:
            for task in group.children:
                if getattr(task.data, "stats", None) and task.data.stats.failed > 0:
                    if task.children:
                        host_node = task.children[0]
                        break
            if host_node:
                break
        assert host_node is not None, "failed_loop fixture should have a failing host"
        tree.move_cursor(host_node)
        await pilot.pause()
        assert tree.cursor_node is host_node, "cursor failed to land on host node"

        # Two Lefts: host → parent task; then task collapses (if expanded)
        # or → parent group. Either way, focus must stay in tasks-tree
        # since we're still well below the top-level play.
        for _ in range(2):
            await pilot.press("left")
            await pilot.pause()
            ids: list[str | None] = []
            node = app.focused
            while node is not None:
                ids.append(getattr(node, "id", None))
                node = getattr(node, "parent", None)
            assert "tasks-tree" in ids, f"Left arrow stole focus out of Tasks pane; got {ids!r}"


@pytest.mark.asyncio
async def test_left_arrow_collapses_or_walks_up_tree(state_dir: Path):
    """Right expands a collapsed node; Left collapses an expanded node."""
    from ansible_aom.tui.screens.inspect import InspectApp, _NavTree

    app = InspectApp(state_dir=state_dir, initial_session_id=_ALIASES["failed_loop"])
    async with app.run_test() as pilot:
        await pilot.pause()
        tree = app.query_one("#tasks-tree")
        assert isinstance(tree, _NavTree)
        tree.focus()
        await pilot.pause()
        # Move cursor to the first top-level node (a play). Direct
        # cursor_line assignment avoids ``select_node()`` which can
        # interact with auto_expand even when it's disabled.
        if tree.root.children:
            tree.cursor_line = 0
        await pilot.pause()
        first_top = tree.cursor_node
        assert first_top is not None and first_top.allow_expand
        # The play auto-expanded on load; Left should collapse it.
        assert first_top.is_expanded
        await pilot.press("left")
        await pilot.pause()
        assert not first_top.is_expanded, "Left should collapse the expanded node"
        # Right should expand it again.
        await pilot.press("right")
        await pilot.pause()
        assert first_top.is_expanded, "Right should re-expand the collapsed node"


@pytest.mark.asyncio
async def test_d_opens_confirm_then_y_deletes(state_dir: Path):
    """`d` opens a confirm modal; pressing `y` actually deletes the session dir."""
    from ansible_aom.tui.screens.inspect import InspectApp

    app = InspectApp(state_dir=state_dir, initial_session_id=_ALIASES["failed_loop"])
    target_dir = state_dir / _ALIASES["failed_loop"]
    assert target_dir.exists()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.focus_runs()
        await pilot.pause()
        await pilot.press("d")
        await pilot.pause()
        # Confirm modal is up; press y to confirm.
        await pilot.press("y")
        await pilot.pause()
    assert not target_dir.exists(), "Session directory should have been deleted"


@pytest.mark.asyncio
async def test_dd_double_tap_deletes(state_dir: Path):
    """Two consecutive `d` presses (open + confirm) also delete the session."""
    from ansible_aom.tui.screens.inspect import InspectApp

    app = InspectApp(state_dir=state_dir, initial_session_id=_ALIASES["failed_loop"])
    target_dir = state_dir / _ALIASES["failed_loop"]
    assert target_dir.exists()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.focus_runs()
        await pilot.pause()
        await pilot.press("d")
        await pilot.pause()
        await pilot.press("d")  # confirm on the modal
        await pilot.pause()
        await pilot.pause()
    assert not target_dir.exists(), "Session should have been deleted by `dd`"


@pytest.mark.asyncio
async def test_delete_auto_selects_next_session(state_dir: Path):
    """After deleting a session, the next entry in the list takes focus.

    Without auto-advance, the user is left looking at an empty Tasks
    pane after every delete — they'd have to manually re-select.
    """
    from ansible_aom.tui.screens.inspect import InspectApp

    app = InspectApp(state_dir=state_dir, initial_session_id=_ALIASES["failed_loop"])
    async with app.run_test() as pilot:
        await pilot.pause()
        listview = app.query_one("#runs-list")
        before = len(listview.children)
        # Note the second session_id (newest-first ordering puts it at index 1).
        second_sid = listview.children[1].session_id  # type: ignore[attr-defined]
        app.focus_runs()
        await pilot.pause()
        await pilot.press("d")
        await pilot.pause()
        await pilot.press("y")
        # The dismiss callback runs after the modal closes; an extra
        # pause cycle gives it room to land.
        await pilot.pause()
        await pilot.pause()
        after = len(listview.children)
        assert after == before - 1
        # The session that was at index 1 is now at index 0 and selected.
        assert app.selected_session_id == second_sid
        # Tasks tree has been refreshed for the new selection (not empty
        # unless that session genuinely has no tasks).
        # (The clean_run fixture has 2 tasks, so the tree should be non-empty.)
        tree = app.query_one("#tasks-tree")
        assert len(tree.root.children) > 0


@pytest.mark.asyncio
async def test_d_cancel_keeps_session(state_dir: Path):
    """`d` then Esc cancels — session stays on disk."""
    from ansible_aom.tui.screens.inspect import InspectApp

    app = InspectApp(state_dir=state_dir, initial_session_id=_ALIASES["failed_loop"])
    target_dir = state_dir / _ALIASES["failed_loop"]
    async with app.run_test() as pilot:
        await pilot.pause()
        app.focus_runs()
        await pilot.pause()
        await pilot.press("d")
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
    assert target_dir.exists(), "Session should still exist after canceling"


@pytest.mark.asyncio
async def test_question_mark_opens_help(state_dir: Path):
    """`?` opens the help overlay."""
    from ansible_aom.tui.screens.inspect import InspectApp, _HelpScreen

    app = InspectApp(state_dir=state_dir)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("question_mark")
        await pilot.pause()
        # The active screen should now be a _HelpScreen.
        assert isinstance(app.screen, _HelpScreen)


@pytest.mark.asyncio
async def test_r_reloads_runs_from_disk(state_dir: Path):
    """`r` re-reads the state dir; deleting a session out-of-band is reflected."""
    import shutil as _shutil

    from ansible_aom.tui.screens.inspect import InspectApp

    app = InspectApp(state_dir=state_dir, initial_session_id=_ALIASES["failed_loop"])
    async with app.run_test() as pilot:
        await pilot.pause()
        listview = app.query_one("#runs-list")
        before = len(listview.children)
        # Delete one session directly from disk.
        _shutil.rmtree(state_dir / _ALIASES["multi_host"])
        await pilot.press("r")
        await pilot.pause()
        after = len(listview.children)
        assert after == before - 1, (
            f"Expected reload to drop one row; before={before} after={after}"
        )


@pytest.mark.asyncio
async def test_focused_pane_gets_visual_class(state_dir: Path):
    """The focused pane carries the ``--focused-pane`` CSS class."""
    from ansible_aom.tui.screens.inspect import InspectApp

    app = InspectApp(state_dir=state_dir, initial_session_id=_ALIASES["failed_loop"])
    async with app.run_test() as pilot:
        await pilot.pause()
        app.focus_tasks()
        await pilot.pause()
        tasks_pane = app.query_one("#tasks-pane")
        runs_pane = app.query_one("#runs-pane")
        assert "--focused-pane" in tasks_pane.classes
        assert "--focused-pane" not in runs_pane.classes


@pytest.mark.asyncio
async def test_right_arrow_on_runs_drills_into_tasks(state_dir: Path):
    """Right arrow while focused on the Runs pane moves to the Tasks pane."""
    from ansible_aom.tui.screens.inspect import InspectApp

    app = InspectApp(state_dir=state_dir, initial_session_id=_ALIASES["failed_loop"])
    async with app.run_test() as pilot:
        await pilot.pause()
        app.focus_runs()
        await pilot.pause()
        await pilot.press("right")
        await pilot.pause()
        node = app.focused
        ids: list[str | None] = []
        while node is not None:
            ids.append(getattr(node, "id", None))
            node = getattr(node, "parent", None)
        assert "tasks-tree" in ids, f"Expected focus on tasks-tree, got {ids!r}"


@pytest.mark.asyncio
async def test_escape_steps_back_to_previous_pane(state_dir: Path):
    """Escape moves focus one pane to the left (Detail → Tasks → Runs)."""
    from ansible_aom.tui.screens.inspect import InspectApp

    app = InspectApp(state_dir=state_dir, initial_session_id=_ALIASES["failed_loop"])
    async with app.run_test() as pilot:
        await pilot.pause()
        app.focus_detail()
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        # From Detail, Escape lands in Tasks pane.
        node = app.focused
        ids: list[str | None] = []
        while node is not None:
            ids.append(getattr(node, "id", None))
            node = getattr(node, "parent", None)
        assert "tasks-tree" in ids, f"After Esc from Detail, expected Tasks pane; got {ids!r}"


@pytest.mark.asyncio
async def test_status_labels_carry_colour_markup(state_dir: Path):
    """Stats labels in tree + runs use Rich markup so OK/failed are colour-coded."""
    from ansible_aom.core.inspect_model import StatusCounts
    from ansible_aom.tui.screens.inspect import _RunRow, _stats_label

    label = _stats_label(StatusCounts(ok=3, failed=1, changed=2))
    assert "[green]" in label
    assert "[bold red]" in label
    assert "[yellow]" in label

    from ansible_aom.tui.screens.inspect import InspectApp

    app = InspectApp(state_dir=state_dir, initial_session_id=_ALIASES["failed_loop"])
    async with app.run_test() as pilot:
        await pilot.pause()
        listview = app.query_one("#runs-list")
        # The failed_loop row's status icon should be wrapped in a colour
        # markup span, so the source line1 (before Rich consumes it)
        # contains the icon plus the colour tag.
        first = listview.children[0]
        assert isinstance(first, _RunRow)
        from ansible_aom.tui.screens.inspect import _render_run_lines

        line1, _line2, _line3 = _render_run_lines(first.summary)
        assert "✖" in line1
        assert "bold red" in line1


@pytest.mark.asyncio
async def test_detail_block_includes_action_and_no_session_stderr(state_dir: Path):
    """Per-task detail surfaces the module (``action``) and omits the
    session-wide stderr.log that used to leak into every task."""
    from ansible_aom.tui.screens.inspect import InspectApp

    app = InspectApp(state_dir=state_dir, initial_session_id=_ALIASES["failed_loop"])
    async with app.run_test() as pilot:
        await pilot.pause()
        body = app._detail_text
        assert "ACTION community.general.homebrew_cask" in body
        # The previous version embedded "stderr.log (tail)" here; the
        # session-wide log no longer leaks into per-task detail.
        assert "stderr.log" not in body


@pytest.mark.asyncio
async def test_y_yanks_detail(state_dir: Path, monkeypatch):
    copied: list[str] = []
    monkeypatch.setattr(
        "ansible_aom.tui.screens.inspect._copy_to_clipboard",
        lambda text: copied.append(text),
    )
    from ansible_aom.tui.screens.inspect import InspectApp

    app = InspectApp(state_dir=state_dir, initial_session_id=_ALIASES["failed_loop"])
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("y")
        await pilot.pause()
    assert copied
    assert "One or more items failed" in copied[0]
