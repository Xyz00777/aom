# ARCHITECTURE — AOM (Ansible Output Monitor)

System design, module boundaries, and the development philosophy that shapes them.
For day-to-day commands and style rules see [`CLAUDE.md`](CLAUDE.md).
For behavior spec see [`SPECIFICATION.md`](SPECIFICATION.md).

This document describes the **target architecture**. Section 7 lists the gaps
between target and current source tree — that punch list is what the upcoming
refactor will close.

---

## 1. Design Principles

1. **Two ports, three layers.** Everything in the system is on one side of one
   of two protocols: `EventSource` (drives a run) and `Renderer` (sinks the
   updates). The domain layer in between knows about neither implementation.
2. **`cli.py` is the only composition root.** Only the CLI knows concrete
   adapters. Every other module depends on protocols or on pure domain types.
3. **Pure domain, no I/O.** `core/` must be importable as a plain Python
   library with zero side effects, no PTY, no Textual, no disk reads. Anything
   that touches the world lives in an infrastructure package.
4. **Pure formatting, separated from lifecycle.** A renderer's job splits in
   two: project domain state to display strings (pure), and push those strings
   to the terminal / TUI / file (impure). Tests target the pure half.
5. **Library-first.** Every `core/` module should be reusable by an unrelated
   project that just wants to parse ansible JSONL or analyse a recorded
   session.

---

## 2. Layer Map

```
                ┌──────────────────────────────────────────┐
                │ cli.py — composition root                │
                │  picks one EventSource + one Renderer    │
                └────────────┬──────────────┬──────────────┘
                             │              │
                  ┌──────────▼────┐   ┌─────▼──────────┐
                  │ EventSource   │   │ Renderer       │
                  │ Protocol      │   │ Protocol       │
                  └──────┬────────┘   └─────────┬──────┘
                         │                      │
        ┌────────────────┼──────────┐      ┌────┼─────────────┐
        ▼                ▼          ▼      ▼    ▼             ▼
   drivers/live   drivers/replay   …   compact   tui    formats/json
   (wraps              (wraps               │     │           │
    ansible/runner)     session/store)      └─────┴──── all read pure ──┐
                         │                                core/ types   │
                         ▼                                + projections │
                    session/store                                       │
                                                                        │
                              ┌──────────────────────────────┐          │
                              │ core/  (pure domain)         │◀─────────┘
                              │  models, state, events,      │
                              │  parser, redaction, tree,    │
                              │  heartbeat, inspect_model,   │
                              │  overhead, parity, icons,    │
                              │  config                      │
                              └──────────────────────────────┘
```

Two arrows leave the composition root and one arrow leaves each adapter — that
is the entire dependency story. No cycles, no back-references.

---

## 3. Module Map (target)

