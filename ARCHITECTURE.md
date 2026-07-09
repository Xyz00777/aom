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
>
> **Disk usage:** a 200-host run with `--capture-verbose --capture-setup`
> lands around `~50MB` of `events.jsonl`; 100 such sessions stack up to
> roughly `5GB` under `~/.local/state/aom/sessions/`. Reclaim space with
> `aom inspect prune --days N`.

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

Legend: **[done]** = shipped, **[in progress]** = partially landed,
**[open]** = not yet started.

### 7.1 Introduce the missing port (`EventSource`) — **[done]**

- [done] `drivers/protocol.py` with `EventSource` Protocol.
- [done] `LiveDriver` class in `drivers/` satisfies `EventSource`; the
  pexpect pump is encapsulated behind `drive(renderer)`.
- [done] `ReplayDriver` class extracted; replay flows through the same
  `driver.drive(renderer)` seam as the live run.
- [done] `cli.py` reduces to: construct driver, construct renderer,
  call `driver.drive(renderer)`.

### 7.2 Move infrastructure out of the top level — **[done]**

- [done] `runner.py`        → `ansible/runner.py`
- [done] `replay.py`        → `drivers/replay.py`  (entry point relocates to `cli.py`)
- [done] `json_renderer.py` → `formats/json.py`
- [done] `core/preflight.py` → `ansible/preflight.py` (uses subprocess — not pure)
- [done] `core/session.py`  → `session/store.py` + `session/summary.py` (file I/O leaves `core/`)

### 7.3 Split the `compact/` god module — **[done]**

`compact/renderer.py` was ~1.5k lines. Now split into:

- [done] `compact/format.py` — pure formatters (`format_status_bar`,
  `format_host_rows`, `format_tree_block`, `format_failure_recap`,
  `format_preflight_summary`, `format_host_summary`, `_compute_*`,
  `collect_tags`, `count_*`).
- [done] `compact/exit_code.py` — kept as a backward-compat re-export
  shim; the canonical implementation now lives in `core/exit_code.py`
  (see §7.9 / M2 below).
- [done] `compact/renderer.py` — only the `CompactRenderer` class
  (Rich Live lifecycle, tick orchestration, password pass-through
  coordination).

### 7.4 Rename clashes & misleading names — **[done]**

- [done] `core/state.py` → `core/state_machine.py`. `core/state.py` is
  removed; `RunState` continues to live in `core/models.py`.
- [done] `inspect/display.py` → `inspect/formatters.py`. `inspect/display.py`
  is removed; `compact/display.py` remains untouched.

### 7.5 Pull pure prompt detection into `core/` — **[done]**

- [done] `is_password_prompt` and `_looks_like_interactive_prompt` now
  live in `core/prompts.py` as pure text heuristics.
- [done] `compact/password.py` keeps only the terminal pass-through;
  `runner.py` keeps only the driver-side decision to fire a prompt.

### 7.6 Complete the `Renderer` Protocol surface — **[in progress]**

- [done] `renderer/protocol.py` declares the full surface with a
  per-method mandatory / no-op-able table in the module docstring.
  `protocol.py` is the explicit source of truth for the surface.
- [done] `SPECIFICATION.md §2.3` already points at `protocol.py` as
  the source of truth.
- [open] The factory code-block in `SPECIFICATION.md §2.3` still shows
  the legacy `tui_mode: bool = False` factory signature; the real
  factory (`renderer/factory.create_renderer`) accepts a `mode`
  literal (``"compact"`` / ``"tui"`` / ``"json"``) and keeps
  `tui_mode` / `format` only as deprecated aliases. Refresh that
  example to match §7.7.

### 7.7 Factory covers all renderers — **[done]**

- [done] `renderer/factory.create_renderer(mode=...)` accepts
  ``"compact"`` / ``"tui"`` / ``"json"`` and returns the matching
  concrete renderer. The legacy `tui_mode` (bool) and `format` (str)
  parameters are kept as deprecated aliases so older callers and tests
  keep working — `mode` wins when both are supplied. The CLI no longer
  special-cases JSON output.
- [open] Once §7.6's spec refresh lands, drop the deprecated aliases
  in `renderer/factory.py` and migrate all call sites to `mode=`.

### 7.8 Enforce boundaries in CI (cheap) — **[in progress]**

- [done] `tests/unit/test_layering.py` ships and passes (5 tests). It
  parses every module under `src/ansible_aom/` for `import` statements
  (top-level *and* lazy, inside function bodies) and asserts the rules
  in §1–2:
  - `core/**` does not import from `compact/`, `tui/`, `renderer/`,
    `ansible/`, `session/`, `drivers/`, `inspect/`, `rerun/`, `formats/`.
  - `drivers/**` does not import from `compact/`, `tui/`, `formats/`.
  - `compact/**`, `tui/**`, `formats/**` do not import from each other.
  - `renderer/protocol.py` does not import a concrete renderer
    (`compact`, `tui`, `formats`); `renderer/factory.py` may.
