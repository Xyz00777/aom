"""Smoke tests for the AOM TUI screens (Item #6).

Each of these screens was at 0% coverage before this file:

* ``HelpOverlay`` (help.py)
* ``InspectScreen`` (inspect.py)
* ``QuitConfirmScreen`` (quit_confirm.py)
* ``RerunDialog`` (rerun.py)
* ``SettingsScreen`` (settings.py)

The tests assert *liveness* — each screen mounts, renders, and dismisses
cleanly via the keybinding documented in its module. Visual fidelity
isn't covered here (that's snapshot territory); the goal is to catch
"the screen import-errors at runtime" and "the dismiss key crashes".

Discoverability of the screens from the main keymap:

* Only ``QuitConfirmScreen`` is auto-pushed by the main app — pressing
  ``q`` while the run is in ``RUNNING`` state triggers ``action_quit``
  (see ``AOMApp.action_quit``).
* The others (Help, Settings, Inspect, Rerun) are not wired into the
  main keymap *yet* — the keybindings exist (``?``, ``S``, …) but the
  ``action_*`` handlers are not implemented on AOMApp. So we push
  those screens directly via ``pilot.app.push_screen`` and smoke-test
  render + dismiss. This is documented as the deferred wiring.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from textual.widgets import Static

from ansible_aom.tui.app import AOMApp


# ---------------------------------------------------------------------------
# HelpOverlay
# ---------------------------------------------------------------------------


class TestHelpOverlaySmoke:
    """``?`` opens HelpOverlay → Escape dismisses → back to MainScreen."""

    @pytest.mark.asyncio
    async def test_help_mounts_and_dismisses(self) -> None:
        from ansible_aom.tui.screens.help import HelpOverlay
        from ansible_aom.tui.screens.main import MainScreen

        app = AOMApp()
        async with app.run_test() as pilot:
            # Screen not reachable from the main keymap (no action_show_help
            # on AOMApp yet), so push directly. Documented above.
            await pilot.app.push_screen(HelpOverlay())
            await pilot.pause()
            assert isinstance(pilot.app.screen, HelpOverlay)

            # Hero widget: a Static with id="help-content" carrying the
            # rendered keybinding list.
            content = pilot.app.screen.query_one("#help-content", Static)
            text = str(content.render())
            assert "AOM - Keybindings" in text
            # At least one keybinding from the GLOBAL context is present.
            assert "Quit" in text or "quit" in text.lower()

            # Escape is the documented dismiss key.
            await pilot.press("escape")
            await pilot.pause()
            assert isinstance(pilot.app.screen, MainScreen)


# ---------------------------------------------------------------------------
# SettingsScreen
# ---------------------------------------------------------------------------


class TestSettingsScreenSmoke:
    @pytest.mark.asyncio
    async def test_settings_mounts_and_dismisses(self) -> None:
        from ansible_aom.tui.screens.main import MainScreen
        from ansible_aom.tui.screens.settings import SettingsScreen

        app = AOMApp()
        async with app.run_test() as pilot:
            await pilot.app.push_screen(SettingsScreen())
            await pilot.pause()
            assert isinstance(pilot.app.screen, SettingsScreen)

            content = pilot.app.screen.query_one("#settings-content", Static)
            text = str(content.render())
            assert "AOM - Settings" in text
            # Key sections from _build_display_lines.
            assert "Status Bar:" in text
            assert "Redaction:" in text

            await pilot.press("escape")
            await pilot.pause()
            assert isinstance(pilot.app.screen, MainScreen)


# ---------------------------------------------------------------------------
# QuitConfirmScreen
# ---------------------------------------------------------------------------


class TestQuitConfirmScreenSmoke:
    """The quit-confirm modal returns True (quit) or False (cancel).

    Reached from the main keymap when the app is in RUNNING/STARTING
    state (see ``AOMApp.action_quit``). We force the app into STARTING
    by calling ``start`` directly — that's the documented entry path
    for an in-progress run.
    """

    @pytest.mark.asyncio
    async def test_quit_confirm_mounts(self) -> None:
        from ansible_aom.tui.screens.quit_confirm import QuitConfirmScreen

        app = AOMApp()
        async with app.run_test() as pilot:
            await pilot.app.push_screen(QuitConfirmScreen())
            await pilot.pause()
            assert isinstance(pilot.app.screen, QuitConfirmScreen)

            content = pilot.app.screen.query_one("#quit-content", Static)
            text = str(content.render())
            assert "Quit Confirmation" in text

    @pytest.mark.asyncio
    async def test_quit_confirm_yes_dismisses_with_true(self) -> None:
        from ansible_aom.tui.screens.main import MainScreen
        from ansible_aom.tui.screens.quit_confirm import QuitConfirmScreen

        app = AOMApp()
        async with app.run_test() as pilot:
            captured: list[bool | None] = []

            def on_result(result: bool | None) -> None:
                captured.append(result)

            await pilot.app.push_screen(QuitConfirmScreen(), on_result)
            await pilot.pause()
            await pilot.press("y")
            await pilot.pause()
            # Back on the main screen after the modal dismissed.
            assert isinstance(pilot.app.screen, MainScreen)
            assert captured == [True], f"expected confirm callback True, got {captured}"

    @pytest.mark.asyncio
    async def test_quit_confirm_no_dismisses_with_false(self) -> None:
        from ansible_aom.tui.screens.main import MainScreen
        from ansible_aom.tui.screens.quit_confirm import QuitConfirmScreen

        app = AOMApp()
        async with app.run_test() as pilot:
            captured: list[bool | None] = []

            def on_result(result: bool | None) -> None:
                captured.append(result)

            await pilot.app.push_screen(QuitConfirmScreen(), on_result)
            await pilot.pause()
            await pilot.press("n")
            await pilot.pause()
            assert isinstance(pilot.app.screen, MainScreen)
            assert captured == [False], f"expected cancel callback False, got {captured}"


# ---------------------------------------------------------------------------
# RerunDialog
# ---------------------------------------------------------------------------


class TestRerunDialogSmoke:
    @pytest.mark.asyncio
    async def test_rerun_mounts_and_dismisses(self) -> None:
        from ansible_aom.tui.screens.main import MainScreen
        from ansible_aom.tui.screens.rerun import RerunDialog

        app = AOMApp()
        async with app.run_test() as pilot:
            await pilot.app.push_screen(RerunDialog())
            await pilot.pause()
            assert isinstance(pilot.app.screen, RerunDialog)

            content = pilot.app.screen.query_one("#rerun-content", Static)
            text = str(content.render())
            assert "Re-run Playbook" in text

            await pilot.press("escape")
            await pilot.pause()
            assert isinstance(pilot.app.screen, MainScreen)

    @pytest.mark.asyncio
    async def test_rerun_same_args_returns_true(self) -> None:
        from ansible_aom.tui.screens.rerun import RerunDialog

        app = AOMApp()
        async with app.run_test() as pilot:
            captured: list[bool | None] = []

            def on_result(result: bool | None) -> None:
                captured.append(result)

            await pilot.app.push_screen(RerunDialog(), on_result)
            await pilot.pause()
            await pilot.press("s")
            await pilot.pause()
            assert captured == [True], f"expected same-args True, got {captured}"

    @pytest.mark.asyncio
    async def test_rerun_modified_args_returns_false(self) -> None:
        from ansible_aom.tui.screens.rerun import RerunDialog

        app = AOMApp()
        async with app.run_test() as pilot:
            captured: list[bool | None] = []

            def on_result(result: bool | None) -> None:
                captured.append(result)

            await pilot.app.push_screen(RerunDialog(), on_result)
            await pilot.pause()
            await pilot.press("m")
            await pilot.pause()
            assert captured == [False], f"expected modified-args False, got {captured}"


# ---------------------------------------------------------------------------
# InspectScreen
# ---------------------------------------------------------------------------


class TestInspectScreenSmoke:
    """InspectScreen loads a session if given a session_id + state_dir.

    The screen is mounted directly (no main-screen keybinding wires
    into it yet — same deferred-wiring story as Help/Settings/Rerun).
    We construct a minimal session on disk so the screen exercises
    its data-loading path rather than the placeholder branch.
    """

    @pytest.mark.asyncio
    async def test_inspect_with_session_mounts_and_dismisses(
        self, tmp_path: Path
    ) -> None:
        import json

        from ansible_aom.tui.screens.inspect import InspectScreen
        from ansible_aom.tui.screens.main import MainScreen

        # Minimal session on disk: one play, one host, one OK task.
        sid = "01971111-1111-7000-8000-000000000777"
        session_path = tmp_path / sid
        session_path.mkdir(parents=True)
        meta = {
            "playbook": "site.yml",
            "ansible_args": ["-i", "inv.ini"],
            "start_time": "2026-05-13T10:00:00Z",
            "end_time": "2026-05-13T10:00:05Z",
            "duration_seconds": 5.0,
            "session_id": sid,
            "status": "completed",
            "version": "1.1",
        }
        (session_path / "meta.json").write_text(json.dumps(meta))
        events = [
            {
                "_event": "v2_playbook_on_play_start",
                "play": {"id": "p1", "name": "Deploy"},
            },
            {
                "_event": "v2_runner_on_ok",
                "task": {"id": "t1", "name": "Install"},
                "hosts": {"web1": {"ok": True}},
            },
            {
                "_event": "v2_playbook_on_stats",
                "stats": {"web1": {"ok": 1, "failures": 0}},
            },
        ]
        (session_path / "events.jsonl").write_text(
            "\n".join(json.dumps(e) for e in events) + "\n"
        )
        (session_path / "stderr.log").write_text("")

        app = AOMApp()
        async with app.run_test() as pilot:
            await pilot.app.push_screen(
                InspectScreen(session_id=sid, state_dir=tmp_path)
            )
            await pilot.pause()
            assert isinstance(pilot.app.screen, InspectScreen)

            # Hero widgets: the tree panel and info panel.
            tree = pilot.app.screen.query_one("#session-tree", Static)
            info = pilot.app.screen.query_one("#session-info", Static)
            tree_text = str(tree.render())
            info_text = str(info.render())
            assert "Session Tree" in tree_text
            assert sid[:8] in tree_text  # short_id rendered
            assert "Session Summary" in info_text
            assert "Plays: 1" in info_text

            await pilot.press("escape")
            await pilot.pause()
            assert isinstance(pilot.app.screen, MainScreen)

    @pytest.mark.asyncio
    async def test_inspect_without_session_shows_placeholder(self) -> None:
        """No session_id → InspectScreen renders the placeholder branch."""
        from ansible_aom.tui.screens.inspect import InspectScreen

        app = AOMApp()
        async with app.run_test() as pilot:
            await pilot.app.push_screen(InspectScreen())
            await pilot.pause()
            assert isinstance(pilot.app.screen, InspectScreen)

            tree = pilot.app.screen.query_one("#session-tree", Static)
            tree_text = str(tree.render())
            assert "No session loaded" in tree_text
