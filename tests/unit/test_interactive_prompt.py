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

    def test_surfaces_prompt_text_via_stdout_not_input_arg(self, capsys) -> None:
        """The prompt must go to stdout directly, NOT via input(prompt).

        readline (auto-loaded with stdlib) routes ``input(prompt)``'s
        prompt to stderr when stdin/stdout are TTYs, which means
        ``aom site.yml 2>file`` hides the prompt from the user
        entirely. Writing to stdout via ``sys.stdout.write`` bypasses
        readline.
        """
        from ansible_aom.compact.renderer import CompactRenderer

        renderer = CompactRenderer()
        with (
            patch.object(renderer._display, "stop"),
            patch.object(renderer._display, "start"),
            patch("builtins.input", return_value="") as mock_input,
        ):
            renderer.handle_interactive_prompt("Deploy? Press Enter: ")

        # input() called WITHOUT a prompt arg.
        mock_input.assert_called_once_with()
        # Prompt text reached stdout directly.
        out = capsys.readouterr().out
        assert "Deploy? Press Enter: " in out

    def test_returns_empty_string_on_eof(self) -> None:
        from ansible_aom.compact.renderer import CompactRenderer

        renderer = CompactRenderer()
        with (
            patch.object(renderer._display, "stop"),
            patch.object(renderer._display, "start"),
            patch("builtins.input", side_effect=EOFError),
        ):
            assert renderer.handle_interactive_prompt("anything: ") == ""

    def test_keyboard_interrupt_propagates_so_run_can_abort(self) -> None:
        """Pause says 'Ctrl+C to abort' — Ctrl+C MUST abort, not continue.

        Previously the handler caught KeyboardInterrupt and returned ""
        (i.e. Enter), which silently turned every abort into a confirm.
        The runner's outer KeyboardInterrupt handler now sees the
        propagation and SIGINTs the child.
        """
        from ansible_aom.compact.renderer import CompactRenderer

        renderer = CompactRenderer()
        import pytest as _pytest

        with (
            patch.object(renderer._display, "stop"),
            patch.object(renderer._display, "start"),
            patch("builtins.input", side_effect=KeyboardInterrupt),
        ):
            with _pytest.raises(KeyboardInterrupt):
                renderer.handle_interactive_prompt("anything: ")

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
