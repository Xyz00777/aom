# AOM Test Specification

> Version 1.0 — 2026-04-20
> Companion document to SPECIFICATION.md v1.8

## Overview

This document specifies all test cases for the AOM (Ansible Output Monitor) project, organized by specification section. Each test case is designed for strict Test-Driven Development (TDD): tests are written BEFORE implementation.

### Test Case Format

Each test case follows this format:
- **TC-XXX**: Unique identifier
- **Section**: Specification section reference (e.g., "5.6")
- **Category**: unit | integration | system | snapshot | property
- **Priority**: critical | high | medium | low
- **Description**: What is being tested
- **Test**: Specific test logic — what to assert
- **Fixture/Setup**: What data or mocks are needed
- **Edge Cases**: Boundary conditions

### Priority Definitions

- **critical**: Must pass for any release. Core functionality.
- **high**: Must pass for production. Important features.
- **medium**: Should pass. Nice-to-have features.
- **low**: Can defer. Edge cases and polish.

### Category Definitions

- **unit**: Tests a single function or class in isolation
- **integration**: Tests interaction between multiple components
- **system**: Tests end-to-end workflows
- **snapshot**: Visual regression tests (compact renderer output snapshots)
- **property**: Property-based tests (invariant checks)

---

## Section 1-2: Project Identity & Architecture

### TC-001: Package Name Verification
**Section:** 1.1
**Category:** unit
**Priority:** critical
**Description:** Verify the package is named correctly
**Test:** Assert package name is `ansible-aom` with CLI entry point `aom`
**Fixture/Setup:** Package installation or source checkout
**Edge Cases:** None

### TC-002: CLI Entry Point Exists
**Section:** 2.1
**Category:** unit
**Priority:** critical
**Description:** Verify `aom` command is available after installation
**Test:** `which aom` returns valid path; `aom --help` exits 0
**Fixture/Setup:** Installed package
**Edge Cases:** Missing PATH entry

### TC-003: Core Module Structure
**Section:** 2.1, 2.2
**Category:** unit
**Priority:** high
**Description:** Verify core modules exist at the paths declared in ARCHITECTURE.md §3.
**Test:** Assert files exist for the target layout: `cli.py`, `__main__.py`,
`core/models.py`, `core/state_machine.py`, `core/parser.py`,
`ansible/runner.py`, `ansible/preflight.py`, `session/store.py`,
`renderer/protocol.py`, `drivers/protocol.py`.
**Fixture/Setup:** Source tree
**Edge Cases:** None
**Notes:** Pair with the layering test from ARCHITECTURE.md §7.8
(`tests/unit/test_layering.py`) — together they pin both presence and
direction of dependencies.

### TC-004: Renderer Protocol Implementation
**Section:** 2.3
**Category:** unit
**Priority:** critical
**Description:** Both CompactRenderer and AOMApp satisfy the Renderer Protocol
**Test:** Protocol ABC defines `start()`, `update_state()`, `handle_password_prompt()`, `handle_completion()`, `stop()`. Both renderers implement all methods.
**Fixture/Setup:** Mock renderer instances
**Edge Cases:** None

### TC-005: Renderer Factory Selection
**Section:** 2.3
**Category:** unit
**Priority:** high
**Description:** `create_renderer(tui_mode=False)` returns CompactRenderer; `create_renderer(tui_mode=True)` returns AOMApp
**Test:** Assert factory returns correct type based on flag
**Fixture/Setup:** None
**Edge Cases:** Invalid kwargs passed through

---

## Section 3: Command Interface

### TC-006: Basic CLI Invocation
**Section:** 3.1
**Category:** integration
**Priority:** critical
**Description:** `aom playbook.yml` launches successfully
**Test:** Command exits 0 or runs expected playbook
**Fixture/Setup:** Valid playbook file
**Edge Cases:** Missing playbook file

### TC-007: TUI Mode Flag
**Section:** 3.2
**Category:** integration
**Priority:** high
**Description:** `--tui` flag launches full Textual TUI instead of compact view
**Test:** With `--tui`, Textual app launches; without it, compact ANSI renderer launches
**Fixture/Setup:** Terminal with TTY
**Edge Cases:** Non-TTY environment

### TC-008: Verbose Flag Diagnostics
**Section:** 3.2
**Category:** integration
**Priority:** medium
**Description:** `--verbose` / `-v` prints pre-execution diagnostics
**Test:** Output includes: resolved ansible-playbook path, environment overrides, terminal capabilities, --list-tasks summary
**Fixture/Setup:** Valid playbook
**Edge Cases:** Verbose with non-existent playbook

### TC-009: Verbose Enables DEBUG Logging
**Section:** 3.2
**Category:** integration
**Priority:** medium
**Description:** `--verbose` flag enables DEBUG level logging to log file
**Test:** Log file contains DEBUG level entries when flag is set
**Fixture/Setup:** Writable log directory
**Edge Cases:** Log directory not writable

### TC-010: Ansible Options Pass-Through
**Section:** 3.2
**Category:** integration
**Priority:** critical
**Description:** All unknown arguments pass through to ansible-playbook
**Test:** `aom playbook.yml -i inventory.ini --limit webservers` passes `-i inventory.ini --limit webservers` to ansible-playbook
**Fixture/Setup:** Valid inventory file
**Edge Cases:** Invalid ansible options

### TC-011: Help Flag
**Section:** 3.2
**Category:** unit
**Priority:** critical
**Description:** `--help` displays usage information and exits 0
**Test:** Output contains usage pattern, available flags, examples
**Fixture/Setup:** None
**Edge Cases:** Help with other arguments (should show help and exit)

### TC-012: Version Flag
**Section:** 3.2
**Category:** unit
**Priority:** medium
**Description:** `--version` displays version string and exits 0
**Test:** Output matches semantic version pattern (e.g., `1.7.0`)
**Fixture/Setup:** None
**Edge Cases:** Version with other arguments

### TC-013: Inspect List Subcommand
**Section:** 3.3
**Category:** integration
**Priority:** medium
**Description:** `aom inspect list` lists all recorded sessions
**Test:** Output shows session IDs, timestamps, playbook names
**Fixture/Setup:** Session directory with recorded sessions
**Edge Cases:** Empty session directory

### TC-014: Inspect Session Summary
**Section:** 3.3
**Category:** integration
**Priority:** medium
**Description:** `aom inspect <session-id>` shows session summary
**Test:** Output includes playbook name, hosts, task counts, duration
**Fixture/Setup:** Valid session artifact
**Edge Cases:** Invalid/non-existent session ID

### TC-015: Inspect Filter Failed Tasks
**Section:** 3.3
**Category:** integration
**Priority:** medium
**Description:** `aom inspect <session-id> --failed` shows only failed tasks
**Test:** Output contains only tasks with status=failed
**Fixture/Setup:** Session with mixed results including failures
**Edge Cases:** Session with no failures

### TC-016: Inspect Filter by Host
**Section:** 3.3
**Category:** integration
**Priority:** medium
**Description:** `aom inspect <session-id> --host <name>` filters results by host
**Test:** Output shows only events for specified host
**Fixture/Setup:** Session with multiple hosts
**Edge Cases:** Host not in session

### TC-017: Inspect Tree View
**Section:** 3.3
**Category:** integration
**Priority:** medium
**Description:** `aom inspect <session-id> --tree` shows task tree structure
**Test:** Output displays hierarchical play/task/role structure
**Fixture/Setup:** Session with plays and roles
**Edge Cases:** Empty session

### TC-018: Inspect Export Artifact
**Section:** 3.3
**Category:** integration
**Priority:** medium
**Description:** `aom inspect <session-id> --export` creates .aom artifact file
**Test:** Artifact file is created with correct JSONL format
**Fixture/Setup:** Valid session
**Edge Cases:** Export destination not writable

### TC-019: Inspect Diff Sessions
**Section:** 3.3
**Category:** integration
**Priority:** medium
**Description:** `aom inspect diff <id1> <id2>` compares two sessions
**Test:** Output shows differences in task results, host status
**Fixture/Setup:** Two comparable sessions
**Edge Cases:** Same session ID twice; non-existent session

### TC-020: Inspect Prune Sessions
**Section:** 3.3
**Category:** integration
**Priority:** medium
**Description:** `aom inspect prune --days 30` removes sessions older than 30 days
**Test:** Sessions older than threshold are deleted; newer kept
**Fixture/Setup:** Session directory with old and new sessions
**Edge Cases:** No sessions to prune; prune all sessions

### TC-021: Inspect TUI Mode
**Section:** 3.3
**Category:** integration
**Priority:** low
**Description:** `aom inspect --tui` launches TUI for browsing sessions
**Test:** Textual TUI launches with session list
**Fixture/Setup:** Terminal with TTY
**Edge Cases:** Non-TTY environment

### TC-022: Inspect JSON Output
**Section:** 3.3
**Category:** integration
**Priority:** medium
**Description:** `aom inspect <id> --json` outputs JSON format
**Test:** Output is valid JSON with session data
**Fixture/Setup:** Valid session
**Edge Cases:** None

### TC-023: Inspect JSONL Output
**Section:** 3.3
**Category:** integration
**Priority:** medium
**Description:** `aom inspect <id> --jsonl` outputs raw event dump
**Test:** Output is line-delimited JSON events
**Fixture/Setup:** Valid session
**Edge Cases:** None

### TC-024: Exit Code 0 - Success
**Section:** 3.4
**Category:** integration
**Priority:** critical
**Description:** Exit code 0 for successful playbook execution
**Test:** Playbook completing with all tasks ok yields exit code 0
**Fixture/Setup:** Playbook with all successful tasks
**Edge Cases:** None

### TC-025: Exit Code 1 - Playbook Failure
**Section:** 3.4
**Category:** integration
**Priority:** critical
**Description:** Exit code 1 for task failure or unreachable host
**Test:** Playbook with failed task yields exit code 1
**Fixture/Setup:** Playbook with failing task
**Edge Cases:** Task with ignore_errors (may still be exit 0)

### TC-026: Exit Code 2 - Unreachable Hosts
**Section:** 3.4
**Category:** integration
**Priority:** critical
**Description:** Exit code 2 for unreachable hosts (if distinct from failure)
**Test:** All hosts unreachable yields exit code 2
**Fixture/Setup:** Playbook targeting unreachable hosts
**Edge Cases:** Mixed unreachable and reachable hosts

### TC-027: Exit Code 127 - Command Not Found
**Section:** 3.4
**Category:** integration
**Priority:** high
**Description:** Exit code 127 when ansible-playbook not found
**Test:** AOM gracefully exits 127 with error message when ansible-playbook missing
**Fixture/Setup:** PATH without ansible-playbook
**Edge Cases:** ansible-playbook installed but not executable

### TC-028: Exit Code 130 - User Cancelled
**Section:** 3.4
**Category:** integration
**Priority:** high
**Description:** Exit code 130 on SIGINT (Ctrl+C)
**Test:** First Ctrl+C forwards to subprocess; second Ctrl+C (within 2s) kills everything and exits 130
**Fixture/Setup:** Running playbook
**Edge Cases:** Rapid multiple signals

---

## Section 4: View Modes

### TC-029: Compact View Default Layout
**Section:** 4.1
**Category:** snapshot
**Priority:** critical
**Description:** Compact view displays header, running tasks, tree, and summary panels
**Test:** Assert output contains: playbook header with progress, Running: section, Tree panel, Summary panel
**Fixture/Setup:** Running playbook
**Edge Cases:** Edge cases for panel truncation

### TC-030: Compact View Status Icons
**Section:** 4.1
**Category:** unit
**Priority:** high
**Description:** Status icons display correctly: ● (ok), ◆ (changed), ✖ (failed), ⊝ (unreachable), ◐ (running), □ (pending/skipped)
**Test:** Each status maps to correct Unicode character
**Fixture/Setup:** Mock state with each status
**Edge Cases:** Unicode fallback support

### TC-031: Compact View Elapsed Time
**Section:** 4.1
**Category:** integration
**Priority:** medium
**Description:** Elapsed time displays in HH:MM:SS format, updates every second
**Test:** Timer starts from playbook start, increments each second
**Fixture/Setup:** Running playbook with known start time
**Edge Cases:** Long duration (24+ hours)

### TC-032: Compact View Progress Bar
**Section:** 4.1
**Category:** unit
**Priority:** medium
**Description:** Progress bar shows completion percentage in header
**Test:** Progress bar length proportional to completed tasks
**Fixture/Setup:** State with known task completion
**Edge Cases:** 0 tasks, all tasks completed

### TC-033: Rich Live Rendering for Compact Mode
**Section:** 4.1
**Category:** integration
**Priority:** high
**Description:** Compact mode uses Rich Live with refresh_per_second=4
**Test:** Status panel updates at most 4 times per second
**Fixture/Setup:** Mock event stream with rapid updates
**Edge Cases:** Event burst handling

### TC-034: Compact Password Pass-Through
**Section:** 4.1
**Category:** integration
**Priority:** critical
**Description:** Compact mode pauses Rich Live for password prompts, allows terminal pass-through
**Test:** On password prompt, Live.stop() called, prompt appears on terminal, Live.start() called after input
**Fixture/Setup:** Playbook requiring password
**Edge Cases:** Password prompt timeout

### TC-035: Compact Mode Dependencies
**Section:** 4.1
**Category:** unit
**Priority:** low
**Description:** Compact mode requires `rich` library; `blessed` optional
**Test:** Import succeeds for rich; blessed import optional
**Fixture/Setup:** Dependency check
**Edge Cases:** Missing blessed (should still work)

### TC-036: TUI Multi-Panel Layout
**Section:** 4.2
**Category:** snapshot
**Priority:** critical
**Description:** TUI displays status bar, tree view, summary panel, log panel, footer
**Test:** All five components rendered in correct positions
**Fixture/Setup:** Screen capture or mock output
**Edge Cases:** Terminal resize

### TC-037: TUI Tree Navigation
**Section:** 4.2
**Category:** integration
**Priority:** high
**Description:** TUI supports keyboard navigation: ↑↓ navigate, → expand, ← collapse, Tab switch panels
**Test:** Key presses update focus and expansion state
**Fixture/Setup:** Interactive TUI session
**Edge Cases:** First/last item navigation

### TC-038: TUI Search in Log Panel
**Section:** 4.2
**Category:** integration
**Priority:** medium
**Description:** TUI log panel supports text search
**Test:** Search highlights matching lines, navigation between matches
**Fixture/Setup:** Log panel with scrollable content
**Edge Cases:** Empty search, no matches

### TC-039: TUI Status Bar Configuration
**Section:** 4.2
**Category:** unit
**Priority:** low
**Description:** Status bar shows playbook name, current play, elapsed time, task progress
**Test:** Status bar content matches current state
**Fixture/Setup:** Mock state
**Edge Cases:** Long playbook names (truncation)

### TC-040: TUI Footer Shortcuts
**Section:** 4.2
**Category:** unit
**Priority:** low
**Description:** Footer displays available shortcuts: ? Help, q Quit, ↑↓ Navigate, → Expand, ← Collapse, Tab Switch
**Test:** Footer text matches specification
**Fixture/Setup:** TUI render
**Edge Cases:** None

### TC-041: Non-TTY Output Format
**Section:** 4.3
**Category:** integration
**Priority:** medium
**Description:** When piped/redirected, output uses ANSI formatting but one line per status update
**Test:** Non-TTY output is line-based with ANSI codes (colors preserved)
**Fixture/Setup:** Piped output capture
**Edge Cases:** Binary output vs text

### TC-042: Non-TTY No Interactive Features
**Section:** 4.3
**Category:** integration
**Priority:** medium
**Description:** Non-TTY mode disables all interactive features
**Test:** No TUI launch, no password prompts via getpass, no keyboard input expected
**Fixture/Setup:** Redirected stdout
**Edge Cases:** Interactive flags ignored silently

### TC-043: Minimum Terminal Size Check
**Section:** 4.4
**Category:** integration
**Priority:** critical
**Description:** AOM checks terminal size at startup; minimum 24 lines × 80 columns
**Test:** Below minimum shows error and exits 1
**Fixture/Setup:** Mocked small terminal
**Edge Cases:** Terminal reports 0x0

### TC-044: Terminal Size Error Message
**Section:** 4.4
**Category:** integration
**Priority:** high
**Description:** Error message for small terminal shows dimensions and minimum
**Test:** Message format: "Terminal too small: {rows}×{cols}. Minimum: 24×80. Resize or use --no-tui flag."
**Fixture/Setup:** Mocked terminal size
**Edge Cases:** None

### TC-045: Terminal Graceful Degradation
**Section:** 4.4
**Category:** integration
**Priority:** medium
**Description:** Below minimum size, warning banner displayed but operation continues with --force
**Test:** Warning visible but execution proceeds
**Fixture/Setup:** Mocked small terminal with force flag
**Edge Cases:** None

### TC-046: Signal Handling - SIGINT First Press
**Section:** 4.4
**Category:** integration
**Priority:** critical
**Description:** First Ctrl+C forwards signal to subprocess (ansible-playbook)
**Test:** First SIGINT does NOT terminate AOM; subprocess receives signal
**Fixture/Setup:** Running playbook
**Edge Cases:** Subprocess already terminating

### TC-047: Signal Handling - SIGINT Second Press
**Section:** 4.4
**Category:** integration
**Priority:** critical
**Description:** Second Ctrl+C within 2 seconds kills everything and exits with code 130
**Test:** Second SIGINT within 2s terminates AOM immediately with exit 130
**Fixture/Setup:** Running playbook, mock signal timing
**Edge Cases:** Delayed second signal (>2s)

### TC-048: Signal Handling - SIGQUIT
**Section:** 4.4
**Category:** integration
**Priority:** medium
**Description:** SIGQUIT (Ctrl+\) logs stack trace to file and continues execution
**Test:** Stack trace written to log file; AOM continues running
**Fixture/Setup:** Running playbook, writable log directory
**Edge Cases:** Log file not writable

### TC-049: Signal Handling - SIGTERM
**Section:** 4.4
**Category:** integration
**Priority:** high
**Description:** SIGTERM saves session, cleans terminal, exits gracefully with code 0
**Test:** Session saved, cursor restored, colors reset, exit 0
**Fixture/Setup:** Running playbook with session state
**Edge Cases:** Corruption during save

### TC-050: Signal Handling - SIGHUP
**Section:** 4.4
**Category:** integration
**Priority:** high
**Description:** SIGHUP saves session, cleans terminal, exits gracefully with code 0
**Test:** Same as SIGTERM graceful shutdown
**Fixture/Setup:** Running playbook
**Edge Cases:** None

### TC-051: Signal Handling - SIGWINCH
**Section:** 4.4
**Category:** integration
**Priority:** medium
**Description:** SIGWINCH triggers re-render in both modes
**Test:** Compact mode re-renders status panel; TUI re-layouts all panels
**Fixture/Setup:** Running playbook, terminal resize
**Edge Cases:** Very rapid resize events

### TC-052: Signal Handling - SIGPIPE
**Section:** 4.4
**Category:** integration
**Priority:** low
**Description:** SIGPIPE is ignored (Python default)
**Test:** Process continues after SIGPIPE; no crash
**Fixture/Setup:** Piped output closed by consumer
**Edge Cases:** None

### TC-053: Terminal Cleanup on Exit
**Section:** 4.4
**Category:** integration
**Priority:** critical
**Description:** On any exit, AOM restores cursor visibility, exits alternate screen, resets colors, flushes output
**Test:** Terminal state after exit matches pre-AOM state
**Fixture/Setup:** Terminal state capture before/after
**Edge Cases:** Already in alternate screen; already hidden cursor

### TC-054: Event-Driven Refresh
**Section:** 4.5
**Category:** integration
**Priority:** high
**Description:** Status panel re-renders on every state change event (ok, failed, changed, skipped, unreachable, runner_start)
**Test:** Each event type triggers exactly one render
**Fixture/Setup:** Mock event stream
**Edge Cases:** Multiple rapid events

### TC-055: Throttled Refresh Rate
**Section:** 4.5
**Category:** integration
**Priority:** high
**Description:** Maximum 4 updates per second regardless of event rate
**Test:** 10 events in 1 second yields at most 4 render calls
**Fixture/Setup:** Burst of mock events
**Edge Cases:** None

### TC-056: Timer-Based Elapsed Time
**Section:** 4.5
**Category:** integration
**Priority:** medium
**Description:** Elapsed time updates every 1 second independent of events
**Test:** Timer fires every 1 second updating elapsed display
**Fixture/Setup:** Running playbook with no events
**Edge Cases:** None

### TC-057: Debounced Event Batching
**Section:** 4.5
**Category:** integration
**Priority:** medium
**Description:** Events within same 250ms window are batched into single render
**Test:** Multiple events within 250ms yield single render
**Fixture/Setup:** Timed mock events
**Edge Cases:** None

### TC-058: Non-TTY Refresh Fallback
**Section:** 4.5
**Category:** integration
**Priority:** medium
**Description:** Non-TTY uses one line per status change, no cursor manipulation, no continuous elapsed time
**Test:** Piped output has one line per status event
**Fixture/Setup:** Piped output capture
**Edge Cases:** None

### TC-059: Unicode Support Detection
**Section:** 4.6
**Category:** unit
**Priority:** high
**Description:** AOM detects Unicode support via blessed.Terminal() at startup
**Test:** Unicode terminal detected, fallback on ASCII-only terminal
**Fixture/Setup:** Mocked terminal capabilities
**Edge Cases:** Detection failure defaults to ASCII

### TC-060: Unicode Fallback Characters
**Section:** 4.6
**Category:** unit
**Priority:** high
**Description:** Non-Unicode terminals use ASCII equivalents: ●→*, ◆→+, ✖→X, ◐→@, □→.
**Test:** Each Unicode icon maps correctly to ASCII fallback
**Fixture/Setup:** No-Unicode terminal mock
**Edge Cases:** Partial Unicode support

### TC-061: Color Support Detection
**Section:** 4.6
**Category:** unit
**Priority:** high
**Description:** AOM detects color support level: truecolor/256/16/monochrome
**Test:** Rich Console.detect_color() or blessed.Terminal().number_of_colors returns correct level
**Fixture/Setup:** Mocked terminal capabilities
**Edge Cases:** No color support (piped)

### TC-062: 16-Color Fallback
**Section:** 4.6
**Category:** unit
**Priority:** medium
**Description:** 16-color terminals use standard ANSI colors (green, yellow, red, cyan, white, dim)
**Test:** Colors map to 16-color ANSI codes
**Fixture/Setup:** 16-color terminal mock
**Edge Cases:** None

### TC-063: Monochrome Fallback
**Section:** 4.6
**Category:** unit
**Priority:** medium
**Description:** Monochrome/piped output uses text labels (OK, CHANGED, FAILED, etc.) instead of colors
**Test:** Status displayed as text labels
**Fixture/Setup:** No-color terminal mock
**Edge Cases:** None

### TC-064: Minimum Width at 80 Columns
**Section:** 4.6
**Category:** integration
**Priority:** high
**Description:** Compact status panel designed for 80 columns minimum
**Test:** Panel renders fully at 80 columns
**Fixture/Setup:** Terminal width 80
**Edge Cases:** None

### TC-065: Width 60-79 Columns Truncation
**Section:** 4.6
**Category:** integration
**Priority:** medium
**Description:** At 60-79 columns, task names truncated (minimum 10 chars shown)
**Test:** Task names correctly truncated at narrow widths
**Fixture/Setup:** Terminal width 60-79
**Edge Cases:** Very long task names

### TC-066: Width Below 60 Columns Minimal View
**Section:** 4.6
**Category:** integration
**Priority:** medium
**Description:** Below 60 columns, switch to minimal view (icon + status only)
**Test:** No task names displayed, only icons and status
**Fixture/Setup:** Terminal width 59
**Edge Cases:** Very narrow terminals

---

## Section 5: JSONL Callback and Parsing

### TC-067: ansible.posix Availability Check
**Section:** 5.1
**Category:** integration
**Priority:** critical
**Description:** AOM checks if ansible.posix collection is installed at startup
**Test:** `ansible-galaxy collection list | grep ansible.posix` executed; failure prompts for install
**Fixture/Setup:** Environment with/without ansible.posix
**Edge Cases:** ansible-galaxy command not found

