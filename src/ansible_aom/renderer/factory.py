"""Renderer factory for AOM.

This module provides the factory function to create the appropriate
renderer based on CLI flags.

See SPECIFICATION.md Section 2.3 for factory function.
"""

from typing import Any

from ansible_aom.renderer.protocol import Renderer


def create_renderer(tui_mode: bool = False, **kwargs: Any) -> Renderer:
    """Create the appropriate renderer based on CLI flags.

    Args:
        tui_mode: If True, create Textual TUI renderer. Otherwise compact.
        **kwargs: Additional arguments passed to renderer constructor.

    Returns:
        Renderer instance (CompactRenderer or AOMApp).
    """
    if tui_mode:
        from ansible_aom.tui.app import AOMApp

        return AOMApp(**kwargs)
    else:
        from ansible_aom.compact.renderer import CompactRenderer

        return CompactRenderer(**kwargs)
