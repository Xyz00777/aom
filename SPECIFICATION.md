# AOM (Ansible Output Monitor) - Technical Specification

**Version:** 1.8  
**Last Updated:** 2026-04-20

---

## 1. Overview

### 1.1 What is AOM?

AOM (Ansible Output Monitor) is a nom-style terminal interface for monitoring `ansible-playbook` execution in real time. It provides a clean, streaming view of playbook progress with status indicators, optionally expanding into a full multi-panel TUI for interactive inspection.

### 1.2 Why This Exists

Previous generations (ansible-tui, ansible-aom, ansible-aomp) each had tradeoffs:

- **ansible-tui**: Full Textual TUI with regex parsing - unreliable matching, complex async coordination
- **ansible-aom**: Comprehensive spec with JSON callback - over-engineered, too many dependencies
- **ansible-aomp**: Zero dependencies, stdlib-only - no interactive features, no keyboard navigation

AOM combines the best of all approaches: robust JSONL parsing, interactive TUI when needed, and a clean nom-style default view.

### 1.3 Key Differences from Previous Generations

| Aspect | Previous | AOM |
|--------|----------|-----|
| Default view | Full TUI or streaming text | Compact nom-style (streaming) |
| Full TUI | Always on | Optional via `--tui` flag |
| Parsing | Regex or JSON callback | JSONL only (ansible.posix.jsonl) |
| Task matching | Name-based (fragile) | Task IDs (reliable) |
| Configuration | Multi-layer hierarchy | Single config.yaml + CLI args |
| Dependencies | Heavy or none | Textual, Pydantic, pexpect |
| View toggle | Not supported | Fixed at CLI start |

---

## 2. Architecture

### 2.1 High-Level Components

```
┌─────────────────────────────────────────────────────────┐
│                     CLI Entry Point                      │
│                    (cli.py, __main__.py)                 │
└────────────────────────┬────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
┌──────────────────────┐ ┌──────────────────────┐
│  EventSource port    │ │  Renderer port       │
│  (drivers/protocol)  │ │ (renderer/protocol)  │
└──────────┬───────────┘ └──────────┬───────────┘
           │                        │
   ┌───────┴───────┐         ┌──────┴────────────┐
   ▼               ▼         ▼          ▼        ▼
LiveDriver    ReplayDriver  compact   tui   formats/json
(ansible/      (session/
 runner +       store)
 preflight)
           │                        │
           └───────────┬────────────┘
                       ▼
┌─────────────────────────────────────────────┐
│         Pure domain core (core/)             │
│  ┌────────────────────────────────────────┐  │
│  │ models.py — RunState aggregate +       │  │
│  │   plays / tasks / hosts entities        │  │
│  ├────────────────────────────────────────┤  │
│  │ parser.py — JSONL + --list-* parsing   │  │
│  ├────────────────────────────────────────┤  │
│  │ state_machine.py — ExecutionState FSM  │  │
│  ├────────────────────────────────────────┤  │
│  │ tree, heartbeat, overhead, redaction,  │  │
│  │ inspect_model, parity, prompts, icons  │  │
│  └────────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
                       ▲
                       │
              Compact / TUI / JSON
              renderers read this
├─────────────────────┤    ├─────────────────────┤
│ • Rich Console      │    │ • Textual App        │
│ • ANSI cursor ctrl   │    │ • Multi-panel UI    │
│ • Fixed-bottom panel │    │ • Interactive nav   │
│ • Scrolling logs    │    │ • Search/filter      │
└─────────────────────┘    └─────────────────────┘
    (default)                    (optional)
```

### 2.2 Component Responsibilities

Module layout and inter-package dependencies are owned by
[`ARCHITECTURE.md`](ARCHITECTURE.md) — see §3 (Module Map) and §6 (Architectural
Decisions). This section restates only the responsibilities that affect
externally observable behavior.

**CLI layer** (`cli.py`, `__main__.py`)
- Parse CLI arguments and check ansible.posix availability.
- Compose one `EventSource` (live vs replay) with one `Renderer` (compact, TUI,
  or JSON). The CLI is the only place that knows concrete adapters.

**Live driver** (`drivers/live.py` wrapping `ansible/runner.py`)
- Run `ansible-playbook --list-tasks` and `--list-hosts` in parallel.
- Spawn `ansible-playbook` under a pexpect PTY with the JSONL callback.
- Detect password / interactive prompts; route them to the renderer.
- Handle signals and cancellation; emit a final completion event.

**Replay driver** (`drivers/replay.py`)
- Read a recorded session artifact via `session/store.py` and re-emit the
  recorded events through the same `Renderer` interface as the live driver.

**Domain core** (`core/`)
- `models.py` — `RunState` aggregate, `PlayRunState`/`TaskRunState`/`HostRunState`
  entities, definition value objects, `Status` and `WarningType` enums.
- `state_machine.py` — `ExecutionState` lifecycle FSM.
- `parser.py` — JSONL stream parsing, `--list-tasks` / `--list-hosts` parsing.
- `tree.py`, `heartbeat.py`, `overhead.py`, `inspect_model.py` — pure
  projections of state into render-ready shapes.
- `redaction.py`, `prompts.py`, `icons.py`, `config.py` — pure services.

**Compact renderer** (`compact/`)
- ANSI output via Rich Console + ANSI cursor manipulation.
- Fixed nom-style status panel at the bottom, scrolling logs above.
- Pure formatters in `compact/format.py`; lifecycle in `compact/renderer.py`.

**Textual TUI** (`tui/`)
- Multi-panel interactive interface, tree navigation, log panel with search,
  summary panel, configurable status bar, help overlay, settings screen.

**JSON renderer** (`formats/json.py`)
- Emits the `RunSummary v1` JSON schema for non-interactive consumers.

### 2.3 Renderer Protocol

The `Renderer` Protocol defines the sink that the compact, TUI, and JSON
renderers all satisfy. The full method surface — including
`set_definitions`, `add_warning`, `print_log`, `tick`, `note_pty_bytes`,
`note_subprocess_active`, and `handle_interactive_prompt` — is defined in
[`src/ansible_aom/renderer/protocol.py`](src/ansible_aom/renderer/protocol.py),
which is the source of truth. See [`ARCHITECTURE.md`](ARCHITECTURE.md) §4.1 for
the architectural role of the Protocol.

The minimal surface every renderer implements is:

```python
class Renderer(Protocol):
    def start(self, playbook: str, args: list[str]) -> None: ...
    def set_definitions(self, definitions: list[PlayDefinition]) -> None: ...
    def update_state(self, event: dict) -> None: ...
    def handle_password_prompt(self, prompt_text: str) -> str: ...
    def handle_completion(self, exit_code: int, state: str) -> None: ...
    def stop(self) -> None: ...
```

The Protocol is paired with an `EventSource` Protocol (`drivers/protocol.py`)
that produces the events fed into the renderer — see ARCHITECTURE.md §4.2.

**Factory Function:**

```python
def create_renderer(tui_mode: bool = False, **kwargs) -> Renderer:
    """Create the appropriate renderer based on CLI flags."""
    if tui_mode:
        from ansible_aom.tui.app import AOMApp
        return AOMApp(**kwargs)
    else:
        from ansible_aom.compact.renderer import CompactRenderer
        return CompactRenderer(**kwargs)
```

This Protocol-based architecture allows:
- Runtime renderer selection via `--tui` flag
- Shared core logic in `ansible_aom.core`
- Clean separation between UI and business logic
- Independent testing of each renderer

### 2.4 Data Flow

```
1. Startup
   CLI → Check ansible.posix → Pre-parse --list-tasks → Build tree
                              ↓
   Show compact view OR launch full TUI

2. Execution
   pexpect spawn → Stream JSONL → Parse events → Update state
                                            ↓
   Call_from_thread → Render updates

3. Password Prompt
   pexpect detects prompt → Signal main thread → Show modal
                           ← User input ←
   Send password to PTY

4. Completion
   Process exits → Save artifact → Stay open for review
```

---

## 3. Command Interface

### 3.1 Main Command

```
aom [OPTIONS] <playbook> [ANSIBLE_OPTIONS]
```

**Examples:**

```bash
# Basic usage (compact view)
aom playbook.yml

# Full TUI mode
aom --tui playbook.yml

# With Ansible options
aom playbook.yml -i inventory.ini --limit webservers

# Interactive password
aom playbook.yml --ask-vault-pass --ask-become-pass

# Inspect previous runs
aom inspect list
aom inspect <session-id> --failed
```

### 3.2 CLI Flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--tui` | flag | false | Launch full multi-panel TUI |
| `--verbose` / `-v` | flag | false | Print pre-execution diagnostics; enable DEBUG logging |
| `--help` | flag | - | Show help message |
| `--version` | flag | - | Show version |

All other arguments pass through to ansible-playbook.

**`--verbose` / `-v` Flag Behavior:**

When `--verbose` is specified, AOM prints diagnostic information BEFORE the run starts:

- Resolved `ansible-playbook` command (full path)
- Environment overrides (ANSIBLE_* variables)
- Terminal capabilities detected (color support, Unicode, size)
- `--list-tasks` summary (play count, task count, roles detected)

This works in BOTH modes (compact and TUI). The flag also enables DEBUG level logging to the log file (see Section 14.5).

### 3.3 Inspect Subcommand

```
aom inspect list                          # List all sessions
aom inspect <session-id>                  # Show summary
aom inspect <session-id> --failed         # Filter failed tasks
aom inspect <session-id> --host <name>    # Filter by host
aom inspect <session-id> --tree           # Show task tree
aom inspect <session-id> --export         # Export as .aom artifact
aom inspect diff <id1> <id2>              # Compare two runs
aom inspect prune --days 30               # Cleanup old sessions
aom inspect --tui                         # Optional TUI mode for browsing
```

Output formats:
- Default: Rich tables (pipe-friendly)
- `--json`: JSON output
- `--jsonl`: Raw event dump

### 3.4 Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Successful playbook execution |
| 1 | Playbook execution failed (task failure or unreachable host) |
| 2 | Unreachable hosts |
| 127 | `ansible-playbook` command not found |
| 130 | User cancelled (SIGINT) |

---

## 4. View Modes

### 4.1 Compact View (Default)

The default mode provides a nom-style streaming interface:

```
▶ site.yml ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Running: Install nginx on web1, Configure firewall on web2

┌─ Play: Configure Webservers ────────────────────────────────────────────┐
│ ● Install nginx                                           web1: 0:02 │
│ ● Install nginx                                           web2: 0:02 │
│ ◐ Configure firewall                                      web1      │
│ □ Configure firewall                                      web2      │
│ □ Start services                                          web1,web2 │
└─────────────────────────────────────────────────────────────────────────┘

host  ok  changed  failed  on
web1   2        0       0  Configure firewall  ◐ 0s
web2   1        0       0  (idle)

site.yml │ 2/2 hosts │ 3/5 tasks │ 0:00:42 ●
```

On playbook completion, the host table always prints (with a `skipped`
column when any host has skipped tasks). On failure or cancel, the tree
snapshot is also printed so the user can inspect what was in flight. On
success, only the host table is printed (stale running indicators would
be misleading).

**Layout:**
- Header: Playbook name with progress bar
- Running: Currently executing tasks per host
- Tree: Collapsible play/task structure with status icons
- Host table: Per-host status counts in column-aligned rows
- Status line: Warning ⚠ and deprecation ✱ counts displayed alongside host progress

**Status Line Format (Compact Mode):**
```
site.yml │ 3/10 hosts │ ⚠ 2 ✱ 1 │ 0:05:23
```
Where:
- `site.yml` — Playbook name
- `3/10 hosts` — Hosts completed/total
- `⚠ 2` — Warning count
- `✱ 1` — Deprecation count
- `0:05:23` — Elapsed time

**Characteristics:**
- ANSI-based rendering using Rich Console + direct ANSI cursor positioning
- Fixed-bottom status panel while logs scroll above (nom-style)
- No Textual dependency (lightweight alternative)
- Streaming updates with status icons
- No interactive panel switching

**Rendering Implementation (Compact Mode):**

Two approaches available, use **Rich Live** for MVP:

1. **Rich Live** (recommended for initial implementation):
   - `Rich Live` context manager renders the status panel (bottom)
   - `live.console.print()` outputs log lines ABOVE the live display
   - `live.update()` refreshes the status panel content
   - `refresh_per_second=4` for smooth updates (same as nom)
   - Limitation: less control over cursor positioning than direct ANSI

2. **blessed + ANSI** (advanced, for pixel-perfect nom-style):
   - `blessed` library provides full ANSI cursor positioning API
   - `term.location(0, term.height - N)` for bottom positioning
   - ANSI escape sequences: `\033[s/u` (save/restore cursor), `\033[K` (clear line)
   - DEC mode 2026 (`\x1b[?2026h/l`) for synchronized output (no flicker)
   - How nom itself works — maximum control, most portability risk