```
src/ansible_aom/
  __init__.py              # __version__, source_hash()
  __main__.py              # python -m ansible_aom
  cli.py                   # argparse + wiring only — no business logic
  completion.py            # argcomplete glue (small, top-level OK)
  styles/app.tcss          # Textual stylesheet

  core/                    # PURE DOMAIN — zero infra deps, library-grade
    models.py              # RunState, PlayRunState, TaskRunState, HostRunState,
                           #   PlayDefinition, TaskDefinition, RoleGroupDefinition,
                           #   Status, WarningType, WarningEntry
    state_machine.py       # ExecutionState, StateMachine (run lifecycle FSM)
                           #   [renamed from state.py to avoid clash with RunState]
    events.py              # event-type constants, MAX_LOG_LINES, JSONL field names
    parser.py              # PtyStreamParser, JsonLineStream,
                           #   parse_list_tasks_output, parse_list_hosts_output,
                           #   group_roles  (string in → events / defs out)
    redaction.py           # pure event sanitiser
    config.py              # pydantic-settings loader (boundary, but stable enough)
    icons.py               # status → glyph value map (ASCII fallback)
    heartbeat.py           # LivenessState, HeartbeatTracker
    tree.py                # TreeProjection, TreeLine, HostRow (RunState → tree)
    overhead.py            # OverheadStats from event stream
    parity.py              # RunState → renderer-agnostic dict (test oracle)
    inspect_model.py       # session-dict builders for inspect display
    prompts.py             # is_password_prompt, is_interactive_prompt
                           #   [pure text heuristics — pulled out of compact/]

  renderer/                # PORT for display sinks
    protocol.py            # Renderer Protocol (full surface, see §4)
    factory.py             # create_renderer(mode) → compact | tui | json

  drivers/                 # PORT for event sources
    protocol.py            # EventSource Protocol (see §4)
    live.py                # LiveDriver — wraps ansible/runner.py
    replay.py              # ReplayDriver — wraps session/store
                           #   [moved from top-level replay.py]

  ansible/                 # ANSIBLE INFRASTRUCTURE (subprocess, pexpect)
    runner.py              # run_playbook() — PTY spawn, JSONL pump
                           #   [moved from top-level runner.py]
    preflight.py           # parallel --list-tasks + --list-hosts orchestration
                           #   [moved from core/preflight.py — uses subprocess]

  session/                 # SESSION ARTIFACT STORAGE (file I/O)
    store.py               # SessionManager, load_session, list_sessions,
                           #   find_latest_session, cleanup_old_sessions
                           #   [moved from core/session.py — file I/O isn't pure]
    summary.py             # create_session_summary, collect_failed_hosts,
                           #   collect_unreachable_hosts, collect_changed_hosts

  compact/                 # ANSI RENDERER (implements Renderer)
    renderer.py            # CompactRenderer — Rich Live lifecycle + tick orchestration
    format.py              # PURE formatters: status_bar, host_rows, tree_block,
                           #   recap, mode_label, count_cells
                           #   [extracted from today's 1.5k-line renderer.py]
    exit_code.py           # determine_exit_code(state)
    password.py            # terminal pass-through for prompts
                           #   [pure detection moved to core/prompts.py]
    display.py             # check_terminal_size, Display helper

  tui/                     # TEXTUAL RENDERER (implements Renderer)
    app.py                 # AOMApp — does NOT import drivers; cli.py wires it
    keybindings.py
    screens/               # main, help, settings, inspect, quit_confirm, rerun
    widgets/               # task_tree, log_panel, status_bar, summary_panel,
                           #   debug_panel

  formats/                 # NON-INTERACTIVE RENDERERS
    json.py                # JsonRenderer — implements Renderer Protocol,
                           #   emits RunSummary v1 JSON
                           #   [moved from top-level json_renderer.py]

  inspect/                 # `aom inspect` CLI — session viewer (post-mortem)
    cli.py
    text.py                # plain-text rendering of a session
    formatters.py          # overhead etc. [renamed from display.py to avoid
                           #   the name clash with compact/display.py]

  rerun/                   # `aom rerun` CLI
    cli.py
```

> `.aom/` / `~/.local/state/aom/` are runtime artifact directories, **not** source.
> They are read/written via `session/store.py`.

---

## 4. The Two Protocols

These are the only inter-layer contracts. Every module either implements one of
them, depends on one of them, or is pure domain.

### 4.1 `Renderer` Protocol (`renderer/protocol.py`)

A sink for run progress. Concrete: `CompactRenderer`, `AOMApp`, `JsonRenderer`.

```python
class Renderer(Protocol):
    # Lifecycle
    def start(self, playbook: str, args: list[str]) -> None: ...
    def stop(self) -> None: ...

    # Definitions provided once after preflight
    def set_definitions(self, definitions: list[PlayDefinition]) -> None: ...

    # Per-event updates
    def update_state(self, event: dict) -> None: ...

    # Diagnostics + telemetry pushed by the driver
    def add_warning(self, warning: WarningEntry) -> None: ...
    def print_log(self, line: str) -> None: ...
    def note_pty_bytes(self, n: int) -> None: ...
    def note_subprocess_active(self, active: bool) -> None: ...
    def tick(self) -> None: ...

    # Interactive prompts (live driver only — replay/json no-op)
    def handle_password_prompt(self, prompt_text: str) -> str: ...
    def handle_interactive_prompt(self, prompt_text: str) -> str: ...

    # Terminal state
    def handle_completion(self, exit_code: int, state: str) -> None: ...
```

Optional methods (replay/JSON renderers no-op them) must be explicitly documented
on the Protocol so a new renderer knows what it can skip.

### 4.2 `EventSource` Protocol (`drivers/protocol.py`) — **new**

A producer of run events. Concrete: `LiveDriver`, `ReplayDriver`.

```python
class EventSource(Protocol):
    def drive(self, renderer: Renderer) -> int:
        """Pump events into renderer; return process exit code."""
        ...
```

This is the seam that's missing today. With it:

- `cli.py` becomes 100% wiring: pick a driver, pick a renderer, call
  `driver.drive(renderer)`.
- Replay tests can swap in a `FakeRenderer` and ignore I/O.
- TUI tests can swap in a `ScriptedDriver` and ignore subprocess.
- `tui/app.py` stops importing `runner` directly — the driver is passed in.

---

## 5. Data Flow

### Live run (composition root: `cli.py`)

```
cli.py
  ├── load AppConfig (core/config)
  ├── preflight = ansible/preflight.run_preflight(playbook, args)
  │     → list[PlayDefinition]
  ├── driver   = drivers.live.LiveDriver(playbook, args, preflight)
  ├── renderer = renderer.factory.create_renderer(mode, ...)
  ├── exit_code = driver.drive(renderer)
  └── session/store writes the .aom artifact (driven by LiveDriver's sink)
```

