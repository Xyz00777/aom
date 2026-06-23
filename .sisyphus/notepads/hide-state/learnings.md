# hide-state Implementation Learnings

## Session: 2026-06-22 — log_filter.py creation

### Module Design

- **`VALID_STATES`**: `frozenset[str]` of `{"ok", "changed", "failed", "skipped", "unreachable"}`. Immutable, hashable — matches the project's preference for `frozenset` over `set` for constants.
- **`_EVENT_STATE_MAP`**: Private mapping from JSONL event type strings to the set of user-visible state names they represent. Key design decision: `v2_runner_on_ok` and `v2_runner_item_on_ok` map to `{"ok", "changed"}` because ansible emits the same event type for both — the `changed` distinction lives inside the host result dict's `changed` field, not in the event type.
- **`normalize_hide_states`**: Lowercases, deduplicates, validates against `VALID_STATES`, separates unknowns. Returns `(frozenset, list)` — always both, never `None`. Unknown values preserve first-encounter order.
- **`should_hide_event`**: Uses `frozenset.isdisjoint()` for O(1) lookup. Non-runner events (anything not in `_EVENT_STATE_MAP`) always return `False`.

### Test Patterns

- 34 tests total: 10 for `normalize_hide_states`, 24 for `should_hide_event`.
- Class-based organization (`TestNormalizeHideStates`, `TestShouldHideEvent`) matching `test_cli.py` style.
- Section comments (`# --- v2_runner_on_ok ---`) for grouping related tests in a large file.
- Tested edge cases: empty input, case insensitivity, deduplication, unknown values, order preservation, iterable acceptance (generators), empty event type string, multiple hide states.

### Verification Results

- `uv run pytest tests/unit/test_log_filter.py -q`: 34 passed
- `uv run pytest tests/unit/ -q`: 1740 passed (full unit suite, no regressions)
- `uv run ruff format`: 1 file reformatted (log_filter.py), test file unchanged
- `uv run ruff check --fix`: All checks passed
- `uv run mypy src/ansible_aom`: Success, no issues found in 69 source files

### Layer Compliance

- Zero imports from `renderer`, `cli`, `session`, `tui`, `compact`, `ansible`.
- Only imports: `from __future__ import annotations`, `from collections.abc import Iterable`.
- No `# type: ignore` — `core/` is strict by default in pyproject.toml, no override needed.
- No new dependencies added to pyproject.toml.

## Session: 2026-06-22 — CLI flag + plumbing

### Changes Made

- **`cli.py`**: Added `--hide-state` flag to `create_parser()` (after `--no-record`, before `--install-completion`). Uses `action="append"`, `choices` for the five valid states, `default=None`. Updated `_run_compact()` to accept `hide_states: list[str] | None = None` and forward it to `create_renderer()`. Updated `main()` to extract `args.hide_state` (normalizing `None` → `[]`) and pass to `_run_compact()`.
- **`renderer/factory.py`**: Added `hide_states: list[str] | None = None` parameter to `create_renderer()`. Forwards to `CompactRenderer(hide_states=hide_states or [])`. Ignored by `AOMApp` and `JsonRenderer`.
- **`compact/renderer.py`**: Added `hide_states: list[str] | None = None` parameter to `CompactRenderer.__init__()`. Stored as `self._hide_states: list[str] = hide_states or []`.
- **`test_cli.py`**: Added `TestHideStateFlag` (6 parser tests) and `TestHideStateCompactPlumbing` (3 plumbing tests with mocked `create_renderer`).

### Verification Results

- `uv run pytest tests/unit/test_cli.py -v`: 114 passed (all existing + 9 new)
- `uv run pytest tests/unit/ -q`: 1749 passed (full unit suite, no regressions)
- `uv run ruff format`: 234 files unchanged
- `uv run ruff check --fix`: 2 pre-existing errors in untouched files (`core/tree.py`, `tui/screens/inspect.py`)
- `uv run mypy src/ansible_aom`: Success, no issues in 69 source files

### Design Decisions

