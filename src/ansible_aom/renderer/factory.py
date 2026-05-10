"""Renderer factory for AOM.

This module provides the factory function to create the appropriate
renderer based on CLI flags.

See SPECIFICATION.md Section 2.3 for factory function.
"""

from ansible_aom.renderer.protocol import Renderer


def create_renderer(tui_mode: bool = False, is_tty: bool = True) -> Renderer:
    """Create the appropriate renderer based on CLI flags.

    Args:
        tui_mode: If True, create Textual TUI renderer. Otherwise compact.
        is_tty: Whether stdout is a TTY. Forwarded to CompactRenderer to
            decide whether ANSI cursor control should be active. Ignored
            for the TUI (Textual manages its own terminal handling).

    Returns:
        Renderer instance (CompactRenderer or AOMApp).
    """
    if tui_mode:
        from ansible_aom.tui.app import AOMApp

        return AOMApp()
    from ansible_aom.compact.renderer import CompactRenderer

    return CompactRenderer(is_tty=is_tty)
