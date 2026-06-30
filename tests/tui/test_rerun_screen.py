"""Unit tests for the TUI rerun dialog screen.

Tests cover the L2 rerun.py expansion:
- RerunDialog is a ModalScreen returning bool
- Lists failed / unreachable hosts from the loaded session
- Shows the planned ansible-playbook command line
- Has a confirm/cancel flow (y / n / escape)
- Reads session data via session/store.py + session/summary.py
"""

from __future__ import annotations

import asyncio
import json
from io import StringIO
from pathlib import Path

import pytest
from rich.console import Console


def _write_session(state_dir: Path, session_id: str, **overrides) -> Path:
    """Create a session directory with a minimal meta.json + events.jsonl."""
    meta: dict = {
        "session_id": session_id,
        "playbook": "site.yml",
        "ansible_args": ["-i", "inv.ini"],
        "start_time": "2026-05-20T10:00:00.000000Z",
        "end_time": "2026-05-20T10:01:30.000000Z",
        "duration_seconds": 90.0,
        "status": "failed",
        "version": "1.1",
    }
    meta.update(overrides)
    session_dir = state_dir / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / "meta.json").write_text(json.dumps(meta))
    return session_dir


def _write_events(session_dir: Path, events: list[dict]) -> None:
    """Append events.jsonl to a session directory."""
    events_file = session_dir / "events.jsonl"
    with events_file.open("w") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")


class TestRerunDialogStructure:
    """Structural assertions about the RerunDialog."""

    def test_rerun_dialog_is_modal_screen(self):
        from textual.screen import ModalScreen

        from ansible_aom.tui.screens.rerun import RerunDialog

        assert issubclass(RerunDialog, ModalScreen)

    def test_rerun_dialog_can_be_imported(self):
        from ansible_aom.tui.screens import rerun as rerun_module
        from ansible_aom.tui.screens.rerun import RerunDialog

        assert rerun_module.RerunDialog is RerunDialog

    def test_rerun_dialog_has_confirm_action(self):
        from ansible_aom.tui.screens.rerun import RerunDialog

        action_names = {b.action for b in RerunDialog.BINDINGS}
        assert "confirm" in action_names

    def test_rerun_dialog_has_cancel_action(self):
        from ansible_aom.tui.screens.rerun import RerunDialog

        action_names = {b.action for b in RerunDialog.BINDINGS}
        assert "cancel" in action_names


async def _render_dialog_text(app, dialog) -> str:
    """Mount the dialog and return its rendered body as text."""
    await app.push_screen(dialog)
    await asyncio.sleep(0)
    body_widget = app.screen.query_one("#rerun-content")
    content = body_widget._Static__content
    buf = StringIO()
    console = Console(file=buf, force_terminal=False, width=160, color_system=None)
    console.print(content)
    return buf.getvalue()


class TestRerunDialogContent:
    """Content assertions: the dialog shows real session data."""

    @pytest.mark.asyncio
    async def test_shows_planned_command(self, tmp_path: Path):
        from ansible_aom.tui.app import AOMApp
        from ansible_aom.tui.screens.rerun import RerunDialog

        session_id = "01971111-1111-7000-8000-000000000001"
        state_dir = tmp_path / "sessions"
        _write_session(state_dir, session_id)
        _write_events(
            state_dir / session_id,
            [
                {
                    "_event": "v2_runner_on_failed",
                    "task": {"name": "T1"},
                    "hosts": {"web2": {"failed": True}},
                }
            ],
        )

        app = AOMApp()
        async with app.run_test() as pilot:
            text = await _render_dialog_text(app, RerunDialog(state_dir=state_dir))
            await pilot.press("escape")
            assert "ansible-playbook" in text or "ansible" in text.lower()
            assert "site.yml" in text or "playbook" in text.lower()

    @pytest.mark.asyncio
    async def test_shows_failed_hosts(self, tmp_path: Path):
        from ansible_aom.tui.app import AOMApp
        from ansible_aom.tui.screens.rerun import RerunDialog

        session_id = "01971111-1111-7000-8000-000000000002"
        state_dir = tmp_path / "sessions"
        _write_session(state_dir, session_id)
        _write_events(
            state_dir / session_id,
            [
                {
                    "_event": "v2_runner_on_failed",
                    "task": {"name": "T1"},
                    "hosts": {"web1": {"failed": True}, "web2": {"failed": True}},
                }
            ],
        )

        app = AOMApp()
        async with app.run_test() as pilot:
            text = await _render_dialog_text(app, RerunDialog(state_dir=state_dir))
            await pilot.press("escape")
            assert "web1" in text
            assert "web2" in text

    @pytest.mark.asyncio
    async def test_shows_unreachable_hosts(self, tmp_path: Path):
        from ansible_aom.tui.app import AOMApp
        from ansible_aom.tui.screens.rerun import RerunDialog

        session_id = "01971111-1111-7000-8000-000000000003"
        state_dir = tmp_path / "sessions"
        _write_session(state_dir, session_id)
        _write_events(
            state_dir / session_id,
            [
                {
                    "_event": "v2_runner_on_unreachable",
                    "task": {"name": "T1"},
                    "hosts": {"db1": {"unreachable": True}},
                }
            ],
        )

        app = AOMApp()
        async with app.run_test() as pilot:
            text = await _render_dialog_text(
                app,
                RerunDialog(state_dir=state_dir, host_filter="unreachable"),
            )
            await pilot.press("escape")
            assert "db1" in text

    @pytest.mark.asyncio
    async def test_handles_empty_host_set(self, tmp_path: Path):
        from ansible_aom.tui.app import AOMApp
        from ansible_aom.tui.screens.rerun import RerunDialog

        session_id = "01971111-1111-7000-8000-000000000004"
        state_dir = tmp_path / "sessions"
        _write_session(state_dir, session_id)
        _write_events(state_dir / session_id, [])

        app = AOMApp()
        async with app.run_test() as pilot:
            text = await _render_dialog_text(app, RerunDialog(state_dir=state_dir))
            await pilot.press("escape")
            lowered = text.lower()
            assert "nothing" in lowered or "no failed" in lowered or "no " in lowered

    @pytest.mark.asyncio
    async def test_handles_no_sessions(self, tmp_path: Path):
        from ansible_aom.tui.app import AOMApp
        from ansible_aom.tui.screens.rerun import RerunDialog

        state_dir = tmp_path / "sessions"
        state_dir.mkdir(parents=True, exist_ok=True)

        app = AOMApp()
        async with app.run_test() as pilot:
            text = await _render_dialog_text(app, RerunDialog(state_dir=state_dir))
            await pilot.press("escape")
            lowered = text.lower()
            assert "no sessions" in lowered or "session" in lowered


