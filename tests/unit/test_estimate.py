"""Pure run-duration projection — result-segmented covered-prior-work.

Prior wall splits into a *fixed* floor (tasks that were ok/skipped last run
— empirically ~constant) and a *variable* part (tasks that were changed —
where all the run-to-run variance lives). The fixed floor is projected
unscaled; the variable part is scaled by a work-pace measured only from
the variable tasks' actual-vs-prior wall.
"""

from __future__ import annotations

from ansible_aom.core.estimate import (
    RunEstimate,
    RunProgress,
    add_completed,
    add_in_flight,
    project_remaining,
)


def _est(
    fixed: dict[str, float] | None = None,
    variable: dict[str, float] | None = None,
) -> RunEstimate:
    fixed = fixed or {}
    variable = variable or {}
    task_wall = {**fixed, **variable}
    return RunEstimate(
        task_wall_s=task_wall,
        variable_paths=frozenset(variable),
        prior_wall_total_s=sum(task_wall.values()),
        prior_var_total_s=sum(variable.values()),
    )


# --- RunEstimate -----------------------------------------------------------


def test_fixed_total_is_total_minus_variable() -> None:
    est = _est(fixed={"a": 10.0}, variable={"b": 30.0})
    assert est.prior_fixed_total_s == 10.0
    assert est.is_variable("b") is True
    assert est.is_variable("a") is False


# --- add_completed accumulation -------------------------------------------


def test_add_completed_buckets_by_prior_result() -> None:
    est = _est(fixed={"ok1": 5.0}, variable={"ch1": 20.0})
    prog = RunProgress()
    add_completed(est, prog, "ok1", actual_wall_s=4.0)
    add_completed(est, prog, "ch1", actual_wall_s=8.0)
    assert prog.covered_fixed_s == 5.0
    assert prog.covered_var_s == 20.0  # prior wall, not actual
    assert prog.var_actual_s == 8.0  # actual wall of the variable task
    assert prog.completed_covered_s == 25.0
    assert prog.matched_tasks == 2


def test_add_completed_ignores_unmatched_path() -> None:
    est = _est(fixed={"ok1": 5.0})
    prog = RunProgress()
    add_completed(est, prog, "new.yml:9", actual_wall_s=3.0)
    assert prog.matched_tasks == 0
    assert prog.completed_covered_s == 0.0


def test_add_completed_fixed_task_does_not_touch_var_actual() -> None:
    est = _est(fixed={"ok1": 5.0})
    prog = RunProgress()
    add_completed(est, prog, "ok1", actual_wall_s=99.0)
    assert prog.var_actual_s == 0.0


# --- add_in_flight (does not advance the gate) -----------------------------


def test_add_in_flight_credits_variable_bucket_and_actual() -> None:
    est = _est(variable={"long": 80.0})
    prog = RunProgress()
    add_in_flight(est, prog, "long", run_elapsed_s=40.0)
    assert prog.covered_var_s == 40.0  # min(40, 80)
    assert prog.var_actual_s == 40.0
    assert prog.completed_covered_s == 0.0  # in-flight never advances the gate
    assert prog.matched_tasks == 0


def test_add_in_flight_caps_credit_at_prior_but_not_actual() -> None:
    est = _est(variable={"long": 80.0})
    prog = RunProgress()
    add_in_flight(est, prog, "long", run_elapsed_s=120.0)  # overrun
    assert prog.covered_var_s == 80.0  # credit capped at prior wall
    assert prog.var_actual_s == 120.0  # actual is the real (over)time


def test_add_in_flight_fixed_task_credits_floor_only() -> None:
    est = _est(fixed={"chk": 5.0})
    prog = RunProgress()
    add_in_flight(est, prog, "chk", run_elapsed_s=3.0)
    assert prog.covered_fixed_s == 3.0
    assert prog.var_actual_s == 0.0


# --- project_remaining: gates ---------------------------------------------


def test_no_prior_returns_none() -> None:
    est = _est()
    assert project_remaining(est, RunProgress()) is None


def test_warmup_min_tasks_gate() -> None:
    est = _est(fixed={f"a{i}": 10.0 for i in range(10)})  # total 100
    prog = RunProgress(completed_covered_s=10.0, covered_fixed_s=10.0, matched_tasks=1)
    assert project_remaining(est, prog) is None


