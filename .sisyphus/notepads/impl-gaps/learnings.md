# Implementation Learnings

## Redaction Module (src/ansible_aom/core/redaction.py)

### API to implement:
```python
# Constants
PASSWORD_MATCH = re.compile(r'^(?:.+[-_\s])?pass(?:[-_\s]?(?:word|phrase|wrd|wd))?(?:[-_\s].+)?$', re.IGNORECASE)
ANSIBLE_PASSWORD_FIELDS = frozenset({...})
GENERIC_SECRET_FIELDS = frozenset({...})
PASSWORD_WHITELIST = frozenset({"passenger_version", "passenger_pool", "bypass", "overpass", "compass", "underpass", "passport_number"})
URL_CRED_PATTERN = re.compile(r'([a-zA-Z]+://[^:]+:)([^@]+)(@)')
CLI_CRED_PATTERN = re.compile(r'(--(?:password|pass|pwd|token|secret|key|api-key)\s*[=: ]+)\S+', re.IGNORECASE)
REDACTED = '********'
MAX_DEPTH = 10

# Functions
def redact_event(event: dict, config: RedactionConfig) -> dict
def redact_dict(data: dict, config: RedactionConfig, depth: int = 0) -> dict
def sanitize_string(s: str, config: RedactionConfig) -> str
def should_redact(key: str, config: RedactionConfig) -> bool
```

### Layer Rules:
1. **Layer 1**: If `_ansible_no_log=True` is in a result dict (even nested in lists), replace that ENTIRE result with `{'censored': '(no_log)'}`.
2. **Layer 2**: For all result dict keys (except whitelisted), match `PASSWORD_MATCH` regex, `ANSIBLE_PASSWORD_FIELDS`, `GENERIC_SECRET_FIELDS`, or `config.custom_fields` → value replaced with `REDACTED`.
3. **Layer 3**: For specific string fields (`cmd`, `stdout`, `stderr`, `msg`), apply `URL_CRED_PATTERN` and `CLI_CRED_PATTERN` substitutions, plus `config.custom_patterns`.
4. **Layer 4**: If event has `res.invocation.module_args`, recursively redact with same logic (max depth 10).

## CLI Exit Code Tests (test_cli.py TC-027/TC-028)

Current tests are trivial constants. Need to mock actual behavior:
- TC-027: Mock subprocess execution to raise FileNotFoundError, verify `main()` returns 127
- TC-028: Mock signal handling or KeyboardInterrupt during main, verify `main()` returns 130

The `main()` currently handles inspect and playbook. For playbook, it calls `create_renderer()` → `print(...)`. Need to ensure `main()` properly handles `FileNotFoundError` for ansible-playbook → 127.
Since main() currently doesn't spawn ansible-playbook yet (returns 0 after print), the tests should test the DESIRED behavior defined in spec. The current code may need minor modifications to handle `FileNotFoundError` gracefully.

## Missing POSIX Callback Tests (TC-067 to TC-071)

These check:
- ansible.posix availability (via ansible-galaxy collection list or importlib)
- Install prompt
- ansible-core version >= 2.14
- ansible.posix version >= 1.5.0
- ANSIBLE_STDOUT_CALLBACK env var set

## Missing Host Resolution Tests (TC-149 to TC-152)

- resolved_hosts population
- Host cross-check warning
- Fallback after --list-hosts failure
- v2_playbook_on_stats cross-check

## TC-027 & TC-028: CLI Exit Codes for FileNotFoundError and KeyboardInterrupt (2026-04-23)

**Pattern**: Exception handling order matters in Python - specific exceptions must come before generic `Exception` handler.

**Implementation**:
- Added `FileNotFoundError` handler → return 127
- Added `KeyboardInterrupt` handler → return 130  
- Placed **before** the existing `NotImplementedError` and `Exception` handlers

**Test Pattern** for mocking exceptions in CLI:
```python
with patch("ansible_aom.renderer.factory.create_renderer") as mock_renderer:
    mock_renderer.side_effect = FileNotFoundError("ansible-playbook")
    with patch("sys.argv", ["aom", "playbook.yml"]):
        result = main()
        assert result == 127
```

**Key insight**: The `patch` path must match where the function is imported/used, not where it's defined. Since `cli.py` does `from ansible_aom.renderer.factory import create_renderer`, we patch `ansible_aom.renderer.factory.create_renderer`.

## Host Status Display (resolved)

### Skipped status was missing from host overview (resolved 2026-05)

