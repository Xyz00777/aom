"""Pure run-duration projection — covered-prior-work + live pace.

``project_remaining`` turns "how much of the prior run's wall-clock have
we covered" plus "how long that took us" into a remaining-time estimate,
with a warmup gate and a pace clamp so first runs and diverged playbooks
degrade to "no estimate" rather than garbage.
"""

from __future__ import annotations

from ansible_aom.core.estimate import (
    RunEstimate,
    covered_prior_s,
    in_flight_credit_s,
    project_remaining,
)


def _est(task_wall: dict[str, float]) -> RunEstimate:
    return RunEstimate(task_wall_s=task_wall, prior_wall_total_s=sum(task_wall.values()))


# --- covered_prior_s -------------------------------------------------------


def test_covered_sums_matched_paths_and_counts_them() -> None:
    est = _est({"a.yml:1": 10.0, "a.yml:2": 20.0, "a.yml:3": 30.0})
    done, matched = covered_prior_s(est, ["a.yml:1", "a.yml:3"])
    assert done == 40.0
    assert matched == 2


def test_covered_ignores_unmatched_paths() -> None:
    est = _est({"a.yml:1": 10.0})
    done, matched = covered_prior_s(est, ["a.yml:1", "new.yml:99"])
    assert done == 10.0
    assert matched == 1  # the unmatched path is not counted


def test_covered_adds_per_occurrence_average_each_time() -> None:
    # A recurring path stores a per-occurrence average; each completion
    # adds it again.
    est = _est({"role.yml:1": 5.0})
    done, matched = covered_prior_s(est, ["role.yml:1", "role.yml:1"])
    assert done == 10.0
    assert matched == 2


# --- project_remaining: gates ---------------------------------------------


def test_no_prior_returns_none() -> None:
    est = RunEstimate(task_wall_s={}, prior_wall_total_s=0.0)
    assert project_remaining(est, done_prior_s=0.0, matched_tasks=0, elapsed_s=5.0) is None


def test_warmup_min_tasks_gate() -> None:
    est = _est({f"a.yml:{i}": 10.0 for i in range(10)})  # total 100
    # 1 matched task, 10% covered — fails the min-tasks gate.
    assert project_remaining(est, done_prior_s=10.0, matched_tasks=1, elapsed_s=10.0) is None


def test_warmup_fraction_gate() -> None:
    est = _est({f"a.yml:{i}": 10.0 for i in range(10)})  # total 100
    # 2 matched but only 5% of prior wall covered — fails the fraction gate.
    assert project_remaining(est, done_prior_s=5.0, matched_tasks=2, elapsed_s=5.0) is None


def test_gates_open_returns_estimate() -> None:
    est = _est({f"a.yml:{i}": 10.0 for i in range(10)})  # total 100
    # 2 matched, 20% covered, on-pace (elapsed == done_prior).
    remaining = project_remaining(est, done_prior_s=20.0, matched_tasks=2, elapsed_s=20.0)
    assert remaining == 80.0  # pace 1.0 × (100 - 20)


# --- project_remaining: pace --------------------------------------------


def test_fast_rerun_shrinks_remaining() -> None:
    est = _est({f"a.yml:{i}": 10.0 for i in range(10)})  # total 100
    # Covered 50 of prior wall in only 10s → pace 0.2 → remaining halves of half.
    remaining = project_remaining(est, done_prior_s=50.0, matched_tasks=5, elapsed_s=10.0)
    assert remaining == 0.2 * 50.0  # 10.0


def test_pace_clamped_low() -> None:
    est = _est({f"a.yml:{i}": 10.0 for i in range(10)})  # total 100
    # Absurdly fast (pace would be 0.01) → clamped to 0.2.
    remaining = project_remaining(est, done_prior_s=50.0, matched_tasks=5, elapsed_s=0.5)
    assert remaining == 0.2 * 50.0


def test_pace_clamped_high() -> None:
    est = _est({f"a.yml:{i}": 10.0 for i in range(10)})  # total 100
    # Far slower than prior (pace would be 20) → clamped to 5.0.
    remaining = project_remaining(est, done_prior_s=50.0, matched_tasks=5, elapsed_s=1000.0)
    assert remaining == 5.0 * 50.0


def test_remaining_never_negative() -> None:
    est = _est({"a.yml:1": 10.0, "a.yml:2": 10.0})  # total 20
    # Covered more than total (new tasks pushed done_prior past prior) —
    # remaining floors at 0 rather than going negative.
    remaining = project_remaining(est, done_prior_s=25.0, matched_tasks=2, elapsed_s=25.0)
    assert remaining == 0.0


# --- in_flight_credit_s ----------------------------------------------------


def test_in_flight_credit_sums_min_of_elapsed_and_prior() -> None:
    est = _est({"long.yml:1": 80.0, "mid.yml:1": 30.0})
    # long has run 40s (< its 80s prior) → credit 40; mid has run 50s
    # (> its 30s prior) → credit caps at 30.
    credit = in_flight_credit_s(est, [("long.yml:1", 40.0), ("mid.yml:1", 50.0)])
    assert credit == 70.0


def test_in_flight_credit_ignores_unknown_paths() -> None:
    est = _est({"long.yml:1": 80.0})
    credit = in_flight_credit_s(est, [("long.yml:1", 10.0), ("new.yml:9", 99.0)])
    assert credit == 10.0


def test_in_flight_credit_floors_negative_elapsed() -> None:
    est = _est({"long.yml:1": 80.0})
    # Clock skew shouldn't produce negative credit.
    assert in_flight_credit_s(est, [("long.yml:1", -5.0)]) == 0.0


# --- project_remaining: in-flight credit (the long-task burn-down) ---------


def test_long_running_task_burns_down_instead_of_inflating() -> None:
    # 4 short (5s) + 1 long (80s) = 100s prior; long task runs last.
    est = RunEstimate(
        task_wall_s={"s1": 5.0, "s2": 5.0, "s3": 5.0, "s4": 5.0, "long": 80.0},
        prior_wall_total_s=100.0,
    )
    done_prior = 20.0  # all four short tasks completed
    # The long task runs; on pace its run-elapsed == time past the short
    # tasks, so covered == elapsed and remaining burns down 80 → 0.
    for run_elapsed, expected in [(0.0, 80.0), (20.0, 60.0), (40.0, 40.0), (80.0, 0.0)]:
        credit = in_flight_credit_s(est, [("long", run_elapsed)])
        elapsed = done_prior + run_elapsed  # on pace
        remaining = project_remaining(
            est,
            done_prior_s=done_prior,
            matched_tasks=4,
            elapsed_s=elapsed,
            in_flight_credit_s=credit,
        )
        assert remaining == expected


def test_in_flight_credit_does_not_open_warmup_gate() -> None:
    est = _est({f"a.yml:{i}": 10.0 for i in range(10)})  # total 100
    # Only 1 completed task, but a big in-flight credit — the gate is on
    # *completed* work, so this still returns None.
    remaining = project_remaining(
        est,
        done_prior_s=10.0,
        matched_tasks=1,
        elapsed_s=10.0,
        in_flight_credit_s=40.0,
    )
    assert remaining is None


def test_in_flight_credit_capped_at_total_floors_remaining() -> None:
    est = _est({"a.yml:1": 10.0, "long": 30.0})  # total 40
    # done 10, long task overran (credit caps at its 30 prior) → covered 40
    # == total → remaining floors at 0 even while the task still runs.
    remaining = project_remaining(
        est,
        done_prior_s=10.0,
        matched_tasks=1 + 1,
        elapsed_s=200.0,
        in_flight_credit_s=30.0,
    )
    assert remaining == 0.0