def test_warmup_fraction_gate() -> None:
    est = _est(fixed={f"a{i}": 10.0 for i in range(10)})  # total 100
    prog = RunProgress(completed_covered_s=5.0, covered_fixed_s=5.0, matched_tasks=2)
    assert project_remaining(est, prog) is None


# --- project_remaining: the segmented model -------------------------------


def test_fixed_floor_projected_unscaled() -> None:
    # All fixed work; nothing variable. Remaining is just the uncovered
    # floor, never scaled — even though we've completed faster/slower.
    est = _est(fixed={f"a{i}": 10.0 for i in range(10)})  # total 100
    prog = RunProgress(completed_covered_s=20.0, covered_fixed_s=20.0, matched_tasks=2)
    assert project_remaining(est, prog) == 80.0


def test_variable_remainder_scaled_by_work_pace() -> None:
    # Fixed floor 40 (covered 40) + variable 60 (covered 20 so far, and that
    # 20 of prior variable work actually took only 10s → work_pace 0.5).
    est = _est(
        fixed={f"f{i}": 10.0 for i in range(4)},  # 40
        variable={f"v{i}": 20.0 for i in range(3)},  # 60
    )
    prog = RunProgress(
        completed_covered_s=60.0,
        covered_fixed_s=40.0,
        covered_var_s=20.0,
        var_actual_s=10.0,  # pace 0.5
        matched_tasks=5,
    )
    # rem_fixed = 0; rem_var_prior = 40; work_pace 0.5 → 20.
    assert project_remaining(est, prog) == 20.0


def test_fast_rerun_keeps_floor_but_collapses_variable() -> None:
    # site.yml-shaped: 20s fixed floor (constant), 174s prior variable work
    # that this run is blowing through at pace ~0.17.
    est = _est(fixed={"floor": 20.0}, variable={"work": 174.0})
    prog = RunProgress(
        completed_covered_s=20.0,  # floor done
        covered_fixed_s=20.0,
        covered_var_s=87.0,  # half the variable prior covered
        var_actual_s=15.0,  # ...in only 15s → pace ~0.17
        matched_tasks=2,
    )
    remaining = project_remaining(est, prog)
    # floor fully covered (rem_fixed 0) + 0.1724 × 87 ≈ 15.0
    assert remaining is not None
    assert 14.0 < remaining < 16.0


def test_work_pace_defaults_to_one_before_any_variable_completes() -> None:
    est = _est(fixed={"f1": 20.0, "f2": 20.0}, variable={"v1": 60.0})  # total 100
    prog = RunProgress(completed_covered_s=40.0, covered_fixed_s=40.0, matched_tasks=2)
    # No variable work measured yet → assume on-pace (×1): rem_var = 60.
    assert project_remaining(est, prog) == 60.0


def test_work_pace_clamped_low() -> None:
    est = _est(fixed={"f": 10.0}, variable={"v1": 45.0, "v2": 45.0})  # total 100
    prog = RunProgress(
        completed_covered_s=55.0,
        covered_fixed_s=10.0,
        covered_var_s=45.0,
        var_actual_s=0.1,  # pace 0.0022 → clamped to floor 0.05
        matched_tasks=2,
    )
    # rem_fixed 0 + clamp(0.05) × 45 = 2.25
    assert project_remaining(est, prog) == 45.0 * 0.05


def test_work_pace_clamped_high() -> None:
    est = _est(fixed={"f": 10.0}, variable={"v1": 45.0, "v2": 45.0})  # total 100
    prog = RunProgress(
        completed_covered_s=55.0,
        covered_fixed_s=10.0,
        covered_var_s=45.0,
        var_actual_s=900.0,  # pace 20 → clamped to ceiling 5.0
        matched_tasks=2,
    )
    assert project_remaining(est, prog) == 45.0 * 5.0


def test_remaining_never_negative() -> None:
    est = _est(fixed={"f1": 10.0, "f2": 10.0})  # total 20
    prog = RunProgress(completed_covered_s=25.0, covered_fixed_s=25.0, matched_tasks=2)
    assert project_remaining(est, prog) == 0.0
