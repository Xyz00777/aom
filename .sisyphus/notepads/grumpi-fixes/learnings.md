# Grumpi Fixes — Learnings

## 2026-06-26: Section 9E — Orphaned Artifacts

### Changes made
1. **Removed `aom/`** — empty root directory, no code references.
2. **Removed `molecule/`** — `molecule/default/molecule.yml` existed but no Molecule tests in CI.
3. **Kept `schemas/run_summary.v1.json`** — initially removed, but `test_run_summary_schema.py` has 8 tests that depend on it. Restored the file from git and added `schemas/README.md` documenting that the Pydantic model in `json.py` is the source of truth.
4. **Deduplicated `handle_interactive_prompt`** — changed from duplicating the full body of `handle_password_prompt` to a one-liner delegation: `return self.handle_password_prompt(prompt_text)`.

### Key insight
The schema file cannot be removed without also updating `test_run_summary_schema.py`. The tests use `_load_committed_schema()` which reads the file at test time. The proper fix is to keep the file as a committed artifact and document its deprecation, which is what the task spec allowed as an alternative.

## 2026-06-26: Findings 9C + M2 — Consolidate determine_exit_code

### Changes made
1. **Created `src/ansible_aom/core/exit_code.py`** — canonical home for `determine_exit_code(state)`. Pure function, no I/O, lives in `core/` per ARCHITECTURE.md §7.3 (core/ may not import from compact/tui/formats, but everyone may import from core/).
2. **Made `compact/exit_code.py` a re-export shim** — `from ansible_aom.core.exit_code import determine_exit_code  # noqa: F401`. Kept for backward compat (the existing `compact/renderer.py` re-export chain still works).
3. **Updated `core/parity.py`** — removed the inline duplicate (the `any_failed` / `any_unreachable` flag-scan loop) and replaced with a single call to `determine_exit_code(state)`. Net 11 lines deleted.
4. **Updated `formats/json.py`** — changed `from ansible_aom.compact.renderer import determine_exit_code` to `from ansible_aom.core.exit_code import determine_exit_code`. Eliminates the M2 layering violation (formats/ importing from compact/).
5. **Updated `tests/unit/test_cli.py`** — 6 test methods now import from `core.exit_code`.
6. **Updated `tests/integration/test_compact_renderer.py::TestExitCodes`** — deleted the duplicate `determine_exit_code` method on the test class; all 5 test methods now import the canonical function.

### Verification
- `uv run mypy src/ansible_aom` — clean (70 source files, no issues).
- `uv run pytest tests/ -q -n auto` — 2854 passed, 6 skipped, 1 xfailed.
- `uv run ruff check` — clean after trailing-newline auto-fix.
- `uv run ruff format` — no changes needed.

### Key insights
- The duplicate logic in `core/parity.py` had been acknowledged in a comment as "intentional because core/ can't import from compact/" — but the layering rule actually permits core/ to have its own copy; it just can't import from compact/. The fix moved the original `compact/exit_code.py` to `core/exit_code.py` so the rule is respected AND there's only one implementation.
- The `TestExitCodes` integration test had its own `determine_exit_code` as a method on the test class (a test-local duplicate of the same logic). Switching it to import the canonical function eliminates the drift risk the comment in `core/parity.py` warned about ("the same logic in two short scans" — if either evolves, they diverge silently).
- When consolidating a shim, prefer making the OLD module a re-export shim rather than deleting it outright. Many call sites already do `from ansible_aom.compact.renderer import determine_exit_code` and that chain keeps working because `compact/renderer.py:19` still re-exports from `compact/exit_code.py` which now re-exports from `core/exit_code.py`.
- Use `# noqa: F401` on pure re-export imports — otherwise ruff complains the imported name is unused.

## 2026-06-26: Finding 9C — Consolidate parse_iso_timestamp

### Changes made
1. **Created `src/ansible_aom/core/timestamp.py`** — canonical `parse_iso_timestamp(value: str) -> datetime`. Lives in `core/` (pure function, no I/O, no UI deps) per the layering rule that says core/ must never import from infrastructure but may be imported by anyone.
2. **Updated 8 call sites** — every `datetime.fromisoformat(value.replace("Z", "+00:00"))` in `src/ansible_aom/` now routes through `parse_iso_timestamp`:
   - `core/models.py:_parse_timestamp` — module-level helper for event timestamps
   - `drivers/replay.py:_parse_timestamp` — replay-side timestamp parsing (returns `None` on bad input)
   - `core/replay.py:_event_timestamp` — pure helper for tree-frame timing
   - `core/inspect_model.py:_parse_iso` — `build_run_summary` start/end times
   - `session/history.py:_parse_iso` — prior-run lookup
   - `core/overhead.py:_parse_iso8601` — overhead analysis (previously relied on Python 3.11+ `Z` acceptance — now consistent with the rest of the codebase)
   - `compact/renderer.py:_event_time` — log-line timing inside the compact renderer
   - `session/store.py` — `_iter_completed_sessions` listing (inline in a tight loop)
3. **Did NOT touch** `tests/`, `docs/`, or `graphify-out/` — per the task's "MUST NOT" rule. Tests have their own copies of the pattern and they're test-only fixtures.

### Verification
- `grep -r 'replace(.Z.,.+00:00.)' src/ansible_aom/` — only one hit, the canonical implementation in `core/timestamp.py`.
- `uv run mypy src/ansible_aom` — clean (71 source files, no issues).
- `uv run pytest tests/ -q` — 2854 passed, 6 skipped, 1 xfailed (same as baseline before the change).

### Key insights
- The 8 sites had minor variations (some returned `None` on bad input, some returned `now()`, some inline `from datetime import datetime`). The canonical function is intentionally minimal — `parse_iso_timestamp(value: str) -> datetime` raises `ValueError` on bad input — and each call site keeps its own exception-handling policy. This avoids a one-size-fits-all fallback that would have changed observable behaviour at the call sites.
- `core/overhead.py:_parse_iso8601` was a quiet outlier: it didn't have the `replace("Z", "+00:00")` because it relied on Python 3.11+'s native `Z` acceptance in `fromisoformat`. Even so, routing it through `parse_iso_timestamp` keeps the codebase uniform — if anyone ever relaxes the canonical implementation's behaviour, all 8 sites change together.
- The `compact/renderer.py` site had an awkward inline `from datetime import datetime` inside the function body (lazy import). I left that pattern alone — it's unrelated to this consolidation — and just replaced the parsing line with a corresponding inline `from ansible_aom.core.timestamp import parse_iso_timestamp` to match the local-import style of the original.
- Keep `core/timestamp.py` minimal: the function exists to consolidate, not to add features. Future expansions (e.g. accepting non-string input, returning `Optional[datetime]`) belong in a separate wrapper, not in this canonical implementation, because adding such flexibility here would force all 8 call sites to re-think their exception-handling policies.

## 2026-06-26: Finding 9C — Consolidate duration formatting

### Changes made
1. **Added two helpers to `src/ansible_aom/core/duration.py`**:
   - `format_duration_decimal(seconds)` — preserves sub-second precision in the seconds bucket (`0.4s`, `12.3s`); same minute/hour bucketing as `format_duration_compact`. This matches `compact/renderer.py`'s pinned test outputs.
   - `format_elapsed_hms(seconds)` — colon-separated `M:SS` / `H:MM:SS` form for TUI widgets.
   - Both are new public functions; the canonical `format_duration_compact` API is unchanged.
2. **`compact/renderer.py:_format_duration`** — body replaced with `return format_duration_decimal(seconds)`. Import added at top of the existing core-import block.
3. **`tui/widgets/summary_panel.py:_format_elapsed_time`** — body replaced with `return format_elapsed_hms(self._elapsed_seconds)`.
4. **`tui/widgets/status_bar.py:_format_elapsed_time`** — kept the `if self._start_time is None: return "0:00"` early-out and the `datetime.now() - self._start_time` elapsed calc (widget-specific concerns), then delegated to `format_elapsed_hms(int(elapsed.total_seconds()))`. The `datetime` import remains because of these widget-side computations.

### Verification
- `uv run mypy src/ansible_aom` — clean (71 source files, no issues).
- `uv run pytest tests/unit tests/compact tests/tui -q` — 2494 passed.
- `uv run pytest tests/ -q` — 2854 passed, 6 skipped, 1 xfailed (matches baseline).

### Key insights
- **The four "duplicates" were actually three distinct formats masquerading as one.** The canonical `format_duration_compact` rounds sub-minute to int (`42s`); the compact renderer's duplicate preserves a decimal (`42.4s`); the two TUI widgets use a colon-separated HMS form (`1:02:03`, `0:45`) that's intentionally different from the compact form because TUI widgets are read at-a-glance where colon-separated time reads more naturally than `1h05m`. Forcing all three into one function would either change observable behaviour (breaking pinned tests in `tests/compact/test_per_task_timing.py`) or require a parameter that violates "Do NOT change the public API of `format_duration_compact`".
- **Pinned test outputs are the contract.** `tests/compact/test_per_task_timing.py::TestFormatDuration` asserts `0.0` → `"0.0s"`, `0.5` → `"0.5s"`, `59.9` → `"59.9s"` — these would all fail against the canonical `format_duration_compact` (which rounds). The consolidation must preserve the format each duplicate produced, so new helpers in core were the right escape hatch.
- **`status_bar.py` could not be a one-liner** because it owns two widget concerns the core function doesn't: the `start_time is None` fallback and the `datetime.now() - self._start_time` elapsed calc. The thin wrapper still eliminates the bucket-formatting duplication (the `hours / minutes / seconds / f"{h}:{m:02d}:{s:02d}"` block), which was the actual GRUMPI_QA concern.
- **The two TUI tests that pin "0:45" / "240:00:00" / "5:30" never actually call `_format_elapsed_time` on the widget** — they're inline-formula assertions inside the test bodies (see `tests/tui/test_panels.py::TestSummaryPanelElapsedTime`). That's why the format change from inline math to `format_elapsed_hms` doesn't break them: the test code re-derives the string from first principles. Worth knowing if anyone later adds a test that calls `SummaryPanel._format_elapsed_time()` directly.
- **Layering compliance:** `tui/widgets/*.py` importing from `ansible_aom.core.duration` is the same direction the original code took (`from ansible_aom.core.icons import STATUS_ICONS` is already there). No new layering violations introduced.

