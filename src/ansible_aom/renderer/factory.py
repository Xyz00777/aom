"""Renderer factory for compact and JSON output."""

from __future__ import annotations

from typing import Literal

from ansible_aom.renderer.protocol import Renderer

RenderMode = Literal["compact", "json"]


def create_renderer(
    is_tty: bool = True,
    mode: RenderMode = "compact",
    hide_states: list[str] | None = None,
    record: bool = False,
    capture_verbose: bool = False,
    show_failed_hint: bool = True,
    show_warnings: bool = True,
    show_deprecations: bool = True,
) -> Renderer:
    """Create the renderer selected by ``mode``.

    Args:
        mode: ``"compact"`` (default streaming nom-style ANSI view),
            or ``"json"`` (silent during the run; emits one JSON object
            on completion).
        is_tty: Whether stdout is a TTY. Forwarded to ``CompactRenderer``
            so it knows whether to use ANSI cursor control. Ignored by
            ``JsonRenderer`` (silent during the run).
        hide_states: List of host states to suppress from the compact
            log (e.g. ``["ok", "skipped"]``). Ignored by ``JsonRenderer``.
        record: Whether the compact renderer is actively recording this
            run. When true, the status bar shows the recording chip.
        capture_verbose: Whether verbose capture is enabled. When true,
            the recording chip upgrades from ``● REC`` to ``● REC+VC``.
        show_failed_hint: Whether compact mode should show the first line
            of failed/unreachable ``msg`` beneath the task summary.
        show_warnings: Whether compact mode should surface warnings in
            the live log.
        show_deprecations: Whether compact mode should surface
            deprecations in the live log.

    Returns:
        A :class:`Renderer` instance: :class:`CompactRenderer` or
        :class:`JsonRenderer`.
    """
    if mode == "json":
        from ansible_aom.formats.json import JsonRenderer

        return JsonRenderer()

    from ansible_aom.compact.renderer import CompactRenderer

    return CompactRenderer(
        is_tty=is_tty,
        hide_states=hide_states or [],
        record=record,
        capture_verbose=capture_verbose,
        show_failed_hint=show_failed_hint,
        show_warnings=show_warnings,
        show_deprecations=show_deprecations,
    )
