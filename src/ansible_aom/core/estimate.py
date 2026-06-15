"""Pure run-duration projection from a prior run's per-task profile.

The "Last run: N tasks in T" hint already tells the user a matching prior
session existed and how long it took. This module turns that prior into a
*live* remaining-time estimate using a covered-prior-work model:

    covered    = Σ prior_wall[path] for completed tasks   (done_prior)
               + Σ min(run_elapsed, prior_wall[path]) for in-flight tasks
    pace_ratio = elapsed / covered               # <1 ⇒ faster than last time
    remaining  = pace_ratio × (prior_wall_total_s − covered)

Accumulating *covered* prior work (rather than matching the upcoming task
list, which ``--list-tasks`` can't reliably enumerate) makes the model
self-correcting: a big task completing jumps ``covered`` a lot, and a task
skipped this run that ran for 30 s last run advances ``covered`` by ~30 s
while ``elapsed`` barely moves — so the pace ratio drops and the ETA shrinks
honestly. Crucially, in-flight tasks are credited too (capped at their prior
duration): without that, a long-running task would freeze ``covered`` while
``elapsed`` climbed, inflating the estimate instead of burning it down.

Robustness lives in :func:`project_remaining`: a warmup gate suppresses the
noisy early window and a clamp bounds the pace ratio, so a first run (no
prior) or a diverged playbook (shifted task paths → few matches) degrades
to "no estimate" rather than an absurd number.

Pure: no I/O, no global state. Lives in ``core/`` so both the compact
renderer and a future TUI can share one definition.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

# Clamp the observed pace ratio so a diverged playbook (few path matches →
# tiny ``done_prior``) can't blow the ETA up, and an all-cached run can't
# collapse it to ~0 either.
_PACE_MIN = 0.2
_PACE_MAX = 5.0

# Warmup gate: emit no estimate until the run has covered at least this
# fraction of the prior wall-clock AND completed at least this many tasks
# that matched the prior profile. Below either threshold the pace ratio is
# too noisy to trust.
_WARMUP_FRACTION = 0.10
_WARMUP_MIN_TASKS = 2


@dataclass(frozen=True)
class RunEstimate:
    """Per-task wall-time profile mined from a matching prior run.

    ``task_wall_s`` maps a task ``path`` to its per-occurrence average
    wall-clock duration; ``prior_wall_total_s`` is the sum of every mined
    inter-task delta (so ``done_prior`` reaches it exactly when every prior
    task has re-run). An empty profile / zero total means "no usable prior"
    and :func:`project_remaining` returns ``None``.
    """

    task_wall_s: dict[str, float]
    prior_wall_total_s: float


def covered_prior_s(estimate: RunEstimate, completed_paths: Iterable[str]) -> tuple[float, int]:
    """Sum per-occurrence prior wall for ``completed_paths``.

    Returns ``(done_prior_s, matched_tasks)``. A completed path absent from
    the prior profile (a new or edited task) contributes 0 and is not
    counted as matched — that under-counts progress on a diverged playbook,
    which the warmup gate then refuses to estimate from.
    """
    done = 0.0
    matched = 0
    for path in completed_paths:
        wall = estimate.task_wall_s.get(path)
        if wall is None:
            continue
        done += wall
        matched += 1
    return done, matched


def in_flight_credit_s(estimate: RunEstimate, running: Iterable[tuple[str, float]]) -> float:
    """Prior wall already covered by *currently running* tasks.

    ``running`` is ``(path, running_elapsed_s)`` per in-flight task. Each
    contributes ``min(running_elapsed, prior_wall[path])`` — we credit the
    task's progress up to its known prior duration, but no further, so that
    an overrun (the task taking longer than last time) counts against the
    pace ratio rather than masking it. Unknown paths (new/edited tasks)
    contribute 0; negative elapsed (clock skew) floors at 0.
    """
    total = 0.0
    for path, run_elapsed in running:
        wall = estimate.task_wall_s.get(path)
        if wall is None:
            continue
        total += min(max(run_elapsed, 0.0), wall)
    return total


def project_remaining(
    estimate: RunEstimate,
    done_prior_s: float,
    matched_tasks: int,
    elapsed_s: float,
    in_flight_credit_s: float = 0.0,
) -> float | None:
    """Project remaining wall-clock seconds, or ``None`` if not estimable.

    ``None`` is returned for: no usable prior profile, the warmup window
    (too few matched tasks or too little *completed* prior wall covered),
    and the defensive ``covered <= 0`` case.

    Otherwise the run's covered prior wall is ``done_prior + in-flight
    credit`` (the latter crediting the *currently running* tasks against
    their prior duration so a long task burns the estimate down instead of
    inflating it — see :func:`in_flight_credit_s`), capped at the prior
    total. The pace ratio (``elapsed / covered``) is clamped to
    ``[0.2, 5.0]`` and applied to the uncovered prior wall; the result
    floors at 0 (a run that overran its prior shows "0s left", not a
    negative).

    The warmup gate is deliberately checked against ``done_prior_s`` alone
    — confidence comes from *completed* tasks, so an in-flight credit can
    refine an estimate but never trip the gate open on its own.
    """
    if estimate.prior_wall_total_s <= 0:
        return None
    if matched_tasks < _WARMUP_MIN_TASKS:
        return None
    if done_prior_s < _WARMUP_FRACTION * estimate.prior_wall_total_s:
        return None
    covered = min(done_prior_s + in_flight_credit_s, estimate.prior_wall_total_s)
    if covered <= 0:
        return None
    pace = elapsed_s / covered
    pace = min(max(pace, _PACE_MIN), _PACE_MAX)
    remaining = pace * (estimate.prior_wall_total_s - covered)
    return max(remaining, 0.0)