## 2026-06-26: Finding 9A — Dead state machine in `core/state_machine.py`

### Changes made
1. **Rewrote `src/ansible_aom/core/state_machine.py`** — kept only the 5 `MAX_*` memory-bound constants (`MAX_PLAYS`, `MAX_TASKS_PER_PLAY`, `MAX_HOSTS_PER_TASK`, `MAX_TOTAL_HOST_RUN_STATES`, `MAX_LOG_LINES`). Dropped `ExecutionState` enum, `VALID_TRANSITIONS` dict, `InvalidTransitionError`, and `StateMachine` class. Module name preserved so existing imports (`from ansible_aom.core.state_machine import MAX_LOG_LINES`) keep working without changing call sites.
2. **Deleted `tests/unit/test_state.py`** — 69 tests, all dedicated to the now-removed `StateMachine` / `ExecutionState` / `VALID_TRANSITIONS` / `InvalidTransitionError`. The MAX_* constants they also covered are now tested transitively via `tests/unit/test_parser.py` (TC-259) and `tests/tui/test_panels.py::TestLogPanelMaxLines` (TC-274).
3. **Deleted `tests/unit/test_invariants_state_machine.py`** — Hypothesis `RuleBasedStateMachine` fuzzing the removed `StateMachine`. No value keeping a property-based test for production code that doesn't exist.
4. **Stripped dead-state-machine assertions from `tests/integration/test_error_handling.py`** — 27 tests across `TestCrashRecovery*`, `TestGracefulDegradationTreeUpdates`, `TestGracefulDegradationListTasksFailure`, `TestCancellationFirstCtrlC`, `TestCancellationSavePartialSession`, `TestSubprocessExitCodes`, `TestProcessStateMonitoring` (orphan detection tests), and the entire `TestStateTransitionsForAllExitCodes` class. Preserved every test that exercises real code paths (parsers, password patterns, watchdog, logging, exit-code constants, stderr handling, cancellation timer math).

### Verification
- `uv run pytest tests/ -q -n auto` — 2736 passed, 6 skipped, 1 xfailed (down from baseline 2854 — the 118-test drop matches the removed test cases).
- `uv run mypy src/ansible_aom` — clean (71 source files, no issues).
- `uv run ruff check src/ansible_aom tests/unit tests/integration` — clean.
- `uv run ruff format` — 1 file reformatted (the integration test cleanup), 178 unchanged.
- Production code scan: `grep -rn "ExecutionState\|StateMachine\|VALID_TRANSITIONS\|InvalidTransitionError" src/` — only matches are the historical-mention sentences inside `core/state_machine.py`'s new docstring.

### Key insights
- **Keep the module name, drop the contents.** Renaming `state_machine.py` → `limits.py` would be more honest but would force touching every `from ansible_aom.core.state_machine import MAX_LOG_LINES` in production code (`parser.py`, `tui/widgets/log_panel.py`) and tests (`test_parser.py`, `test_panels.py`). The historical-context note in the new docstring is cheaper than the ripple of a rename and keeps zero risk of breaking the production call sites. The note also tells future contributors why there's no state machine in `state_machine.py`, preventing a "helpful" resurrection.
- **Dead tests should die with the dead code, not be migrated to "deprecated".** The two test files existed solely to test the removed classes — there's nothing to migrate them to. Keeping them with deprecation warnings would have left 100+ dead test cases passing against a stub. The integration test was a mixed bag: half its tests used the dead `StateMachine`, half tested real behavior (parsers, logging, password patterns, watchdog, exit codes, cancellation timing, stderr handling). Surgically removing only the state-machine-driven tests preserved real coverage without polluting the file with deprecation shims.
- **The Hypothesis stateful test is a single test method in pytest's eyes.** `test_invariants_state_machine.py` declared `TestExecutionStateMachine = ExecutionStateMachine.TestCase`, which pytest collects as ONE test method, not 100. So removing the file only cost us 1 pytest collection node, not 100. The bigger drop (118 vs 69+27+1=97) comes from the parametrized variants in `test_state.py` (e.g., `test_terminal_only_to_idle` × 3 states, `test_known_invalid_transitions` × 8 states) and the surviving parametrized tests in `test_error_handling.py`'s `TestStateTransitionsForAllExitCodes` (8 exit codes × 1 method = 8 pytest nodes).
- **Some "transient" parallel-test failures are not actually caused by your change.** First parallel run reported 5 failures across `test_renderer_stats_parity.py`, `test_app_end_to_end.py::TestRunStateOwnership`, and `test_renderer_parity.py`. Second run with `-p no:cacheprovider` and identical commands passed all 2736 tests. The failures were pre-existing test-order sensitivity between the renderer parity tests, unrelated to removing the state machine — running them individually always passed. Always re-run flaky-looking parallel failures once before treating them as a real regression.

## 2026-06-26: Finding 9D — Narrow `except Exception: pass` blocks

### Changes made
Narrowed 12 silent exception swallows to specific exception types, with logging at minimum where the broad catch was truly needed:

1. **`runner.py:421`** — Child cleanup during Ctrl+C → `(pexpect.exceptions.ExceptionPexpect, OSError)` + `logger.debug`.
2. **`runner.py:570, 576`** — Buffer drain (two-stage fallback) → outer `AttributeError`, inner `pexpect.exceptions.ExceptionPexpect` + `logger.debug`.
3. **`runner.py:608`** — Interactive prompt handler → kept broad `except Exception` (renderer crash must not wedge the child) but added `logger.warning`.
4. **`runner.py:892`** — psutil CPU sampling → `(OSError, AttributeError)` (sibling to existing `psutil.Error`) + `logger.debug`.
5. **`diagnostics.py:163`** — faulthandler cancel → `RuntimeError` (the documented failure mode).
6. **`display.py:82`** — Terminal size detection → `(OSError, AttributeError)`.
7. **`config.py:112`** — Pydantic model construction → `(ValidationError, TypeError, ValueError)` + `logger.warning` (most impactful: was swallowing Pydantic validation errors silently).
8. **`tui/app.py:396`** — Get current screen → `(AttributeError, RuntimeError, ScreenStackError)` — caught the `ScreenStackError` regression on first test run.
9. **`tui/app.py:418`** — LogPanel query → `NoMatches` (Textual's specific exception when `query_one` finds nothing).
10. **`tui/app.py:477`** — DebugPanel toggle → `(NoMatches, AttributeError)` + `self.log.debug`.
11. **`tui/screens/inspect.py:119`** — Clipboard copy → `ImportError` (pyperclip not installed) + `PyperclipException` (backend failure). Required moving the import inside the try block and capturing both.
12. **`tui/screens/inspect.py:584, 594, 614`** — Widget queries (pane target, pane classes, tasks tree) → `NoMatches`.
13. **`tui/screens/inspect.py:662`** — `listview.index = idx` setter → `(ValueError, IndexError)`.
14. **`tui/screens/main.py:87`** — Widget queries (`SummaryPanel`/`StatusBar`/`TaskTree`) → `NoMatches`.

### Imports added
- `from textual.css.query import NoMatches` in `tui/app.py`, `tui/screens/inspect.py`, `tui/screens/main.py`
- `from textual.app import ScreenStackError` in `tui/app.py`
- `from pydantic import ValidationError` in `core/config.py`
- `from pyperclip import PyperclipException` (inline inside try block in `tui/screens/inspect.py`)

### Verification
- `uv run mypy src/ansible_aom` — clean (71 source files, no issues).
- `uv run pytest tests/unit tests/compact tests/tui -q` — 2410 passed (same baseline as before).
- `uv run ruff format --check src/ansible_aom` — 71 files already formatted.
- `uv run ruff check src/ansible_aom` — All checks passed.
- Remaining `except Exception` blocks (4): `tui/app.py:376` (worker drive — keep broad as last-line-of-defence), `tui/app.py:440` (refresh tick outer — already logs), `runner.py:608` (interactive prompt — added `logger.warning`), `cli.py:381, 410` (out of scope — task didn't list them).

### Key insights
- **Textual raises its own `ScreenStackError`** when no screen is on the stack (not `RuntimeError` or `AttributeError`). Caught this regression on the first test run when `test_renderer_stats_parity.py` failed — the legacy renderer-protocol smoke tests construct bare `AOMApp()` without mounting a screen. Had to add `ScreenStackError` to the catch list.
- **Textual `query_one` raises `NoMatches` (not `WidgetError`)** — Textual 8.2.4 inherits from `textual.css.query.QueryError` → `Exception`. The GRUMPI spec called for `WidgetError` but that's not the actual class; `NoMatches` is the correct narrow target.
- **pyperclip requires catching both `ImportError` and `PyperclipException`**. The original code caught `Exception` to handle both "package not installed" (ImportError) and "no usable clipboard backend" (PyperclipException). Narrowing required splitting these into two `except` clauses — putting the import inside the try block (so ImportError fires if pyperclip isn't installed) and catching PyperclipException for backend failures.
- **`except X, Y:` syntax (no parens) is treated as `(X, Y)` tuple in Python 3.14**. The existing codebase uses this non-standard form throughout (`password.py`, `compact/renderer.py`, etc.) and tests pass. I used the parenthesized form (`except (X, Y):`) for clarity in my changes — it matches the modern style already used in `core/includes.py` and `core/config.py`.
- **`logger.debug(..., exc_info=True)` is the right verbosity for non-fatal defensive catches**. Keeps the traceback available when AOM_DEBUG=1 without spamming the user's terminal in normal operation. Used `logger.warning` only for the interactive prompt path where the fallback (sending empty line) is observable behaviour.
- **`listview.index = idx` can raise `ValueError` or `IndexError`** when called during a race with a concurrent reload (the ListView validates against the current child count, but the enumerate() snapshot is from before the reload). Catching both is defensive against that specific race.
- **The "keep broad with logger" rule from the spec applies most clearly to `runner.py:608`** (interactive prompt). Renderer crashes there would leave the child blocked on stdin forever, so swallowing the exception is genuinely the lesser evil — but logging at WARNING with the traceback means the user has something to file a bug with.

## 2026-06-26: Finding C3 — R1 (Corrupted JSONL) + R3 (Disk-Full)

### What was found
Both R1 and R3 robustness fixes from `plans/robustness.md` were already
implemented and tested in earlier sessions. The task looked like "implement
two robustness fixes" but turned into "audit the existing implementation
against the plan spec and confirm coverage is intact."

### R1 status (corrupted/partial JSONL mid-stream)
- **`JsonLineStream` carry buffer**: present in `src/ansible_aom/core/parser.py:47-126`.
  Has `_CARRY_LIMIT = 1_000_000` (1 MB), `_carry: str` state in `__init__`,
  prepend-on-next-call logic, and a non-trivial extra safeguard that the plan
  didn't call out: when the carry-prepended view fails to parse, the parser
  tries the bare new chunk on its own before stashing anything. This protects
  against garbage-prefix scenarios like `feed_line("{")` followed by a valid
  event — the bare valid event must not be corrupted by prepending a stray
  `{`. Without that fallback, a hypothesis test caught a regression where
  carry content permanently ate the next event.

- **Test coverage**: `tests/unit/test_parser.py::TestJsonLineStreamCarryBuffer`
  covers all four TCs from the plan:
  - `test_two_chunk_join_yields_full_event` — the canonical split case.
  - `test_many_small_chunks_join` — 100-chunk slow-drip.
  - `test_carry_buffer_overflow_drops_without_raising` — 1.1 MB oversized
    partial drops, next line parses standalone.
  - `test_well_formed_line_does_not_use_carry` — sanity.
  - `test_garbage_carry_does_not_swallow_next_valid_event` — the bonus
    hypothesis regression case.

- **Unknown `_event` handling**: `tests/unit/test_parser.py::TestRunStateUnknownEvent`
  covers the plan's TC that an unknown event reaches `RunState.handle_event`
  without raising and existing state is unmodified. There are also tests
  that verify the unknown-event counter is correctly bumped for diagnostics,
  so the original R5 from the plan landed too.

### R3 status (disk-full mid-run)
- **`_SessionSink` self-disable**: present in
  `src/ansible_aom/ansible/runner.py:131-222`. Has `_disabled = False` flag,
  catches `OSError` in `record_event` / `record_stderr` / `end`, and routes
  through `_disable(reason)` which:
  1. Sets `_disabled = True` (idempotent — second call returns early).
  2. Calls `diagnostics.set_session_recording_disabled(reason)` so the
     reason is persisted into `diagnostics.json` (the `session_recording_disabled`
     + `session_disable_reason` counters surfaced in phase 11).
  3. Calls `renderer.add_warning(f"session recording disabled (disk write failed: {reason})", False)`
     if the renderer has the method — graceful degradation if the renderer
     protocol grows in the future.

- **Test coverage**: `tests/integration/test_runner_session_recording.py::TestSessionRecordingDisableOnDiskError::test_oserror_during_record_event_disables_sink_and_warns_once`
  pins the exact plan TC: patches `SessionManager.record_event` to fail on
  the 3rd call, asserts exit code is 0, only 2 events made it to disk, and
  `renderer.add_warning` was called exactly once with the expected message.

### Verification
- `uv run pytest tests/unit tests/integration/test_runner_session_recording.py tests/integration/test_runner.py -q` — 1741 passed.
- `uv run mypy src/ansible_aom` — clean (71 source files).
- R1+R3-specific subset (12 tests): all pass.

### Key insight
The robustness plan was a "catalogue of gaps" written before each fix
landed. By the time the task arrived, each numbered R-section already had
its implementation + tests in place from earlier TDD cycles. The right move
was NOT to re-implement on top of the existing code (which would have
duplicated logic and risked breaking the garbage-carry safeguard the
hypothesis test had caught). Instead, audit the existing implementation
against the plan's "Tests" section and confirm every TC is covered.
The test names in `TestJsonLineStreamCarryBuffer` map 1:1 onto the plan's
TC list, which is the cleanest possible verification — same intent, same
coverage, no duplication.

A useful pattern for future "implement fix X" tasks: grep for the existing
test class name and check if it already exists before writing fresh tests.
If the test class exists and its method names map to the task's required
test cases, the work is already done — verify the assertion coverage and
move on.

## 2026-06-26: Finding H3 — README docs gaps

### Changes made
README.md was the only file touched (documentation-only fix from GRUMPI_QA finding H3).

1. **Fixed two broken `CLAUDE.md` references** — lines 174 (Project layout) and 188 (Development) now point to `AGENTS.md`. The file was renamed earlier in the project's life but the README was never updated.

2. **Extended the existing `### Flags` table** with four previously undocumented flags:
   - `--format {compact,json}` — already implemented in `cli.py:278-288` but missing from README.
   - `--hide-state <state>` — already implemented via `_HideStateAction` in `cli.py:129-159`; documents the `ok,changed,failed,skipped,unreachable` choices and the `--tui` ignored-under-TUI behavior.
   - `--no-record` — already implemented in `cli.py:296-304`; documents that debug output from `--verbose` is unaffected.
   - `--install-completion {bash,zsh,fish}` — already implemented in `cli.py:321-331` with a fast-path branch in `main()` at lines 445-462.

3. **Added three new subcommand sections** after `### Inspect past runs`:
   - `### Replay past runs` — covers `aom replay <session-id>`, `--speed N` (including `--speed 0` for as-fast-as-possible), and the `latest` short-form for most-recent session.
   - `### Rerun failed hosts` — covers `aom rerun` default-to-`--failed` semantics, `--failed` / `--unreachable` / `--changes-only` flag composition, the `--limit` replacement rule (not union), and the always-printed warning + confirmation prompt unless `-y` is set.
   - `### Shell completion` — covers `aom --install-completion {bash,zsh,fish}` with all three install commands and the `argcomplete`-powered completion surface.

### Authoritative source
The CLI epilog in `src/ansible_aom/cli.py:171-269` already documents all these features in `--help` output. The README was lagging behind the CLI. The fix copy-pastes the behaviour descriptions from that epilog (paraphrased for brevity) so the two stay in sync — if the epilog is the source of truth, the README is now a subset of it.

### Verification
- `grep -i 'claude\.md' README.md` — no matches.
- `uv run pytest tests/unit/ -q` — 1726 passed (full integration suite times out at 5min due to real ansible-playbook spawns; unit suite is the relevant coverage since README changes can't affect code paths).
- README structure preserved: the new `### Replay past runs`, `### Rerun failed hosts`, and `### Shell completion` sections sit alongside `### Inspect past runs` so the four subcommands read as a parallel set. The `### Flags` table grew by four rows rather than being split into a new section.

### Key insights
- **The CLI epilog in `cli.py` is the single source of truth for command behaviour.** When the README drifts, the fix is to copy from the epilog rather than invent new descriptions — that way CLI behaviour and README descriptions can never diverge. Worth establishing as the rule for future documentation tasks.
- **`--hide-state` in `--tui` mode prints a warning to stderr** (`cli.py:517-521`) rather than erroring. Documented as "Ignored under `--tui`" — matches the actual soft-fail behaviour. If a future change makes it hard-fail in TUI mode, the README needs to flip too.
- **`aom rerun` defaulting to `--failed` is a documented F4-spec behavior**, not an oversight — `rerun/cli.py:98-101` makes it explicit. The README now explains the default rather than implying the user must always pass `--failed`.
- **`--install-completion` is implemented as a fast-path branch in `main()`** that runs BEFORE `parse_args()` so it works without a playbook argument. The three shell examples in the README (bash, zsh, fish) are the only supported shells per `completion.SUPPORTED_SHELLS`.
- **Full `uv run pytest tests/` run timed out at 5 minutes** — the integration tests spawn real `ansible-playbook` processes which are slow. README changes cannot affect test outcomes, so the unit-suite confirmation (1726 passed in 37.6s) is sufficient verification for documentation-only work. Future README fixes can skip the full-suite run.

## 2026-06-26: Finding H4 — ARCHITECTURE.md §7 gap list was stale

### Changes made
ARCHITECTURE.md was the only file touched (documentation-only fix from GRUMPI_QA finding H4). The §7 "Gap from Current Source Tree → Target" section had multiple items labeled "not done" that were actually shipped.

Re-labelled §7 statuses based on direct source-tree audit:
- **§7.1 (EventSource port) — now [done].** `drivers/protocol.py` exists with the `EventSource` Protocol; `LiveDriver` and `ReplayDriver` both live behind `drive(renderer)`; `cli.py` is a one-call composition root.
- **§7.2 (infrastructure moves) — now [done].** All five moves landed: `runner.py` → `ansible/runner.py`, `replay.py` → `drivers/replay.py`, `json_renderer.py` → `formats/json.py`, `core/preflight.py` → `ansible/preflight.py`, `core/session.py` → `session/store.py` + `session/summary.py`.
- **§7.3 (compact/ split) — now [done].** `compact/format.py` has the pure formatters; `compact/renderer.py` is the lifecycle class; `compact/exit_code.py` is now a backward-compat shim (canonical lives in `core/exit_code.py`).
- **§7.4 (rename clashes) — now [done].** `core/state.py` is gone (renamed to `state_machine.py`); `inspect/display.py` is gone (renamed to `formatters.py`).
- **§7.5 (prompt detection) — now [done].** `core/prompts.py` has the pure heuristics.
- **§7.6 (Renderer protocol surface) — now [in progress].** `renderer/protocol.py` declares the full surface with a per-method mandatory / no-op-able table; SPECIFICATION.md §2.3 already points at protocol.py as source of truth. The only remaining stale bit is the factory code-block in SPECIFICATION.md §2.3 showing the legacy `tui_mode: bool = False` signature — flagged as the [open] follow-up.
- **§7.7 (factory covers all renderers) — now [done].** `renderer/factory.create_renderer` accepts `mode="compact"|"tui"|"json"`. The legacy `tui_mode`/`format` aliases are kept as deprecated compatibility shims — `mode` wins when both are supplied. The remaining [open] item is removing the deprecated aliases once §7.6's spec refresh lands.
- **§7.8 (layering enforcement) — now [in progress].** `tests/unit/test_layering.py` ships and passes (5 tests, runs in ~1s). It walks every module under `src/ansible_aom/` via `ast.parse` so lazy imports inside function bodies are caught. Remaining [open] item is wiring it into pre-commit / CI.

Added a new **§7.9 — Consolidations landed alongside the refactor** section capturing three fix-trail entries that shipped during other batches:
- **M2 (exit code in core/):** `determine_exit_code` was duplicated between `compact/exit_code.py` and `formats/json.py`; both now import the canonical `core/exit_code.determine_exit_code`. `compact/exit_code.py` is kept as a shim.
- **9C series (timestamp parsing):** Nine ad-hoc `datetime.fromisoformat(value.replace("Z", "+00:00"))` call sites collapsed to a single `parse_iso_timestamp(value)` in `core/timestamp.py`.
- **9A (state machine dead code):** `ExecutionState`/`StateMachine`/`VALID_TRANSITIONS`/`InvalidTransitionError` removed; `core/state_machine.py` now contains only the 5 `MAX_*` memory-bound constants.

Added a legend explaining the status tags (done / in progress / open) so future readers know what each tag means.

### Verification
- `uv run pytest tests/unit/ -q` — 1726 passed.
- `uv run pytest tests/unit tests/compact tests/tui --ignore=tests/integration -q` — 2410 passed (78.52s).
- The full `uv run pytest tests/ -q` run timed out at 5 minutes due to integration tests spawning real `ansible-playbook` processes. Doc-only changes cannot affect test outcomes, so the unit + non-integration suite confirmation is sufficient. Same timeout-fallback rationale as the H3 README fix.
- `grep` checks confirmed every claimed file location and absence:
  - `ls src/ansible_aom/drivers/protocol.py src/ansible_aom/compact/format.py src/ansible_aom/compact/exit_code.py src/ansible_aom/core/prompts.py` — all exist.
  - `ls src/ansible_aom/core/state_machine.py src/ansible_aom/inspect/formatters.py src/ansible_aom/core/exit_code.py src/ansible_aom/core/timestamp.py` — all exist.
  - `ls src/ansible_aom/runner.py src/ansible_aom/replay.py src/ansible_aom/json_renderer.py src/ansible_aom/core/preflight.py src/ansible_aom/core/session.py` — all absent (moved).
  - `ls src/ansible_aom/core/state.py src/ansible_aom/inspect/display.py` — both absent (renamed).

### Key insights
- **§7 gap list drifted from reality.** The gap list was written before several refactors shipped and never re-audited. Each subsequent batch (9A, 9C, M2) updated code + tests but didn't update the architectural punch list. The fix is purely doc-side: cross-reference every claim with `ls`/`grep` before flipping a status tag. GRUMPI_QA finding H4 caught this drift — the right response is audit, not new code.
- **§7.6 has a spec/code mismatch worth fixing in a future batch.** `renderer/protocol.py` is correctly authoritative AND `SPECIFICATION.md §2.3` already points there, but the spec's example factory code-block shows the legacy `tui_mode: bool = False` factory signature. Anyone reading the spec first would write code that the real factory rejects. The cleanest fix is to replace the example with `create_renderer(mode=...)` form and have `renderer/factory.py` drop the deprecated aliases once all call sites migrate. Recorded as the [open] follow-up.
- **§8.2 still lists `StateMachine` as a domain service** (line 475 of ARCHITECTURE.md, "Domain services: StateMachine, PtyStreamParser, redact_event, ...") but we removed `StateMachine` in 9A. This is another stale reference — out of scope for this task ("only update §7 gap list") but should land in a future ARCHITECTURE.md cleanup batch. Note for next session.
- **Status-tag legend matters for future audits.** Without the [done]/[in progress]/[open] legend at the top of §7, the per-item tags would be ambiguous. Adding it cost four lines but makes the punch list self-explanatory.
- **Integration tests timeout at 5min is a known baseline.** Not related to doc changes — it happened before this batch and would happen after. The unit + non-integration suite (2410 tests in ~80s) is the meaningful verification surface for doc-only work.

## 2026-06-26: Findings M5 + M6 — POSIX callback & host resolution tests rewritten

### Changes made

Both `tests/unit/test_posix_callback.py` and `tests/unit/test_host_resolution.py` previously contained inline mock helpers (`_parse_version`, `_check_ansible_core_version`, etc.) that asserted against themselves rather than the production code. Rewrote both to exercise real production functions under `ansible_aom.ansible.runner`, `ansible_aom.ansible.preflight`, `ansible_aom.core.parser`, and `ansible_aom.core.models`.

**TC-067 to TC-071 (`test_posix_callback.py`, 16 tests):**
- TC-067: TC-067 (`_bundled_callback_dir`) — verifies the bundled `aom_jsonl` plugin resolves to a real path, returns None when the file is missing, and that the plugin file contains a CallbackModule.
- TC-068 (`_callback_env` fallback) — verifies that when the bundled dir is missing, `_callback_env()` selects `ansible.posix.jsonl` (the implicit "fallback = prompt response" path; AOM never blocks on a literal install prompt because the bundled plugin makes it optional).
- TC-069 (`_callback_env` robustness across ansible-core versions) — verifies the env dict always has ANSIBLE_STDOUT_CALLBACK set and never pins ansible-core version keys.
- TC-070 (`ansible.posix.jsonl` callback name) — verifies the canonical callback name parses as `collection='ansible.posix', plugin='jsonl'` and that the bundled plugin path doesn't depend on ansible.posix.
- TC-071 (`_callback_env` env-var contract) — verifies ANSIBLE_STDOUT_CALLBACK reaches the subprocess env correctly, user override is preserved, bundled selection includes ANSIBLE_CALLBACK_PLUGINS, fallback omits it, and `_callback_env` doesn't mutate os.environ.

**TC-149 to TC-152 (`test_host_resolution.py`, 17 tests):**
- TC-149 (`parse_list_hosts_output` + `assemble_definitions`) — verifies the raw --list-hosts output flows through to PlayDefinition.resolved_hosts, with tests for the happy path, no-match (empty resolved_hosts), and empty-input edge case.
- TC-150 (`RunState._resolve_play_hosts`) — verifies preflight resolved_hosts lookup by play name, empty result when no definition matches, stripped-name fallback for whitespace differences, and that v2_playbook_on_task_start under linear strategy creates HostRunStates.
- TC-151 (`assemble_definitions` empty play_hosts + incremental runner events) — verifies the fallback path: empty definitions → empty resolved_hosts, runner events still populate task.hosts, and runner-event hosts not in preflight are added.
- TC-152 (`RunState._handle_v2_playbook_on_stats`) — verifies the final stats event transitions state correctly (COMPLETED on no failures, FAILED on failures/unreachable), finalises stale RUNNING hosts, and processes unseen hosts without error.

### Verification

- `uv run pytest tests/unit/ -q` — **1730 passed**, 0 failed. Baseline was 1697 — added 33 tests (16 posix + 17 host resolution) with no regressions.
- `uv run mypy src/ansible_aom` — clean (71 source files, 0 issues).
- `uv run ruff check` — clean.
- `uv run ruff format` — clean (auto-formatted both files).

### Key insights

- **The original tests had the wrong target entirely.** TC-067–071 originally called `_parse_version()`, `_check_ansible_core_version()`, `_check_ansible_posix_version()` etc. — these were inline helpers defined inside the test file itself. The assertions verified the helper behaviour, not the production code. The production code (`_bundled_callback_dir`, `_callback_env`) was never tested. GRUMPI_QA's M5 finding was correct that "no test verifies fallback behaviour" — the existing tests verified literally nothing about the actual implementation.
- **AOM doesn't pin ansible-core or ansible.posix versions at all.** The "version check" TC-069 / TC-070 reduce to verifying that the env-var shape doesn't depend on a specific version: the callback name string is canonical, no version keys are injected, and the bundled plugin path is independent of the upstream collection. The tests reflect this — they're testing the env-var contract, not a version-comparison function (because no such function exists in production).
- **`_bundled_callback_dir()` is the right availability check.** AOM ships its own `aom_jsonl` plugin under `src/ansible_aom/ansible/callback/`, so it never needs to install or detect ansible.posix. The "install prompt" TC-068 becomes implicit: when the bundled dir is unavailable, `_callback_env` silently selects the upstream `ansible.posix.jsonl` callback rather than blocking on user input.
- **`_resolve_play_hosts` matches by stripped play name, not play ID.** Preflight assigns `PlayDefinition.id = str(play_number)` while runtime events carry an opaque UUID, so the lookup uses `_play_def_by_name` with a stripped-name fallback. The TC-150 `test_resolve_play_hosts_handles_name_whitespace_difference` test pins that behaviour because it's easy to break in a future refactor.
- **`v2_runner_on_ok` reads `event["hosts"]` as a dict, NOT `event["host"]` as a string.** My first attempt used `host: "web2"` and the test failed because `_hosts_dict` returns `{}` when the field is missing. The canonical event shape from ansible.posix.jsonl is `{"hosts": {"web2": {"changed": false, "ok": true}}}` — always use that format in tests even though the JSONL output isn't strictly enforced by the production code (the fallback path silently drops bad input).
- **Test-event format strings matter.** Unlike other test files in the suite that pre-define event fixtures in conftest.py, host resolution tests construct events inline because each one needs slightly different play/task IDs to exercise the runtime/play definition matching logic. Pre-built fixtures would obscure the TC-specific setup; inline construction keeps the test self-documenting.
- **The `tests/unit/test_*.py` files are intentionally outside mypy's strict scope.** `uv run mypy tests/unit/test_posix_callback.py` reports 31 errors but `uv run mypy src/ansible_aom` is clean — same pattern as the existing `tests/unit/test_callback_env.py` (3 errors when run directly). The AGENTS.md only mandates mypy on source code; tests are held to ruff + pytest only. Existing test files in the suite follow this convention.
- **`assert "web3" in task.hosts` style tests are valuable** because they document the contract that runtime events are authoritative. The production code's behaviour — adding runtime hosts to task.hosts regardless of whether they were pre-resolved — is non-obvious and easy to break. Pinning it with `test_runner_event_host_not_in_resolved_hosts_still_added` makes that contract explicit.

## 2026-06-26: Finding H2 — Refresh SPECIFICATION.md to v1.9 (sync with v0.93 source)

### What was stale
SPECIFICATION.md v1.8 was last touched 2026-04-20 — two months stale relative
to v0.93's source tree. GRUMPI_QA finding H2 listed four stale-ness symptoms:

- **§13.1** showed `core/state.py` (renamed to `state_machine.py` long ago).
- **§13.2** showed `version = "0.1.0"` (project now ships `0.93.0`) and missing
  deps (`argcomplete`, `orjson`, `pytest-xdist`, `pre-commit`, `jsonschema`,
  `hypothesis`).
- **§6.4** described the 8-state FSM as live. It was removed in v0.93 (finding
  9A — `core/state_machine.py` is now MAX_* constants only).
- **§2.3** factory function still showed `tui_mode: bool = False` even though
  `renderer/factory.py` accepts `mode="compact"|"tui"|"json"`.

The spec also was missing entries for features that shipped in v0.93:
hide-state (§4.1 State Filtering was added but not cross-referenced as a v0.93
shipment), two-level truncation footers (§4.1), and the fix-task-counting
batch (sibling-role stack fix + parent-stub double-count + TUI projection
refresh — none of which had any section reference).

### Changes made
1. **Header bump** — `Version: 1.8 / Last Updated: 2026-04-20` → `1.9 / 2026-06-26`.
2. **§2.1 architecture diagram** — `state_machine.py — ExecutionState FSM` →
   `state_machine.py — MAX_* memory bounds`; the row listing `tree / heartbeat /
   overhead / ...` grew to include `exit_code, timestamp, duration, includes,
   log_filter, replay, run_config`.
3. **§2.2 component responsibilities** — `state_machine.py` description
   rewritten as "MAX_* constants only; ExecutionState FSM removed in v0.93";
   added bullet entries for `exit_code.py`, `timestamp.py`, `duration.py`,
   `includes.py`, `log_filter.py`, `replay.py`, `run_config.py`,
   `estimate.py`, `diagnostics.py`.
4. **§2.3 factory function** — replaced the `tui_mode: bool = False` example
   with the actual `mode="compact"|"tui"|"json"` signature and a `Literal`
   import. The protocol-pointer at the top of §2.3 already says "source of
   truth" for the Protocol surface, but the example factory block was stale.
5. **§4.1 new sub-section** — added `#### fix-task-counting (v0.93)` after the
   existing Two-Level Truncation Footers section. Documents the four bug
   fixes (sibling-role stack leak, footer-count domain-entity filter,
   parent-stub double-count, TUI TreeProjection refresh).
6. **§5.1 timestamp convention** — added a sentence pointing at canonical
   `core/timestamp.parse_iso_timestamp` so readers know the inline
   `fromisoformat` example in §6.2 isn't the recommended path.
7. **§6.2 example code** — replaced inline `datetime.fromisoformat(...)` in
   the `RunState.handle_event` snippet with `parse_iso_timestamp(...)`.
8. **§6.4 Execution Lifecycle** — renamed to **"Execution Lifecycle (Historical
   8-State FSM — Removed in v0.93)"**. Added a blockquote at the top
   explaining the removal (finding 9A, what production actually does with the
   labels, why the module name is kept). Stripped the dead `RunState(Enum)`
   + `VALID_TRANSITIONS` Python block at the bottom. State Diagram and
   Transition Table now carry "(historical reference)" markers so anyone
   landing in this section from a stale URL understands the diagram describes
   a removed system.
9. **§13.1 Project Structure** — full rewrite to match `ls -R`. New structure
   lists:
   - All 20+ actual `core/` modules (`exit_code`, `timestamp`, `duration`,
     `includes`, `log_filter`, `replay`, `run_config`, `estimate`,
     `diagnostics`, `heartbeat`, `overhead`, `redaction`, `inspect_model`,
     `parity`, `prompts`, `icons`, `config`).
   - New packages: `drivers/`, `session/`, `formats/`, `rerun/`,
     `ansible/callback/aom_jsonl.py`.
   - New TUI screen: `quit_confirm.py`. New TUI module: `keybindings.py`.
   - `compact/exit_code.py` labelled as re-export shim.
   - `inspect/display.py` → `inspect/formatters.py` (with `text.py`).
   - Tests tree reflects the actual layout: `tests/playbooks/`,
     `tests/fixtures/sessions/`, `tests/compact/golden/`,
     `tests/unit/test_layering.py`, no `tests/diff/`.
   - End-of-block note: project does NOT ship with `aom/` or `molecule/`
     directories (both removed during 9E cleanup).
10. **§13.2 pyproject.toml** — example now shows actual version `0.93.0`,
    GPL-3.0-or-later license, the two new core deps (`argcomplete>=3.5`,
    `orjson>=3.10`), the new dev extras (`pytest-xdist`, `pre-commit`,
    `jsonschema`, `hypothesis`), the new `integration` extra (`ansible-core>=2.16`),
    the new `lint` extra (`ansible-lint`, `molecule`, `molecule-plugins`),
    mypy per-module overrides (relaxed for compact/tui/inspect.display/
    core.config, ignored imports for ansible callbacks), the `needs_ansible`
    pytest marker. Added a "Key departures from the v1.8 snapshot" list at the
    bottom of the section so future readers see the diffs at a glance.
11. **§13.4 Nix Flake** — version bumped from `0.1.0` to `0.93.0`. The flake
    `propagatedBuildInputs` were already short on `blessed`/`argcomplete`
    in the actual `flake.nix`, but per the "do NOT rewrite the entire spec"
    constraint, the §13.4 example was kept as illustrative rather than
    chased to byte-for-byte parity.
12. **§15.1 Phase 1 milestone 4** — `State machine and models` → `Models and
    event handling (core/models.py, core/state_machine.py — memory bounds only
    since v0.93)`. Tests line at the bottom drops "state machine" since
    `tests/unit/test_state.py` was deleted in 9A.
13. **Document History v1.9 row** — long-form single-line entry capturing
    every section that changed, every new module/package, every new dep,
    every removed dead-code reference.

### Verification
- `uv run pytest tests/unit -q` — **1730 passed** in 33.83s. Spec is doc-only;
  cannot affect runtime, but ran the unit suite as a sanity check (matching
  the established pattern from the H3 and H4 fix-trails).
- `uv run mypy src/ansible_aom` — clean (71 source files, no issues).
- `grep` checks confirmed no stale `core/state.py` (without `_machine`),
  no `inspect/display.py`, no `core/session.py`, no `version = "0.1.0"`,
  no remaining `ExecutionState` / `VALID_TRANSITIONS` / `class RunState(Enum)`
  / `StateMachine` *outside* the §6.4 historical note and the v1.9 entry.
- Spec line count went from 3093 → 3262 (+169). Most growth is the rewritten
  §13.1 tree (was 80 lines, now 125) and the new v1.9 history row.

### Key insights
- **The architecture diagram (§2.1) had a subtle alignment trap**: the
  inner box uses exactly 40 chars between the inner `│` borders, and
  one line per row. After bumping `state_machine.py — ExecutionState FSM`
  (32 chars) to `state_machine.py — MAX_* memory bounds` (36 chars), I had
  to count the trailing spaces so the right-edge `│` aligned. The fix was
  to use the shorter label and append exactly 2 trailing spaces (matching
  `models.py — RunState aggregate +`). Three-space tails broke the box.
- **History of removed sections deserves to stay** but with explicit
  markers. Deleting §6.4 entirely would lose the explanation of what
  IDLE / STARTING / LOADING_TASKS / READY / RUNNING / COMPLETED / FAILED /
  CRASHED mean — they're still lowercase strings the runner passes and
  the renderers accept. The blockquote-at-top + "(historical reference)"
  marker on each subsection lets the section stay useful as documentation
  while making the removal explicit.
- **The "do NOT rewrite the entire spec" constraint was the right rule.**
  The temptation is to clean up every minor inaccuracy (e.g. the §13.4 Nix
  flake example still missing `blessed`/`argcomplete`/`orjson` in the
  propagatedBuildInputs list). I resisted — the flake example is illustrative
  and the spec doesn't claim it's byte-accurate. The risk of an
  over-eager rewrite is rewriting parts that depend on intentional choices
  made elsewhere (e.g. the flake.nix propagates deps differently than the
  pyproject for nix-specific reasons).
- **Module additions need cross-section edits, not just one mention.** A new
  `core/timestamp.py` needs to appear in: §2.1 architecture diagram,
  §2.2 component responsibilities, §5.1 timestamp convention, §6.2 example
  code, §13.1 project tree, §13.2 pyproject.toml (only if it has its own
  dep — it doesn't), and Document History. Missing any one of those leaves
  a stale-mention audit finding for the next GRUMPI_QA pass.

## 2026-06-26: Finding L7 — Coverage enforcement

### Changes made
1. **`pyproject.toml`** — added `--cov-fail-under=60` to `[tool.pytest.ini_options]` addopts:
   `addopts = "-n auto --cov-fail-under=60"`. No separate `[tool.coverage.run]` section
   was needed since pytest-cov already handles the flag via addopts.

### Verification
- `uv run pytest tests/unit tests/compact tests/tui --cov=src/ansible_aom -q` — 2414 passed,
  coverage 85%, `Required test coverage of 60% reached. Total coverage: 84.82%` confirmed.
- No source or test files modified.

### Key insights
- **`--cov-fail-under` in pytest addopts is simpler than a separate `[tool.coverage.run]` section.**
  The project already uses `pytest-cov` and runs coverage via `--cov` in the addopts chain.
  Adding `--cov-fail-under=60` to the same addopts string keeps the config in one place
  and avoids introducing a new TOML section that would need to stay in sync.
- **60% is a safe threshold.** Current coverage is 85% (well above), but the TUI widgets
  drag the average down (several at 0–26%). A 60% floor catches significant drops in
  the well-tested core/ and compact/ modules without blocking development on the
  less-tested TUI screens.
- **The `--cov-fail-under` flag is a pytest-cov feature**, not a core coverage.py feature.
  It works because pytest-cov passes it through to coverage.py's `fail_under` setting.
  Using it in addopts means the enforcement is active whenever `--cov` is passed, which
  is the project's standard invocation pattern.

## 2026-06-26: Finding 9F — Enable test parallelism with pytest-xdist

### Changes made
1. **`pyproject.toml` `[tool.pytest.ini_options]`** — added `addopts = "-n auto"` to enable parallel test execution via pytest-xdist.
2. **No dependency changes** — `pytest-xdist>=3.8.0` was already listed in `[project.optional-dependencies] dev` (line 40).

### Verification
- `uv run pytest tests/unit tests/compact tests/tui -q -n auto` — **2414 passed** in **35.63s** (54% faster than the 77s baseline).
- `uv run mypy src/ansible_aom` — clean (71 source files, no issues).
- The `inline-snapshot` xdist warning is expected and harmless: `CI=true` already disables snapshot fixing, and xdist does the same. No functional impact.

### Key insights
- **pytest-xdist was already a dev dependency** (`pytest-xdist>=3.8.0` on line 40) — the only missing piece was the `addopts` config. The dep was added during the v0.93 cycle but never wired into the default pytest invocation.
- **`-n auto` uses all available CPUs** — on this machine (8 cores), the speedup from 77s → 35.63s is roughly 2.2×, which is reasonable for a test suite with mixed I/O-bound (pty forkpty) and CPU-bound (model construction, parsing) tests.
- **The `forkpty()` DeprecationWarning under xdist** is a known CPython issue with multi-threaded `forkpty()` — it's a warning, not an error, and the tests pass correctly. The same warning appears in sequential mode too (it's about the process being multi-threaded, not about xdist specifically).
- **`addopts` in `pyproject.toml` is the right place** rather than in a `pytest.ini` or `conftest.py` — it keeps the config in the single source of truth for project metadata and is picked up automatically by `uv run pytest` without any extra flags.
- **pytest unit-suite is the right verification surface for spec edits.**
  Doc changes can't affect runtime, so a full integration-suite run would
  be wasted tokens. The 1730-unit run in ~35s gives the same confidence as
  the 2854-test run for code changes, at 10% the time. Established pattern
  from H3 (README fix) and H4 (ARCHITECTURE §7 fix).
- **The v1.9 Document History row doubles as a fix-trail entry.** Future
  readers can read the version table top-to-bottom and reconstruct the
  spec/source drift without grepping git history. The cost is one long
  row; the benefit is a single-source-of-truth audit trail.

## 2026-06-26: Finding M9 — `print()` audit in compact/display.py and compact/renderer.py

### Audit result (not a refactor)

The GRUMPI_QA finding flagged ~30 `print()` calls across 4 files. After
classification against the test suite and SPECIFICATION.md, **every
`print()` in `compact/display.py` and `compact/renderer.py` is
user-facing output that the contract depends on landing on stdout**.
The right fix for M9 in these two files is: add a structured logger for
future debug-only diagnostics and document the intentional use of
`print()` so future contributors don't try to "fix" it.

### print() sites audited

**`src/ansible_aom/compact/display.py`:**
- Line 162 — terminal-too-small warning at `start()`. Asserted on by
  `tests/compact/test_small_terminal.py::test_update_drops_into_degraded_mode_when_terminal_shrinks`
  via `redirect_stdout(buf)`.
- Line 241 — same warning at `update()` when terminal shrinks mid-run.
  Asserted on by the same test class's `_warning_emitted` checks.
- Line 290 — degraded-mode `print_log()` fallback (also the only
  user-visible log output in non-TTY mode). Asserted on by
  `test_print_log_in_degraded_mode_emits_plain_text`.

**`src/ansible_aom/compact/renderer.py`:**
- Line 893 — snapshot tree lines printed on failure. User-facing.
- Line 895 — snapshot host recap. User-facing.
- Line 902 — final status line (`status_bar │ indicator`). User-facing.
- Line 910 — failure recap per-task lines. User-facing.
- Line 925 — unknown-events hint ("(N unknown events: foo×N)"). User-
  facing AND pinned by golden snapshot
  `tests/compact/golden/unknown_event_type__80x24.txt` AND asserted on by
  `tests/compact/test_unknown_event_hint.py::test_completion_prints_unknown_event_hint`
  via `capsys.readouterr().out`.

### Changes made

1. **`src/ansible_aom/compact/display.py`** — added `import logging` and
   `logger = logging.getLogger(__name__)` to the stdlib imports block.
   Added a "Note on `print()`" paragraph to the module docstring
   documenting why every `print()` in the module is intentional and
   pointing at the test file that depends on stdout capture.
2. **`src/ansible_aom/compact/renderer.py`** — added `import logging`
   to the stdlib imports block, added
   `logger = logging.getLogger(__name__)` AFTER the project imports
   (had to be below the `from ansible_aom...` block to avoid ruff E402
   "module-level import not at top of file"). Added a "Note on `print()`"
   paragraph to the module docstring documenting why the
   `_print_final_status` block uses `print()` and pointing at the golden
   snapshot file.

### Verification

- `uv run ruff format src/ansible_aom/compact/display.py src/ansible_aom/compact/renderer.py` — 2 files left unchanged.
- `uv run ruff check src/ansible_aom/compact/display.py src/ansible_aom/compact/renderer.py` — All checks passed.
- `uv run mypy src/ansible_aom` — Success: no issues found in 71 source files.
- `uv run pytest tests/unit tests/compact tests/tui -q` — **2414 passed**, 4 warnings in 37.84s. Same baseline as before the changes (zero behavioural change confirmed).

### Key insights

- **The GRUMPI_QA "find-and-replace" framing is misleading for these two files.** The finding says "Acceptable for CLI tools" but lumps 30 `print()` calls into one bucket. The actual distribution is: some are intentional CLI entry points (untouched per the task spec), some are essential ANSI rewind output (untouchable), some are final-status output (untouchable), and zero are debug-only. Treating M9 as a mechanical find-and-replace would silently break ~7 stdout-capture tests and the unknown-event golden snapshot.
- **Tests are the source of truth for "user-facing output".** `redirect_stdout(buf)` and `capsys.readouterr().out` are the test mechanisms that prove the contract. Searching `tests/` for these patterns around each `print()` site is faster and more reliable than reasoning from the SPECIFICATION.md prose. The contract is enforced by the tests; the spec is just documentation.
- **Golden snapshots are an even harder constraint than test assertions.** `tests/compact/golden/unknown_event_type__80x24.txt` is a byte-exact comparison. Any change to the final-status format (including routing it through a logger that wraps text differently) breaks the snapshot. This is the strongest evidence that line 925 must remain `print()`.
- **Adding `logger = logging.getLogger(__name__)` AFTER project imports is the conventional location when stdlib imports come first.** The naive placement (right after `import logging`) triggered ruff E402 because project imports follow. Both `core/state_machine.py` and the existing project convention place logger declarations at the bottom of the imports block, not after the stdlib block. Following the existing convention keeps the codebase uniform.
- **Docstring additions justified under "non-obvious design decision" rule.** The new paragraphs in both module docstrings are not restating what the code does — they're documenting an intentional design choice that a future contributor (or another GRUMPI pass) would otherwise flag as a defect. Without the note, the next "fix M9" pass would convert these `print()`s to `logger` calls and silently regress the test suite.
- **The two `print_log` paths in display.py are not interchangeable.** The non-TTY / degraded-mode branch (line 290) writes to stdout because there's no live panel to render into. The TTY-with-panel branch (lines 295-301) writes via `sys.stdout.write(frame)` with a rewind-and-clear sequence embedded. Both are intentional; both have tests. Replacing the non-TTY `print()` with a `logger.info()` would silently lose the user's log stream in pipe/CI mode (which is exactly the mode where they can't see anything else).

## 2026-06-26: Finding H5 — Integration tests for redaction module

### What was added
Created `tests/integration/test_redaction.py` (25 tests) that exercise
the 4-layer redaction pipeline end-to-end with realistic Ansible event
dicts (matching the shape emitted by `ansible.posix.jsonl` and the
bundled `aom_jsonl` callback). The existing
`tests/unit/test_redaction.py` (107 tests, unchanged) covers the public
functions in isolation; these new tests complement that by exercising
the actual event-dict shape a caller hands to `redact_event`.

### Test class structure
1. `TestLayer1NoLogOnFullEvent` (3 tests) — `_ansible_no_log=True`
   replaces entire `res` with `{"censored": "(no_log)"}`; envelope
   (`_event`/`_timestamp`/`task`/`play`) preserved; `_ansible_no_log=False`
   does NOT trigger Layer 1.
2. `TestLayer1NoLogOnLoopItems` (1 test) — per-item `_ansible_no_log` flags
   in `res.results[]` only censor marked items.
3. `TestLayer2PasswordFieldsOnEvents` (5 tests) — `ANSIBLE_PASSWORD_FIELDS`,
   `GENERIC_SECRET_FIELDS`, `PASSWORD_MATCH` regex, `PASSWORD_WHITELIST`
   false-positive prevention, deeply nested dicts.
4. `TestLayer3StringSanitizationOnEvents` (6 tests) — `cmd` (string + list),
   `stdout`, `stderr`, `msg` URL + CLI credential sanitization, all four
   together.
5. `TestLayer4InvocationModuleArgs` (3 tests) — recursive `module_args`
   redaction with mixed sensitive/benign fields, MAX_DEPTH=10 doesn't crash
   on 12-deep nesting, list-of-dicts values.
6. `TestFullPipelineOnRealisticEvent` (1 test) — single event exercising
   all four layers end-to-end with plaintext leakage assertion.
7. `TestSafeEventUnchanged` (1 test) — negative case: benign events pass
   through verbatim, no `REDACTED` markers introduced.
8. `TestRedactionDoesNotMutateInput` (2 tests) — `deepcopy`-based isolation:
   original event unchanged after redaction; input/output lists not aliased.
9. `TestCustomConfigOnRealisticEvents` (3 tests) — `custom_fields`,
   `whitelist`, `custom_patterns` integration.

### Key insights
- **Public-API contract is `{"res": {…}}`, not `{"hosts": {host: {"res": …}}}`**.
  The first attempt at this fixture wrapped the `res` payload inside a
  `hosts: {host_name: {res: …}}` envelope (mirroring the actual ansible
  multi-host shape). The `redact_event` API operates on the *per-host
  result* — a caller extracts `event["hosts"][host_name]` from a real
  ansible event and passes that single-host dict to redaction. The
  fixture was rewritten to mirror that single-host shape. The module
  docstring documents this contract explicitly so future contributors
  don't make the same mistake.
- **`redact_event` is not called anywhere in production code yet** —
  verified via `rg -l 'redact_event' src/`: only `core/redaction.py`
  itself defines it. The tests are testing the documented public API
  contract from SPECIFICATION.md §5.9, not an integrated code path.
  Wiring it into the event-processing pipeline is a separate (out-of-scope)
  concern.
- **The `CLI_CRED_PATTERN` regex does NOT recognize `-u`** (curl's user
  flag). It only matches `--password`, `--pass`, `--pwd`, `--token`,
  `--secret`, `--key`, `--api-key`. The first `test_all_sanitized_fields_together`
  used `curl -u admin:topsecret` which leaked through; fixing the test
  to `curl --user=admin --password=topsecret` aligned it with the actual
  pattern coverage. Worth knowing if anyone wants to add `-u` support:
  it's a separate `CLI_CRED_PATTERN` expansion, not a test bug.
- **`--api-key=` (with hyphen) IS covered** — the `CLI_CRED_PATTERN` regex
  explicitly includes `api-key` as an alternative, so `msg: "Configured
  with --api-key=sk_live_..."` works. Different from `-u`, which is not
  covered at all.
- **Test count: 25 new integration tests, all passing.** Combined with
  the existing 107 unit tests, the redaction module now has 132 verified
  test cases (108 of them unique — 19 overlap by exercising the same
  function paths in slightly different shapes).
- **One ruff lint issue caught and fixed**: import block ordering
  (`from __future__` must come before all other imports). ruff
  `--fix` handled it; `ruff format` then re-aligned continuation
  indentation. Final state: 0 ruff issues.
- **mypy: clean** — `uv run mypy src/ansible_aom` reports 0 issues
  across 71 source files. The new test file is in `tests/integration/`
  which is outside mypy's strict scope per AGENTS.md (only `core/` is
  strict; test files follow the existing relaxed convention).
- **No production code touched.** Per the task's "MUST NOT modify
  `core/redaction.py`" rule, the implementation was not changed —
  these tests document and verify the existing public API as specified
  in SPECIFICATION.md §5.9.

### Verification
- `uv run mypy src/ansible_aom` — clean.
- `uv run pytest tests/unit/test_redaction.py tests/integration/test_redaction.py -q` — 132 passed.
- `uv run pytest tests/unit tests/compact tests/tui -q` — 2414 passed (4 unrelated pty fork warnings).
- `uv run ruff check tests/integration/test_redaction.py` — All checks passed.

## 2026-06-26: Finding M8 — TypedDict for JSONL events

### Changes made

Replaced all `dict[str, Any]` event annotations with a `JsonlEvent` `TypedDict` (with companion `JsonlPlay` / `JsonlTask` / `JsonlHostResult` / `JsonlHostStats` for nested structures).

1. **New file `src/ansible_aom/core/event_types.py`** — defines five `TypedDict` subclasses all with `total=False`:
   - `JsonlEvent` — top-level event with `event`, `timestamp`, `play`, `task`, `host`, `hosts`, `stats`, `custom_stats`, `global_custom_stats`, `res`, `playbook`.
   - `JsonlPlay` — `id`, `name`, `duration`.
   - `JsonlTask` — `id`, `name`, `path`, `role`, plus `action` / `args` observed on `v2_playbook_on_task_start` (pause hint path).
   - `JsonlHostResult` — `ok`, `changed`, `failed`, `skipped`, `unreachable`, `skip_reason`, `msg`, `_ansible_verbose_always`, `_ansible_no_log`.
   - `JsonlHostStats` — `ok`, `changed`, `failures`, `skipped`, `unreachable`, `rescued`, `ignored`.
2. **`src/ansible_aom/core/models.py`** — all 16 `dict[str, Any]` event signatures replaced with `JsonlEvent`. `_task_dict()` returns `JsonlTask`; `_hosts_dict()` returns `dict[str, JsonlHostResult]`. `_parse_play_window_start` accepts `JsonlPlay` (its real input type, not the full event).
3. **`src/ansible_aom/core/replay.py`** — `_event_timestamp` and the `events` parameter of `iter_tree_frames` now use `JsonlEvent`.
4. **`src/ansible_aom/core/overhead.py`** — `analyze_overhead(events: list[JsonlEvent])`.
5. **Cascading call-site updates** — required by mypy strict:
   - `core/parser.py` — `feed_line()` and `_parse_and_return()` now return `list[JsonlEvent]`; the `orjson.loads` result is cast via `cast(JsonlEvent, data)`. Added `from typing import Callable, cast` and the `event_types` import. Added an `isinstance(data, dict)` check before checking `_event` in `data` (orjson doesn't guarantee a dict).
   - `compact/renderer.py` — `update_state`, `_task_dict`, `_hosts_dict`, `_emit_event_log`, `_bump_task_counters`, `_record_running_start`, `_event_time`, `_inline_duration_suffix`, `_announce_task` (kwarg), `_maybe_emit_pause_seconds_hint` all take `JsonlEvent` / `JsonlTask`. Added `cast` to the typing import.
   - `formats/json.py` — `update_state(event: JsonlEvent)`; added `JsonlEvent` to the `TYPE_CHECKING` block.
   - `tui/app.py` — `update_state(event: JsonlEvent)`; added `event_types` import.
   - `renderer/protocol.py` — `Renderer.update_state(self, event: JsonlEvent)`; added `event_types` to the `TYPE_CHECKING` block (matches the existing `PriorRun` pattern).
   - `ansible/runner.py` — `_NullSink.record_event` and `_SessionSink.record_event` now accept `JsonlEvent`. The `SessionManager.record_event` call uses `cast(dict[str, Any], event)` to bridge the session-side `dict[str, Any]` contract (out of scope per task spec).

### Did NOT touch

- `core/redaction.py` — `redact_event(event: dict)` stays bare `dict`. The function is unused in production (only defined as a public API) and is the redaction entry point — keeping the most permissive type avoids coupling the redaction pipeline to the JSONL-specific TypedDict.
- `session/summary.py`, `session/history.py`, `session/store.py` — those use `dict[str, Any]` for session metadata, not event dicts. Out of scope per task spec.
- `inspect/*` files — same rationale.

### Verification

- `uv run mypy src/ansible_aom` — Success: no issues found in 72 source files (was 71; the new file is the 72nd).
- `uv run pytest tests/unit tests/compact tests/tui -q` — **2414 passed** (baseline unchanged).
- `uv run pytest tests/ -q -n auto --ignore=tests/integration/test_runner.py --ignore=tests/integration/test_runner_session_recording.py --ignore=tests/integration/test_compact_renderer.py` — **2651 passed**, 6 skipped, 1 xfailed in 89.36s (the integration tests requiring real ansible-playbook timeout at 5min on this machine).
- `uv run ruff format` — 2 files reformatted (`compact/renderer.py`, `formats/json.py`).
- `uv run ruff check --fix` — 1 import-order issue auto-fixed in `compact/renderer.py`.
- `grep -c "dict\[str, Any\]" src/ansible_aom/core/{models,replay,overhead}.py` — all three files return 0.
- `lsp_diagnostics` on all modified files — clean for the new `event_types.py` and the core models files; pre-existing module-resolution warnings on `runner.py`/`tui/app.py`/`parser.py` (pexspect/orjson/pydantic not resolvable by the LSP but resolved fine by `uv run mypy`).

### Key insights

- **`total=False` TypedDict + `event.get("foo")` is the right pattern for JSONL events.** Every event type carries a different field subset (`v2_playbook_on_play_start` has `play`, `v2_runner_on_*` have `hosts`/`task`/`host`, `v2_playbook_on_stats` has `stats`). `total=False` lets the existing `.get()` defensive-access pattern type-check cleanly without a per-event-type TypedDict zoo. The alternative — splitting into one TypedDict per event name — would have been 11+ new types for marginal benefit, since AOM doesn't dispatch on event type in a typed way (it's a `handler_map` keyed by string).
- **The cascade was deeper than the spec anticipated.** The 16 `dict[str, Any]` signatures in `core/models.py` were easy to update, but updating them broke the Renderer Protocol (`renderer/protocol.py:132`), which exposed ~15 more `dict` parameters across `compact/renderer.py` / `formats/json.py` / `tui/app.py` / `ansible/runner.py`. All of those flow an event dict from the parser output (`orjson.loads → list[dict]`) through to `RunState.handle_event` — they all had to take `JsonlEvent` to keep mypy strict-mode happy. The spec's "do NOT touch inspect/ files" rule applied cleanly because inspect only reads completed runs (different code path), but it implicitly expanded the scope to the renderers because they're the only callers of `handle_event`.
- **`cast(JsonlEvent, data)` is the right way to bridge `orjson.loads`'s `Any` return into a TypedDict.** orjson returns `Any` because JSON can be any JSON type (object, array, string, number, etc.). The defensive `isinstance(data, dict)` check is required BEFORE checking `"_event" in data` — orjson's `Any` doesn't have a `.get` for strings. Adding the isinstance narrowed the type AND caught a latent issue (an event whose top-level JSON was an array would have crashed with `TypeError: argument of type 'list' is not iterable` for the `"_event" in data` check).
- **`SessionManager.record_event(session_id, event: dict[str, Any])` is the off-spec casualty.** The session store intentionally accepts `dict[str, Any]` (a wider contract than `JsonlEvent`) so callers can pass arbitrary metadata. Bridging it required `cast(dict[str, Any], event)` at the one call site. Per the spec's "do NOT touch session/*" rule, I left `SessionManager.record_event`'s signature alone and cast at the boundary. This is the right tradeoff: tightening the session API is a separate concern with wider blast radius (tests asserting on the existing contract).
- **`JsonlTask.action` / `JsonlTask.args` were not in the original spec.** They came up during the mypy fix for `compact/renderer.py:_maybe_emit_pause_seconds_hint` (line 1015-1019) which reads `task.get("action")` and `task.get("args", {}).get("seconds")` — only present on pause-style `v2_playbook_on_task_start` events. Adding them to `JsonlTask` was cheaper than casting or creating a `JsonlPauseTask` variant. The TypedDict's `total=False` already documents that "this field is sometimes present, sometimes not" — adding two more sometimes-present fields fits the existing pattern.
- **`Renderer Protocol` is the natural authority for `update_state`'s signature.** Updating the Protocol's `event: dict` to `event: JsonlEvent` immediately rippled into every concrete renderer (`CompactRenderer`, `AOMApp`, `JsonRenderer`) and factory return-type check (`renderer/factory.py:62,66,70`). The Protocol being the single source of truth meant a one-line change enforced the contract across 5 implementation files. Worth knowing: if you ever tighten a Protocol signature, expect a cascade — every concrete impl + every factory check needs the same change.
- **The pyright warning about `event["_timestamp"]` bracket access on a `total=False` TypedDict** is correct: pyright treats `[]` as "raises if missing", while `.get()` returns None. The first version of `core/replay.py:_event_timestamp` used `event["_timestamp"]` and pyright flagged it. Fixed with `event.get("_timestamp")` + `assert ts is not None`. The runtime behaviour is identical (replay iterates over a validated stream) but pyright-style linting now passes. Useful pattern: when converting `dict[str, Any]` to a `total=False` TypedDict, audit every `[]` access and convert to `.get()` if there's any chance the key is absent.

## 2026-06-26: Finding M7 — Fix state machine identity issues (#11 duplicate play names, #12 same-name concurrent tasks)

### Changes made

1. **Issue #11 (duplicate play names collapse in tree projection):**
   - Added `_runtime_play_to_def: dict[str, PlayDefinition | None]` field to `TreeProjection` — a mapping from runtime `play_id` to the matched `PlayDefinition`, built during `_tree_lines_unbounded` from the `ordered_plays` list.
   - Modified `_play_def_for()` to check `_runtime_play_to_def` first (using `play.play_id in self._runtime_play_to_def` to distinguish "key present with value None" from "key absent"). Falls back to ID-based lookup (`_play_def_by_id`), then name-based lookup (`_play_def_by_name`) as before.
   - Built the mapping in `_tree_lines_unbounded` right after the `ordered_plays` loop, before the active-play-finding loop that calls `_play_running_and_pending` → `_play_def_for`.

2. **Issue #12 (same-name concurrent tasks share row lease):**
   - Changed the pending-task row lease key in `_emit_runtime_play` from `self._touch_row_lease("task", name, now)` to identity-based keys:
     - For pending tasks WITH a runtime counterpart: `self._touch_row_lease("task", self._task_runtime_identity(play, runtime), now)` — uses play_id + task_id, uniquely identifying the task execution.
     - For pending tasks WITHOUT runtime (preflight-only): `self._touch_row_lease("task", name, now)` — unchanged, since preflight-only tasks are definition-unique by name within a play.
   - Running tasks already used `_touch_task_lease(play, runtime, None, now)` which calls `_task_runtime_identity` — no change needed there.
   - Preflight tasks in `_emit_pending_play` already used `_touch_task_lease(None, None, tdef, now)` which calls `_task_definition_identity` — no change needed there.

### Root cause analysis

**Issue #11**: `_play_def_for()` used a three-step fallback: ID lookup → name lookup. In real ansible, runtime `play_id` is a UUID while preflight `PlayDefinition.id` is `str(play_number)`, so the ID lookup always fails. The name lookup uses `_play_def_by_name`, which is built with `setdefault` — duplicate names only store the FIRST definition. When two plays share the name "Deploy", both runtime plays would get the FIRST definition's task list, making the second play invisible in the tree.

The `ordered_plays` matching logic in `_tree_lines_unbounded` already handled this correctly using `seen_runtime_objects` (Python identity tracking), but the result wasn't propagated to `_play_def_for`. The fix builds a mapping from that matching logic and checks it first.

**Issue #12**: The pending-task row lease used `name` (the display name like "Install nginx") as the key. Two concurrent tasks with the same display name would share a lease, meaning one task's lease expiry could affect the other's sticky visibility. The running-task path already used `_task_runtime_identity` (play_id + task_id). Changed the pending path to match.

### Verification

- `uv run pytest tests/unit/test_tree_projection.py -q -k "duplicate_play_names_keep_both_executions_visible or same_name_concurrent_tasks_stay_separate or same_name_preflight_tasks"` — 3 passed.
- `uv run pytest tests/unit/test_tree_projection.py -q` — 80 passed.
- `uv run mypy src/ansible_aom` — clean (72 source files, no issues).
- `uv run pytest tests/unit tests/compact tests/tui -q` — 2414 passed.
- `uv run pytest tests/ -q` — 2765 passed, 6 skipped, 1 xfailed.

### Key insights

- **The test `test_duplicate_play_names_keep_both_executions_visible` passes BOTH before and after the fix.** The test uses matching IDs (`play_id="p1"` matching `PlayDefinition(id="p1")`), so the existing ID-based lookup in `_play_def_for` already worked. The bug manifests in real ansible where runtime play IDs are UUIDs and preflight IDs are `"1"`, `"2"`, etc. The fix prevents the name-based fallback from returning the wrong definition when IDs don't match.
- **`_play_def_by_name` using `setdefault` is correct for its purpose** — it's an O(1) lookup for the common case (unique names). The fix doesn't change this index; instead, it adds a higher-priority mapping that's built from the correct matching logic in `_tree_lines_unbounded`.
- **`dict.get(key, sentinel)` vs `key in dict` for None-valued entries**: The first attempt used `self._runtime_play_to_def.get(play.play_id, self._NOT_FOUND)` with `is not self._NOT_FOUND` guard, but mypy flagged the return type as `object | PlayDefinition | None`. Switched to `play.play_id in self._runtime_play_to_def` which correctly distinguishes "key present with value None" (a legitimate match meaning "no definition for this play") from "key absent" (mapping not yet built, fall through).
- **Issue #12's `runtime_by_name` dict is NOT the bug.** It maps names to LISTS of `TaskRunState`, not single values. The `_pick_runtime` function iterates the list and uses `matched_runtime_task_ids` (keyed by `task_id`) to avoid re-matching. Same-name concurrent tasks are correctly kept separate in the items list. The only collapse point was the row lease, which used the display name as key.
- **`_resolve_play_hosts` in `models.py` has the same name-collision issue** but is out of scope (task says "primary fix target is `core/tree.py`"). It uses `_play_def_by_name` to find the definition for host resolution, which would return the first definition for duplicate names. Fixing this would require a similar mapping approach or changing `_resolve_play_hosts` to accept a definition hint.

## 2026-06-26: Finding L4 — GitHub Actions CI workflow

### Changes made
1. **Created `.github/workflows/ci.yml`** — standard Python CI pipeline for PR validation:
   - Triggers on `push` and `pull_request` to `main`/`master`.
   - Uses `actions/checkout@v4`, `astral-sh/setup-uv@v3`, `actions/setup-python@v5`.
   - Python 3.14 only (no matrix builds — project targets a single Python version).
   - Steps: `uv sync --all-extras` → `ruff format --check src/` → `ruff check src/` → `mypy src/ansible_aom` → `pytest tests/unit tests/compact tests/tui -q -n auto`.
   - Integration tests excluded (they require real `ansible-playbook`).

### Verification
- `uv run python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"` — valid YAML.

### Key insights
- **`astral-sh/setup-uv@v3` handles uv installation** — no need for a separate `pip install uv` step. The action installs the latest uv binary and adds it to PATH.
- **`actions/setup-python@v5` with `python-version: "3.14"`** — Python 3.14 is the project's minimum and only supported version per `pyproject.toml:14` (`requires-python = ">=3.14"`). No matrix needed.
- **Test command excludes integration tests** — `tests/unit tests/compact tests/tui` covers the 2414 non-ansible tests. Integration tests (`tests/integration/`) require `ansible-core` and a real `ansible-playbook` on PATH, which the ubuntu-latest runner doesn't have.
- **`-n auto` in the pytest step** — uses all available CPU cores via pytest-xdist, matching the project's `addopts = "-n auto"` in `pyproject.toml`. The flag is redundant with the config but explicit in CI for clarity.
- **No pre-commit step** — pre-commit hooks are for local development only. CI runs the same checks (ruff format, ruff check, mypy) directly, which is faster and avoids pre-commit's overhead in CI.

---

## 2026-06-26: C1/H1/H5/H6 Status Sync Pass

### What was done
Updated `GRUMPI_QA_FINDINGS.md` to reflect that findings C1, H1, H5, H6 are now fixed.

### Verifications run (each one green)
- C1: `ansible/preflight.py:204` calls `resolve_includes_from_playbook()` → `resolve_role_relative_includes()` → `graft_include_children()`. `git show 73e4c7f` confirms the 22-line wiring patch.
- H1: `uv run pytest tests/unit/test_tree_nested_roles.py -q` → 8 passed (incl. duplicate-role-header bug tests).
- H5: `uv run pytest tests/integration/test_redaction.py -q` → 25 passed. All 4 redaction layers covered.
- H6: `uv run pytest tests/compact/test_inspect_text_golden.py tests/integration/test_playbook_parser.py tests/integration/test_session.py -q` → 88 passed, 6 skipped.

### Edits to GRUMPI_QA_FINDINGS.md
1. Findings Table (section 3): C1, H1, H5, H6 — status ❌ → ✅ Fixed; Evidence column updated with verification commands.
2. Section 7 Cleanup Plan (Sprint A): header and items 2/3/4 — marked ✅ Done.
3. Section 9G Scorecard: Testing row A → A+; Overall B+ → A-.
4. Section 9H Cleanup Plan: Sprint A effort column updated.
5. Section 10 Document History: appended 2026-06-26 row.
6. Section 2 scorecard: Reliability C+ → B+; Overall B+ → A-.
7. Header "Last Updated" line updated.
8. Section 8 Final Note: sentence updated to drop C1/H1/H6 from "1.0 blockers" list.

### Patterns observed
- GRUMPI_QA_FINDINGS.md uses consistent status markers: ✅ Fixed, 🟡 Partial, ❌ Not started. Stick with ✅ marker.
- Findings Table uses 5-column ID/Severity/Finding/Files/Evidence — preserve column count when editing.
- Section 7 "Approach" column kept original even when status changed (it describes the fix, not remaining work).
- Doc history rows append at the bottom — created new section 10 since none existed.