Inside `LiveDriver.drive(renderer)`:

```
ansible/runner.run_playbook(playbook, args, sink=...)
  → pexpect PTY → bytes
  → core/parser.PtyStreamParser → classified events
  → renderer.update_state(event)  for JSONL
  → renderer.print_log(line)      for plaintext
  → renderer.handle_password_prompt(...) on detection
  → renderer.handle_completion(exit_code, state) on exit
```

### Replay (composition root: `cli.py` via `aom replay`)

```
cli.py
  ├── session = session/store.load_session(id)
  ├── driver  = drivers.replay.ReplayDriver(session)
  ├── renderer = factory.create_renderer(mode)
  └── exit_code = driver.drive(renderer)
```

`ReplayDriver` re-emits the recorded events through the same `Renderer`
interface. Bit-for-bit cross-renderer parity is asserted via
`core/parity.reduce_state_for_parity`.

### Inspect (post-mortem)

`aom inspect` does not use the renderer/driver pair — it's a non-streaming
viewer. It calls `session/store.load_session()` and renders via
`core/inspect_model` + `inspect/text` or the inspect Textual screens.

---

## 6. Key Architectural Decisions

1. **Two-port architecture.** `Renderer` + `EventSource` are the only
   horizontal contracts. New renderers (`html`, `prometheus`, …) and new
   sources (`fixture`, `network-stream`, …) plug in without touching anything
   else.

2. **Strategy detection at runtime.** The JSONL callback does NOT emit a
   `strategy` field. Detect linear vs free by observing whether
   `v2_playbook_on_task_start` or `v2_runner_on_start` arrives first after a
   play begins.

3. **Role grouping.** 5+ consecutive tasks sharing the same role auto-collapse
   into a "Role: name (N tasks)" node. Lives in `core/parser.group_roles`.

4. **`include_tasks` dynamic expansion.** `--list-tasks` does NOT expand
   `include_tasks`. When JSONL events arrive for unknown tasks, create
   `TaskDefinition` with `is_dynamic=True`, `task_order=-1`, parented to the
   `include_tasks` node.

5. **Interactive prompt handling.** Detection is a pure heuristic
   (`core/prompts`). Response is renderer-specific: compact stops Rich Live
   and lets terminal pass-through handle getpass; TUI shows a Textual
   `Input(password=True)` modal; JSON renderer fails fast (no human present).
   The driver simply calls `renderer.handle_password_prompt(...)`.

6. **Secrets redaction.** Four layers: (1) honour `_ansible_no_log`,
   (2) pattern-match field names against Ansible's `PASSWORD_MATCH` regex
   plus known secret field names, (3) sanitise strings, (4) configurable
   whitelist for false positives like `passenger_version`.
   Applied in `core/redaction` before any renderer sees the event.

7. **Pure formatting is in `core/` or in `<renderer>/format.py`.** Lifecycle
   classes (`CompactRenderer`, `AOMApp`, `JsonRenderer`) own state machines
   and I/O; they delegate text construction to pure functions that take
   `RunState` + `list[PlayDefinition]` and return strings.

8. **Session storage is infrastructure.** File-format reads/writes live in
   `session/store.py`, not in `core/`. `core/inspect_model` takes a session
   dict as input — it does not know where that dict came from.

---

## 7. Gap from Current Source Tree → Target

Concrete refactor punch list. Each item is independently shippable; ordering is
suggested for low-risk landing.

### 7.1 Introduce the missing port (`EventSource`)

- Add `drivers/protocol.py` with `EventSource` Protocol.
- Extract `run_playbook` driving loop in `runner.py` behind a `LiveDriver`
  class that satisfies `EventSource`.
- Extract `replay_session` body behind a `ReplayDriver` class.
- `cli.py`, `tui/app.py`, and `replay.py` all reduce to: construct driver,
  construct renderer, call `driver.drive(renderer)`.

### 7.2 Move infrastructure out of the top level

- `runner.py`        → `ansible/runner.py`
- `replay.py`        → `drivers/replay.py`  (entry point relocates to `cli.py`)
- `json_renderer.py` → `formats/json.py`
- `core/preflight.py` → `ansible/preflight.py` (uses subprocess — not pure)
- `core/session.py`  → `session/store.py` + `session/summary.py` (file I/O leaves `core/`)

### 7.3 Split the `compact/` god module

`compact/renderer.py` is currently ~1.5k lines. Split into:

