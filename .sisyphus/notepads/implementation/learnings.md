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
- **TC-148** (Timeout default): 9 tests — DEFAULT_PASSWORD_TIMEOUT=60, type checks, timeout constant availability

## 2026-05-08 nom-style Display Backend Swap (branch: feat/nom-compact-renderer)

### What changed

- **`compact/display.py`**: replaced `rich.live.Live` with direct stdout
  ANSI cursor positioning + DEC mode 2026 (synchronized output). Public
  API (`start`/`stop`/`update`/`print_log`/`clear`, `is_running`, `is_tty`)
  is preserved so `CompactRenderer` needs no changes. Each frame is wrapped
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
  produces no ANSI, `stop()` emits the show-cursor sequence, throttle
  coalesces frames within 250 ms.
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