**Password Prompt Handling (Compact Mode):**

The "pass-through" pattern — pause rendering, let user interact with terminal, resume:

```python
def _handle_password_prompt(self, child: pexpect.spawn):
    # 1. Stop the live rendering
    self.live.stop()
    
    # 2. Show any buffered prompt text from pexpect
    sys.stdout.write(child.before)
    sys.stdout.flush()
    
    # 3. Let getpass handle input (reads from /dev/tty, handles masking)
    password = getpass.getpass('')
    
    # 4. Send password to the PTY subprocess
    child.sendline(password)
    
    # 5. Resume rendering
    self.live.start()
```

This works because:
- When pexpect spawns a PTY, the subprocess's `/dev/tty` is the PTY slave
- `getpass.getpass()` opens the ACTUAL controlling terminal directly
- Rich `Live.stop()` clears the live display and restores normal stdout/stderr
- `Live.start()` reinitializes the display after input is complete

**Compact Mode Runtime Dependencies** (in addition to core):
- `rich` (already required) — for Live display and Console formatting
- Optional: `blessed` — for advanced ANSI cursor positioning (Phase 2)

### 4.2 Full TUI (--tui mode)

Multi-panel interactive interface:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [RUNNING] site.yml | Play: Configure Webservers | 0:04:23 | 23/45      │
├────────────────────────────────────────┬────────────────────────────────┤
│                                        │  Summary                        │
│  Tree View                             │  ───────────────────────────────│
│  ────────────────────────────────────  │  Play: Configure Webservers     │
│  ▼ ● Play: Configure Webservers        │  Hosts: 2/2 complete            │
│    ▼ ● Role: nginx (5 tasks)           │  Tasks: 23/45 complete          │
│      ● Install nginx           web1    │  Elapsed: 0:04:23               │
│      ● Install nginx           web2    │                                 │
│      ◐ Configure firewall      web1    │  Host Summary:                  │
│      □ Configure firewall      web2    │  web1: ● 12 ok, ◆ 3 changed    │
│      □ Start services          web1,2  │  web2: ◐ 1 running, ● 11 ok, ○ 2 skipped │
│    □ Task: Deploy config               ├────────────────────────────────┤
│                                        │  Log Panel                      │
│                                        │  ───────────────────────────────│
│                                        │  TASK [Install nginx]            │
│                                        │  ok: [web1] => {"changed": ...}  │
│                                        │  ok: [web2] => {"changed": ...}  │
│                                        │  TASK [Configure firewall]        │
│                                        │  ...                             │
├────────────────────────────────────────┴────────────────────────────────┤
│  ? Help | q Quit | ↑↓ Navigate | → Expand | ← Collapse | Tab Switch    │
└─────────────────────────────────────────────────────────────────────────┘
```

**Layout Components:**
- Status Bar (top, configurable)
- Tree View (left panel)
- Summary Panel (right top)
- Log Panel (right bottom)
- Footer (help shortcuts)

### 4.3 Non-TTY Behavior

When piped or redirected:
- Still use ANSI formatting (colors, icons)
- One line per status update
- No interactive features

### 4.4 Terminal Requirements

**Minimum Terminal Size:**
- 24 lines × 80 columns
- This is the minimum viable size for both compact and TUI modes

**Enforcement:**
- Check terminal size at startup
- If below minimum:
  - Show clear error: `"Terminal too small: {rows}×{cols}. Minimum: 24×80..Resize or use --no-tui flag."`
  - Exit with code 1

**Graceful Degradation:**
- If terminal is smaller than minimum, still attempt to render
- Show warning banner but continue operation
- Allow `--force` flag to proceed anyway

**Signal Handling:**

| Signal | Behavior |
|--------|----------|
| SIGINT (Ctrl+C) | **First press**: Forward to subprocess. **Second press** (within 2s): Kill everything, immediate exit. |
| SIGQUIT (Ctrl+\) | Log stack trace to file, then continue (do NOT terminate). Equivalent to Python's default SIGQUIT behavior. |
| SIGTERM | Save session, clean up terminal (restore cursor, clear alternate screen), exit gracefully with code 0 |
| SIGHUP | Save session, clean up terminal, exit gracefully with code 0 |
| SIGWINCH | Re-render in both modes. Compact mode re-renders status panel; TUI mode re-layouts all panels |
| SIGPIPE | Ignore (Python default behavior) |

**Terminal Cleanup on Exit:**

When AOM exits (any reason), it must:
1. Restore cursor visibility (if hidden)
2. Exit alternate screen mode (if entered)
3. Reset terminal colors and styles
4. Flush any buffered output

### 4.5 Compact Renderer Refresh Strategy

**Refresh Triggers:**
- **Event-driven**: Status panel re-renders on every state change event (ok, failed, changed, skipped, unreachable, runner_start)
- **Throttled**: Maximum 4 updates per second (`refresh_per_second=4` in Rich Live)
- **Timer-based**: Elapsed time updates every 1 second (independent of events)
- **Debounced**: Multiple events within the same 250ms window are batched into a single render

**Non-TTY Fallback:**
- No cursor manipulation or refresh throttling
- One line per status change event
- Elapsed time not updated continuously

### 4.6 Terminal Compatibility

**Unicode Support:**
- AOM requires Unicode support (UTF-8) for status icons (●, ◆, ✖, etc.)
- If terminal doesn't support Unicode: fall back to ASCII equivalents (●→*, ◆→+, ✖→X, ◐→@, □→.)
- Detection: check `blessed.Terminal()` capabilities at startup

**Color Support:**
- Full color (256/truecolor): Use full icon colors and Rich/Textual themes
- 16-color: Fall back to standard ANSI colors (green, yellow, red, cyan, white, dim)
- No color (monochrome/piped): Strip all colors, use text labels (OK, CHANGED, FAILED, etc.)
- Detection: Rich's `Console.detect_color()` and `blessed.Terminal().number_of_colors`

**Minimum Terminal Width:**
- Compact status panel is designed for 80 columns
- At 60-79 columns: truncate task names more aggressively (show last 10 chars minimum)
- Below 60 columns: switch to minimal view (icon + status only, no task names)

## 5. Parsing and Subprocess

### 5.1 JSONL Callback

AOM uses `ANSIBLE_STDOUT_CALLBACK=ansible.posix.jsonl` for reliable, structured output.

**Prerequisite Check:**
```
At startup, check if ansible.posix collection is installed:
  ansible-galaxy collection list | grep ansible.posix
  
If missing:
  - Prompt user: "ansible.posix collection not found. Install? [Y/n]"
  - If yes: ansible-galaxy collection install ansible.posix
  - If no: Exit with error and instructions
```

**Minimum Version Requirements:**
- AOM requires ansible-core >= 2.14 (for ansible.posix.jsonl callback support)
- Requires ansible.posix >= 1.5.0 (for JSONL callback with path field)

**Event Types:**

AOM receives 10 distinct JSONL event types from the ansible.posix.jsonl callback:

| Event | When Emitted | Strategy Scope |
|-------|--------------|-----------------|
| `v2_playbook_on_start` | Playbook begins | All |
| `v2_playbook_on_play_start` | Each play begins | All |
| `v2_runner_on_start` | Task starts on host | All strategies (emitted by StrategyBase._queue_task) |
| `v2_playbook_on_task_start` | Task starts | All strategies (once for linear, per-host for free) |
| `v2_playbook_on_handler_task_start` | Handler task starts | Lockstep |
| `v2_runner_on_ok` | Task succeeds on host | All |
| `v2_runner_on_failed` | Task fails on host | All |
| `v2_runner_on_skipped` | Task skipped on host | All |
| `v2_runner_on_unreachable` | Host unreachable | All |
| `v2_playbook_on_stats` | Playbook ends (PLAY RECAP) | All |

**Key Finding: Strategy Detection**

The JSONL callback plugin does **NOT** include the `strategy` field in the `v2_playbook_on_play_start` event. The `play.strategy` is used internally (`self._is_lockstep = play.strategy in LOCKSTEP_CALLBACKS`) but not serialized.

**Strategy Detection Approach:**

AOM detects the strategy by observing which task-start events arrive:

| Event Pattern | Strategy | Action |
|--------------|----------|--------|
| `v2_playbook_on_task_start` WITHOUT prior `v2_runner_on_start` for same task | Linear (lockstep) | Use task_start as task begin signal |
| `v2_runner_on_start` for each host | Free / host_pinned (non-lockstep) | Use runner_on_start as per-host begin signal |
| Both events received for same task | Mixed (uncommon) | Prefer `v2_runner_on_start` for per-host detail |

**Implementation: The first `v2_playbook_on_task_start` or `v2_runner_on_start` event after a `v2_playbook_on_play_start` determines the detected strategy for that play. Store as `PlayRunState.detected_strategy: str | None`, defaulting to None until first task event.**

**Note on Free/Host_Pinned Behavior:**
- `free` and `host_pinned` strategies emit `v2_playbook_on_task_start` **per host per task** (no deduplication), unlike `linear` which emits it once per task
- `v2_runner_on_start` is emitted by ALL strategies via the base `StrategyBase._queue_task()` method
- `serial` is a play-level keyword (batch size), NOT a separate strategy — it works with both `linear` and `free`

#### Event Structures

**1. v2_playbook_on_start**
```json
{
  "_event": "v2_playbook_on_start",
  "_timestamp": "2025-11-09T15:00:00.000000Z"
}
```
Emitted once when playbook execution begins. No playbook path in payload.

**2. v2_playbook_on_play_start**
```json
{
  "_event": "v2_playbook_on_play_start",
  "_timestamp": "2025-11-09T15:00:00.100000Z",
  "play": {
    "id": "uuid-here",
    "name": "Configure Webservers",
    "path": "/path/to/playbook.yml:1",
    "duration": { "start": "2025-11-09T15:00:00.100000Z" }
  }
}
```
Emitted once per play. Play IDs are UUIDs generated by Ansible's Play object (`play._uuid`). These use Ansible's internal UUID format (UUID v4 variant). Session IDs use UUIDv7 for time-ordering; play/task UUIDs from JSONL events use Ansible's format as-is.

**3. v2_runner_on_start (Non-Lockstep Only)**
```json
{
  "_event": "v2_runner_on_start",
  "_timestamp": "2025-11-09T15:00:00.200000Z",
  "hosts": {},
  "task": {
    "id": "task-uuid",
    "name": "Install nginx",
    "path": "/path/to/playbook.yml:7",
    "duration": { "start": "..." }
  }
}
```
Only emitted for free/host_pinned strategies. One event per host per task.

**4. v2_playbook_on_task_start (Lockstep Only)**
```json
{
  "_event": "v2_playbook_on_task_start",
  "_timestamp": "2025-11-09T15:00:00.200000Z",
  "task": {
    "id": "task-uuid",
    "name": "Install nginx",
    "path": "/path/to/playbook.yml:7",
    "duration": { "start": "..." }
  },
  "is_conditional": false,
  "uuid": "..."
}
```
Only emitted for linear/debug strategies. One event per task (all hosts).

**5. v2_playbook_on_handler_task_start (Lockstep Only)**
Same structure as `v2_playbook_on_task_start`, but for handler tasks triggered by `notify`.

**6. v2_runner_on_ok**
```json
{
  "_event": "v2_runner_on_ok",
  "_timestamp": "2025-11-09T15:00:00.300000Z",
  "task": {
    "id": "task-uuid",
    "name": "Install nginx",
    "path": "/path/to/playbook.yml:7",
    "duration": { "start": "...", "end": "..." }
  },
  "hosts": {
    "web1": {
      "changed": false,
      "action": "ansible.builtin.apt",
      "_ansible_no_log": false,
      "msg": "..."
    }
  }
}
```
Host result includes `changed` (bool), `action` (string), and optional `msg`.

**7. v2_runner_on_failed**
```json
{
  "_event": "v2_runner_on_failed",
  "_timestamp": "...",
  "task": { "id": "...", "name": "...", "path": "...", "duration": {...} },
  "hosts": {
    "web1": {
      "failed": true,
      "rc": 1,
      "cmd": ["/bin/false"],
      "msg": "non-zero return code",
      "stderr": "..."
    }
  }
}
```
Host result includes `failed: true`, `rc`, `cmd`, `msg`, and optionally `stderr`/`stdout`.

**8. v2_runner_on_skipped**
```json
{
  "_event": "v2_runner_on_skipped",
  "_timestamp": "...",
  "task": { "id": "...", "name": "...", "path": "...", "duration": {...} },
  "hosts": {
    "web1": {
      "skipped": true,
      "skip_reason": "Conditional result was False"
    }
  }
}
```
Host result includes `skipped: true` and `skip_reason`.

**9. v2_runner_on_unreachable**
```json
{
  "_event": "v2_runner_on_unreachable",
  "_timestamp": "...",
  "task": { "id": "...", "name": "...", "path": "...", "duration": {...} },
  "hosts": {
    "web1": {
      "unreachable": true,
      "msg": "SSH connection failed: Connection refused"
    }
  }
}
```
Host result includes `unreachable: true` and error `msg`.

**10. v2_playbook_on_stats (PLAY RECAP)**
```json
{
  "_event": "v2_playbook_on_stats",
  "_timestamp": "...",
  "stats": {
    "web1": {
      "ok": 5,
      "changed": 2,
      "failures": 0,
      "skipped": 1,
      "unreachable": 0,
      "rescued": 0,
      "ignored": 0
    },
    "web2": { ... }
  },
  "custom_stats": {},
  "global_custom_stats": {}
}
```
Final event with per-host aggregate statistics. Matches PLAY RECAP output.

**Timestamp Convention:**
- All `_timestamp` values from JSONL events are ISO 8601 UTC (e.g., `"2025-11-09T15:00:00.100000Z"`)
- AOM stores timestamps as-is (UTC) in session artifacts
- Display converts to local timezone using `datetime.fromisoformat(ts).astimezone()`
- Elapsed time is calculated as `now - start_time` in UTC, displayed as `HH:MM:SS`

### 5.2 Pre-Parse Phase

Before execution, AOM runs TWO discovery commands in parallel:

```python
# Both run concurrently during LOADING_TASKS phase:
# 1. ansible-playbook playbook.yml --list-tasks   → task tree structure
# 2. ansible-playbook playbook.yml --list-hosts  → resolved hostnames per play

