## 2026-04-24 Potential Issues (all resolved as of 2026-05-11)

1. TUI widgets inheriting Textual classes need Textual installed and importable
   → **Resolved** — Textual ≥0.60 in pyproject.toml dependencies.
2. Rich Live display needs proper context manager lifecycle in compact/renderer.py
   → **Resolved** — replaced with direct ANSI cursor positioning (2026-05-08).
3. Signal handling in compact mode needs careful subprocess management
   → **Resolved** — runner.py handles KeyboardInterrupt + SIGINT via pexpect
     `sendintr` + `close(force=True)` (2026-05-10).
4. Password pass-through needs pexpect mocking in tests
   → **Resolved** — TC-143 through TC-148 fully covered in
     `tests/compact/test_password.py` (2026-05-08).
5. Some test functions use `pass` placeholder for complex integration tests
   → **Resolved** — all stubs replaced with real implementations.
6. tui/app.py needs to satisfy Renderer Protocol
   → **Resolved** — AOMApp implements full Renderer Protocol + worker-driven
     playbook execution (2026-05-11).

## 2026-05-23 Open issues

7. **Fallback host leaves default to Status.RUNNING** — when a task finishes
   but `runtime.hosts` is empty (implicit tasks like `meta: flush_handlers`),
   the fallback path creates host leaves with running spinners instead of the
   final status. Root cause: ansible doesn't emit `v2_runner_on_ok` for
   implicit tasks.
   → **Partially mitigated** 2026-05-24: sticky fallback (`_last_running_play_id`)
     keeps the active play visible instead of bouncing to completed plays,
     so this only manifests during brief transition windows. Still not fully fixed.

## 2026-05-24 Open issues

8. **Push blocked** — remote `git.eisen5.eu:2222` connection refused.
   11 unpushed commits on `feat/nom-compact-renderer` (7 from May 23 + 4 from May 24).
9. **Strategy detection is post-hoc** — The strategy is assumed "linear" until
    `v2_runner_on_start` fires, which flips it to "free". But by then the
    playbook may have already emitted tasks with wrong force-completion behavior.
    If the playbook has zero `runner_on_start` events (all tasks in lockstep),
    strategy stays "linear" which is arguably correct. Edge case: a playbook
    that starts in linear mode but switches to free mid-run would have wrong
    completions for the linear portion.
    → **Acceptable trade-off**: The JSONL callback only emits runner_on_start
      when NOT in lockstep, so the flip is actually a detection of linear vs free.
      No known playbook switches strategy mid-run.

10. **Projection reset can still flip the active play on a gap frame** —
    `CompactRenderer.update_state()` currently clears `_projection` on every
    event, so a gap frame after an active play completes can lose
    `TreeProjection._last_running_play_id` and reselect the later completed
    play. The new regression test in
    `tests/compact/test_tree_projection_lifecycle.py::test_perf_022_update_state_keeps_sticky_active_play_on_gap_frame`
    pins this down with a two-play state (`active` vs `later`) and expects
    `play: active` to remain the only active play row.
11. **Duplicate play names still collapse in tree projection** —
    `TreeProjection` still joins runtime plays/definitions by `name`, so two
    executions with the same visible play name can surface the first play's
    task tree twice while hiding the second play's task surface entirely.
    Guarded by `tests/unit/test_tree_projection.py::TestTreeLinesPlayIdentity::test_duplicate_play_names_keep_both_executions_visible`.

12. **Same-name concurrent runtime tasks still collapse by display name** —
    `TreeProjection._play_running_and_pending()` keys runtime task surfaces by
    `task.name`, so two live task executions with different ids but the same
    visible label collapse into one task row. Guarded by
    `tests/unit/test_tree_projection.py::TestTreeLinesTaskIdentity::test_same_name_concurrent_tasks_stay_separate`.