### TC-068: ansible.posix Install Prompt
**Section:** 5.1
**Category:** integration
**Priority:** high
**Description:** If ansible.posix missing, prompt user to install
**Test:** Prompt shows "ansible.posix collection not found. Install? [Y/n]"
**Fixture/Setup:** Missing ansible.posix
**Edge Cases:** User declines install (exit with instructions)

### TC-069: ansible-core Version Check
**Section:** 5.1
**Category:** integration
**Priority:** high
**Description:** AOM requires ansible-core >= 2.14 for JSONL callback support
**Test:** Version check at startup; error if below minimum
**Fixture/Setup:** Various ansible-core versions
**Edge Cases:** ansible-core not installed

### TC-070: ansible.posix Version Check
**Section:** 5.1
**Category:** integration
**Priority:** high
**Description:** AOM requires ansible.posix >= 1.5.0 for JSONL callback with path field
**Test:** Version check at startup; warning if below minimum
**Fixture/Setup:** Various ansible.posix versions
**Edge Cases:** ansible.posix not installed

### TC-071: JSONL Environment Variable
**Section:** 5.1
**Category:** integration
**Priority:** critical
**Description:** AOM sets ANSIBLE_STDOUT_CALLBACK=ansible.posix.jsonl when spawning ansible-playbook
**Test:** Subprocess environment contains correct callback setting
**Fixture/Setup:** Process spawn capture
**Edge Cases:** User overrides callback in args

### TC-072: Event Type - v2_playbook_on_start
**Section:** 5.1
**Category:** unit
**Priority:** critical
**Description:** v2_playbook_on_start event parsed correctly
**Test:** Event contains _event field and _timestamp; playbook start recorded
**Fixture/Setup:** JSONL event sample
**Edge Cases:** Missing timestamp field

### TC-073: Event Type - v2_playbook_on_play_start
**Section:** 5.1
**Category:** unit
**Priority:** critical
**Description:** v2_playbook_on_play_start event parsed with play.id, play.name, play.path
**Test:** PlayRunState created with correct UUID and name
**Fixture/Setup:** JSONL event sample
**Edge Cases:** Missing play.id

### TC-074: Event Type - v2_runner_on_start
**Section:** 5.1
**Category:** unit
**Priority:** critical
**Description:** v2_runner_on_start event (non-lockstep strategies) parsed with task.id and hosts
**Test:** TaskRunState created; hosts dict populated
**Fixture/Setup:** JSONL event sample for free strategy
**Edge Cases:** Event with no hosts field

### TC-075: Event Type - v2_playbook_on_task_start
**Section:** 5.1
**Category:** unit
**Priority:** critical
**Description:** v2_playbook_on_task_start event (lockstep) parsed with task.id, task.name, is_conditional
**Test:** TaskRunState created with one entry per task (not per host)
**Fixture/Setup:** JSONL event sample for linear strategy
**Edge Cases:** Missing is_conditional field

### TC-076: Event Type - v2_playbook_on_handler_task_start
**Section:** 5.1
**Category:** unit
**Priority:** medium
**Description:** v2_playbook_on_handler_task_start event parsed and marked as handler
**Test:** TaskDefinition marked as handler type
**Fixture/Setup:** Handler task JSONL sample
**Edge Cases:** Handler with no parent task

### TC-077: Event Type - v2_runner_on_ok
**Section:** 5.1
**Category:** unit
**Priority:** critical
**Description:** v2_runner_on_ok event parsed with hosts result (changed, action, _ansible_no_log)
**Test:** HostRunState status=OK; changed flag set correctly
**Fixture/Setup:** JSONL ok event sample
**Edge Cases:** changed=true vs changed=false

### TC-078: Event Type - v2_runner_on_failed
**Section:** 5.1
**Category:** unit
**Priority:** critical
**Description:** v2_runner_on_failed event parsed with hosts result (failed, rc, cmd, msg, stderr)
**Test:** HostRunState status=FAILED; error message captured
**Fixture/Setup:** JSONL failed event sample
**Edge Cases:** Missing stderr/stdout fields

### TC-079: Event Type - v2_runner_on_skipped
**Section:** 5.1
**Category:** unit
**Priority:** high
**Description:** v2_runner_on_skipped event parsed with hosts result (skipped, skip_reason)
**Test:** HostRunState status=SKIPPED; skip_reason captured
**Fixture/Setup:** JSONL skipped event sample
**Edge Cases:** Empty skip_reason

### TC-080: Event Type - v2_runner_on_unreachable
**Section:** 5.1
**Category:** unit
**Priority:** critical
**Description:** v2_runner_on_unreachable event parsed with hosts result (unreachable, msg)
**Test:** HostRunState status=UNREACHABLE; error message captured
**Fixture/Setup:** JSONL unreachable event sample
**Edge Cases:** None

### TC-081: Event Type - v2_playbook_on_stats
**Section:** 5.1
**Category:** unit
**Priority:** critical
**Description:** v2_playbook_on_stats event parsed with per-host stats (ok, changed, failures, skipped, unreachable, rescued, ignored)
**Test:** Final statistics match aggregated state
**Fixture/Setup:** JSONL stats event sample
**Edge Cases:** Empty stats dict

### TC-082: Strategy Detection - Linear
**Section:** 5.1
**Category:** integration
**Priority:** high
**Description:** AOM detects linear strategy from v2_playbook_on_task_start WITHOUT prior v2_runner_on_start
**Test:** First task event after play_start sets detected_strategy="linear"
**Fixture/Setup:** JSONL stream with linear pattern
**Edge Cases:** Mixed events (unusual)

### TC-083: Strategy Detection - Free
**Section:** 5.1
**Category:** integration
**Priority:** high
**Description:** AOM detects free/host_pinned strategy from v2_runner_on_start events
**Test:** First runner_on_start event sets detected_strategy="free"
**Fixture/Setup:** JSONL stream with free pattern
**Edge Cases:** None

### TC-084: Timestamp Format - ISO 8601 UTC
**Section:** 5.1
**Category:** unit
**Priority:** high
**Description:** All _timestamp values are ISO 8601 UTC (e.g., "2025-11-09T15:00:00.100000Z")
**Test:** Timestamp parsing succeeds; stored as UTC
**Fixture/Setup:** JSONL event samples
**Edge Cases:** Invalid timestamp format

### TC-085: Timestamp Display - Local Timezone
**Section:** 5.1
**Category:** unit
**Priority:** medium
**Description:** Display converts UTC timestamps to local timezone
**Test:** displayed_time = fromisoformat(ts).astimezone()
**Fixture/Setup:** Known UTC timestamp
**Edge Cases:** Timezone-aware display issues

### TC-086: Elapsed Time Calculation
**Section:** 5.1
**Category:** unit
**Priority:** medium
**Description:** Elapsed time calculated as now - start_time in UTC, displayed as HH:MM:SS
**Test:** Elapsed displays correctly formatted
**Fixture/Setup:** Known start time
**Edge Cases:** Long durations (24+ hours)

---

## Section 5.2: Pre-Parse Phase

### TC-087: Parallel Pre-Parse Execution
**Section:** 5.2
**Category:** integration
**Priority:** critical
**Description:** --list-tasks and --list-hosts run in parallel during LOADING_TASKS phase
**Test:** Both commands execute concurrently; results combined after both complete
**Fixture/Setup:** Playbook with multiple plays
**Edge Cases:** One command fails before other completes

### TC-088: Pre-Parse Result Assembly
**Section:** 5.2
**Category:** integration
**Priority:** high
**Description:** PreParseResult contains plays (from --list-tasks) and play_hosts (from --list-hosts)
**Test:** Result has both structures populated
**Fixture/Setup:** Valid playbook
**Edge Cases:** None

### TC-089: --list-hosts Fallback
**Section:** 5.2
**Category:** integration
**Priority:** high
**Description:** If --list-hosts fails, fall back to incremental host list from runner events
**Test:** Warning logged; hosts appear as tasks execute
**Fixture/Setup:** Playbook with Jinja2 in hosts field
**Edge Cases:** Both --list-hosts AND runner events fail to provide hosts

### TC-090: --list-hosts Fallback Warning Message
**Section:** 5.2
**Category:** integration
**Priority:** medium
**Description:** Fallback shows warning "Host resolution failed, hosts will appear as tasks execute"
**Test:** Warning message logged/displayed
**Fixture/Setup:** Invalid hosts pattern
**Edge Cases:** None

### TC-091: Task Matching by UUID
**Section:** 5.2
**Category:** unit
**Priority:** high
**Description:** Primary matching method uses task.id (UUID from JSONL)
**Test:** TaskDefinition matched correctly by UUID
**Fixture/Setup:** UUIDs from --list-tasks and JSONL events
**Edge Cases:** UUID collision (extremely rare)

### TC-092: Task Matching by Path
**Section:** 5.2
**Category:** unit
**Priority:** medium
**Description:** Secondary matching uses task.path (file:line format)
**Test:** Match succeeds when path matches but UUID differs
**Fixture/Setup:** TaskDefinitions with path info
**Edge Cases:** Path missing or malformed

### TC-093: Task Matching by Sequential + Name
**Section:** 5.2
**Category:** unit
**Priority:** medium
**Description:** Fallback matching uses play_order, task_order, and normalized name
**Test:** Match succeeds when no UUID or path match
**Fixture/Setup:** TaskDefinitions with ordering fields
**Edge Cases:** Name normalization differences

### TC-094: include_tasks Dynamic Expansion
**Section:** 5.2
**Category:** integration
**Priority:** high
**Description:** Tasks from include_tasks not in --list-tasks output are created dynamically as children
**Test:** Dynamic tasks have is_dynamic=True, task_order=-1, parent relationship set
**Fixture/Setup:** Playbook with include_tasks
**Edge Cases:** Nested include_tasks

### TC-095: Dynamic Task Parent Relationship
**Section:** 5.2
**Category:** unit
**Priority:** high
**Description:** Dynamic tasks are children of the include_tasks node
**Test:** parent_task.children contains dynamic task
**Fixture/Setup:** include_tasks with dynamic tasks
**Edge Cases:** Orphan dynamic task (no parent)

### TC-096: Dynamic Task Ordering
**Section:** 5.2
**Category:** unit
**Priority:** medium
**Description:** Dynamic tasks have task_order=-1 (placed after pre-parsed siblings)
**Test:** Dynamic tasks appear after static siblings in display
**Fixture/Setup:** Mixed static and dynamic tasks
**Edge Cases:** All dynamic tasks (no static)

---

## Section 5.2.1: --list-hosts Output Parsing

### TC-097: --list-hosts Play Pattern Parsing
**Section:** 5.2.1
**Category:** unit
**Priority:** critical
**Description:** Parse play line format: "play #N (hosts): name\tTAGS: [tags]"
**Test:** Regex correctly extracts play number, hosts pattern, name, tags
**Fixture/Setup:** Sample --list-hosts output
**Edge Cases:** Empty tags, special characters in name

### TC-098: --list-hosts Hostname Extraction
**Section:** 5.2.1
**Category:** unit
**Priority:** critical
**Description:** Parse hostnames from 6-space indented lines
**Test:** All hostnames extracted correctly
**Fixture/Setup:** Multi-play --list-hosts output
**Edge Cases:** Hostname with special characters

### TC-099: --list-hosts Skip Non-Host Lines
**Section:** 5.2.1
**Category:** unit
**Priority:** high
**Description:** Parser skips 'pattern:', 'hosts (N):', 'tasks:', and blank lines
**Test:** result dict contains only plays and hostnames
**Fixture/Setup:** Full --list-hosts output
**Edge Cases:** None

### TC-100: --list-hosts Localhost Handling
**Section:** 5.2.1
**Category:** integration
**Priority:** high
**Description:** hosts: localhost returns ['localhost']
**Test:** Localhost play resolves correctly
**Fixture/Setup:** Playbook targeting localhost
**Edge Cases:** localhost with connection options

### TC-101: --list-hosts 'all' Handling
**Section:** 5.2.1
**Category:** integration
**Priority:** high
**Description:** hosts: all returns all inventory hosts
**Test:** All hosts from inventory appear
**Fixture/Setup:** Inventory with multiple hosts
**Edge Cases:** Empty inventory

### TC-102: --list-hosts Pattern Filtering
**Section:** 5.2.1
**Category:** integration
**Priority:** high
**Description:** hosts: webservers:!db_primary returns filtered set
**Test:** Pattern resolution by Ansible
**Fixture/Setup:** Inventory with groups
**Edge Cases:** Invalid pattern

### TC-103: --list-hosts Dynamic Pattern Fallback
**Section:** 5.2.1
**Category:** integration
**Priority:** medium
**Description:** hosts: "{{ dynamic_group }}" may not expand; fall back to runner events
**Test:** Fallback triggered when --list-hosts fails
**Fixture/Setup:** Playbook with Jinja2 hosts
**Edge Cases:** None

### TC-104: --list-hosts with --limit
**Section:** 5.2.1
**Category:** integration
**Priority:** medium
**Description:** Pattern resolved, then --limit applied
**Test:** Hosts list respects --limit flag
**Fixture/Setup:** Inventory larger than limit
**Edge Cases:** Limit excludes all hosts

### TC-105: --list-hosts Empty Inventory
**Section:** 5.2.1
**Category:** integration
**Priority:** medium
**Description:** Empty inventory yields hosts (0): and empty list
**Test:** Result dict has empty hosts list
**Fixture/Setup:** Empty inventory
**Edge Cases:** None

### TC-106: --list-hosts Dynamic Inventory
**Section:** 5.2.1
**Category:** integration
**Priority:** medium
**Description:** Dynamic inventory (AWS) works but may be slow
**Test:** Hosts resolved after API calls complete
**Fixture/Setup:** AWS dynamic inventory config
**Edge Cases:** Timeout during resolution

---

## Section 5.3: --list-tasks Output Parsing

### TC-107: --list-tasks No JSON Output
**Section:** 5.3
**Category:** unit
**Priority:** critical
**Description:** --list-tasks output is always plain text; no JSON mode
**Test:** Parser handles only text format
**Fixture/Setup:** --list-tasks output sample
**Edge Cases:** Attempt to use invalid --json flag

### TC-108: --list-tasks TAB Separator
**Section:** 5.3
**Category:** unit
**Priority:** critical
**Description:** Separator between task name and TAGS: is literal TAB character (0x09)
**Test:** Parser uses TAB in regex, not spaces
**Fixture/Setup:** Output with TAB characters
**Edge Cases:** Tabs in task name

### TC-109: --list-tasks Play Indent
**Section:** 5.3
**Category:** unit
**Priority:** high
**Description:** Play lines have exactly 2-space indent
**Test:** Parser recognizes play lines by 2-space prefix
**Fixture/Setup:** Sample output
**Edge Cases:** Indentation varies (invalid playbook)

### TC-110: --list-tasks Task Indent
**Section:** 5.3
**Category:** unit
**Priority:** high
**Description:** Task lines have exactly 6-space indent
**Test:** Parser recognizes task lines by 6-space prefix
**Fixture/Setup:** Sample output
**Edge Cases:** Indentation varies

### TC-111: --list-tasks Role Prefix Format
**Section:** 5.3
**Category:** unit
**Priority:** high
**Description:** Role prefix format is "role_name : task_name" (space-colon-space)
**Test:** Parser extracts role and task name correctly
**Fixture/Setup:** Tasks with role prefix
**Edge Cases:** Task name containing " : "

### TC-112: --list-tasks Playbook Header
**Section:** 5.3
**Category:** unit
**Priority:** medium
**Description:** First line is "playbook: <path>" followed by blank line
**Test:** Parser skips header line and blank
**Fixture/Setup:** Full output sample
**Edge Cases:** Malformed header

### TC-113: --list-tasks include_tasks NOT Expanded
**Section:** 5.3
**Category:** integration
**Priority:** critical
**Description:** include_tasks shown as single task entry (NOT expanded)
**Test:** Single task appears for include_tasks
**Fixture/Setup:** Playbook with include_tasks
**Edge Cases:** None

### TC-114: --list-tasks import_tasks IS Expanded
**Section:** 5.3
**Category:** integration
**Priority:** critical
**Description:** import_tasks expanded inline without prefix
**Test:** Imported tasks appear in output without special marker
**Fixture/Setup:** Playbook with import_tasks
**Edge Cases:** Missing imported file

### TC-115: --list-tasks Blocks Flattened
**Section:** 5.3
**Category:** integration
**Priority:** high
**Description:** Blocks are flattened; no block container in output
**Test:** Tasks in blocks appear as flat list
**Fixture/Setup:** Playbook with blocks
**Edge Cases:** Nested blocks

### TC-116: --list-tasks pre_tasks/post_tasks
**Section:** 5.3
**Category:** integration
**Priority:** medium
**Description:** pre_tasks and post_tasks appear as regular tasks (no prefix indicating type)
**Test:** No special distinction in output
**Fixture/Setup:** Playbook with pre_tasks/post_tasks
**Edge Cases:** None

### TC-117: --list-tasks Unnamed Task Fallback
**Section:** 5.3
**Category:** unit
**Priority:** medium
**Description:** Unnamed tasks use module name or hosts pattern as fallback
**Test:** Task name derives from module when unnamed
**Fixture/Setup:** Playbook with unnamed tasks
**Edge Cases:** None

### TC-118: --list-tasks Output to stdout
**Section:** 5.3
**Category:** integration
**Priority:** low
**Description:** All --list-tasks output goes to stdout (even warnings)
**Test:** No stderr output for --list-tasks
**Fixture/Setup:** Capture both streams
**Edge Cases:** Ansible errors to stderr

### TC-119: --list-tasks Exit Code Success
**Section:** 5.3
**Category:** integration
**Priority:** high
**Description:** Exit code 0 for successful --list-tasks
**Test:** Valid playbook yields exit 0
**Fixture/Setup:** Valid playbook
**Edge Cases:** None

### TC-120: --list-tasks Exit Code Error
**Section:** 5.3
**Category:** integration
**Priority:** high
**Description:** Exit code 1 for missing role or file
**Test:** Invalid playbook yields exit 1
**Fixture/Setup:** Playbook with missing role
**Edge Cases:** Role not found message

### TC-121: --list-tasks Exit Code Syntax Error
**Section:** 5.3
**Category:** integration
**Priority:** high
**Description:** Exit code 4 for syntax error in playbook
**Test:** Syntax error yields exit 4
**Fixture/Setup:** Playbook with YAML error
**Edge Cases:** None

---

## Section 5.4: Role Grouping

### TC-122: Role Grouping Threshold
**Section:** 5.4
**Category:** unit
**Priority:** high
**Description:** 5+ consecutive tasks with same role are grouped
**Test:** RoleGroupDefinition created for roles with >= 5 tasks
**Fixture/Setup:** Role with 5+ tasks
**Edge Cases:** Exactly 4 tasks (not grouped)

### TC-123: Role Grouping Display
**Section:** 5.4
**Category:** integration
**Priority:** medium
**Description:** Grouped role displays as "Role: nginx (5 tasks)" with expandable/collapsible children
**Test:** Tree view shows role as collapsible node
**Fixture/Setup:** Mock state with grouped role
**Edge Cases:** None

---

## Section 5.5: PTY with pexpect

### TC-124: pexpect Spawn Configuration
**Section:** 5.5
**Category:** integration
**Priority:** critical
**Description:** pexpect.spawn uses encoding='utf-8', timeout=300, and ANSIBLE_STDOUT_CALLBACK env var
**Test:** subprocess spawned with correct parameters
**Fixture/Setup:** Mock pexpect
**Edge Cases:** timeout=300 expiration

### TC-125: pexpect Cancellation
**Section:** 5.5
**Category:** integration
**Priority:** critical
**Description:** worker.is_cancelled triggers child.sendintr() and child.close()
**Test:** Cancellation properly terminates subprocess
**Fixture/Setup:** Mock worker, running subprocess
**Edge Cases:** Subprocess doesn't respond to SIGINT

### TC-126: pexpect Stream Processing
**Section:** 5.5
**Category:** integration
**Priority:** high
**Description:** pexpect.expect([pexpect.EOF, '\n']) with timeout=0.1 for non-blocking reads
**Test:** Lines processed as they arrive; EOF detected
**Fixture/Setup:** Mock pexpect buffer
**Edge Cases:** Partial line at EOF

### TC-127: pexpect Thread Worker Pattern
**Section:** 5.5
**Category:** integration
**Priority:** high
**Description:** @work(thread=True, exclusive=True) used for playbook execution
**Test:** Worker runs in separate thread; exclusive access enforced
**Fixture/Setup:** Thread worker mock
**Edge Cases:** Worker cancellation during startup

---

## Section 5.6: PTY Stream Parsing Design

### TC-128: Stream Phase - PRE_RUN_PROMPTS
**Section:** 5.6
**Category:** unit
**Priority:** critical
**Description:** Initial phase before v2_playbook_on_start; password prompts may appear
**Test:** State machine starts in PRE_RUN_PROMPTS; transitions on v2_playbook_on_start
**Fixture/Setup:** PtyStreamParser instance
**Edge Cases:** Multiple prompts before start

### TC-129: Stream Phase - EXECUTION
**Section:** 5.6
**Category:** unit
**Priority:** critical
**Description:** Main phase for JSONL events; warnings may interleave
**Test:** Transitions from PRE_RUN_PROMPTS; JSONL events parsed
**Fixture/Setup:** PtyStreamParser with JSONL events
**Edge Cases:** Non-JSON lines during execution

### TC-130: Stream Phase - POST_RUN_RECAP
**Section:** 5.6
**Category:** unit
**Priority:** critical
**Description:** Final phase after v2_playbook_on_stats; plaintext PLAY RECAP may follow
**Test:** Transitions on v2_playbook_on_stats; plaintext captured
**Fixture/Setup:** PtyStreamParser with stats event
**Edge Cases:** No recap output

### TC-131: Phase Transition - Start Event
**Section:** 5.6
**Category:** integration
**Priority:** high
**Description:** v2_playbook_on_start event triggers PRE_RUN_PROMPTS → EXECUTION transition
**Test:** Phase changes after parsing start event
**Fixture/Setup:** Stream with start event
**Edge Cases:** Multiple start events (invalid)

### TC-132: Phase Transition - Stats Event
**Section:** 5.6
**Category:** integration
**Priority:** high
**Description:** v2_playbook_on_stats event triggers EXECUTION → POST_RUN_RECAP transition
**Test:** Phase changes after parsing stats event
**Fixture/Setup:** Stream with stats event
**Edge Cases:** None

### TC-133: Password Pattern Detection
**Section:** 5.6
**Category:** unit
**Priority:** critical
**Description:** All PASSWORD_PATTERNS correctly match known prompts
**Test:** Each pattern matches its corresponding prompt type
**Fixture/Setup:** PASSWORD_PATTERNS list
**Edge Cases:** Variant prompt formats

### TC-134: Password Patterns - Vault Password
**Section:** 5.6
**Category:** unit
**Priority:** high
**Description:** Pattern r'Vault password: ' detected
**Test:** "Vault password: " matches; "Vault password (id): " matches
**Fixture/Setup:** Regex pattern
**Edge Cases:** None

### TC-135: Password Patterns - Vault ID Variant
**Section:** 5.6
**Category:** unit
**Priority:** high
**Description:** Pattern r'Vault password \([^)]+\): ' detected for vault_id variant
**Test:** "Vault password (prod): " matches
**Fixture/Setup:** Regex pattern
**Edge Cases:** None

### TC-136: Password Patterns - SSH Password
**Section:** 5.6
**Category:** unit
**Priority:** high
**Description:** Pattern r'SSH password: ' detected
**Test:** "SSH password: " matches
**Fixture/Setup:** Regex pattern
**Edge Cases:** None

### TC-137: Password Patterns - BECOME Password
**Section:** 5.6
**Category:** unit
**Priority:** high
**Description:** Pattern r'BECOME password: ' detected
**Test:** "BECOME password: " matches
**Fixture/Setup:** Regex pattern
**Edge Cases:** None

### TC-138: Password Patterns - BECOME Default Variant
**Section:** 5.6
**Category:** unit
**Priority:** medium
**Description:** Pattern r'BECOME password\[defaults to SSH password\]: ' detected
**Test:** "BECOME password[defaults to SSH password]: " matches
**Fixture/Setup:** Regex pattern
**Edge Cases:** None

