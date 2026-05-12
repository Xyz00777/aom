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
        """Build the RunSummary from accumulated RunState and print as JSON.

        ``exit_code`` and ``state`` are accepted to satisfy the Protocol
        but the JSON output's ``exit_code`` field is recomputed from
        ``RunState`` via ``determine_exit_code`` — the Protocol exit_code
        is what the runner *thinks* it should be (often 0 on a clean
        subprocess exit even when JSONL says a host failed); the
        state-derived value is what `aom inspect` and humans agree with.
        """
        import sys
        import time
        from datetime import datetime, timezone

        from ansible_aom.compact.renderer import determine_exit_code
        from ansible_aom.core.models import RunState, Status

        self._wall_end = time.time()

        # Always produce a RunState so the schema is consistent on
        # preflight-only failures (where update_state never fired).
        run_state: RunState = (
            self._state if self._state is not None else RunState(playbook=self._playbook)
        )

        # Timestamps: prefer state-recorded times, fall back to wall clock.
        if run_state.start_time is not None:
            started_at = run_state.start_time.isoformat()
        else:
            started_at = datetime.fromtimestamp(self._wall_start, tz=timezone.utc).isoformat()

        if run_state.end_time is not None:
            ended_at = run_state.end_time.isoformat()
            duration = (
                (run_state.end_time - run_state.start_time).total_seconds()
                if run_state.start_time is not None
                else self._wall_end - self._wall_start
            )
        else:
            ended_at = datetime.fromtimestamp(self._wall_end, tz=timezone.utc).isoformat()
            duration = self._wall_end - self._wall_start

        duration_s = round(max(duration, 0.0), 1)

        # Aggregate per-host counts and collect failures in one pass.
        host_counts: dict[str, dict[str, int]] = {}
        failures: list[TaskFailure] = []

        for play in run_state.plays.values():
            for task in play.tasks.values():
                for hostname, host_state in task.hosts.items():
                    counts = host_counts.setdefault(
                        hostname,
                        {"ok": 0, "changed": 0, "failed": 0, "unreachable": 0},
                    )
                    if host_state.status == Status.OK:
                        counts["ok"] += 1
                    elif host_state.status == Status.CHANGED:
                        counts["changed"] += 1
                    elif host_state.status == Status.FAILED:
                        counts["failed"] += 1
                        failures.append(
                            TaskFailure(
                                host=hostname,
                                task=task.name,
                                msg=host_state.message or "",
                            )
                        )
                    elif host_state.status == Status.UNREACHABLE:
                        counts["unreachable"] += 1
                        failures.append(
                            TaskFailure(
                                host=hostname,
                                task=task.name,
                                msg=host_state.message or "",
                            )
                        )

        hosts = {name: HostCounts(**counts) for name, counts in host_counts.items()}

        summary = RunSummary(
            schema_version=1,
            playbook=self._playbook,
            exit_code=determine_exit_code(run_state),
            started_at=started_at,
            ended_at=ended_at,
            duration_s=duration_s,
            hosts=hosts,
            tasks_failed=failures,
        )

        sys.stdout.write(summary.model_dump_json())
        sys.stdout.write("\n")
        sys.stdout.flush()

    def stop(self) -> None:
        """No-op — no display to tear down."""
        return