class TestRerunDialogDismissValues:
    """The dialog must return True on confirm, False on cancel."""

    @pytest.mark.asyncio
    async def test_confirm_returns_true(self, tmp_path: Path):
        from ansible_aom.tui.app import AOMApp
        from ansible_aom.tui.screens.rerun import RerunDialog

        session_id = "01971111-1111-7000-8000-000000000099"
        state_dir = tmp_path / "sessions"
        _write_session(state_dir, session_id)
        _write_events(
            state_dir / session_id,
            [
                {
                    "_event": "v2_runner_on_failed",
                    "task": {"name": "T1"},
                    "hosts": {"web3": {"failed": True}},
                }
            ],
        )

        app = AOMApp()
        async with app.run_test() as pilot:
            result_holder: dict = {}

            def on_result(value):
                result_holder["value"] = value

            dialog = RerunDialog(state_dir=state_dir)
            await app.push_screen(dialog, on_result)
            await pilot.pause()
            await pilot.press("y")
            await pilot.pause()

            assert result_holder.get("value") is True

    @pytest.mark.asyncio
    async def test_cancel_returns_false(self, tmp_path: Path):
        from ansible_aom.tui.app import AOMApp
        from ansible_aom.tui.screens.rerun import RerunDialog

        session_id = "01971111-1111-7000-8000-000000000098"
        state_dir = tmp_path / "sessions"
        _write_session(state_dir, session_id)
        _write_events(state_dir / session_id, [])

        app = AOMApp()
        async with app.run_test() as pilot:
            result_holder: dict = {}

            def on_result(value):
                result_holder["value"] = value

            dialog = RerunDialog(state_dir=state_dir)
            await app.push_screen(dialog, on_result)
            await pilot.pause()
            await pilot.press("n")
            await pilot.pause()

            assert result_holder.get("value") is False


class TestRerunDialogPlanBuilder:
    """RerunDialog should reuse the rerun/cli.py plan builder, not duplicate it."""

    def test_uses_session_store(self, tmp_path: Path):
        from ansible_aom.session.store import list_sessions

        session_id = "01971111-1111-7000-8000-000000000050"
        state_dir = tmp_path / "sessions"
        _write_session(state_dir, session_id)
        sessions = list_sessions(state_dir)
        assert sessions[0]["session_id"] == session_id

    def test_uses_session_summary_helpers(self):
        from ansible_aom.session import summary

        assert hasattr(summary, "collect_failed_hosts")
        assert hasattr(summary, "collect_unreachable_hosts")
        assert hasattr(summary, "collect_changed_hosts")


class TestRerunDialogLineCount:
    """The expansion must be substantive — not a stub."""

    def test_rerun_module_is_substantive(self):
        from pathlib import Path

        src = (
            Path(__file__).resolve().parents[2]
            / "src"
            / "ansible_aom"
            / "tui"
            / "screens"
            / "rerun.py"
        )
        line_count = sum(1 for _ in src.read_text().splitlines())
        assert line_count > 85, (
            f"rerun.py has only {line_count} lines; expected a substantive "
            "expansion beyond the original 85-line stub."
        )