### TC-139: Password Patterns - New Vault Password
**Section:** 5.6
**Category:** unit
**Priority:** medium
**Description:** Patterns r'New Vault password: ' and r'Confirm New Vault password: ' detected
**Test:** Both match their respective prompts
**Fixture/Setup:** Regex patterns
**Edge Cases:** None

### TC-140: PLAY RECAP Detection
**Section:** 5.6
**Category:** unit
**Priority:** high
**Description:** RECAP_PATTERN r'^PLAY RECAP \*{5,}' correctly matches recap section
**Test:** "PLAY RECAP ************" matches
**Fixture/Setup:** Regex pattern
**Edge Cases:** Exact asterisk count

### TC-141: Warning Pattern Detection
**Section:** 5.6
**Category:** unit
**Priority:** medium
**Description:** WARNING_PATTERNS match [WARNING]:, [DEPRECATION WARNING]:, and [DEPRECATED]: prefixes
**Test:** All three warning types classified correctly: regular WARNING, active deprecation warning, and removed-feature deprecation
**Fixture/Setup:** WARNING_PATTERNS list with all three patterns
**Edge Cases:** Multi-line warnings, [DEPRECATED]: vs [DEPRECATION WARNING]: distinction

### TC-142: _handle_plaintext Classification
**Section:** 5.6
**Category:** unit
**Priority:** high
**Description:** Non-JSON lines classified as: password prompt, PLAY RECAP, warning, or other
**Test:** Each classification routes to correct handler
**Fixture/Setup:** Sample plaintext lines
**Edge Cases:** Ambiguous classifications

---

## Section 5.10: Password Prompt Handling

### TC-143: Password Prompt PTY Integration
**Section:** 5.10
**Category:** integration
**Priority:** critical
**Description:** pexpect spawns process with PTY; Ansible's getpass reads from /dev/tty
**Test:** PTY mode allows password prompts to pass through
**Fixture/Setup:** Mock pexpect with PTY
**Edge Cases:** PTY allocation failure

### TC-144: Compact Mode Password Flow
**Section:** 5.10
**Category:** integration
**Priority:** critical
**Description:** Compact mode: stop Live → show prompt → read password → start Live
**Test:** Live.stop() and Live.start() called around password input
**Fixture/Setup:** Mock Rich Live
**Edge Cases:** Password prompt timeout

### TC-145: Compact Mode Terminal Pass-Through
**Section:** 5.10
**Category:** integration
**Priority:** high
**Description:** User types password directly; Ansible's getpass handles masking
**Test:** Password not visible in output; entered password sent to PTY
**Fixture/Setup:** Mock terminal, mock getpass
**Edge Cases:** Empty password, very long password

### TC-146: TUI Mode Password Modal
**Section:** 5.10
**Category:** integration
**Priority:** critical
**Description:** TUI mode: detect prompt → call_from_thread → show Textual modal → block worker → send password
**Test:** Modal appears; worker blocked until password entered
**Fixture/Setup:** Textual app mock
**Edge Cases:** Modal timeout

### TC-147: TUI Mode Password Masking
**Section:** 5.10
**Category:** unit
**Priority:** high
**Description:** TUI modal uses Input(password=True) for masking
**Test:** Password displays as asterisks or dots
**Fixture/Setup:** Textual Input widget
**Edge Cases:** Empty password

### TC-148: Password Timeout Default
**Section:** 5.10
**Category:** integration
**Priority:** medium
**Description:** Password prompt times out after 60 seconds
**Test:** Timeout raises exception or cancels
**Fixture/Setup:** Mock clock
**Edge Cases:** Timeout exactly at 60s

---

## Section 5.8: Host Name Resolution

### TC-149: --list-hosts Resolves Hostnames
**Section:** 5.8
**Category:** integration
**Priority:** critical
**Description:** --list-hosts populates PlayDefinition.resolved_hosts during LOADING_TASKS
**Test:** resolved_hosts list populated after pre-parse
**Fixture/Setup:** Valid playbook and inventory
**Edge Cases:** None

### TC-150: Host Cross-Check During Execution
**Section:** 5.8
**Category:** integration
**Priority:** high
**Description:** Runner event hostnames matched against resolved_hosts; new hosts logged as WARNING
**Test:** New hosts trigger warning log
**Fixture/Setup:** Runner event with unexpected host
**Edge Cases:** Host name normalization

### TC-151: Host Fallback After --list-hosts Failure
**Section:** 5.8
**Category:** integration
**Priority:** high
**Description:** If --list-hosts fails, resolved_hosts starts empty; populated by runner events
**Test:** Fallback builds host list incrementally
**Fixture/Setup:** Mock --list-hosts failure
**Edge Cases:** First runner event before fallback setup

### TC-152: v2_playbook_on_stats Cross-Check
**Section:** 5.8
**Category:** integration
**Priority:** medium
**Description:** Final stats event cross-checks collected hosts; missing hosts logged
**Test:** Discrepancy logged at completion
**Fixture/Setup:** Stats event with hosts not seen during run
**Edge Cases:** None

---

## Section 5.9: Password/Secret Redaction

### TC-153: Layer 1 - _ansible_no_log Flag
**Section:** 5.9
**Category:** unit
**Priority:** critical
**Description:** When res._ansible_no_log==True, entire result replaced with {'censored': '(no_log)'}
**Test:** Result censored; sensitive data removed
**Fixture/Setup:** Event with _ansible_no_log=True
**Edge Cases:** Nested structures with _ansible_no_log

### TC-154: Layer 1 - Loop Item _ansible_no_log
**Section:** 5.9
**Category:** unit
**Priority:** high
**Description:** Loop items with _ansible_no_log are individually censored
**Test:** Each censored loop item replaced
**Fixture/Setup:** Event with loop results and per-item _ansible_no_log
**Edge Cases:** Mixed loop items (some censored, some not)

### TC-155: Layer 2 - PASSWORD_MATCH Regex
**Section:** 5.9
**Category:** unit
**Priority:** critical
**Description:** PASSWORD_MATCH matches password field names (pass, password, passphrase, etc.)
**Test:** Regex matches known password variants
**Fixture/Setup:** PASSWORD_MATCH regex
**Edge Cases:** False positives (passenger, bypass)

### TC-156: Layer 2 - ANSIBLE_PASSWORD_FIELDS
**Section:** 5.9
**Category:** unit
**Priority:** high
**Description:** ANSIBLE_PASSWORD_FIELDS contains ansible_ssh_pass, ansible_password, ansible_become_pass, etc.
**Test:** All fields in set are redacted
**Fixture/Setup:** ANSIBLE_PASSWORD_FIELDS set
**Edge Cases:** None

### TC-157: Layer 2 - GENERIC_SECRET_FIELDS
**Section:** 5.9
**Category:** unit
**Priority:** high
**Description:** GENERIC_SECRET_FIELDS contains api_key, api_token, secret, token, auth_token, etc.
**Test:** All fields in set are redacted
**Fixture/Setup:** GENERIC_SECRET_FIELDS set
**Edge Cases:** None

### TC-158: Layer 2 - Recursive Redaction
**Section:** 5.9
**Category:** unit
**Priority:** high
**Description:** redact_dict recursively processes nested dicts and lists
**Test:** Nested password fields at any depth are redacted
**Fixture/Setup:** Nested dict with password fields
**Edge Cases:** Max depth (10) truncation

### TC-159: Layer 2 - Whitelist False Positives
**Section:** 5.9
**Category:** unit
**Priority:** high
**Description:** PASSWORD_WHITELIST prevents false positive redaction (passenger_version, bypass, etc.)
**Test:** Whitelisted fields NOT redacted
**Fixture/Setup:** Event with passenger_version field
**Edge Cases:** Configured custom whitelist

### TC-160: Layer 3 - URL Credential Sanitization
**Section:** 5.9
**Category:** unit
**Priority:** high
**Description:** URL_CRED_PATTERN redacts protocol://user:password@host format
**Test:** "mysql://admin:secret123@db.example.com" becomes "mysql://admin:********@db.example.com"
**Fixture/Setup:** URL with credentials
**Edge Cases:** URL-encoded passwords

### TC-161: Layer 3 - CLI Credential Sanitization
**Section:** 5.9
**Category:** unit
**Priority:** high
**Description:** CLI_CRED_PATTERN redacts --password=xxx, --token=xxx, --secret=xxx
**Test:** "--password=secret123" becomes "--password=********"
**Fixture/Setup:** Command string with credentials
**Edge Cases:** Variant formats (`--pass=`, `--pwd=`)

### TC-162: Layer 3 - Applied Fields
**Section:** 5.9
**Category:** integration
**Priority:** high
**Description:** Sanitization applied to res.cmd, res.stdout, res.stderr, res.msg fields
**Test:** All four fields sanitized
**Fixture/Setup:** Event with all fields populated
**Edge Cases:** Missing fields

### TC-163: Layer 4 - invocation.module_args Redaction
**Section:** 5.9
**Category:** unit
**Priority:** high
**Description:** At -vvv verbosity, invocation.module_args is recursively redacted
**Test:** Nested module args with passwords redacted
**Fixture/Setup:** Verbose event with invocation
**Edge Cases:** Deeply nested args

### TC-164: Redaction Always On
**Section:** 5.9
**Category:** integration
**Priority:** critical
**Description:** No --no-redact flag; redaction always active
**Test:** No command-line flag to disable redaction
**Fixture/Setup:** Argument parser
**Edge Cases:** None

### TC-165: Redaction in Compact Display
**Section:** 5.9
**Category:** integration
**Priority:** critical
**Description:** Compact mode displays redacted values as "********"
**Test:** Password values show as asterisks
**Fixture/Setup:** Event with password in log
**Edge Cases:** None

### TC-166: Redaction in TUI Display
**Section:** 5.9
**Category:** integration
**Priority:** critical
**Description:** TUI mode displays redacted values in tree, log, and summary panels
**Test:** All panels show "********" for sensitive fields
**Fixture/Setup:** TUI render with sensitive data
**Edge Cases:** None

### TC-167: Redaction in Inspect Output
**Section:** 5.9
**Category:** integration
**Priority:** critical
**Description:** `aom inspect` command output redacts sensitive values
**Test:** Inspect shows "********" for password fields
**Fixture/Setup:** Session artifact with sensitive data
**Edge Cases:** None

### TC-168: Redaction in JSON Output
**Section:** 5.9
**Category:** integration
**Priority:** critical
**Description:** `aom inspect --json` output redacts sensitive values
**Test:** JSON contains "********" for password fields
**Fixture/Setup:** JSON export
**Edge Cases:** None

### TC-169: Redaction in Session Artifacts
**Section:** 5.9
**Category:** integration
**Priority:** critical
**Description:** .aom session artifacts are always redacted
**Test:** Artifact file contains no plaintext passwords
**Fixture/Setup:** Written .aom file
**Edge Cases:** None

### TC-170: RedactionConfig Model
**Section:** 5.9
**Category:** unit
**Priority:** medium
**Description:** RedactionConfig has whitelist, custom_fields, custom_patterns fields
**Test:** Pydantic model validates config structure
**Fixture/Setup:** config.yaml with redaction section
**Edge Cases:** Invalid pattern regex

### TC-171: RedactionConfig Custom Whitelist
**Section:** 5.9
**Category:** unit
**Priority:** medium
**Description:** Config whitelist extends PASSWORD_WHITELIST
**Test:** Custom whitelist fields not redacted
**Fixture/Setup:** Config with custom whitelist
**Edge Cases:** None

### TC-172: RedactionConfig Custom Fields
**Section:** 5.9
**Category:** unit
**Priority:** medium
**Description:** Config custom_fields adds fields to redact
**Test:** my_secret_var redacted per config
**Fixture/Setup:** Config with custom_fields
**Edge Cases:** None

### TC-173: RedactionConfig Custom Patterns
**Section:** 5.9
**Category:** unit
**Priority:** medium
**Description:** Config custom_patterns adds regex patterns for string sanitization
**Test:** "--db-password=\S+" pattern redacts matching strings
**Fixture/Setup:** Config with custom_patterns
**Edge Cases:** Invalid regex pattern

---

## Section 6: State Management

### Section 6.1: Data Models

### TC-174: TaskDefinition Field Validation
**Section:** 6.1
**Category:** unit
**Priority:** critical
**Description:** Validate all TaskDefinition dataclass fields are initialized correctly with correct types
**Test:** Create TaskDefinition with all required fields; assert each field has correct type and value
**Fixture/Setup:** Sample task definition data from mock --list-tasks output
**Edge Cases:** role=None, uuid=None, path=None, children empty list, task_order=-1 for dynamic tasks

### TC-175: TaskDefinition is_dynamic Flag Default
**Section:** 6.1
**Category:** unit
**Priority:** high
**Description:** Verify is_dynamic defaults to False for static tasks
**Test:** Create TaskDefinition without is_dynamic; assert defaults to False
**Fixture/Setup:** None
**Edge Cases:** Dynamic child tasks should have parent reference via children list

### TC-176: TaskDefinition UUID Field Nullability
**Section:** 6.1
**Category:** unit
**Priority:** high
**Description:** UUID is None before JSONL matching, populated after matching via event
**Test:** Create TaskDefinition before JSONL event; assert uuid=None. After matching, assert uuid populated
**Fixture/Setup:** Mock JSONL event with task.id field
**Edge Cases:** UUID may remain None if task never matched

### TC-177: TaskDefinition Path Field Nullability
**Section:** 6.1
**Category:** unit
**Priority:** high
**Description:** path is None before JSONL matching, populated with file:line format after matching
**Test:** Create TaskDefinition; assert path=None. After matching, assert path contains valid file:line format
**Fixture/Setup:** Mock JSONL event with task.path field
**Edge Cases:** Path format validation - must contain colon separating file and line number

### TC-178: TaskDefinition children Field Default
**Section:** 6.1
**Category:** unit
**Priority:** high
**Description:** children defaults to empty list; populated with TaskDefinition objects for dynamic children
**Test:** Create TaskDefinition without children; assert children=[]
**Fixture/Setup:** Mock include_tasks expansion with multiple dynamic tasks
**Edge Cases:** Nested include_tasks (children of children)

### TC-179: TaskDefinition task_order for Dynamic Tasks
**Section:** 6.1
**Category:** unit
**Priority:** high
**Description:** task_order is -1 for dynamic tasks (created at runtime)
**Test:** Create static task with task_order >= 0. Create dynamic task with task_order=-1; assert preserved
**Fixture/Setup:** None
**Edge Cases:** task_order=-1 indicates lookup should use UUID or path matching

### TC-180: RoleGroupDefinition Initialization
**Section:** 6.1
**Category:** unit
**Priority:** high
**Description:** RoleGroupDefinition groups consecutive same-role tasks with name property
**Test:** Create RoleGroupDefinition with role name and task list; assert role, tasks fields correct
**Fixture/Setup:** List of 5+ TaskDefinition objects with same role
**Edge Cases:** Empty tasks list (should not occur per spec)

### TC-181: RoleGroupDefinition Name Property Format
**Section:** 6.1
**Category:** unit
**Priority:** medium
**Description:** name property returns formatted string with role name and task count
**Test:** Create RoleGroupDefinition with 7 tasks; assert name == "Role: nginx (7 tasks)"
**Fixture/Setup:** RoleGroupDefinition with known task count
**Edge Cases:** Role name with special characters, long role names

### TC-182: PlayDefinition Field Validation
**Section:** 6.1
**Category:** unit
**Priority:** critical
**Description:** Validate PlayDefinition fields: id (sequential string), name, hosts (pattern), resolved_hosts (list)
**Test:** Create PlayDefinition with all fields; assert types correct
**Fixture/Setup:** Mock --list-tasks and --list-hosts output
**Edge Cases:** hosts pattern "*" resolves to many hosts

### TC-183: PlayDefinition id Sequential Number Format
**Section:** 6.1
**Category:** unit
**Priority:** high
**Description:** id is sequential number string from --list-tasks (e.g., "1", "2"), NOT UUID
**Test:** Parse plays from --list-tasks; assert id matches sequential position
**Fixture/Setup:** Mock --list-tasks with multiple plays
**Edge Cases:** JSONL events use UUIDs for play.id

### TC-184: PlayDefinition hosts vs resolved_hosts
**Section:** 6.1
**Category:** unit
**Priority:** high
**Description:** hosts contains the host pattern; resolved_hosts contains actual hostnames
**Test:** Create PlayDefinition with hosts="webservers"; assert hosts field is pattern
**Fixture/Setup:** Mock --list-hosts output
**Edge Cases:** resolved_hosts empty if --list-hosts fails

### TC-185: PlayDefinition resolved_hosts Empty List Default
**Section:** 6.1
**Category:** unit
**Priority:** high
**Description:** resolved_hosts defaults to empty list; populated during LOADING_TASKS or from runner events
**Test:** Create PlayDefinition without resolved_hosts; assert defaults to []
**Fixture/Setup:** Mock failed --list-hosts execution
**Edge Cases:** Host pattern matching zero hosts

### TC-186: Status Enum All Values
**Section:** 6.1
**Category:** unit
**Priority:** critical
**Description:** Status enum contains exactly 7 values: PENDING, RUNNING, OK, CHANGED, FAILED, SKIPPED, UNREACHABLE
**Test:** Assert len(Status) == 7. Assert each value exists
**Fixture/Setup:** None
**Edge Cases:** No unknown status values should exist

### TC-187: HostRunState Field Validation
**Section:** 6.1
**Category:** unit
**Priority:** critical
**Description:** HostRunState tracks per-host task execution with hostname, status, changed, message, timestamps
**Test:** Create HostRunState; assert all fields correct types
**Fixture/Setup:** None
**Edge Cases:** start_time set before end_time, changed=True only for CHANGED status

### TC-188: HostRunState Mutable Status Transitions
**Section:** 6.1
**Category:** unit
**Priority:** high
**Description:** HostRunState status updates as task execution progresses
**Test:** Create HostRunState with status=Status.PENDING. Process events; assert status updates
**Fixture/Setup:** Mock runner events for same host
**Edge Cases:** Failed host gets Status.FAILED

### TC-189: TaskRunState Field Validation
**Section:** 6.1
**Category:** unit
**Priority:** critical
**Description:** TaskRunState aggregates per-host states for a single task
**Test:** Create TaskRunState; assert task_id, name, status, hosts dict correct
**Fixture/Setup:** None
**Edge Cases:** hosts dict keyed by hostname string

### TC-190: TaskRunState hosts Dict Key Type
**Section:** 6.1
**Category:** unit
**Priority:** high
**Description:** hosts dictionary uses hostname string as key, HostRunState as value
**Test:** Create TaskRunState; add HostRunState for "web1"; assert hosts["web1"] is HostRunState
**Fixture/Setup:** Sample hostnames from event
**Edge Cases:** Hostname with special characters (dots, underscores)

### TC-191: PlayRunState Field Validation
**Section:** 6.1
**Category:** unit
**Priority:** critical
**Description:** PlayRunState aggregates task states for a single play, including detected_strategy
**Test:** Create PlayRunState; assert play_id, name, status, tasks dict, detected_strategy None default
**Fixture/Setup:** None
**Edge Cases:** detected_strategy None before first task event

### TC-192: PlayRunState detected_strategy Default None
**Section:** 6.1
**Category:** unit
**Priority:** high
**Description:** detected_strategy is None before strategy detection; set on first task or runner event
**Test:** Create PlayRunState; assert detected_strategy is None
**Fixture/Setup:** Mock v2_playbook_on_task_start event
**Edge Cases:** Multiple plays may have different strategies detected independently

### TC-193: PlayRunState detected_strategy Values
**Section:** 6.1
**Category:** unit
**Priority:** high
**Description:** detected_strategy can only be "linear" (lockstep) or "free" (non-lockstep) or None
**Test:** Process v2_playbook_on_task_start; assert detected_strategy="linear"
**Fixture/Setup:** Mock task_start and runner_on_start events
**Edge Cases:** Invalid strategy values should not be set

### TC-194: RunState Top-Level Container
**Section:** 6.1
**Category:** unit
**Priority:** critical
**Description:** RunState is top-level container for entire playbook execution state
**Test:** Create RunState; assert playbook, plays dict, definitions list, start_time, end_time, status correct
**Fixture/Setup:** None
**Edge Cases:** Single playbook run represented by one RunState instance

### TC-195: RunState definitions List
**Section:** 6.1
**Category:** unit
**Priority:** high
**Description:** definitions contains PlayDefinition objects from --list-tasks output
**Test:** Load definitions from --list-tasks; assert len matches play count
**Fixture/Setup:** Mock --list-tasks output with multiple plays
**Edge Cases:** definitions empty if --list-tasks fails

### TC-196: RunState plays Dict Key Type
**Section:** 6.1
**Category:** unit
**Priority:** high
**Description:** plays dictionary uses play UUID/id string as key, PlayRunState as value
**Test:** Create RunState; add PlayRunState with play_id="abc123"; assert plays["abc123"] is PlayRunState
**Fixture/Setup:** Mock play start event with play.id
**Edge Cases:** play.id from JSONL is UUID; mapping to definitions uses play_order position

### Section 6.2: Event Processing

### TC-197: handle_event Dispatcher Routing
**Section:** 6.2
**Category:** unit
**Priority:** critical
**Description:** handle_event routes events to correct handler method based on _event field
**Test:** Call handle_event with event; assert correct handler called
**Fixture/Setup:** RunState instance with mocked handler methods
**Edge Cases:** Missing _event field, empty string _event, unknown event type

### TC-198: handle_event Timestamp Parsing
**Section:** 6.2
**Category:** unit
**Priority:** high
**Description:** Timestamp is parsed from _timestamp field as ISO format datetime
**Test:** Call handle_event with valid ISO timestamp; assert datetime object passed to handler
**Fixture/Setup:** Event with _timestamp="2026-04-20T10:00:00Z"
**Edge Cases:** Invalid timestamp string, missing _timestamp field

### TC-199: handle_event Unknown Event Type Graceful Handling
**Section:** 6.2
**Category:** unit
**Priority:** high
**Description:** Unknown _event types are silently ignored without error
**Test:** Call handle_event with unknown _event; assert no exception raised
**Fixture/Setup:** RunState instance
**Edge Cases:** Future event types added by Ansible should not break AOM

### TC-200: _handle_v2_playbook_on_start Sets Execution Start
**Section:** 6.2
**Category:** integration
**Priority:** critical
**Description:** v2_playbook_on_start event sets RunState.start_time and status to RUNNING
**Test:** Create RunState with status=Status.PENDING. Process v2_playbook_on_start; assert status=Status.RUNNING
**Fixture/Setup:** Mock v2_playbook_on_start event with timestamp
**Edge Cases:** Multiple playbook_on_start events (should not occur)

### TC-201: _handle_v2_playbook_on_play_start Creates PlayRunState
**Section:** 6.2
**Category:** integration
**Priority:** critical
**Description:** v2_playbook_on_play_start creates new PlayRunState entry in plays dict
**Test:** Process v2_playbook_on_play_start with play.id="p1", play.name="Deploy"; assert plays["p1"] exists
**Fixture/Setup:** Mock play_start event with play data
**Edge Cases:** Same play.id seen twice (should update existing, not create duplicate)

### TC-202: _handle_v2_playbook_on_task_start Detects Linear Strategy
**Section:** 6.2
**Category:** integration
**Priority:** high
**Description:** First v2_playbook_on_task_start event sets play.detected_strategy to "linear"
**Test:** Create PlayRunState with detected_strategy=None. Process task_start; assert detected_strategy="linear"
**Fixture/Setup:** Mock task_start event with play.id matching existing PlayRunState
**Edge Cases:** Subsequent task_start events should not change detected_strategy if already set

### TC-203: _handle_v2_runner_on_start Detects Free Strategy
**Section:** 6.2
**Category:** integration
**Priority:** high
**Description:** v2_runner_on_start event (without prior task_start) indicates free strategy
**Test:** Create PlayRunState with detected_strategy=None. Process runner_on_start; assert detected_strategy="free"
**Fixture/Setup:** Mock runner_on_start event with task data
**Edge Cases:** If task_start already occurred, runner_on_start does not change strategy