The host overview (`format_host_rows`) and host summary (`format_host_summary`) only showed ok/changed/failed/unreachable. `Status.SKIPPED` was tracked in `RunState` and `tree.py` but never surfaced in the display.

**Fix**: Added `skipped` parameter to `_format_count_cells`, `format_host_summary`, and conditional `skipped` column to `format_host_rows` (hidden when no host has skipped tasks, mirroring the `unreachable` column pattern). The `v2_runner_on_skipped` handler already created `HostRunState(status=Status.SKIPPED)` correctly.

### Per-host summary lines were duplicating the host table (resolved 2026-05)

After completion, the renderer printed both a column-aligned host table (`format_host_rows`) AND per-host summary lines (`format_host_summary`) with the same data. The summary lines were pure duplication.

**Fix**: Removed `_format_per_host_lines` method entirely. On completion, the host table now always prints (not just on failure). The tree snapshot only prints on failure/cancel — on success, stale running spinners would be misleading. `_capture_panel_snapshot` now returns `(tree_lines, host_lines)` tuple so callers can print them independently.

### Host leaves only showed RUNNING hosts (resolved 2026-05)

Tree host leaves under a running task only showed hosts with `Status.RUNNING`. This meant completed hosts disappeared from the tree before the task was done.

**Fix**: Removed the `if hs.status != Status.RUNNING: continue` filter in `_emit_runtime_play`. All hosts under a running task now appear with status-specific icons (● OK, ◐ RUNNING, ○ SKIPPED, etc.).

### Linear strategy tasks stayed RUNNING until playbook end (resolved 2026-05)

Under linear strategy, `task.status` only transitioned to COMPLETED at `v2_playbook_on_stats`. Previous tasks showed as "running" long after they finished.

**Fix**: In `_handle_v2_playbook_on_task_start`, when a new task starts under linear strategy, mark all other RUNNING tasks in the same play as COMPLETED (either all hosts terminal, or empty hosts meaning no runner events arrived). The `_classify` method respects `Status.COMPLETED` as an early exit returning "completed" so the tree prunes them immediately.

### Hostname fallback showed all hosts from all plays (resolved 2026-05)

The tree fallback `_all_known_hostnames` collected hostnames from every
task across every play when `runtime.hosts` was empty. On multi-play
playbooks, play 2 would show host leaves from play 1 (plus `localhost`
from test playbooks).

**Fix**: Replaced with `_play_target_hostnames(play, play_def)` that uses
`play_def.resolved_hosts` (preflight targets) when available, falling
back to the play's own runtime task hostnames. Call site already had both
`play` (PlayRunState) and `play_def` (PlayDefinition) in scope.

### Elapsed time stuck at 0s for fallback host leaves (resolved 2026-05)

Fallback host leaves (when `runtime.hosts` is empty) hardcoded
`elapsed_s=0.0` with `Status.RUNNING`. The elapsed counter never
advanced from zero, even for tasks that had been running for minutes.

