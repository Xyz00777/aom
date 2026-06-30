# `aom inspect` rebuild — design

**Status:** draft, awaiting review
**Date:** 2026-05-20
**Owner:** Felix
**Supersedes:** SPECIFICATION.md §9 (Session Inspection)

## Problem

Today's `aom inspect` is unusable for the most common debugging task: "the playbook just failed, show me why."

Concrete failures observed against a real session (run `019e4520-fa64-7000-…`, an `ansible/site.yml` run that failed on the `os_macos : Install brew casks` task):

- `aom inspect show <id> --failed` and `--tree` render only play headers; the failed task itself never appears, even though `events.jsonl` contains the full per-host `msg` / loop `results[]`.
- `aom inspect show <id>` requires the **full 36-char UUIDv7**. The 8-char `short_id` printed by `inspect list` does not resolve, contradicting the spec.
- `--state-dir` is a top-level parser argument that must precede the subcommand, which is awkward.
- `inspect list` dumps 2,908 rows with no filter and no interactive selection. Of those 2,908, **2,590 are sub-second test-suite leakage** — the test fixtures write real session dirs into `~/.local/state/aom/sessions/` instead of `tmp_path`. The user reasonably concluded that "a session is per-task" when in fact a session *is* per-run; the appearance is a test bug.

The rich data the user needs is already on disk (`msg`, per-item `results[]`, `task.path`, `_timestamp`, `stderr.log`); the renderer just doesn't surface it.

## Goals

1. From a failed run, the user can see **why** a task failed — the module's `msg`, per-loop-item errors, `stderr` — within at most two keystrokes.
2. Recent runs are browsable interactively; the user does not need to copy-paste UUIDs.
3. The default invocation (`aom inspect`, no args) lands directly in the inspector with the most recent run pre-selected.
4. Non-TTY contexts (CI, SSH, pipes) still work via a text-mode fallback.
5. Test runs stop polluting the user state directory.

## Non-goals

- Cross-run diffing. The current `inspect diff` is removed; `git diff` covers playbook source comparisons, and run-result deltas are not a debugging primitive the user reaches for.
- Editing/replaying from inside the TUI. Re-run still goes through `aom rerun` (the `R` key copies a rerun command to the clipboard rather than invoking it).
- Live tail of an in-progress run. The inspector reads finalised session dirs; the streaming view is `aom`'s default compact renderer.

## CLI surface

| Command | Behavior |
|---|---|
| `aom inspect` | Launch TUI, most-recent run pre-selected. |
| `aom inspect --text` | Print most-recent run's text-mode summary (run header + failure detail). Also implied when stdout is not a TTY. |
| `aom inspect prune [--days N] [--keep N]` | Manual cleanup of old sessions. Kept from the existing CLI. |

**Removed:** `aom inspect list`, `aom inspect show`, `aom inspect diff`, and the previously-considered `aom inspect <prefix>` positional. Rationale: users navigate chronologically inside the TUI, so a CLI-level prefix selector buys nothing once the no-arg invocation lands them in a browsable list.

`--state-dir` is a subcommand-level flag:
```bash
aom inspect --state-dir /tmp/aom
```

### Surfacing the session ID at the end of a run

`aom <playbook>` (the streaming runner, not `inspect`) currently records a session dir but never tells the user the ID. The inspector cannot help if the user doesn't know a session exists. Therefore:

- On every normal termination (clean exit, failure exit, `Ctrl+C`), the compact renderer prints a final one-line footer:
  ```
  Session 019e4520-fa64-7000-…   aom inspect
  ```
  The 8-char short ID is rendered prominently; the hint at the right tells the user how to drill in. Suppressed when `--no-session` is passed or when output is not a TTY *and* `--quiet` is set (so JSON/CI usage stays clean).
- On crash (uncaught exception during runner setup before a session exists), nothing extra is printed.
- The TUI mode (`--tui`) prints the same line to stderr after exit so it's visible in the scroll-back.

## TUI layout

Three-pane single screen, sized for a 24×80 minimum terminal. Pane widths reflow with terminal size; on very narrow terminals the right pane stacks below.