### TC-204: _handle_v2_runner_on_start Creates TaskRunState
**Section:** 6.2
**Category:** integration
**Priority:** critical
**Description:** v2_runner_on_start creates or updates TaskRunState with status=RUNNING and start_time
**Test:** Process v2_runner_on_start with task.id="t1", task.name="Install nginx"; assert TaskRunState created
**Fixture/Setup:** Runner event with task.id and task.name
**Edge Cases:** Find existing task by UUID match, path match, or sequential+name match

### TC-205: _handle_v2_runner_on_ok Updates HostRunState
**Section:** 6.2
**Category:** integration
**Priority:** critical
**Description:** v2_runner_on_ok creates HostRunState per host with correct status and changed flag
**Test:** Process v2_runner_on_ok with hosts dict; assert HostRunState created with correct status
**Fixture/Setup:** Mock runner_on_ok event with hosts dict
**Edge Cases:** Multiple hosts in single event all get individual HostRunState entries

### TC-206: _handle_v2_runner_on_ok Status Based on Changed
**Section:** 6.2
**Category:** unit
**Priority:** high
**Description:** HostRunState status is Status.CHANGED if changed=true, Status.OK if changed=false
**Test:** Process runner_on_ok with changed=true; assert HostRunState.status=Status.CHANGED
**Fixture/Setup:** Mock runner_on_ok events with different changed values
**Edge Cases:** Missing changed field (default to false/OK)

### TC-207: _handle_v2_playbook_on_handler_task_start Marks Handler
**Section:** 6.2
**Category:** integration
**Priority:** medium
**Description:** Handler task start event processes same as task_start but flagged as handler
**Test:** Process v2_playbook_on_handler_task_start; assert task created/found
**Fixture/Setup:** Mock handler_task_start event
**Edge Cases:** Handler tasks follow same matching logic as regular tasks

### TC-208: _handle_v2_runner_on_failed Creates Failed HostRunState
**Section:** 6.2
**Category:** integration
**Priority:** critical
**Description:** v2_runner_on_failed creates HostRunState with status checking ignore_errors flag
**Test:** Process v2_runner_on_failed with hosts where ignore_errors=false; assert HostRunState.status=Status.FAILED
**Fixture/Setup:** Mock runner_on_failed events with _ansible_verbose_always.ignore_errors field
**Edge Cases:** ignore_errors flag location: result.get("_ansible_verbose_always", {}).get("ignore_errors", False)

### TC-209: _handle_v2_runner_on_failed ignore_errors Handling
**Section:** 6.2
**Category:** unit
**Priority:** critical
**Description:** When ignore_errors=true, failed task is treated as OK status
**Test:** Process runner_on_failed with ignore_errors=true; assert HostRunState.status=Status.OK
**Fixture/Setup:** Mock events with and without ignore_errors flag
**Edge Cases:** Nested ignore_errors location, missing _ansible_verbose_always dict

### TC-210: _handle_v2_runner_on_failed Triggers FAILED State
**Section:** 6.2
**Category:** integration
**Priority:** critical
**Description:** Failed task (ignore_errors=false) triggers transition from RUNNING to FAILED state
**Test:** Start with RunState.status=Status.RUNNING. Process runner_on_failed with ignore_errors=false; assert FAILED
**Fixture/Setup:** RunState in RUNNING state
**Edge Cases:** Multiple failures - state remains FAILED, first failure triggers transition

### TC-211: _handle_v2_runner_on_skipped Creates Skipped HostRunState
**Section:** 6.2
**Category:** integration
**Priority:** high
**Description:** v2_runner_on_skipped creates HostRunState with status=Status.SKIPPED
**Test:** Process v2_runner_on_skipped with hosts; assert HostRunState.status=Status.SKIPPED
**Fixture/Setup:** Mock runner_on_skipped event
**Edge Cases:** Multiple hosts skipped in single event

### TC-212: _handle_v2_runner_on_unreachable Creates Unreachable HostRunState
**Section:** 6.2
**Category:** integration
**Priority:** critical
**Description:** v2_runner_on_unreachable creates HostRunState with status=Status.UNREACHABLE and marks play
**Test:** Process v2_runner_on_unreachable with hosts; assert HostRunState.status=Status.UNREACHABLE
**Fixture/Setup:** Mock runner_on_unreachable event
**Edge Cases:** Unreachable triggers FAILED state transition regardless of ignore_errors

### TC-213: _handle_v2_runner_on_unreachable Triggers FAILED State
**Section:** 6.2
**Category:** integration
**Priority:** critical
**Description:** Unreachable host immediately triggers transition from RUNNING to FAILED state
**Test:** Start with RunState.status=Status.RUNNING. Process runner_on_unreachable; assert FAILED
**Fixture/Setup:** RunState in RUNNING state
**Edge Cases:** Unlike ignore_errors=true for failures, unreachable always triggers FAILED

### TC-214: _handle_v2_playbook_on_stats Sets End State
**Section:** 6.2
**Category:** integration
**Priority:** critical
**Description:** v2_playbook_on_stats sets RunState.end_time and final status based on failures
**Test:** Process v2_playbook_on_stats event; assert end_time set, status correct
**Fixture/Setup:** RunState with various host states
**Edge Cases:** Empty plays dict, no task states recorded

### TC-215: _handle_v2_playbook_on_stats Cross-Validation
**Section:** 6.2
**Category:** integration
**Priority:** high
**Description:** Stats event triggers cross-check: hosts in stats vs HostRunStates collected
**Test:** Process playbook with hosts in stats; cross-check against collected states
**Fixture/Setup:** RunState with partial host coverage
**Edge Cases:** Missing hosts in stats implies unreachable

### TC-216: _handle_v2_playbook_on_stats Missing Hosts Marked Unreachable
**Section:** 6.2
**Category:** integration
**Priority:** high
**Description:** Any host in HostRunState but missing from stats is marked unreachable
**Test:** Create HostRunState for host not in stats; process stats; assert marked unreachable
**Fixture/Setup:** RunState with host not appearing in final stats
**Edge Cases:** Stats contain hosts not seen in events (add to state)

### Section 6.3: Session Recording

### TC-217: Session Directory Structure Format
**Section:** 6.3
**Category:** system
**Priority:** critical
**Description:** Session directory created at ~/.local/state/aom/sessions/{uuidv7}/ with correct subfiles
**Test:** Start playbook run; assert directory created with UUIDv7 name format
**Fixture/Setup:** Mock XDG_STATE_HOME or use default path
**Edge Cases:** Directory already exists (should not occur with UUIDv7), permission denied

### TC-218: Session Directory UUIDv7 Format Validation
**Section:** 6.3
**Category:** unit
**Priority:** high
**Description:** Session directory uses UUIDv7 format (time-sortable UUID)
**Test:** Generate session UUID; assert matches UUIDv7 format pattern
**Fixture/Setup:** UUID generation code
**Edge Cases:** System clock regression may produce out-of-order UUIDs

### TC-219: Session events.jsonl Content
**Section:** 6.3
**Category:** integration
**Priority:** critical
**Description:** events.jsonl contains all JSONL events from ansible-playbook execution
**Test:** Run playbook generating N events; assert events.jsonl has N lines, each valid JSON
**Fixture/Setup:** Mock playbook run with known event count
**Edge Cases:** Large event streams (>10MB), binary data in JSON fields

### TC-220: Session stderr.log Content
**Section:** 6.3
**Category:** integration
**Priority:** high
**Description:** stderr.log contains captured stderr from ansible-playbook subprocess
**Test:** Run playbook that writes to stderr; assert stderr.log contains expected output
**Fixture/Setup:** Mock playbook with deprecation warnings (written to stderr)
**Edge Cases:** Empty stderr.log if no stderr output, UTF-8 encoding

### TC-221: Session meta.json Content
**Section:** 6.3
**Category:** integration
**Priority:** high
**Description:** meta.json contains session metadata including playbook name, version, timestamps
**Test:** Complete playbook run; read meta.json; assert contains playbook name, timestamps
**Fixture/Setup:** Completed session directory
**Edge Cases:** meta.json corrupted during crash

### TC-222: Artifact File Location After Completion
**Section:** 6.3
**Category:** system
**Priority:** critical
**Description:** After completion, session is consolidated to ~/.local/state/aom/artifacts/{uuidv7}.aom
**Test:** Complete playbook run; assert .aom file exists in artifacts directory
**Fixture/Setup:** Completed session
**Edge Cases:** Session directory remains until cleanup, artifact is permanent record

### TC-223: Artifact Format Metadata Header
**Section:** 6.3
**Category:** integration
**Priority:** high
**Description:** .aom artifact starts with metadata header line {"type": "metadata", ...}
**Test:** Read artifact file; assert first line is JSON with type="metadata"
**Fixture/Setup:** Generated .aom artifact
**Edge Cases:** Missing metadata line (malformed artifact)

### TC-224: Artifact Format Event Lines
**Section:** 6.3
**Category:** integration
**Priority:** high
**Description:** Artifact contains event lines with {"type": "event", "_event": "...", ...}
**Test:** Read artifact after metadata line; assert each line has type="event" or type="stats"
**Fixture/Setup:** Generated .aom artifact
**Edge Cases:** Order of events preserved from original JSONL stream

### TC-225: Artifact Format Stats Line
**Section:** 6.3
**Category:** integration
**Priority:** high
**Description:** Artifact ends with stats line {"type": "stats", "ok": N, "changed": M, ...}
**Test:** Read artifact last line; assert type="stats" with final statistics
**Fixture/Setup:** Generated .aom artifact
**Edge Cases:** Missing stats line (truncated artifact)

### TC-226: Session File Permissions 0o644
**Section:** 6.3
**Category:** system
**Priority:** high
**Description:** Session files created with mode 0o644 (world-readable)
**Test:** Create session directory; assert file permissions match 0o644
**Fixture/Setup:** New session file creation
**Edge Cases:** umask may affect permissions; AOM should explicitly set mode

### TC-227: Artifact File Permissions 0o600
**Section:** 6.3
**Category:** system
**Priority:** critical
**Description:** Artifact files (.aom) created with mode 0o600 (user-only) due to potentially sensitive playbook names
**Test:** Create artifact file; assert permissions match 0o600
**Fixture/Setup:** New artifact file creation
**Edge Cases:** AOM must override umask to enforce 0o600 for artifacts

### TC-228: Rotation Policy Session Count Limit
**Section:** 6.3
**Category:** system
**Priority:** medium
**Description:** Keep last 100 sessions (default, configurable) before cleanup
**Test:** Create 105 sessions; run cleanup; assert only 100 most recent remain
**Fixture/Setup:** Multiple mock session directories
**Edge Cases:** Configurable limit, session count less than limit (no deletion)

### TC-229: Rotation Policy Age Limit
**Section:** 6.3
**Category:** system
**Priority:** medium
**Description:** Delete sessions older than 30 days (default, configurable)
**Test:** Create session with old timestamp (35 days); run cleanup; assert deleted
**Fixture/Setup:** Session files with modified timestamps
**Edge Cases:** Sessions exactly at 30 days (boundary)

### TC-230: Rotation Cleanup Trigger
**Section:** 6.3
**Category:** integration
**Priority:** medium
**Description:** Cleanup runs on each AOM invocation
**Test:** Run AOM; assert cleanup code executed
**Fixture/Setup:** Mock old session files
**Edge Cases:** Cleanup errors (permission denied) should not prevent AOM run

### TC-231: Corrupted Session Truncated JSONL Handling
**Section:** 6.3
**Category:** integration
**Priority:** high
**Description:** Truncated .jsonl file is handled gracefully - malformed lines skipped with WARNING
**Test:** Create .jsonl with partial line at end; assert inspect loads valid lines, logs WARNING
**Fixture/Setup:** Artifact with truncated final line
**Edge Cases:** Mid-file corruption (single malformed line in middle)

### TC-232: Corrupted Session Malformed JSON Handling
**Section:** 6.3
**Category:** integration
**Priority:** high
**Description:** Malformed JSON lines are skipped with WARNING log
**Test:** Create .jsonl with malformed JSON line; assert parse continues, WARNING logged
**Fixture/Setup:** Artifact with malformed JSON line
**Edge Cases:** Multiple malformed lines, all valid lines must still be processed

### TC-233: Corrupted Session Inspect Output
**Section:** 6.3
**Category:** integration
**Priority:** medium
**Description:** Inspect command shows note "(N malformed lines skipped)"
**Test:** Inspect artifact with 3 malformed lines; assert output contains "(3 malformed lines skipped)"
**Fixture/Setup:** Artifact with known malformed line count
**Edge Cases:** Zero malformed lines - no note displayed

### Section 6.4: Execution State Machine

### TC-234: State Machine Eight States
**Section:** 6.4
**Category:** unit
**Priority:** critical
**Description:** RunState enum contains exactly 8 states: IDLE, STARTING, LOADING_TASKS, READY, RUNNING, COMPLETED, FAILED, CRASHED
**Test:** Assert len(RunState) == 8. Assert each enum value exists
**Fixture/Setup:** None
**Edge Cases:** No additional states; state machine is frozen

### TC-235: State Transition IDLE to STARTING
**Section:** 6.4
**Category:** integration
**Priority:** critical
**Description:** Valid transition from IDLE to STARTING on user command
**Test:** Set state to IDLE; trigger user runs aom; assert state transitions to STARTING
**Fixture/Setup:** State machine in IDLE state
**Edge Cases:** Only valid transition from IDLE is to STARTING

### TC-236: State Transition STARTING to LOADING_TASKS
**Section:** 6.4
**Category:** integration
**Priority:** critical
**Description:** Valid transition from STARTING to LOADING_TASKS when beginning discovery
**Test:** Set state to STARTING; begin --list-tasks execution; assert state transitions to LOADING_TASKS
**Fixture/Setup:** State machine in STARTING state
**Edge Cases:** LOADING_TASKS may transition to READY or CRASHED

### TC-237: State Transition LOADING_TASKS to READY
**Section:** 6.4
**Category:** integration
**Priority:** critical
**Description:** Valid transition from LOADING_TASKS to READY on successful discovery
**Test:** Set state to LOADING_TASKS; complete --list-tasks successfully; assert READY
**Fixture/Setup:** State machine in LOADING_TASKS state with successful discovery
**Edge Cases:** READY may timeout back to IDLE or transition to RUNNING

### TC-238: State Transition LOADING_TASKS to CRASHED
**Section:** 6.4
**Category:** integration
**Priority:** critical
**Description:** Valid transition from LOADING_TASKS to CRASHED on discovery failure
**Test:** Set state to LOADING_TASKS; fail --list-tasks; assert CRASHED
**Fixture/Setup:** State machine in LOADING_TASKS with failing --list-tasks
**Edge Cases:** Invalid playbook syntax, missing playbook file

### TC-239: State Transition READY to RUNNING
**Section:** 6.4
**Category:** integration
**Priority:** critical
**Description:** Valid transition from READY to RUNNING when ansible-playbook subprocess starts
**Test:** Set state to READY; start ansible-playbook; assert RUNNING
**Fixture/Setup:** State machine in READY state with subprocess start
**Edge Cases:** RUNNING may self-loop or transition to COMPLETED, FAILED, or CRASHED

### TC-240: State Transition READY Timeout to IDLE
**Section:** 6.4
**Category:** integration
**Priority:** high
**Description:** READY state times out back to IDLE after configurable period
**Test:** Set state to READY; wait for timeout; assert IDLE
**Fixture/Setup:** State machine in READY with timeout configured
**Edge Cases:** Timeout duration configurable

### TC-241: State Transition RUNNING Self-Loop
**Section:** 6.4
**Category:** unit
**Priority:** high
**Description:** RUNNING state may stay in RUNNING (processing events)
**Test:** Set state to RUNNING; process intermediate event; assert state remains RUNNING
**Fixture/Setup:** State machine in RUNNING state
**Edge Cases:** RUNNING is longest-lived state during successful execution

### TC-242: State Transition RUNNING to COMPLETED
**Section:** 6.4
**Category:** integration
**Priority:** critical
**Description:** Valid transition from RUNNING to COMPLETED on v2_playbook_on_stats with no failures
**Test:** Set state to RUNNING; receive v2_playbook_on_stats with no failures; assert COMPLETED
**Fixture/Setup:** State machine in RUNNING with successful completion
**Edge Cases:** COMPLETED may only transition to IDLE

### TC-243: State Transition RUNNING to FAILED
**Section:** 6.4
**Category:** integration
**Priority:** critical
**Description:** Valid transition from RUNNING to FAILED on runner_on_failed or runner_on_unreachable
**Test:** Set state to RUNNING; receive v2_runner_on_failed with ignore_errors=false; assert FAILED
**Fixture/Setup:** State machine in RUNNING with failure event
**Edge Cases:** FAILED may only transition to IDLE

### TC-244: State Transition RUNNING to CRASHED
**Section:** 6.4
**Category:** integration
**Priority:** critical
**Description:** Valid transition from RUNNING to CRASHED on subprocess crash or JSON parse error
**Test:** Set state to RUNNING; simulate subprocess signal/EOF; assert CRASHED
**Fixture/Setup:** State machine in RUNNING with crash condition
**Edge Cases:** CRASHED may only transition to IDLE

### TC-245: State Transition FAILED to IDLE
**Section:** 6.4
**Category:** integration
**Priority:** high
**Description:** Valid transition from FAILED to IDLE on user exit or re-run
**Test:** Set state to FAILED; user exits AOM or starts new run; assert IDLE
**Fixture/Setup:** State machine in FAILED state
**Edge Cases:** Terminal states (FAILED, COMPLETED, CRASHED) all reset to IDLE

### TC-246: State Transition CRASHED to IDLE
**Section:** 6.4
**Category:** integration
**Priority:** high
**Description:** Valid transition from CRASHED to IDLE on user exit or re-run
**Test:** Set state to CRASHED; user starts new run; assert IDLE then STARTING
**Fixture/Setup:** State machine in CRASHED state
**Edge Cases:** CRASHED state preserves crash information for debugging

### TC-247: State Transition COMPLETED to IDLE
**Section:** 6.4
**Category:** integration
**Priority:** high
**Description:** Valid transition from COMPLETED to IDLE on user exit or re-run
**Test:** Set state to COMPLETED; user exits AOM; assert IDLE
**Fixture/Setup:** State machine in COMPLETED state
**Edge Cases:** COMPLETED is terminal state for successful execution

### TC-248: Invalid Transition Rejection
**Section:** 6.4
**Category:** unit
**Priority:** critical
**Description:** Invalid state transitions are rejected (raise error or log warning)
**Test:** Set state to IDLE; attempt transition to RUNNING directly; assert rejected
**Fixture/Setup:** VALID_TRANSITIONS dict from spec
**Edge Cases:** All invalid transitions should be caught before execution

### TC-249: CRASHED Trigger Subprocess Signal
**Section:** 6.4
**Category:** integration
**Priority:** critical
**Description:** Subprocess receiving signal (SIGKILL, SIGTERM) triggers CRASHED state
**Test:** Set state to RUNNING; send SIGKILL to subprocess; assert CRASHED
**Fixture/Setup:** Running subprocess in PTY
**Edge Cases:** User Ctrl+C (SIGINT) may be handled differently

### TC-250: CRASHED Trigger Unexpected EOF
**Section:** 6.4
**Category:** integration
**Priority:** critical
**Description:** Unexpected EOF from subprocess (without stats event) triggers CRASHED state
**Test:** Set state to RUNNING; close PTY without sending v2_playbook_on_stats; assert CRASHED
**Fixture/Setup:** Running subprocess with premature termination
**Edge Cases:** Distinguish between normal EOF (after stats) and unexpected EOF

### TC-251: CRASHED Trigger JSON Parse Error
**Section:** 6.4
**Category:** integration
**Priority:** critical
**Description:** JSON parse error in event stream triggers CRASHED state
**Test:** Set state to RUNNING; send malformed JSON line to stream; assert CRASHED
**Fixture/Setup:** Running subprocess with corrupted JSON output
**Edge Cases:** Single malformed line may be logged as warning, multiple may trigger CRASHED

### TC-252: Valid Transitions Dictionary Completeness
**Section:** 6.4
**Category:** unit
**Priority:** critical
**Description:** VALID_TRANSITIONS dict contains all 8 states with correct allowed transitions
**Test:** Assert VALID_TRANSITIONS has keys for all 8 states; assert each set matches spec diagram
**Fixture/Setup:** VALID_TRANSITIONS constant from spec
**Edge Cases:** RUNNING has self-loop included in transitions set

### Section 6.5: Memory Bounds

### TC-253: Memory Bound Max Plays 1000
**Section:** 6.5
**Category:** unit
**Priority:** high
**Description:** Maximum 1000 plays tracked; exceeding logs WARNING but continues execution
**Test:** Create 1001 plays; assert WARNING logged, Play 1001+ not added to state but execution continues
**Fixture/Setup:** Mock playbook with 1001 plays
**Edge Cases:** Exact boundary: 1000 plays OK, 1001 triggers warning

### TC-254: Memory Bound Max Tasks Per Play 10000
**Section:** 6.5
**Category:** unit
**Priority:** high
**Description:** Maximum 10000 tasks per play tracked; exceeding logs WARNING
**Test:** Create playbook with 10001 tasks in single play; assert WARNING logged
**Fixture/Setup:** Mock play with excessive tasks
**Edge Cases:** Count includes dynamic tasks from include_tasks expansion

### TC-255: Memory Bound Max Hosts Per Task 10000
**Section:** 6.5
**Category:** unit
**Priority:** high
**Description:** Maximum 10000 hosts per task tracked; exceeding logs WARNING
**Test:** Process task with results from 10001 hosts; assert WARNING logged
**Fixture/Setup:** Mock runner_on_ok with 10001 hosts
**Edge Cases:** Large inventory with many hosts, but practical limit enforced

### TC-256: Memory Bound Max Total HostRunState 1M
**Section:** 6.5
**Category:** unit
**Priority:** critical
**Description:** Maximum 1,000,000 total HostRunState entries across all tasks; exceeding stops individual tracking
**Test:** Create state with 1M entries; process additional host; assert WARNING logged, tracking stops
**Fixture/Setup:** Large playbook mock data
**Edge Cases:** Memory safeguard prevents unbounded growth

### TC-257: Memory Bound Exceeded Warning Message
**Section:** 6.5
**Category:** unit
**Priority:** medium
**Description:** When memory bound exceeded, WARNING logged with explanation but playbook continues
**Test:** Exceed any memory bound; assert WARNING message logged with specific bound exceeded
**Fixture/Setup:** Mock exceeding each bound type
**Edge Cases:** Multiple bound warnings may occur during same run

### TC-258: Memory Bound Exceeded Continues Execution
**Section:** 6.5
**Category:** integration
**Priority:** high
**Description:** Memory bounds are soft limits - execution continues with degraded tracking
**Test:** Exceed 1000 plays limit; assert remaining plays execute but not tracked in state tree
**Fixture/Setup:** Mock large playbook exceeding bounds
**Edge Cases:** Degraded tracking means final stats cross-check incomplete

### TC-259: Memory Bound Log Panel Max Lines 50000
**Section:** 6.5
**Category:** unit
**Priority:** medium
**Description:** Log panel has max_lines=50000 for memory bounds (configurable)
**Test:** Generate 60000 log lines; assert older lines truncated, 50000 most recent retained
**Fixture/Setup:** Log panel widget with config
**Edge Cases:** Very long playbook output causing memory pressure

### TC-260: Memory Bound Configurable Limits
**Section:** 6.5
**Category:** unit
**Priority:** low
**Description:** Memory bounds are configurable via config file
**Test:** Set config memory.max_plays=500; assert limit updated from default 1000 to 500
**Fixture/Setup:** Config file with custom limits
**Edge Cases:** Very low limits may break functionality (min threshold enforcement)

### TC-261: Task Matching Strategy Primary UUID
**Section:** 6.1
**Category:** integration
**Priority:** critical
**Description:** JSONL events matched to TaskDefinition primarily by UUID (task.id field)
**Test:** Create TaskDefinition with uuid="abc123". Process JSONL event with task.id="abc123"; assert matched
**Fixture/Setup:** TaskDefinition and JSONL event with matching UUID
**Edge Cases:** UUID mismatch falls back to path matching

### TC-262: Task Matching Strategy Secondary Path
**Section:** 6.1
**Category:** integration
**Priority:** high
**Description:** If UUID unavailable or mismatched, match by task.path (file:line format)
**Test:** Create TaskDefinition with path="site.yml:42" and no UUID. Process event with matching path; assert matched
**Fixture/Setup:** TaskDefinition and event with matching path
**Edge Cases:** Path format parsing (file:line), path may be relative

