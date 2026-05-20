"""Inspect TUI app — stub.

The real three-pane implementation lands in later tasks. For now this is
just enough to import without crashing the CLI's lazy-import path; when
stdout is not a TTY the CLI never calls ``run()`` so the stub is invisible.
"""

from __future__ import annotations

from pathlib import Path


class InspectApp:
    """Stub. Replaced by a real Textual ``App`` in subsequent tasks."""

    def __init__(self, *, state_dir: Path, initial_session_id: str | None = None) -> None:
        self.state_dir = state_dir
        self.initial_session_id = initial_session_id

    def run(self) -> None:
        raise NotImplementedError("InspectApp is not yet implemented")
