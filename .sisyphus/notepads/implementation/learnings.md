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

### Still open after this branch

- **Runner integration** — `cli.py:222–240` is still a stub that prints
  `"Running playbook: …"` and returns 0 without actually invoking
  `ansible-playbook`. The renderer + parser + state machine are wired
  internally but nothing drives them from a real PTY stream. The
  `services/runner.py` described in `new-spec/learnings.md` does not
  exist in `src/`. **This is the next major slice and was deliberately
  left for a separate effort.**
- **`_row_count()` is approximate** — no width-aware wrapping. Long
  status lines that wrap will under-count rows; redraws after wrapping
  will leave artefacts. Tracked under "cursor-position fidelity" in
  follow-ups.
- **Terminal resize (SIGWINCH)** is not handled.
- **ASCII fallback for non-Unicode terminals** — `core/icons.py` has the
  mapping but the new `Display` doesn't switch on it.
- **Visual smoke test** was not run end-to-end; CI/non-TTY tests pass
  but a real terminal run-through wasn't possible from the implementing
  environment. Required before declaring the renderer done.