- **`action="append"` with `default=None`**: argparse doesn't set the attribute when the flag is absent, so `args.hide_state` is `None` by default. We normalize to `[]` in `main()` before passing downstream. This avoids the `action="append"` + `default=[]` pitfall where argparse mutates the shared default list across invocations.
- **`hide_states: list[str] | None = None` in `_run_compact()`**: Using `None` default instead of `()` avoids the mypy `[assignment]` error (tuple default for list annotation). The `None` → `[]` conversion happens at the `create_renderer()` call site.
- **Factory + CompactRenderer changes were necessary**: The task's own code passes `hide_states` to `create_renderer()`, so the factory must accept it for the production path to work. Two pre-existing tests (`test_exit_code_127_for_missing_ansible`, `test_main_dispatches_json_renderer_when_format_json`) call the real factory (not mocked), so they would fail without the factory update. These are minimal plumbing changes — no filtering logic was added to the renderer.

## Session: 2026-06-22 — gating logic + compact tests

### Changes Made

- **`compact/renderer.py`**:
  - Added import: `from ansible_aom.core.log_filter import normalize_hide_states, should_hide_event`
  - `__init__`: Replaced `self._hide_states: list[str] = hide_states or []` with `valid, _unknown = normalize_hide_states(hide_states or []); self._hide_states: frozenset[str] = valid`
  - `_emit_event_log` — gated 5 branches:
    - `v2_runner_on_ok`: `if "ok" in self._hide_states: return` after flush/flag side effects
    - `v2_runner_on_failed`: `if "failed" in self._hide_states: return` after flush/flag
    - `v2_runner_on_unreachable`: `if "unreachable" in self._hide_states: return` after flush/flag
    - `v2_runner_on_skipped`: `if "skipped" in self._hide_states: return` before buffer append
    - `v2_runner_item_on_*`: `if should_hide_event(name, self._hide_states):` with flush/flag for non-skipped items before return
  - Never gated: `v2_playbook_on_play_start`, `v2_playbook_on_task_start`, `v2_runner_on_start`, `v2_playbook_on_stats`
  - Not modified: `_flush_pending_skips()`, `_render_status_panel()`, `update_state()`, `_bump_task_counters()`

- **`tests/compact/test_hide_state.py`** (new file, 284 lines):
  - 16 tests across 7 classes: `TestHideOk` (5), `TestHideSkipped` (2), `TestHideFailed` (2), `TestHideUnreachable` (1), `TestHideMultiple` (2), `TestHideStateDefaults` (2), `TestHideStateRunStateUnaffected` (2)
  - Helper functions: `_task_start`, `_skipped`, `_ok`, `_changed`, `_failed`, `_unreachable`, `_play_start`, `_stats`, `_renderer(hide_states=...)`, `_logged`
  - Follows exact pattern of `test_skipped_collapsing.py` — same mock Display, same assertion style, no class/method docstrings

### Key Design Decisions

- **Gate placement**: Flush/flag side effects (`_flush_pending_skips`, `_current_task_had_nonskipped_result`) run BEFORE the gate. This is correct because even when the log line is suppressed, the task DID produce a result that matters for skip-collapsing rules at task transitions.
- **`v2_runner_on_skipped` gate**: Returns before `_pending_skipped_hosts.extend()`, so the buffer stays empty and `_flush_pending_skips` becomes a no-op (fast path at line 1048: `if not self._pending_skipped_hosts: return`).
- **`v2_runner_item_on_*` gate**: Uses `should_hide_event()` from core module for proper event-to-state mapping. Non-skipped items still flush/flag before returning — same rationale as the aggregate handlers.
- **`frozenset` over `list`**: `normalize_hide_states()` returns a `frozenset[str]` — immutable, hashable, O(1) membership test. The `_unknown` return value is discarded since the CLI already validates choices.
- **State-verification tests**: `_emit_event_log` does NOT mutate state — only `handle_event` does. Tests must call `handle_event` for both `_task_start` and the result event, and must send `_play_start` first to set `_current_play_id` so the result event resolves to the correct play.

