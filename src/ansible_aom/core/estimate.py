"""Pure run-duration projection from a prior run's per-task profile.

The "Last run: N tasks in T" hint already tells the user a matching prior
session existed and how long it took. This module turns that prior into a
*live* remaining-time estimate.

Result-segmented model
----------------------
Empirically (measured across repeated real runs), a task's wall time splits
cleanly by its result:

- ``ok`` / ``skipped`` tasks are ~constant run-to-run — an idempotency
  check that finds nothing to do costs about the same every time. These
  form a *fixed floor*.
- ``changed`` (and failed/unreachable) tasks carry essentially all the
  run-to-run variance — they do the actual, variable work.

So we mine each prior task's wall AND whether it was variable, then project:

    remaining = (fixed_total − covered_fixed)              # unscaled floor
              + clamp(work_pace) × (var_total − covered_var)
    work_pace = Σ actual_wall(variable tasks done) / Σ prior_wall(same)

Scaling only the variable part by a pace measured only from variable tasks
avoids the classic failure of a single global pace: on a fast re-run (most
tasks ``ok``) a global pace would wrongly shrink the constant floor too.

Covered work accumulates as tasks complete (:func:`add_completed`) and is
topped up each render by in-flight tasks (:func:`add_in_flight`) so a long
running task burns the estimate down instead of inflating it. A warmup gate
(on *completed* work only) and the pace clamp keep first runs and diverged
playbooks degrading to "no estimate" rather than garbage.

Pure: no I/O, no global state. Lives in ``core/`` so both the compact
renderer and a future TUI can share one definition.
"""

from __future__ import annotations

from dataclasses import dataclass

# Clamp the observed work pace. The high bound stops a single anomalously
# slow task blowing the variable projection up. The low bound is loose (not
# the 0.2 a *global* pace would use) because the fixed floor is now projected
# separately — so a genuinely fast re-run, where variable tasks are cached
# and run near-instantly, can legitimately push the work pace well below 0.2.
# A small floor (not 0) just avoids predicting a literal zero from early noise.
_PACE_MIN = 0.05
_PACE_MAX = 5.0

# Warmup gate: emit no estimate until the run has *completed* at least this
# fraction of the prior wall-clock AND this many tasks that matched the prior
# profile. Confidence comes from finished tasks; an in-flight credit can
# refine an estimate but never trips the gate open on its own.
_WARMUP_FRACTION = 0.10
_WARMUP_MIN_TASKS = 2


@dataclass(frozen=True)
class RunEstimate:
    """Per-task wall-time profile mined from a matching prior run.

    ``task_wall_s`` maps a task ``path`` to its per-occurrence average wall
    duration. ``variable_paths`` is the subset whose prior result was
    ``changed`` (or failed/unreachable) — the rest are the fixed floor.
    ``prior_wall_total_s`` is the sum of every mined inter-task delta;
    ``prior_var_total_s`` is the portion attributable to variable paths. An
    empty profile / zero total means "no usable prior" and
    :func:`project_remaining` returns ``None``.
    """

    task_wall_s: dict[str, float]
    variable_paths: frozenset[str]
    prior_wall_total_s: float
    prior_var_total_s: float

    @property
    def prior_fixed_total_s(self) -> float:
        return max(self.prior_wall_total_s - self.prior_var_total_s, 0.0)

    def is_variable(self, path: str) -> bool:
        return path in self.variable_paths


@dataclass
class RunProgress:
    """Mutable covered-work accumulators for the live run.

    ``covered_fixed_s`` / ``covered_var_s`` are the prior wall covered so far,
    bucketed by each task's *prior* result. ``var_actual_s`` is the actual
    wall spent on variable-prior tasks (the work-pace numerator).
    ``completed_covered_s`` and ``matched_tasks`` count *completed* work only
    and drive the warmup gate — in-flight top-ups deliberately don't touch
    them.
    """

    covered_fixed_s: float = 0.0
    covered_var_s: float = 0.0
    var_actual_s: float = 0.0
    completed_covered_s: float = 0.0
    matched_tasks: int = 0

    def copy(self) -> RunProgress:
        return RunProgress(
            covered_fixed_s=self.covered_fixed_s,
            covered_var_s=self.covered_var_s,
            var_actual_s=self.var_actual_s,
            completed_covered_s=self.completed_covered_s,
            matched_tasks=self.matched_tasks,
        )


def add_completed(
    estimate: RunEstimate, progress: RunProgress, path: str, actual_wall_s: float
) -> None:
    """Fold a just-completed task into ``progress`` by its prior bucket.

    A path absent from the prior profile (new/edited task) is ignored — it
    contributes nothing and is not counted as matched. Variable-prior tasks
    record both their prior wall (covered) and this run's actual wall (the
    work-pace numerator); fixed-prior tasks record prior wall only.
    """
    wall = estimate.task_wall_s.get(path)
    if wall is None:
        return
    progress.matched_tasks += 1
    progress.completed_covered_s += wall
    if estimate.is_variable(path):
        progress.covered_var_s += wall
        progress.var_actual_s += max(actual_wall_s, 0.0)
    else:
        progress.covered_fixed_s += wall


def add_in_flight(
    estimate: RunEstimate, progress: RunProgress, path: str, run_elapsed_s: float
) -> None:
    """Top up ``progress`` with a still-running task's partial progress.

    Credits ``min(run_elapsed, prior_wall)`` to the covered bucket — capped
    at the prior duration so an overrun counts against the work pace rather
    than masking it — and the full ``run_elapsed`` to ``var_actual_s`` for
    variable tasks. Never advances ``completed_covered_s`` / ``matched_tasks``
    (the gate is on completed work). Unknown paths contribute nothing.
    """
    wall = estimate.task_wall_s.get(path)
    if wall is None:
        return
    run_elapsed = max(run_elapsed_s, 0.0)
    credit = min(run_elapsed, wall)
    if estimate.is_variable(path):
        progress.covered_var_s += credit
        progress.var_actual_s += run_elapsed
    else:
        progress.covered_fixed_s += credit


def project_remaining(estimate: RunEstimate, progress: RunProgress) -> float | None:
    """Project remaining wall-clock seconds, or ``None`` if not estimable.

    ``None`` for: no usable prior profile, or the warmup window (too few
    completed matched tasks / too little completed prior wall).

    Otherwise the uncovered fixed floor is added unscaled to the uncovered
    variable work scaled by the clamped work pace (``var_actual /
    covered_var``, defaulting to 1.0 before any variable task is measured).
    Both remainders floor at 0.
    """
    if estimate.prior_wall_total_s <= 0:
        return None
    if progress.matched_tasks < _WARMUP_MIN_TASKS:
        return None
    if progress.completed_covered_s < _WARMUP_FRACTION * estimate.prior_wall_total_s:
        return None

    rem_fixed = max(estimate.prior_fixed_total_s - progress.covered_fixed_s, 0.0)
    rem_var = max(estimate.prior_var_total_s - progress.covered_var_s, 0.0)

    if progress.covered_var_s > 0:
        work_pace = progress.var_actual_s / progress.covered_var_s
        work_pace = min(max(work_pace, _PACE_MIN), _PACE_MAX)
    else:
        # No variable work measured yet — assume this run matches the prior.
        work_pace = 1.0

    return rem_fixed + work_pace * rem_var