### TC-263: Task Matching Strategy Fallback Sequential Plus Name
**Section:** 6.1
**Category:** integration
**Priority:** high
**Description:** Fallback matching uses play_order, task_order, and normalized task name
**Test:** Create TaskDefinition at play_order=1, task_order=5, name="Install nginx". Process event for same position; assert matched
**Fixture/Setup:** TaskDefinition with position data and event without UUID/path
**Edge Cases:** Name normalization (strip role prefix, whitespace), ambiguous matches

---

## Section 7: TUI Components

### TC-264: Tree View Hierarchy Structure
**Section:** 7.1
**Category:** unit
**Priority:** critical
**Description:** Verify tree view displays correct hierarchy: Root → Play → RoleGroup (optional) → Task → Host
**Test:** Assert tree structure contains Play nodes at root level, RoleGroup nodes when 5+ consecutive same-role tasks exist, Task nodes under RoleGroup or Play, and Host nodes under Task
**Fixture/Setup:** Mock RunState with plays containing role-grouped tasks and standalone tasks
**Edge Cases:** Empty playbook, single task no role, tasks with mixed roles (not grouped)

### TC-265: Tree View Navigation Up/Down
**Section:** 7.1
**Category:** integration
**Priority:** high
**Description:** Verify ↑/↓ keys navigate selection up and down through tree nodes
**Test:** Press ↑ from node N, assert selection moves to N-1 (or stays at first). Press ↓, assert selection moves to N+1 (or stays at last)
**Fixture/Setup:** AOMApp with populated tree, pilot.keypress("up"), pilot.keypress("down")
**Edge Cases:** Navigation at first node (↑ does nothing), at last node (↓ does nothing)

### TC-266: Tree View Expand/Collapse Arrow Keys
**Section:** 7.1
**Category:** integration
**Priority:** high
**Description:** Verify → expands collapsed node, ← collapses expanded node
**Test:** On collapsed Play node, press →, assert children now visible. On expanded node, press ←, assert children hidden
**Fixture/Setup:** AOMApp with Play containing tasks
**Edge Cases:** Leaf nodes (Host) where expand/collapse has no effect

### TC-267: Tree View Enter Toggle
**Section:** 7.1
**Category:** integration
**Priority:** high
**Description:** Verify Enter key toggles expand/collapse state of selected node
**Test:** On collapsed node, press Enter, assert expanded. Press Enter again, assert collapsed
**Fixture/Setup:** AOMApp with collapsible tree nodes
**Edge Cases:** Leaf nodes (Host) where Enter is no-op

### TC-268: Tree View Uses Textual Tree Widget
**Section:** 7.1
**Category:** unit
**Priority:** medium
**Description:** Verify Tree view implementation uses Textual's built-in Tree widget
**Test:** Assert tree_widget is instance of Tree. Assert custom TreeNode classes exist for Play, RoleGroup, Task, Host types
**Fixture/Setup:** Inspect AOMApp widget tree
**Edge Cases:** None

### TC-269: Tree View Reactive Updates
**Section:** 7.1
**Category:** integration
**Priority:** high
**Description:** Verify tree updates reactively when RunState changes (new tasks, status updates)
**Test:** Update RunState with new task event, assert tree reflects new node. Update task status to FAILED, assert icon/color changes
**Fixture/Setup:** AOMApp with watch method on state property
**Edge Cases:** Rapid consecutive updates, updates during tree collapse

### TC-270: Tree View Task Name Truncation
**Section:** 7.1
**Category:** unit
**Priority:** high
**Description:** Verify long task names are truncated with … (U+2026) when exceeding available width
**Test:** Given task name longer than available width, assert displayed name ends with … and starts with first N characters. Assert minimum 10 visible characters before …
**Fixture/Setup:** Tree widget with various task name lengths, verify truncation function
**Edge Cases:** Name exactly at width boundary, name shorter than 10 chars, empty name

### TC-271: Tree View Role Name Priority in Truncation
**Section:** 7.1
**Category:** unit
**Priority:** medium
**Description:** When truncating, prioritize showing role name over task name if both are long
**Test:** Given role name "very-long-role-name" and task name "also-very-long-task", verify role name is preserved in truncation over task name
**Fixture/Setup:** RoleGroupDefinition with long names in both role and task
**Edge Cases:** Role name alone exceeds width

### TC-272: Compact Mode Hard-Truncate at Width-20
**Section:** 7.1
**Category:** unit
**Priority:** medium
**Description:** Verify compact mode status panel hard-truncates task names at terminal width minus 20 chars (for status icons)
**Test:** Given terminal width W, assert task name display length ≤ W-20. Assert truncation uses … suffix
**Fixture/Setup:** CompactRenderer with mocked terminal width
**Edge Cases:** Terminal width < 30 chars (minimal viable width)

### TC-273: RoleGroup Creation Threshold
**Section:** 7.1
**Category:** unit
**Priority:** high
**Description:** Verify RoleGroup is created when 5 or more consecutive tasks belong to same role
**Test:** Given 4 consecutive tasks with role "nginx", assert no RoleGroup created. Given 5+ consecutive tasks with role "nginx", assert RoleGroup created containing those tasks
**Fixture/Setup:** PlayDefinition with task sequences of varying role repetition
**Edge Cases:** Exactly 5 tasks, tasks with no role mixed in breaking the sequence

### TC-274: Log Panel Max Lines Bound
**Section:** 7.2
**Category:** unit
**Priority:** critical
**Description:** Verify RichLog widget enforces max_lines=50000 (or configurable value)
**Test:** Write 60000 lines to RichLog, assert only last 50000 retained. Assert line count ≤ max_lines after overflow
**Fixture/Setup:** RichLog widget with max_lines=50000
**Edge Cases:** Exactly max_lines, max_lines-1, max_lines+1

### TC-275: Log Panel Auto-Scroll Behavior
**Section:** 7.2
**Category:** integration
**Priority:** high
**Description:** Verify auto-scroll pauses when user manually scrolls up, resumes when scrolled to bottom
**Test:** When at scroll end, new lines auto-scroll. When scrolled up, new lines do not move view. Return to bottom resumes auto-scroll
**Fixture/Setup:** LogPanel with scroll tracking
**Edge Cases:** Scrolling during rapid line addition

### TC-276: Log Panel JSON Line Detection
**Section:** 7.2
**Category:** unit
**Priority:** high
**Description:** Verify JSON lines (starting with '{') are parsed differently from raw text
**Test:** Feed line '{"_event": "v2_runner_on_ok"}' to append_line. assert JSON parsing attempted. Feed plain line "TASK [test]". assert treated as text
**Fixture/Setup:** LogPanel.append_line method with JSON detection logic
**Edge Cases:** Malformed JSON (should fall back to text), JSON within text

### TC-277: Log Panel ANSI Color Handling
**Section:** 7.2
**Category:** unit
**Priority:** medium
**Description:** Verify ANSI escape codes in log lines are preserved/converted correctly
**Test:** Feed line with ANSI codes "\033[31mERROR\033[0m", assert Rich Text.from_ansi() is called and colors visible
**Fixture/Setup:** Text.from_ansi() handling
**Edge Cases:** Invalid ANSI sequences, complex ANSI (multiple attributes)

### TC-278: Log Panel Search Overlay Activation
**Section:** 7.2
**Category:** integration
**Priority:** high
**Description:** Verify Ctrl+F opens search overlay at top of log panel
**Test:** Focus log panel. Press Ctrl+F. Assert search input widget visible. Assert overlay is focused
**Fixture/Setup:** AOMApp with LogPanel focused, pilot.keypress("ctrl+f")
**Edge Cases:** Search when log is empty

### TC-279: Log Panel Search Plain Text Mode
**Section:** 7.2
**Category:** integration
**Priority:** high
**Description:** Verify plain text search finds and highlights matching lines
**Test:** Open search. Type "INSTALL". Assert all lines containing "INSTALL" highlighted. Case-insensitive by default
**Fixture/Setup:** LogPanel with sample lines containing search term
**Edge Cases:** No matches, special regex characters in plain text mode

### TC-280: Log Panel Search Regex Mode
**Section:** 7.2
**Category:** integration
**Priority:** medium
**Description:** Verify regex search mode matches patterns
**Test:** Enable regex mode. Search for "TASK \[.*\]". Assert matches all TASK headers. Validate regex compile errors are handled gracefully
**Fixture/Setup:** LogPanel with search bar supporting regex toggle
**Edge Cases:** Invalid regex patterns

### TC-281: Log Panel Search Case-Sensitive Toggle
**Section:** 7.2
**Category:** integration
**Priority:** medium
**Description:** Verify case-sensitive toggle affects search matching
**Test:** Search for "error" with case-insensitive (default), assert "ERROR" matches. Toggle case-sensitive, assert "ERROR" does not match "error" query
**Fixture/Setup:** LogPanel with case-sensitive toggle in search bar
**Edge Cases:** Unicode case sensitivity

### TC-282: Log Panel Search F3 Navigation
**Section:** 7.2
**Category:** integration
**Priority:** high
**Description:** Verify F3 jumps to next match, Shift+F3 jumps to previous match
**Test:** After search with multiple matches, press F3, assert scroll moves to next match. Press Shift+F3, assert scroll moves to previous match
**Fixture/Setup:** LogPanel with search active and multiple matches
**Edge Cases:** At last match (F3 wraps or stops), at first match (Shift+F3 wraps or stops)

### TC-283: Log Panel Search Match Highlighting
**Section:** 7.2
**Category:** unit
**Priority:** medium
**Description:** Verify search matches are visually highlighted (background color or underline)
**Test:** After search, assert matched text has distinct style from non-matched text
**Fixture/Setup:** LogPanel with Rich Text highlighting
**Edge Cases:** Overlapping highlights (should not occur in simple search)

### TC-284: Log Panel Smart Auto-Scroll Pause
**Section:** 7.2
**Category:** integration
**Priority:** high
**Description:** Verify is_vertical_scroll_end() correctly detects bottom position
**Test:** Add lines while at bottom, assert auto-scroll continues. Scroll up 5 lines, add lines, assert view unchanged. Scroll to bottom, add line, assert auto-scroll resumes
**Fixture/Setup:** LogPanel tracking scroll position
**Edge Cases:** Terminal resize affecting scroll position

### TC-285: Summary Panel Current Play Display
**Section:** 7.3
**Category:** unit
**Priority:** high
**Description:** Verify summary panel shows current play name
**Test:** Given RunState with active play "Configure Webservers", assert summary displays "Play: Configure Webservers"
**Fixture/Setup:** SummaryPanel with mock RunState
**Edge Cases:** No active play (pre-execution), multiple plays completed

### TC-286: Summary Panel Hosts Progress
**Section:** 7.3
**Category:** unit
**Priority:** high
**Description:** Verify hosts completed/total display (e.g., "Hosts: 2/5 complete")
**Test:** Given RunState with 2 hosts complete out of 5 total, assert "Hosts: 2/5 complete" displayed
**Fixture/Setup:** SummaryPanel with host progress calculation
**Edge Cases:** Zero hosts, all hosts complete, unreachable hosts

### TC-287: Summary Panel Tasks Progress
**Section:** 7.3
**Category:** unit
**Priority:** high
**Description:** Verify tasks completed/total display (e.g., "Tasks: 23/45 complete")
**Test:** Given RunState with 23 tasks complete out of 45 total, assert "Tasks: 23/45 complete"
**Fixture/Setup:** SummaryPanel with task counting from RunState
**Edge Cases:** Zero tasks, dynamic tasks added during run

### TC-288: Summary Panel Elapsed Time Format
**Section:** 7.3
**Category:** unit
**Priority:** medium
**Description:** Verify elapsed time displays in HH:MM:SS format
**Test:** Given 3723 seconds elapsed, assert "1:02:03" displayed. Given 45 seconds, assert "0:00:45"
**Fixture/Setup:** SummaryPanel with start_time set
**Edge Cases:** Zero elapsed, > 99 hours

### TC-289: Summary Panel Per-Host Status Breakdown
**Section:** 7.3
**Category:** unit
**Priority:** high
**Description:** Verify per-host status line shows counts with icons (e.g., "web1: ● 12 ok, ◆ 3 changed, ✖ 0 failed")
**Test:** Given host "web1" with 12 ok, 3 changed, 0 failed, assert summary line matches expected format with correct icons
**Fixture/Setup:** SummaryPanel with HostRunState data
**Edge Cases:** Host with all tasks pending, host with unreachable status

### TC-290: Status Bar Element Configuration
**Section:** 7.4
**Category:** unit
**Priority:** medium
**Description:** Verify status bar displays configured elements from config.yaml
**Test:** Given config with playbook_name, elapsed_time, task_progress, assert status bar shows exactly those elements in order
**Fixture/Setup:** StatusBar with StatusBarConfig from YAML
**Edge Cases:** Empty elements list (use defaults), invalid element name (should be ignored)

### TC-291: Status Bar Available Elements
**Section:** 7.4
**Category:** unit
**Priority:** medium
**Description:** Verify all available elements display correctly: playbook_name, current_play, elapsed_time, task_progress, current_task, host_count, per-host progress, subprocess_pid, memory_usage, activity_ticker
**Test:** For each element type, assert it renders with correct data from RunState or system
**Fixture/Setup:** StatusBar with each element enabled individually
**Edge Cases:** PID not available, memory usage unavailable (fallback to N/A)

### TC-292: Status Bar YAML Configuration Schema
**Section:** 7.4
**Category:** integration
**Priority:** high
**Description:** Verify YAML config correctly configures status bar elements
**Test:** Parse config.yaml with status_bar.elements list. Assert StatusBarConfig.elements matches parsed values
**Fixture/Setup:** AppConfig with status_bar key from YAML
**Edge Cases:** Malformed YAML, empty elements list (use defaults)

### TC-293: Debug Panel Toggle Key
**Section:** 7.5
**Category:** integration
**Priority:** high
**Description:** Verify D key toggles debug panel visibility
**Test:** Press D when debug panel hidden, assert panel visible. Press D again, assert panel hidden
**Fixture/Setup:** AOMApp with debug panel toggle handler
**Edge Cases:** Toggle during rapid state changes

### TC-294: Debug Panel Data Display
**Section:** 7.5
**Category:** unit
**Priority:** medium
**Description:** Verify debug panel shows all required data: command/env overrides, event count, parsing errors, callback status, timing stats, subprocess PID, state tree snapshot, pending events queue, memory usage, renderer FPS, event processing latency
**Test:** Assert each data field is present and displays expected format. Verify live updates on state changes
**Fixture/Setup:** DebugPanel with mock AppState containing all debug data
**Edge Cases:** Zero events processed, no parsing errors, no pending events

### TC-295: Debug Panel Command and Env Display
**Section:** 7.5
**Category:** unit
**Priority:** low
**Description:** Verify command line and environment overrides are displayed
**Test:** Given subprocess command "ansible-playbook site.yml -i hosts", assert command displayed. Given ANSIBLE_* env vars, assert they are listed
**Fixture/Setup:** DebugPanel with runner state
**Edge Cases:** No env overrides (display empty/default)

### TC-296: Debug Panel Event Count
**Section:** 7.5
**Category:** unit
**Priority:** low
**Description:** Verify event count updates as JSONL events are processed
**Test:** Process N events, assert displayed count equals N
**Fixture/Setup:** DebugPanel tracking event_count
**Edge Cases:** Zero events (display "0")

### TC-297: Debug Panel Parsing Errors
**Section:** 7.5
**Category:** unit
**Priority:** medium
**Description:** Verify parsing errors (malformed JSON) are listed with count and sample
**Test:** Inject 3 malformed JSON lines, assert error count shows 3. If expanded, assert sample lines shown
**Fixture/Setup:** DebugPanel with PtyStreamParser error tracking
**Edge Cases:** No errors (hide or show "0 errors")

### TC-298: Debug Panel Memory Usage RSS/VSZ
**Section:** 7.5
**Category:** unit
**Priority:** low
**Description:** Verify memory usage displays RSS and VSZ values
**Test:** Assert memory_display shows "RSS: Xm VSZ: Ym" format. Verify values are plausible (>0 for running process)
**Fixture/Setup:** DebugPanel with psutil RSS/VSZ read
**Edge Cases:** psutil unavailable (skip or show N/A)

### TC-299: Debug Panel Subprocess PID
**Section:** 7.5
**Category:** unit
**Priority:** low
**Description:** Verify subprocess PID is displayed when ansible-playbook is running
**Test:** Given running subprocess with PID 12345, assert "PID: 12345" displayed. After completion, assert PID hidden or shows "(completed)"
**Fixture/Setup:** DebugPanel with runner subprocess reference
**Edge Cases:** No subprocess (pre-start or post-completion)

### TC-300: Filter Panel Activation Key
**Section:** 7.6
**Category:** integration
**Priority:** high
**Description:** Verify 'f' key opens filter panel
**Test:** Press 'f' from any panel, assert filter panel overlay appears. Assert filter panel is focused
**Fixture/Setup:** AOMApp with filter panel mountable on key press
**Edge Cases:** Filter panel already open (toggle close)

### TC-301: Filter Panel Status Checkboxes
**Section:** 7.6
**Category:** integration
**Priority:** high
**Description:** Verify status checkboxes filter tasks by status: OK, Changed, Failed, Skipped, Unreachable, Running, Pending
**Test:** Check only "Failed" checkbox, assert only failed tasks visible in tree. Check multiple statuses, assert union shown. Uncheck all, assert all tasks shown
**Fixture/Setup:** FilterPanel with status checkboxes affecting tree view
**Edge Cases:** No tasks match filter (empty tree)

### TC-302: Filter Panel Text Filter
**Section:** 7.6
**Category:** integration
**Priority:** high
**Description:** Verify text filter filters tasks by name substring match
**Test:** Enter "nginx" in text filter, assert only tasks with "nginx" in name shown. Clear filter, assert all tasks shown
**Fixture/Setup:** FilterPanel with text input field connected to tree filtering
**Edge Cases:** Case sensitivity, regex in input (if supported)

### TC-303: Filter Panel Host Filter
**Section:** 7.6
**Category:** integration
**Priority:** high
**Description:** Verify host filter shows only tasks that ran (or will run) on specified host
**Test:** Enter "web1" in host filter, assert only tasks with web1 in host list shown. Enter multiple hosts, assert tasks matching any host shown
**Fixture/Setup:** FilterPanel with host input connected to host-based filtering
**Edge Cases:** Host not in inventory, empty host input (no filter)

---

## Section 8: Configuration

### TC-304: Config File XDG Path
**Section:** 8.1
**Category:** unit
**Priority:** critical
**Description:** Verify config file path follows XDG spec: ~/.config/aom/config.yaml
**Test:** Assert default config path equals expanded ~/.config/aom/config.yaml. Verify platformdirs is used correctly
**Fixture/Setup:** AppConfig with default path resolution
**Edge Cases:** XDG_CONFIG_HOME environment variable override

### TC-305: Config File First Run Creation
**Section:** 8.1
**Category:** integration
**Priority:** high
**Description:** Verify first run creates config.yaml with all settings commented out
**Test:** When config file does not exist, assert file created. Assert file content has all settings commented with # prefix. Assert settings are documented with defaults
**Fixture/Setup:** Fresh environment with no config
**Edge Cases:** Write permissions, directory creation (~/.config/aom/)

### TC-306: Config File First Run User Override
**Section:** 8.1
**Category:** integration
**Priority:** medium
**Description:** Verify user can uncomment settings in created config to override defaults
**Test:** First run creates commented config. User uncomments "log_max_lines: 100000". Assert new value 100000 used on next run
**Fixture/Setup:** Config file with commented defaults
**Edge Cases:** Invalid YAML after uncommenting (validation error)

### TC-307: Config Schema StatusBar Elements
**Section:** 8.1
**Category:** unit
**Priority:** medium
**Description:** Verify status_bar.elements config is valid list of element names
**Test:** Parse status_bar.elements: ["playbook_name", "elapsed_time"]. Assert StatusBarConfig validates element names against allowed set
**Fixture/Setup:** StatusBarConfig Pydantic model
**Edge Cases:** Empty list (use defaults), invalid element name (validation warning or ignore)

### TC-308: Config Schema Panels Dimensions
**Section:** 8.1
**Category:** unit
**Priority:** medium
**Description:** Verify panels.tree_width and panels.summary_height are percentages (0-100)
**Test:** Parse panels.tree_width: 40. Assert value is integer 0-100. Parse panels.summary_height: 30. Assert valid
**Fixture/Setup:** PanelsConfig Pydantic model
**Edge Cases:** Values outside 0-100 (validation error)

### TC-309: Config Schema Keybindings Override
**Section:** 8.1
**Category:** integration
**Priority:** medium
**Description:** Verify custom keybindings in config override defaults
**Test:** Parse keybindings.quit: "x". Assert app uses 'x' instead of 'q' for quit. Verify all bindable actions can be customized
**Fixture/Setup:** AppConfig with keybindings dict
**Edge Cases:** Invalid key combination, conflicting bindings

### TC-310: Config Schema Log Settings
**Section:** 8.1
**Category:** unit
**Priority:** medium
**Description:** Verify log.max_lines and log.auto_scroll configuration
**Test:** Parse log.max_lines: 75000. Assert RichLog initialized with 75000 max_lines. Parse log.auto_scroll: false. Assert auto-scroll disabled
**Fixture/Setup:** LogConfig Pydantic model, LogPanel initialization
**Edge Cases:** max_lines below minimum (validation error)

### TC-311: Config Schema Session Storage
**Section:** 8.1
**Category:** unit
**Priority:** high
**Description:** Verify session.storage_dir, session.keep_sessions, session.keep_days configuration
**Test:** Parse session.storage_dir: "/custom/path". Assert sessions stored in custom path. Parse keep_sessions: 50, keep_days: 7. Assert rotation policy uses 50 sessions or 7 days
**Fixture/Setup:** SessionConfig Pydantic model, SessionManager initialization
**Edge Cases:** Storage dir doesn't exist (create it), invalid path (permission error)

### TC-312: Config Schema Redaction Whitelist
**Section:** 8.1
**Category:** unit
**Priority:** high
**Description:** Verify redaction.whitelist excludes fields from redaction
**Test:** Given whitelist: ["passenger_version", "bypass"], assert these field names are NOT redacted even if matching password pattern
**Fixture/Setup:** RedactionConfig with custom whitelist
**Edge Cases:** Empty whitelist (all matched fields redacted)

### TC-313: Config Schema Redaction Custom Fields
**Section:** 8.1
**Category:** unit
**Priority:** medium
**Description:** Verify redaction.custom_fields adds additional field names to redaction list
**Test:** Given custom_fields: ["my_secret_var", "db_connection_string"], assert these fields are redacted in addition to built-in list
**Fixture/Setup:** RedactionConfig with custom_fields
**Edge Cases:** Field already in built-in list (deduplicated)

### TC-314: Config Schema Redaction Custom Patterns
**Section:** 8.1
**Category:** unit
**Priority:** medium
**Description:** Verify redaction.custom_patterns adds regex patterns for string redaction
**Test:** Given custom_patterns: [{regex: "--db-password=\\S+", replacement: "--db-password=********"}], assert matching strings are redacted with custom replacement
**Fixture/Setup:** RedactionConfig with custom_patterns, sanitize_string function
**Edge Cases:** Invalid regex pattern (validation error), pattern doesn't compile

### TC-315: Config Schema Ansible Default Args
**Section:** 8.1
**Category:** unit
**Priority:** low
**Description:** Verify ansible.default_args adds arguments to every ansible-playbook invocation
**Test:** Given default_args: ["-v", "--diff"], assert these args are appended to every playbook run command
**Fixture/Setup:** AppConfig with ansible.default_args
**Edge Cases:** Empty list (no extra args)

### TC-316: Config Validation Pydantic BaseModel
**Section:** 8.2
**Category:** unit
**Priority:** critical
**Description:** Verify configuration is validated via Pydantic BaseModel
**Test:** Create AppConfig with invalid value (e.g., negative log_max_lines). Assert Pydantic ValidationError raised with field-specific error
**Fixture/Setup:** AppConfig Pydantic model
**Edge Cases:** All model fields tested for validation

