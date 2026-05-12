"""Renderer factory for AOM.

This module provides the factory function to create the appropriate
renderer based on CLI flags.

See SPECIFICATION.md Section 2.3 for factory function.
"""

from typing import Literal

from ansible_aom.renderer.protocol import Renderer

RenderFormat = Literal["compact", "json"]


def create_renderer(
    tui_mode: bool = False,
    is_tty: bool = True,
    format: RenderFormat = "compact",
) -> Renderer:
    """Create the appropriate renderer based on CLI flags.

    Args:
        tui_mode: If True, create Textual TUI renderer. Wins over
            ``format`` because the TUI doesn't have a JSON variant —
            the CLI is responsible for rejecting ``--tui --format json``
            as a usage error before getting here.
        is_tty: Whether stdout is a TTY. Forwarded to CompactRenderer to
            decide whether ANSI cursor control should be active. Ignored
            for the TUI (Textual manages its own terminal handling) and
            for the JSON renderer (silent during the run).
        format: Output format for the streaming renderer. ``"compact"``
            (default) is the nom-style ANSI live view; ``"json"`` is
            silent during the run and emits a single JSON object on
            completion.

    Returns:
        Renderer instance (CompactRenderer, AOMApp, or JsonRenderer).
    """
    if tui_mode:
        from ansible_aom.tui.app import AOMApp

        return AOMApp()
    if format == "json":
        from ansible_aom.json_renderer import JsonRenderer

        return JsonRenderer()
    from ansible_aom.compact.renderer import CompactRenderer

    return CompactRenderer(is_tty=is_tty)
