"""Tests for handle_interactive_prompt (IP1, IP4).

ansible.builtin.pause and vars_prompt emit prompts ending without a
trailing newline and read a single line from stdin. These tests pin
the renderer-side contract: suspend the live panel, surface the
captured prompt text, read a line with echo, restart the panel,
return the answer. ``getpass`` is intentionally NOT used here —
pause/vars_prompt are not secrets, and the user expects to see what
they type.
"""

from __future__ import annotations

from unittest.mock import patch


class TestCompactRendererInteractivePrompt:
    """CompactRenderer must implement handle_interactive_prompt."""

    def test_method_exists(self) -> None:
        from ansible_aom.compact.renderer import CompactRenderer

        renderer = CompactRenderer()
        assert hasattr(renderer, "handle_interactive_prompt")

    def test_stops_display_then_reads_input_then_restarts(self) -> None:
        from ansible_aom.compact.renderer import CompactRenderer

        renderer = CompactRenderer()
        call_order: list[str] = []

        with (
            patch.object(renderer._display, "stop", side_effect=lambda: call_order.append("stop")),
            patch.object(
                renderer._display, "start", side_effect=lambda: call_order.append("start")
            ),
            patch("builtins.input", side_effect=lambda *_: call_order.append("input") or "yes"),
        ):
            answer = renderer.handle_interactive_prompt("Deploy to web1? Press Enter: ")

        assert answer == "yes"
        # stop must run before input (otherwise the live panel overwrites
        # the prompt) and start after (so the panel comes back).
        assert call_order == ["stop", "input", "start"]

    def test_surfaces_prompt_text_to_user(self) -> None:
        """The pending prompt content the user couldn't see goes to input()."""
        from ansible_aom.compact.renderer import CompactRenderer

        renderer = CompactRenderer()
        with (
            patch.object(renderer._display, "stop"),
            patch.object(renderer._display, "start"),
            patch("builtins.input", return_value="") as mock_input,
        ):
            renderer.handle_interactive_prompt("Deploy? Press Enter: ")

        mock_input.assert_called_once_with("Deploy? Press Enter: ")

    def test_returns_empty_string_on_eof(self) -> None:
        from ansible_aom.compact.renderer import CompactRenderer

        renderer = CompactRenderer()
        with (
            patch.object(renderer._display, "stop"),
            patch.object(renderer._display, "start"),
            patch("builtins.input", side_effect=EOFError),
        ):
            assert renderer.handle_interactive_prompt("anything: ") == ""

    def test_returns_empty_string_on_keyboard_interrupt(self) -> None:
        from ansible_aom.compact.renderer import CompactRenderer

        renderer = CompactRenderer()
        with (
            patch.object(renderer._display, "stop"),
            patch.object(renderer._display, "start"),
            patch("builtins.input", side_effect=KeyboardInterrupt),
        ):
            assert renderer.handle_interactive_prompt("anything: ") == ""

    def test_restarts_display_even_if_input_raises(self) -> None:
        """A crashing input() must not leave the panel torn down."""
        from ansible_aom.compact.renderer import CompactRenderer

        renderer = CompactRenderer()
        restarted: list[bool] = []
        with (
            patch.object(renderer._display, "stop"),
            patch.object(renderer._display, "start", side_effect=lambda: restarted.append(True)),
            patch("builtins.input", side_effect=EOFError),
        ):
            renderer.handle_interactive_prompt("x: ")

        assert restarted == [True]


class TestAOMAppInteractivePrompt:
    """AOMApp must implement handle_interactive_prompt via suspend + input."""

    def test_method_exists(self) -> None:
        from ansible_aom.tui.app import AOMApp

        app = AOMApp()
        assert hasattr(app, "handle_interactive_prompt")

    def test_suspends_then_reads_input(self) -> None:
        from ansible_aom.tui.app import AOMApp

        app = AOMApp()
        suspended = False

        class FakeSuspend:
            def __enter__(self):
                nonlocal suspended
                suspended = True
                return self

            def __exit__(self, *args):
                pass

        with (
            patch.object(app, "suspend", return_value=FakeSuspend()),
            patch("builtins.input", return_value="yes"),
        ):
            answer = app.handle_interactive_prompt("Deploy? Press Enter: ")

        assert suspended is True
        assert answer == "yes"

    def test_passes_prompt_to_input(self) -> None:
        from ansible_aom.tui.app import AOMApp

        app = AOMApp()
        with (
            patch.object(app, "suspend"),
            patch("builtins.input", return_value="") as mock_input,
        ):
            app.handle_interactive_prompt("Deploy? Press Enter: ")
        mock_input.assert_called_once_with("Deploy? Press Enter: ")

    def test_returns_empty_on_eof(self) -> None:
        from ansible_aom.tui.app import AOMApp

        app = AOMApp()
        with (
            patch.object(app, "suspend"),
            patch("builtins.input", side_effect=EOFError),
        ):
            assert app.handle_interactive_prompt("x: ") == ""

    def test_returns_empty_on_keyboard_interrupt(self) -> None:
        from ansible_aom.tui.app import AOMApp

        app = AOMApp()
        with (
            patch.object(app, "suspend"),
            patch("builtins.input", side_effect=KeyboardInterrupt),
        ):
            assert app.handle_interactive_prompt("x: ") == ""


class TestProtocol:
    """Renderer protocol gains the interactive prompt method."""

    def test_protocol_declares_handle_interactive_prompt(self) -> None:
        import inspect as py_inspect

        from ansible_aom.renderer.protocol import Renderer

        assert hasattr(Renderer, "handle_interactive_prompt")
        sig = py_inspect.signature(Renderer.handle_interactive_prompt)
        params = list(sig.parameters.keys())
        # self, prompt_text
        assert "prompt_text" in params

    def test_compact_renderer_still_satisfies_protocol(self) -> None:
        from ansible_aom.compact.renderer import CompactRenderer
        from ansible_aom.renderer.protocol import Renderer

        assert isinstance(CompactRenderer(), Renderer)

    def test_aom_app_still_satisfies_protocol(self) -> None:
        from ansible_aom.renderer.protocol import Renderer
        from ansible_aom.tui.app import AOMApp

        assert isinstance(AOMApp(), Renderer)