**Fix**: Compute elapsed from `runtime.start_time` instead of hardcoding
0. When `start_time` is None (task hasn't started yet), 0 is correct.

### Dynamic children not shown as pending in tree (resolved 2026-05-23)

Grafted `include_tasks` children (in `TaskDefinition.children`) appeared only in role task counts, not as visual □ pending entries in the tree. Users couldn't see what dynamic tasks were coming.

**Fix**: Added a new loop in `_play_running_and_pending` after the runtime-only tasks loop. Iterates `play_def.tasks` for entries with `.children`, emitting each child as either "running" (if announced at runtime with a matching `TaskRunState`) or "pending" (if not yet seen). Completed children are filtered. Duplicates prevented via `emitted_names` — the runtime-only loop now also adds to `emitted_names` so dynamic children already picked up there don't re-appear.

**Tests added**: TC-320 (pending before announcement), TC-321 (running status), TC-322 (completed filtered), TC-323 (under role header), TC-324 (host leaves), + duplicate-prevention test.

## Cross-Play Task Leakage (resolved 2026-05-24)

Completed plays showed `◐` running tasks from *later* plays because
`_play_running_and_pending` searched `runtime_by_name` across all plays
without filtering by play ownership.

**Fix** (`dab145a`): Added `include_cross_play=False` parameter. Completed
plays use `False` — they only emit their own tasks. Active plays still
use `True` to show handler tasks from other plays.

**Key files**: `tree.py:_play_running_and_pending` — new `include_cross_play` parameter

## Tree Flicker Between Plays (resolved 2026-05-24)

Between play transitions, the tree alternated between completed and
current play on alternate frames because the play selection lacked
temporal persistence.

**Fix** (`f179469`): Introduced `_last_running_play_id` — a sticky
fallback that persists the most recently running play across frames.
Selection tiers: (1) fresh running play, (2) previous frame's sticky,
(3) cold-start fallback.

**Key files**: `tree.py:_select_play_for_tree` — `_last_running_play_id` logic

## Stuck Meta Tasks Under Linear Strategy (resolved 2026-05-24)

`meta: reset_connection` showed `◐` forever (elapsed time >15 minutes)
because the linear force-completion loop had scope guards that skipped
meta tasks with zero hosts.

**Fix** (`d981444`): Added third completion branch scoped to same play:
`elif p.play_id == play.play_id:` force-transitions RUNNING hosts to
OK. Only RUNNING is force-completed — real terminal events preserved.

**Key files**: `models.py:_handle_v2_playbook_on_task_start` — new
force-completion branch

## Upcoming Plays Invisible (resolved 2026-05-24)

Plays with zero `runtime.tasks` (not yet started) were silently omitted
from the tree because the skip guard `and runtime.tasks` treated them
the same as completed plays.

**Fix** (`cd68065`): Changed guard to `runtime.tasks is not None` instead
of truthiness. Upcoming plays have empty dicts (truthy `is not None`)
while completed+empty plays still get skipped.

**Key files**: `tree.py:_select_play_for_tree` — skip guard logic

## --hide-state Comma-Separated Support (2026-06-22)

**Change**: `--hide-state` now accepts both comma-separated values (`--hide-state ok,skipped`) and repeatable invocations (`--hide-state ok --hide-state skipped`).

**Pattern**: Used `action="extend"` with a custom `type` function (`_comma_sep_state`) that splits on commas, validates each token, and returns a `list[str]`. Argparse's `extend` action flattens list-returning types into a single accumulated list.

**Key details**:
- `choices` parameter was removed (it conflicts with a list-returning `type` function — validation happens inside `_comma_sep_state` instead)
- `action="extend"` is available in Python 3.8+ (project uses 3.14)
- The `hide_state` attribute on the parsed namespace still arrives as `list[str]` — no downstream changes needed in `main()` or `_run_compact()`
- Existing tests for repeatable invocation still pass unchanged
- New tests cover: comma-separated, mixed append+comma, unknown in comma-separated, single value without comma

## Strategy Detection Corrected (resolved 2026-05-24)

Strategy detection never flipped to "free" because `v2_runner_on_start`
only fires outside lockstep mode — but no code handled this signal.

**Fix**: In `_handle_v2_runner_on_start`, flip `detected_strategy`
from "linear" to "free" on first occurrence. This is correct because
the JSONL callback guards `runner_on_start` behind `if self._is_lockstep: return`.

**Key files**: `models.py:_handle_v2_runner_on_start` — strategy flip logic

## Throttle Gate Render-Starvation Bug (resolved 2026-06-22)

The dirty-path throttle in `_render_status_panel` could suppress renders
indefinitely when state changes arrived faster than the 0.25 s window.

**Symptom**: User reports "i already had a view with status changed but
they did not get showed" — the panel froze on stale output during event
bursts.

**Root cause**: The original gate (lines 494-503) compared
`elapsed_since_compute < _PANEL_COMPUTE_THROTTLE_S`. If state changes
kept arriving faster than 0.25 s, every render call skipped AND
`_last_panel_compute_time` was never updated — the timer couldn't
"advance" past the throttle window. Result: 0 renders per second despite
the panel being dirty.

**Fix**: Split the clock in two:
- `_last_panel_compute_time` — when the panel was last actually rendered
- `_last_state_change_monotonic` — when state last changed

Gate logic now branches on `last_compute >= last_change`:
- If compute is AFTER the last state change → already saw this state →
  wait up to 1 s for the tick refresh
- If compute is BEFORE the last state change → stale compute → render
  now (after a 50 ms coalesce window to absorb truly simultaneous events)

`update_state` and `set_definitions` stamp `_last_state_change_monotonic`
alongside `_panel_dirty = True`. Added `_PANEL_DIRTY_COALESCE_S = 0.05`
constant for the burst-absorption window.

**Files touched**:
- `src/ansible_aom/compact/renderer.py` — gate logic, init, two stamp
  sites
- `tests/compact/test_render_dirty_flag.py` — `test_perf_043` (renders
  after burst settles) and `test_perf_044` (waits for tick refresh when
  compute is fresh)

**Verification**: 2810 tests pass (was 2808, +2 from regression tests).
mypy strict, ruff lint, ruff format — all clean.

**Pattern**: When a throttle gate depends on a "did we render this yet?"
check, the gate must advance the timer on EVERY call (even when it
skips) OR it must distinguish "state changed since last render" from
"no state changed" via a separate clock. Otherwise a fast-changing
input can starve the output indefinitely.

## Async-Poll Dict-Leak Guard Extended to Inspect Path (2026-06-27)

**Task**: Applied the same async-poll dict-leak guard to `_make_loop_item` in
`core/inspect_model.py` that already existed in `compact/renderer.py:_format_loop_item_line`.

**Detection criterion** (shared): `"ansible_job_id" in raw and "_ansible_item_label" not in raw and "item" not in raw`

**Layering decision**: The helper `_is_async_poll_payload` was relocated from
`compact/renderer.py` to a new `core/_async_poll.py` module, because `core/`
must never import from `compact/`. The renderer now imports
`is_async_poll_payload` from `ansible_aom.core._async_poll`. The old
`_is_async_poll_payload` function was removed from the renderer.

**Files modified**:
- `src/ansible_aom/core/_async_poll.py` — new module, exports `is_async_poll_payload`
- `src/ansible_aom/core/inspect_model.py` — `_make_loop_item` now checks
  `is_async_poll_payload(raw)` and returns `(async, job_id=XXX)` label
- `src/ansible_aom/compact/renderer.py` — import relocated from local def to
  `core._async_poll`; all 3 call sites updated from `_is_async_poll_payload` to
  `is_async_poll_payload`
- `tests/unit/test_inspect_model.py` — new class
  `TestAsyncPollDoesNotLeakDictIntoLoopItem` with 3 tests

**Verification**: 2498 tests pass (was 2495, +3 new). ruff format, ruff check,
mypy strict — all clean.

## Integration Test Expansion (2026-06-26)

**Task**: Added 17 new integration tests across 8 test classes in
`tests/integration/test_playbook_parser.py`, covering previously untested
playbooks.

**Playbooks now covered**:
- `10-free-strategy` — `TestFreeStrategy` (2 tests)
- `11-role-grouping` — `TestRoleGrouping` (2 tests)
- `27-single-host-localhost` — `TestSingleHostLocalhost` (2 tests)
- `28-host-pattern-filtering` — `TestHostPatternFiltering` (2 tests)
- `29-tags` — `TestTags` (3 tests: `--tags install`, `--tags configure`, `--tags all`)
- `30-include-vs-import` — `TestIncludeVsImport` (2 tests)
- `31-block-tasks` — `TestBlockTasks` (2 tests)
- `33-mixed-warnings-execution` — `TestMixedWarningsExecution` (2 tests)

**Pattern**: Each test class follows the established convention:
- `@requires_ansible` decorator on each test method
- `run_ansible_playbook()` helper with `extra_args` for flags like `--tags`
- `parse_jsonl_output()` to feed through `PtyStreamParser` + `RunState`
- Assertions on `run_state.status`, `len(run_state.plays)`, `len(play.tasks)`

**Key insight**: The `run_ansible_playbook()` helper already supports
`extra_args` — `--tags` filtering tests pass `["--tags", "install"]` etc.
No changes needed to the helper.

**Pre-existing failures** (unrelated): 6 tests + 1 error from
`_EOF_WATCHDOG_S` import error and `_line_is_stats_event` NameError in
other test files. New tests: 17/17 pass.

## R7 Ctrl-C Race Guard (2026-06-26)

**Task**: Fixed the race where KeyboardInterrupt between `_drive()`
returning and `run_playbook()` returning overwrites a child's clean
exit code with unconditional 130.

**Fix** (`src/ansible_aom/ansible/runner.py`):
1. Pre-declared `exit_code: int | None = None` BEFORE the `_drive()`
   call so the except branch can read it.
2. In the `except KeyboardInterrupt` handler, added a guard: if
   `child is not None and not child.isalive() and child.exitstatus
   is not None`, use `child.exitstatus` as the exit code instead
   of 130. A still-running child falls through to the existing
   130 path (genuine cancel).

**Tests added** (`tests/unit/test_runner_ctrl_c_race.py`):
- `TestCtrlCAfterChildExitedCleanly` (2 tests) — covers window #2
  (race after clean exit) for both exit_code=0 and exit_code=2.
- `TestCtrlCDuringActiveRun` (1 test) — pins that window #1
  (mid-run SIGINT) STILL returns 130 (fix MUST NOT mask cancels).

**Tests updated** (`tests/integration/test_ctrl_c_race.py`):
- `test_signal_after_drive_still_maps_to_130` was renamed to
  `test_signal_after_drive_returns_real_exit_code` and flipped to
  assert the new contract (completion wins).
- Added `test_signal_after_drive_returns_non_zero_exit_code` for
  the failure case (child exits 2, SIGINT during cleanup).
- Updated module docstring and class docstrings to reflect R7
  settled spec: completion wins.

**Pattern**: To test a KeyboardInterrupt handler with a real
`pexpect.spawn`, use a `_FakeSpawn` class that emits fixed JSONL
lines and exposes `exitstatus`. The fixture is much faster than a
real subprocess and lets us deterministically simulate race
conditions. See `tests/unit/test_runner_ctrl_c_race.py::_FakeSpawn`.

**Gotcha**: The `MagicMock.side_effect = [KeyboardInterrupt(), None]`
one-shot iterator pattern is required when the SIGINT fires INSIDE
the runner's `handle_completion` call: the first invocation raises
(SIGINT), the second (the recovery call in the except branch) must
NOT re-raise or the test infinite-loops. A bare `side_effect =
KeyboardInterrupt` would re-raise forever.

**Gotcha 2**: When using `_FakeSpawn` to drive the runner, the
`exit_code` constructor argument must actually be stored and
returned from `close()` — otherwise `child.exitstatus` is always 0
and the R7 race guard (which reads `child.exitstatus`) reports the
wrong code. Caught by writing two tests (one for exit=0, one for
exit=2) up-front.

**Verification**: 1741 unit tests pass, 377 integration tests
pass, mypy strict + ruff lint + ruff format all clean for changed
files. The pre-existing R8 (EOF watchdog) xfail is unrelated —
`test_no_eof_hang.py` was xfail-marked in a prior session.

## 2026-06-26 R6 done — closing gap

`.sisyphus/notepads/plans/robustness.md` R6 closed. Pexpect now uses
`codec_errors="surrogateescape"`; renderer display path normalises
surrogates to U+FFFD via `_truncate_msg` → `_replace_surrogates` in
`compact/format.py`. 9 new tests in
`tests/integration/test_r6_encoding_roundtrip.py`. The parser gained
a `_safe_loads` shim (orjson for clean lines, stdlib json for
surrogate-bearing lines) so orjson's "surrogates not allowed" rejection
doesn't drop invalid-UTF-8 events on the floor.

## Nested include_role: podman inside angie_ssl_terminator fix (2026-06-26)

**Bug**: When an `include_role: podman` stub lives inside another role
(e.g. `angie_ssl_terminator : include_role: podman`), the runtime task
arrives with a deep prefix like `"angie_ssl_terminator : podman : Install podman"`.
`runtime_role_from_task_name` returns the **outermost** prefix (`"angie_ssl_terminator"`),
which equals `parent.role`. The grafting branch takes the `else` path,
sets `graft_role = parent.role = "angie_ssl_terminator"`, and calls
`_graft_role_pending_siblings(role_name="angie_ssl_terminator", ...)`.
That discovers the wrong role and either grafts nothing (empty children)
or grafts `angie_ssl_terminator`'s tasks instead of `podman`'s.

**Fix** (`src/ansible_aom/core/run_state.py`): Override `runtime_role`
after extraction when the parent is an include_role/import_role stub.
Use `_extract_role_from_include_stub(parent.name)` (already at line 53)
to get the actual target role (`"podman"`).

**Secondary fix**: `_graft_role_pending_siblings` had a dedupe check
`if prefixed == current_task_name` which fails when `current_task_name`
is deeper than `role_name : role_task_name` (e.g. the
`angie_ssl_terminator : podman : Install podman` case above).
Added a deeper-prefix match: compare
`current_task_name.rsplit(" : ", 1)[-1] == role_task_name` so the
current task isn't duplicated under its own bare form.

**Note on `strip_role_prefix`**: only strips ONE level of prefix, so
not suitable for arbitrarily deep role chains. Use
`rsplit(" : ", 1)[-1]` instead.

**Test** (`tests/unit/test_dynamic_expansion.py::TestIncludeRoleStubInsideOuterRole`):
creates a preflight with parent `angie_ssl_terminator : include_role: podman`
(role=angie_ssl_terminator), fires task_start for the stub, then for
`angie_ssl_terminator : podman : Install podman`. Asserts:
- 3 children grafted (Install, Configure, Start podman)
- Every child has `role="podman"`, `parent_role="angie_ssl_terminator"`

**Verification**: 2837 unit + integration tests pass. The single
failing test `test_tree_projection_shows_pending_role_tasks` is a
PRE-EXISTING failure (confirmed by reverting run_state.py changes —
still fails) — caused by a duplicate `"Install podman"` appearing in
the tree projection (once as pending graft, once as running) for an
unrelated include_role test that uses parent="Apply podman role".
Not caused by this fix and outside the scope of the current task.

## no_log: true → Empty FAILED! Line (2026-06-26)

**Bug**: When a failing task has `no_log: true`, ansible-core strips
`msg`/`module_stderr`/`stderr`/`module_stdout`/`stdout` and replaces
the result with a single `"censored"` field. AOM's `_extract_error_msg`
only walked those 5 fields, so it returned `""`, callers dropped the
`=>` tail, and the user saw `fatal: [host] (0.1s): FAILED!` with no
explanation.

**JSONL event shape** for a `no_log: true` failure:
```json
{"_event": "v2_runner_on_failed",
 "hosts": {"privatepodman": {
   "_ansible_no_log": true,
   "censored": "the output has been hidden...",
   "failed": true,
   "exception": "(traceback unavailable)"
 }}}
```

**Fix** (`src/ansible_aom/compact/renderer.py:_extract_error_msg`):
1. After the standard 5-field walk, check `result.get("_ansible_no_log") is True`
   → return `"(no_log)"` (the project's canonical redacted marker from
   `core/redaction.py` Layer 1).
2. As a fallback, check `result.get("censored")` for non-empty string
   content (edge case where `_ansible_no_log` is not set but `censored`
   exists).

**Key decisions**:
- Return `"(no_log)"` rather than the raw `censored` text (ansible's
  default is "the output has been hidden due to the fact that 'no_log:
  true' was specified for this result" — too verbose). The project
  already standardized on `(no_log)` in `core/redaction.py` line 242.
- Priority order unchanged: `msg` > `module_stderr` > `stderr` >
  `module_stdout` > `stdout` > `_ansible_no_log` > `censored`.
- The `_ansible_no_log` check is BEFORE the `censored` fallback so that
  the canonical `(no_log)` marker always wins when the flag is set,
  regardless of what ansible put in `censored`.
- No changes to callers (`v2_runner_on_failed`, `v2_runner_on_unreachable`,
  `_format_loop_item_line`) — they already render `=> {msg}` when
  `_extract_error_msg` returns non-empty.

**Tests added** (`tests/compact/test_error_message_extraction.py`):
- `test_failed_no_log_shows_censored_marker` — `_ansible_no_log=True`,
  no other fields → `FAILED! => (no_log)`
- `test_failed_no_log_msg_still_wins` — `_ansible_no_log=True` + `msg`
  field → `msg` still takes priority
- `test_failed_censored_fallback_when_no_other_fields` — `_ansible_no_log=False`
  + `censored` field → uses raw `censored` text
- `test_unreachable_no_log_shows_censored_marker` — unreachable variant
  → `UNREACHABLE! => (no_log)`
- `test_failed_loop_item_no_log_shows_censored_marker` — loop item with
  `_ansible_no_log=True` → `failed: [host] => (item=…) => (no_log)`

**Verification**: 2867 tests pass (was 2862, +5 new). mypy strict, ruff
lint, ruff format — all clean. Live repro confirmed: the bug playbook
now shows `FAILED! => (no_log)` instead of bare `FAILED!`.

## 2026-06-29: Verbosity-feature inventory (read-only exploration)

Goal: capture the current state of AOM's JSONL parsing, data model,
post-run inspect capability, and any verbosity handling to inform the
"capture verbose details for post-run inspect" feature.

### Source layout (src/ansible_aom/)
- ansible/        — callback plugin (aom_jsonl.py subclasses ansible.posix.jsonl), pexpect runner, preflight parser
- cli.py          — argparse entry; `--verbose` (AOM debug); `-v`/`-vv`/`-vvvv`/`-vvvvvv` REMAINDER to ansible-playbook
- compact/        — Rich Live renderer (default nom-style)
- core/           — pure logic (models, parser, run_state, event_types, inspect_model, redaction, log_filter, ...)
- drivers/        — live + replay event sources
- formats/        — `--format json` output
- inspect/        — `aom inspect [--text|--debug|prune]` CLI + text renderer + overhead formatter
- renderer/       — protocol + factory (picks compact vs json renderer)
- rerun/          — `aom rerun` CLI
- session/        — recording-on-disk + list/load helpers
- tui/            — `--tui` Textual app + InspectApp three-pane browser

### JSONL event surface (core/event_types.py + core/run_state.py)
TypedDict `JsonlEvent` (total=False): `_event`, `_timestamp`, `playbook`,
`play` (JsonlPlay: id, name, duration), `task` (JsonlTask: id, name, path,
role, action, args), `host`, `hosts` (dict of JsonlHostResult: ok,
changed, failed, skipped, unreachable, skip_reason, msg,
_ansible_verbose_always, _ansible_no_log), `stats` (JsonlHostStats: ok,
changed, failures, skipped, unreachable, rescued, ignored),
`custom_stats`, `global_custom_stats`, `res`.

Event types actually handled (RunState.handle_event handler_map, parser
phase boundaries, log_filter map, history/summary consumers):
- v2_playbook_on_start            (parser boundary; sets start_time)
- v2_playbook_on_play_start       (create PlayRunState, finalize prior play)
- v2_playbook_on_task_start       (mark task RUNNING, graft dynamic includes)
- v2_playbook_on_handler_task_start (same as task_start)
- v2_runner_on_start              (per-host RUNNING, free-strategy only)
- v2_runner_on_ok                 (terminal ok/changed)
- v2_runner_on_failed             (terminal failed; honors
                                   _ansible_verbose_always.ignore_errors)
- v2_runner_on_skipped            (terminal skipped)
- v2_runner_on_unreachable        (terminal unreachable; RunState -> FAILED)
- v2_runner_item_on_ok / _failed / _skipped   (live loop progress only;
                                   do NOT change final status — additive
                                   signal emitted by bundled aom_jsonl
                                   callback subclass)
- v2_playbook_on_stats            (final stats event; parser boundary)

### Data model (core/models.py + core/run_state.py + core/inspect_model.py)
- Stdlib `@dataclass` everywhere — NOT Pydantic. Pydantic is only in
  `core/config.py` for AppConfig / RedactionConfig / StatusBarConfig /
  WarningsConfig (loaded from ~/.config/aom/config.yaml).
- Dual-track architecture: Definition classes (immutable, from
  `--list-tasks` / `--list-hosts`) + State classes (mutable, from JSONL).
- `TaskDefinition` carries: name, role, tags, play_id, play_order,
  task_order, is_dynamic, uuid, path, children, parent_role.
- `PlayDefinition`: id, name, hosts, resolved_hosts, tasks.
- `TaskRunState`: task_id, name, status, hosts (dict[hostname,
  HostRunState]), start_time, end_time, path, parent_role.
- `HostRunState`: hostname, status, changed, message, start_time,
  end_time, loop_items_done.
- `PlayRunState`: play_id, name, status, tasks, detected_strategy,
  window_start, window_ordinal.
- Inspect view models (core/inspect_model.py — all `@dataclass(frozen=True)`):
  RunSummary, TaskTreeNode, DetailBlock, LoopItem, StatusCounts.
  `DetailBlock` exposes ONLY: task_name, file_line, host, duration,
  status, action, msg, failed_items, ok_items, module_stdout,
  module_stderr, warnings, raw_event. **No module_args, no diff.**

### Existing post-run inspect feature — YES, fully built
- CLI: `aom inspect [--text|--debug|--json] [--session ID]` /
  `aom inspect prune --days N` (src/ansible_aom/inspect/cli.py)
- TUI: `aom inspect` → three-pane InspectApp (Runs / Tasks / Detail)
  (src/ansible_aom/tui/screens/inspect.py, 1039 lines)
- Builders: src/ansible_aom/core/inspect_model.py — pure, no Textual,
  no I/O. Used by both TUI and text renderer.
- Text renderer: src/ansible_aom/inspect/text.py — deterministic
  ANSI-free output (header, failures, stderr tail).
- Replay: src/ansible_aom/drivers/replay.py + src/ansible_aom/core/replay.py.
- Rerun: src/ansible_aom/rerun/cli.py — reads session, derives host set,
  rebuilds ansible-playbook argv with original ansible_args plus
  appropriate --limit.
- Diagnostics overlay: `aom inspect --debug` reads diagnostics.json.

### Verbosity handling — current state
- **`--verbose` is AOM debug only** (cli.py:290-294). `-v`/`-vv`/`-vvvv`/
  `-vvvvvv` flow through `ansible_args` argparse REMAINDER untouched
  (cli.py:341). Runner just builds `ansible-playbook <playbook> <args>`.
- `core/run_config.py` ignores `-v` / `-vv` / `-vvv` / `-vvvv` /
  `--verbose` / `--syntax-check` when computing the run-config key
  (so two invocations differing only in verbosity bucket together for
  history matching).
- **Re-archiving**: `session/store.py RECORD_EVENT_KEEP_FIELDS` does NOT
  include `invocation` / `diff` / `module_args` / `results` / `msg` /
  `stdout` / `stderr`. Only `_event`, `_timestamp`, `task`, `play`,
  `hosts` (top-level only), `changed`, `failed`, `skipped`,
  `unreachable`, `duration`, `stats`. So even though ansible.posix.jsonl
  emits full `result._result` for every host on every event, AOM
  DROPS module_args, diff, msg, stdout, stderr, results[] before
  writing to events.jsonl.
- `_lean_event` (store.py:74) explicitly strips "the bulky `msg` /
  `module_stdout` / full `results[]` array … so a 1 MB event doesn't
  write 1 MB to disk."
- `core/redaction.py` only fires when callers invoke `redact_event()`,
  but **nothing currently calls it** — it's defined and tested
  (Layer 1-4 tests in tests/unit + tests/integration/test_redaction.py)
  but not wired into the recording path.
- `run_state.py:1208-1212` reads `_ansible_verbose_always.ignore_errors`
  — this is the ONLY field from the verbose branch that currently
  affects behavior, and only because it lets a "failed" task with
  ignore_errors render as OK.
- Inspect TUI's Detail pane renders `msg`, `module_stdout`,
  `module_stderr`, `warnings`, `failed_items`/`ok_items` — but those
  fields are STRIPPED by `RECORD_EVENT_KEEP_FIELDS` before they ever
  hit disk, so the inspect view shows "(module returned no message,
  stdout, or stderr)" for everything that didn't carry
  `changed`/`failed`/`skipped`/`unreachable`.

### Implication for the planned feature
JSONL already carries the full result dict; everything else is a
display/strip decision. The change "capture verbose details for
post-run inspect" reduces to:
1. Decide which fields in `hosts[host].*` matter for `-v`/`-vv`/`-vvv`
   users (msg, stdout_lines, stderr_lines, invocation.module_args,
   diff, results[] are the standard candidates per ansible
   conventions; see `.sisyphus/notepads/research/decisions.md`
   "Verbosity × JSONL" mapping table).
2. Decide where they live:
   - Option A: extend `RECORD_EVENT_KEEP_FIELDS` so they hit disk, then
     extend `DetailBlock` in inspect_model to expose them with a
     `--verbose` toggle in the TUI Detail pane.
   - Option B: capture them into a sidecar file
     (`verbose.jsonl` per task/host) loaded only by `aom inspect
     --verbose`. Smaller live-view surface but more moving parts.
   - The current `_lean_event` rationale (1 MB events, OOM on read) is
     real — adding `results[]` and `module_stdout` back at scale needs
     either a per-event size cap or an opt-in.
3. Wire `redact_event` into the recording path so the new fields
   don't leak secrets through inspect (already-tested function;
   dead code today).
4. Surface the captured-verbosity level in `meta.json` (env snapshot
   already includes ANSIBLE_STDOUT_CALLBACK; could add
   `ANSIBLE_VERBOSITY` or detect `-v` count in `ansible_args`).

### Cross-cutting constraints (from AGENTS.md / ARCHITECTURE.md)
- `core/` may not import from `compact/`, `tui/`, `formats/`, `renderer/`.
  All verbosity-aware logic and the new field schema must live in `core/`
  so every renderer (compact, TUI, json, inspect) can read it.
- Inspect builders MUST stay pure (no Textual, no I/O) — current
  inspect_model.py is the contract; new verbose fields belong there.
- Pydantic exists only for config; do NOT introduce Pydantic into
  event / state models — stdlib dataclasses are the project convention.
- Session on-disk format is `events.jsonl` (JSONL) + `meta.json` +
  `stderr.log` + `diagnostics.json`. Adding a new file or extending
  RECORD_EVENT_KEEP_FIELDS both count as "change the on-disk
  format" — existing sessions stay readable because missing fields
  default to None.
- Tests must pass without ansible-core (unit/) and verify end-to-end
  with it (integration/, marked `needs_ansible`).