- [open] Wire the test into pre-commit (or CI) so the layering
  invariant is enforced automatically, not just observed locally.

### 7.9 Consolidations landed alongside the refactor — **[done]**

These shipped while §7.1–§7.5 were being closed; recording them so
the gap list reflects reality.

- [done] **Exit-code derivation lives in `core/`** (GRUMPI_QA finding
  M2). `determine_exit_code(state)` was duplicated between
  `compact/exit_code.py` and `formats/json.py`; both now import the
  canonical `core/exit_code.determine_exit_code`. `compact/exit_code.py`
  is kept as a backward-compat shim for any third-party imports.
- [done] **ISO-8601 timestamp parsing consolidated** (GRUMPI_QA finding
  9C series). Nine separate ad-hoc `datetime.fromisoformat(...)` call
  sites have been collapsed to a single `parse_iso_timestamp(value)` in
  `core/timestamp.py`, which normalises the ``Z`` UTC suffix to
  ``+00:00`` defensively. All call sites in `core/`, `compact/`,
  `session/`, and `drivers/replay.py` now import from `core/timestamp`.
- [done] **State-machine dead code removed** (GRUMPI_QA finding 9A).
  `core/state.py` originally housed an 8-state `ExecutionState` enum
  and a `StateMachine` class that were never wired into production
  code (the TUI tracked state as a plain string, `compact/` relied on
  `RunState`, and the runner passed lowercase strings to
  `handle_completion`). After the §7.4 rename, `core/state_machine.py`
  contains only the memory-bounds constants (`MAX_PLAYS`,
  `MAX_TASKS_PER_PLAY`, `MAX_HOSTS_PER_TASK`,
  `MAX_TOTAL_HOST_RUN_STATES`, `MAX_LOG_LINES`) that are actually
  imported by `core/parser.py` and `tui/widgets/log_panel.py`. The
  docstring records the removal rationale.

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

---

## 9. Schemas and Data Formats

The `schemas/` directory at the repository root contains JSON Schema files
that describe the shape of AOM's non-interactive output.

### `schemas/run_summary.v1.json`

Defines the `RunSummary` object emitted by `JsonRenderer.handle_completion`
(the `--format json` renderer). The schema covers:

- **Metadata**: `schema_version` (literal `1`), `playbook` path, `exit_code`,
  `started_at` / `ended_at` (ISO 8601 with UTC offset), `duration_s` (float
  seconds, 1 dp).
- **Per-host counts** (`hosts`): a map of hostname → `HostCounts` with
  `ok`, `changed`, `failed`, `unreachable` integer counters aggregated
  across every task in every play.
- **Task failures** (`tasks_failed`): an array of `(host, task, msg)` tuples
  for every (host, task) pair that ended in `FAILED` or `UNREACHABLE`.

**Status: documentation-only.** The F6 JSON renderer (`formats/json.py`) is
implemented and the Pydantic `RunSummary` model in that module is the
authoritative source of truth. The committed `.json` file is kept for test
parity — `tests/unit/test_run_summary_schema.py` asserts the Pydantic model
matches the schema. When the model changes, regenerate with
`UPDATE_SCHEMA=1 pytest tests/unit/test_run_summary_schema.py`.

The `aom/` and `molecule/` directories that previously lived alongside
`schemas/` at the repository root have been removed; `schemas/` is the only
remaining top-level data-format directory.

---

## 10. Licensing

### 10.1 GPL subclass concern: `ansible/callback/aom_jsonl.py`

`src/ansible_aom/ansible/callback/aom_jsonl.py` subclasses
`ansible_collections.ansible.posix.plugins.callback.jsonl`, which is
licensed GPL-3.0-or-later (inherited from `ansible-core`). By subclassing
a GPL-licensed class, `aom_jsonl.py` itself is a derivative work and must
be distributed under GPL-compatible terms — which it is, as part of AOM's
GPL-3.0-or-later overall license.

**Why this does not GPL-contaminate the rest of AOM:**

1. **Process boundary.** The callback plugin runs *inside* the
   `ansible-playbook` subprocess, not inside AOM's own process. AOM
   communicates with it via the PTY (pexpect) — an arm's-length pipe,
   not a Python import or link.
2. **No import.** AOM's main codebase never imports
   `aom_jsonl.CallbackModule` or any other `ansible-core` module at
   runtime. The callback is selected by setting the `ANSIBLE_STDOUT_CALLBACK`
   environment variable before spawning the subprocess.
3. **Precedent.** This is the same pattern used by `ansible-navigator`
   (Apache-2.0) and `ansible-runner` (Apache-2.0): both shell out to
   `ansible-playbook` and parse its output without importing `ansible-core`.
   The FSF's GPL FAQ confirms that arm's-length communication via pipes
   does not trigger the GPL's copyleft provisions.

See `.sisyphus/notepads/research/decisions.md` for the full licensing
research that led to this conclusion.