### Verification Results

- `uv run pytest tests/compact/test_hide_state.py -v`: 16 passed
- `uv run pytest tests/compact/ -q`: 383 passed (no regressions)
- `uv run pytest tests/unit/ -q`: 1749 passed (no regressions)
- `uv run ruff format`: 2 files reformatted (renderer.py, test_hide_state.py)
- `uv run ruff check --fix`: 2 pre-existing errors in untouched files (`core/tree.py`, `tui/screens/inspect.py`); changed files clean
- `uv run mypy src/ansible_aom`: Success, no issues in 69 source files

## Session: 2026-06-22 — SPEC and TEST_SPEC documentation

### Changes Made

- **`SPECIFICATION.md` §3.2**: Added `--hide-state` row to the CLI flag table at line 238 (between `--version` and the "All other arguments pass through" paragraph). Row format: `| flag | type | default | description |`.
- **`SPECIFICATION.md` §4.1**: Added `#### State Filtering` sub-section between `### 4.2 Full TUI (--tui mode)` header (old line 391) and the previous `Optional: blessed` bullet (line 389). The sub-section covers: gated event types table, never-suppressed items list, recording behavior, TUI boundary, default behaviour.
- **`TEST_SPECIFICATION.md`**: Added TC-650 through TC-659 after TC-512 (line 4762), before the `---` separator at line 4889. Each TC follows the canonical format with `**Section:**`, `**Priority:**`, `**Test Steps:**`, `**Expected Outcome:**`.

### Insertion Points

- Flag table row: After line 237 (`| `--version` | flag | - | Show version |`), before the empty line at line 238.
- State Filtering sub-section: After line 389 (`Optional: `blessed` — for advanced ANSI cursor positioning (Phase 2)`), before line 391 (`### 4.2 Full TUI (--tui mode)`).
- TC-650-659: After line 4761 (the `**Edge Cases:**` line of TC-512), before line 4763 (`---`).

### Verification Results

- `uv run ruff format`: 1 file reformatted (SPECIFICATION.md)
- `uv run ruff check --fix`: 2 pre-existing errors in untouched Python files (`core/tree.py`, `tui/screens/inspect.py`); no issues in spec files

## Session: 2026-06-22 — Bug fix: `--hide-state ok,skipped` unrecognized arguments

### Root Cause

`action="extend"` with `nargs=1` and `type=_comma_sep_state` (returning `list[str]`) caused double-wrapping: argparse wrapped the list from `_comma_sep_state` in another list, producing `[['ok', 'skipped']]` instead of `['ok', 'skipped']`. Without `nargs=1`, Python 3.9+ argparse splits each character of the value as a separate token when `type=str` (or any type returning a string), so `--hide-state ok,skipped` became `['o', 'k', ',', 's', 'k', 'i', 'p', 'p', 'e', 'd']`.

### Fix: Custom argparse Action (Option A)

Replaced `_comma_sep_state` type function with `_HideStateAction(argparse.Action)`:

- `nargs=1` — consumes exactly one value per invocation, preventing character-splitting
- `__call__` handles splitting on commas, whitespace stripping, validation against `VALID_STATES`, and flat accumulation into `namespace.hide_state`
- Uses `parser.error()` for invalid choices (not `argparse.ArgumentTypeError`) because `ArgumentTypeError` raised from a custom action's `__call__` is NOT caught by argparse — only `parser.error()` reliably produces `SystemExit`
- `values` parameter typed as `str | Sequence[str] | None` to match supertype's `Sequence[Any]` signature (Liskov-compliant)
- `default=None` preserved — no flag → `args.hide_state is None`, normalized to `[]` in `main()`

### Key Learnings