import asyncio

async def pre_parse(playbook: Path, inventory_args: list[str]) -> PreParseResult:
    """Run --list-tasks and --list-hosts in parallel."""
    base_cmd = ['ansible-playbook', str(playbook)] + inventory_args
    
    tasks_proc = await asyncio.create_subprocess_exec(
        *base_cmd, '--list-tasks',
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    hosts_proc = await asyncio.create_subprocess_exec(
        *base_cmd, '--list-hosts',
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    
    tasks_out, _ = await tasks_proc.communicate()
    hosts_out, _ = await hosts_proc.communicate()
    
    return PreParseResult(
        plays=parse_list_tasks(tasks_out.decode()),
        play_hosts=parse_list_hosts(hosts_out.decode()),
    )
```

**Why both commands:**
- `--list-tasks` provides the task tree structure (plays, tasks, roles, tags)
- `--list-hosts` resolves host patterns to actual inventory hostnames
- Running in parallel minimizes startup overhead (both complete in ~same time)

**Fallback if `--list-hosts` fails:**
- If exit code non-zero or parse error: fall back to building host list incrementally from runner events
- Show warning: "Host resolution failed, hosts will appear as tasks execute"
- This covers edge cases like Jinja2 templates in `hosts:` field that need runtime variables

**Task Matching:**
- JSONL events include `task.id` (unique identifier)
- Pre-parse gives structure without IDs
- Match by position + name normalization during run
- Accept that some tasks may not match perfectly (conditionals)

**include_tasks Dynamic Expansion:**

When JSONL events arrive for tasks that don't match any `--list-tasks` entry (because `include_tasks` is NOT expanded in the pre-parse output), AOM creates new `TaskDefinition` nodes dynamically:

- **Parent relationship:** Dynamic tasks are children of the parent `include_tasks` node
- **Ordering:** `task_order = -1` (placed after pre-parsed siblings)
- **Flag:** `is_dynamic = True` (marks runtime-created definitions)
- **Role grouping:** Applies to dynamic tasks the same as pre-parsed tasks

```python
# Dynamic TaskDefinition creation during RUNNING:
if not matched_definition:
    dynamic_task = TaskDefinition(
        name=event_task_name,
        role=event_task_role,
        tags=[],
        play_id=parent_task.play_id,
        play_order=parent_task.play_order,
        task_order=-1,  # Sentinel for dynamic tasks
        is_dynamic=True
    )
    parent_task.children.append(dynamic_task)
```

### 5.2.1 --list-hosts Output Parsing

**Output Format:**

```
playbook: deploy.yml

  play #1 (webservers): Deploy web application	TAGS: []
    pattern: ['webservers']
    hosts (3):
      web1.example.com
      web2.example.com
      web3.example.com

  play #2 (dbservers): Deploy database	TAGS: []
    pattern: ['dbservers']
    hosts (2):
      db1.example.com
      db2.example.com
```

**Formatting details:**
- Play line format identical to `--list-tasks` (TAB separator before `TAGS:`)
- `pattern:` line shows the original hosts pattern (list syntax)
- `hosts (N):` line shows count
- Hostnames are 6-space indented, one per line
- No JSON output option (same as `--list-tasks`)

**Parser Implementation:**

```python
import re

LIST_HOSTS_PLAY_PATTERN = re.compile(
    r'^  play #(\d+) \(([^)]+)\): ([^\t]+)\tTAGS: \[([^\]]*)\]'
)

def parse_list_hosts(output: str) -> dict[int, list[str]]:
    """Parse --list-hosts output into {play_number: [hostnames]}.
    
    Returns a mapping of play sequence number to list of resolved hostnames.
    """
    result: dict[int, list[str]] = {}
    current_play: int | None = None
    current_hosts: list[str] = []
    past_header = False
    
    for line in output.splitlines():
        if match := LIST_HOSTS_PLAY_PATTERN.match(line):
            # Save previous play's hosts
            if current_play is not None:
                result[current_play] = current_hosts
            
            current_play = int(match.group(1))
            current_hosts = []
            past_header = True
            
        elif past_header and current_play is not None:
            stripped = line.strip()
            # Skip 'pattern:', 'hosts (N):', and 'tasks:' lines
            if stripped.startswith('pattern:') or stripped.startswith('hosts') or stripped.startswith('tasks:'):
                continue
            # Skip blank lines
            if not stripped:
                continue
            # Hostname line (6-space indent)
            if line.startswith('      ') and not line.strip().startswith('#'):
                current_hosts.append(stripped)
    
    # Save last play
    if current_play is not None:
        result[current_play] = current_hosts
    
    return result
```

**Edge Cases:**

| Scenario | Behavior |
|----------|----------|
| `hosts: localhost` | Returns `['localhost']` |
| `hosts: all` | Returns all inventory hosts |
| `hosts: webservers:!db_primary` | Returns filtered set (pattern resolved by Ansible) |
| `hosts: "{{ dynamic_group }}"` | Pattern NOT expanded — `--list-hosts` may fail. Fall back to runner events. |
| `--limit` applied | Pattern resolved, then limit applied (fewer hosts) |
| Empty inventory | `hosts (0):` — empty list |
| Dynamic inventory (AWS, etc.) | Works but may be slow (API calls during resolution) |

### 5.3 --list-tasks Output Parsing

**Critical Findings:**

The `ansible-playbook --list-tasks` command has specific output characteristics that AOM must handle:

1. **No JSON Output Option:**
   - `ansible-playbook --list-tasks` has **NO JSON output mode**
   - The `--json` flag **does not exist** for `--list-tasks`
   - `ANSIBLE_STDOUT_CALLBACK` has **NO effect** on `--list-tasks` output
   - Output is **always plain text** with TAB separators

2. **Exact Output Format:**

   ```
   playbook: <path>

     play #N (<hosts>): <name>\tTAGS: [<tags>]
       <role> : <task>\tTAGS: [<tags>]
   ```

   **Formatting details:**
   - Separator between task name and `TAGS:` is a **TAB character** (0x09), not spaces
   - Play indent: **exactly 2 spaces**
   - Task indent: **exactly 6 spaces**
   - Role prefix: `role_name : task_name` (space-colon-space)

3. **Playbook Header:**
   - First line is always: `playbook: <path>`
   - Followed by a blank line

4. **Play Format:**
   - Pattern: `play #N (<hosts>): <name>\tTAGS: [<tags>]`
   - The `\t` is a literal TAB character
   - `<hosts>` is the hosts pattern (e.g., `webservers`, `all`, `localhost`)

5. **Edge Cases:**

   | Scenario | Behavior |
   |----------|----------|
   | `include_tasks` | **NOT expanded** — shown as single task entry |
   | `import_tasks` | **IS expanded** — shown inline without prefix |
   | Blocks | **Flattened** — no block container shown in output |
   | `pre_tasks`/`post_tasks` | Appear as regular tasks (no prefix indicating type) |
   | Unnamed play/task | Uses hosts pattern or module name as fallback |
   | Output destination | ALL output goes to **stdout** (even warnings) |

6. **Exit Codes:**

   | Code | Meaning |
   |------|---------|
   | 0 | Success |
   | 1 | Error (missing role, missing file) |
   | 4 | Syntax error in playbook |

**Parser Implementation:**

```python
import re

# Play pattern: 2-space indent, "play #N", hosts in parens, name, TAB, TAGS
PLAY_PATTERN = re.compile(
    r'^  play #(\d+) \(([^)]+)\): ([^\t]+)\tTAGS: \[([^\]]*)\]'
)

# Task pattern: 6-space indent, optional role prefix, task name, TAB, TAGS
TASK_PATTERN = re.compile(
    r'^      (?:([^ ]+) : )?([^\t]+)\tTAGS: \[([^\]]*)\]'
)

def parse_list_tasks(output: str) -> list[PlayDefinition]:
    """Parse --list-tasks output into structured format."""
    plays = []
    for line in output.splitlines():
        if line.startswith('playbook:'):
            continue  # Skip header
        if match := PLAY_PATTERN.match(line):
            plays.append(PlayDefinition(
                id=match.group(1),
                hosts=match.group(2),
                name=match.group(3).strip(),
                tags=parse_tags(match.group(4)),
                tasks=[]
            ))
        elif match := TASK_PATTERN.match(line):
            role = match.group(1)  # None if no role prefix
            task_name = match.group(2).strip()
            tags = parse_tags(match.group(3))
            # Add to current play's task list
            # ...
    return plays
```

### 5.4 Role Grouping

When 5+ consecutive tasks share the same role, group them:

```
▼ ● Role: nginx (5 tasks)
  ● Install nginx
  ● Configure nginx
  ● Enable service
  ● Deploy config
  ● Verify
```

**Threshold:** Hard-coded at 5 for MVP.

### 5.5 PTY with pexpect

**Thread Worker Pattern:**

```python
@work(thread=True, exclusive=True)
def run_playbook(self, playbook: Path) -> None:
    worker = get_current_worker()
    
    child = pexpect.spawn(
        'ansible-playbook',
        [str(playbook)],
        encoding='utf-8',
        timeout=300,
        env={'ANSIBLE_STDOUT_CALLBACK': 'ansible.posix.jsonl', **os.environ}
    )
    
    while True:
        if worker.is_cancelled:
            child.sendintr()
            child.close()
            return
        
        try:
            index = child.expect([pexpect.EOF, '\n'], timeout=0.1)
            if index == 0:  # EOF
                break
            line = child.before.strip()
            self.app.call_from_thread(self.process_line, line)
        except pexpect.TIMEOUT:
            continue
```

### 5.6 PTY Stream Parsing Design

The PTY stream from `ansible-playbook` has three temporal phases that require different parsing strategies:

**Phase 1: PRE_RUN_PROMPTS**
- Password prompts, SSH key prompts appear
- NO JSONL events yet
- Non-JSON lines should be buffered for display
- Transition: detect `v2_playbook_on_start` event

**Phase 2: EXECUTION**
- JSONL events (primary stream)
- Warnings and deprecation messages may interleave
- Classify non-JSON lines as: plaintext output, password prompt, or malformed JSON

**Phase 3: POST_RUN_RECAP**
- `v2_playbook_on_stats` is the last JSONL event
- Optional plaintext PLAY RECAP may follow
- Process exits

**Implementation:**

```python
from enum import Enum, auto

class StreamPhase(Enum):
    PRE_RUN_PROMPTS = auto()  # Before v2_playbook_on_start
    EXECUTION = auto()       # JSONL events flowing
    POST_RUN_RECAP = auto()  # After v2_playbook_on_stats

class PtyStreamParser:
    def __init__(self):
        self.phase = StreamPhase.PRE_RUN_PROMPTS
        self._pending_password_prompt: str | None = None
        self._in_recap: bool = False
        self._recap_lines: list[str] = []
        self._warnings: list[WarningEntry] = []
        self._plaintext_lines: list[str] = []
        self._current_timestamp: datetime | None = None  # Updated on each event
    
    def feed_line(self, line: str) -> list[dict]:
        """Parse a line and return zero or more events."""
        events = []
        
        if self.phase == StreamPhase.PRE_RUN_PROMPTS:
            if self._is_jsonl_start_event(line):
                self.phase = StreamPhase.EXECUTION
                events.append(self._parse_json(line))
            else:
                # Buffer non-JSON (password prompts, warnings)
                self._handle_plaintext(line)
        
        elif self.phase == StreamPhase.EXECUTION:
            if self._is_jsonl_stats_event(line):
                events.append(self._parse_json(line))
                self.phase = StreamPhase.POST_RUN_RECAP
            elif self._is_json(line):
                events.append(self._parse_json(line))
            else:
                # Interleaved plaintext
                self._handle_plaintext(line)
        
        elif self.phase == StreamPhase.POST_RUN_RECAP:
            # Plaintext PLAY RECAP or process exit
            self._handle_recap_output(line)
        
        return events

    # Plaintext classification patterns
    PASSWORD_PATTERNS = [
        r'Vault password: ',
        r'Vault password \([^)]+\): ',
        r'SSH password: ',
        r'BECOME password: ',
        r'BECOME password\[defaults to SSH password\]: ',
        r'New Vault password: ',
        r'Confirm New Vault password: ',
    ]
    RECAP_PATTERN = re.compile(r'^PLAY RECAP \*{5,}')
    WARNING_PATTERNS = [
        r'^\[WARNING\]:',
        r'^\[DEPRECATION WARNING\]:',
        r'^\[DEPRECATED\]:',
    ]
    
    def _handle_plaintext(self, line: str) -> None:
        """Classify and handle non-JSON lines from PTY stream.
        
        Lines are classified into:
        - Password prompts: Routed to password handler
        - PLAY RECAP: Collected separately (Phase 3)
        - Warnings/deprecations: Displayed in log panel
        - Other: Displayed in log panel as-is
        """
        # Check for password prompt
        if any(re.search(p, line) for p in self.PASSWORD_PATTERNS):
            self._pending_password_prompt = line
            return
        
        # Check for PLAY RECAP
        if self.RECAP_PATTERN.match(line):
            self._in_recap = True
        
        if self._in_recap:
            self._recap_lines.append(line)
            return
        
        # Check for warnings and classify type
        if any(re.search(p, line) for p in self.WARNING_PATTERNS):
            # Determine if this is a deprecation or regular warning
            is_deprecation = bool(
                re.search(r'^\[DEPRECATION WARNING\]:', line) or
                re.search(r'^\[DEPRECATED\]:', line)
            )
            self._warnings.append(WarningEntry(
                type=WarningType.DEPRECATION if is_deprecation else WarningType.WARNING,
                message=line,
                timestamp=self._current_timestamp,
                source="controller",  # PTY stream warnings come from controller
            ))
        
        # All other plaintext: emit to log
        self._plaintext_lines.append(line)
```

### 5.10 Password Prompt Handling

**PTY Integration:**
- pexpect spawns process with PTY (pseudo-terminal)
- Ansible's `getpass` reads from `/dev/tty`
- PTY makes this work transparently
- AOM intercepts prompt on pexpect stream before it reaches terminal

**Password Prompt Patterns:**
```python
PASSWORD_PATTERNS = [
    r'Vault password: ',
    r'Vault password \([^)]+\): ',     # vault_id variant
    r'SSH password: ',
    r'BECOME password: ',
    r'BECOME password\[defaults to SSH password\]: ',
    r'New Vault password: ',
    r'Confirm New Vault password: ',
]
```

#### Compact Mode (ANSI Renderer)

The compact mode handles password prompts differently from TUI mode, using terminal pass-through:

**Approach:**
1. Detect password prompt via pexpect regex matching on PTY stream
2. **Pause ANSI rendering**: Stop Rich Live display, halt cursor manipulation
3. **Pass through to terminal**: Let the pexpect subprocess prompt appear directly on the actual terminal
4. User types password directly (Ansible's `getpass` handles masking via `/dev/tty which works in PTY mode)
5. **Resume rendering** after password is entered

**Implementation:**
```python
# In ANSI renderer:
def handle_password_prompt(self, prompt_text: str, child: pexpect.spawn) -> str:
    # 1. Stop the Rich Live display
    self.live.stop()
    
    # 2. Move cursor to bottom of screen for prompt
    sys.stdout.write('\033[999;0H')  # Move to bottom
    sys.stdout.flush()
    
    # 3. Let pexpect handle the prompt (reads from PTY)
    child.sendline('')  # Trigger prompt display
    
    # 4. Wait for password entry (getpass handles masking)
    # pexpect will capture the input
    
    # 5. Resume Rich Live display
    self.live.start()
    
    return password
```

**Why pass-through works:**
- PTY acts as a virtual terminal for the subprocess
- When we stop our ANSI rendering, the subprocess can write directly to the real terminal
- User sees the actual password prompt from Ansible (not a simulated one)
- Masking is handled by Ansible's `getpass` module

#### TUI Mode (Textual Frontend)

TUI mode uses Textual's modal capabilities:

**Approach:**
1. Detect password prompt via pexpect regex
2. Signal main thread via `call_from_thread`
3. Show Textual `Input(password=True)` modal
4. Block worker thread until user responds
5. Send password to PTY

**Implementation:**
```python
# In Textual worker:
if detected_password_prompt:
    event = threading.Event()
    result = {}
    self.app.call_from_thread(self.show_password_modal, prompt, event, result)
    event.wait(timeout=60)  # Block until user responds
    password = result.get('password', '')
    child.sendline(password)
```

**Modal using `app.suspend()`:**
```python
async def show_password_modal(self, prompt: str) -> str:
    """Show password modal, suspending TUI temporarily."""
    # Use Textual's Input widget with password=True
    # Or use app.suspend() to temporarily return terminal control
    pass
```

#### Backend-Specific Behavior

| Aspect | Compact (ANSI) | TUI (Textual) |
|--------|----------------|---------------|
| Detection | pexpect regex | pexpect regex |
| User interface | Terminal pass-through | Textual modal |
| Masking | Ansible `getpass` | Textual `Input(password=True)` |
| Rendering pause | Stop Rich Live | Suspend app or overlay modal |
| Timeout | 60s default | 60s default |

**Per-host prompts.** `ansible.builtin.pause` bypasses the host loop and prompts
once per batch. For per-host confirmation use `serial: 1` (AOM forwards each
host's prompt sequentially) or the `aom.interactive.confirm` action plugin. AOM
emits a startup warning when a per-host prompt is found in a non-serial
multi-host play.

The `aom.interactive.confirm` action plugin provides per-host prompts regardless
of strategy. It does not bypass the host loop, so ansible runs it once per host;
under AOM it exchanges a prompt request and answer over a FIFO control channel
(`AOM_PROMPT_CONTROL_DIR`), and falls back to stdin when run without AOM. Aborting
a host (`no`/`abort`) fails only that host; other hosts proceed.

### 5.8 Host Name Resolution

AOM resolves host patterns to actual inventory hostnames using `--list-hosts` during the LOADING_TASKS phase. This provides the complete host list BEFORE execution begins.

**Resolution Flow:**

```
STARTUP
  ├── ansible-playbook --list-tasks  (parallel)  → TaskDefinition tree
  ├── ansible-playbook --list-hosts   (parallel)  → PlayDefinition.resolved_hosts
  └── BOTH COMPLETE → READY state

EXECUTION
  ├── Runner events arrive → Cross-check resolved_hosts
  └── Any NEW hosts not in resolved_hosts? → Append with WARNING log

POST-RUN
  └── v2_playbook_on_stats → Final cross-check of host lists
```

**Data Flow:**

1. `--list-hosts` populates `PlayDefinition.resolved_hosts: list[str]` during LOADING_TASKS
2. When runner events arrive, hostnames are matched against `resolved_hosts`
3. If a hostname appears in a runner event but NOT in `resolved_hosts`:
   - Still create `HostRunState` for the host
   - Log WARNING: "Host {hostname} not in pre-resolved list, may be from dynamic inventory"
   - Append to `resolved_hosts`
4. `v2_playbook_on_stats` provides final cross-check — missing hosts are logged

**Fallback (if --list-hosts fails):**

- Build host list incrementally from runner events (as in v1.5 behavior)
- Show warning: "Host pre-resolution failed, hosts will appear as tasks execute"
- `PlayDefinition.resolved_hosts` starts empty, populated as runner events arrive

### 5.9 Password/Secret Redaction

AOM implements **defense-in-depth** secret redaction. Even when playbook authors forget `no_log: true`, AOM attempts to prevent secrets from appearing in logs and display.

**Why this is needed:**
- `no_log: true` is opt-in — authors must remember to set it
- Vault-decrypted values can appear in verbose mode (`-vvv`) via `invocation.module_args`
- Modules may echo credentials in `stdout`/`stderr`/`cmd` fields
- Loops may contain per-item secrets

**Redaction Layers (in order of priority):**

#### Layer 1: Trust `_ansible_no_log` Flag

If `res._ansible_no_log == True` in a JSONL event, AOM replaces the entire result:

```python
# In event processor:
if result.get('_ansible_no_log', False):
    event['res'] = {'censored': '(no_log)'}
```

Loop items are checked individually:
```python
for i, item in enumerate(result.get('results', [])):
    if isinstance(item, dict) and item.get('_ansible_no_log', False):
        result['results'][i] = {'censored': '(no_log)'}
```

#### Layer 2: Pattern-Match Password Fields

AOM uses Ansible's own `PASSWORD_MATCH` regex to detect password field names:

```python
import re

# Ansible's password detection regex (from ansible.module_utils.basic)
PASSWORD_MATCH = re.compile(
    r'^(?:.+[-_\s])?pass(?:[-_\s]?(?:word|phrase|wrd|wd)?)(?:[-_\s].+)?$',
    re.IGNORECASE
)

# Known Ansible connection password fields
ANSIBLE_PASSWORD_FIELDS = frozenset({
    'ansible_ssh_pass', 'ansible_password',
    'ansible_become_pass', 'ansible_become_password',
    'ansible_vault_password',
})

# Common generic secret field names
GENERIC_SECRET_FIELDS = frozenset({
    'api_key', 'api_token', 'secret', 'secret_key',
    'token', 'auth_token', 'access_token', 'private_key',
    'credential', 'credentials',
})
```

When a JSONL result event contains a dict with a key matching these patterns:
- The **value** is replaced with `********` (8 asterisks)
- This applies recursively to nested dicts and lists

```python
REDACTED = '********'

def redact_dict(data: dict, depth: int = 0) -> dict:
    """Recursively redact password fields in a dictionary."""
    if depth > 10 or not isinstance(data, dict):
        return data
    result = {}
    for key, value in data.items():
        key_lower = key.lower()
        if (key_lower in ANSIBLE_PASSWORD_FIELDS
            or key_lower in GENERIC_SECRET_FIELDS
            or PASSWORD_MATCH.match(key_lower)):
            result[key] = REDACTED
        elif isinstance(value, dict):
            result[key] = redact_dict(value, depth + 1)
        elif isinstance(value, list):
            result[key] = [redact_dict(x, depth + 1) if isinstance(x, dict) else x for x in value]
        else:
            result[key] = value
    return result
```

**Whitelist for False Positives:**

Ansible's regex is broad (`pass` matches `passenger_version`, `bypass`, etc.). AOM provides a configurable whitelist:

```python
# Default whitelist — field names containing "pass" that are NOT passwords
PASSWORD_WHITELIST = frozenset({
    'passenger_version', 'passenger_pool', 'bypass', 'overpass',
    'compass', 'underpass', 'passport_number',
})

def should_redact(key: str) -> bool:
    key_lower = key.lower()
    if key_lower in PASSWORD_WHITELIST or key_lower in config.redaction.whitelist:
        return False
    return (key_lower in ANSIBLE_PASSWORD_FIELDS
            or key_lower in GENERIC_SECRET_FIELDS
            or PASSWORD_MATCH.match(key_lower) is not None)
```

#### Layer 3: Sanitize Command Strings

Commands and output strings may contain inline credentials. AOM applies regex sanitization:

```python
# URL-style credentials: protocol://user:password@host
URL_CRED_PATTERN = re.compile(
    r'([a-zA-Z]+://[^:]+:)([^@]+)(@)',
)

# CLI --password=xxx, --token=xxx, --secret=xxx
CLI_CRED_PATTERN = re.compile(
    r'(--(?:password|pass|pwd|token|secret|key|api-key)\s*[=: ]+)\S+',
    re.IGNORECASE,
)

def sanitize_string(s: str) -> str:
    """Sanitize credentials in command/output strings."""
    s = URL_CRED_PATTERN.sub(r'\1********\3', s)
    s = CLI_CRED_PATTERN.sub(r'\1********', s)
    return s
```

Applied to: `res.cmd`, `res.stdout`, `res.stderr`, `res.msg` fields.

#### Layer 4: Verbose Mode `invocation` Sanitization

At `-vvv` verbosity, Ansible includes `invocation.module_args` in result events. AOM redacts this recursively:

```python
if 'invocation' in result and 'module_args' in result['invocation']:
    result['invocation']['module_args'] = redact_dict(result['invocation']['module_args'])
```

#### Redaction Scope (Where It Applies)

| Output | Redacted? | Notes |
|--------|-----------|-------|
| Compact display | ✅ Yes | Secret values replaced with `********` |
| TUI display (tree/log/summary) | ✅ Yes | Secret values replaced with `********` |
| Inspect CLI output | ✅ Yes | Secret values replaced with `********` |
| Inspect `--json` output | ✅ Yes | Secret values replaced with `********` |
| Session artifact (`.aom` file) | ✅ Yes | Artifacts are always redacted — no opt-out |

**Note:** Redaction is always active. There is no `--no-redact` flag. Secrets are protected by design in all output paths. If debugging requires raw data, users should run `ansible-playbook` directly without AOM.

**Redaction Configuration:**

```yaml
# ~/.config/aom/config.yaml
redaction:
  whitelist:                      # Field names to NOT redact (false positive prevention)
    - passenger_version
    - bypass
  custom_fields:                  # Additional field names to redact
    - my_secret_var
    - db_connection_string
  custom_patterns:                 # Additional regex patterns to redact in strings
    - regex: '--db-password=\S+'
      replacement: '--db-password=********'
```

**Note:** There is no `enabled` switch — redaction is always active by design.

**Corresponding Pydantic model:**

```python
class RedactionConfig(BaseModel):
    whitelist: list[str] = Field(default_factory=lambda: list(PASSWORD_WHITELIST))
    custom_fields: list[str] = Field(default_factory=list)
    custom_patterns: list[dict[str, str]] = Field(default_factory=list)

class AppConfig(BaseSettings):
    # ... existing fields ...
    redaction: RedactionConfig = Field(default_factory=RedactionConfig)
```

---

## 6. State Management

### 6.1 Data Models

AOM uses a **dual-track architecture** with separate Definition and State classes:

**Definition classes** (from `--list-tasks`):
- Immutable, pre-execution data
- Created during `LOADING_TASKS` state
- Represent the static playbook structure

**State classes** (from JSONL events):
- Runtime data, mutable during execution
- Created/updated during `RUNNING` state
- Track live execution progress

**Task Matching Strategy:**

When JSONL events arrive, AOM matches them to `TaskDefinition` nodes via three phases:

1. **Primary: UUID matching** — Match by `task.id` from JSONL event (most reliable)
2. **Secondary: Path matching** — Match by `task.path` (file:line format)
3. **Fallback: Sequential + name** — Match by `play_order`, `task_order`, and normalized name

**Definition classes include ordering fields:**

```python
@dataclass
class TaskDefinition:
    """Static task info from --list-tasks."""
    name: str
    role: str | None
    tags: list[str]
    play_id: str
    play_order: int      # 0-indexed play position (for sequential matching)
    task_order: int      # 0-indexed task position within play, or -1 for dynamic tasks
    is_dynamic: bool = False  # True if created at runtime from include_tasks expansion
    uuid: str | None = None  # Task UUID from JSONL events (available after matching)
    path: str | None = None  # Task path in file:line format (available after matching)
    children: list[TaskDefinition] = field(default_factory=list)  # Dynamic child tasks from include_tasks
```

@dataclass
class RoleGroupDefinition:
    """Grouped role tasks."""
    role: str
    tasks: list[TaskDefinition]
    
    @property
    def name(self) -> str:
        return f"Role: {self.role} ({len(self.tasks)} tasks)"

@dataclass
class PlayDefinition:
    """Static play info from --list-tasks and --list-hosts."""
    id: str                    # Sequential number from --list-tasks (e.g., "1", "2")
    name: str                  # Play name from --list-tasks
    hosts: str                 # Host pattern (e.g., "webservers") — NOT resolved hostnames
    resolved_hosts: list[str] = field(default_factory=list)  # Actual hostnames from --list-hosts
    tasks: list[TaskDefinition | RoleGroupDefinition] = field(default_factory=list)
    # Note: JSONL events use UUIDs for play.id. The matching uses
    # sequential position (play_order) to map definitions to states.
    # resolved_hosts is populated during LOADING_TASKS from --list-hosts.
    # Falls back to empty list if --list-hosts fails; populated by runner events.

class Status(Enum):
    PENDING = "pending"
    RUNNING = "running"
    OK = "ok"
    CHANGED = "changed"
    FAILED = "failed"
    SKIPPED = "skipped"
    UNREACHABLE = "unreachable"

class WarningType(Enum):
    WARNING = "warning"
    DEPRECATION = "deprecation"

@dataclass
class WarningEntry:
    """A classified warning or deprecation from the PTY stream."""
    type: WarningType
    message: str
    timestamp: datetime | None = None
    source: str = ""  # "controller" or "task_result"

@dataclass
class HostRunState:
    hostname: str
    status: Status
    changed: bool = False
    message: str = ""
    start_time: datetime | None = None
    end_time: datetime | None = None

@dataclass
class TaskRunState:
    task_id: str
    name: str
    status: Status = Status.PENDING
    hosts: dict[str, HostRunState] = field(default_factory=dict)
    start_time: datetime | None = None
    end_time: datetime | None = None

@dataclass
class PlayRunState:
    play_id: str
    name: str
    status: Status = Status.PENDING
    tasks: dict[str, TaskRunState] = field(default_factory=dict)
    detected_strategy: str | None = None  # Detected from first task event: "linear" or "free"

@dataclass
class RunState:
    """Complete execution state."""
    playbook: str
    plays: dict[str, PlayRunState] = field(default_factory=dict)
    definitions: list[PlayDefinition] = field(default_factory=list)
    start_time: datetime | None = None
    end_time: datetime | None = None
    status: Status = Status.PENDING
```

### 6.2 Event Processing

```python
class RunState:
    def handle_event(self, event: dict) -> None:
        event_type = event.get("_event", "")
        timestamp = datetime.fromisoformat(event.get("_timestamp", ""))
        
        handler = getattr(self, f"_handle_{event_type}", None)
        if handler:
            handler(event, timestamp)
    
    def _handle_v2_runner_on_start(self, event: dict, ts: datetime) -> None:
        task_id = event["task"]["id"]
        task_name = event["task"]["name"]
        play_id = event.get("play", {}).get("id", "")
        
        # Find or create task state
        # Set status to RUNNING
        # Record start time

    def _handle_v2_runner_on_ok(self, event: dict, ts: datetime) -> None:
        task_id = event["task"]["id"]
        hosts = event.get("hosts", {})
        
        for hostname, result in hosts.items():
            # Create HostRunState
            # Set status, changed, message
            # Record end time

    def _handle_v2_playbook_on_start(self, event: dict, ts: datetime) -> None:
        """Handle playbook start event."""
        self.start_time = ts
        self.status = Status.RUNNING

    def _handle_v2_playbook_on_play_start(self, event: dict, ts: datetime) -> None:
        """Handle new play event. Create PlayRunState, detect strategy."""
        play_data = event.get("play", {})
        play_id = play_data.get("id", "")
        play_name = play_data.get("name", "")
        self.plays[play_id] = PlayRunState(
            play_id=play_id,
            name=play_name,
            status=Status.RUNNING
        )

    def _handle_v2_playbook_on_task_start(self, event: dict, ts: datetime) -> None:
        """Handle task start (lockstep). Detect strategy on first task event."""
        task_data = event.get("task", {})
        task_id = task_data.get("id", "")
        play_id = event.get("play", {}).get("id", "")
        if play_id in self.plays:
            self.plays[play_id].detected_strategy = "linear"  # First task_start implies lockstep

    def _handle_v2_playbook_on_handler_task_start(self, event: dict, ts: datetime) -> None:
        """Handle handler task start."""
        task_data = event.get("task", {})
        # Same logic as task_start but mark as handler
        task_id = task_data.get("id", "")

    def _handle_v2_runner_on_start(self, event: dict, ts: datetime) -> None:
        """Handle runner start (non-lockstep). Detect strategy on first runner event."""
        task_id = event["task"]["id"]
        # If no strategy detected yet, this confirms non-lockstep
        for play in self.plays.values():
            if play.detected_strategy is None:
                play.detected_strategy = "free"

    def _handle_v2_runner_on_failed(self, event: dict, ts: datetime) -> None:
        """Handle task failure on host."""
        task_id = event["task"]["id"]
        hosts = event.get("hosts", {})
        for hostname, result in hosts.items():
            # Check ignore_errors flag
            ignore_errors = result.get("_ansible_verbose_always", {}).get("ignore_errors", False)
            status = Status.FAILED if not ignore_errors else Status.OK
            # Create/update HostRunState

    def _handle_v2_runner_on_skipped(self, event: dict, ts: datetime) -> None:
        """Handle task skipped on host."""
        task_id = event["task"]["id"]
        hosts = event.get("hosts", {})
        for hostname, result in hosts.items():
            # Create HostRunState with Status.SKIPPED

    def _handle_v2_runner_on_unreachable(self, event: dict, ts: datetime) -> None:
        """Handle unreachable host."""
        task_id = event["task"]["id"]
        hosts = event.get("hosts", {})
        for hostname, result in hosts.items():
            # Create HostRunState with Status.UNREACHABLE
            # Mark play as having unreachable hosts

    def _handle_v2_playbook_on_stats(self, event: dict, ts: datetime) -> None:
        """Handle final STATS event. Cross-check with collected state."""
        self.end_time = ts
        stats = event.get("stats", {})
        # Cross-check: compare stats hostnames with HostRunStates collected
        # Any missing hosts → mark as unreachable
        # Set final status based on failures
        if any(h.status == Status.FAILED for p in self.plays.values() for t in p.tasks.values() for h in t.hosts.values()):
            self.status = Status.FAILED
        else:
            self.status = Status.COMPLETED
```

### 6.3 Session Recording

**Directory Structure (during run):**
```
~/.local/state/aom/sessions/{uuidv7}/
├── events.jsonl      # All JSONL events
├── stderr.log        # Captured stderr
└── meta.json         # Session metadata
```

**Artifact Format (after completion):**
```
~/.local/state/aom/artifacts/{uuidv7}.aom
```

A single JSONL file with metadata header:
```jsonl
{"type": "metadata", "playbook": "site.yml", "version": "1.0", "created": "2026-04-20T10:00:00Z"}
{"type": "event", "_event": "v2_playbook_on_start", ...}
{"type": "event", "_event": "v2_playbook_on_play_start", ...}
...
{"type": "stats", "ok": 45, "changed": 12, "failed": 0, ...}
```

**Rotation Policy:**
- Keep last 100 sessions OR last 30 days (configurable)
- Cleanup on each run

**File Permissions:**
- Session files are created with mode 0o644 (world-readable)
- Artifact files (.aom) are created with mode 0o600 (user-only) as they may contain sensitive playbook names

**Corrupted Session Handling:**
- If a .jsonl artifact is truncated or contains malformed JSON, AOM skips the malformed line and logs a WARNING
- The inspect command shows a note: "(N malformed lines skipped)"

### 6.4 Execution State Machine

AOM manages playbook execution through an 8-state machine:

```
States: IDLE, STARTING, LOADING_TASKS, READY, RUNNING, COMPLETED, FAILED, CRASHED
```

**State Diagram:**
```
                                     ┌──────────┐
                                     │  IDLE    │
                                     └────┬─────┘
                                          │ user runs aom
                                          ▼
                                     ┌──────────┐
                           ┌────────│ STARTING │◄──────────────┐
                           │        └────┬─────┘               │
                           │             │ start playbook      │
                           │             ▼                     │
                           │        ┌──────────┐               │
               (error)     │        │ LOADING_ │               │
             ┌─────────────┼───────►│  TASKS   │               │
             │             │        └────┬─────┘               │
             │             │             │ --list-tasks OK    │
             │             │             ▼                     │
             │             │        ┌──────────┐               │
             │             │        │  READY   │──(timeout)────┤
             │             │        └────┬─────┘               │
             │             │             │ playbook starts    │
             │             │             ▼                     │
             │             │        ┌──────────┐               │
             │             │        │ RUNNING  │──(error)──────┤
             │             │        └────┬─────┘               │
             │             │             │ v2_playbook_on_stats
             │             │             ▼                     │
             │             │        ┌──────────┐               │
             │             │        │COMPLETED │───────────────┘
             │             │        └──────────┘    reset
             │             │
             │             │       (v2_runner_on_failed, ignore_errors=false)
             │             │       OR (v2_runner_on_unreachable)
             │             │             ▼
             │             │        ┌──────────┐
             └──────────────┼──────►│  FAILED  │
                           │        └──────────┘
                           │
                           │       (subprocess crash, JSON parse error)
                           │             ▼
                           │        ┌──────────┐
                           └───────►│ CRASHED  │
                                    └──────────┘
```

**Transition Table:**

| From | To | Trigger |
|------|----|---------|
| IDLE | STARTING | User runs `aom <playbook>` |
| STARTING | LOADING_TASKS | Begin `--list-tasks` discovery |
| LOADING_TASKS | READY | `--list-tasks` succeeds, tree built |
| LOADING_TASKS | CRASHED | `--list-tasks` fails (invalid playbook, etc.) |
| READY | RUNNING | `ansible-playbook` subprocess starts |
| RUNNING | COMPLETED | `v2_playbook_on_stats` received, no failures |
| RUNNING | FAILED | `v2_runner_on_failed` (ignore_errors=false) or `v2_runner_on_unreachable` |
| RUNNING | CRASHED | Subprocess crash (signal, EOF unexpected, JSON parse error) |
| COMPLETED/FAILED/CRASHED | IDLE | User exits AOM or re-runs |

**State Implementation:**
```python
from enum import Enum, auto

class RunState(Enum):
    IDLE = auto()          # Initial state, no execution
    STARTING = auto()      # Command invoked, initializing
    LOADING_TASKS = auto() # Running --list-tasks discovery
    READY = auto()         # Discovery complete, tasks loaded
    RUNNING = auto()       # Live playbook execution
    COMPLETED = auto()     # Successful completion
    FAILED = auto()        # Task failure or unreachable
    CRASHED = auto()       # Unexpected error

VALID_TRANSITIONS = {
    RunState.IDLE: {RunState.STARTING},
    RunState.STARTING: {RunState.LOADING_TASKS, RunState.CRASHED},
    RunState.LOADING_TASKS: {RunState.READY, RunState.CRASHED},
    RunState.READY: {RunState.RUNNING, RunState.IDLE},
    RunState.RUNNING: {RunState.RUNNING, RunState.COMPLETED,
                      RunState.FAILED, RunState.CRASHED},
    RunState.COMPLETED: {RunState.IDLE},
    RunState.FAILED: {RunState.IDLE},
    RunState.CRASHED: {RunState.IDLE},
}
```

### 6.5 Memory Bounds

**State Tree Limits:**
- Maximum plays: 1000 (practical upper bound; typical playbooks have <50)
- Maximum tasks per play: 10,000 (practical upper bound; typical <500)
- Maximum hosts per task: 10,000 (practical upper bound; typical <100)
- Maximum total HostRunState entries: 1,000,000 (memory limit safeguard)
- If limits are exceeded: log WARNING, stop tracking individual hosts but continue playbook execution
- Log panel `max_lines`: 50,000 (configurable)

---

## 7. TUI Components

### 7.1 Tree View (Full TUI)

**Structure:**
```
Root
└── Play
    └── RoleGroup (optional, when 5+ consecutive same-role tasks)
        └── Task
            └── Host
```

**Navigation:**
- `↑/↓`: Move selection
- `→`: Expand node
- `←`: Collapse node
- `Enter`: Toggle expand/collapse

**Rendering:**
- Use Textual's built-in `Tree` widget
- Custom TreeNode classes for each type
- Reactive updates via state changes

**Task Name Truncation:**
- If task name exceeds available column width, truncate with `…` (U+2026)
- Minimum visible characters: 10 (plus `…`)
- Priority: show role name over task name if both are long
- In compact mode status panel: hard-truncate at terminal width minus 20 chars (for status icons)

### 7.2 Log Panel (Full TUI)

**Implementation:**
- Based on `RichLog` widget
- `max_lines=50000` for memory bounds
- Smart auto-scroll (pause when scrolled up)

**Content Handling:**
```python
def append_line(self, line: str):
    if line.strip().startswith('{'):
        try:
            event = json.loads(line)
            self._write_event(event)
            return
        except json.JSONDecodeError:
            pass
    # Raw text with ANSI colors
    text = Text.from_ansi(line)
    self.write(text, scroll_end=self.is_vertical_scroll_end())
```

**Search (Ctrl+F):**
- Search bar overlay at top
- Plain text + regex mode
- Case-sensitive toggle
- Match highlighting
- F3/Shift+F3 navigation

### 7.3 Summary Panel (Full TUI)

**Contents:**
- Current play name
- Hosts completed/total
- Tasks completed/total
- Elapsed time (HH:MM:SS)
- Per-host status breakdown

### 7.4 Status Bar (Full TUI, Configurable)

**Available Elements:**
- Playbook name
- Current play
- Elapsed time
- Total tasks / completed tasks
- Current task name
- Host count
- Per-host progress indicators
- Subprocess PID
- Memory usage
- Activity ticker

**Configuration:**
```yaml
status_bar:
  - playbook_name
  - elapsed_time
  - task_progress
  - current_task
  - memory_usage
```

### 7.5 Debug Panel (Full TUI)

**Shows:**
- Command and env overrides
- Event count
- Parsing errors
- Callback status
- Timing stats
- Subprocess PID
- Current state tree snapshot
- Pending events queue
- Memory usage (RSS/VSZ)
- Renderer FPS
- Event processing latency

**Toggle:** `D` key

### 7.6 Filter Panel (Full TUI)

**Key:** `f`

**Options:**
- Status checkboxes: OK, Changed, Failed, Skipped, Unreachable, Running, Pending
- Warning checkboxes: Warning, Deprecation
- Text filter for task names
- Host filter

**Deprecation Filtering:**

Deprecation warnings from Ansible are **not** emitted as JSONL callback events. They appear as plaintext lines on stderr in two formats:
- `[DEPRECATION WARNING]: <message>` — Active deprecation warnings
- `[DEPRECATED]: <message>` — Already-removed features

AOM classifies these into `WarningEntry` objects with `WarningType.WARNING` or `WarningType.DEPRECATION`. The filter panel provides checkboxes to show/hide each type independently.

In compact mode, the status line displays warning and deprecation counts:
```
site.yml │ 3/10 hosts │ ⚠ 2 ✱ 1 │ 0:05:23
```
Where ⚠ is the warning count and ✱ is the deprecation count.

---

## 8. Configuration

### 8.1 Config File

**Path:** `~/.config/aom/config.yaml` (XDG-compliant)

**First Run Behavior:**
- Create config with all settings commented out
- User can uncomment to override defaults

**Schema:**

```yaml
# Status bar configuration
status_bar:
  elements:
    - playbook_name
    - elapsed_time
    - task_progress
    # - current_task
    # - memory_usage
    # - subprocess_pid

# Panel defaults
panels:
  tree_width: 40        # percentage
  summary_height: 30    # percentage
  
# Keybindings (override defaults)
keybindings:
  quit: "q"
  search: "ctrl+f"
  expand: "right"
  collapse: "left"

# Log settings
log:
  max_lines: 50000
  auto_scroll: true

# Session storage
session:
  storage_dir: "~/.local/state/aom"
  keep_sessions: 100
  keep_days: 30

# Secret redaction
redaction:
  enabled: true
  whitelist:
    - passenger_version
    - bypass
  custom_fields: []
  custom_patterns: []

# Warning display
warnings:
  show_warnings: true
  show_deprecations: true

# Default ansible args
ansible:
  default_args: []
```

### 8.2 Validation

**Framework:** Pydantic + Pydantic Settings

```python
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

class StatusBarConfig(BaseModel):
    elements: list[str] = Field(default_factory=lambda: [
        "playbook_name", "elapsed_time", "task_progress"
    ])

class RedactionConfig(BaseModel):
    whitelist: list[str] = Field(default_factory=list)
    custom_fields: list[str] = Field(default_factory=list)
    custom_patterns: list[dict[str, str]] = Field(default_factory=list)

class WarningsConfig(BaseModel):
    show_warnings: bool = Field(default=True)
    show_deprecations: bool = Field(default=True)

class AppConfig(BaseSettings):
    status_bar: StatusBarConfig = Field(default_factory=StatusBarConfig)
    redaction: RedactionConfig = Field(default_factory=RedactionConfig)
    warnings: WarningsConfig = Field(default_factory=WarningsConfig)
    log_max_lines: int = Field(default=50000, ge=1000, le=100000)
    session_keep_count: int = Field(default=100, ge=1)
    session_keep_days: int = Field(default=30, ge=1)
    
    model_config = SettingsConfigDict(
        yaml_file="~/.config/aom/config.yaml"
    )
```

---

## 9. Session Inspection

### 9.1 Inspect Commands

**List Sessions:**
```bash
aom inspect list
```
Output: Table with session ID, playbook, date, status, duration

**Session ID Display Format:**
Session UUIDs are displayed as the first 8 characters in `aom inspect list` output (e.g., `01923abc...`), with full UUIDv7 available via `aom inspect <id>`.

**Show Session Summary:**
```bash
aom inspect <session-id>
```
Output: Full summary with play/task breakdown

**Filter Failed:**
```bash
aom inspect <session-id> --failed
```
Output: Only failed tasks

**Filter by Host:**
```bash
aom inspect <session-id> --host web1
```
Output: Tasks that ran on specified host

**Show Tree:**
```bash
aom inspect <session-id> --tree
```
Output: ASCII tree of plays/tasks with status icons

**Diff Sessions:**
```bash
aom inspect diff <id1> <id2>
```
Output: Table comparing task outcomes between runs

### 9.3 Session Diff Details

The `aom inspect diff` command compares two playbook runs to identify changes in task outcomes:

**Task Matching Strategy:**

Diff uses a silent hybrid matching approach to correlate tasks between runs. The matching method (UUID, path, or name) is determined automatically and not displayed to users:

1. **Primary: Task UUID** — Match by `task.uuid` (most reliable, from JSONL events). This is especially important because roles can be imported multiple times, creating multiple tasks with the same name.
2. **Fallback: Task Path** — Match by `task.path` (file:line format)
3. **Last Resort: Task Name** — Match by name (less reliable due to templating)

```python
def match_tasks(old_tasks, new_tasks):
    """Match tasks between sessions with silent fallback strategy."""
    # Try UUID match first (handles duplicate role imports)
    by_uuid = {t.uuid: t for t in old_tasks}
    matches = {}
    unmatched_new = []
    
    for task in new_tasks:
        if task.uuid in by_uuid:
            matches[task.uuid] = (by_uuid[task.uuid], task)
        else:
            unmatched_new.append(task)
    
    # Fallback to path matching for remaining
    # ... (implementation continues)
```

**Cross-Playbook Diff:**

When comparing sessions from different playbooks:
- If playbook names differ, display a **warning banner** at the top of the diff output
- **Proceed with the comparison** using whatever tasks can be matched by the matching strategy
- Clearly label unmatched tasks as "new" (only in current session) or "removed" (only in baseline session)

**Task Visibility:**

- **Default:** Show ALL tasks, including unchanged ones
- **`--changes-only` flag:** Filter to show only tasks with status changes (hide unchanged)

**Note on Comparing Playbook Source Code:**

AOM does NOT compare playbook source code. Comparing `.yml` files is what `git diff` is for. AOM compares **execution results** (task outcomes) across runs, not source changes.

**Diff Table Columns:**

| Column | Description |
|--------|-------------|
| Task | Task name |
| Baseline | Status from first session |
| Current | Status from second session |
| Classification | Change category |

**Classification Categories:**

| Category | Color | Meaning |
|----------|-------|---------|
| `regressed` | Red | Task failed in current (was ok/changed before) |
| `improved` | Green | Task succeeded in current (was failed before) |
| `changed` | Yellow | Status changed (e.g., ok → changed, skipped → ok) |
| `new` | Cyan | Task only exists in current session |
| `removed` | Dim | Task only exists in baseline session |
| `unchanged` | (no highlight) | Same status in both sessions |

**Duration Comparison:**

AOM does **NOT** compare task durations between runs. Duration deltas are noisy and don't meaningfully indicate problems. AOM focuses exclusively on **status changes** (ok, failed, changed, skipped, unreachable).

**Cleanup:**
```bash
aom inspect prune --days 30
```
Deletes sessions older than 30 days.

### 9.4 Output Formats

- Default: Rich tables (pipe-friendly)
- `--json`: Structured JSON output
- `--jsonl`: Raw event dump

---

## 10. Keybindings

### 10.1 Full Reference

| Key | Action | Context |
|-----|--------|---------|
| `q` | Quit (with confirmation) | Global |
| `Ctrl+C` (1st) | Forward to subprocess | Global |
| `Ctrl+C` (2nd) | Kill everything | Global |
| `↑` / `↓` | Navigate tree up/down | Tree focused |
| `→` | Expand tree node | Tree focused |
| `←` | Collapse tree node | Tree focused |
| `Tab` | Switch panel focus | Global |
| `Ctrl+F` | Open search in log | Log focused |
| `Ctrl+←/→` | Resize panel split | Global |
| `D` | Toggle debug panel | Global |
| `?` | Help overlay | Global |
| `S` | Settings screen | Global |
| `R` | Re-run with same args | Post-run |
| `Shift+R` | Re-run with modified args | Post-run |
| `f` | Open filter panel | Global |
| `Alt+T` | Cycle themes | Global |
| `1-5` | Toggle panels | Global |

### 10.2 Panel Toggle Keys

| Key | Panel |
|-----|-------|
| `1` | Status Bar |
| `2` | Tree View |
| `3` | Summary Panel |
| `4` | Log Panel |
| `5` | Footer |

---

## 11. Icons and Theming

### 11.1 Status Icons

Simple Unicode icons that work in most terminals:

| Status | Icon | Color |
|--------|------|-------|
| OK | `●` | Green |
| Changed | `◆` | Yellow |
| Failed | `✖` | Bold Red |
| Unreachable | `⊝` | Dim Red |
| Running | `◐ ◓ ◑ ◒` | Cyan (animated) |
| Pending | `□` | Dim |
| Skipped | `○` | Dim |

**Running Animation:**
Cycle through quadrant icons at 4 FPS: `◐ → ◓ → ◑ → ◒ → ◐`

### 11.2 Tree Icons

| Icon | Meaning |
|------|---------|
| `▶` | Collapsed node |
| `▼` | Expanded node |

### 11.3 Themes

**Built-in:** Dark, Light, Solarized, Monokai (Textual has 15+ built-in)

**Cycling:** `Alt+T` to cycle through themes

**Custom:** Via Textual's Theme API, all widgets auto-update via CSS `$` variables

---

## 12. Testing Strategy

### 12.1 TDD Approach

**Strict TDD:** Write test before implementation. Every feature starts with a failing test.

### 12.2 Test Pyramid

```
        ~10 snapshot tests
       ~50 integration tests
      ~100 unit tests
```

### 12.3 Testing Frameworks

| Purpose | Tool |
|---------|------|
| Test runner | pytest >=8.0 |
| Async support | pytest-asyncio >=0.23 |
| Visual regression | pytest-textual-snapshot >=0.5 |
| Coverage | pytest-cov |

### 12.4 Textual Testing

```python
async def test_app_renders():
    app = AomApp()
    async with app.run_test() as pilot:
        # App is running
        assert app.query_one("#tree")
        await pilot.press("q")  # Triggers quit dialog
```

### 12.5 Subprocess Mocking

```python
@pytest.fixture
def mock_ansible_playbook(monkeypatch):
    """Mock pexpect.spawn for unit tests."""
    class MockSpawn:
        def __init__(self, *args, **kwargs):
            self.before = '{"_event": "v2_playbook_on_start", ...}'
            self.is_alive = False
        
        def expect(self, patterns, timeout=None):
            return 0  # EOF
        
        def close(self):
            pass
    
    monkeypatch.setattr(pexpect, "spawn", MockSpawn)
```

### 12.6 Snapshot Testing

```python
def test_main_screen(snap_compare):
    """Visual regression test for main screen."""
    async def setup(pilot):
        # Setup state
        await pilot.app.load_playbook("test.yml")
    
    assert snap_compare(AomApp(), run_before=setup)
```

### 12.7 Compact Renderer Testing

Compact mode testing requires different strategies than TUI testing since there's no Textual app to drive.

**Three-Tier Testing Approach:**

| Tier | Scope | Tools | Purpose |
|------|-------|-------|---------|
| Unit | State → render | `Console.capture()` + mocks | Test rendering logic in isolation |
| Integration | Mock pexpect | `pexpect` mock + `inline-snapshot` | Test renderer with simulated JSONL |
| System | Real ansible | Real `ansible-playbook` | End-to-end verification |

**Unit Testing with Rich Console Capture:**

```python
from rich.console import Console
from rich.text import Text

def test_task_status_rendering():
    """Test that task states render correctly."""
    console = Console(width=80)
    
    with console.capture() as capture:
        console.print("[green]●[/] Install nginx")
        console.print("[yellow]◐[/] Configure firewall")
    
    output = capture.get()
    assert "Install nginx" in output
    assert "Configure firewall" in output
```

**Snapshot Testing with inline-snapshot:**

The `inline-snapshot` library stores expected output directly in test files, updating them when behavior changes intentionally:

```python
from inline_snapshot import snapshot

def test_compact_status_panel():
    """Test compact mode status panel output."""
    renderer = CompactRenderer()
    renderer.update_state(create_mock_event())
    
    output = renderer.render_status_panel()
    
    # inline-snapshot stores expected value in test file
    assert output == snapshot("""\
┌─ Summary ────────────────────────────────────────┐
│ web1: ● 2 ok, ◆ 0 changed, ✖ 0 failed           │
│ web2: ◐ 1 running, ● 1 ok                       │
│ Elapsed: 0:04:23                                 │
└────────────────────────────────────────────────────┘
""")
```

When output changes, run `pytest --inline-snapshot=review` to update snapshots.

**Snapshot Testing for Diff Output:**

Diff output snapshot tests should capture the default view (all tasks shown, including unchanged) and verify the toggle behavior:

```python
def test_diff_snapshot_all_tasks():
    """Test diff output shows all tasks by default."""
    diff_output = generate_diff(old_session, new_session)
    
    # Default shows all tasks including unchanged
    assert diff_output == snapshot("""\
┌─ Task Diff: baseline → current ──────────────────────────────────┐
│ Task                          Baseline    Current    Classification │
├─────────────────────────────────────────────────────────────────────┤
│ Install nginx                    ●           ●          unchanged │
│ Configure firewall               ●           ✖          regressed  │
│ Start services                   ○           ●          improved   │
│ Deploy app                       □           □          unchanged │
└─────────────────────────────────────────────────────────────────────┘
""")

def test_diff_snapshot_changes_only():
    """Test --changes-only flag filters to show only changed tasks."""
    diff_output = generate_diff(old_session, new_session, changes_only=True)
    
    # Filtered view hides unchanged tasks
    assert diff_output == snapshot("""\
┌─ Task Diff: baseline → current ──────────────────────────────────┐
│ Task                          Baseline    Current    Classification │
├─────────────────────────────────────────────────────────────────────┤
│ Configure firewall               ●           ✖          regressed  │
│ Start services                   ○           ●          improved   │
└─────────────────────────────────────────────────────────────────────┘
""")
```

**Testing Non-TTY Fallback:**

```python
def test_non_tty_output():
    """Test rendering when stdout is not a TTY."""
    console = Console(force_terminal=False, width=80)
    
    # Non-TTY mode should still output ANSI codes
    # but without cursor positioning
    with console.capture() as capture:
        renderer = CompactRenderer(console=console)
        renderer.render()
    
    output = capture.get()
    # Verify basic output without curses-style positioning
    assert "Running:" in output
```

**Mocking pexpect for Integration Tests:**

```python
import pexpect
from unittest.mock import patch, MagicMock

def test_renderer_handles_jsonl_stream():
    """Test renderer processes mock JSONL events."""
    events = [
        {"_event": "v2_playbook_on_start"},
        {"_event": "v2_playbook_on_play_start", "play": {"name": "Setup"}},
        {"_event": "v2_runner_on_ok", "task": {"name": "Ping"}, "hosts": {"web1": {"ok": True}}},
    ]
    
    mock_child = MagicMock()
    mock_child.before = "\n".join(json.dumps(e) for e in events)
    
    renderer = CompactRenderer()
    for event in events:
        renderer.update_state(event)
    
    # Verify state updates
    assert renderer.state.status == Status.COMPLETED
```

### 12.8 Phase 1 Test Names (TDD Starter)

**Parser Tests:**
- `test_parse_play_header` — Parses "play #1 (webservers): Setup" correctly
- `test_parse_task_with_role` — Parses "nginx : Install nginx" with role extraction
- `test_parse_task_without_role` — Parses "Deploy application" without role
- `test_parse_tags` — Extracts TAGS from TAB-separated format
- `test_parse_include_tasks_not_expanded` — include_tasks appears as single entry
- `test_parse_import_tasks_expanded` — import_tasks tasks appear inline

**State Machine Tests:**
- `test_state_transitions_on_start` — IDLE → STARTING → LOADING_TASKS → READY
- `test_state_on_play_start` — READY → RUNNING on first play event
- `test_state_on_task_start_linear` — track task start in linear mode
- `test_state_on_runner_start_free` — detect free strategy from runner_on_start
- `test_state_on_runner_ok` — set host status to OK/CHANGED
- `test_state_on_runner_failed` — set host status to FAILED
- `test_state_on_stats_completes` — transition to COMPLETED

**Model Tests:**
- `test_task_definition_uuid_matching` — match by UUID field
- `test_task_definition_path_matching` — match by path field
- `test_task_definition_sequential_matching` — match by order + name
- `test_dynamic_task_creation` — include_tasks creates children at runtime
- `test_role_grouping_threshold` — 5+ consecutive same-role triggers grouping

**PtyStreamParser Tests:**
- `test_phase_transition_pre_to_execution` — detect v2_playbook_on_start
- `test_phase_transition_execution_to_recap` — detect v2_playbook_on_stats
- `test_plaintext_password_detection` — classify password prompts
- `test_plaintext_recap_collection` — collect PLAY RECAP lines
- `test_plaintext_warning_classification` — classify [WARNING] lines

---

## 13. Building and Distribution

### 13.1 Project Structure

```
new_ansible-aom/
├── pyproject.toml
├── .python-version
├── uv.lock
├── README.md
├── LICENSE
├── src/
│   └── ansible_aom/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── core/                  # Shared logic (NO UI dependencies)
│       │   ├── __init__.py
│       │   ├── state.py           # State machine
│       │   ├── parser.py          # JSONL parser
│       │   ├── models.py          # Data models
│       │   ├── session.py         # Session manager + artifact writer
│       │   └── config.py          # Configuration (Pydantic Settings)
│       ├── renderer/              # Interface layer
│       │   ├── __init__.py
│       │   ├── protocol.py        # Renderer Protocol (structural typing)
│       │   └── factory.py         # create_renderer() factory function
│       ├── compact/               # ANSI renderer (default mode)
│       │   ├── __init__.py
│       │   ├── renderer.py        # CompactRenderer (satisfies Protocol)
│       │   ├── display.py         # Rich Live + blessed display logic
│       │   ├── password.py         # Password pass-through (getpass)
│       │   └── logs.py           # Log streaming + non-TTY fallback
│       ├── tui/                  # Textual renderer (--tui mode)
│       │   ├── __init__.py
│       │   ├── app.py            # AOMApp (satisfies Protocol)
│       │   ├── screens/
│       │   │   ├── __init__.py
│       │   │   ├── main.py       # Main TUI screen
│       │   │   ├── help.py       # Help overlay (?)
│       │   │   ├── settings.py   # Settings screen (S)
│       │   │   ├── inspect.py    # Readonly inspect TUI
│       │   │   └── rerun.py      # Re-run dialog (Shift+R)
│       │   └── widgets/
│       │       ├── __init__.py
│       │       ├── task_tree.py  # Tree widget (Play/RoleGroup/Task/Host)
│       │       ├── log_panel.py  # RichLog with search
│       │       ├── summary_panel.py # Play-level overview
│       │       ├── status_bar.py # Configurable status bar
│       │       └── debug_panel.py # Full internal state
│       ├── styles/
│       │   └── app.tcss          # Textual CSS
│       └── inspect/              # Inspect CLI (text mode)
│           ├── __init__.py
│           ├── cli.py            # Click/typer CLI commands
│           ├── diff.py           # Session diff logic
│           └── display.py        # Rich table formatting
├── tests/
│   ├── conftest.py
│   ├── fixtures/                 # JSONL event fixtures
│   │   ├── single_task_ok.jsonl
│   │   ├── multi_host_mixed.jsonl
│   │   ├── playbook_failed.jsonl
│   │   └── ...
│   ├── unit/
│   │   ├── test_parser.py
│   │   ├── test_state.py
│   │   ├── test_models.py
│   │   └── test_config.py
│   ├── compact/                  # Compact renderer tests
│   │   ├── test_renderer.py
│   │   ├── test_renderer_snapshots.py  # inline-snapshot
│   │   └── test_password.py
│   ├── tui/                     # Textual TUI tests
│   │   ├── test_app.py
│   │   ├── test_snapshots.py    # pytest-textual-snapshot
│   │   └── test_widgets/
│   ├── integration/
│   │   ├── test_runner.py
│   │   └── test_inspect.py
│   └── diff/
│       └── test_diff.py
└── flake.nix
```

### 13.2 pyproject.toml

```toml
[project]
name = "ansible-aom"
version = "0.1.0"
description = "Ansible Output Monitor - nom-style TUI for ansible-playbook"
requires-python = ">=3.14"
dependencies = [
    "textual>=0.60",
    "rich",
    "pyyaml>=6.0",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "platformdirs>=3.0",
    "pexpect>=4.8",
    "psutil>=5.9",
    "blessed>=1.20",           # ANSI cursor positioning for compact mode
]

[project.scripts]
aom = "ansible_aom.cli:main"

[project.optional-dependencies]
dev = [
    "textual-dev>=0.86",
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-textual-snapshot>=0.5",
    "pytest-cov",
    "ruff",
    "mypy",
    "inline-snapshot>=0.10",   # Compact mode snapshot testing
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/ansible_aom"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py314"

[tool.mypy]
python_version = "3.14"
strict = true
```

### 13.3 Nuitka Build

**Command:**
```bash
nuitka --standalone \
       --onefile \
       --output-filename=aom \
       --include-package=textual \
       --include-package=rich \
       --include-package=yaml \
       --include-package=pydantic \
       --include-package=ansible_aom \
       --include-data-files=src/ansible_aom/styles/*.tcss=ansible_aom/styles/ \
       src/ansible_aom/__main__.py
```

**Output:** `aom` standalone executable

### 13.4 Nix Flake

```nix
{
  description = "aom - Ansible Output Monitor";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python314;
      in {
        packages.default = python.pkgs.buildPythonApplication {
          pname = "ansible-aom";
          version = "0.1.0";
          src = ./.;
          format = "pyproject";
          
          nativeBuildInputs = [ python.pkgs.hatchling ];
          
          propagatedBuildInputs = with python.pkgs; [
            textual pyyaml pydantic pydantic-settings
            platformdirs pexpect psutil
          ];
          
          nativeCheckInputs = [ python.pkgs.pytest ];
        };

        devShells.default = pkgs.mkShell {
          inputsFrom = [ self.packages.${system}.default ];
          buildInputs = with pkgs; [
            python
            ruff
            mypy
            python.pkgs.pytest
            uv
          ];
        };

        apps.default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/aom";
        };
      });
}
```

---

## 14. Error Handling

**Exit Codes:**

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Execution error (task failed, unreachable hosts) |
| 2 | Unreachable hosts |
| 127 | Command not found |
| 130 | SIGINT received |

### 14.1 Crash Recovery

**Behavior:**
- AOM stays open after process exits (success, failure, or crash)
- All panels remain interactive
- Crash shows graceful degradation + brief notification modal
- Auto-save partial session data

### 14.2 Graceful Degradation

**If JSONL parsing fails:**
- Log warning
- Display raw output in log panel
- Continue with degraded tree updates

**If --list-tasks fails:**
- Build tree dynamically from JSONL events
- Show warning: "Pre-parse failed, building tree at runtime"

### 14.3 Cancellation

**First Ctrl+C:**
- Forward SIGINT to ansible-playbook subprocess
- Allow graceful termination

**Second Ctrl+C (within 2 seconds):**
- Kill everything
- Immediate exit
- Save partial session if possible

### 14.4 Password Timeout

- 60-second timeout for password modal
- If timeout: cancel with error
- User can retry or abort

### 14.5 Logging

AOM maintains its own log file for debugging and troubleshooting:

**Log Path:**
```
~/.local/state/aom/log/aom.log
```
(XDG-compliant state directory)

**Characteristics:**
- **File-only:** Silent during normal operation, no console output
- **Rotation:** `RotatingFileHandler` — 10 MB/file, 5 backups (50 MB max)
- **Non-blocking:** `QueueHandler` + `QueueListener` — writes in background thread to avoid I/O blocking the main process

**Log Levels:**

| Level | Events |
|-------|--------|
| DEBUG | JSONL events received, state transitions, pexpect output, terminal capabilities |
| INFO | Playbook start/end, session created, config loaded, `--list-tasks` completed |
| WARNING | `--list-tasks` failed (falling back), JSON parse error, password prompt detected, slow terminal |
| ERROR | Unexpected subprocess crash, ansible-playbook not found, ansible.posix not installed |

**`--verbose` Flag:**
- Enables DEBUG level logging to the log file
- Additionally prints pre-execution diagnostics to console (Section 3.2)

### 14.6 Missing ansible-playbook

If `ansible-playbook` is not found in PATH:

**Detection:**
- Check at startup before any execution
- Exit code: 127

**Error Message:**
```
Error: ansible-playbook not found.

Install with:
  apt install ansible-core      # Debian/Ubuntu
  pip install ansible-core      # Python pip
  brew install ansible          # macOS Homebrew
```

**ansible.posix Collection Missing:**

If `ansible.posix` collection is not installed:

```
Error: ansible.posix collection not found. Required for JSONL output.

Install with:
  ansible-galaxy collection install ansible.posix
```

### 14.7 Subprocess Error Handling

**Exit Code Interpretation:**

| Exit Code | Meaning | AOM Action |
|-----------|---------|------------|
| 0 | Success | Mark COMPLETED |
| 1 | Failed task(s) | Mark FAILED, collect failed hosts |
| 2 | Unreachable host(s) | Mark FAILED, collect unreachable hosts |
| 4 | Playbook error (syntax, missing file) | Mark CRASHED, show error |
| 127 | Command not found | Mark CRASHED, show "ansible-playbook not found" |
| 130 | SIGINT (Ctrl+C) | Mark IDLE (user-initiated cancel) |
| 137 | SIGKILL | Mark CRASHED, log "Process was killed" |
| -N | Signal N | Mark CRASHED, log signal info |

**Stderr Capture:**
- Capture all stderr output from subprocess
- Store in session directory as `stderr.log`
- Display stderr lines in log panel (TUI) or console (compact)
- If stderr contains JSON: attempt to parse as JSONL event (some errors leak to stderr)

**Process State Monitoring:**
- Check `child.isalive()` periodically (every 0.5s)
- Detect orphaned processes: if process exits before JSONL events complete
- If process terminates during LOADING_TASKS phase: immediate CRASHED state
- If process terminates during EXECUTION phase: attempt to parse remaining buffer, then transition to appropriate terminal state

**Process Hang Detection (Watchdog):**
- If no output (JSONL or otherwise) received for 60 seconds, log WARNING
- If no output for 300 seconds (5 minutes), log ERROR and offer user choice:
  - Continue waiting (user may have long-running task)
  - Cancel execution (SIGINT → SIGKILL sequence)
- Watchdog timer resets on any output from subprocess
- Watchdog is disabled during password prompt phase (user input expected)

## 15. Incremental Implementation Plan

### Phase 1: Core Foundation

**Goal:** Basic playable run with compact view

**Milestones:**
1. Project structure and dependencies
2. CLI parsing and entry point
3. JSONL stream parser (`core/parser.py`)
4. State machine and models (`core/state_machine.py`, `core/models.py`)
5. Pre-parser for `--list-tasks` / `--list-hosts` (`ansible/preflight.py`)
6. Basic pexpect runner (`ansible/runner.py`)
7. Compact view rendering (`compact/`)
8. Session recording (`session/store.py`)

**Tests:** Unit tests for parser, state machine, models

### Phase 2: Password Handling

**Goal:** Interactive password prompts work

**Milestones:**
1. Password prompt detection
2. Textual modal for password entry
3. Threading sync between worker and modal
4. Multiple password types (vault, become, SSH)

**Tests:** Integration tests with mock prompts

### Phase 3: Full TUI

**Goal:** Multi-panel interactive interface

**Milestones:**
1. Full TUI layout
2. Tree widget (play/task/host)
3. Log panel with RichLog
4. Summary panel
5. Status bar
6. Keyboard navigation
7. Panel focus switching

**Tests:** Widget tests, snapshot tests

### Phase 4: Interactive Features

**Goal:** Search, filter, help, settings

**Milestones:**
1. Search overlay (Ctrl+F)
2. Filter panel
3. Help overlay (?)
4. Settings screen (S)
5. Theme cycling

**Tests:** Interaction tests

### Phase 5: Post-Run Features

**Goal:** Run inspection and re-run

**Milestones:**
1. Stay open after completion
2. Re-run with same args (R)
3. Re-run with modified args (Shift+R)
4. Session artifact export
5. Inspect CLI subcommand

**Tests:** Integration tests

### Phase 6: Polish

**Goal:** Distribution-ready

**Milestones:**
1. Nuitka build
2. Nix flake
3. Documentation
4. CI/CD pipeline
5. Release preparation

**Tests:** End-to-end tests, packaging tests

---

## Appendix A: Decision Summary

This section captures the key decisions from the 55 user questions.

### Core Identity
- Project: aom
- Package: ansible-aom
- Module: ansible_aom
- CLI: aom
- Concept: nom-style monitor with optional full TUI

### Technical
- Language: Python 3.14
- TUI: Textual >=0.60
- Build: Nuitka + Nix flake
- Package manager: uv
- Config: YAML

### Parsing
- Format: JSONL only (ansible.posix.jsonl)
- Pre-parse: --list-tasks before execution
- Matching: Task IDs from JSONL events
- Role grouping: Auto-collapse at 5+ consecutive

### Views
- **Dual Backend Architecture**: Two rendering backends sharing common core
- Default: Compact mode (ANSI renderer: Rich Console + cursor manipulation)
- Optional: Full TUI via `--tui` flag (Textual framework)
- Shared Core: State machine, JSONL parser, models, session manager
- Non-TTY: ANSI formatting preserved

### Features
- Password: pexpect PTY (terminal pass-through for compact / Textual modal for TUI)
- Search: Ctrl+F overlay with regex support (TUI only)
- Session: UUIDv7 directories + .aom artifacts
- Config: Single YAML file
- Inspection: Full CLI for session review

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-04-20 | Initial specification |
| 1.1 | 2026-04-20 | Two-backend architecture (Q56), JSONL event types (10 events), 8-state state machine, compact mode password handling |
| 1.2 | 2026-04-20 | Protocol-based architecture with Renderer Protocol, `blessed` and `inline-snapshot` dependencies, session diff matching strategy, compact renderer testing approach |
| 1.3 | 2026-04-20 | Diff improvements (Q61-65): cross-playbook diff warns but proceeds; silent task matching (no method displayed); show all tasks by default with `--changes-only` filter; no duration comparison (status changes only); no playbook source diff (git's job); diff snapshot tests for default/filtered views |
| 1.4 | 2026-04-20 | `--verbose` flag for pre-execution diagnostics; `--list-tasks` parsing documentation (no JSON, TAB separators, edge cases); logging section (XDG path, rotation, levels); ansible-playbook not found handling; terminal requirements (24×80 min, SIGWINCH, SIGTERM, SIGHUP, SIGPIPE) |
| 1.5 | 2026-04-20 | PTY stream parsing (3-phase: PRE_RUN_PROMPTS, EXECUTION, POST_RUN_RECAP with PtyStreamParser class); dual-track Definition/State architecture (UUID → path → sequential+name matching with play_order/task_order fields); include_tasks dynamic expansion (task_order=-1, is_dynamic=True flag) |
| 1.6 | 2026-04-20 | Gap fixes: Strategy detection from event patterns (not JSONL field), host name resolution (actual hostnames from runner events), PtyStreamParser._handle_plaintext classification, complete RunState event handlers, TaskDefinition uuid/path/children fields, PlayDefinition.id clarification, PlayRunState.detected_strategy, Section 14.7 Subprocess Error Handling (exit codes, stderr capture, watchdog), compact renderer refresh strategy, terminal compatibility (Unicode/color fallback), memory bounds, SIGQUIT handling, timestamp convention, task name truncation, TDD starter test names, session file permissions, corrupted session handling, minimum ansible-core >=2.14 requirement |
| 1.7 | 2026-04-20 | Inventory-based host resolution via `--list-hosts` (parallel with `--list-tasks`); `PlayDefinition.resolved_hosts` field; `--list-hosts` parser with fallback; defense-in-depth password/secret redaction (4 layers: _ansible_no_log, PASSWORD_MATCH regex + whitelist, command string sanitization, verbose invocation redaction); redaction always-on (no opt-out); redaction config schema; Section 5.2.1 --list-hosts parsing |
| 1.8 | 2026-04-20 | Deprecation warning filtering: WARNING_PATTERNS regex updated to match both `[DEPRECATION WARNING]:` and `[DEPRECATED]:` formats; `WarningType` enum and `WarningEntry` dataclass for classified warning storage; Filter Panel (7.6) updated with Warning/Deprecation checkboxes; compact mode status line shows warning ⚠ and deprecation ✱ counts; config schema updated with warnings section; research confirmed deprecations are plaintext on stderr (not JSONL events) |

---

**End of Specification**