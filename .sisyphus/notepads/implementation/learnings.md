## 2026-06-26 L3: Tightened test file ruff ignores

Replaced the blanket `"tests/**" = ["F401", "F811", "F841", "E501"]` with 36 precise per-file entries. Every rule still has real violations — none could be fully removed. But new test files no longer inherit these suppressions automatically.

- F401: 83 violations across 29 files
- F811: 24 violations across 3 files (test_compact_renderer.py, test_playbook_parser.py, test_config.py)
- F841: 26 violations across 13 files
- E501: 19 violations across 12 files

Also added entries for 3 untracked test files (test_r6_encoding_roundtrip.py, test_help_screen.py, test_runner_eof_watchdog.py) that were never covered by the wildcard.

## 2026-04-24 Exploration Results

### Stub Status
- compact/renderer.py (85 lines): Has basic state storage, missing Rich Live display, status bar, event handling
- compact/display.py (51 lines): Skeleton state management, no rendering
- compact/password.py (27 lines): Pure NotImplementedError stub
- compact/logs.py (23 lines): Pure NotImplementedError stub  
- tui/app.py (34 lines): Pure NotImplementedError stub
- ALL tui/screens/* (14-15 lines each): class body is `pass`
- ALL tui/widgets/* (15 lines each): class body is `pass`

### Key Test Contracts
- CompactRenderer must satisfy Renderer Protocol (start, update_state, handle_password_prompt, handle_completion, stop)
- Display needs: start(), stop(), update(), print_log(), clear()
- format_status_bar() must return: "playbook | X/Y hosts | warn N deprec N | H:MM:SS"
- format_host_summary() must return per-host status with icons
- determine_exit_code() must traverse RunState for exit code
- check_terminal_size() must return (bool, str) tuple
- CompactRenderer._refresh_per_second = 4
- Display must handle Rich Live context manager

### Spec References
- Section 4: Compact mode layout (header + running line + tree + summary)
- Section 5.10: Password pass-through (stop Live, getpass, restart Live)
- Section 7: TUI with screens/widgets (see keybindings.py - already 382 lines implemented)
- Section 12: Signal handling, exit codes, watchdog
## 2026-04-24 AOMApp Implementation

### AOMApp (tui/app.py)
- AOMApp satisfies Renderer Protocol with 5 methods: start, update_state, handle_password_prompt, handle_completion, stop
- Internal state tracking: `_playbook`, `_args`, `_state`, `_exit_code`
- BINDINGS are dynamically built from KEYBINDINGS dict filtering for GLOBAL context only
- CSS_PATH uses relative path `../styles/app.tcss` (Textual resolves from app.py location)
- Actions (action_quit, action_toggle_debug) must be async to match Textual App method signatures
- on_mount pushes MainScreen - deferred import prevents circular imports

### Keybindings Integration
- Keybindings module is fully implemented (379 lines) with get_keybinding(), get_action_keybindings(), get_keybindings_by_context()
- Global keybindings: q (quit), ? (help), f (filter), S (settings), s (sort), d (debug), etc.
- Context-specific keybindings: tree (navigation), log (search), post_run (rerun)

### Test Verification
- Factory test confirms create_renderer(tui_mode=True) returns AOMApp instance
- All Renderer Protocol methods present and callable
- All 1376 tests pass
- ruff check and mypy both pass clean

## Integration Test Playbooks - Summary (2026-04-24)

Created comprehensive integration test plan covering **12 playbooks** that exercise ALL AOM features:

### Key Findings from SPECIFICATION Analysis

1. **10 JSONL Event Types** from `ansible.posix.jsonl`:
   - `v2_playbook_on_start` — Playbook begins
   - `v2_playbook_on_play_start` — Each play begins
   - `v2_runner_on_start` — Task starts (non-lockstep strategies)
   - `v2_playbook_on_task_start` — Task starts (lockstep strategies)
   - `v2_playbook_on_handler_task_start` — Handler task starts
   - `v2_runner_on_ok` — Task succeeds
   - `v2_runner_on_failed` — Task fails
   - `v2_runner_on_skipped` — Task skipped
   - `v2_runner_on_unreachable` — Host unreachable
   - `v2_playbook_on_stats` — Final PLAY RECAP

2. **8-Stage State Machine**:
   `IDLE → STARTING → LOADING_TASKS → READY → RUNNING → COMPLETED/FAILED/CRASHED`

3. **Password Prompt Phases**:
   - `PRE_RUN_PROMPTS` — Before playbook starts (password prompts)
   - `EXECUTION` — JSONL events flowing
   - `POST_RUN_RECAP` — After `v2_playbook_on_stats`

4. **Role Grouping Threshold**: 5+ consecutive same-role tasks → `RoleGroupDefinition`

5. **Dynamic Tasks from `include_tasks`**:
   - NOT expanded in `--list-tasks` output
   - Created at runtime with `is_dynamic=True`, `task_order=-1`

6. **Exit Codes**:
   - 0: Success
   - 1: Task failure / unreachable
   - 2: Host unreachable (distinct from failure)
   - 4: Syntax error
   - 127: ansible-playbook not found
   - 130: SIGINT (Ctrl+C)

7. **Strategy Detection**:
   - `v2_playbook_on_task_start` WITHOUT prior `v2_runner_on_start` → **linear**
   - `v2_runner_on_start` events for each host → **free/host_pinned**

### Minimum Viable Test Set (4 Playbooks)

For comprehensive coverage with minimal tests:
1. **Happy Path** — Basic success, all events, COMPLETED state
2. **Failure Scenarios** — FAILED state, `ignore_errors`, `v2_runner_on_failed`
3. **Role-Based** — RoleGroup creation, role grouping
4. **Interrupt & Signals** — SIGINT handling, terminal cleanup, exit codes

### Files Created
- `.sisyphus/notepads/implementation/INTEGRATION_TEST_PLAN.md` — Full 1159-line document with 12 playbook designs

## 2026-04-24 StatusBar render() Implementation

### Pattern Used
- `render()` method returns `Text` from `rich.text`
- Elements configured via `StatusBarConfig.elements` list
- Element mapping: `playbook_name`, `elapsed_time`, `task_progress`, `current_task`, `host_count`, `memory_usage`, `subprocess_pid`
- Separator: `" │ "` (matching compact renderer's `format_status_bar()`)
- Empty config defaults to `["playbook_name", "elapsed_time", "task_progress"]`
- Unknown elements silently skipped
- Empty values filtered out before joining

### Key Design Decisions
- Return `Text("")` not `None` when no parts (Textual requires renderable)
- Call formatter methods rather than duplicating formatting logic
- Pre-existing docstrings in file follow Args/Returns style - preserved for consistency

## 2026-04-24 SummaryPanel render() Implementation

### Pattern Used
- `render()` method returns `Text` from `rich.text`
- Multi-line output using `\n`.join() for newline separation
- Displays: play name, hosts progress, tasks progress, elapsed time
- Uses existing `_format_elapsed_time()` method for time formatting
- No separator character (unlike StatusBar's " │ ") - uses newlines for vertical layout
- Default state shows "No active play" from `_play_name` initialization

### Key Design Decision
- Always shows all four fields regardless of state (play name "No active play" when inactive)
- Tests focus on DATA LAYER (formatters, setters) not rendering output
- Existing methods preserved exactly - only render() added

## 2026-04-24 DebugPanel render() Implementation

### Pattern Used
- `render()` method returns `Text` from `rich.text`
- Multi-line output using `\n`.join() for newline separation
- Access private attributes directly (not via get_debug_summary) to avoid type issues with `dict[str, object]`
- All 12 fields displayed, each on its own line with label prefix
- Dicts formatted as comma-separated `key=value` pairs
- Empty dicts show "(none)", None values show "N/A"

### Fields Displayed
1. Command - command string or N/A
2. Environment - env overrides as `KEY=value, KEY2=value2` or "(none)"
3. Events - integer count
4. Parse errors - count (len of list)
5. Callback status - string status
6. Timing stats - dict as `key=X.Xms` or "(none)"
7. PID - integer or N/A
8. State tree - dict as `key=value` or "(none)"
9. Pending events - integer count
10. Memory - tuple as `RSS: Xm VSZ: Xm` or N/A
11. Renderer FPS - float with 1 decimal
12. Event latency - float with 1 decimal + "ms"

### Key Design Decision
- Use private attributes directly for type safety (avoids mypy errors from `dict[str, object]`)
- Removed TDD stub notice from module docstring since implementation is complete

## 2026-04-24 MainScreen Data Flow Wiring

### Update Methods Implemented
- MainScreen now has 7 update methods that propagate RunState to child widgets:
  - `update_from_state(run_state)` — extracts play name, host/task progress from RunState and updates all widgets
  - `update_play_name(name)` — updates SummaryPanel and StatusBar
  - `update_hosts_progress(completed, total)` — updates SummaryPanel and StatusBar
  - `update_tasks_progress(completed, total)` — updates SummaryPanel and StatusBar
  - `update_elapsed(seconds)` — updates SummaryPanel and StatusBar with calculated start time
  - `update_log_line(line)` — writes to LogPanel
  - `update_debug_from_summary(summary)` — updates DebugPanel from dict with type coercion

### Textual Widget Query Pattern
- Use `self.query_one(WidgetClass)` to find child widgets
- DebugPanel not composed by default but still queryable if added
- Completed status values: ("ok", "changed", "failed", "skipped", "unreachable")

### Key Import
- `from ansible_aom.core.models import RunState`
- Removed "TDD: STUB implementations" comment as implementation is complete

## 2026-04-24 LogPanel Auto-Scroll Implementation

### Key Textual Discovery
RichLog's `write()` method accepts `scroll_end` parameter - pass `scroll_end=self._auto_scroll` instead of calling `scroll_end()` separately. This is the clean pattern.

### Auto-Scroll State Machine
- `_auto_scroll = True` on mount (initial state)
- `on_scroll()` event handler: check `self.is_vertical_scroll_end`
  - If at bottom: set `_auto_scroll = True`
  - If scrolled up: set `_auto_scroll = False`
- `scroll_to_end()`: public method to re-enable auto-scroll and scroll to bottom
- `write_line()`: pass `scroll_end=self._auto_scroll` to parent's write()

### Textual Widget Properties
- `is_vertical_scroll_end`: property returning True when scrolled to max (inherited from Widget)
- `scroll_end(animate=False)`: scroll to bottom immediately
- `on_scroll()`: event handler automatically called on scroll events

## 2026-05-08 Password Test Implementation (TC-143 through TC-148)

### Mock Path Patterns for AOM
- **Compact mode password module**: Mock `ansible_aom.compact.password.getpass.getpass` (imported at module level)
- **Compact mode renderer**: Mock `ansible_aom.compact.renderer.do_handle_password_prompt` (imported with `from ... as` alias)
- **TUI app getpass**: Mock `getpass.getpass` (local import `import getpass` inside method — must mock the stdlib module, not the app module attribute)
- **Key insight**: When a module uses `import getpass` inside a method body, `patch("module.app.getpass")` fails because `getpass` is never an attribute of `app`. Use `patch("getpass.getpass")` instead.
- **Display class mocking**: Use `patch.object(renderer._display, "stop")` / `patch.object(renderer._display, "start")` since the Display instance is attached to the renderer

### TDD Method
- Created `tests/compact/__init__.py` (empty) and `tests/compact/test_password.py` (56 tests)
- TC-143 through TC-148 fully covered
- No source file modifications needed

### Test Categories
- **TC-143** (PTY integration): 20 tests — `is_password_prompt()`, `handle_password_prompt()` delegates to getpass, cursor positioning, error handling, child param compatibility
- **TC-144** (Compact flow): 7 tests — Display.stop/start order, try/finally guarantee, return values
- **TC-145** (Terminal pass-through): 11 tests — getpass masking, prompt display, special chars, cursor positioning, non-TTY fallback
- **TC-146** (TUI modal): 6 tests — suspend() context, prompt suffix, return values, error handling, synchronous nature
- **TC-147** (Password masking): 5 tests — getpass masking in both modes, Renderer Protocol interface

## 2026-05-24 Tree replay determinism harness

- Added a pure frame-capture helper in `tests/integration/test_replay_determinism.py` that
  drives `RunState.handle_event()` + `TreeProjection.from_run_state()` + `tree_lines(now=...)`
  for every JSONL event.
- Deterministic timestamps came straight from each event's `_timestamp`, so the captured frame
  signatures stay stable across repeated runs.
- A shared-prefix assertion across successive frames is a lightweight guard against row churn /
  reordering without needing full snapshot fixtures.
- **TC-148** (Timeout default): 9 tests — DEFAULT_PASSWORD_TIMEOUT=60, type checks, timeout constant availability

## 2026-05-25 run_once / serial window probe

- Real `ansible.posix.jsonl` output for `serial: 1` repeats `v2_playbook_on_play_start` once per batch.
- The repeated play-start events keep the same `play.id` and `play.path`, and the repeated task events keep the same `task.id` and `task.path`.
- The only stream field that clearly changes at the batch/window boundary is `play.duration.start` on each repeated `v2_playbook_on_play_start` event.
- For the `run_once: true` task under `serial: 1`, the task row still reappears once per batch with the same task identity; the host field changes from `web1` → `web2` → `web3` across batches.
- Recommendation: treat `play.duration.start` (or an internal ordinal derived from repeated play-start events) as the smallest stable batch/window discriminator and scope runtime play/task row identity with it.

## 2026-06-21 Play boundary regression repros

- Added `tests/unit/test_play_boundary_state.py` to pin two play-boundary regressions in `core.models`.
- Duplicate `v2_playbook_on_play_start` for the same `play.id` currently replaces the whole `PlayRunState`, so the repro asserts that completed task entries must survive the second play-start.
- The cross-play meta-task repro needs the next play's first `v2_playbook_on_task_start` before any boundary finalization can mask the issue; otherwise `_finalize_play()` makes the state look healthy too early.

## 2026-05-08 nom-style Display Backend Swap (branch: feat/nom-compact-renderer)

### What changed

- **`compact/display.py`**: replaced `rich.live.Live` with direct stdout
  ANSI cursor positioning + DEC mode 2026 (synchronized output). Public
  API (`start`/`stop`/`update`/`print_log`/`clear`, `is_running`, `is_tty`)
  is preserved so `CompactRenderer` needs no changes. Each frame is wrapped

## 2026-05-24 Tree meta-task normalization

- Compact tree projection now treats explicit `meta: ...` tasks as hostless
  control-flow rows: the task stays visible, but synthetic host leaves are
  suppressed even when runtime fallback data is present.
- Caveat: the heuristic is intentionally narrow and string-based; if Ansible
  introduces other hostless pseudo-actions, add them explicitly instead of
  broadening the fallback.
  in BSU (`\x1b[?2026h`) / ESU (`\x1b[?2026l`) so multi-line redraws apply
  atomically without flicker.
- **250 ms refresh throttle ported.** `Display.update()` records the
  monotonic timestamp of each emitted frame and skips writes that fall
  inside the window — rapid bursts coalesce to the latest content.
  `print_log()` bypasses the throttle (logs are informational) but resets
  the throttle clock since the status is redrawn as part of the same frame.
- **`compact/renderer.py::handle_completion`**: now prints the final
  summary on stdout when `is_tty=False`. Closes PQ6 — without this, a
  piped run produced zero final-state output because `Display.update()`

## 2026-05-25 run_once / serial replay identity

- `serial` is a play-level batching directive, not a separate strategy.
  `run_once` executes once per active batch, so the same logical task can
  legitimately reappear across multiple execution windows in one play.
- The existing `task.path` disambiguation still covers same-name async /
  delegated rows inside a batch, but it does **not** distinguish repeated
  `run_once` windows across serial batches.
- The missing dimension is batch identity: play identity alone is too
  coarse, and per-task runtime identity alone is too fine. The durable
  key needs to include the current batch/window.

## 2026-05-24 Phase 0 replay harness / frame coverage

### Deterministic replay helper
- Added `ansible_aom.core.replay.iter_tree_frames()` as a pure helper that
  reuses one `TreeProjection` across successive JSONL events.
- This preserves projection-local continuity state during replay, which is
  required for frame-by-frame assertions instead of final-snapshot-only checks.

### Frame-level regression shape
- The replay regression now inspects per-frame task groups, not just the final
  tree text.
- Same-name concurrent task rows can be asserted by grouping each frame’s task
  label with the attached host leaves; that catches row swapping / collapse if
  it ever regresses.
  is a no-op in non-TTY mode.
- **`core/session.py::cleanup_old_sessions`**: was using `datetime.now()`
  as the fallback sort key for sessions without `meta.json`, giving every
  fallback the same microsecond and producing nondeterministic order
  (TC-228 was flaky for this reason). Now uses directory `mtime`. Also
  fixed `except json.JSONDecodeError, ValueError:` — Python 3 parses that
  as Py2-style "catch only `JSONDecodeError`, bind to local `ValueError`"
  and silently shadows the builtin name inside the block; replaced with
  the parenthesised tuple form.

### Test impact

- Suite: **1583 passed, 0 failed, 6 skipped** (was 1579/1/6).
- Added `tests/compact/test_display_ansi.py` (2 tests): asserts BSU/ESU
  presence in TTY output and absence in non-TTY output.
- Rewrote 5 tests in `tests/integration/test_compact_renderer.py` that
  asserted Rich Live implementation details (`_live`, `_console.show_cursor`,
  `live.refresh_per_second`) to assert observable behaviour: non-TTY

## 2026-05-25 Sticky fallback identity split

- `TreeProjection._last_running_play_id` stays on the legacy plain runtime
  play id for sticky-fallback compatibility and test expectations.
- Window-aware lease/selection now uses a separate internal runtime identity
  (`play_id + window_start/window_ordinal`) so repeated `serial` / `run_once`
  batches still disambiguate active play windows.
- This split keeps public sticky state stable while preserving batch-safe
  selection and lease lookup in the projection layer.
  produces no ANSI, `stop()` emits the show-cursor sequence, throttle
  coalesces frames within 250 ms.

## 2026-05-24 Projection lifecycle note

- `CompactRenderer` should keep the cached `TreeProjection` alive across
  non-structural result events (`runner_on_ok` / failed / skipped /
  unreachable) so sticky tree state stays anchored between frames.
- Projection invalidation is still needed for task/host start events
  (`task_start`, handler task start, `runner_on_start`) because those can
  introduce new tree nodes and new role-name memo entries.
- Added one PQ6 test asserting non-TTY `handle_completion` prints the
  final summary as plain text.

## 2026-05-10 Runner Implementation (same branch)

### What changed

- **New `src/ansible_aom/runner.py`** — `run_playbook(playbook, args, renderer)`
  spawns `ansible-playbook` via `pexpect.spawn` with `ANSIBLE_STDOUT_CALLBACK=ansible.posix.jsonl`,
  reads the PTY line-by-line using `child.expect([newline, EOF, TIMEOUT, *PASSWORD_PATTERNS])`,
  feeds JSONL lines to the existing `PtyStreamParser`, and pumps emitted
  events into the renderer via `update_state`.
- **Password prompts are matched at the pexpect layer**, not in the parser.
  Live PTY prompts (`Vault password: `) have no trailing newline so they
  never reach the parser's line-oriented `feed_line`. The runner round-trips
  through `renderer.handle_password_prompt(prompt)` and writes the result
  back to the child via `child.sendline`.
- **Lifecycle ownership** — `renderer.start` before spawn,
  `handle_completion(exit_code, state)` on exit, `renderer.stop` in a
  `finally`. Spawn-time failures (`ExceptionPexpect`/`FileNotFoundError`/
  `OSError`) → exit 127, state="crashed". `KeyboardInterrupt` →
  `child.sendintr() + close(force=True)` → exit 130.
- **`cli.py` rewired** to call `run_playbook` instead of the previous stub.
  Renderer constructed with `is_tty=sys.stdout.isatty()` so the PQ6
  non-TTY summary path activates correctly under pipes.

### Test impact

- New `tests/integration/test_runner.py` — 4 tests covering happy path,
  event forwarding, non-zero exit → state="failed", missing executable →
  exit 127 + state="crashed". Tests substitute a fake "ansible-playbook"

## 2026-05-24 Tree play identity caveat

- Tree projection now prefers `play_id` for joining runtime plays to
  preflight play definitions, with display-name matching only as a
  fallback for legacy/partial streams. This prevents duplicate visible
  play names from collapsing into one projection row.
  built from `python -c "..."` that emits canned JSONL — exercises the
  real spawn/expect loop without needing Ansible to be installed.
- Updated TC-027 in `tests/unit/test_cli.py` — used to patch
  `create_renderer.side_effect = FileNotFoundError`; now patches
  `runner.run_playbook` because that's where the FileNotFound handling
  lives.
- Suite: **1587 passed, 0 failed, 6 skipped** (was 1583/0/6).

### End-to-end smoke

```
$ uv run aom .sisyphus/test-fixtures/simple.yml -i localhost, -c local
.sisyphus/test-fixtures/simple.yml │ 1/1 hosts │ 0:00:00 ●
$ echo $?
0

$ uv run aom .sisyphus/test-fixtures/syntax_error.yml -i localhost, -c local
.sisyphus/test-fixtures/syntax_error.yml │ 0/0 hosts │ 0:00:00 ✖
$ echo $?
4
```

### Quirk noted

Python 3.14 parses `except A, B, C:` as the same `ast.Tuple` as
`except (A, B, C):` — i.e. it now means "catch any of these three", not
the Py2 "catch A and bind to local B" semantics. Ruff format takes the
parens away and accepts the parens-less form as canonical. **The fix in
`session.py` (commit a4bd140) was about clarity, not a bug** — both
forms catch the tuple correctly under 3.14. The session.py file got
re-formatted by ruff after the commit so the parens may be gone again
on disk. Worth deciding as a project: keep parens for portability to
older Pythons or accept ruff's preference. Project is currently 3.14-only
(`requires-python = ">=3.14"`), so ruff's preference is harmless here.

### Still open after this branch

- **Pre-flight `--list-tasks` / `--list-hosts`** — runner skips them.
  The renderer therefore can't show the full task tree or resolved-hosts
  list at startup; it builds state purely from JSONL events as they
  arrive. ARCHITECTURE.md's data-flow diagram describes parallel
  pre-flight that still doesn't exist yet. **Next major slice.**
- **`_row_count()` is approximate** — no width-aware wrapping. Long
  status lines that wrap will under-count rows; redraws will leave
  artefacts. Currently the panel is single-line, so this is theoretical.
- **Terminal resize (SIGWINCH)** is not handled.
- **ASCII fallback for non-Unicode terminals** — `core/icons.py` has
  the mapping (`STATUS_ICONS_ASCII`) but the renderer hard-codes the
  Unicode forms in `format_status_bar` and `handle_completion`. Needs
  a `supports_unicode()` detector + icon-set parameter threading.

## 2026-05-24 Delegated task identity normalization

- `TaskRunState.path` now persists the upstream JSONL task path, so core
  projection can distinguish same-name delegated/non-delegated task rows
  without repurposing host attribution.
- `TreeProjection._play_running_and_pending()` now prefers exact
  `task.path` matches before bare-name heuristics, which keeps the
  delegated and non-delegated twins in preflight order even when runtime
  arrival order is reversed.
- Regression added in `tests/unit/test_tree_projection.py` using the
  real server-setup delegate example (`deploy_vms.yml:134`) and a
  non-delegated twin (`snapshot.yml:13`).

## 2026-05-10 TTY UX fixes + nom-style streaming logs (same branch)

Triggered by an interactive smoke test from the user: "starts and
immediately terminates and clears". Diagnosed as four coupled gaps —
the panel cleared on stop with no record left, no streaming task output
during the run, no elapsed-time updates during quiet periods, and the
warnings counter stuck at zero because of an ANSI-prefix mismatch.

### What changed

- **`compact/renderer.py::handle_completion`**: moved the final-summary
  `print()` outside the `if not is_tty` guard and put it AFTER `stop()`.
  In TTY mode this lands at the cursor position the panel used to occupy,
  leaving the run outcome as the last visible line; in non-TTY it's the
  only output Display ever produces (PQ6 still satisfied).
- **`compact/renderer.py::_emit_event_log`**: new helper called from
  `update_state` that prints a nom-style log line above the status panel
  for each significant event (PLAY, TASK headers, ok/changed/fatal/
  skipping per host). v2_playbook_on_stats stays silent — the panel and
  the final summary already cover that. Throttling on the panel update
  means the panel may visibly trail the logs, which matches nom.
- **`compact/renderer.py::tick`**: new public method that re-renders
  the status bar without processing an event. Extracted the status-bar
  computation into `_render_status_bar()` so both `update_state` and
  `tick` share it. The runner's TIMEOUT branch calls `tick()` via
  `getattr` so renderers without it (TUI) are silently skipped.
- **`core/parser.py::_handle_plaintext`**: strip CSI SGR escapes
  before matching `WARNING_PATTERNS`. Real ansible-playbook prints
  `\x1b[1;35m[WARNING]:\x1b[0m...` and the `^\[WARNING\]:` anchor
  never matched through the colour escape. Store the cleaned message
  so downstream UI doesn't need to re-strip.
- **`core/parser.py::drain_warnings`**: returns and clears the warnings
  list in one call, so the runner can forward newly-detected warnings
  without tracking an index.
- **`runner.py::_feed`**: after each `feed_line`, drain warnings and
  forward via `renderer.add_warning(message, is_deprecation)` if the
  renderer implements it (getattr-guarded).

### Test impact

- Suite: **1594 passed, 0 failed, 6 skipped** (was 1587/0/6).
- New tests cover: TTY final-summary persistence, log-line emission for
  every significant event type, `tick()` panel-only refresh, ANSI-
  prefixed warning classification (with backwards-compat for plain form
  and a negative case for non-warning ANSI text).

### End-to-end smoke (pipe mode)

```
$ uv run aom .sisyphus/test-fixtures/simple.yml -i localhost, -c local

PLAY [Simple test playbook] *********...
TASK [First task] *********...
ok: [localhost]
TASK [Second task with tags] *********...
ok: [localhost]
TASK [Third task] *********...
ok: [localhost]
.sisyphus/test-fixtures/simple.yml │ 1/1 hosts │ ⚠ 1 │ ✱ 1 │ 0:00:00 ●
```

The `⚠ 1 │ ✱ 1` confirms the warning + deprecation that ansible-core
2.20 emits at startup are now reaching the panel.

### Still open after these fixes

- **Pre-flight `--list-tasks` / `--list-hosts`** (unchanged — next major
  slice). The renderer can't show the task tree at startup yet.
- **`_row_count()` width-aware wrapping**, **SIGWINCH**, **ASCII
  fallback wiring** (unchanged).
- **Stderr-only diagnostics** — pexpect.spawn merges stderr into the
  pty, so warnings come through; but ansible-playbook's syntax-error
  diagnostics go to stderr in a way that doesn't always reach our
  parser (the syntax_error.yml smoke shows exit 4 with an empty log).
  Worth investigating once pre-flight is in.
- **Renderer Protocol gaps** — `tick`/`add_warning` are getattr-guarded
  on the runner side. Once the TUI is wired through `runner.run_playbook`
  (rather than its current `app.run()` path), we should promote both to
  the Protocol so calls aren't optional.
- **Visual TTY smoke** — please re-run interactively now that streaming
  logs + final-summary persistence are in. Should look like nom: logs
  scrolling, panel anchored, summary survives at the cursor on exit.

## 2026-05-24 Recursive grouped-role traversal

- `RoleGroupDefinition.tasks` and nested `TaskDefinition.children` now
  share one recursive preflight walk in `core/models.py` + `core/tree.py`,
  so `_task_def_index`, role labels, and tree emission stay in the same
  order for grouped roles with include_role/import_role descendants.
- The sticky play fallback only stops lingering once the active play's
  nested running task is visible to the tree; recursive traversal makes
  that nested async-status row count as the active play instead of a stale
  previous play.

## 2026-05-10 Pre-flight `--list-tasks` / `--list-hosts` (same branch)

The major slice that was open after the TTY UX work — runner now does
parallel pre-flight before the JSONL spawn so the renderer has plays,
tasks, and resolved hosts from the very first frame instead of building
state purely from JSONL events as they arrive. Plan in
`docs/superpowers/plans/2026-05-10-preflight-listing.md`.

### What changed

- **New `core/preflight.py`** — split by purity per the ABSTRACT rule
  in CLAUDE.md:
  - `assemble_definitions(plays=, play_hosts=)` — pure mapping from raw
    parsed dicts (output of existing `parse_list_tasks_output` /
    `parse_list_hosts_output`) to `list[PlayDefinition]` with
    `TaskDefinition` children, applies `group_roles` for 5+-task role
    collapses, stitches `resolved_hosts` in by `play_number`. No I/O.
  - `run_preflight(playbook=, ansible_args=, executable=...)` — spawns
    `ansible-playbook --list-tasks` and `--list-hosts` concurrently in
    a `ThreadPoolExecutor` (max_workers=2) with a 30s timeout each.
    Subprocess errors (FileNotFoundError → 127, PermissionError → 126,
    TimeoutExpired → 124, OSError → 1) become entries in
    `PreParseResult.errors` rather than exceptions. Whichever
    subprocess succeeded still contributes its data.
- **`core/parser.py::PreParseResult`** — extended with two optional
  fields: `definitions: list[PlayDefinition]` and `errors: list[str]`.
  Defaults to empty so existing call sites keep working.
- **`renderer/protocol.py::Renderer`** — new required Protocol method
  `set_definitions(definitions: list)`. Called once between `start()`
  and the first `update_state()`. Annotated as `list` (not
  `list[PlayDefinition]`) to keep the Protocol free of model imports;
  `runtime_checkable` only verifies presence anyway.
- **`compact/renderer.py::CompactRenderer`** — new `_definitions: list`
  attribute and `set_definitions()` method that recomputes the status
  bar. The host count is now `max(len(host_statuses_from_jsonl),
  len(union of resolved_hosts))` — preflight seeds the denominator
  from frame zero, JSONL takes over once events arrive. Same union
  logic applied to `handle_completion()`.
- **`tui/app.py::AOMApp.set_definitions`** — no-op for now. The TUI
  builds its tree from RunState; preflight wiring there is a separate
  slice once the TUI moves under `runner.run_playbook`.
- **`runner.py::run_playbook`** — calls `run_preflight()` after
  `renderer.start()` and before the `pexpect.spawn` block. Pushes
  `pre_result.definitions` through `renderer.set_definitions` (getattr-
  guarded) and forwards each `pre_result.errors` entry through
  `renderer.add_warning(err, False)`.

### Test impact

- Suite: **1611 passed, 0 failed, 6 skipped** (was 1594/0/6, +17 new
  tests).
- `tests/unit/test_preflight.py` — 6 tests: PreParseResult shape,
  empty-input handling, missing host data, role grouping invocation,
  basic combination from existing fixtures.
- `tests/integration/test_preflight_runner.py` — 4 tests using a fake
  Python `ansible-playbook` shim (same trick as `test_runner.py`):
  parallel-execution success, FileNotFoundError → error entry,
  --list-hosts failure isolated from --list-tasks success, ansible_args
  forwarded to both invocations.
- `tests/compact/test_renderer_set_definitions.py` — 5 tests:
  storage, hosts_total seeding, pre-start safety, empty-list handling,
  union across plays.
- `tests/integration/test_runner.py::TestRunnerPreflight` — 2 tests for
  the wiring: definitions forwarded to renderer, errors forwarded as
  warnings.

### End-to-end smoke (pipe mode)

```
$ uv run aom .sisyphus/test-fixtures/simple.yml -i localhost, -c local
PLAY [Simple test playbook] *********...
TASK [First task] *********...
ok: [localhost]
TASK [Second task with tags] *********...
ok: [localhost]
TASK [Third task] *********...
ok: [localhost]
.sisyphus/test-fixtures/simple.yml │ 1/1 hosts │ ⚠ 1 │ ✱ 1 │ 0:00:00 ●
$ echo $?
0

$ uv run aom .sisyphus/test-fixtures/syntax_error.yml -i localhost, -c local
.sisyphus/test-fixtures/syntax_error.yml │ 0/0 hosts │ ⚠ 2 │ 0:00:00 ✖
$ echo $?
4
```

The `⚠ 2` on `syntax_error.yml` is preflight's two failures (one each
from `--list-tasks` and `--list-hosts`) bubbling up via `add_warning` —
this is new diagnostic surface that didn't exist before. Closes the
"empty log on syntax error" gap noted in the previous session's "still
open" list.

### Still open after this slice

- **Task tree rendering** — preflight now hands the renderer a full
  `list[PlayDefinition]` with tasks, but the compact renderer only uses
  it to seed `hosts_total`. Drawing the actual tree (preview before
  run, progress during run) is a follow-up slice and depends on the
  width-aware `_row_count()` work since a multi-line panel will hit
  the wrap-counting bug.
- **TUI preflight integration** — `AOMApp.set_definitions` is a no-op.
  Should populate `TaskTree` widget once the TUI moves under
  `runner.run_playbook`.
- **Unicode warning escape** — same warning text is now emitted twice
  in some cases (once from preflight stderr, once from JSONL stderr).
  Worth deduping if it produces noisy `⚠` counts in the wild.
- **`include_tasks` dynamic expansion** — TC-094 / TC-095 still
  unimplemented. Definitions from preflight are static; runtime needs
  to graft dynamic tasks under their `include_tasks` parent when
  unknown task UUIDs arrive.
- **`_row_count()` width-aware wrapping**, **SIGWINCH**, **ASCII
  fallback wiring** (unchanged).

## 2026-05-10 Pre-flight summary + error visibility (same branch)

Two follow-up polish slices on top of the preflight orchestration:

### What changed (slice 1: startup tree preview)

- **`compact/renderer.py::format_preflight_summary`** — pure formatter
  that turns the `list[PlayDefinition]` from preflight into a one-shot
  startup summary, one line per play:

  ```
  PLAY [Setup web servers] (webservers, 2 hosts, 3 tasks)
  PLAY [Setup database]    (dbservers, 1 host, 2 tasks)
  ```

  RoleGroupDefinition entries contribute their inner task count, not
  1. Pluralisation handled (1 host vs N hosts). Returns None for empty
  input so the caller can skip the print.
- **`compact/renderer.py::CompactRenderer.set_definitions`** — calls
  `_display.print_log()` with the formatted summary so it lands above
  the status panel in TTY mode and as plain text in pipe mode.

### What changed (slice 2: error visibility + NOCOLOR)

- **`core/preflight.py::_preflight_env`** — sets `ANSIBLE_NOCOLOR=1`
  in the subprocess environment. ansible-playbook otherwise suppresses
  stderr entirely when stderr is not a TTY (which is always the case
  for our captured subprocess), leaving us with empty `(no stderr)`
  messages for syntax errors. With NOCOLOR set, the actual YAML
  diagnostic — line, column, source-context lines — comes through.
- **`compact/renderer.py::CompactRenderer.print_log`** — thin
  pass-through to `Display.print_log()`. Lets the runner surface
  important messages above the panel without going through the
  warning-counter aggregation.
- **`runner.py::run_playbook`** — preflight errors now have two
  surfaces: full message via `renderer.print_log()` (so the user can
  actually read the YAML diagnostic), and counter bump via
  `add_warning()` (so the panel reflects the failure). Identical
  error bodies from `--list-tasks` and `--list-hosts` are deduped
  for the print path; the counter still bumps for both since both
  subprocesses really did fail.

### Test impact

- Suite: **1622 passed, 0 failed, 6 skipped** (was 1611/0/6, +11 new
  tests).
- `tests/compact/test_preflight_summary.py` — 6 tests: empty input,
  single play, multi-play, pluralisation, role-group task counting,
  no-resolved-hosts fallback.
- `tests/compact/test_renderer_set_definitions.py` — 2 added tests
  for the print-log behaviour.
- `tests/integration/test_preflight_runner.py` — 1 added test
  asserting `ANSIBLE_NOCOLOR=1` is set in subprocess env.
- `tests/integration/test_runner.py::TestRunnerPreflight` — 2 added
  tests: `print_log` called for preflight errors, dedup on identical
  bodies vs distinct bodies.

### End-to-end smoke (pipe mode)

```
$ uv run aom .sisyphus/test-fixtures/simple.yml -i localhost, -c local
PLAY [Simple test playbook] (localhost, 1 host, 3 tasks)

PLAY [Simple test playbook] *********...
TASK [First task] *********...
ok: [localhost]
TASK [Second task with tags] *********...
ok: [localhost]
TASK [Third task] *********...
ok: [localhost]
.sisyphus/test-fixtures/simple.yml │ 1/1 hosts │ ⚠ 1 │ ✱ 1 │ 0:00:00 ●

$ uv run aom .sisyphus/test-fixtures/syntax_error.yml -i localhost, -c local
--list-tasks failed (exit 4): [ERROR]: YAML parsing failed: While scanning a simple key could not find expected ':'.
Origin: /Users/felix/Coding/ansible-aom/.sisyphus/test-fixtures/syntax_error.yml:10:12

 8     - name: Broken task
 9       debug
10         msg: "bad syntax - missing colon"
              ^ column 12
.sisyphus/test-fixtures/syntax_error.yml │ 0/0 hosts │ ⚠ 2 │ 0:00:00 ✖
$ echo $?
4
```

The syntax_error case used to be empty-log + exit 4 — now shows the
full ansible diagnostic above the panel, deduped to one print, with
the counter still showing `⚠ 2` since both preflight subprocesses
genuinely failed.

### Quirk noted: `ANSIBLE_NOCOLOR` vs `ANSIBLE_FORCE_COLOR`

ansible-playbook's TTY-detection-driven output has three modes:
- TTY stderr → coloured output
- non-TTY stderr (default) → suppressed entirely
- non-TTY stderr + `ANSIBLE_NOCOLOR=1` → plain output
- non-TTY stderr + `ANSIBLE_FORCE_COLOR=1` → coloured output

We use NOCOLOR rather than FORCE_COLOR + strip — saves us an ANSI-strip
pass and there's no benefit to colouring output we're going to wrap in
our own format string anyway.

### Still open after this slice

- **Task progress in status bar** — currently `X/Y hosts` only. Adding
  `task: M/N` would use preflight's static count, but include_tasks
  inflates the dynamic count. Probably wants a "tasks done" tally
  rather than a fraction.
- **TUI preflight integration**, **`include_tasks` dynamic
  expansion**, **width-aware row count**, **SIGWINCH**, **ASCII
  fallback** — all unchanged from before.
- **Renderer Protocol cleanup** — `print_log` joins `tick`/`add_warning`
  as getattr-guarded on the runner side. All four (incl. preflight's
  `set_definitions`) want to be required Protocol methods once the TUI
  is wired through `runner.run_playbook`, so no more stringly-typed
  attribute lookups.

## 2026-05-10 TTY rewind bug + UX polish (same branch)

User reported: "terminal clearing may also affect the currently/last
displayed command line that started aom" (interactive fish smoke).
True bug, plus three UX polish items in the same session.

### Bug fix: status rewind erased the command line above

`Display._rewind_status()` returned `CSI N F` for an N-row status, where
`F` is "cursor previous line" — it moves UP N lines and to col 1. After
writing an N-row status with no trailing newline, the cursor is on the
LAST row of the block; to get back to the FIRST row needs N-1 lines up.
For N=1 it needs no vertical movement at all, just `\r`.

The old code over-rewound by one line. With the typical 1-row status
the rewind landed on the user's shell command line; the subsequent
`CSI J` (clear-to-EOS) wiped it. Every redraw repeated the damage.

Fix in `compact/display.py::_rewind_status`:
- N = 0: return `""` (unchanged — nothing drawn yet)
- N = 1: return `"\r"` (cursor already on the right row)
- N > 1: return `CSI (N-1) F`

Tests in `tests/compact/test_display_ansi.py::TestRewindCorrectness`
pin three cases: 1-row uses `\r`, multi-row uses `CSI (N-1) F`, the
print_log-after-update flow never emits `CSI 1 F` (the bug signature).

### UX polish 1: per-host summary on completion

`format_host_summary()` had been sitting in `compact/renderer.py` with
its own unit tests but no caller. Now `handle_completion` aggregates
per-host status counts across every task in every play and prints
one indented line per host underneath the aggregate status:

```
.sisyphus/test-fixtures/simple.yml │ 1/1 hosts │ ⚠ 1 │ ✱ 1 │ 0:00:00 ●
  localhost: ● 3 ok
```

With one host this barely differs from the aggregate; with N hosts
it's the only way to see who succeeded vs who failed at a glance.
Empty-state-safe — preflight-only-failure runs don't get a stray
hosts block.

### UX polish 2: warnings now visible, not just counted

`⚠ 1` on the panel was opaque — the user had no way to know whether
the warning was a benign deprecation notice or something they should
act on. `CompactRenderer.add_warning` now prints each unique warning
message via `Display.print_log` AND bumps the counter (as before).

Repeated identical messages (e.g. the same deprecation firing
per-host on a many-host run) print once but each still contributes
to the counter — `_seen_warning_messages: set[str]` tracks the
prints. The parser keeps the raw `[WARNING]: ...` /
`[DEPRECATION WARNING]: ...` prefix on the message, so we print
as-is when the message already starts with `[`, and add our own
`[WARNING]` / `[DEPRECATION]` prefix only when it's absent.

### Test impact

- Suite: **1633 passed, 0 failed, 6 skipped** (was 1622/0/6, +11 new
  tests this session).
- `tests/compact/test_display_ansi.py` — 3 new tests for rewind
  correctness.
- `tests/compact/test_completion_summary.py` — 3 new tests covering
  per-host breakdown, indent, empty-state safety.
- `tests/compact/test_warning_visibility.py` — 5 new tests covering
  print-with-message, prefix classification, counter still bumps,
  dedupe of repeats, distinct messages each print.

### End-to-end smoke (pipe mode)

```
$ uv run aom .sisyphus/test-fixtures/simple.yml -i localhost, -c local
PLAY [Simple test playbook] (localhost, 1 host, 3 tasks)
[WARNING]: Deprecation warnings can be disabled by setting `deprecation_warnings=False` in ansible.cfg.
[DEPRECATION WARNING]: Importing 'to_text' from 'ansible.module_utils._text' is deprecated. ...

PLAY [Simple test playbook] *********...
TASK [First task] *********...
ok: [localhost]
TASK [Second task with tags] *********...
ok: [localhost]
TASK [Third task] *********...
ok: [localhost]
.sisyphus/test-fixtures/simple.yml │ 1/1 hosts │ ⚠ 1 │ ✱ 1 │ 0:00:00 ●
  localhost: ● 3 ok
```

### Feature roadmap (open question for next session)

User asked: "what other features would be useful? how can we make
usage as easy and simple as possible, with sane defaults?"

Ranked rough notes; pick which are worth a slice:

**Smaller / quick wins:**
1. **Promote getattr-guarded methods to required Protocol** —
   `print_log`, `add_warning`, `tick`, `set_definitions` are all on
   CompactRenderer; AOMApp can implement no-op or sensible. Removes
   the stringly-typed lookups in `runner.py`.
2. **Auto-detect `./inventory.ini`** — if no `-i` flag and the file
   exists in cwd, default to it. ansible.cfg-driven users won't be
   affected because they have an explicit setting.
3. **`--check` / `--diff` first-class flags** — currently passable as
   REMAINDER args. Promoting to first-class lets aom remember and
   replay them.
4. **Better `aom` (no-args) output** — current help is verbose;
   could lead with a single Usage line.

**Medium / feature-shaped:**
5. **Task progress in status bar** — `tasks: M/N` uses preflight's
   static count for N. Caveat: include_tasks inflates the dynamic
   count past N. Could show "tasks: M" without denominator, or use
   "tasks: M of ~N" to signal the soft estimate.
6. **Verbose passthrough** — repeated `-v` (`-vvv`) maps to
   ansible-playbook's verbosity. Mildly tricky because aom's own `-v`
   currently means "diagnostics-on", not passthrough.
7. **Recap-style failure summary** — when something failed, list the
   failed task name + host + first message line at the bottom, above
   the per-host summary. Right now the user has to scroll up through
   the log to find the fatal line.
8. **Tag preview** — preflight summary could include "tags: [foo, bar]"
   per play, so the user can sanity-check before passing `--tags`.

**Large / blocked:**
9. **TUI end-to-end** — currently broken. AOMApp uses `app.run()` for
   its own event loop; runner calls `update_state()` from a different
   loop. Needs `call_from_thread` plumbing or a different model where
   the runner drives Textual's loop.
10. **`aom inspect` subcommands** — list/show/diff/prune are stubs.
    Spec describes session artifacts in `.aom/` but the writer isn't
    wired in.
11. **`include_tasks` dynamic expansion** — TC-094/TC-095. Need to
    graft TaskDefinition(is_dynamic=True, task_order=-1) under the
    parent include_tasks node when unknown task UUIDs appear.
12. **SIGWINCH + width-aware `_row_count()`** — robustness for tall
    panels with wrapping, terminal resize. Currently theoretical.
13. **ASCII fallback** — `core/icons.STATUS_ICONS_ASCII` exists; the
    renderer hard-codes Unicode. Need a `supports_unicode()` detector
    + parameter threading.
14. **Session recording** — write `.aom/<session_id>/` with raw JSONL,
    state snapshot, diagnostics. Enables `aom inspect`.

---

## 2026-05-10 (later) — Argparse-wall trim, recap-style summary, inventory auto-detect

User reported (verbatim):
> `uv run aom .sisyphus/test-fixtures/simple.yml -i localhost -c local
> .sisyphus/test-fixtures/simple.yml`
> ... `ansible-playbook: error: unrecognized arguments: ...` followed
> by ~200 lines of `--help` text dumped twice into the panel.

Three slices delivered, all TDD, all green (1656 passing, 6 skipped).

### 1. Trim argparse help wall from preflight stderr
`core/preflight._trim_stderr()` extracts only lines matching
`^[\w.-]+:\s*error:\s*.+` from stderr; falls back to the first 5
non-empty lines when no marker is present. Drops the redundant
`print_log` path in `runner.py` — `add_warning` already prints + bumps
counter, so the two-surface dance produced doubled output.

Net effect on the user's command above: from ~200 lines of help text
to two clean lines:
```
[WARNING] --list-tasks failed (exit 2): ansible-playbook: error: unrecognized arguments: ...
[WARNING] --list-hosts failed (exit 2): ansible-playbook: error: unrecognized arguments: ...
```

Tests: `test_preflight.py` (5 new `_trim_stderr` cases) +
`test_preflight_runner.py` (1 new integration). Two old runner
tests pinning `print_log`-side dedupe deleted; replaced by single
`test_run_playbook_forwards_every_preflight_error_to_add_warning`.

### 2. Failure recap on completion
New `format_failure_recap(state)` in `compact/renderer.py` returns one
line per (host, task) pair that ended FAILED or UNREACHABLE.
`handle_completion` calls it after the per-host summary block, gated on
`exit_code != 0`. Visual: indented under the status line, mirrors
the per-host summary's two-space indent.

Roadmap item #7 from yesterday — checked off.

### 3. Inventory auto-detect (CLI)
`cli.detect_default_inventory()` walks a preference-ordered tuple of
conventional names (`inventory.ini` → `.yml`/.yaml → `inventory` →
`hosts.ini` → `hosts.yml`/.yaml → `hosts`). `ensure_inventory_arg()`
prepends `-i <path>` to ansible_args iff none of `-i`,
`--inventory`, `--inventory-file`, `--inventory=...` is present AND a
candidate file exists in CWD.

Roadmap item #2 — checked off.

### What's still open

Quick wins remaining:
- (#1) Promote optional Protocol methods (`print_log`, `add_warning`,
  `tick`, `set_definitions`) to required. Now that all CompactRenderer
  call sites use them, AOMApp just needs no-op stubs.
- (#3) `--check`/`--diff` first-class flags
- (#4) Better empty-aom output

Feature-shaped:
- (#5) Task progress in status bar — use preflight task count as denom
- (#6) Verbose passthrough — `-v` collision needs renaming
- (#8) Tag preview in preflight summary

Larger / blocked: 9-14 unchanged from yesterday.

### One quirk noted (not fixed)

`runner.py:117` is `except pexpect.exceptions.ExceptionPexpect, FileNotFoundError, OSError:`
— Python 3.14 happily parses this as `except (A, B, C):` (tuple
expression as the test). It's valid 3.x; not a bug; just unusual.

---

## 2026-05-10 (third pass) — Protocol promotion, kwargs cleanup, duplicate-playbook detection

User asked: "continue roadmap. simplify code & usage where possible."

Three more slices delivered (1661 passing, 6 skipped).

### 1. Promote optional Protocol methods to required (#1)
`print_log`, `add_warning`, `tick` were getattr-guarded throughout
`runner.py`. Adding no-op stubs to AOMApp lets us drop all four
guards (the fourth being `set_definitions`, which was already on the
Protocol but still guarded). Net: 4 `getattr(...)` lookups gone, the
Protocol is now an honest contract, and the runner reads top-down
without lookup-then-call dances.

### 2. Drop **kwargs from CompactRenderer + factory
`CompactRenderer.__init__(**kwargs)` only ever read `is_tty`. The
factory blindly forwarded kwargs, which would have crashed for
TUI mode if anything other than `is_tty` was passed. Replaced with
explicit `is_tty: bool = True` parameters on both. The
`test_factory_passes_kwargs_to_renderer` test was renamed to
`test_factory_forwards_is_tty_to_compact_renderer` and tightened
to assert the actual contract (Display.is_tty matches the request).

### 3. Detect duplicate playbook positional (#3 from yesterday's roadmap, repurposed)
Direct response to the user's reproducer (`aom site.yml ... site.yml`).
`detect_duplicate_playbook(playbook, ansible_args)` checks if the
positional appears (path-normalised) anywhere in ansible_args. Main
exits 2 with a one-line message before touching pexpect. The
trim-stderr work from earlier still catches the case where the user's
typo is something other than an exact path repeat.

Bonus tidy: dropped a redundant local `import os` from the verbose
branch in `cli.py` (`os` is now imported at module scope for
`detect_default_inventory`).

### Remaining roadmap

Quick wins:
- (#4) Better empty-aom output — minor; argparse help is fine
- (#3-original) `--check` / `--diff` first-class flags — works already
  via REMAINDER; first-class makes them tab-completable and visible
  in `--help` but is not strictly a simplification

Feature-shaped: 5, 6, 8 unchanged.

Larger / blocked: 9-14 unchanged.

### Quirks noted but not addressed

- `runner.py:95` `except A, B, C:` — Python 3.x parses this as
  `except (A, B, C):` (tuple expression as the except test). Valid,
  unusual, would normally write with parens. Same shape exists at
  `core/models.py:132`.

---

## 2026-05-10 — CLI cleanups + task progress segment

### 1. Drop dead `--changes-only` top-level flag
`args.changes_only` was parsed but never read in `main()` or the
runner. The useful instance lives on `aom inspect diff`. Removed the
parser arg + the two pinning unit tests.

### 2. Wire `aom inspect …` to the real implementation
The top-level CLI had a parallel stub parser (`create_inspect_parser`)
and `handle_inspect` that printed misleading lines like "Listing
sessions..." while a real implementation in
`src/ansible_aom/inspect/cli.py` already covers list / show / diff /
prune end-to-end. Refactored `inspect.cli.main` to accept an explicit
`argv: list[str] | None` so the dispatcher can pass `sys.argv[2:]`
(stripping the `inspect` token before the inspect parser sees it).

Replaced the stub-pinning `TestInspectSubcommand` parser tests (11
cases) with four dispatch tests that mock `inspect.cli.main` and
assert (a) the forwarded argv slice and (b) propagated exit code.
Real subcommand behaviour is already covered by
`tests/integration/test_inspect.py`. Deleted the
`TestInspectTUIMode` block — those four tests pinned fictional stub
behaviour that returned 0 for `aom inspect --tui`.

### 3. Drop dead `--version` arg + `NotImplementedError` catch
`main()` short-circuits on `--version in sys.argv` before parse_args
runs, so the parser-level `--version` arg and the `if args.version`
block were unreachable. Also removed `except NotImplementedError`
from the runner-call try-block — nothing in src/ raises it any more
(runner and AOMApp are both fully implemented), and the catch-all
`except Exception` already returns the same exit code 1.

### 4. Task progress segment in the status bar (roadmap #5)
Status bar now reads
`site.yml │ 3/10 hosts │ 5/47 tasks │ 0:01:23` whenever preflight
gives us a static task count. Without this segment, on a 50-task
playbook the user can't tell if they're 10% or 90% through the run.

Two pure helpers in `compact/renderer.py`:
- `count_total_tasks(definitions)` sums leaf TaskDefinitions across
  plays, expanding `RoleGroupDefinition` entries to their inner tasks.
- `count_completed_tasks(state)` counts task entries whose status is
  in `{OK, CHANGED, FAILED, SKIPPED, UNREACHABLE, COMPLETED}`. RUNNING
  is explicitly excluded — a task is in flight until every host has a
  terminal result.

`format_status_bar` gains optional `tasks_completed`/`tasks_total`
params. The segment is omitted entirely when `tasks_total == 0`, so
playbooks with only `include_tasks` (no static count) and existing
five-arg callers keep their current output. Wired into both the live
`_render_status_bar` (event + tick) and the final
`handle_completion` frame.

### 5. Tag preview + task-count fix (roadmap #8 + adjacent bug)

**Tag preview.** `format_preflight_summary` now appends `Tags: a, b, c`
when preflight `--list-tasks` produces any tags. Helper
`collect_tags(definitions)` returns the sorted unique set, expanding
`RoleGroupDefinition` entries so tags from inside roles surface. Line
suppressed when no task carries a tag (e.g. plain "always" defaults).

**Task-count fix surfaced by the live test of #8.** The previous
`count_completed_tasks` matched `TaskRunState.status` against terminal
values, but the state machine never moves task.status past
PENDING/RUNNING — only `task.hosts` gets populated, by the
`v2_runner_on_*` handlers. Result: `0/3 tasks` on a 3-task success
run. Switched to "task has at least one host result"; monotonic and
ansible-faithful for linear strategy. The dead `_TASK_DONE_STATUSES`
frozenset got removed with the change. Updated tests to use realistic
state shape (host entries instead of fictional task.status
transitions).

### 6. ASCII fallback for non-UTF8 terminals (roadmap #13)

`STATUS_ICONS_ASCII` already lived in `core/icons.py` (with TC-377
unit tests) but was never reachable from the renderer; on `LANG=C`
consoles `│ ⚠ ✱ ● ◆ ✖` rendered as `?` / mojibake. Added
`is_unicode_terminal()` (returns False unless `sys.stdout.encoding`
contains "utf"), `ascii_mode: bool = False` on `format_status_bar`
and `format_host_summary`, plus a per-instance `_ascii_mode`
auto-detected in `CompactRenderer.__init__`. ASCII mode swaps
separator → `|`, warning → `!`, deprecation → `*`, status icons →
`STATUS_ICONS_ASCII`, completion glyphs → `* / X`. Threaded through
every status-bar render + the final indicator + the per-host summary.
Smoke-tested with `PYTHONIOENCODING=ascii`.

### 7. Width-aware row count + SIGWINCH self-heal (roadmap #12)

`_row_count` was newline-only — a status bar that wrapped at the
right margin counted as 1 row but rendered as 2+, so subsequent
rewinds left stale half-bars on screen. Fixed:

- `_row_count(text, width)` sums `ceil(len(line) / width)` per logical
  line. Trailing `"\n"` no longer counts (the cursor sits at start of
  the next row but nothing renders there).
- New `_terminal_width()` calls `shutil.get_terminal_size()` on every
  render. The kernel keeps TIOCGWINSZ current per SIGWINCH, so resize
  is picked up on the next `update()` / `print_log()` without an
  explicit signal handler.
- 12 unit tests for the row count math + 1 integration test pinning
  that `Display.update` records the wrapped count from the live
  terminal width (monkeypatched to 20 cols).

Approximation kept: `len()` undercounts East Asian wide chars (emoji,
CJK). Documented in the docstring; safe at every current call site
(status bar content is BMP punctuation + ASCII).

### 8. Drop -v alias for ansible passthrough (roadmap #6)

AOM's `--verbose` previously had a `-v` short alias that shadowed
ansible-playbook's own `-v` / `-vv` / `-vvv` verbosity ramp. `aom
site.yml -v` activated AOM debug instead of ansible verbosity.

Dropped the `-v` alias. `--verbose` (long form only) stays for AOM
diagnostics. Bare `-v` after the playbook now flows through REMAINDER
to ansible-playbook unchanged. Help epilog updated to document the
convention. Single test rewritten from "verbose accepts -v" to "-v
after the playbook leaves args.verbose False and lands in
ansible_args".

### Remaining roadmap

Larger / blocked: 9 (TUI end-to-end), 11 (include_tasks dynamic
expansion), 14 (session recording).

---

## 2026-05-11 — include_tasks dynamic expansion (roadmap #11)

TC-094 / TC-095 from TEST_SPECIFICATION.md, Section 5.2 in
SPECIFICATION.md. Picked because it's the most contained of the three
remaining roadmap items (#9 TUI needs cross-loop plumbing, #14 needs
the `.aom/` writer wired in; this one is pure state-machine logic).

### What landed

`RunState` now grafts dynamic `TaskDefinition` nodes onto preflight
`definitions` when a `v2_playbook_on_task_start` or `v2_runner_on_start`
event arrives for a task name that doesn't match any preflight leaf:

- New private method `RunState._graft_or_match_task(task_id, task_name)`.
  Called from both task-start handlers (linear and free strategy).
- Match algorithm: iterate every leaf `TaskDefinition` across all plays
  (unwrapping `RoleGroupDefinition` for visibility), compare by name.
  Hit → save as `_last_matched_task_def`; miss → graft as child of
  whichever node is currently saved as the parent cursor.
- Dynamic children inherit `play_id`, `play_order`, `role` from the
  parent; `task_order=-1`, `is_dynamic=True`, fresh empty `tags`.
- `_grafted_uuids: set[str]` deduplicates: a UUID arriving twice (e.g.
  `task_start` then a later `runner_on_start` for the same task) only
  grafts once.
- Orphan unknown tasks (no preflight match yet) are dropped silently —
  no spurious grafts onto an arbitrary node.

Helper `_iter_leaf_task_defs(plays)` extracted at module scope as the
pure piece. Could move to a dedicated `core/matching.py` if matching
grows more cases (path, sequential-name fallback per TC-092/TC-093);
single function in `models.py` is fine for now.

### Tests

`tests/unit/test_dynamic_expansion.py` — 8 cases, all green:
1. Single unknown task grafted as child of last matched parent (TC-095)
2. Dynamic task inherits play_id / play_order from parent
3. Multiple unknown tasks accumulate under same parent (TC-094)
4. Repeated UUID across task_start + runner_on_start doesn't duplicate
5. Static-task arrival between dynamics resets the parent cursor
6. Orphan unknown task before any match is dropped, no crash
7. Grafting works through `v2_runner_on_start` (free strategy)
8. No definitions at all → handler still safe, doesn't crash

Full suite: 1691 passed, 6 skipped (no regressions; same skip count).

### Open caveats

- Name-collision tolerance: matching is "first leaf with that name
  across all plays". Two static tasks with identical names in different
  plays would set the cursor to whichever is iterated first. Live
  ansible event order means this rarely matters in practice; if it
  bites, add play-scoping (match within current play first).
- The renderer doesn't yet *display* dynamic children differently —
  preflight summary still shows the static task count. That's fine for
  the spec ("dynamic include_tasks are not counted" — `count_total_tasks`
  already only walks the top-level `tasks` list, not `children`).

### Remaining roadmap

Larger / blocked: 9 (TUI end-to-end), 14 (session recording).

---

## 2026-05-11 (later) — Session recording wired into runner (roadmap #14)

The `SessionManager` in `core/session.py` and the `aom inspect` read
side both existed in full; the missing piece was the runner ever
*writing* anything. With this slice, every `run_playbook` invocation
produces a session directory that `aom inspect list` / `show` can
immediately replay.

### Design

`run_playbook` now takes an optional `session_dir: Path | None`
defaulting to `~/.local/state/aom/sessions/` (matching the inspect-side
default in `inspect/cli.py`). Inside, a private `_SessionSink` class
wraps a `SessionManager`:

- Constructor tries `start_session()`; OSError logs at DEBUG and
  leaves the sink in a no-op state. Recording is observability, not
  control flow — disk problems must never abort a real ansible run.
- `record_event(event)` mirrors every parsed JSONL event before it
  reaches the renderer (placed in `_feed()` between `feed_line` and
  `renderer.update_state`, so the on-disk order matches what the
  renderer actually saw).
- `record_stderr(line)` captures plaintext warnings drained from the
  parser plus the preflight error lines.
- `end(status)` writes the final `status` / `end_time` / `duration`
  into meta.json. Called on every exit path: clean exit, non-zero
  exit (`failed`), exec-missing (`crashed`), and KeyboardInterrupt
  (`crashed`).

The sink is threaded through `_drive`, `_flush_pending`, and `_feed`.
mypy caught one missed callsite (the EOF-during-expect branch in
`_drive` was passing 3 args instead of 4) — fixed before commit.

### Tests

`tests/integration/test_runner_session_recording.py`, 6 cases, all
green:
1. Run creates `events.jsonl`, `meta.json`, `stderr.log` under
   session_dir.
2. Every JSONL event seen by the renderer also lands in `events.jsonl`.
3. meta.json status = `completed` on exit 0.
4. meta.json status = `failed` on non-zero exit.
5. Unwritable `session_dir` (point it at a file): run still succeeds,
   renderer.handle_completion still fires.
6. Default state dir (`~/.local/state/aom/sessions/`) gets a session
   when no override is passed — patched `Path.home()` to a tmp_path.

Full suite: 1697 passed, 6 skipped (up from 1691; +6 = the new file).

### Quirks / open items

- The pre-existing `runner.py:95` `except A, B, C:` (tuple-expression
  except) still parses fine on 3.x but is unusual. Untouched in this
  slice.
- `mypy` still reports the pre-existing "Returning Any from str
  function" warning in models.py and the pexpect stubs-missing note in
  runner.py. Neither is new.
- `inspect/cli.py` defaults `--state-dir` to the same path the runner
  now writes to, so `aom inspect list` works end-to-end after the
  first recorded run with no extra wiring. We don't yet have a
  `--no-record` opt-out — could add if disk usage becomes a concern.
- `SessionManager.create_artifact()` is wired in core but not called
  by the runner; the inspect-side reads from the live `events.jsonl`
  directly, so the `.aom` artifact file is decorative for now.
  Promotable to a post-run consolidation step if/when the cleanup
  policy moves toward purging session dirs.

### Remaining roadmap

Larger / blocked: 9 (TUI end-to-end). That's the last one and the
hardest — AOMApp's `app.run()` event loop versus the runner's pexpect
loop need either `call_from_thread` plumbing or a model where the
runner drives Textual's loop instead of owning its own.

---

## 2026-05-11 (third pass) — TUI end-to-end wiring (roadmap #9)

The architectural collision that blocked this: `cli.py` was calling
`run_playbook(playbook, args, aom_app)`, which runs a pexpect loop
synchronously. Textual's own `app.run()` was never invoked, so the
TUI rendered nothing. The fix flips ownership: in TUI mode, Textual
drives, and pexpect runs in a Textual worker.

### What landed

`AOMApp` now accepts `playbook`, `ansible_args`, and an optional
`session_dir` in its constructor; the no-arg form keeps working so
the protocol smoke tests (and the pre-existing
`tests/compact/test_password.py::TestTUIModePasswordModal` suite)
don't break. The app owns a `RunState` and exposes read-only
properties for every piece of state widgets need:

- `run_state` (mutated by `update_state` → `state.handle_event`)
- `exit_code`, `final_state` (set by `handle_completion`)
- `warnings_count`, `deprecations_count`, `log_lines`

`on_mount()` pushes `MainScreen` and — when constructed with a
playbook — kicks off `run_worker(self._run_playbook_worker,
thread=True, exclusive=True)`. The worker calls `run_playbook(self...
self)`, which drives the existing pexpect loop and hits the
Renderer-Protocol callbacks on `self`. Mutations to plain Python
state (`_run_state`, counters, log lines) are intentionally direct;
any visible widget refresh that depends on them is the widget's
responsibility to schedule via `call_from_thread`.

Two behavioural changes worth noting:

1. **`stop()` is now a no-op.** The legacy `self.exit()` here tore
   the UI down the instant the runner returned, leaving the user
   staring at a blank terminal. Now Textual's loop keeps spinning;
   the user quits with `q` (which is already wired via
   `action_quit`).
2. **`handle_completion` only records state.** It never exits the
   app, for the same reason.

### CLI wiring

`cli.py` now branches on `args.tui` before touching renderers:

- `_run_compact(playbook, args)` — the old synchronous path,
  unchanged in behaviour.
- `_run_tui(playbook, args)` — constructs `AOMApp(playbook=...,
  ansible_args=...)` and calls `app.run()`. After the loop returns
  (user quit, or completion + manual q), `app.exit_code` becomes the
  process exit code; `None` (user quit mid-run) → 1.

The KeyboardInterrupt + generic-Exception guards from the old code
are still there, just split across the two helpers.

### Tests

`tests/tui/test_app_end_to_end.py` (9 cases):
1. Construction with playbook+args (and the no-arg default still
   works).
2. `start()` resets a fresh `RunState`.
3. `update_state` mutates `run_state.plays`.
4. `handle_completion` stores `exit_code` + `final_state`.
5. `set_definitions` lands on `run_state.definitions`.
6. `add_warning` bumps the right counter (warning vs deprecation).
7. `print_log` appends to `log_lines` in order.
8. **Pilot-driven worker test:** `app.run_test()` actually mounts
   the app, patches `run_playbook` to a recording stub, and asserts
   the worker fires with `renderer is app`, the right playbook
   path, args, and `session_dir`, and that completion lands.

`tests/unit/test_cli_tui_launch.py` (4 cases):
1. `aom --tui site.yml` calls `app.run()`, never the legacy
   `run_playbook`.
2. `app.exit_code` propagates as the process exit code.
3. `exit_code=None` (user quit) → cli returns 1.
4. Compact mode still calls `run_playbook` + `create_renderer` —
   no regression.

Full suite: 1710 passed, 6 skipped (up from 1697 — exactly the 13
new tests).

### Open caveats

- Widgets don't yet **react** to state mutations. The plumbing is
  there (state is owned by the app, the worker can mutate it
  safely), but `MainScreen.update_from_state()` is only called from
  the existing inert paths. A follow-up should wire reactive
  attributes or periodic refreshes via `app.set_interval(...)` so
  the panels actually update during a run. That's UI work, not loop
  architecture, so it can land as its own slice once someone runs
  the TUI for real and decides what should pulse.
- `handle_password_prompt` still uses `with self.suspend(): getpass...`
  — that's the same surface
  `tests/compact/test_password.py::TestTUIModePasswordModal` covers,
  and it works correctly from the worker thread because `suspend()`
  is already designed to be reentrant from foreign threads.
- The `runner.py:95` tuple-expression `except` still parses fine
  but reads unusually. Untouched.

### Roadmap complete

All 14 items shipped. The remaining `.sisyphus/notepads/` items
(TC-094/095/096 dynamic-task ordering tests, session-recording
cleanup policy review) are tidy-up work, not blocking features.

## 2026-05 Host Status Display Overhaul

### Skipped status added to host overview

`format_host_rows`, `format_host_summary`, and `_format_count_cells` now
include a `skipped` parameter. The host table shows a conditional `skipped`
column (hidden when no host has skipped tasks, mirroring `unreachable`).

### Per-host summary lines removed from completion

The `_format_per_host_lines` method was removed. On completion, the
column-aligned host table (`format_host_rows`) now always prints (both
success and failure). The per-host summary lines (`hostname: ● N ok ◆ M
changed ○ K skipped`) were pure duplication with the host table.

On failure/cancel: tree + host table + status bar + failure recap.
On success: host table + status bar (no tree — stale running spinners
would be misleading).

### Linear strategy completion marking

Under linear strategy, `v2_playbook_on_task_start` now marks any
previously-running task in the same play as COMPLETED. This prevents
stale "running" entries from lingering until `v2_playbook_on_stats`.

### All hosts appear as tree leaves

Under a running task, ALL hosts now appear as leaves (not just RUNNING).
Completed hosts show ● (OK), skipped hosts show ○, etc. Only
RUNNING hosts were shown before, which meant completed hosts vanished
from the tree mid-playbook.

### Role task count augmentation + prefix extraction

`_emit_runtime_play` now counts runtime tasks per role that weren't in
preflight (include_role tasks). `_task_role` extracts role from
`"role : task"` prefix when the role name is in `_known_roles` (built
from both preflight definitions and runtime task names). This makes
dynamic roles like `podman` show correct "(N tasks)" counts.

## 2026-05-23 — Tree rendering fix pass (branch: feat/nom-compact-renderer)

Four tree rendering bugs found in interactive multi-play smoke testing.
All four interact: a play's host leaves vanish when the next play starts,
stale `□ pending` tasks from a completed play linger in the tree, the
elapsed timer for fallback host leaves is stuck at `0s`, and hosts like
`localhost` show up in playbooks they were never targeted by.

### 1. Host leaves missing during execution (tree budget starvation)

On a 24-row terminal with 17 hosts, the tree panel needed 20+ lines
(one per host leaf + task header + role header) but the budget formula
gave it only 17. Host leaves were truncated from the bottom.

**Fix**: Raised `_compute_tree_budget` cap from 40 to 60
(`src/ansible_aom/compact/format.py:320`). Formula is now
`max(8, min(60, rows // 2 + active_hosts // 3))`. The 40 cap was
arbitrary — 60 covers up to ~35 host leaves on a standard 24-row
terminal without excessive budget waste.

### 2. Stale `□ pending` tasks from completed plays

When play 1 completed and play 2 started running, `_play_running_and_pending`
in `_emit_runtime_play` only searched the *current* play's runtime tasks.
If play 1 had handler tasks (like `meta: flush_handlers`) whose
`runtime.tasks` lived under play 1's UUID, they showed as `□ pending`
forever because the search never crossed play boundaries.

**Fix**: Extended the running/pending scan to search across *all* plays.
Also added cross-play completion marking: when a handler task in a
different play UUID is found running, the linear-completion loop in
`PlayRunState._mark_completed()` now iterates `self.plays.values()` not
just the current play's tasks.

Completed plays are skipped from tree rendering when another play has
running items — a play with zero running items and another play actively
running gets pruned. This uses running-item detection rather than
terminal state: handler plays with no local tasks but running items in
other plays stay visible.

### 3. Elapsed time stuck at 0s for fallback host leaves

When `runtime.hosts` was empty (first task in a new play, or a handler
with no per-host events yet), the fallback path created host leaves with
`Status.RUNNING` and `elapsed_s=0.0`. The elapsed counter never advanced
from zero.

**Fix**: Compute elapsed from the task's `runtime.start_time` instead of
hardcoding 0. When `runtime.start_time` is None (pre-start) it still
falls back to 0, which is correct — the task hasn't started yet.

### 4. All hosts appearing in every play (hostname fallback scope)

The fallback function `_all_known_hostnames` collected hostnames from
every task in every play. On a multi-play playbook where play 1 targets
`[web1, web2, web3]` and play 2 targets `[db1]`, play 2 would show
leaves for `web1`, `web2`, and `web3` (and `localhost` from test
playbooks) because the fallback had no play scoping.

**Fix**: Replaced `_all_known_hostnames` with `_play_target_hostnames`
that takes a `PlayDefinition` parameter and uses `play_def.resolved_hosts`
from preflight when available. When preflight data is absent, it falls
back to hostnames from the play's own runtime tasks only. The call site
in `_emit_runtime_play` already has both `play` (PlayRunState) and
`play_def` (PlayDefinition) in scope, so no plumbing changes needed.

### Test impact

Suite: 2189 passed, 1 known-failure, 1 deselected. The known failure
(`test_render_includes_stderr_tail_on_failure`) is a pre-existing
integration test that depends on ansible-core being installed.

### Commits (unpushed — git.eisen5.eu:2222 unreachable)

```
9d9e2e7 feat(tree): show host leaves during execution, higher budget cap
a2c79e2 fix(tree): cross-play runtime_by_name + completed-play skip
c722bcd fix(tree): cross-play linear completion, remove runtime.tasks guard
00db4bb fix(core): skip completed plays, use _all_known_hostnames fallback
63051d5 fix(tree): filter stale task items (□ pending) from completed plays
f932bee fix(tree): scope hostname fallback to play targets, fix elapsed time
72eba82 fix(core): scope hostname fallback to play targets, fix elapsed time
```

### Still open

- Push blocked: remote `git.eisen5.eu:2222` connection refused
- Fallback host leaves still default to `Status.RUNNING` — when a task
  finishes but `runtime.hosts` is empty, the fallback shows spinners
  instead of the final status. Root cause: ansible doesn't emit
  `v2_runner_on_ok` for implicit tasks like `meta: flush_handlers`.

## 2026-05-23 — Linear Force-Completion Fix

### What Changed
- Added a third completion branch in `_handle_v2_playbook_on_task_start` for
  tasks that still have RUNNING hosts when a new task starts in the same play
  under linear strategy.
- Strategy detection corrected: `v2_runner_on_start` now flips strategy from
  `"linear"` to `"free"` because the JSONL callback only emits that event
  when NOT in lockstep mode (`if self._is_lockstep: return`).

### Key Design Decisions
1. **Same-play only**: Force-completion is scoped to `p.play_id == play.play_id`.
   Cross-play completion was wrong — ansible can start play 2 while play 1 is
   still running.
2. **Preserve real terminal events**: Only `Status.RUNNING` hosts get force-
   transitioned to `Status.OK`. Hosts that received `v2_runner_on_failed` etc.
   keep their actual status.
3. **Strategy flip on runner_on_start**: The earlier `task_start`→linear detection
   is premature. If `runner_on_start` ever fires, the playbook is NOT in lockstep
   mode. The code now flips `detected_strategy` to `"free"` in this case.

### Files Modified
- `src/ansible_aom/core/models.py`: +2 changes
  1. New `elif p.play_id == play.play_id:` branch in linear completion loop
  2. Strategy flip in `_handle_v2_runner_on_start`
- `tests/unit/test_models.py`: +4 test methods in new `TestLinearForceCompletion`
- `tests/unit/test_event_processing.py`: Updated TC-203 test assertion

### Test Results
- 2255 tests pass, 1 pre-existing failure (test_render_includes_stderr_tail_on_failure)
- ruff clean on all modified files

## 2026-05-24 — Cross-Play Leakage, Tree Flicker, Stuck Meta Tasks, Upcoming Plays

Five tree rendering bugs fixed in interactive multi-play smoke testing.
These followed on from the May 23 fixes — all four interact and required
careful ordering to avoid regressing each other.

### 1. Cross-play task leakage (◐ zombies)

**Bug**: Completed plays showed `◐` (running) tasks borrowed from later
plays via `_play_running_and_pending` when the cross-play scan found
running items in a *different* play. A completed play's tree showed
`◐` tasks from the currently-running play.

**Root cause**: The cross-play scan in `_play_running_and_pending`
searched `runtime_by_name` across *all* plays. It didn't filter out
completed plays' own tasks — it found running tasks in other plays and
reported them as belonging to the completed play.

**Fix** (`dab145a`): In `_play_running_and_pending`, completed plays now
only emit their own completed tasks. Running tasks from other plays
are not attributed to a completed play's tree. This uses a new
`include_cross_play=False` parameter that only completed plays use;
active plays still use `True` to show borrowed tasks.

**Key design decision**: The cross-play scan is still needed for active
plays to show pending/running state from handler tasks in other plays.
The fix scopes it to only run for non-completed plays.

### 2. Tree flicker between completed and current plays

**Bug**: When one play ended and the next started, the tree panel
flickered between showing the completed play and the current play on
alternate frames. This was especially visible during the gap between
play completion events — `v2_playbook_on_play_start` for play 2 hadn't
arrived yet, but play 1 was already marked complete.

**Root cause**: The tree play selection logic alternated between
"the last play with running items" and "the last play in the list"
when no play had explicitly running items. The decision bounced
between plays on each render frame.

**Fix** (`f179469`): Introduced `_last_running_play_id` — a sticky
fallback that remembers the most recently active play. The selection
tiers are now:
1. Fresh running play (active play with `any_running == True`)
2. Previous frame's sticky play (`_last_running_play_id`)
3. Last play with tasks (cold-start fallback)

This prevents oscillation because tier 2 persists the choice across
frames until a new play actually starts running.

**Tests**: 4 new test methods in `TestStickyFallback`:
- `test_sticky_fallback_fresh_running_play` — active play wins
- `test_sticky_fallback_remembers_previous` — sticky persists
- `test_sticky_fallback_no_previous` — cold-start fallback
- `test_sticky_fallback_transitions_to_new` — new play overrides sticky

### 3. Stuck meta tasks under linear strategy (◐ 949s)

**Bug**: Under linear strategy, `meta: reset_connection` tasks showed
`◐` forever with elapsed time like `0:15:49` (949 seconds = 15 min).
The task completed almost instantly but never got force-completed
because it had zero hosts (meta tasks don't run on hosts).

**Root cause**: The linear completion branch in `_handle_v2_playbook_on_task_start`
had two guard conditions: (a) all hosts terminal OR (b) empty hosts.
But the empty-hosts branch only ran when `p.play_id == play.play_id` —
and the outer loop iterated `self.plays.values()` which included
*other* plays. When meta tasks belonged to play 1 but the outer loop
was checking play 2, the force-completion was skipped.

**Fix** (`d981444`): Added a third completion branch in the linear
strategy force-completion loop:
```python
elif p.play_id == play.play_id:
    # Same play — force-complete RUNNING hosts on this new task start
    for host_state in p.hosts.values():
        if host_state.status == Status.RUNNING:
            host_state.status = Status.OK
```
This scopes force-completion to the same play, preventing cross-play
host stealing. Hosts with real terminal events (`FAILED`, `UNREACHABLE`)
keep their actual status — only `RUNNING` gets force-transitioned.

### 4. Upcoming plays invisible

**Bug**: Plays that hadn't started yet (zero `runtime.tasks`) were
silently omitted from the tree. On a 3-play playbook, the tree only
showed play 1 until play 2 started.

**Root cause**: The sticky fallback (`_last_running_play_id`) and the
skip-completed-plays logic had a joint guard: `and runtime.tasks`.
When a play had no runtime tasks yet (upcoming play), this guard
treated it like a completed play and skipped it.

**Fix** (`cd68065`): Changed the skip guard from `runtime.tasks` (empty
for upcoming plays too) to `is not None` — upcoming plays have no
runtime tasks yet but should still appear. Only completed plays with
zero running items and nonzero runtime tasks get skipped. The guard
now reads: skip if play is not active AND has runtime tasks AND no
running items in any play.

**Key insight**: The original `runtime.tasks` check was meant to skip
completed plays that had no tasks (like handler-only plays). But it
was accidentally too broad — it also skipped upcoming plays.

### 5. Strategy detection corrected

**Bug**: The strategy detection in `_handle_v2_playbook_on_task_start`
could never detect "free" strategy. The JSONL callback only emits
`v2_runner_on_start` when `self._is_lockstep` is False (i.e., when
NOT in linear mode). So whenever this event fires, the strategy is
NOT linear.

**Fix** (`d981444`): In `_handle_v2_runner_on_start`, added:
```python
if self.detected_strategy == "linear":
    self.detected_strategy = "free"
```
This flips the detected strategy from the default ("linear") to
"free" on the first runner_on_start event.

### Test Impact

- Suite: 2255 passed, 1 known-failure (test_render_includes_stderr_tail_on_failure)
- +52 new tests across all include/import/role features (incremental since May 23)

### Commits (still unpushed — git.eisen5.eu:2222 unreachable)

```
dab145a fix(tree): prevent cross-play task leakage in tree rendering
f179469 fix(tree): implement sticky fallback to prevent tree flicker
d981444 fix(core): force-complete stuck hosts under linear strategy
cd68065 fix(tree): don't skip upcoming plays in sticky fallback
```

### Still open

- Push blocked: remote `git.eisen5.eu:2222` connection refused
  (11 commits unpushed total — 7 from May 23 + 4 from May 24)
- Fallback host leaves still default to `Status.RUNNING` — when a task
  finishes but `runtime.hosts` is empty, the fallback shows spinners
  instead of the final status. Root cause: ansible doesn't emit
  `v2_runner_on_ok` for implicit tasks like `meta: flush_handlers`.
  Partially mitigated: the sticky fallback keeps the last active play
  visible instead of bouncing to the completed play, so this issue
  only manifests during brief transition windows.

## 2026-05-24 Tree projection same-name task identity

- `_play_running_and_pending()` now builds per-name runtime candidate lists and
  consumes unmatched runtime task executions by `task_id` / stable runtime
  identity instead of reusing the first matching display name.
- Same-name preflight task definitions now project as distinct visible rows in
  execution order when their runtime events arrive with different ids.
- Dynamic child matching uses the same unmatched-candidate selection so a
  runtime task is not reused for a later child line after it has already been
  projected once.

## 2026-05-24 Tree projection typecheck cleanup

- The `ordered_plays` loop in `tree.py` needed a variable rename to avoid
  reusing `play_def` with a broader `PlayDefinition | None` type in the same
  scope.
- `mypy src/ansible_aom/core/tree.py` still reports a pre-existing
  `no-any-return` issue in `src/ansible_aom/core/models.py`, but the local
  tree-module type error from the identity change is gone.


## 2026-05-24 Tree Flicker Regression Harness Search

### Existing reusable patterns
- `tests/compact/test_tree_projection_lifecycle.py` already proves projection instance continuity across frames with `MagicMock`, `_renderer()`, `_seed_sticky_gap_state()`, and `tree_lines(20)` assertions.
- `tests/unit/test_tree_projection.py` has pure-data `TreeProjection.from_run_state(...)` coverage plus deterministic repeated-call checks (`bounded == again`) that can be reused for replayed frame assertions.
- `tests/compact/test_golden_frames.py` and `tests/integration/test_replay_determinism.py` already provide replay / golden scaffolding that can be extended to capture per-frame output, not just final-state output.

### Blind spots
- Current coverage mostly checks final frames or two-frame sticky cases; no existing test asserts row identity churn across a longer replay sequence.
- No fixture today captures a hostile frame sequence specifically for tree flicker; likely need a new replay JSONL fixture plus per-event frame snapshots.

## 2026-05-24 Ancestry-aware child matching

- `TreeProjection._play_running_and_pending()` now walks preflight tasks recursively and
  prefers runtime candidates whose host set overlaps the current ancestor branch before
  falling back to flat arrival order.
- That keeps repeated child labels under different include/import parents attached to the
  correct branch instead of swapping host leaves when runtime arrivals interleave.
- Caveat: if two same-name branches expose identical host sets, the projection still falls
  back to the existing arrival-order tie-break; add a stronger runtime ancestry signal if a
  future repro needs it.

## 2026-05-24 Shared recursive preflight traversal

- Added a shared `iter_preflight_task_defs()` helper in `core/models.py` and
  pointed `core/tree.py` at it so grouped roles and nested children are walked
  in one pre-order path for role indexing, task counting, and tree emission.
- `count_leaf_tasks()` still uses the dedicated leaf-tree walk; the shared
  iterator is for the projection/indexing path, not for counting duplicates.

## 2026-05-24 Runtime role prefix guard

- Runtime tree emission now treats ``role : task`` prefixes as roles only
  when the prefix has no whitespace, so literal task names like ``Install
  foo : bar`` stay ungrouped while include_role-style ``podman : ...`` and
  ``nginx : ...`` tasks still group and count correctly.

## 2026-05-24 Phase 2 durable projection / row leases

- Added a private ``RunState._tree_revision`` counter that bumps when
  definitions are reassigned or dynamic tasks are grafted. ``TreeProjection``
  now watches that revision and refreshes its role memo in place instead of
  being recreated.
- ``CompactRenderer`` no longer invalidates ``_projection`` on task/host start
  events; the same projection instance now survives successive events and
  quiet gaps while the core projection refreshes itself lazily.
- Added short-lived internal row leases in ``core/tree.py`` so the sticky play
  anchor and row continuity metadata age out intentionally instead of living
  forever as a side effect of caching.
- Lease bookkeeping is time-bounded (UTC timestamps) and pruned during
  projection passes, which keeps the continuity state small while still
  preserving gap stability.
- Targeted verification: ``uv run pytest tests/unit/test_tree_projection.py
  tests/compact/test_tree_projection_lifecycle.py
  tests/integration/test_replay_determinism.py -q`` → passed.

## 2026-05-24 Play-boundary borrowing tightening

- `TreeProjection._play_running_and_pending()` now only classifies tasks
  owned by the current play; generic same-name cross-play borrowing was
  removed so hostile transition windows do not leak rows across play
  boundaries.
- `include_cross_play` remains as a compatibility knob for existing call
  sites, but explicit ownership still needs to be modeled before any
  borrowing can return safely.
- Added regression coverage that keeps a play's own RUNNING task visible
  while a same-name task in another play stays pending instead of being
  borrowed.

## 2026-05-24 Async launcher / async-status path disambiguation

- `RunState._graft_or_match_task()` now prefers `task.path` over bare
  task name when both are available. That keeps an async launcher row
  and a later async-status row from stealing the same parent cursor when
  they share a display name.
- The runtime JSONL `task.path` field is the right discriminator for
  these real-world async shapes because the launcher and poller live at
  different file:line coordinates in the playbook, even when the visible
  labels are identical.
- Targeted verification passed:
  `uv run pytest tests/unit/test_run_state_index.py tests/unit/test_tree_projection.py tests/unit/test_dynamic_expansion.py -q`.

## 2026-05-25 run_once / serial window normalization

- `PlayRunState` now records `window_start` from `play.duration.start` and
  an ordinal fallback for repeated play-start windows.
- `v2_playbook_on_play_start` now creates a fresh play window, so repeated
  `run_once` batches don't inherit prior task-host state.
- Tree projection scopes runtime task leases by the play-window identity,
  which keeps the same logical task row from being reused across serial
  batches.


## 2026-05-25 Compact noisy-output QA
- Targeted compact renderer regression tests passed: 117/117 in `tests/compact/test_render_dirty_flag.py`, `tests/compact/test_display_ansi.py`, `tests/compact/test_renderer_stats.py`, `tests/integration/test_compact_renderer.py`, `tests/unit/test_renderer_stats_parity.py`.
- Ordinary compact smoke passed on `.sisyphus/test-fixtures/simple.yml` after installing missing `ansible.posix` collection in the local uv environment.
- Noisy-output smoke passed with a synthetic local playbook emitting sustained stdout (`/tmp/opencode/aom-noisy-smoke/noisy_slow.yml`); compact renderer completed with final host/task summary and no obvious freeze.
- Initial smoke failure was environment-related (`ansible.posix.jsonl` missing), not a renderer regression.

## 2026-05-25 Tree gap-state anchor expiry

- Root cause: `TreeProjection.tree_lines()` dropped `active_play_id` to `None` once the play lease expired and no fresh running play was found, which let the next quiet frame widen back out to every completed play.
- Fix: keep the last running play pinned by its internal runtime identity even after the lease ages out; leases still expire for continuity metadata, but they no longer control play selection.
- Added regressions for both the lease-expiry gap and the hostless meta-task gap so earlier completed plays stay hidden while the current play remains anchored.

## 2026-05-25 Failed loop inspect fixture restore

- Restored `tests/fixtures/sessions/019e4520-fa64-7000-a627-000000000002/stderr.log`
  with the documented brew-cask tail so the failed-loop inspect golden test can
  render the stderr header and curl 404 line again.

## 2026-05-25 TUI replay mypy cleanup

- Cleared the last `uv run mypy src/ansible_aom` blockers in the TUI/replay
  path with typing-only changes: explicit tree-node narrowing for
  `set_label()`, a real `str | None` pane-id return, and a dynamic completer
  assignment via `setattr()`.

## 2026-05-25 Tree sticky fallback cleanup

- Removed the bare play-header fallback from `TreeProjection.tree_lines()` so a
  play only stays visible while it still has running/pending surface.
- Updated sticky regressions to expect completed plays to disappear on quiet
  frames, while active plays still render normally while work remains.

## 2026-06-21 Task: mitogen-models-fix

### Problem
ansible.posix.jsonl emits events with non-canonical `task`/`hosts` shapes when mitogen drops the SSH link mid-task. Three shapes crashed `RunState`:
1. `task` as bare UUID string → `.get()` on `str` raises `AttributeError`
2. `task` as `None` → `.get()` on `NoneType` raises `AttributeError`
3. `hosts` as list → `.items()` on `list` or `for hostname in list` materialises bogus host entries

### Helpers Added
- `RunState._task_dict(event) -> dict[str, Any]` — returns `event["task"]` if it's a `dict`, else `{}`. Mirrors the `isinstance(play_data, dict)` guard in `_resolve_play_id` (line 458).
- `RunState._hosts_dict(event) -> dict[str, Any]` — returns `event["hosts"]` if it's a `dict`, else `{}`. Prevents `.items()` crash on list-shaped hosts and prevents string-iteration in the skipped handler.

### Handlers Patched
All 7 handlers that accessed `task` or `hosts` from event payloads:
1. `_handle_v2_playbook_on_task_start` — `task_data = self._task_dict(event)`
2. `_handle_v2_runner_on_start` — `task_data = self._task_dict(event)`
3. `_handle_v2_runner_item_on` — `task_data = self._task_dict(event)` + `for hostname in self._hosts_dict(event)`
4. `_handle_v2_runner_on_ok` — `task_data = self._task_dict(event)` + `hosts_data = self._hosts_dict(event)`
5. `_handle_v2_runner_on_failed` — `task_data = self._task_dict(event)` + `hosts_data = self._hosts_dict(event)`
6. `_handle_v2_runner_on_skipped` — `task_data = self._task_dict(event)` + `hosts_data = self._hosts_dict(event)`
7. `_handle_v2_runner_on_unreachable` — `task_data = self._task_dict(event)` + `hosts_data = self._hosts_dict(event)`

### Behavioural Contract
- Malformed events silently drop (no state change, no exception).
- Pre-existing RUNNING hosts remain RUNNING (TC-MITOGEN-1..6).
- Subsequent well-formed events still mutate state correctly (TC-MITOGEN-7).
- Malformed payloads of the runner_on_* family are NOT counted as unknown (the event type is known; only the payload is malformed).

### Key Pattern
The project already had `isinstance(play_data, dict)` in `_resolve_play_id` (line 458) for the same defensive pattern on the `play` field. The `_task_dict` and `_hosts_dict` helpers follow this same idiom but extract it into reusable private methods.

## 2026-06-21 Task: mitogen-renderer-fix

### Helpers added to `CompactRenderer` (mirroring `core/models.py`)

- `_task_dict(event) -> dict`: Returns `event["task"]` if it's a dict, else `{}`. Defensive against mitogen-distorted `task: "uuid-string"` or `task: None`.
- `_hosts_dict(event) -> dict`: Returns `event["hosts"]` if it's a dict, else synthesises `{host: {}}` from the singular `host` key, else `{}`. Defensive against mitogen-distorted `hosts: ["host1", "host2"]`.

### Call sites patched (14 total)

**`_emit_event_log`**: 6 `_task_dict` replacements (task_start, runner_start, runner_on_ok, runner_on_failed, item_on_*), 5 `_hosts_dict` replacements (runner_on_ok, runner_on_failed, runner_on_unreachable, runner_on_skipped, item_on_*).

**`_inline_duration_suffix`**: 1 `_task_dict` replacement for `task_id` lookup.

**`_bump_task_counters`**: 2 `_task_dict` replacements (task_id lookup, path lookup).

**`_start_running_task`**: 1 `_task_dict` replacement (task dict extraction).

### Key insight: `host` singular fallback

TC-MITOGEN-106 revealed that `_hosts_dict` must also handle the case where `hosts` is absent but `host` (singular) is present. Mitogen events sometimes carry `host: "foreman"` instead of `hosts: {"foreman": {}}`. Without this fallback, the renderer silently skips the event entirely, producing no log output for otherwise well-formed events. The fix synthesises `{hostname: {}}` from the singular key so the normal iteration path still works.

### Test results
- `tests/compact/test_mitogen_robustness.py`: 8/8 pass (TC-MITOGEN-100..107)
- `tests/compact/`: 367 pass, 0 fail
- `tests/`: 2727 pass, 6 skip, 1 xfail, 0 fail
- mypy: clean

## Play-boundary state-machine bugs (June 2026)

### Two bugs in `_handle_v2_playbook_on_play_start` (`src/ansible_aom/core/models.py:414`)

**Bug 1 — Cross-play graft cursor leak.** `_last_matched_task_def` (declared at line 276) was set whenever a runtime task matched a preflight TaskDefinition but never reset on play boundaries. Result: an unknown task arriving after a new play's `play_start` but before its first matched `task_start` got grafted as a child of the PRIOR play's last preflight task, polluting the prior play's definition's `children` list.

**Bug 2 — Force-finalisation under strategy: free.** The unconditional `_finalize_play` loop (lines 428-433) marked all RUNNING hosts/tasks of prior plays as OK/COMPLETED whenever the next play started. Under `strategy: free` (ansible-core 2.16+), the next play's `play_start` can arrive while prior-play hosts are still running. This produced a stale "all green" tree — the user's reported "task/host list not accurate" symptom.

### Fix

Both fixed in the same function:
- Added `if prior.detected_strategy == "free": continue` inside the finalisation loop.
- Added `self._last_matched_task_def = None` immediately after the loop, guarded by a comment explaining the cross-play graft invariant.

### Regression tests added

`tests/unit/test_play_boundary_state.py`: TC-BOUNDARY-4 (cross-play graft guard), TC-BOUNDARY-5 (free-strategy not auto-finalised), TC-BOUNDARY-6 (linear-strategy still finalised — guards against over-correction).

### Verification

- Both reproductions pass post-fix.
- `git stash` of the fix confirms the new tests FAIL on the buggy code.
- Full suite: 2148 passed (was 2145; +3 new tests).
- mypy: clean.
- ruff check: my files clean. Pre-existing ruff errors in `tree.py` (F841) and `tui/screens/inspect.py` (E501) are NOT in scope.

### Lesson

The `_last_matched_task_def` cursor is the same pattern as a stack-pointer in a recursive-descent parser: it must be pushed/popped on every grammar boundary. Play boundaries are the natural pop point — anything else is a bug.

## Session: Split RunState out of models.py

**Goal**: Move `RunState` + its private helpers (`_parse_timestamp`, `_parse_play_window_start`, `_iter_leaf_task_defs`, `_leaves_of_role_group`, `count_leaf_tasks`) from `core/models.py` (1110 lines) into a new `core/run_state.py`. Keep `models.py` re-exporting them for the migration phase. Update every consumer's import.

### What landed

- New module: `src/ansible_aom/core/run_state.py` (~890 lines) — owns `RunState`, the preflight flatteners, timestamp/window parsers, and the lazy `from ansible_aom.core.includes import discover_include_with_runtime_path` inside the two task-start handlers.
- `models.py` shrunk from 1110 → 297 lines. Still owns the dataclasses that `RunState` references (`HostRunState`, `TaskRunState`, `PlayRunState`, `TaskDefinition`, `PlayDefinition`, `RoleGroupDefinition`, `IncludeCacheEntry`, `RoleCacheEntry`) and the leaf-finder helper `_iter_task_def_tree`.
- Source imports updated in 14 files (tree, includes, parity, exit_code, replay, compact/format, compact/renderer, tui/app, tui/screens/main, tui/widgets/task_tree, formats/json, ansible/runner).
- Test imports updated in 14 files (compact, integration, tui, unit) — used `ast` parsing to rewrite `ImportFrom` nodes targeting `ansible_aom.core.models`, splitting out `RunState`/`count_leaf_tasks`/`_parse_timestamp` into a new import from `ansible_aom.core.run_state`.

### The circular-import trap and how I solved it

`run_state.py` needs the dataclasses from `models.py` (`HostRunState`, `PlayRunState`, etc.) to type `RunState`'s fields. `models.py` needs to re-export `RunState` for backward compat. That's a cycle.

Three solutions I considered:

1. **Bottom-of-file re-export**: place `from ansible_aom.core.run_state import RunState` at the end of `models.py`. Works only when `models.py` is imported first. Fails with `ImportError: cannot import name 'RunState' from partially initialized module` if anything imports `run_state` directly (which tests do).

2. **`TYPE_CHECKING` block**: doesn't work because `RunState` uses `field(default_factory=...)` calls referencing real types at class-definition time, not just annotations.

3. **Module-level `__getattr__` + frozenset allowlist**: `models.py` declares `__getattr__(name)` which lazily imports `ansible_aom.core.run_state` only when one of the legacy names is accessed. `__dir__` is overridden so `from … import *` works. This breaks the cycle because the import only happens on first access (after both modules have fully loaded).

I picked option 3 — it works regardless of import order and is the standard Python pattern for backward-compat re-exports across a circular split.

```python
_LEGACY_RUN_STATE_EXPORTS = frozenset({"RunState", "_iter_leaf_task_defs", "count_leaf_tasks"})

def __getattr__(name: str) -> Any:
    if name in _LEGACY_RUN_STATE_EXPORTS:
        from ansible_aom.core import run_state
        value = getattr(run_state, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
```

### Tooling lesson: ast-based refactor over regex

First attempt used a regex over `^from ansible_aom.core.models import …` lines. It broke multi-line paren imports because the script tried to keep parsing "the next line" from a list it had already partially consumed, producing garbled output. Restored from git, rewrote with `ast.parse` + `node.lineno`/`node.end_lineno` to compute exact source spans, then rebuilt the lines. The ast approach correctly handled both single-line and paren-wrapped multi-line imports in one pass.

Key insight: for refactors that touch every import statement, use `ast` to identify ImportFrom nodes and rewrite by line range, never by string substitution.

### Verification

- `uv run ruff check src/ansible_aom/ tests/` — All checks passed.
- `uv run mypy src/ansible_aom` — Success: no issues found in 73 source files.
- `uv run pytest tests/ -q` — 2765 passed, 6 skipped, 1 xfailed (expected).
- `lsp_diagnostics` on `models.py` and `run_state.py` — clean.

### Migration phase notes

The lazy re-export in `models.py` lets the rest of the codebase migrate file-by-file without breaking. Once every caller imports directly from `run_state`, the `__getattr__` shim can be deleted in a follow-up cleanup. Mark it with a TODO so a future session knows the shim is removable when `grep -rn 'from ansible_aom.core.models import.*RunState' src/ tests/` returns nothing.


## Session: Split tree.py into tree_projection.py

**Goal**: Move `TreeProjection` + helpers out of `core/tree.py` (2048 lines) into a new `core/tree_projection.py`. Keep `core/tree.py` as a thin re-export shim so the 24 existing import sites keep working without edits.

### What landed

- New module: `src/ansible_aom/core/tree_projection.py` (2048 lines, verbatim copy of the old `tree.py`).
- `tree.py` is now a 64-line re-export shim that pulls every public and private symbol through `from ansible_aom.core.tree_projection import (...)` and re-exports them via `__all__`. Identity check: `tree.TreeProjection is tree_projection.TreeProjection` — same class object, so `isinstance` checks, `__class__` introspection, and subclass relations are all preserved.
- Zero behavior change. Zero test changes. Zero consumer import changes.

### Why a direct re-export (no `__getattr__`) instead of the lazy trick

The RunState split used `__getattr__` + frozenset allowlist because `run_state.py` and `models.py` form a circular dependency (`run_state` imports dataclasses from `models`, `models` re-exports `RunState`). That cycle can only be broken by deferring the re-export until first attribute access.

`tree_projection.py` has no such cycle: it imports from `models` and `run_state` only, both of which are leaf modules. `tree.py` can do a plain top-level `from ansible_aom.core.tree_projection import (...)` and Python resolves it eagerly at module-load time without ever needing lazy attribute lookup. Direct re-export is simpler, more discoverable (`dir(tree)` lists every symbol), and easier for type checkers and IDEs to follow.

Rule of thumb: reach for `__getattr__` only when the import graph has a cycle. If a cycle doesn't exist, prefer direct re-export.

### Migration phase notes

Same as the RunState split: the shim lets the rest of the codebase migrate file-by-file without breaking. Delete `tree.py` once the grep recipe in its docstring returns zero matches.

### Verification

- `uv run ruff format src/ tests/` — 239 files left unchanged.
- `uv run ruff check src/ tests/` — All checks passed. Note: ruff's import-sorter put `_ROW_LEASE_LIMIT`/`_ROW_LEASE_TTL`/`_TEMPLATE_RE` (uppercase-with-underscore) BEFORE `HostRow` (mixed-case) in the import block, even though they appear alphabetically after `TreeProjection`. That's ruff's case-insensitive sort (uppercase < lowercase in ASCII), not a bug. `__all__` keeps the canonical public ordering for `dir()` and `from … import *`.
- `uv run mypy src/ansible_aom` — Success: no issues found in 74 source files (was 73; tree_projection.py added one).
- `uv run pytest tests/ -q -x` — 2765 passed, 6 skipped, 1 xfailed. Identical to the pre-split baseline.
- `lsp_diagnostics` on `tree.py` and `tree_projection.py` — clean.

### Tooling lesson: raw string for shim docstrings

First draft of the shim docstring contained `ansible_aom\.core\.tree\b` inside a triple-quoted string. Python 3.12+ flags `\.` inside a regular (non-raw) triple-quoted string as an invalid escape sequence (`SyntaxWarning`), which CI linting upgrades to an error. Switched to `r"""..."""` to silence it. Rule of thumb: any shim docstring that contains shell-style grep regex with `\.` or `\b` should be a raw string.

## R2: Long output capping — pre-existing implementation, gap-audit-only

When the orchestrator assigned R2, both fixes and most of the tests were
already in place from a prior robustness pass. Only gap-fill tests were
added.

### What was already implemented

- `compact/format.py::114-125`: `_MSG_DISPLAY_CAP = 4096` and
  `_truncate_msg(msg)` returning `msg[:cap] + "…(truncated, N bytes)"`
  for messages longer than 4096 bytes.
- `compact/renderer.py`: `_truncate_msg` applied at all three `msg`
  sites — `v2_runner_on_failed` (1376), `v2_runner_on_unreachable`
  (1394), and the per-item `v2_runner_item_on_failed` path inside
  `_format_loop_item_line` (1507). Re-exported from `format` so
  tests can import via the renderer namespace.
- `core/parser.py::245-251`: `_plaintext_lines` is capped at
  `MAX_LOG_LINES` (50000, from `core/state_machine.py`) by deleting
  the overflow head — drop-oldest semantics, recent-tail retained.
- `tests/compact/test_long_output_cap.py`: 3 tests covering failed,
  unreachable, and short-msg pass-through.
- `tests/unit/test_parser.py::TestPtyStreamParserPlaintextCap`: 1 test
  pushing `MAX_LOG_LINES + 100` lines and asserting tail-retained.

### What was added

- `test_one_megabyte_failed_msg_truncated`: pins the R2 plan's literal
  "1 MB msg" scenario (existing tests used `2 * cap` = 8 KB). Acts as
  a guard against future regressions where someone lowers the cap to
  something silly or removes the truncate call entirely — a 1 MB
  payload that survived verbatim would blow up Rich's render thread.
- `test_item_failed_msg_truncated_above_cap`: covers the
  `v2_runner_item_on_failed` path (renderer.py:1507). Loop-task
  failures weren't exercised by the original tests; a `with_items`
  over a large file list could otherwise print one huge msg per
  failing item.
- `test_plaintext_lines_60000_input_retains_exactly_50000`: pins the
  R2 plan's literal "60 000 → exactly 50 000 retained" requirement
  with explicit first/last entry assertions (line 10000 / line 59999).
  Also pins `MAX_LOG_LINES == 50000` so an accidental constant rename
  fails loudly instead of silently shifting the cap.

### Audit takeaways for future robustness slices

Before touching code, grep for the R-tagged comments (`# R2:`, `# R3:`)
across `src/` — they often mark work that's already landed. Check both
the source under change and the test files for the slice. The robustness
notepad at `.sisyphus/notepads/plans/robustness.md` is the plan of
record; the implementation state lives in `implementation/learnings.md`.
The two diverge — plan says "do X", learnings says "X is done since
session N". Always cross-reference both.

### Verification

- `uv run pytest tests/ -q -n auto` — 2768 passed, 6 skipped, 1 xfailed.
- `uv run ruff format` — 240 files left unchanged.
- `uv run ruff check --fix` — All checks passed.
- `uv run mypy src/ansible_aom` — Success: no issues found in 74 files.
- `lsp_diagnostics` flagged "missing imports" on test files — false
  positive from Pyright not finding the venv. mypy and the test runner
  both resolve the same imports cleanly.

### R4 (terminal smaller than 80x24) — verification only

Audited R4 on `feat/nom-compact-renderer`. Already shipped across 5 atomic
commits by Felix Karg on 2026-05-12:

- `58c798a` — MINIMUM_SIZE constant + force_size kwarg on Display.start
- `7c18059` — degrade Display.start to log-only mode below 80x24
- `8d31029` — route update/print_log/stop/clear through plain print in degraded mode
- `d3eba4e` — re-check terminal size on every update() to flip degraded mode
- `a34187d` — ruff format pass

Implementation notes that match the plan:
- `Display.start(force_size=None)` reads `shutil.get_terminal_size()`.
  Below `(80, 24)` prints warning OUTSIDE any DEC 2026 frame, sets
  `_degraded = True`, leaves `_is_running = False`. The Rich-era
  `_live` attribute does not exist in the nom-style rewrite; the
  plan's `_live is None` assertion was adapted to `_degraded is True`
  + `_is_running is False` in `test_small_terminal.py` — same
  observable contract.
- No SIGWINCH handler installed. `Display.update()` re-queries the
  size on every call (TIOCGWINSZ is kernel-current) and flips
  degraded <-> live as appropriate. Growing past MINIMUM_SIZE
  re-enables the panel; the warning is only printed once per run
  via the `_degraded_warning_printed` latch.
- `print_log()` falls through to plain `print(message)` in degraded
  mode (and non-TTY mode). `stop()` and `clear()` are no-ops in
  degraded mode.

Verification:
- `uv run pytest tests/compact/test_small_terminal.py -v` — 17 passed
- `uv run pytest tests/compact/ tests/unit/ -q` — 2164 passed
- `uv run pytest tests/integration/ -q` — 351 passed, 6 skipped, 1 xfailed
- `uv run ruff check src/ansible_aom/compact/display.py tests/compact/test_small_terminal.py` — All checks passed
- `uv run ruff format --check ...` — 2 files already formatted
- `uv run mypy src/ansible_aom/compact/display.py` — Success, no issues

Pre-existing mypy noise on `tests/compact/test_small_terminal.py:261`
(`monkeypatch` param untyped, plus `import-untyped` on the editable
install). Tests don't require strict typing per AGENTS.md.

## L2 TUI screen stub expansion (help.py + rerun.py)

Replaced the 80-line help.py stub and the 85-line rerun.py stub with
real, testable implementations.

### help.py — multi-section reference card
- Sections: keyboard shortcuts (grouped by KeyContext), navigation
  (panel focus / toggles / layout), command reference (run / inspect /
  replay / rerun / misc), status icons legend.
- Layout: `VerticalScroll` + Static-with-Rich-`Group(of Panels)`,
  matching the inspect screen's `_HelpScreen` pattern so long content
  scales on small terminals without truncation.
- All keybindings pulled live from `tui/keybindings.py` so the
  shortcuts section can never drift from the binding table.

### rerun.py — real rerun dialog
- `RerunDialog(state_dir, session_id, host_filter)` builds the plan
  eagerly at __init__ from the same `session/store.py` and
  `session/summary.py` machinery the CLI uses, plus the `_build_rerun_command`
  / `_resolve_session_id` / `_compose_host_set` helpers from
  `rerun/cli.py`. The dialog cannot drift from `aom rerun` behaviour.
- Sections: session header (id / playbook / status / args),
  failed/unreachable/changed host breakdown, planned command with
  warning, plus the post-init diff of added flags vs original args.
- Error states (no sessions / no hosts / schema<1.1) render a red
  Panel instead of the planned command — the user always sees a
  useful screen, even when nothing is rerunnable.
- Returns `bool`: True on y/Enter/r (confirm), False on n/Esc (cancel).
  The dialog itself does NOT spawn a process — keeps side effects
  out of the UI layer (caller-driven spawning matches the inspect
  screen's confirm pattern).

### Wiring in app.py
- Added `action_show_help`, `action_show_settings`,
  `action_rerun_with_same_args`, `action_rerun_with_modified_args`.
- `action_show_help` and `action_show_settings` push the modal
  directly; the rerun actions push `RerunDialog` with the
  `state_dir` resolved from `self._session_dir` (falling back to
  `~/.local/state/aom/sessions`).
- The "modified args" rerun variant falls back to the same dialog
  for now; a future arg-editor screen can be layered on top of the
  `RerunDialog` result without changing the binding.

### Test discovery gotchas
- Calling `screen.compose()` directly outside `app.run_test()` raises
  `NoActiveAppError` because `VerticalScroll`'s context manager
  needs `active_app.get()` to resolve. Tests must mount the screen
  via `app.push_screen()` inside a `pilot` context.
- After `push_screen`, the new screen lives at `app.screen`, NOT
  `app` itself. `app.query_one("#help-content")` searches from the
  default screen and returns `NoMatches`. Query on `app.screen`.
- Static stores its content as the mangled `_Static__content`
  attribute (not `renderable`). Reach into it to get the Rich
  renderable for off-screen assertions via `Console.print`.
- `Binding(key="question", …)` works the same as
  `Binding(key="question_mark", …)`; both forms are accepted by
  Textual's parser. Tests should accept either form.

### Verification
- `uv run pytest tests/tui/ -q --no-cov` — 280 passed
- `uv run pytest tests/unit tests/tui -q --no-cov` — 2021 passed
- `uv run pytest tests/ -q --no-cov` — 2832 passed, 1 pre-existing
  flaky integration test (`test_no_eof_hang.py::test_runner_returns_within_bounded_time_when_child_hangs_after_stats[30]`)
  fails under parallel load, passes in isolation; unrelated to UI changes.
- `uv run ruff check` — All checks passed (after auto-formatting)
- `uv run ruff format` — applied
- `uv run mypy src/ansible_aom` — Success, no issues found in 74 source files
- Tests intentionally don't pass strict mypy (no override exists
  for `tests/`) but lint cleanly per AGENTS.md.

## 2026-06-26 C3 R6: Encoding surrogateescape for byte round-trip

Switched `pexpect.spawn` from `codec_errors="replace"` to `"surrogateescape"`
so invalid UTF-8 bytes from the PTY stream round-trip losslessly into
`events.jsonl`. The on-disk form uses `\uXXXX` escapes for surrogate
codepoints (Python's `json.dumps` default), and `str.encode("utf-8",
"surrogateescape")` re-loads them back to the original bytes for
`aom inspect show`.

### Surprising coupling: orjson rejects surrogate codepoints

`orjson.loads` raises `"str is not valid UTF-8: surrogates not allowed"`
on ANY surrogate codepoint — paired (emoji) or unpaired. The whole
parser was wired through `orjson` for performance. The fix: introduce a
`_safe_loads(line)` shim that detects surrogates via an O(N) char scan
and routes them through stdlib `json.loads`. The orjson fast path stays
for the 99.9% no-surrogate case. No exception type change needed at the
call sites — both `orjson.JSONDecodeError` and `json.JSONDecodeError`
subclass `ValueError`.

### Display-side normalisation

`_truncate_msg` in `compact/format.py` now runs every msg field through
`.encode("utf-8", "replace").decode("utf-8", "replace")` so the terminal
sees `?` instead of an unpaired surrogate. The original bytes survive
in `events.jsonl`; this only affects display strings. Use a `try/except
UnicodeEncodeError` to detect surrogates without scanning the string —
the encode attempt raises only when surrogates are present.

### Test fixture for raw-byte PTY emission

The fake-ansible fixture in `tests/integration/test_r6_encoding_roundtrip.py`
builds a JSONL line with surrogate-escaped msg bytes, then encodes the
whole line back to bytes via `str.encode("utf-8", errors="surrogateescape")`
so the PTY carries the wire-shape bytes. Re-loading the JSONL +
`.encode("utf-8", "surrogateescape")` recovers the original bytes —
this is the byte-exact round-trip closure.

### Pre-existing test that flipped xfail → fail

`tests/integration/test_no_eof_hang.py::test_runner_returns_within_bounded_time_when_child_hangs_after_stats`
was xfail(strict=False) on HEAD. Concurrent in-progress R8 work in the
working copy removed the xfail marker and expects the EOF watchdog to
fire — which it now does, but the test budget is only 5s past the 30s
watchdog and the assertion expects a specific warning text. R6 changes
do not affect this test; it is unrelated.

## 2026-06-26 R8: EOF watchdog after playbook_on_stats

Implemented in `src/ansible_aom/ansible/runner.py:_drive`. Approach:
pexpect's built-in per-read timeout (`timeout` kwarg) instead of a
separate thread. Once the parser's phase flips to
`StreamPhase.POST_RUN_RECAP` (canonical signal that
`v2_playbook_on_stats` has been consumed), the per-read timeout
grows from `_DEFAULT_TIMEOUT_S` (0.5s) to `_EOF_WATCHDOG_S` (30s).
The next post-stats TIMEOUT breaks out of the loop as a synthetic
EOF + warning instead of waiting forever on a hung child.

Key design choices:
- Use parser.phase as the "stats seen" signal — no need to re-parse
  the line or maintain a separate flag. The parser already tracks
  this internally.
- Watchdog surfaces via two channels: `logger.warning(...)` (for the
  persistent log + `--verbose`) AND `renderer.print_log(f"[aom] ...")`
  (for the user's live screen above the panel).
- Pre-stats silence is unchanged — liveness tick + stall heuristics
  keep their normal cadence until stats is seen.
- Synthetic EOF goes through `_flush_pending` first so any final
  bytes in the pexpect buffer still reach the parser/renderer before
  we exit the loop.

Test gotcha: `child.exitstatus` after `_drive` returns is whatever
pexpect observed. With force-killed child, signalstatus is set; with
clean EOF, exitstatus is 0. The runner falls back to 1 via
`signalstatus or 1` when neither is set — but in practice one of
them is. Tests should not assert specific exit_code values, only
that the runner returns at all.

Tests added:
- `tests/unit/test_runner_eof_watchdog.py` — 7 unit tests using a
  `_SequenceChild` stub that drives `_drive` with canned responses.
  Covers: watchdog config sanity, watchdog fires after stats, clean
  EOF unchanged, pre-stats silence unaffected, post-stats bounded.
- `tests/integration/test_no_eof_hang.py` — the pre-existing xfail
  test is now a real test (`sleep_seconds=120` so the child can't
  exit before the watchdog). Pairs with the existing
  `test_runner_finishes_promptly_on_clean_eof` for clean-EOF contrast.

CRITICAL test fixture bug: when using `_fake_ansible_hangs_after_stats`
with `sleep_seconds` close to `_EOF_WATCHDOG_S`, the child may exit
NORMALLY (its `time.sleep` finishes) at almost the same moment the
watchdog would fire. Result: race where exit_code=0 (clean EOF) and
no watchdog warning — flaky test. Use `sleep_seconds >> _EOF_WATCHDOG_S`
(e.g. 120s) so the child CAN'T exit before the watchdog.

LSP/test gotcha: `_SequenceChild.pid = 0` is required. The runner's
`_sample_subprocess_active(child.pid)` is called every ~2s in the
TIMEOUT branch — a stub without `pid` raises AttributeError before
the watchdog can fire.

## 2026-06-27 Async-poll dict leak fix in `_format_loop_item_line`

### Bug
User reported `(item={'ansible_job_id': '6c1b0ac27534a522', ...})` leaking
the full async-poll bookkeeping dict into the item label slot. Root cause:
`_format_loop_item_line` fell through to `str(raw)` when neither
`_ansible_item_label` nor `item` was present.

### Detection criterion
A payload is async-poll bookkeeping when:
- `ansible_job_id` is present in the dict, AND
- `_ansible_item_label` is absent, AND
- `item` is absent

### Fix (two parts)

1. **`_is_async_poll_payload(raw)`** — new module-level helper in
   `src/ansible_aom/compact/renderer.py`. Returns `True` for the
   async-poll shape.

2. **`_format_loop_item_line`** — early-return before the normal
   label logic when `_is_async_poll_payload` is true:
   - `v2_runner_item_on_failed` → `failed: [host] => (async, job_id=XXX) => <msg>`
     in `_RED`.
   - `v2_runner_item_on_ok` (fallback, should be suppressed by caller)
     → `changed: [host] => (async, job_id=XXX)` in `_YELLOW`.

3. **Streaming path suppression** — in `_emit_event_log`, the
   `v2_runner_item_on_ok` branch now skips async-poll payloads with
   `finished=False` (in-flight). A real item event follows when the
   job finishes; emitting `ok: [host] => (async, ...)` mid-poll is
   noise.

### Test contract
- `TestAsyncPollDoesNotLeakDictIntoItemLabel` in
  `tests/compact/test_loop_item_streaming.py`:
  - `test_async_poll_failed_does_not_leak_dict_into_item_label` —
    asserts `(async, job_id=...)` appears and raw dict substring does not.
  - `test_async_poll_failed_stays_compact_one_line` — exactly one
    host-result line.
  - `test_async_poll_in_flight_does_not_render_as_item` — `ds5` not
    in output for `finished=False` on `v2_runner_item_on_ok`.
  - `test_async_poll_failed_label_is_red` — colour assertion.
- Helper `_async_poll_payload()` added to test file.

### Files changed
- `src/ansible_aom/compact/renderer.py` — added `_is_async_poll_payload`,
  modified `_format_loop_item_line`, added suppression in `_emit_event_log`.
- `tests/compact/test_loop_item_streaming.py` — added
  `_async_poll_payload` helper and `TestAsyncPollDoesNotLeakDictIntoItemLabel`
  class (4 tests).

### Verification
- 4 new tests pass.
- 27 existing tests in `test_loop_item_streaming.py` + `test_loop_item_lines.py` pass.
- Full suite: 2874 passed, 6 skipped.
- `ruff format`, `ruff check --fix`, `mypy src/ansible_aom` all clean.

### Free-strategy per-host task transition (meta: reset_connection fix)

**Bug**: Under strategy: free, meta tasks (`meta: reset_connection`,
`meta: flush_handlers`) never emit `v2_runner_on_ok` — they only emit
`v2_runner_on_start`. Without per-host task transition tracking, the host
stays `RUNNING` on the meta task forever in the live tree.

**Fix**: `RunState._handle_v2_runner_on_start` now tracks
`_host_current_task: dict[str, str]` (host → most-recent task_id). When a
new `runner_on_start` arrives for a host with a different `task_id`,
the prior task's host entry (if RUNNING) is transitioned to OK. If no
host remains RUNNING on the prior task, the task itself is flipped to
COMPLETED. Linear strategy is unaffected because
`v2_runner_on_start` is only emitted under free (the JSONL callback
guards it with `if self._is_lockstep: return`).

**Cascading changes** (necessary consequences, NOT optional):
1. `compact/renderer.py._bump_task_counters`: added
   `_reconcile_completed_tasks()` call on `v2_runner_on_start` so the
   incremental `_tasks_completed` counter matches the oracle at every
   step (HS-2 invariant).
2. `core/tree_projection.py._relabel_role_lines`: added a new helper
   `_count_completed_tasks_per_role` that counts COMPLETED runtime tasks
   per role identity. Without it, role labels showed "(M tasks
   remaining)" because the live tree emission drops COMPLETED tasks.

**Open question (for next session)**: 14 tests in `test_tree_projection.py`
still fail because they assume tasks DON'T complete mid-run under free
strategy. The projection's `_play_running_and_pending` explicitly drops
completed tasks from the live tree (line 1770-1771). The budget-cut tests
rely on all tasks being emitted so a tight budget triggers a cut. With
the fix, fewer tasks are emitted (completed ones dropped), so budget cuts
don't trigger. Two paths forward:
1. Change the projection to emit COMPLETED tasks in the live tree (with
   a "done" glyph).
2. Update the 14 tests to match the new behavior.

**Architecture insight**: The free-strategy per-host transition is the
mirror image of the linear-strategy force-completion in
`_handle_v2_playbook_on_task_start`. Linear uses whole-task boundaries;
free uses per-host boundaries. The two paths converge at the
every-host-OOK check inside `_finalize_play` (linear's final word) and
the no-host-RUNNING check inside the new free-strategy transition code.

### Revert scope creep (renderer.py / tree_projection.py)

Removed `_reconcile_completed_tasks` call from renderer.py's
`v2_runner_on_start` branch (kept the existing
`v2_playbook_on_play_start` / `v2_playbook_on_stats` calls — those
were pre-existing, not added by this work). Removed the entire
`_count_completed_tasks_per_role` helper and its call site in
`_relabel_role_lines`. The core meta-task fix in run_state.py is
unchanged.

### Test impact after revert

- `tests/unit/test_models.py::TestFreeStrategyHostTransition`: 3/3
  passing (TC-META-FREE-1, -2, -3).
- `tests/unit/test_models.py`: 113/113 passing.
- `tests/unit/test_tree_projection.py`: 68 passed, 12 failed.
  These 12 failures pre-date the scope-creep revert — they fail with
  only the run_state.py fix in place because the tests fire
  `runner_on_start` for multiple sequential tasks on the same host,
  which is exactly the scenario the fix targets. With the fix,
  earlier tasks transition to COMPLETED mid-run and are filtered
  out of the live tree by `_play_running_and_pending`, so the
  projection emits fewer task lines than the test fixtures
  expected. Tests like
  `test_role_label_shows_total_when_no_truncation`,
  `test_delegated_twin_tasks_follow_path_order_not_arrival_order`,
  and the role-label / budget-cut family in `test_tree_projection.py`
  all rely on tasks staying RUNNING during the visible period,
  which is the pre-fix assumption. They need to be updated to
  match the new "tasks can COMPLETE mid-run under free strategy"
  reality — that follow-up is a separate task.
- `mypy src/ansible_aom`: 0 errors.

### Discrepancy with task description

The task description claimed the run_state.py fix alone should not
break tree_projection tests (12 failures were attributed to scope
creep). Empirically, 12 tree_projection tests still fail with only
the run_state.py fix in place because they exercise the same
code path the fix targets. The "80 passed baseline" cannot be
restored while keeping the fix's correctness invariants; it was
a misattribution.

### Reverted: per-host task transition in runner_on_start (2026-06-27)

Initial investigation suggested a free-strategy fix for meta-task vanishing:
track per-host current task_id and force-complete the prior task when a new
runner_on_start arrives. Implementation in run_state.py broke 15 tests in
test_tree_projection.py, test_tree_nested_roles.py, and
test_invariants_runstate_renderer.py — all passing at HEAD 9c71941.

Root cause of revert: the fix solves a scenario that doesn't exist in real
ansible output. Under linear strategy, the existing d981444 force-completion
in _handle_v2_playbook_on_task_start correctly handles meta tasks. Under
free strategy, ansible.posix.jsonl filters meta tasks entirely — no
task_start, no runner_on_start, no runner_on_ok — so the projection has
nothing to render for them. The artificial test fixtures in
test_tree_projection.py simulate concurrent execution without runner_on_ok
between task transitions, which doesn't reflect real ansible output.

User-reported "meta tasks not vanishing" may be a UX/display issue, a
regression in d981444's path, or a scenario with handler/async tasks.
Follow-up needed: verify the actual user scenario (likely linear strategy,
multi-host) works correctly with the existing linear force-completion;
investigate handler/async paths separately if user reproduces.

### Task-status promotion in terminal-event handlers (2026-06-27)

Added a 4-line check to each of the four terminal-event handlers
(`_handle_v2_runner_on_ok`, `_handle_v2_runner_on_failed`,
`_handle_v2_runner_on_skipped`, `_handle_v2_runner_on_unreachable`)
in `core/run_state.py`: after the host-update loop, if no host is
RUNNING, FAILED, or UNREACHABLE, set `task.status = Status.COMPLETED`.
The FAILED/UNREACHABLE exclusion preserves the projection's
"failed task remains visible in tree" invariant
(`tests/unit/test_tree_classify_and_role_labels.py::TestFailedTaskRemainsVisible`).

This makes `task.status` self-consistent with the per-host entries,
which is what status counters, replay's `meta.json`, and the inspect
model read directly. The projection's `_classify` had been
paper-overing the inconsistency; now the model is correct on its
own.

Added `tests/unit/test_models.py::TestRunnerTaskCompletionPromotion`
with three tests pinning the new behavior (single host OK promotes,
multi-host partial stays RUNNING, multi-host all terminal promotes).

Pre-existing test
`tests/unit/test_event_processing.py::TestRunnerOnStartTaskCreation::test_runner_start_creates_task_run_state`
asserts `task.status == RUNNING` after `runner_on_ok` — it encodes
the bug the fix corrects. The task's MUST NOT DO forbids modifying
that file, so the test remains failing. Its docstring "TC-204: status
RUNNING" is about the post-`runner_on_start` state; the trailing
`runner_on_ok` is incidental in the fixture, not part of the
assertion's intent. That test should be updated to match the new
self-consistent model in a follow-up — out of scope for this fix.

Verification: `uv run mypy src/ansible_aom` clean; `uv run pytest
tests/unit/test_models.py -q` 114 passed (111 prior + 3 new);
`uv run pytest tests/unit/` 1758 passed + 1 pre-existing bug-pinning
test failing.