- **`argparse.ArgumentTypeError` is only caught when raised from `type=` functions**, not from custom action `__call__`. Use `parser.error()` in custom actions for consistent `SystemExit` behavior.
- **`action="extend"` + `type=` returning a list** causes double-wrapping. A custom action is the cleanest fix — it keeps validation local to the argparse layer and `main()` stays clean.
- **`Sequence[str]` not `list[str]`** for the `values` parameter to match the supertype's `Sequence[Any]` and avoid mypy `[override]` errors.
- **`isinstance(values, Sequence) and not isinstance(values, str)`** is the correct guard because `str` is also a `Sequence[str]` in Python.

### Verification

- `uv run pytest tests/unit/test_cli.py::TestHideStateFlag tests/unit/test_cli.py::TestHideStateCompactPlumbing -q`: 13 passed
- `uv run pytest tests/unit/ tests/compact/ -q`: 2144 passed (full suite, no regressions)
- `uv run mypy src/ansible_aom`: Success, no issues in 69 source files
- `uv run ruff check src/ansible_aom/cli.py`: All checks passed
- Direct reproduction script: all 9 scenarios pass (comma-separated, repeated, mixed, unknown rejection, default, single, all-valid, unknown-single, unknown-in-comma-list)

## 2026-06-22T20:11:10Z Task: tree-classify-failed-visible

### Bug
`_classify` in `core/tree.py` (line 962) returned `"completed"` whenever no host had `Status.RUNNING`. This made tasks with FAILED/UNREACHABLE hosts invisible in the tree once all hosts reached terminal status — the failure literally vanished from the panel, especially with `--hide-state ok`.

### Root cause
The function checked for RUNNING hosts but not for FAILED/UNREACHABLE hosts. After the last runner event arrived, no host was RUNNING, so the fallthrough returned `"completed"` and the tree projection dropped the entire task row.

### Fix
Added a check before the final `return "completed"`: if any host's `_effective_status()` is FAILED or UNREACHABLE, return `"running"` instead. This keeps the task visible with its failure count.

Used `_effective_status(hs)` (already defined at module level, line 148) to respect the OK+changed→CHANGED collapsing rule — consistent with how `_task_line` classifies hosts for display.

### Key constraint preserved
`TestCompletedDynamicChildFilteredFromTree` (line 607) requires that a fully-ok task (all hosts OK/SKIPPED/CHANGED, none FAILED/UNREACHABLE) is still classified as `"completed"` and filtered from the tree. The new check only promotes tasks with actual failures — all-ok tasks still fall through to `"completed"`.

### Test results
- 2 new regression tests pass (`TestFailedTaskRemainsVisible`)
- 75 existing tree tests pass (no regressions)
- 2155 total suite tests pass
- mypy: clean
- ruff: pre-existing `idx_before` unused variable warning (unrelated)

## Session: 2026-06-22 — Per-host hide-state granularity fix (ok vs changed)

### Bug

`--hide-state ok` suppressed BOTH `ok:` AND `changed:` per-host lines because `should_hide_event("v2_runner_on_ok", {"ok"})` returned `True` at the event level (since `{ok, changed} ∩ {ok} ≠ ∅`), causing `_enter_terminal_event` to early-return before any host lines were rendered.

### Root cause

`should_hide_event` operates at the **event-type** level — it can only answer "should this entire event be hidden?" Ansible's `v2_runner_on_ok` event type covers both `ok` and `changed` states (the distinction is in each host's `result.changed` field). The event-level check conflated them.

### Fix: `should_hide_host_result(result, event_type, hide_states) -> bool`

New pure helper in `core/log_filter.py` that resolves the per-host state from the result dict:

- `v2_runner_on_ok` / `v2_runner_item_on_ok`: `result.get("changed", False)` → `"changed"` or `"ok"`, then check membership in `hide_states`
- `v2_runner_on_failed` / `v2_runner_item_on_failed` → `"failed"`
- `v2_runner_on_unreachable` → `"unreachable"`
- `v2_runner_on_skipped` / `v2_runner_item_on_skipped` → `"skipped"`
- Any other event type → `False`

### Renderer changes