```
┌─ Runs ─────────────────────────┬─ Tasks ────────────────────────┬─ Detail ───────────────────────────┐
│   Date         Playbook    Dur │ ▼ Play: all       44✓ 2✖ 2○    │ TASK   os_macos : Install brew     │
│ ──────────────────────────────  │   caeli: 22✓ 1✖                │        casks                       │
│ ▶ 2026-05-20 12:38  …site.yml  │   web2:  22✓ 1✖                │ FILE   roles/os_macos/tasks/       │
│                          7s  ✓ │                                │        main.yml:42                 │
│   2026-05-20 11:24  …site.yml  │   ▶ common         6 tasks 18✓ │ HOST   caeli                       │
│                          3m  ✖ │   ▼ os_macos       8 tasks 15✓ │ TIME   1m03s   STATUS  failed      │
│   2026-05-20 01:37  …site.yml  │       1✖                       │ ──────────────────────────────────  │
│                          27s ✖ │     ● update brew         1✓   │ msg: One or more items failed      │
│   2026-05-19 18:02  playbooks/ │     ● list installed      1✓   │                                    │
│                  deploy.yml ✓  │   ✖ Install brew casks    1✖   │ Failed items (2 of 24):            │
│   …                            │     └ caeli       1m03s        │   ✖ karabiner-elements             │
│                                │     ● post-install cleanup 1✓  │     Cask not available             │
│                                │   ▶ web           12 tasks     │     stderr: curl: (22) 404         │
│                                │              11✓ 1✖ 2○         │   ✖ rectangle                      │
│                                │                                │     Download failed                │
│                                │                                │ ▶ OK items (22)        [Space]     │
│                                │                                │ ──── stderr.log (tail) ────────── │
│ /  filter   f  failed-only     │ Space  expand   h  hide-OK     │ + brew update                      │
│ p  prune                       │ c  chronological   g  goto fail│ Updated 2 taps...                  │
│ ↑↓ select   Enter drill        │ n/N  next/prev failure         │ O stdout  J raw  R copy-rerun  y yank│
└────────────────────────────────┴────────────────────────────────┴────────────────────────────────────┘
```

### Pane: Runs (left)

**Column header:** `Date | Playbook | Dur` (always visible, distinguishes the pane from the data rows).

**Each row:** full ISO date + time on one line, playbook path (truncated mid-path with `…` when needed, full path shown in the focus row tooltip / detail header), duration, status icon. Two visual lines per row keeps wide playbook paths readable on narrow terminals.

**Selection:** newest first, pointer (`▶`) on the focused row. Arrow keys / `j`/`k` scroll. Initially focused on row 0 (latest run) or on the row matching `<prefix>` if supplied.

**Filters:**
- `/` opens a fuzzy filter (matches against playbook path + date + short id).
- `f` toggles failed-only (`status in {failed, crashed}`).
- Filter state persists for the session but not across launches.

**Actions:**
- `Enter` moves focus to the Tasks pane.
- `p` triggers an in-app prune prompt (`Prune sessions older than N days (default 30): `, Enter to confirm). On completion, reloads the list and reports `Pruned N sessions`.

### Pane: Tasks (middle)

**Hierarchy** (rolled up from `events.jsonl`):

```
Play
└── Role-or-source-group        ← grouping key (see below)
    └── Task
        └── Host                ← only shown when expanded or when task has mixed per-host outcomes
```

**Grouping key:** `task.role` when present in JSONL events. Otherwise the first non-`tasks/` path component of `task.path` (e.g. `playbooks/site.yml:8` → group "playbooks"; `roles/os_macos/tasks/main.yml:42` → group "os_macos"). Falls back to "Tasks" when no signal exists.

**Stats at every level:**
- Aggregate counts: `N tasks  Mok✓ Mfailed✖ Mskipped○ Munreachable⊝ Mchanged◆`. Counts are summed over (task × host) pairs, so a task that runs on three hosts with two OK and one failed contributes `2✓ 1✖`.
- Per-host breakdown: listed inline below the aggregate row when the parent spans multiple hosts. Format: `caeli: 22✓ 1✖`. Hosts with no contribution to a subtree are omitted.