### TC-317: Config Validation Pydantic Settings
**Section:** 8.2
**Category:** integration
**Priority:** high
**Description:** Verify Pydantic Settings loads from YAML file automatically
**Test:** Create config.yaml with status_bar.elements. Load AppConfig via BaseSettings. Assert values match YAML
**Fixture/Setup:** AppConfig inheriting from BaseSettings with SettingsConfigDict
**Edge Cases:** Missing YAML file (use defaults), extra fields in YAML (ignore or warn)

### TC-318: Config Validation Field Constraints ge/le
**Section:** 8.2
**Category:** unit
**Priority:** high
**Description:** Verify Field constraints ge and le enforce bounds on numeric config values
**Test:** Assert log_max_lines has ge=1000, le=100000. Assert session_keep_count has ge=1. Assert session_keep_days has ge=1. Verify ValidationError for values outside bounds
**Fixture/Setup:** AppConfig Field definitions with validators
**Edge Cases:** Boundary values (exactly 1000 and 100000 should pass)

---

## Section 9: Session Inspection

### TC-319: Session Inspect List Command
**Section:** 9.1
**Category:** integration
**Priority:** critical
**Description:** Verify 'aom inspect list' displays table of sessions with ID, playbook, date, status, duration
**Test:** Run 'aom inspect list' with multiple sessions. Assert output is Rich table. Assert columns: Session ID (8 chars), Playbook, Date, Status, Duration
**Fixture/Setup:** Multiple session artifacts in storage directory
**Edge Cases:** Empty sessions (display "No sessions found"), single session

### TC-320: Session UUID Display 8 Chars in List
**Section:** 9.1
**Category:** unit
**Priority:** medium
**Description:** Verify session UUIDs are displayed as first 8 characters in 'aom inspect list'
**Test:** Given session UUID "01923abc-def45678-90abcdef-12345678", assert list shows "01923abc..." with ellipsis or just "01923abc"
**Fixture/Setup:** Session listing function truncating UUID
**Edge Cases:** UUID shorter than 8 chars (malformed)

### TC-321: Session Inspect Show Summary
**Section:** 9.1
**Category:** integration
**Priority:** high
**Description:** Verify 'aom inspect <session-id>' shows full summary with play/task breakdown
**Test:** Run 'aom inspect <uuid>'. Assert output shows full session UUID, playbook name, start/end time, status. Assert plays and tasks are listed with status icons
**Fixture/Setup:** Session artifact with known content
**Edge Cases:** Session UUID not found (error message)

### TC-322: Session Inspect Filter Failed
**Section:** 9.1
**Category:** integration
**Priority:** high
**Description:** Verify 'aom inspect <session-id> --failed' shows only failed tasks
**Test:** Run '--failed' flag on session with mixed results. Assert output contains only tasks with status FAILED. No OK/CHANGED tasks shown
**Fixture/Setup:** Session artifact with failed and ok tasks
**Edge Cases:** No failed tasks (display "No failed tasks")

### TC-323: Session Inspect Filter Host
**Section:** 9.1
**Category:** integration
**Priority:** high
**Description:** Verify 'aom inspect <session-id> --host <name>' shows only tasks for that host
**Test:** Run '--host web1' on session. Assert output contains only tasks that executed on web1. Tasks running on web2, db1 should not appear
**Fixture/Setup:** Session artifact with multi-host execution
**Edge Cases:** Host not in session (display "No tasks for host 'unknown'")

### TC-324: Session Inspect Tree View
**Section:** 9.1
**Category:** integration
**Priority:** high
**Description:** Verify 'aom inspect <session-id> --tree' shows ASCII tree of plays/tasks with status icons
**Test:** Run '--tree' flag. Assert output shows hierarchical tree structure: Play > Task > Host. Assert status icons (●, ◆, ✖, etc.) displayed
**Fixture/Setup:** Session artifact with play/task hierarchy
**Edge Cases:** Deeply nested roles (ensure tree renders correctly)

### TC-325: Session Diff Command
**Section:** 9.3
**Category:** integration
**Priority:** high
**Description:** Verify 'aom inspect diff <id1> <id2>' compares task outcomes between runs
**Test:** Run diff between two sessions. Assert output is table with Task, Baseline, Current, Classification columns. Assert classifications: regressed, improved, changed, new, removed, unchanged
**Fixture/Setup:** Two session artifacts with different task outcomes
**Edge Cases:** Identical sessions (all unchanged), completely different playbooks

### TC-326: Session Diff Task Matching UUID Priority
**Section:** 9.3
**Category:** unit
**Priority:** critical
**Description:** Verify diff uses task.uuid as primary matching method
**Test:** Given two sessions with matching task UUIDs, assert tasks matched by UUID even if names differ
**Fixture/Setup:** Session diff logic with match_tasks function
**Edge Cases:** UUID collision (use path fallback)

### TC-327: Session Diff Task Matching Path Fallback
**Section:** 9.3
**Category:** unit
**Priority:** high
**Description:** Verify diff uses task.path (file:line) as secondary matching when UUIDs unavailable
**Test:** Given tasks without UUIDs but with matching paths, assert tasks matched by path
**Fixture/Setup:** Tasks without UUID field, with path field
**Edge Cases:** Path differs between runs (use name fallback)

### TC-328: Session Diff Task Matching Name Fallback
**Section:** 9.3
**Category:** unit
**Priority:** medium
**Description:** Verify diff uses task name as last resort matching when UUID and path unavailable
**Test:** Given tasks without UUID or path, with matching names, assert tasks matched by name
**Fixture/Setup:** Tasks with only name field
**Edge Cases:** Duplicate task names (ambiguous matching)

### TC-329: Session Diff Cross-Playbook Warning
**Section:** 9.3
**Category:** integration
**Priority:** medium
**Description:** Verify cross-playbook diff shows warning banner when playbook names differ
**Test:** Diff session1 (site.yml) with session2 (deploy.yml). Assert warning banner displayed at top of output indicating different playbooks
**Fixture/Setup:** Two session artifacts from different playbooks
**Edge Cases:** Same playbook filename different content (no warning)

### TC-330: Session Diff Changes Only Flag
**Section:** 9.3
**Category:** integration
**Priority:** high
**Description:** Verify '--changes-only' flag filters to show only tasks with status changes
**Test:** Run diff with '--changes-only'. Assert unchanged tasks are hidden. Assert only regressed, improved, changed, new, removed shown
**Fixture/Setup:** Diff output with various statuses
**Edge Cases:** All unchanged (show "No changes" message)

### TC-331: Session Diff Default Shows All Tasks
**Section:** 9.3
**Category:** integration
**Priority:** medium
**Description:** Verify default diff (without --changes-only) shows ALL tasks including unchanged
**Test:** Run diff without flags. Assert unchanged tasks are displayed in table with "(no highlight)" classification
**Fixture/Setup:** Diff output generation
**Edge Cases:** Large playbook (consider pagination or limit)

### TC-332: Session Diff Classification Colors
**Section:** 9.3
**Category:** unit
**Priority:** low
**Description:** Verify diff classification categories have correct colors: regressed=Red, improved=Green, changed=Yellow, new=Cyan, removed=Dim, unchanged=no highlight
**Test:** Assert color mapping in diff output matches specification
**Fixture/Setup:** Diff output table with Rich styling
**Edge Cases:** Non-TTY output (plain text without colors)

### TC-333: Session Diff Duration Exclusion
**Section:** 9.3
**Category:** unit
**Priority:** medium
**Description:** Verify diff does NOT compare task durations, only status changes
**Test:** Run diff between sessions with different task durations but same statuses. Assert no duration column or duration delta in output
**Fixture/Setup:** Diff table definition
**Edge Cases:** N/A

### TC-334: Session Prune Command
**Section:** 9.3
**Category:** integration
**Priority:** high
**Description:** Verify 'aom inspect prune --days 30' deletes sessions older than 30 days
**Test:** Create sessions older than 30 days. Run prune --days 30. Assert old sessions deleted, recent sessions retained
**Fixture/Setup:** Storage directory with aged session artifacts
**Edge Cases:** --days 0 (delete all), --days 365 (keep all recent)

### TC-335: Session Output Format JSON
**Section:** 9.4
**Category:** integration
**Priority:** medium
**Description:** Verify '--json' flag outputs structured JSON
**Test:** Run 'aom inspect list --json'. Assert output is valid JSON array. Run 'aom inspect <id> --json'. Assert output is valid JSON object with all expected fields
**Fixture/Setup:** Session commands with --json flag
**Edge Cases:** JSON encoding of special characters in task names

### TC-336: Session Output Format JSONL
**Section:** 9.4
**Category:** integration
**Priority:** medium
**Description:** Verify '--jsonl' flag outputs raw event dump (one JSON per line)
**Test:** Run 'aom inspect <id> --jsonl'. Assert each line is valid JSON. Assert lines correspond to stored events
**Fixture/Setup:** Session commands with --jsonl flag
**Edge Cases:** Malformed events in session (skip or include with warning)

### TC-337: Session Full UUID in Inspect
**Section:** 9.1
**Category:** unit
**Priority:** medium
**Description:** Verify 'aom inspect <session-id>' displays full UUID not truncated
**Test:** Run inspect with full UUID as argument. Assert output shows complete UUIDv7 (not truncated). Assert summary displays full session ID
**Fixture/Setup:** Inspect command output formatting
**Edge Cases:** Using 8-char prefix as argument (resolve to full UUID)

### TC-338: Session Corrupted Handling in Inspect
**Section:** 9.1
**Category:** integration
**Priority:** medium
**Description:** Verify inspect handles corrupted/truncated .jsonl files gracefully
**Test:** Create session with malformed JSON event. Run 'aom inspect <id>'. Assert session loads with WARNING about malformed lines. Assert "(N malformed lines skipped)" shown in output
**Fixture/Setup:** Session artifact with injected malformed lines
**Edge Cases:** Empty session file, session with only malformed lines