**`v2_runner_on_ok` branch** (was lines 1243-1270):
- Replaced `if self._enter_terminal_event(name): return` with inline bookkeeping: `self._flush_pending_skips(force_individual=True)` + `self._current_task_had_nonskipped_result = True`
- Added `if should_hide_host_result(result, name, self._hide_states): continue` inside the per-host loop (before the `_streamed_loop_items` skip is fine, but after it is clearer — placed after the loop-items skip to match existing structure)
- This allows some hosts to be hidden while others in the same event still render

**`v2_runner_item_on_ok` branch** (was inside the `v2_runner_item_on_*` block):
- Split out from the shared `should_hide_event` early-return path
- Uses per-host `should_hide_host_result` inside the host loop
- `v2_runner_item_on_failed` and `v2_runner_item_on_skipped` keep event-level `should_hide_event` — their states are unambiguous

**`should_hide_event` preserved**: Still used by `_enter_terminal_event` for `v2_runner_on_failed`, `v2_runner_on_unreachable`, and `v2_runner_on_skipped` — unambiguous single-state events. Also added a warning docstring about its coarseness for `v2_runner_on_ok`.

### Test changes

**Inverted tests** (previously asserted wrong behavior):
- `TestHideOk::test_changed_lines_are_suppressed` → `test_changed_lines_still_print_when_ok_hidden` — changed lines must NOT be hidden when only ok is hidden
- `TestHideChanged::test_ok_lines_are_suppressed_when_changed_hidden` → `test_ok_lines_still_print_when_changed_hidden` — ok lines must NOT be hidden when only changed is hidden

**New tests**:
- `TestShouldHideHostResult` (20 tests in `test_log_filter.py`): Pure unit tests for the new helper — ok/changed/failed/unreachable/skipped per-host logic, missing `changed` defaults to False, both-ok-and-changed combined, item events
- `TestHideOkPerHost` (2 tests in `test_hide_state.py`): Mixed-host event (web1=ok, web2=changed) with `--hide-state ok` and `--hide-state ok,changed`
- `TestHideChangedPerHost` (1 test in `test_hide_state.py`): Mixed-host event with `--hide-state changed`

### Verification

- `uv run pytest tests/compact/test_hide_state.py tests/unit/test_log_filter.py -v`: 85 passed
- `uv run pytest tests/unit/ tests/compact/ -q`: 2182 passed (no regressions)
- `uv run mypy src/ansible_aom`: Success, no issues in 69 source files
- `uv run ruff check src/ansible_aom/core/log_filter.py src/ansible_aom/compact/renderer.py tests/compact/test_hide_state.py tests/unit/test_log_filter.py`: All checks passed

## 2026-06-22 — Per-host summary: show failing task name instead of "(idle)"

### Problem

When a host had FAILED or UNREACHABLE status, the "on" column in the per-host summary table showed "(idle)" or bare "unreachable" — the user couldn't tell WHICH task caused the failure.

### Fix: `failed_task` and `failed_status` fields on `HostRow`

Added two new optional fields to the frozen `HostRow` dataclass:
- `failed_task: str | None = None` — task name of the most recent FAILED/UNREACHABLE result
- `failed_status: Status | None = None` — `Status.FAILED` or `Status.UNREACHABLE`

With defaults, existing `HostRow()` constructions (only 2 in the codebase) require no changes.

### Logic in `host_rows()`

Added a `failed: dict[str, tuple[str, Status]]` accumulator alongside `current`. For each host entry with `effective in (FAILED, UNREACHABLE)`, records `(task.name, effective)`. Later entries overwrite earlier ones (most-recent wins for multi-failure scenarios). Running entries still only update `current` — a running task always takes display precedence over a past failure, but `failed_task` is still recorded for fallback.

### Rendering in `format_host_rows`

New priority chain for the "on" suffix:
1. `current_task is not None` → running task with spinner (unchanged)
2. `failed_task` + `failed_status == FAILED` → `✖ {task_name}` in red (or `X` in ASCII mode)
3. `failed_task` + `failed_status == UNREACHABLE` → `⊝ {task_name}` in magenta (or `O` in ASCII mode)
4. `worst_status == UNREACHABLE` (no task name available) → `"unreachable"` in magenta (fallback)
5. Otherwise → `"(idle)"` in dim (unchanged fallback)

