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

from typing import Literal

from pydantic import BaseModel


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
