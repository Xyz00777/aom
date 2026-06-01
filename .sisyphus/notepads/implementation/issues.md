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

## 2026-05-24 Verification notes

- The durable-projection / row-lease slice passed the targeted checks:
  `tests/unit/test_tree_projection.py`,
  `tests/compact/test_tree_projection_lifecycle.py`, and
  `tests/integration/test_replay_determinism.py`.
- A full-suite attempt (`uv run pytest tests/ -q`) still reports unrelated
  pre-existing failures in `tests/compact/test_inspect_text_golden.py`,
  `tests/integration/test_playbook_parser.py`, and
  `tests/integration/test_session.py`.
- The projection-reset gap issue is addressed by the new revision-aware cache
  refresh path; the old invalidation note above is now historical context.

## 2026-05-24 Async launcher / async-status identity gotcha

- Same-name async launcher and async-status tasks can look identical if the
  matcher only consults task names. Without `task.path`, the later async-status
  child grafts under the launcher branch and the tree order flips. The fix here
  was to key the task-definition lookup by `task.path` first, then fall back to
  name.

## 2026-05-24 Pyright import-resolution caveat

- Pyright in this workspace still reported `ansible_aom` imports as missing in
  `tests/unit/test_tree_classify_and_role_labels.py` until the file opted out
  of `reportMissingImports`; the directive keeps diagnostics clean without
  changing runtime behavior.

## 2026-05-24 Delegated task regression verification

- Focused delegated-task regression passed, and the touched Python files were
  diagnostics-clean after the path-aware task matching change.
- Full-suite status remained unchanged: 15 failures, 2583 passed, 18 skipped,
  with the same unrelated failures in `tests/compact/test_inspect_text_golden.py`,
  `tests/integration/test_playbook_parser.py`, and `tests/integration/test_session.py`.

## 2026-05-25 run_once / serial gotcha

- The JSONL stream does not appear to expose a stable batch discriminator by
  default, so repeated `run_once` executions under `serial` cannot be fixed by
  task name/path alone. The model needs an explicit batch/window key (or an
  equivalent play-execution discriminator) to avoid row reuse across batches.

## 2026-05-25 run_once / serial probe details

- Verified on ansible-core 2.20.4: `serial: 1` causes the play to emit multiple
  `v2_playbook_on_play_start` events with the same `play.id`/`play.path`.
- `v2_playbook_on_task_start` and `v2_runner_on_ok` keep the same `task.id`/
  `task.path` across batches; the runner payload only changes `hosts.*`.
- There is no explicit `batch` / `window` field in the JSONL event payload we
  probed, so path-based task identity alone is insufficient for batch reuse.
- The batch boundary is only observable via the repeated play-start event's
  `play.duration.start` timestamp.
- `v2_playbook_on_task_start` under linear strategy synthesizes all resolved
  hosts, so the serial-window regression probe should prefer
  `v2_runner_on_start`/`v2_runner_on_ok` when the goal is to isolate the
  window discriminator instead of host fan-out.

## 2026-05-25 Large-output stall probe

- Session `019e5c71-98c2-7000-8d73-47021467f5d4` looked like a frozen tree, but
  the diagnostics fit backlog/backpressure: `pty_bytes=2343117`,
  `pexpect_timeouts=247`, `events_received=196`, `stall_count_max=4`.
- The stall path is in `ansible/runner.py`: `_drive()` waits on newline/EOF/
  TIMEOUT, and only `_feed()` calls `PtyStreamParser.feed_line()` after a
  complete line is available. No newline means no JSONL event, no state update.
- Compact rendering is also intentionally rate-limited (`Display.update()` and
  `_render_status_panel()` both coalesce at ~250 ms), so a noisy PTY can make
  the tree *look* stale even while the child is still producing output.
- `TreeProjection` reuse is not the corruption point here: it refreshes caches
  on `RunState._tree_revision` changes, but normal task/host status updates are
  read live from the mutable state on each render.

- Final fix: `CompactRenderer.print_log()` now opportunistically calls the
  compact repaint path, and `Display.print_log()` no longer resets the shared
  status throttle. That keeps status/tree refresh cadence independent from log
  bursts, so long output storms can still surface fresh panel state at the
  normal 4 Hz ceiling.
- Buffer decision: the suspected parser/cache ceiling was **not** implicated.
  The session evidence still fits backlog/lag, so `MAX_LOG_LINES` and the JSONL
  carry cap remain unchanged and bounded.

## 2026-05-25 Session rotation tie-breaker

- `cleanup_old_sessions()` now uses `(start_time, session_dir.name)` as the
  sort key, so fallback-only directories with identical mtimes are pruned
  deterministically. This preserves `meta.json` start-time precedence while
  making coarse-filesystem cleanup stable.
