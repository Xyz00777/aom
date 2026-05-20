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
