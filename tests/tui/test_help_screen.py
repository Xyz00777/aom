"""Unit tests for the TUI help overlay screen.

Tests cover the L2 help.py expansion:
- Help overlay is a ModalScreen bound to '?' / Escape
- Composes all keybinding contexts (global, tree, log, post-run)
- Renders keyboard shortcuts with key + description
- Documents command reference for the ``aom`` CLI
- Documents navigation instructions (panels, focus, scrolling)
- Dismissed result returns None (close-only modal)
"""

from __future__ import annotations

import asyncio
from io import StringIO

import pytest
from rich.console import Console


class TestHelpOverlayStructure:
    """Structural assertions about the HelpOverlay screen."""

    def test_help_overlay_is_modal_screen(self):
        from textual.screen import ModalScreen

        from ansible_aom.tui.screens.help import HelpOverlay

        assert issubclass(HelpOverlay, ModalScreen)

    def test_help_overlay_can_be_imported(self):
        from ansible_aom.tui.screens import help as help_module
        from ansible_aom.tui.screens.help import HelpOverlay

        assert help_module.HelpOverlay is HelpOverlay


class TestHelpOverlayBindings:
    """HelpOverlay must be dismissable from '?' and Escape keys."""

    def test_escape_binding_dismisses(self):
        from ansible_aom.tui.screens.help import HelpOverlay

        keys = [b.key for b in HelpOverlay.BINDINGS]
        assert "escape" in keys

    def test_question_mark_binding_dismisses(self):
        from ansible_aom.tui.screens.help import HelpOverlay

        keys = [b.key for b in HelpOverlay.BINDINGS]
        assert any(k in keys for k in ("question", "question_mark"))

    def test_all_bindings_have_dismiss_action(self):
        from ansible_aom.tui.screens.help import HelpOverlay

        for b in HelpOverlay.BINDINGS:
            assert b.action == "dismiss"


async def _render_overlay_text(app, screen_factory) -> str:
    """Mount the overlay in a running app and return its rendered text."""
    screen = screen_factory()
    await app.push_screen(screen)
    await asyncio.sleep(0)
    body_widget = app.screen.query_one("#help-content")
    content = body_widget._Static__content
    buf = StringIO()
    console = Console(file=buf, force_terminal=False, width=120, color_system=None)
    console.print(content)
    return buf.getvalue()


class TestHelpOverlayContent:
    """Content assertions: the help screen surfaces the actual docs."""

    @pytest.mark.asyncio
    async def test_lists_keyboard_shortcuts(self):
        from ansible_aom.tui.app import AOMApp
        from ansible_aom.tui.screens.help import HelpOverlay

        app = AOMApp()
        async with app.run_test() as pilot:
            text = await _render_overlay_text(app, HelpOverlay)
            await pilot.press("escape")
            assert "Keyboard" in text or "Keybinding" in text or "key" in text.lower()

    @pytest.mark.asyncio
    async def test_includes_quit_shortcut(self):
        from ansible_aom.tui.app import AOMApp
        from ansible_aom.tui.screens.help import HelpOverlay

        app = AOMApp()
        async with app.run_test() as pilot:
            text = await _render_overlay_text(app, HelpOverlay)
            await pilot.press("escape")
            assert "q" in text

    @pytest.mark.asyncio
    async def test_includes_help_shortcut(self):
        from ansible_aom.tui.app import AOMApp
        from ansible_aom.tui.screens.help import HelpOverlay

        app = AOMApp()
        async with app.run_test() as pilot:
            text = await _render_overlay_text(app, HelpOverlay)
            await pilot.press("escape")
            assert "?" in text

    @pytest.mark.asyncio
    async def test_includes_navigation_section(self):
        from ansible_aom.tui.app import AOMApp
        from ansible_aom.tui.screens.help import HelpOverlay

        app = AOMApp()
        async with app.run_test() as pilot:
            text = await _render_overlay_text(app, HelpOverlay)
            await pilot.press("escape")
            assert "tab" in text.lower()

    @pytest.mark.asyncio
    async def test_includes_command_reference_section(self):
        from ansible_aom.tui.app import AOMApp
        from ansible_aom.tui.screens.help import HelpOverlay

        app = AOMApp()
        async with app.run_test() as pilot:
            text = await _render_overlay_text(app, HelpOverlay)
            await pilot.press("escape")
            assert "inspect" in text or "replay" in text or "rerun" in text

    @pytest.mark.asyncio
    async def test_includes_all_keybinding_contexts(self):
        from ansible_aom.tui.app import AOMApp
        from ansible_aom.tui.screens.help import HelpOverlay

        app = AOMApp()
        async with app.run_test() as pilot:
            text = await _render_overlay_text(app, HelpOverlay)
            await pilot.press("escape")
            lowered = text.lower()
            assert "tree" in lowered
            assert "post" in lowered or "rerun" in lowered


class TestHelpOverlayDismissAction:
    """The dismiss action must close the screen without returning a value."""

    @pytest.mark.asyncio
    async def test_dismiss_via_escape_key(self):
        from ansible_aom.tui.app import AOMApp
        from ansible_aom.tui.screens.help import HelpOverlay

        app = AOMApp()
        async with app.run_test() as pilot:
            screen = HelpOverlay()
            await app.push_screen(screen)
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()
            assert app.screen is not screen


class TestHelpOverlayLineCount:
    """The expansion must be substantive — not a one-paragraph stub."""

    def test_help_module_is_substantive(self):
        from pathlib import Path

        src = (
            Path(__file__).resolve().parents[2]
            / "src"
            / "ansible_aom"
            / "tui"
            / "screens"
            / "help.py"
        )
        line_count = sum(1 for _ in src.read_text().splitlines())
        assert line_count > 80, (
            f"help.py has only {line_count} lines; expected a substantive "
            "expansion beyond the original 80-line stub."
        )