Uses existing `STATUS_ICONS` / `STATUS_ICONS_ASCII` lookup already imported.

### Test additions

**`tests/unit/test_tree_projection.py::TestHostRows`** (6 new tests):
- `test_failed_host_tracks_failed_task_name` — FAILED entry populates `failed_task`/`failed_status`
- `test_unreachable_host_tracks_failed_task_name` — UNREACHABLE entry populates `failed_task`/`failed_status`
- `test_running_host_has_no_failed_task` — RUNNING host has `failed_task=None`
- `test_ok_host_has_no_failed_task` — OK host has `failed_task=None`
- `test_failed_task_tracks_most_recent_failure` — multiple failures, last wins
- `test_running_overrides_failed_task_in_display` — running task shown in suffix, but `failed_task` still recorded

**`tests/compact/test_host_table.py`** (3 new tests):
- `test_failed_host_shows_failed_task_in_suffix` — `✖ Start service` appears in rendered row
- `test_unreachable_host_shows_unreachable_task_in_suffix` — `⊝ Gather facts` appears in rendered row
- `test_failed_host_shows_X_in_ascii_mode` — ASCII fallback `X Start service`

**`tests/compact/test_tree_render.py`** — Updated `test_format_host_rows_unreachable_host_shows_unreachable` to assert `⊝ Install nginx` instead of bare `"unreachable"` in the suffix.

### Golden frame updates

Two golden files updated to reflect the new "on" column behavior:
- `all_unreachable__80x24.txt`: `unreachable` → `O Ping nodes`
- `multi_host_mixed__80x24.txt`: `unreachable` → `O Deploy application`, `(idle)` → `X Configure firewall`

### Test filter fix

`test_completion_recap.py::test_failure_recap_lines_indented` filter was too broad — it matched `"install nginx" in line and "web2" in line`, which now also matches the host row suffix. Narrowed to `"FAILED:" in line and "install nginx" in line`.

### Verification

- `uv run pytest tests/unit/test_tree_projection.py::TestHostRows -v`: 12 passed
- `uv run pytest tests/compact/test_host_table.py -q`: 11 passed
- `uv run pytest tests/compact/test_tree_render.py -q`: 14 passed
- `uv run pytest tests/unit/ tests/compact/ -q`: 2191 passed (0 failed)
- `uv run mypy src/ansible_aom`: Success, no issues in 69 source files
- `uv run ruff check src/ansible_aom/core/tree.py src/ansible_aom/compact/format.py`: 1 pre-existing error (tree.py:712 unused `idx_before`)

## 2026-06-23 — Task summary status counts

### What changed

`_emit_previous_task_summary` in `compact/renderer.py` (line 1042) now appends a status count suffix to the summary line:

- Old format: `[10:00:15] Install nginx — 13.0s (15.0s)`
- New format: `[10:00:15] Install nginx — 13.0s (15.0s)  (1 failed, 2 ok)`

### New method: `_build_status_suffix`

Extracted the suffix logic into `_build_status_suffix()` for testability. It:

1. Looks up the previous task's `TaskRunState` via `self._last_task_uuid`
2. Tallies per-status host counts using the same `_effective_status` rule as tree projection (OK+changed → CHANGED)
3. Applies `--hide-state` filtering: hidden states excluded from suffix, EXCEPT failed and unreachable which always show (critical errors must remain visible)
4. Dims non-error states (ok, changed, skipped) when alongside errors (failed, unreachable)
5. Returns empty string when no counts available or all hidden

### Colour mapping

- Failed → red (`_RED`)
- Unreachable → magenta (`_MAGENTA`)
- Changed → yellow (`_YELLOW`), dimmed when alongside errors
- OK → green (`_GREEN`), dimmed when alongside errors
- Skipped → cyan (`_CYAN`), dimmed when alongside errors

### Golden frame updates

8 golden frame snapshots updated to include the new status suffix. The suffix appears on every task summary line except for tasks with no host results (empty task dict) or when all states are hidden.