**Default expansion (smart):**
- Plays: expanded.
- Group nodes: **collapsed if all-OK**, **expanded on path to first failure**.
- Failed tasks: per-host children auto-expanded.

**Keys:**
- `Space`: toggle expand/collapse on focused node.
- `h`: hide all all-OK subtrees globally (toggles).
- `c`: switch to chronological view (flat list of tasks sorted by `_timestamp`); pressing again restores hierarchy.
- `g`: jump cursor to the first failure.
- `n` / `N`: next / previous failure.
- `Enter`: focus Detail pane on the currently-selected task+host.

**Selection unit:** a (task, host) pair when a per-host child is focused, otherwise the task aggregated across hosts. The Detail pane renders the appropriate level.

### Pane: Detail (right)

**Header** (always shown):
- `TASK`  full task name (wraps).
- `FILE`  `task.path` (file:line); when the run lives under a clear playbook root, prefix with the playbook's base path so the user sees `roles/os_macos/tasks/main.yml:42` rather than just `main.yml:42`.
- `HOST`  hostname (or comma-list when aggregated across hosts).
- `TIME`  duration (derived from event-pair `_timestamp` deltas).
- `STATUS`  one of `ok | changed | failed | skipped | unreachable | running`.

**Body — failure case (default for failed/unreachable):**
1. Top-level `msg` (highlighted).
2. For loop tasks: failed items expanded with their per-item `msg`, `stderr`, `module_stderr`. OK items collapsed (`▶ OK items (N)  [Space]`).
3. Module `stdout`: collapsed to a 3-line excerpt by default; `O` to expand fully (loops can produce hundreds of lines of brew/apt output).
4. `stderr.log` tail: last ~20 lines of the session-wide stderr.log, rendered below a separator. The "tail" is global to the session (not per task) but is the most useful piece of cross-task context.

**Body — success case:**
- Task header + duration + one-line result summary (e.g. `changed=true`, key result fields like `rc`, `cmd` if present). No full stdout/stderr dump.

**Keys:**
- `O`: toggle module stdout (collapsed/expanded).
- `J`: toggle raw JSONL event dump (debug escape hatch — shows the entire dict).
- `y`: yank focused detail body to the system clipboard (uses `pyperclip` or `OSC52` fallback).
- `R`: **copy** (not invoke) a rerun command to the clipboard. The command is constructed from the session's `meta.json` `ansible_args` plus `--limit <host>` and `--start-at-task '<task name>'`. A toast confirms `Copied: aom rerun … (from clipboard, paste to run)`.

### Cross-pane navigation

- `Tab` / `Shift+Tab`: cycle pane focus.
- `Esc`: from Detail → Tasks; from Tasks → Runs; from Runs → quit (with confirm).
- `q`: quit (with confirm).
- `?`: help overlay.
- `R` (global, when on a focused task): copy rerun command (same as detail pane).

### Edge cases

- **No sessions yet:** TUI shows a centred empty state — "No sessions yet. Run `aom <playbook>` to record one."
- **In-progress session** (no `end_time` in meta.json): rendered with `⠋` running icon and live duration (`now() - start_time`). Tasks pane shows whatever events have landed so far; rebuild on user-triggered refresh (`r`). Live tail is explicitly not a goal (see Non-goals).
- **Malformed events.jsonl:** counted and surfaced as `(N malformed lines skipped)` in the Detail header for the affected session; rest of the session still renders.
- **Multi-play playbook:** each play is a top-level node in Tasks pane. Stats roll up per play.
- **Terminal < 24×80:** clear error message, no crash (consistent with rest of codebase).
- **Non-TTY (CI, pipe):** auto-fall-back to text mode (see below).

## Text mode (`--text` / non-TTY)

Used by `aom inspect [--text] [<prefix>]` when stdout is not a TTY, or when `--text` is explicit. Output structure:

```
Session 019e4520-fa64-7000-a627-5b8efe0da85f
Playbook ansible/site.yml
Started  2026-05-20 11:24:09Z
Ended    2026-05-20 11:27:10Z
Duration 3m
Status   failed
Hosts    caeli (failed), web2 (ok)

Stats
  caeli: 22 ok, 1 failed, 0 skipped
  web2:  23 ok, 0 failed, 0 skipped

Failures (1)
─────────────
Play: all
Task: os_macos : Install brew casks
File: roles/os_macos/tasks/main.yml:42
Host: caeli
Time: 1m03s

  msg: One or more items failed

  Failed items (2 of 24):
    ✖ karabiner-elements
        Cask 'karabiner-elements' is not available
        stderr: curl: (22) The requested URL returned error: 404
    ✖ rectangle
        Download failed
        stderr: curl: (28) Operation timed out after 30000 ms

stderr.log (tail)
─────────────────
+ brew update
Updated 2 taps...
...
```

Pipe-friendly, free of ANSI control codes unless stdout is a TTY (Rich's `Console(force_terminal=False)` handles this).

## Architecture

### Module map

| New / changed | Path | Purpose |
|---|---|---|
| New | `core/inspect_model.py` | Pure functions deriving (a) run summaries, (b) hierarchical task tree per session, (c) per-task detail blocks. No I/O, no Textual deps. |
| New | `tui/screens/inspect.py` | Textual screen + 3 pane widgets. Consumes the core model. |
| New | `inspect/text.py` | Text-mode renderer for non-TTY and `--text`. Consumes the core model. |
| Rewritten | `inspect/cli.py` | Argparse for the new CLI surface; dispatches to TUI or text renderer; prefix resolver. |
| Modified | `inspect/display.py` | Keep overhead-section helper; remove `format_session_table` / `format_tree_view` (replaced by core model + new renderers). |
| Deleted | `inspect/diff.py` | Removed alongside `inspect diff` subcommand. |
| Modified | `core/session.py` | Add `find_latest_session(session_dir) -> str \| None`. |
| Modified | `runner.py` (or its end-of-run hook) | Print the session-ID footer on termination (see §Surfacing the session ID). |

### Data flow

```
events.jsonl ──► core.session.load_session()
                         │
                         ▼
            core.inspect_model.build_session_view(raw)
                         │
            ┌────────────┼─────────────┐
            ▼            ▼             ▼
       RunSummary   TaskTree    DetailBlocks
            │            │             │
            └────────────┼─────────────┘
                         ▼
              tui.screens.inspect.InspectApp        (interactive)
                         OR
              inspect.text.render(...)              (non-TTY)
```

`core.inspect_model` is the single source of truth for what the panes display. The TUI and text renderer must produce equivalent content for the same input; this is enforceable as a property test (`tests/integration/test_inspect_parity.py`).

### Key types (sketch)

```python
# core/inspect_model.py

@dataclass(frozen=True)
class RunSummary:
    session_id: str
    short_id: str           # first 8 chars, for display
    playbook: str
    start_time: datetime
    end_time: datetime | None
    duration: timedelta | None
    status: str             # ok | failed | crashed | running
    host_counts: Mapping[str, HostCounts]   # caeli -> ok=22, failed=1, ...
    failed_task_count: int

@dataclass(frozen=True)
class TaskTreeNode:
    kind: Literal["play", "group", "task", "host"]
    label: str
    path: str | None        # task.path (file:line) for tasks
    stats: StatusCounts     # ok / failed / skipped / unreachable / changed
    per_host: Mapping[str, StatusCounts]
    children: tuple["TaskTreeNode", ...]
    raw_event: dict | None  # for tasks: the on_ok/on_failed event; for hosts: ditto

@dataclass(frozen=True)
class DetailBlock:
    task_name: str
    file_line: str
    host: str | None
    duration: timedelta | None
    status: str
    msg: str | None
    failed_items: tuple[LoopItem, ...]
    ok_items: tuple[LoopItem, ...]
    module_stdout: str | None
    module_stderr: str | None
    session_stderr_tail: tuple[str, ...]
    raw_event: dict
```

Each builder is a pure function over the session dict from `load_session()`. No widget code in `core/`.

## Test-leakage fix (in-scope)

Orthogonal but necessary for the inspector to be usable today. The tests responsible:

1. Audit `tests/` for `SessionManager(...)` instantiations that don't pass `session_dir=tmp_path`. Add the parameter.
2. Add a `pytest` fixture `isolated_state_dir` (autouse for the integration tests that exercise the runner) that monkeypatches `~/.local/state/aom/sessions` to `tmp_path / "sessions"` for the duration of the test.
3. Provide a one-shot manual prune for the user: `aom inspect prune --days 1` will clear the existing backlog. (No behaviour change to prune; just a documented invocation.)

## Testing strategy

Adheres to the project's TDD rule (write failing tests first).

### Unit tests (`tests/unit/`)
- `test_inspect_model.py` — pure tests over the core model:
  - building a `RunSummary` from a sample session dict
  - hierarchy assembly (play → group → task → host)
  - stat roll-up across multiple hosts
  - smart-collapse rules (all-OK groups vs path-to-failure groups)
  - loop result extraction (failed items, OK items separated)
- `test_runner_session_footer.py` — runner prints the `Session …  aom inspect` line on clean exit, failure exit, and Ctrl+C; suppressed on `--quiet` non-TTY.

### Integration tests (`tests/integration/`)
- `test_inspect_cli.py` — `aom inspect`, `aom inspect --text`, `aom inspect prune` invocations against a fixture state dir.
- `test_inspect_parity.py` — for a curated sample of sessions (success, single-host failure, multi-host failure, loop failure, unreachable, in-progress), assert that TUI's rendered text and text-mode output cover the same key information.
- `test_session_leakage_guard.py` — fixture verifies no test ever writes to `~/.local/state/aom/sessions/`.

### TUI tests (`tests/tui/`)
- `test_inspect_screen.py` — Textual `Pilot` driven:
  - launches with last run pre-selected
  - `f` filters to failed runs only
  - `Enter` moves through panes
  - `g` jumps to first failure
  - `R` copies expected command to clipboard (mock pyperclip)
  - `--text` (CLI flag) bypasses TUI entirely

### Compact / golden frame tests
- `tests/compact/test_inspect_golden.py` — snapshot the text-mode renderer against the curated fixture sessions. Stable, ANSI-stripped.

### Fixtures
- `tests/fixtures/sessions/` — curated `events.jsonl` + `meta.json` + `stderr.log` triples covering: clean run, failed-task run (the brew-cask case from the user's report), multi-host run, loop failure, unreachable, in-progress (no end_time), malformed events.

## Open questions

None. (All design decisions resolved during brainstorming.)

## Implementation order

Suggested incremental delivery; each step ships green tests.

1. **`core.inspect_model`** + unit tests. No UI, no I/O changes.
2. **Text-mode renderer** + golden frame tests. Wires model to `aom inspect --text`. Already useful: `aom inspect --text` is a viable v1 even before the TUI lands.
3. **New CLI dispatch** (`aom inspect [--text]` + `prune`). Drops `list` / `show` / `diff` subcommands. Updates argparse + completions. Adds `core.session.find_latest_session`.
4. **Session-ID footer in the runner** + unit/integration tests. Independent of inspect work; once landed, users start discovering sessions exist.
5. **Test-leakage fix** + autouse fixture. Independent and unblocks the user's machine.
6. **TUI screen** — Runs pane first (port of text mode into a Textual list), then Tasks pane, then Detail pane. Each pane independently testable via `Pilot`.
7. **Smart defaults** (auto-collapse, auto-jump-to-failure) layered on top of the working tree pane.
8. **`R` copy-rerun + `y` yank**: needs clipboard glue (`pyperclip` with OSC-52 fallback for SSH).
9. Delete `inspect/diff.py` and its tests once nothing references it.

## Spec self-review notes

- Placeholder scan: no TBDs.
- Internal consistency: TUI and text mode both consume `core.inspect_model`; parity test enforces this.
- Scope check: one screen, one model, one text renderer; CLI surface trimmed (3 commands + flags). Implementation order suggests landing the text mode first as a partial-but-useful slice. Single design, single plan.
- Ambiguity: prefix resolution semantics (unique, ambiguous → error, no match → error) spelled out. Smart-collapse rules ("all-OK collapsed, path-to-failure expanded") spelled out with examples in the layout sketch.
