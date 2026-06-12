"""Controller side of the per-host prompt channel.

AOM creates a control directory and exports its path (``AOM_PROMPT_CONTROL_DIR``).
The bundled ``aom.interactive.confirm`` action plugin drops one ``<id>.req`` JSON
file per host and blocks reading a per-request ``<id>.fifo``. This class, polled
from the runner's existing 0.5s loop, picks up requests in arrival order, routes
each through ``renderer.handle_interactive_prompt`` (which suspends the live panel),
and writes the answer back to that request's FIFO.

All filesystem errors are swallowed and logged — a broken channel must never crash
the run; worst case the worker stays blocked until ``drain`` unblocks it on teardown.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Protocol

from ansible_aom.core.prompt_channel import (
    FIFO_SUFFIX,
    REQUEST_SUFFIX,
    decode_request,
)

logger = logging.getLogger(__name__)


class _PromptRenderer(Protocol):
    def handle_interactive_prompt(self, prompt_text: str) -> str: ...


class PromptChannel:
    """Watches a control dir for prompt requests and answers them via FIFO."""

    def __init__(self, control_dir: Path) -> None:
        self._dir = control_dir
        self._handled: set[str] = set()

    def _pending(self) -> list[Path]:
        """Return unhandled ``.req`` files, oldest first."""
        try:
            reqs = [p for p in self._dir.glob(f"*{REQUEST_SUFFIX}") if p.stem not in self._handled]
        except OSError as exc:
            logger.debug("prompt channel scan failed: %s", exc)
            return []
        reqs.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0.0)
        return reqs

    def _answer(self, request_id: str, answer: str) -> None:
        """Write a single answer line to the request's FIFO (best-effort)."""
        fifo = self._dir / f"{request_id}{FIFO_SUFFIX}"
        try:
            # Opening for write blocks until the plugin opens for read — which it
            # already has (it wrote the .req then blocked on the FIFO).
            with open(fifo, "w", encoding="utf-8") as fh:
                fh.write(answer + "\n")
        except OSError as exc:
            logger.debug("prompt channel answer write failed (%s): %s", fifo.name, exc)

    def poll(self, renderer: _PromptRenderer) -> bool:
        """Handle at most one pending request. Return True if one was handled.

        One-at-a-time keeps the UX serial when many hosts prompt at once and
        keeps each suspend/restore of the live panel tightly scoped.
        """
        pending = self._pending()
        if not pending:
            return False
        req_path = pending[0]
        try:
            request = decode_request(req_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, KeyError) as exc:
            logger.debug("prompt channel: bad request %s: %s", req_path.name, exc)
            self._handled.add(req_path.stem)
            return False

        answer = renderer.handle_interactive_prompt(request.prompt)
        self._answer(request.id, answer)
        self._handled.add(req_path.stem)
        try:
            req_path.unlink(missing_ok=True)
        except OSError:
            pass
        return True

    def drain(self) -> None:
        """Unblock every outstanding request with an empty (=continue) answer.

        Called on teardown so no plugin worker hangs on its FIFO if the run ends
        (Ctrl+C, crash, normal exit) while a request is pending.
        """
        for req_path in self._pending():
            stem = req_path.stem
            self._answer(stem, "")
            self._handled.add(stem)
            try:
                req_path.unlink(missing_ok=True)
            except OSError:
                pass