### TC-339: Session Rotation Policy Enforcement
**Section:** 8.1
**Category:** integration
**Priority:** high
**Description:** Verify session rotation keeps last N sessions OR last N days (configurable)
**Test:** Set keep_sessions: 5. Create 10 sessions. Assert only 5 most recent remain. Set keep_days: 1. Wait 2 days. Run AOM. Assert sessions older than 1 day deleted
**Fixture/Setup:** SessionManager with rotation logic
**Edge Cases:** Session created during rotation (don't delete active), zero config (use defaults)

---

## Section 10: Keybindings

### TC-340: Keybinding Quit Confirmation
**Section:** 10.1
**Category:** integration
**Priority:** high
**Description:** Verify 'q' key shows quit confirmation dialog before exiting
**Test:** Press 'q' during run. Assert confirmation dialog appears. Accept/y confirms quit. Cancel/n dismisses dialog
**Fixture/Setup:** AOMApp with quit confirmation modal
**Edge Cases:** Quit during password prompt (different behavior)

### TC-341: Keybinding Ctrl+C First Press Forwarding
**Section:** 10.1
**Category:** integration
**Priority:** high
**Description:** Verify first Ctrl+C forwards signal to ansible-playbook subprocess
**Test:** Press Ctrl+C once during execution. Assert SIGINT sent to subprocess. Assert AOM continues running (cleanup mode)
**Fixture/Setup:** Signal handler in Runner
**Edge Cases:** Subprocess not running (show quit dialog directly)

### TC-342: Keybinding Ctrl+C Second Press Kill
**Section:** 10.1
**Category:** integration
**Priority:** critical
**Description:** Verify second Ctrl+C kills everything (AOM and subprocess)
**Test:** Press Ctrl+C twice in quick succession. Assert process terminates immediately with exit code 130
**Fixture/Setup:** Global signal handler for second interrupt
**Edge Cases:** Delayed second press (within timeout window)

### TC-343: Keybinding Tree Navigation Up Down
**Section:** 10.1
**Category:** integration
**Priority:** high
**Description:** Verify ↑/↓ keys navigate tree when tree focused
**Test:** Focus tree panel. Press ↑, assert selection moves up. Press ↓, assert selection moves down
**Fixture/Setup:** Tree view with multiple nodes, focused
**Edge Cases:** At first node (↑ does nothing), at last node (↓ does nothing)

### TC-344: Keybinding Tree Expand/Collapse
**Section:** 10.1
**Category:** integration
**Priority:** high
**Description:** Verify → expands and ← collapses tree nodes when tree focused
**Test:** Focus tree panel. Select collapsed node. Press →, assert node expands. Press ←, assert node collapses
**Fixture/Setup:** Tree view with collapsible nodes
**Edge Cases:** Leaf nodes (no children to expand)

### TC-345: Keybinding Tab Panel Switch
**Section:** 10.1
**Category:** integration
**Priority:** high
**Description:** Verify Tab switches panel focus in global context
**Test:** Press Tab from any panel. Assert focus moves to next panel in cycle. Press Shift+Tab, assert focus moves to previous panel
**Fixture/Setup:** AOMApp with multiple focusable panels
**Edge Cases:** Only one panel (Tab does nothing)

### TC-346: Keybinding Search in Log
**Section:** 10.1
**Category:** integration
**Priority:** high
**Description:** Verify Ctrl+F opens search when log panel focused
**Test:** Focus log panel. Press Ctrl+F. Assert search overlay appears. Type query, press Enter, assert matches highlighted
**Fixture/Setup:** LogPanel with search functionality
**Edge Cases:** Log empty (search still works, no matches)

### TC-347: Keybinding Panel Resize Split
**Section:** 10.1
**Category:** integration
**Priority:** medium
**Description:** Verify Ctrl+←/→ resizes panel split globally
**Test:** Press Ctrl+→, assert panel split shifts right (horizontal panels). Press Ctrl+←, assert panel split shifts left
**Fixture/Setup:** Resizable panel container
**Edge Cases:** Minimum/maximum panel sizes (stop resizing at bounds)

### TC-348: Keybinding Debug Panel Toggle
**Section:** 10.1
**Category:** integration
**Priority:** medium
**Description:** Verify 'D' toggles debug panel visibility globally
**Test:** Press 'D', assert debug panel appears. Press 'D' again, assert debug panel disappears
**Fixture/Setup:** AOMApp with mountable DebugPanel
**Edge Cases:** Debug panel already visible from other trigger

### TC-349: Keybinding Help Overlay
**Section:** 10.1
**Category:** integration
**Priority:** medium
**Description:** Verify '?' shows help overlay globally
**Test:** Press '?', assert help overlay appears with keybinding reference. Press Escape or 'q', assert overlay dismisses
**Fixture/Setup:** HelpScreen modal
**Edge Cases:** Help during password prompt (block or allow)

### TC-350: Keybinding Settings Screen
**Section:** 10.1
**Category:** integration
**Priority:** medium
**Description:** Verify 'S' opens settings screen globally
**Test:** Press 'S', assert settings screen appears. Assert configurable options visible (themes, etc.). Press Escape, assert returns to main
**Fixture/Setup:** SettingsScreen modal with theme selector
**Edge Cases:** Settings during execution (changes apply immediately or on re-run)

### TC-351: Keybinding Re-run Same Args
**Section:** 10.1
**Category:** integration
**Priority:** medium
**Description:** Verify 'R' re-runs playbook with same args (post-run only)
**Test:** After completion, press 'R'. Assert playbook restarts with same arguments. Assert new session created
**Fixture/Setup:** Re-run functionality tracking original args
**Edge Cases:** Re-run during execution (no-op or show error)

### TC-352: Keybinding Re-run Modified Args
**Section:** 10.1
**Category:** integration
**Priority:** low
**Description:** Verify 'Shift+R' opens dialog to modify args before re-run
**Test:** After completion, press Shift+R. Assert dialog appears with editable args. Modify arg, confirm, assert re-run with new args
**Fixture/Setup:** ReRunDialog modal
**Edge Cases:** Cancel dialog (no re-run)

### TC-353: Keybinding Filter Panel
**Section:** 10.1
**Category:** integration
**Priority:** high
**Description:** Verify 'f' opens filter panel globally
**Test:** Press 'f' from any panel. Assert filter panel overlay appears with status checkboxes and text filter
**Fixture/Setup:** FilterPanel modal
**Edge Cases:** Press 'f' again (toggle close)

### TC-354: Keybinding Theme Cycle
**Section:** 10.1
**Category:** integration
**Priority:** low
**Description:** Verify Alt+T cycles through available themes globally
**Test:** Press Alt+T, assert theme changes to next in list. Continue pressing, assert themes cycle. Verify themes: Dark, Light, Solarized, Monokai (and more)
**Fixture/Setup:** Theme registry in app, theme cycling logic
**Edge Cases:** Single theme (cycling does nothing)

### TC-355: Keybinding Panel Toggle 1-5
**Section:** 10.2
**Category:** integration
**Priority:** medium
**Description:** Verify keys 1-5 toggle visibility of specific panels
**Test:** Press '1', assert Status Bar toggles. Press '2', assert Tree View toggles. Press '3', assert Summary Panel toggles. Press '4', assert Log Panel toggles. Press '5', assert Footer toggles
**Fixture/Setup:** Panel visibility management
**Edge Cases:** Toggle same key twice (show → hide → show)

### TC-356: Keybinding Panel Toggle Status Bar
**Section:** 10.2
**Category:** integration
**Priority:** low
**Description:** Verify '1' specifically toggles Status Bar visibility
**Test:** When status bar visible, press '1', assert hidden. When hidden, press '1', assert visible
**Fixture/Setup:** Status bar in panel registry
**Edge Cases:** N/A

### TC-357: Keybinding Panel Toggle Tree View
**Section:** 10.2
**Category:** integration
**Priority:** low
**Description:** Verify '2' specifically toggles Tree View visibility
**Test:** When tree visible, press '2', assert hidden. When hidden, press '2', assert visible
**Fixture/Setup:** Tree view in panel registry
**Edge Cases:** Hiding while tree has selection (preserve selection)

### TC-358: Keybinding Panel Toggle Summary Panel
**Section:** 10.2
**Category:** integration
**Priority:** low
**Description:** Verify '3' specifically toggles Summary Panel visibility
**Test:** When summary visible, press '3', assert hidden. When hidden, press '3', assert visible
**Fixture/Setup:** Summary panel in panel registry
**Edge Cases:** N/A

### TC-359: Keybinding Panel Toggle Log Panel
**Section:** 10.2
**Category:** integration
**Priority:** low
**Description:** Verify '4' specifically toggles Log Panel visibility
**Test:** When log visible, press '4', assert hidden. When hidden, press '4', assert visible
**Fixture/Setup:** Log panel in panel registry
**Edge Cases:** Hiding log during active output (buffer or drop)

### TC-360: Keybinding Panel Toggle Footer
**Section:** 10.2
**Category:** integration
**Priority:** low
**Description:** Verify '5' specifically toggles Footer visibility
**Test:** When footer visible, press '5', assert hidden. When hidden, press '5', assert visible
**Fixture/Setup:** Footer (help hints) in panel registry
**Edge Cases:** N/A

### TC-361: Keybinding Context Tree Focused
**Section:** 10.1
**Category:** integration
**Priority:** medium
**Description:** Verify navigation keys (↑↓→←Enter) only affect tree when tree panel is focused
**Test:** Focus log panel. Press ↑, assert tree selection does NOT change. Focus tree panel. Press ↑, assert tree selection changes
**Fixture/Setup:** Focus management in AOMApp
**Edge Cases:** Global keys (q, D, f, Tab) work regardless of focus

### TC-362: Keybinding Context Log Focused
**Section:** 10.1
**Category:** integration
**Priority:** medium
**Description:** Verify search (Ctrl+F) only activates when log panel is focused
**Test:** Focus tree panel. Press Ctrl+F, assert search does NOT activate. Focus log panel. Press Ctrl+F, assert search activates
**Fixture/Setup:** Search bound to log panel focus
**Edge Cases:** Global search shortcut (if implemented)

### TC-363: Keybinding Post-Run Context
**Section:** 10.1
**Category:** integration
**Priority:** medium
**Description:** Verify re-run keys (R, Shift+R) only work after playbook completion
**Test:** During execution, press 'R', assert no action or error shown. After completion, press 'R', assert re-run initiates
**Fixture/Setup:** Re-run functionality gated on run state
**Edge Cases:** Failed execution (allow re-run)

### TC-364: Keybinding Global Context
**Section:** 10.1
**Category:** integration
**Priority:** high
**Description:** Verify global keys (q, Ctrl+C, Tab, D, ?, S, f, Alt+T, 1-5) work from any panel
**Test:** From each focusable panel, press each global key. Assert expected action occurs
**Fixture/Setup:** Global keybinding handler
**Edge Cases:** Password prompt modal open (global keys may be blocked)

---

## Section 11: Icons and Theming

### TC-365: Status Icon OK - Green Circle
**Section:** 11.1
**Category:** unit
**Priority:** high
**Description:** OK status displays green circle icon (●)
**Test:** Render task with OK status, verify icon is ● with green color
**Fixture/Setup:** Task with status OK
**Edge Cases:** Monochrome terminal

### TC-366: Status Icon Changed - Yellow Diamond
**Section:** 11.1
**Category:** unit
**Priority:** high
**Description:** Changed status displays yellow diamond icon (◆)
**Test:** Render task with changed status, verify icon is ◆ with yellow color
**Fixture/Setup:** Task with changed status
**Edge Cases:** 16-color terminal

### TC-367: Status Icon Failed - Bold Red X
**Section:** 11.1
**Category:** unit
**Priority:** high
**Description:** Failed status displays bold red X icon (✖)
**Test:** Render task with failed status, verify icon is ✖ with bold red color
**Fixture/Setup:** Task with failed status
**Edge Cases:** No-color mode

### TC-368: Status Icon Unreachable - Dim Red Circle
**Section:** 11.1
**Category:** unit
**Priority:** high
**Description:** Unreachable status displays dim red circle with dash (⊝)
**Test:** Render task with unreachable status, verify icon is ⊝ with dim red
**Fixture/Setup:** Task with unreachable status
**Edge Cases:** Unicode fallback

### TC-369: Status Icon Running - Animated Cycle
**Section:** 11.1
**Category:** unit
**Priority:** critical
**Description:** Running status cycles through quadrant icons at 4 FPS: ◐ → ◓ → ◑ → ◒ → ◐
**Test:** Verify animation cycles through all 4 icons in correct order at 4 FPS timing
**Fixture/Setup:** Running task, animation frame counter
**Edge Cases:** Task completes mid-cycle

### TC-370: Status Icon Pending - Dim Square
**Section:** 11.1
**Category:** unit
**Priority:** medium
**Description:** Pending status displays dim square (□)
**Test:** Render task not yet started, verify icon is □ with dim style
**Fixture/Setup:** Task with pending status
**Edge Cases:** Task transitioning from pending to running

### TC-371: Status Icon Skipped - Dim Circle Outline
**Section:** 11.1
**Category:** unit
**Priority:** medium
**Description:** Skipped status displays dim circle outline (○)
**Test:** Render skipped task, verify icon is ○ with dim style
**Fixture/Setup:** Skipped task
**Edge Cases:** Conditional skip

### TC-372: Running Animation Frame Rate
**Section:** 11.1
**Category:** unit
**Priority:** high
**Description:** Running icon animation completes full cycle in 1 second (4 frames at 4 FPS)
**Test:** Verify 4 frame transitions in 1 second for running task
**Fixture/Setup:** Timer mock
**Edge Cases:** Animation paused during scroll

### TC-373: Tree Icon Collapsed Node
**Section:** 11.2
**Category:** unit
**Priority:** medium
**Description:** Collapsed tree node displays right arrow (▶)
**Test:** Verify collapsed play/task shows ▶ icon
**Fixture/Setup:** Collapsed tree node
**Edge Cases:** No children to expand

### TC-374: Tree Icon Expanded Node
**Section:** 11.2
**Category:** unit
**Priority:** medium
**Description:** Expanded tree node displays down arrow (▼)
**Test:** Verify expanded play/task shows ▼ icon
**Fixture/Setup:** Expanded tree node
**Edge Cases:** Node with single child

### TC-375: Theme Cycling with Alt+T
**Section:** 11.3
**Category:** integration
**Priority:** high
**Description:** Alt+T cycles through available themes
**Test:** Press Alt+T repeatedly, verify theme cycles through Dark → Light → Solarized → Monokai → Dark
**Fixture/Setup:** AOMApp instance, theme list
**Edge Cases:** Custom themes in list

### TC-376: Theme CSS Variable Update
**Section:** 11.3
**Category:** unit
**Priority:** high
**Description:** All widgets auto-update when theme changes via CSS $ variables
**Test:** Change theme, verify all widget colors update correctly
**Fixture/Setup:** Multiple widgets with themed styles
**Edge Cases:** Widget with hardcoded colors

### TC-377: Unicode Fallback to ASCII
**Section:** 11.3 / 4.6
**Category:** unit
**Priority:** high
**Description:** Terminals without Unicode support use ASCII equivalent icons
**Test:** Set terminal without Unicode capability, verify icons fall back (●→*, ◆→+, ✖→X, ◐→@, □→.)
**Fixture/Setup:** Mock terminal without Unicode
**Edge Cases:** Mixed Unicode/ASCII output

### TC-378: Color Fallback to 16 Colors
**Section:** 11.3 / 4.6
**Category:** unit
**Priority:** medium
**Description:** 16-color terminals fall back to standard ANSI colors
**Test:** Set terminal to 16-color mode, verify icons use standard ANSI colors
**Fixture/Setup:** Terminal with 16-color capability
**Edge Cases:** Monochrome within 16-color mode

### TC-379: Monochrome Color Stripping
**Section:** 11.3 / 4.6
**Category:** unit
**Priority:** medium
**Description:** Monochrome/piped output strips all colors, uses text labels
**Test:** Run with non-color terminal, verify text labels (OK, CHANGED, FAILED) used
**Fixture/Setup:** Console with no color support
**Edge Cases:** Partial color removal

---

## Section 12: Testing Strategy

### TC-380: TDD Failing Test Before Implementation
**Section:** 12.1
**Category:** process
**Priority:** critical
**Description:** Every feature starts with a failing test
**Test:** Verify all feature implementations have corresponding failing test first
**Fixture/Setup:** Test file history verification
**Edge Cases:** Bug fixes (may start with passing test)

### TC-381: Test Pyramid Proportions
**Section:** 12.2
**Category:** system
**Priority:** medium
**Description:** Test counts follow pyramid: ~100 unit, ~50 integration, ~10 snapshot
**Test:** Run pytest --collect-only, verify test count proportions by category
**Fixture/Setup:** Full test suite
**Edge Cases:** New features adding tests

### TC-382: Pytest Framework Version
**Section:** 12.3
**Category:** unit
**Priority:** low
**Description:** pytest >=8.0 is used as test runner
**Test:** Verify pytest version in pyproject.toml and environment
**Fixture/Setup:** Dependency inspection
**Edge Cases:** Development environment

### TC-383: Pytest-Asyncio Version
**Section:** 12.3
**Category:** unit
**Priority:** low
**Description:** pytest-asyncio >=0.23 is used for async support
**Test:** Verify pytest-asyncio version
**Fixture/Setup:** Dependency inspection
**Edge Cases:** Compatibility with pytest version

### TC-384: Pytest-Textual-Snapshot Version
**Section:** 12.3
**Category:** unit
**Priority:** low
**Description:** pytest-textual-snapshot >=0.5 is used for visual regression
**Test:** Verify pytest-textual-snapshot version
**Fixture/Setup:** Dependency inspection
**Edge Cases:** Snapshot format changes

### TC-385: Textual Test App Running
**Section:** 12.4
**Category:** integration
**Priority:** high
**Description:** Textual tests use run_test() context manager
**Test:** Verify AOMApp runs with run_test() and widgets are queryable
**Fixture/Setup:** AOMApp instance
**Edge Cases:** App with long-running background task

### TC-386: Textual Test Key Press
**Section:** 12.4
**Category:** integration
**Priority:** high
**Description:** Key presses trigger expected actions in tests
**Test:** await pilot.press("q"), verify quit dialog appears
**Fixture/Setup:** AOMApp with pilot
**Edge Cases:** Multi-key sequences (Ctrl+F)

### TC-387: Subprocess Mock pexpect.spawn
**Section:** 12.5
**Category:** unit
**Priority:** high
**Description:** pexpect.spawn can be mocked for unit tests
**Test:** MockSpawn returns test JSONL events, verify parser processes them
**Fixture/Setup:** MockSpawn class with configurable events
**Edge Cases:** Timeout handling

### TC-388: Subprocess Mock is_alive
**Section:** 12.5
**Category:** unit
**Priority:** medium
**Description:** Mock is_alive() method for process state
**Test:** Verify mocked is_alive controls execution flow
**Fixture/Setup:** MockSpawn with configurable is_alive
**Edge Cases:** Process dies mid-event

### TC-389: Snapshot Test Main Screen
**Section:** 12.6
**Category:** snapshot
**Priority:** high
**Description:** Visual regression test for main screen
**Test:** Compare main screen snapshot with baseline
**Fixture/Setup:** AOMApp with loaded playbook
**Edge Cases:** Terminal size variations

### TC-390: Snapshot Test with run_before
**Section:** 12.6
**Category:** snapshot
**Priority:** high
**Description:** Snapshot tests accept run_before setup function
**Test:** Verify snap_compare works with pilot.app.load_playbook() in run_before
**Fixture/Setup:** snap_compare fixture
**Edge Cases:** Async setup function

### TC-391: Compact Renderer Rich Console Capture
**Section:** 12.7
**Category:** unit
**Priority:** high
**Description:** Compact renderer can be tested with Console.capture()
**Test:** Use console.capture() to verify rendered output contains expected strings
**Fixture/Setup:** CompactRenderer, Rich Console
**Edge Cases:** ANSI codes in captured output

### TC-392: Compact Renderer inline-snapshot
**Section:** 12.7
**Category:** snapshot
**Priority:** high
**Description:** inline-snapshot stores expected output in test file
**Test:** Verify renderer output matches snapshot, use --inline-snapshot=review to update
**Fixture/Setup:** inline-snapshot library
**Edge Cases:** Snapshot drift detection

### TC-393: Diff Snapshot All Tasks
**Section:** 12.7
**Category:** snapshot
**Priority:** high
**Description:** Diff output shows all tasks by default (including unchanged)
**Test:** Generate diff between sessions, verify unchanged tasks visible
**Fixture/Setup:** Two sessions with overlapping tasks
**Edge Cases:** Empty sessions

### TC-394: Diff Snapshot Changes Only
**Section:** 12.7
**Category:** snapshot
**Priority:** high
**Description:** --changes-only flag filters to show only changed tasks
**Test:** Generate diff with changes_only=True, verify unchanged tasks hidden
**Fixture/Setup:** Two sessions with task status changes
**Edge Cases:** No changes between sessions

### TC-395: Non-TTY Output Testing
**Section:** 12.7
**Category:** unit
**Priority:** high
**Description:** Non-TTY mode outputs correctly without cursor positioning
**Test:** Run with Console(force_terminal=False), verify output is ANSI-formatted but no cursor codes
**Fixture/Setup:** Console without terminal
**Edge Cases:** Width constraints

### TC-396: Mock pexpect Integration Test
**Section:** 12.7
**Category:** integration
**Priority:** high
**Description:** Renderer processes mock JSONL events from mock pexpect
**Test:** Feed events to renderer, verify state updates correctly
**Fixture/Setup:** Mock child with concatenated JSON events
**Edge Cases:** Malformed JSONL lines

### TC-397: parse_play_header Test
**Section:** 12.8
**Category:** unit
**Priority:** critical
**Description:** Parses "play #1 (webservers): Setup" correctly
**Test:** Verify play number, hosts, name extracted from --list-tasks output
**Fixture/Setup:** --list-tasks output parser
**Edge Cases:** Play names with colons, special characters

### TC-398: parse_task_with_role Test
**Section:** 12.8
**Category:** unit
**Priority:** critical
**Description:** Parses "nginx : Install nginx" with role extraction
**Test:** Verify role name and task name extracted separately
**Fixture/Setup:** TaskParser
**Edge Cases:** Role names with spaces

### TC-399: parse_task_without_role Test
**Section:** 12.8
**Category:** unit
**Priority:** critical
**Description:** Parses "Deploy application" without role
**Test:** Verify task parsed without role prefix
**Fixture/Setup:** TaskParser
**Edge Cases:** Task name with colon (non-role)

### TC-400: parse_tags Test
**Section:** 12.8
**Category:** unit
**Priority:** medium
**Description:** Extracts TAGS from TAB-separated format
**Test:** Verify tags extracted from "task_name\tTAGS: [tag1, tag2]" format
**Fixture/Setup:** --list-tasks output with tags
**Edge Cases:** Empty tags, special characters in tags

### TC-401: parse_include_tasks_not_expanded Test
**Section:** 12.8
**Category:** unit
**Priority:** high
**Description:** include_tasks appears as single task entry (not expanded)
**Test:** Verify include_tasks task not expanded in --list-tasks output
**Fixture/Setup:** --list-tasks output with include_tasks
**Edge Cases:** Nested include_tasks

### TC-402: parse_import_tasks_expanded Test
**Section:** 12.8
**Category:** unit
**Priority:** high
**Description:** import_tasks tasks appear inline (expanded)
**Test:** Verify import_tasks tasks appear as individual tasks
**Fixture/Setup:** --list-tasks output with import_tasks
**Edge Cases:** Conditional imports

### TC-403: state_transitions_on_start Test
**Section:** 12.8
**Category:** unit
**Priority:** critical
**Description:** IDLE → STARTING → LOADING_TASKS → READY state transitions
**Test:** Verify state machine transitions correctly on playbook start
**Fixture/Setup:** StateMachine, --list-tasks success
**Edge Cases:** Very quick transitions

### TC-404: state_on_play_start Test
**Section:** 12.8
**Category:** unit
**Priority:** critical
**Description:** READY → RUNNING on first play event
**Test:** Send v2_playbook_on_play_start, verify state transition to RUNNING
**Fixture/Setup:** StateMachine with mock events
**Edge Cases:** Multiple simultaneous plays

### TC-405: state_on_task_start_linear Test
**Section:** 12.8
**Category:** unit
**Priority:** high
**Description:** Track task start in linear strategy mode
**Test:** Verify task tracking when strategy is linear
**Fixture/Setup:** StateMachine with linear strategy detection
**Edge Cases:** Free strategy fallback

### TC-406: state_on_runner_start_free Test
**Section:** 12.8
**Category:** unit
**Priority:** high
**Description:** Detect free strategy from runner_on_start event pattern
**Test:** Verify free strategy detected when runner_on_start events arrive first
**Fixture/Setup:** StateMachine with free strategy events
**Edge Cases:** Mixed strategy within playbook

### TC-407: state_on_runner_ok Test
**Section:** 12.8
**Category:** unit
**Priority:** critical
**Description:** Set host status to OK/CHANGED on runner_on_ok
**Test:** Process v2_runner_on_ok event, verify host status updated correctly
**Fixture/Setup:** StateMachine with running task
**Edge Cases:** Host renamed mid-execution

### TC-408: state_on_runner_failed Test
**Section:** 12.8
**Category:** unit
**Priority:** critical
**Description:** Set host status to FAILED on runner_on_failed
**Test:** Process v2_runner_on_failed event, verify FAILED status and failure tracking
**Fixture/Setup:** StateMachine with running task
**Edge Cases:** ignore_errors=true (should not mark FAILED)

### TC-409: state_on_stats_completes Test
**Section:** 12.8
**Category:** unit
**Priority:** critical
**Description:** Transition to COMPLETED on v2_playbook_on_stats
**Test:** Process stats event with no failures, verify COMPLETED state
**Fixture/Setup:** StateMachine with running playbook
**Edge Cases:** Stats with failures → FAILED state

### TC-410: task_definition_uuid_matching Test
**Section:** 12.8
**Category:** unit
**Priority:** critical
**Description:** Match tasks by UUID field
**Test:** Verify task matching uses UUID field as primary method
**Fixture/Setup:** TaskDefinition with UUID
**Edge Cases:** UUID collision (extremely rare)

### TC-411: task_definition_path_matching Test
**Section:** 12.8
**Category:** unit
**Priority:** high
**Description:** Match tasks by path field as fallback
**Test:** Verify path matching when UUID unavailable
**Fixture/Setup:** TaskDefinition without UUID
**Edge Cases:** Same task in different files

### TC-412: task_definition_sequential_matching Test
**Section:** 12.8
**Category:** unit
**Priority:** medium
**Description:** Match tasks by order + name as last resort
**Test:** Verify sequential matching when UUID and path unavailable
**Fixture/Setup:** TaskDefinition with play_order/task_order
**Edge Cases:** Name normalization differences

### TC-413: dynamic_task_creation Test
**Section:** 12.8
**Category:** unit
**Priority:** high
**Description:** include_tasks creates children at runtime
**Test:** Verify include_tasks task creates child tasks dynamically
**Fixture/Setup:** TaskDefinition with task_order=-1, is_dynamic=True
**Edge Cases:** Nested include_tasks

### TC-414: role_grouping_threshold Test
**Section:** 12.8
**Category:** unit
**Priority:** high
**Description:** 5+ consecutive same-role tasks trigger grouping
**Test:** Verify 5 consecutive nginx tasks create RoleGroup node
**Fixture/Setup:** TaskParser with consecutive role tasks
**Edge Cases:** Exactly 4 tasks (no grouping)

### TC-415: phase_transition_pre_to_execution Test
**Section:** 12.8
**Category:** unit
**Priority:** critical
**Description:** PtyStreamParser detects v2_playbook_on_start for phase transition
**Test:** Verify PRE_RUN_PROMPTS → EXECUTION transition on start event
**Fixture/Setup:** PtyStreamParser
**Edge Cases:** Multiple start events

### TC-416: phase_transition_execution_to_recap Test
**Section:** 12.8
**Category:** unit
**Priority:** critical
**Description:** PtyStreamParser detects v2_playbook_on_stats for phase transition
**Test:** Verify EXECUTION → POST_RUN_RECAP transition on stats event
**Fixture/Setup:** PtyStreamParser in EXECUTION phase
**Edge Cases:** Stats event followed by more events

### TC-417: plaintext_password_detection Test
**Section:** 12.8
**Category:** unit
**Priority:** critical
**Description:** Classify password prompts in plaintext output
**Test:** Verify "BECOME password:" and "SSH password:" classified correctly
**Fixture/Setup:** PtyStreamParser password regex
**Edge Cases:** Custom password prompts

### TC-418: plaintext_recap_collection Test
**Section:** 12.8
**Category:** unit
**Priority:** high
**Description:** Collect PLAY RECAP lines from plaintext
**Test:** Verify recap lines parsed and stored for display
**Fixture/Setup:** PtyStreamParser with recap output
**Edge Cases:** Malformed recap lines

### TC-419: plaintext_warning_classification Test
**Section:** 12.8
**Category:** unit
**Priority:** medium
**Description:** Classify [WARNING] lines correctly
**Test:** Verify [WARNING] lines classified and displayed appropriately
**Fixture/Setup:** PtyStreamParser with warning lines
**Edge Cases:** Multiple warnings

---

## Section 13: Building and Distribution

### TC-420: Project Structure pyproject.toml
**Section:** 13.1
**Category:** unit
**Priority:** critical
**Description:** pyproject.toml exists at root with correct structure
**Test:** Verify pyproject.toml contains [project], [project.scripts], [build-system]
**Fixture/Setup:** Filesystem check
**Edge Cases:** Missing optional sections

### TC-421: Project Structure .python-version
**Section:** 13.1
**Category:** unit
**Priority:** medium
**Description:** .python-version file exists
**Test:** Verify .python-version file present and contains valid version
**Fixture/Setup:** Filesystem check
**Edge Cases:** Missing file (uv manages)

### TC-422: Project Structure src/ansible_aom
**Section:** 13.1
**Category:** unit
**Priority:** critical
**Description:** Source code in src/ansible_aom directory
**Test:** Verify directory structure matches specification
**Fixture/Setup:** Filesystem check
**Edge Cases:** Empty directories

### TC-423: Project Structure Core Module
**Section:** 13.1
**Category:** unit
**Priority:** critical
**Description:** Core module contains no UI dependencies
**Test:** Verify ansible_aom.core has no imports from textual or compact
**Fixture/Setup:** Import analysis
**Edge Cases:** Shared types via renderer/protocol

### TC-424: Project Structure Renderer Protocol
**Section:** 13.1
**Category:** unit
**Priority:** critical
**Description:** Renderer protocol defined in renderer/protocol.py
**Test:** Verify Protocol class with required methods: start, update_state, handle_password_prompt, handle_completion, stop
**Fixture/Setup:** Protocol inspection
**Edge Cases:** Optional methods

### TC-425: pyproject.toml Project Name
**Section:** 13.2
**Category:** unit
**Priority:** high
**Description:** Project name is ansible-aom
**Test:** Verify name = "ansible-aom" in pyproject.toml
**Fixture/Setup:** TOML parsing
**Edge Cases:** Version mismatch

### TC-426: pyproject.toml Requires Python
**Section:** 13.2
**Category:** unit
**Priority:** critical
**Description:** Requires Python >=3.14
**Test:** Verify requires-python = ">=3.14" or similar
**Fixture/Setup:** TOML parsing
**Edge Cases:** Compatibility with older Python

### TC-427: pyproject.toml Dependencies
**Section:** 13.2
**Category:** unit
**Priority:** critical
**Description:** All required dependencies listed with versions
**Test:** Verify textual>=0.60, rich, pyyaml>=6.0, pydantic>=2.0, pydantic-settings>=2.0, platformdirs>=3.0, pexpect>=4.8, psutil>=5.9, blessed>=1.20
**Fixture/Setup:** TOML parsing
**Edge Cases:** Optional dependencies

### TC-428: pyproject.toml Entry Point
**Section:** 13.2
**Category:** unit
**Priority:** critical
**Description:** Entry point aom maps to ansible_aom.cli:main
**Test:** Verify [project.scripts] aom = "ansible_aom.cli:main"
**Fixture/Setup:** TOML parsing
**Edge Cases:** Alternative entry points

### TC-429: pyproject.toml Dev Dependencies
**Section:** 13.2
**Category:** unit
**Priority:** high
**Description:** Dev dependencies include test frameworks
**Test:** Verify pytest>=8.0, pytest-asyncio>=0.23, pytest-textual-snapshot>=0.5, pytest-cov, ruff, mypy, inline-snapshot>=0.10
**Fixture/Setup:** TOML parsing
**Edge Cases:** Extra dev tools

### TC-430: pyproject.toml Hatch Build
**Section:** 13.2
**Category:** unit
**Priority:** high
**Description:** Hatchling build configuration correct
**Test:** Verify [tool.hatch.build.targets.wheel] packages = ["src/ansible_aom"]
**Fixture/Setup:** TOML parsing
**Edge Cases:** Alternative build backends

### TC-431: pyproject.toml Pytest Config
**Section:** 13.2
**Category:** unit
**Priority:** medium
**Description:** Pytest configuration present
**Test:** Verify asyncio_mode = "auto" and asyncio_default_fixture_loop_scope = "function"
**Fixture/Setup:** TOML parsing
**Edge Cases:** Custom pytest plugins

### TC-432: pyproject.toml Ruff Config
**Section:** 13.2
**Category:** unit
**Priority:** medium
**Description:** Ruff configuration present
**Test:** Verify line-length = 100, target-version = "py314"
**Fixture/Setup:** TOML parsing
**Edge Cases:** Custom ruff rules

### TC-433: pyproject.toml Mypy Config
**Section:** 13.2
**Category:** unit
**Priority:** medium
**Description:** Mypy configuration present
**Test:** Verify python_version = "3.14", strict = true
**Fixture/Setup:** TOML parsing
**Edge Cases:** Custom mypy options

### TC-434: Nuitka Build Command
**Section:** 13.3
**Category:** system
**Priority:** high
**Description:** Nuitka build produces standalone executable
**Test:** Run Nuitka build command, verify aom executable created
**Fixture/Setup:** Nuitka installed, build environment
**Edge Cases:** Cross-platform builds

### TC-435: Nuitka Onefile Output
**Section:** 13.3
**Category:** system
**Priority:** high
**Description:** Nuitka onefile mode produces single aom binary
**Test:** Verify --onefile flag creates single executable
**Fixture/Setup:** Nuitka build
**Edge Cases:** Large executable size

### TC-436: Nuitka Include Packages
**Section:** 13.3
**Category:** system
**Priority:** high
**Description:** Nuitka includes all required packages
**Test:** Verify textual, rich, yaml, pydantic, ansible_aom packages included
**Fixture/Setup:** Built executable dependency check
**Edge Cases:** Missing packages

### TC-437: Nuitka TCSS Data Files
**Section:** 13.3
**Category:** system
**Priority:** high
**Description:** Textual CSS files included in build
**Test:** Verify --include-data-files includes *.tcss files
**Fixture/Setup:** Built executable with styles
**Edge Cases:** Dynamic style loading

### TC-438: Nix Flake Structure
**Section:** 13.4
**Category:** system
**Priority:** high
**Description:** Nix flake produces buildable package
**Test:** Run nix build, verify derivation succeeds
**Fixture/Setup:** Nix environment
**Edge Cases:** Nixpkgs version pinning

### TC-439: Nix Flake Dev Shell
**Section:** 13.4
**Category:** system
**Priority:** medium
**Description:** Nix flake devShell includes development tools
**Test:** Verify devShell includes python, ruff, mypy, pytest, uv
**Fixture/Setup:** Nix environment
**Edge Cases:** Tool version mismatches

### TC-440: Nix Flake App
**Section:** 13.4
**Category:** system
**Priority:** medium
**Description:** Nix flake app runs built executable
**Test:** Run nix run, verify AOM starts correctly
**Fixture/Setup:** Nix environment
**Edge Cases:** Runtime dependencies

---

## Section 14: Error Handling

### TC-441: Crash Recovery - Stay Open After Exit
**Section:** 14.1
**Category:** integration
**Priority:** critical
**Description:** AOM stays open after playbook process exits (success, failure, or crash)
**Test:** Run playbook to completion, verify AOM remains open for review
**Fixture/Setup:** Completed playbook session
**Edge Cases:** Crashed subprocess

### TC-442: Crash Recovery - Panels Interactive
**Section:** 14.1
**Category:** integration
**Priority:** critical
**Description:** All panels remain interactive after process exits
**Test:** Complete playbook, verify tree navigation and log panel work
**Fixture/Setup:** Completed session, interactive test
**Edge Cases:** Inspect mode transitions

### TC-443: Crash Recovery - Graceful Degradation Notification
**Section:** 14.1
**Category:** integration
**Priority:** high
**Description:** Crash shows graceful degradation with brief notification modal
**Test:** Simulate crash, verify modal appears with error summary
**Fixture/Setup:** Crash simulation
**Edge Cases:** Multiple crashes in sequence

### TC-444: Crash Recovery - Auto Save Partial Session
**Section:** 14.1
**Category:** integration
**Priority:** critical
**Description:** Session data auto-saved on crash
**Test:** Crash during execution, verify partial session saved to disk
**Fixture/Setup:** Session directory, crash injection
**Edge Cases:** Crash during save

### TC-445: Graceful Degradation - JSONL Parse Failure
**Section:** 14.2
**Category:** integration
**Priority:** critical
**Description:** JSONL parse failure logs warning and displays raw output
**Test:** Send malformed JSONL, verify warning logged and raw text in log panel
**Fixture/Setup:** Malformed JSONL fixture
**Edge Cases:** Partially valid JSONL stream

### TC-446: Graceful Degradation - Tree Updates Continue
**Section:** 14.2
**Category:** integration
**Priority:** high
**Description:** Tree continues updating with degraded data on parse failure
**Test:** Send mix of valid and invalid JSONL, verify tree updates for valid events
**Fixture/Setup:** Mixed JSONL fixture
**Edge Cases:** All events invalid

### TC-447: Graceful Degradation - list-tasks Failure
**Section:** 14.2
**Category:** integration
**Priority:** critical
**Description:** --list-tasks failure falls back to dynamic tree from JSONL
**Test:** Mock --list-tasks failure, verify runtime tree building
**Fixture/Setup:** --list-tasks returning error
**Edge Cases:** No JSONL events received

### TC-448: Graceful Degradation - list-tasks Warning Message
**Section:** 14.2
**Category:** integration
**Priority:** medium
**Description:** --list-tasks failure shows "Pre-parse failed, building tree at runtime" warning
**Test:** Verify warning message displayed in UI
**Fixture/Setup:** --list-tasks failure mock
**Edge Cases:** User dismissal

### TC-449: Cancellation - First Ctrl+C Forward to Subprocess
**Section:** 14.3
**Category:** integration
**Priority:** critical
**Description:** First Ctrl+C forwards SIGINT to ansible-playbook subprocess
**Test:** Send first SIGINT, verify subprocess receives signal and graceful termination
**Fixture/Setup:** Running subprocess
**Edge Cases:** Subprocess already terminating

### TC-450: Cancellation - Second Ctrl+C Kill Everything
**Section:** 14.3
**Category:** integration
**Priority:** critical
**Description:** Second Ctrl+C within 2 seconds kills everything immediately
**Test:** Send two SIGINTs within 2s, verify immediate exit
**Fixture/Setup:** Signal timing control
**Edge Cases:** Timeout boundary at exactly 2s

### TC-451: Cancellation - Save Partial Session on Kill
**Section:** 14.3
**Category:** integration
**Priority:** high
**Description:** Partial session saved on second Ctrl+C if possible
**Test:** Force kill, verify session data saved to disk
**Fixture/Setup:** Session directory
**Edge Cases:** Unsaved data loss

### TC-452: Password Timeout - 60 Second Limit
**Section:** 14.4
**Category:** integration
**Priority:** critical
**Description:** Password modal times out after 60 seconds
**Test:** Show password prompt, wait 61s, verify timeout error displayed
**Fixture/Setup:** Timer mock
**Edge Cases:** Timeout at exactly 60s

### TC-453: Password Timeout - Cancel with Error
**Section:** 14.4
**Category:** integration
**Priority:** high
**Description:** Password timeout cancels with error message
**Test:** Timeout password prompt, verify error message shown
**Fixture/Setup:** Timeout simulation
**Edge Cases:** Retry option presented

### TC-454: Password Timeout - Retry Option
**Section:** 14.4
**Category:** integration
**Priority:** high
**Description:** User can retry or abort after timeout
**Test:** After timeout, verify retry and abort options available
**Fixture/Setup:** Timeout handling
**Edge Cases:** Multiple timeouts in sequence

### TC-455: Logging - File Path XDG Compliant
**Section:** 14.5
**Category:** unit
**Priority:** high
**Description:** Log file at ~/.local/state/aom/log/aom.log
**Test:** Verify log path follows XDG state directory convention
**Fixture/Setup:** Environment variable check
**Edge Cases:** Custom XDG_STATE_HOME

### TC-456: Logging - Silent During Normal Operation
**Section:** 14.5
**Category:** unit
**Priority:** high
**Description:** Log file written but console silent during normal operation
**Test:** Run successful playbook, verify no console output from logging
**Fixture/Setup:** Log capture, stdout/stderr capture
**Edge Cases:** Errors during normal operation

### TC-457: Logging - Rotation 10MB 5 Backups
**Section:** 14.5
**Category:** integration
**Priority:** medium
**Description:** RotatingFileHandler with 10MB/file, 5 backups (50MB max)
**Test:** Generate 55MB of logs, verify only 5 backup files exist
**Fixture/Setup:** Log rotation test
**Edge Cases:** Empty log rotation

### TC-458: Logging - Non-Blocking QueueHandler
**Section:** 14.5
**Category:** unit
**Priority:** high
**Description:** QueueHandler + QueueListener writes in background thread
**Test:** Verify no I/O blocking during log write from main thread
**Fixture/Setup:** Thread timing measurement
**Edge Cases:** Queue overflow

### TC-459: Logging - DEBUG Level Events
**Section:** 14.5
**Category:** unit
**Priority:** medium
**Description:** DEBUG level logs JSONL events, state transitions, pexpect output, terminal capabilities
**Test:** Run with DEBUG level, verify detailed output in log file
**Fixture/Setup:** Debug logging enabled
**Edge Cases:** Sensitive data redaction

### TC-460: Logging - INFO Level Events
**Section:** 14.5
**Category:** unit
**Priority:** medium
**Description:** INFO level logs playbook start/end, session created, config loaded, --list-tasks completed
**Test:** Run playbook, verify lifecycle events logged at INFO
**Fixture/Setup:** Info logging
**Edge Cases:** Info during crash

### TC-461: Logging - WARNING Level Events
**Section:** 14.5
**Category:** unit
**Priority:** medium
**Description:** WARNING level logs --list-tasks failed, JSON parse error, password prompt, slow terminal
**Test:** Trigger warnings, verify warning log entries
**Fixture/Setup:** Warning conditions
**Edge Cases:** Warning flood

### TC-462: Logging - ERROR Level Events
**Section:** 14.5
**Category:** unit
**Priority:** medium
**Description:** ERROR level logs subprocess crash, ansible-playbook not found, ansible.posix not installed
**Test:** Trigger errors, verify error log entries
**Fixture/Setup:** Error conditions
**Edge Cases:** Error during error logging

### TC-463: Logging - Verbose Flag
**Section:** 14.5
**Category:** integration
**Priority:** high
**Description:** --verbose flag enables DEBUG logging to file
**Test:** Run with --verbose, verify DEBUG level in log file
**Fixture/Setup:** CLI flag parsing
**Edge Cases:** Verbose with log level env var

### TC-464: Logging - Verbose Console Diagnostics
**Section:** 14.5
**Category:** integration
**Priority:** medium
**Description:** --verbose prints pre-execution diagnostics to console
**Test:** Run with --verbose, verify diagnostics printed before execution
**Fixture/Setup:** Console output capture
**Edge Cases:** Non-TTY verbose output

### TC-465: Missing ansible-playbook Detection
**Section:** 14.6
**Category:** unit
**Priority:** critical
**Description:** ansible-playbook not found in PATH detected at startup
**Test:** Run with ansible-playbook not in PATH, verify error before execution
**Fixture/Setup:** Mock shutil.which() returning None
**Edge Cases:** ansible-playbook in non-standard path

### TC-466: Missing ansible-playbook Exit Code
**Section:** 14.6
**Category:** unit
**Priority:** critical
**Description:** ansible-playbook not found results in exit code 127
**Test:** Verify exit code 127 when ansible-playbook missing
**Fixture/Setup:** Missing ansible-playbook
**Edge Cases:** Other errors after ansible-playbook check

### TC-467: Missing ansible-playbook Error Message
**Section:** 14.6
**Category:** unit
**Priority:** critical
**Description:** ansible-playbook not found shows installation instructions
**Test:** Verify error message includes apt/pip/brew install suggestions
**Fixture/Setup:** Missing ansible-playbook, stdout capture
**Edge Cases:** Platform-specific suggestions

### TC-468: Missing ansible.posix Collection
**Section:** 14.6
**Category:** unit
**Priority:** critical
**Description:** ansible.posix not installed shows error and install command
**Test:** Verify error message includes ansible-galaxy collection install ansible.posix
**Fixture/Setup:** Mock ansible-galaxy collection list returning empty
**Edge Cases:** Old ansible.posix version

### TC-469: Subprocess Exit Code 0
**Section:** 14.7
**Category:** integration
**Priority:** critical
**Description:** Exit code 0 marks COMPLETED state
**Test:** Run successful playbook, verify COMPLETED state
**Fixture/Setup:** Mock subprocess returning 0
**Edge Cases:** Warnings in output (still success)

### TC-470: Subprocess Exit Code 1 - Task Failure
**Section:** 14.7
**Category:** integration
**Priority:** critical
**Description:** Exit code 1 marks FAILED state with failed hosts collected
**Test:** Run playbook with failed task, verify FAILED state and host list
**Fixture/Setup:** Mock subprocess returning 1
**Edge Cases:** Multiple failed hosts

### TC-471: Subprocess Exit Code 2 - Unreachable
**Section:** 14.7
**Category:** integration
**Priority:** high
**Description:** Exit code 2 marks FAILED state with unreachable hosts
**Test:** Run playbook with unreachable host, verify FAILED and host list
**Fixture/Setup:** Mock subprocess returning 2
**Edge Cases:** Mix of unreachable and failed

### TC-472: Subprocess Exit Code 4 - Playbook Error
**Section:** 14.7
**Category:** integration
**Priority:** high
**Description:** Exit code 4 marks CRASHED state with error shown
**Test:** Run playbook with syntax error, verify CRASHED and error message
**Fixture/Setup:** Mock subprocess returning 4
**Edge Cases:** Error code without clear message

### TC-473: Subprocess Exit Code 127 - Command Not Found
**Section:** 14.7
**Category:** integration
**Priority:** critical
**Description:** Exit code 127 marks CRASHED with "ansible-playbook not found" message
**Test:** Verify CRASHED state and appropriate message
**Fixture/Setup:** Mock subprocess returning 127
**Edge Cases:** Shell vs exec difference

### TC-474: Subprocess Exit Code 130 - SIGINT
**Section:** 14.7
**Category:** integration
**Priority:** high
**Description:** Exit code 130 marks IDLE state (user-initiated cancel)
**Test:** Run cancelled playbook, verify IDLE state
**Fixture/Setup:** Mock subprocess returning 130
**Edge Cases:** Cancel during password prompt

### TC-475: Subprocess Exit Code 137 - SIGKILL
**Section:** 14.7
**Category:** integration
**Priority:** medium
**Description:** Exit code 137 marks CRASHED with "Process was killed" log
**Test:** Run killed process, verify CRASHED and log message
**Fixture/Setup:** Mock subprocess returning 137
**Edge Cases:** Timeout vs manual kill

### TC-476: Subprocess Exit Code Negative - Signal
**Section:** 14.7
**Category:** integration
**Priority:** medium
**Description:** Negative exit code (-N) marks CRASHED with signal info logged
**Test:** Run process killed by signal, verify CRASHED and signal logged
**Fixture/Setup:** Mock subprocess returning -9 (SIGKILL)
**Edge Cases:** Unknown signal number

### TC-477: Stderr Capture
**Section:** 14.7
**Category:** integration
**Priority:** critical
**Description:** All stderr output captured and stored in session directory
**Test:** Run playbook with stderr output, verify stderr.log file created
**Fixture/Setup:** Subprocess with stderr
**Edge Cases:** Large stderr output

### TC-478: Stderr Display
**Section:** 14.7
**Category:** integration
**Priority:** high
**Description:** Stderr lines displayed in log panel (TUI) or console (compact)
**Test:** Verify stderr visible during execution
**Fixture/Setup:** Subprocess with stderr
**Edge Cases:** Stderr mixed with JSONL

### TC-479: Stderr JSON Parsing
**Section:** 14.7
**Category:** integration
**Priority:** medium
**Description:** Stderr containing JSON is parsed as JSONL event if possible
**Test:** Send JSON event via stderr, verify parsed and processed
**Fixture/Setup:** JSON in stderr
**Edge Cases:** Malformed JSON in stderr

### TC-480: Process State Monitoring Interval
**Section:** 14.7
**Category:** unit
**Priority:** high
**Description:** child.isalive() checked every 0.5 seconds
**Test:** Verify polling interval approximately 0.5s
**Fixture/Setup:** Timer mock, subprocess monitoring
**Edge Cases:** Poll during I/O

### TC-481: Orphan Process Detection
**Section:** 14.7
**Category:** integration
**Priority:** high
**Description:** Detect orphaned process that exits before JSONL events complete
**Test:** Kill subprocess early, verify orphan detection logged
**Fixture/Setup:** Early subprocess termination
**Edge Cases:** Graceful subprocess exit

### TC-482: Early Termination During LOADING_TASKS
**Section:** 14.7
**Category:** integration
**Priority:** high
**Description:** Process termination during LOADING_TASKS causes immediate CRASHED state
**Test:** Kill during --list-tasks, verify CRASHED state
**Fixture/Setup:** --list-tasks phase, early kill
**Edge Cases:** Kill after --list-tasks starts

### TC-483: Early Termination During EXECUTION
**Section:** 14.7
**Category:** integration
**Priority:** high
**Description:** Process termination during EXECUTION attempts to parse remaining buffer
**Test:** Kill during playbook execution, verify buffer parsed before state change
**Fixture/Setup:** RUNNING state, early kill
**Edge Cases:** Empty buffer on kill

### TC-484: Watchdog Timer - 60 Second Warning
**Section:** 14.7
**Category:** integration
**Priority:** high
**Description:** No output for 60 seconds logs WARNING
**Test:** Run quiet playbook >60s, verify warning logged
**Fixture/Setup:** Long-running quiet subprocess
**Edge Cases:** Watchdog reset on output

### TC-485: Watchdog Timer - 300 Second Error
**Section:** 14.7
**Category:** integration
**Priority:** high
**Description:** No output for 300 seconds logs ERROR and offers user choice
**Test:** Run quiet playbook >300s, verify error and choice prompt
**Fixture/Setup:** Very long subprocess timeout
**Edge Cases:** User choice to continue waiting

### TC-486: Watchdog Timer Reset
**Section:** 14.7
**Category:** integration
**Priority:** high
**Description:** Watchdog timer resets on any subprocess output
**Test:** Send output at intervals, verify watchdog never triggers
**Fixture/Setup:** Periodic output mock
**Edge Cases:** Output just before timer triggers

### TC-487: Watchdog Disabled During Password
**Section:** 14.7
**Category:** integration
**Priority:** critical
**Description:** Watchdog timer disabled during password prompt phase
**Test:** Show password prompt, verify no watchdog warnings during wait
**Fixture/Setup:** Password prompt state
**Edge Cases:** Password prompt >60s

---

## Section 15: Implementation Phases

### TC-488: Phase 1 Core Foundation - Project Structure
**Section:** 15
**Category:** integration
**Priority:** high
**Description:** Phase 1 creates project structure and dependencies
**Test:** Verify all Phase 1 files and directories created
**Fixture/Setup:** Clean checkout
**Edge Cases:** Phase overlap

### TC-489: Phase 1 Core Foundation - JSONL Stream Parser
**Section:** 15
**Category:** integration
**Priority:** critical
**Description:** Phase 1 implements the JSONL stream parser (`core/parser.py`)
**Test:** Verify parser processes all 10 event types
**Fixture/Setup:** JSONL event fixtures
**Edge Cases:** Invalid JSONL lines

### TC-490: Phase 2 Password Handling - Modal
**Section:** 15
**Category:** integration
**Priority:** high
**Description:** Phase 2 implements Textual password modal
**Test:** Verify password modal appears, accepts input, sends to PTY
**Fixture/Setup:** Password prompt detection
**Edge Cases:** Cancel during password entry

### TC-491: Phase 2 Password Handling - Multiple Types
**Section:** 15
**Category:** integration
**Priority:** high
**Description:** Phase 2 handles vault, become, and SSH password types
**Test:** Verify each password type handled correctly
**Fixture/Setup:** Different password prompt patterns
**Edge Cases:** Multiple passwords in sequence

### TC-492: Phase 3 Full TUI - Layout
**Section:** 15
**Category:** integration
**Priority:** high
**Description:** Phase 3 implements full TUI layout with panels
**Test:** Verify status bar, tree, summary, log, footer all rendered
**Fixture/Setup:** AOMApp launch
**Edge Cases:** Minimal terminal size

### TC-493: Phase 4 Interactive Features - Search
**Section:** 15
**Category:** integration
**Priority:** high
**Description:** Phase 4 implements Ctrl+F search overlay
**Test:** Press Ctrl+F, verify search bar appears and highlights matches
**Fixture/Setup:** Log with searchable content
**Edge Cases:** Regex search mode

### TC-494: Phase 5 Post-Run - Stay Open
**Section:** 15
**Category:** integration
**Priority:** high
**Description:** Phase 5 implements stay-open after completion
**Test:** Complete playbook, verify AOM remains interactive
**Fixture/Setup:** Completed session
**Edge Cases:** Immediate quit option

### TC-495: Phase 6 Polish - Nuitka Build
**Section:** 15
**Category:** system
**Priority:** high
**Description:** Phase 6 produces working Nuitka build
**Test:** Build with Nuitka, verify executable runs
**Fixture/Setup:** Build environment
**Edge Cases:** Distribution testing

---

## Section 5.6 Supplement: Deprecation & Warning Classification (v1.8)

### TC-496: WarningType Enum Values
**Section:** 6.1
**Category:** unit
**Priority:** critical
**Description:** WarningType enum has WARNING and DEPRECATION values
**Test:** Assert WarningType.WARNING == "warning" and WarningType.DEPRECATION == "deprecation"
**Fixture/Setup:** Import WarningType enum
**Edge Cases:** None

### TC-497: WarningEntry Dataclass Fields
**Section:** 6.1
**Category:** unit
**Priority:** critical
**Description:** WarningEntry dataclass has type, message, timestamp, and source fields
**Test:** Create WarningEntry with all fields, verify type is WarningType, message is str, timestamp is optional datetime, source defaults to ""
**Fixture/Setup:** Import WarningEntry, WarningType
**Edge Cases:** Empty message, None timestamp

### TC-498: Deprecation Warning Classification in PtyStreamParser
**Section:** 5.6
**Category:** unit
**Priority:** critical
**Description:** Lines matching `[DEPRECATION WARNING]:` are classified as WarningType.DEPRECATION
**Test:** Feed `[DEPRECATION WARNING]: Some feature is deprecated` to _handle_plaintext, verify WarningEntry with type=WarningType.DEPRECATION is created
**Fixture/Setup:** PtyStreamParser instance
**Edge Cases:** Whitespace before bracket, multi-line deprecation messages

### TC-499: Deprecated Feature Classification in PtyStreamParser
**Section:** 5.6
**Category:** unit
**Priority:** critical
**Description:** Lines matching `[DEPRECATED]:` are classified as WarningType.DEPRECATION
**Test:** Feed `[DEPRECATED]: This feature was removed in v2.15` to _handle_plaintext, verify WarningEntry with type=WarningType.DEPRECATION
**Fixture/Setup:** PtyStreamParser instance
**Edge Cases:** Distinguish from `[DEPRECATION WARNING]:` pattern

### TC-500: Regular Warning Classification in PtyStreamParser
**Section:** 5.6
**Category:** unit
**Priority:** high
**Description:** Lines matching `[WARNING]:` are classified as WarningType.WARNING (not DEPRECATION)
**Test:** Feed `[WARNING]: Could not find module` to _handle_plaintext, verify WarningEntry with type=WarningType.WARNING
**Fixture/Setup:** PtyStreamParser instance
**Edge Cases:** Warning that contains word "deprecation" in message body

### TC-501: PtyStreamParser Warnings List Contains WarningEntry Objects
**Section:** 5.6
**Category:** unit
**Priority:** high
**Description:** self._warnings is a list of WarningEntry objects, not plain strings
**Test:** After processing warning lines, verify type(self._warnings[0]) is WarningEntry
**Fixture/Setup:** PtyStreamParser with processed warnings
**Edge Cases:** Empty warnings list

### TC-502: WarningEntry Source Field for PTY Stream
**Section:** 5.6
**Category:** unit
**Priority:** medium
**Description:** WarningEntry objects from PtyStreamParser have source="controller"
**Test:** Verify source field is "controller" for all PTY-stream warnings
**Fixture/Setup:** PtyStreamParser instance
**Edge Cases:** Task-result deprecations (source would differ if captured from result.deprecations)

### TC-503: WarningEntry Timestamp from PTY Stream
**Section:** 5.6
**Category:** unit
**Priority:** medium
**Description:** WarningEntry objects capture the current timestamp from the PTY stream parser
**Test:** Process a warning line, verify the WarningEntry.timestamp matches self._current_timestamp
**Fixture/Setup:** PtyStreamParser with known timestamp
**Edge Cases:** None timestamp (if parser hasn't started)

## Section 7.6 Supplement: Deprecation Filter Panel (v1.8)

### TC-504: Filter Panel Shows Warning Checkboxes
**Section:** 7.6
**Category:** integration
**Priority:** high
**Description:** Filter panel displays Warning and Deprecation checkboxes alongside status checkboxes
**Test:** Open filter panel (press f), verify both "Warning" and "Deprecation" checkboxes are visible and togglable
**Fixture/Setup:** AOMApp with warnings and deprecations present
**Edge Cases:** No warnings present (checkboxes still shown but zero count)

### TC-505: Filter Panel Deprecation Checkbox Filters Display
**Section:** 7.6
**Category:** integration
**Priority:** high
**Description:** Unchecking "Deprecation" checkbox hides deprecation entries from tree and log views
**Test:** Open filter panel, uncheck Deprecation, verify only Warning entries remain visible; verify deprecation lines hidden in log panel
**Fixture/Setup:** AOMApp with both warnings and deprecations
**Edge Cases:** All warnings are deprecations (tree shows empty), mixed warning types

### TC-506: Filter Panel Warning Checkbox Filters Display
**Section:** 7.6
**Category:** integration
**Priority:** high
**Description:** Unchecking "Warning" checkbox hides warning entries from tree and log views
**Test:** Open filter panel, uncheck Warning, verify only Deprecation and non-warning entries visible
**Fixture/Setup:** AOMApp with both warnings and deprecations
**Edge Cases:** All entries are warnings (nothing shown after uncheck)

## Section 4.1 Supplement: Compact Mode Warning Display (v1.8)

### TC-507: Compact Mode Warning Count Display
**Section:** 4.1
**Category:** integration
**Priority:** high
**Description:** Compact mode status line shows warning ⚠ count and deprecation ✱ count
**Test:** Run playbook that produces 2 warnings and 1 deprecation, verify status line shows "⚠ 2 ✱ 1"
**Fixture/Setup:** Playbook with warning and deprecation output
**Edge Cases:** Zero warnings (⚠ omitted or shows ⚠ 0), zero deprecations

### TC-508: Compact Mode Warning Count Updates in Real Time
**Section:** 4.1
**Category:** integration
**Priority:** medium
**Description:** Warning and deprecation counts update as new warnings arrive during execution
**Test:** Start playbook, verify counts increment as warnings appear in PTY stream
**Fixture/Setup:** Playbook with staggered warning output
**Edge Cases:** Multiple warnings in rapid succession (throttled updates)

## Section 8.1 Supplement: Warning Configuration (v1.8)

### TC-509: WarningsConfig Default Values
**Section:** 8.2
**Category:** unit
**Priority:** high
**Description:** WarningsConfig defaults to show_warnings=True and show_deprecations=True
**Test:** Create WarningsConfig with no arguments, verify both fields default to True
**Fixture/Setup:** Import WarningsConfig
**Edge Cases:** None

### TC-510: WarningsConfig Show Warnings False
**Section:** 8.2
**Category:** unit
**Priority:** medium
**Description:** Setting show_warnings=False hides warnings from display
**Test:** Create WarningsConfig(show_warnings=False), render with warnings, verify warnings not shown
**Fixture/Setup:** Config with show_warnings=False
**Edge Cases:** show_warnings=True but no warnings present

### TC-511: WarningsConfig Show Deprecations False
**Section:** 8.2
**Category:** unit
**Priority:** medium
**Description:** Setting show_deprecations=False hides deprecation entries from display
**Test:** Create WarningsConfig(show_deprecations=False), render with deprecations, verify deprecations not shown
**Fixture/Setup:** Config with show_deprecations=False
**Edge Cases:** show_deprecations=True but no deprecations present

### TC-512: WarningsConfig in YAML Config File
**Section:** 8.1
**Category:** integration
**Priority:** medium
**Description:** warnings section in config.yaml is parsed into WarningsConfig
**Test:** Write config.yaml with warnings: {show_warnings: false, show_deprecations: true}, load config, verify WarningsConfig fields
**Fixture/Setup:** Config file with warnings section
**Edge Cases:** Missing warnings section (defaults apply), partial config (one field set)

---

## Test Priority Summary

| Priority | Count |
|----------|-------|
| critical | 139 |
| high | 220 |
| medium | 130 |
| low | 23 |

**Total Test Cases: 512**

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-04-20 | Initial test specification from SPECIFICATION.md v1.8 |
| 1.1 | 2026-04-20 | Added v1.8 supplement: WarningType/WarningEntry test cases (TC-496-TC-503), Deprecation filter panel (TC-504-TC-506), Compact mode warning display (TC-507-TC-508), Warning configuration (TC-509-TC-512), fixed TC-141 WARNING_PATTERNS description |