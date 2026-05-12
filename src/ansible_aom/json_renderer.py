"""JSON output renderer for AOM (F6).

Implements the Renderer Protocol but produces no streaming output.
On completion, emits a single JSON object to stdout that summarises
the run — playbook, exit code, host counts, failed tasks, timing.

Designed for CI and `jq` pipelines: no ANSI, no progress bars, no
interactive prompts. If ansible asks for a password mid-run, this
renderer refuses on stderr rather than blocking forever.

Schema is pinned by the ``RunSummary`` Pydantic model below; the
``schema_version`` field is a ``Literal[1]`` so accidental drift
shows up at construction time.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel

if TYPE_CHECKING:
    from ansible_aom.core.models import RunState


class HostCounts(BaseModel):
    """Per-host status counts aggregated across every task in every play."""

    ok: int = 0
    changed: int = 0
    failed: int = 0
    unreachable: int = 0


class TaskFailure(BaseModel):
    """One (host, task) pair that ended in FAILED or UNREACHABLE."""

    host: str
    task: str
    msg: str


class RunSummary(BaseModel):
    """End-of-run summary emitted by ``JsonRenderer.handle_completion``.

    Field rules:

    - ``schema_version``: literal ``1``. Bump only on breaking change.
    - ``playbook``: the path passed to ``start()``.
    - ``exit_code``: ``determine_exit_code(state)``.
    - ``started_at`` / ``ended_at``: ISO 8601 with UTC offset.
    - ``duration_s``: float seconds, rounded to 1 dp.
    - ``hosts``: every host that ever produced a result, exactly once.
    - ``tasks_failed``: one entry per (host, task) pair that failed
      or went unreachable. ``msg`` may be the empty string.
    """

    schema_version: Literal[1]
    playbook: str
    exit_code: int
    started_at: str
    ended_at: str
    duration_s: float
    hosts: dict[str, HostCounts]
    tasks_failed: list[TaskFailure]


# =============================================================================
# JsonRenderer
# =============================================================================


class JsonRenderer:
    """End-of-run JSON renderer satisfying the Renderer Protocol.

    Silent during the run; emits a single JSON object on
    ``handle_completion``. Interactive prompts are refused to stderr —
    JSON mode is for non-interactive consumers.
    """

    def __init__(self) -> None:
        self._playbook: str = ""
        self._args: list[str] = []
        self._definitions: list = []
        self._state: RunState | None = None
        self._wall_start: float = 0.0
        self._wall_end: float = 0.0

    def start(self, playbook: str, args: list[str]) -> None:
        """Capture playbook + args; initialise empty RunState. No output."""
        import time

        from ansible_aom.core.models import RunState

        self._playbook = playbook
        self._args = list(args)
        self._state = RunState(playbook=playbook)
        self._wall_start = time.time()

    def set_definitions(self, definitions: list) -> None:
        """Store preflight definitions. No output."""
        self._definitions = list(definitions)

    def update_state(self, event: dict) -> None:
        """Drive RunState from a JSONL event. No output."""
        if self._state is None:
            return
        self._state.handle_event(event)

    def add_warning(self, message: str, is_deprecation: bool = False) -> None:
        """No-op — warnings aren't part of the v1 schema."""
        return

    def print_log(self, message: str) -> None:
        """No-op — JSON mode produces no streaming output."""
        return

    def tick(self) -> None:
        """No-op — no clock to refresh."""
        return

    def handle_password_prompt(self, prompt_text: str) -> str:
        """Refuse on stderr; return empty so ansible fails the auth attempt."""
        import sys

        sys.stderr.write("aom: --format json cannot answer interactive prompt; refusing.\n")
        sys.stderr.flush()
        return ""

    def handle_interactive_prompt(self, prompt_text: str) -> str:
        """Refuse on stderr; return empty so the playbook proceeds without input."""
        import sys

        sys.stderr.write("aom: --format json cannot answer interactive prompt; refusing.\n")
        sys.stderr.flush()
        return ""

    def handle_completion(self, exit_code: int, state: str) -> None:
        """Emit the JSON summary. Filled in by Task 3."""
        return

    def stop(self) -> None:
        """No-op — no display to tear down."""
        return