- `compact/format.py` — all pure formatters (`format_status_bar`,
  `format_host_rows`, `format_tree_block`, `format_failure_recap`,
  `format_preflight_summary`, `format_host_summary`, `_compute_*`,
  `collect_tags`, `count_*`).
- `compact/exit_code.py` — `determine_exit_code(state)`.
- `compact/renderer.py` — only the `CompactRenderer` class (Rich Live
  lifecycle, tick orchestration, password pass-through coordination).

### 7.4 Rename clashes & misleading names

- `core/state.py` → `core/state_machine.py` (today's `state.py` is a
  lifecycle FSM, while `RunState` lives in `models.py` — the current name
  invites confusion).
- `inspect/display.py` → `inspect/formatters.py` (name collides with
  `compact/display.py`, which does a completely different job).

### 7.5 Pull pure prompt detection into `core/`

- `is_password_prompt` and `_looks_like_interactive_prompt` are pure text
  heuristics. Move to `core/prompts.py`. `compact/password.py` keeps only
  the terminal pass-through; `runner.py` keeps only the driver-side
  decision to fire a prompt.

### 7.6 Complete the `Renderer` Protocol surface

- `renderer/protocol.py` already declares the full surface, but
  `SPECIFICATION.md §2.3` is stale. Mark `protocol.py` as the source of
  truth, update the spec to point there, and ensure every method has a
  docstring stating whether it is mandatory or no-op-able.

### 7.7 Factory covers all renderers

- `renderer/factory.create_renderer` currently dispatches between compact
  and TUI; `JsonRenderer` is wired separately. Add `mode="json"` so the
  CLI doesn't special-case JSON output.

### 7.8 Enforce boundaries in CI (cheap)

Add an import-linter or a small custom test (`tests/unit/test_layering.py`)
that asserts:

- `core/**` does not import from `compact/`, `tui/`, `renderer/`,
  `ansible/`, `session/`, `drivers/`, `inspect/`, `rerun/`, `formats/`.
- `drivers/**` does not import from `compact/`, `tui/`, `formats/`.
- `compact/**`, `tui/**`, `formats/**` do not import from each other.

The current `core/` is clean today (verified by grep) — codify it before it
drifts.

---

## 8. Development Philosophy

### TDD with Strict OODA Loop

ALL development follows a Test-Driven Development cycle with the OODA loop:

```
1. OBSERVE:   Read the spec section and matching TC-XXX test cases
2. ORIENT:    Write the test FIRST — assert expected behavior
3. DECIDE:    Run the test — it MUST fail (red phase)
4. ACT:       Implement the minimum code to make it pass (green phase)
5. ABSTRACT:  Can this logic be abstracted into the core library?
              - Pure logic with no I/O → extract to core/
              - Depends on pexpect/Textual/TTY → keep in infrastructure layer
              - Mixed → split into core logic + thin infrastructure wrapper
6. LOOP:      Refactor (clean), then next test case — NEVER skip a cycle
```

**Golden rules:**

- **More tests are better than fewer tests.** When in doubt, ADD another test.
- **Tests are specification.** If the spec says something should happen,
  there MUST be a test asserting it.
- **Never implement without a failing test first.**
- **Run the full suite after every change.** `uv run pytest tests/ -q`
  must be green before pushing.
- **Coverage gaps are bugs waiting to happen.**

### Domain-Driven Design

The codebase uses DDD to keep business logic decoupled from infrastructure.

**Core domain (`core/`):**

- **Entities**: `PlayRunState`, `TaskRunState`, `HostRunState` (mutable identity)
- **Value objects**: `Status` enum, `WarningType` enum, `WarningEntry`,
  `TaskDefinition`, `PlayDefinition`, `RoleGroupDefinition`
- **Aggregate**: `RunState` (transactional boundary)
- **Domain services**: `StateMachine`, `PtyStreamParser`, `redact_event`,
  `TreeProjection`, `HeartbeatTracker`, `analyze_overhead`,
  `reduce_state_for_parity`
- **Ports**: `Renderer` Protocol (`renderer/protocol.py`),
  `EventSource` Protocol (`drivers/protocol.py`)
- **Adapters**: everything in `ansible/`, `session/`, `compact/`, `tui/`,
  `formats/`, `inspect/`, `rerun/`

**Rule (enforced by §7.8):** core domain modules must NEVER import from any
infrastructure package. Infrastructure depends on core, never the reverse.

### Library-First

Every `core/` module is designed as a reusable library.

Before adding any feature, ask:

1. Does this logic belong in `core/` or is it infrastructure-specific?
2. Could another Python project import this module and use it?
3. Does this function have any implicit dependency on pexpect, Textual,
   subprocess, or the TTY?

The **ABSTRACT** step in the OODA loop is mandatory. Code that belongs in
`core/` but lives in an infrastructure package is a design defect.
