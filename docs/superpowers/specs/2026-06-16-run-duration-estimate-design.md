# Run-duration estimate (ETA) — design

**Date:** 2026-06-16
**Status:** Approved, ready for implementation
**Branch:** `feat/nom-compact-renderer`

## Problem

We already surface a "Last run: N tasks in T (D ago)" hint from the most
recent matching completed session (see `session/history.py` →
`PriorRun`). That same prior session knows how long it took — so we can
project a live **remaining-time** estimate during the current run.

It will not be as accurate as a purpose-built progress model — a *first*
run has no prior, and a much-faster second run (everything cached/skipped)
diverges from the prior pace. But for the common "roughly normal" re-run
it's a major glanceability win, and the failure modes degrade to "show
nothing", never "show garbage".

## Chosen model: per-task profile + live pace (self-correcting)

Rather than scale a flat total by task-count fraction (wrong — tasks are
wildly uneven in wall time), we mine **per-task wall durations** from the
prior session and track how much of that prior wall-clock the current run
has *covered*, then scale the remainder by the observed pace.

```
done_prior   = Σ task_wall_s[path]  for every task path completed so far
pace_ratio   = elapsed / done_prior            # <1 ⇒ faster than last time
remaining    = pace_ratio × (prior_wall_total_s − done_prior)
```

Why this formulation (covered-work accumulation) rather than matching the
*upcoming* task list:

- We never have to predict upcoming tasks (`--list-tasks` doesn't expand
  `include_tasks`, so we couldn't reliably anyway).
- Uneven tasks are handled intrinsically: completing a big task jumps
  `done_prior` a lot.
- Skips self-correct: a task skipped this run that ran for 30 s last run
  advances `done_prior` by ~30 s while `elapsed` barely moves →
  `pace_ratio` drops → ETA shrinks. Correct.
- New/edited tasks whose paths don't match the prior map contribute 0 to
  `done_prior` → graceful underestimate of progress, absorbed partly by
  `pace_ratio`, and bounded by the clamp (below).

## Robustness: warmup gate + clamp

Early in a run `done_prior` is tiny, so `pace_ratio` is noisy; a diverged
playbook (shifted task paths → few/no matches) could push `done_prior ≈ 0`
and blow the ETA up. Guards:

- **Warmup gate** — emit no estimate until `done_prior ≥ 10% ×
  prior_wall_total_s` AND `matched_tasks ≥ 2`. If paths never match
  (edited playbook), the gate never opens → stays on today's elapsed-only
  bar forever.
- **Pace clamp** — `pace_ratio` clamped to `[0.2, 5.0]` so a diverged run
  can't show absurd values.
- **No usable prior** — `prior_wall_total_s ≤ 0` (first run, or pre-mining
  session) → estimate is `None` → status bar unchanged.

## Architecture & layering

| Layer | File | Change |
|-------|------|--------|
| core (pure) | `core/estimate.py` *(new)* | `RunEstimate`, `covered_prior_s`, `project_remaining` — projection math, no I/O |
| core (pure) | `core/duration.py` | reused as-is (`format_duration_compact`) |
| session (I/O) | `session/history.py` | mine per-task wall durations into `PriorRun`, same `events.jsonl` pass as `loop_totals` |
| infra | `compact/renderer.py` | accumulate covered prior work on task completion; call projector; feed status bar |
| infra | `compact/format.py` | `format_status_bar` gains `remaining_seconds: float \| None` |

Pure math in `core/`; mutable accumulation in the renderer (mirrors the
existing `_tasks_completed` / `_completed_task_ids` counters). `core/`
imports nothing from `compact/`.

## Data: mining prior per-task wall durations

Extend the winning-session mine in `find_previous_run` (it already opens
`events.jsonl` once for `loop_totals`) with per-task wall timing:

- Walk events in order. On each `v2_playbook_on_task_start` with a
  `_timestamp` and `task.path`, the **previous** task's wall duration is
  `this_ts − prev_ts`; accumulate it under the previous task's path. Close
  the final task at `v2_playbook_on_stats` (`stats_ts − prev_ts`).
- A recurring path (role/include invoked twice) accumulates total +
  occurrence count; store the **per-occurrence average**
  `task_wall_s[path] = total / count`. `prior_wall_total_s = Σ all deltas`.
- Best-effort: missing/malformed events → empty map + `0.0` total (feature
  silently off), same pattern as `loop_totals`.

`PriorRun` gains two fields (both default-empty so old sessions are safe):

```python
task_wall_s: dict[str, float] = field(default_factory=dict)
prior_wall_total_s: float = 0.0
```

`prior_wall_total_s` (sum of inter-task deltas) is intentionally *separate*
from the existing `duration_seconds` used by the "Last run" hint: the mined
total excludes pre-first-task setup and post-last-task teardown, so the
ratio math stays internally consistent — `done_prior` reaches
`prior_wall_total_s` exactly when every prior task has re-run. No
`meta.json` schema bump.

## Projection (`core/estimate.py`)

```python
@dataclass(frozen=True)
class RunEstimate:
    task_wall_s: dict[str, float]      # per-occurrence avg, from PriorRun
    prior_wall_total_s: float

_PACE_MIN, _PACE_MAX = 0.2, 5.0
_WARMUP_FRACTION = 0.10
_WARMUP_MIN_TASKS = 2

def covered_prior_s(
    estimate: RunEstimate, completed_paths: Iterable[str]
) -> tuple[float, int]:
    """Sum per-occurrence priors for completed paths; return (done_prior, matched).

    A completed path absent from task_wall_s contributes 0 and is not
    counted as matched.
    """

def project_remaining(
    estimate: RunEstimate,
    done_prior_s: float,
    matched_tasks: int,
    elapsed_s: float,
) -> float | None:
    if estimate.prior_wall_total_s <= 0:
        return None
    if matched_tasks < _WARMUP_MIN_TASKS:
        return None
    if done_prior_s < _WARMUP_FRACTION * estimate.prior_wall_total_s:
        return None
    if done_prior_s <= 0:                      # defensive; gate above implies >0
        return None
    pace = elapsed_s / done_prior_s
    pace = min(max(pace, _PACE_MIN), _PACE_MAX)
    return max(pace * (estimate.prior_wall_total_s - done_prior_s), 0.0)
```

Renderer side: maintain `done_prior` + `matched_tasks` incrementally,
bumped on each terminal task event keyed by `task.path` (cheaper than
re-summing a set each render; mirrors `_completed_task_ids` guarding
double counts). On render, call `project_remaining(...)`; `None` → bar
unchanged.

## Display

`format_status_bar` gains `remaining_seconds: float | None = None`:

```
site.yml │ 5/47 tasks │ ⚠ 2 │ 0:05:23  ~1m40s left
```

- Rendered `f"~{format_duration_compact(remaining)} left"`, dimmed
  (`_DIM`), hugging the elapsed segment with a space — an annotation on
  it, like the liveness dot — not a pipe-separated peer counter.
- Omitted entirely when `None`. Width-safe: ≤12 chars (`~99h59m left`).

## Testing (TDD, failing-first)

- **Mining** (`session/history.py`): per-task wall = inter-`task_start`
  delta; final task closed at `on_stats`; recurring path averaged;
  malformed/missing events → empty + 0.0.
- **Projection** (`core/estimate.py`, pure): warmup gate (under fraction →
  None; under min-tasks → None); pace clamp at both ends; fast-rerun
  shrinks remaining; `prior_wall_total_s == 0` → None; `covered_prior_s`
  ignores unmatched paths and counts matched correctly.
- **Status bar** (`compact/format.py`): segment present/absent, dim wrap,
  ascii mode, width budget.
- **Renderer integration**: completion bumps `done_prior`; `None`
  projection leaves the bar untouched.

New `TEST_SPECIFICATION.md` cases to be allocated contiguous TC numbers
when implementing.

## Out of scope (YAGNI)

- ETA wall-clock-of-day display and elapsed/total framing (we chose
  remaining-time only).
- Per-host ETA, persisting a dedicated profile.json, or `meta.json`
  versioning — mining the existing event log is sufficient.
- TUI surfacing — compact renderer only for now (the status bar is the
  compact view's; TUI can adopt `project_remaining` later for free since
  it's pure `core`).