### Design decisions

- **always_show for FAILED/UNREACHABLE**: These are critical error states. Even if a user passes `--hide-state failed`, the summary line still shows the failure count. This differs from per-host line gating (where `--hide-state failed` does suppress the `fatal:` line) because the summary line is the user's last chance to notice something went wrong.
- **OK+changed → CHANGED**: Uses the same effective-status rule as tree projection and host rows for consistency.
- **Defensive task lookup**: If `_last_task_uuid` isn't found in any play's tasks (e.g., task was cleared between plays), `_build_status_suffix` returns an empty string and the summary line falls back to the old format without counts.

### Test results

- 15 new tests in `tests/compact/test_task_summary.py`
- 2206 total suite tests pass
- mypy: clean
- ruff: clean

## 2026-06-23 — Case-insensitive --hide-state + difflib "did you mean?" suggestions

### What changed

**`src/ansible_aom/cli.py`** — `_HideStateAction.__call__`:
- Added `import difflib` at top of module
- Each token is now lowercased (`.lower()`) before validation against `VALID_STATES`
- Lowercased token is appended to `accumulated` (not original), so downstream always gets lowercase
- On validation failure, uses `difflib.get_close_matches(token.lower(), VALID_STATES, n=1, cutoff=0.6)` to suggest the closest valid state
- Error message format: `invalid choice: 'skip' (choose from changed, failed, ok, skipped, unreachable); did you mean 'skipped'?`
- Original token spelling preserved in the error message (e.g., `'Skip'` not `'skip'`)

### Design decisions

- **Lowercase in the action, not in normalize_hide_states**: `normalize_hide_states` already lowercases, but the CLI validation gate should accept case-insensitive input BEFORE it reaches normalize. This keeps the argparse layer self-contained.
- **`cutoff=0.6`**: Standard difflib cutoff for "similar" strings. `skip`→`skipped` matches (0.73 similarity). `fail`→`failed` matches. `xyz`→anything doesn't match.
- **`n=1`**: Only one suggestion — showing multiple would clutter the error.
- **Original token in error**: The error shows `'Skip'` (as typed), not the lowercased `'skip'`, so the user can see what they actually typed. The suggestion uses the canonical lowercase form from `VALID_STATES`.
- **No dedup in the action**: `--hide-state ok,OK` produces `["ok", "ok"]` — dedup happens downstream in `normalize_hide_states`. This is the same behavior as before (the action just accumulates tokens), and normalize already handles it.

### New tests (9 in TestHideStateFlag)

- `test_hide_state_case_insensitive_ok` — `OK` accepted, stored as `ok`
- `test_hide_state_case_insensitive_mixed` — `OK,Skipped` accepted, stored as `ok`, `skipped`
- `test_hide_state_case_insensitive_all_upper` — `OK`, `CHANGED`, `FAILED` all accepted
- `test_hide_state_case_insensitive_dedup` — `ok,OK` produces `["ok", "ok"]`
- `test_hide_state_typo_suggests_skipped` — `skip` → error includes `did you mean 'skipped'?`
- `test_hide_state_typo_suggests_failed` — `fail` → error includes `did you mean 'failed'?`
- `test_hide_state_random_garbage_no_suggestion` — `xyz` → no `did you mean`
- `test_hide_state_error_includes_choices` — error has `(choose from ...)` with all valid states
- `test_hide_state_typo_error_preserves_original_token` — `Skip` shows `'Skip'` in error, not `'skip'`

### Verification

- `uv run pytest tests/unit/test_cli.py -v -k hide_state`: 22 passed
- `uv run pytest tests/unit/ tests/compact/ -q`: 2215 passed
- `uv run mypy src/ansible_aom`: Success, no issues in 69 files
- `uv run ruff check src/ansible_aom/cli.py tests/unit/test_cli.py`: All checks passed
- Hands-on: `aom --hide-state OK --version` succeeds; `aom --hide-state skip site.yml` shows suggestion
