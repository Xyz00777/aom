"""Renderer factory.

One entry point — :func:`create_renderer` — that picks the concrete
:class:`Renderer` for a given ``mode``. The CLI passes a single
``mode`` literal (``"compact"`` / ``"tui"`` / ``"json"``) so it no
longer special-cases JSON output. See ARCHITECTURE.md §3, §7.7.

The legacy ``tui_mode`` (boolean) and ``format`` (str) parameters are
still accepted as deprecated aliases so older callers and tests keep
working — ``mode`` wins when both are supplied.
"""

from __future__ import annotations

from typing import Literal

from ansible_aom.renderer.protocol import Renderer

RenderMode = Literal["compact", "tui", "json"]

# Legacy alias retained for callers that still type-check against it.
RenderFormat = Literal["compact", "json"]


def create_renderer(
    tui_mode: bool | None = None,
    is_tty: bool = True,
    format: RenderFormat | None = None,
    mode: RenderMode | None = None,
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
            ``"tui"`` (multi-panel Textual TUI), or ``"json"`` (silent
            during the run; emits one JSON object on completion). When
            omitted, falls back to the legacy ``tui_mode`` / ``format``
            args so the call sites haven't all migrated yet still work.
        is_tty: Whether stdout is a TTY. Forwarded to ``CompactRenderer``
            so it knows whether to use ANSI cursor control. Ignored by
            ``AOMApp`` (Textual manages its own terminal handling) and by
            ``JsonRenderer`` (silent during the run).
        tui_mode: **Deprecated** — pass ``mode="tui"`` instead. Kept so
            historical call sites don't need a same-PR migration.
        format: **Deprecated** — pass ``mode="json"`` instead. Same
            rationale as ``tui_mode``.
        hide_states: List of host states to suppress from the compact
            log (e.g. ``["ok", "skipped"]``). Forwarded to
            ``CompactRenderer``; ignored by ``AOMApp`` and
            ``JsonRenderer``.
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
        A :class:`Renderer` instance: :class:`CompactRenderer`,
        :class:`AOMApp`, or :class:`JsonRenderer`.
    """
    resolved = _resolve_mode(mode=mode, tui_mode=tui_mode, format=format)

    if resolved == "tui":
        from ansible_aom.tui.app import AOMApp

        return AOMApp()
    if resolved == "json":
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


def _resolve_mode(
    *,
    mode: RenderMode | None,
    tui_mode: bool | None,
    format: RenderFormat | None,
) -> RenderMode:
    """Pick a single ``RenderMode`` from the user-facing parameter set.

    Priority: explicit ``mode`` wins. Otherwise, ``tui_mode=True`` →
    ``"tui"``, ``format="json"`` → ``"json"``, else ``"compact"``. The
    CLI's mutual-exclusion check (``--tui`` + ``--format json``) means
    we never see both set in production, but tests sometimes do — TUI
    wins, matching today's behaviour.
    """
    if mode is not None:
        return mode
    if tui_mode:
        return "tui"
    if format == "json":
        return "json"
    return "compact"
