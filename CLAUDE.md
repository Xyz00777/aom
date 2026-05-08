# CLAUDE.md — AOM (Ansible Output Monitor)

> Claude Code auto-loads this file. Keep it current.

## What We're Building

**ansible-aom** — nom-style TUI for monitoring `ansible-playbook` in real time. Think `nom build` but for Ansible.

- **Default**: Compact ANSI streaming view (lightweight, no Textual)
- **Optional**: Full multi-panel Textual TUI (`--tui` flag)
- **Parsing**: JSONL only via `ansible.posix.jsonl` callback — never regex
- **Stack**: Python 3.14, Textual ≥0.60, pexpect, Rich, Pydantic, blessed
- **Build**: hatchling, managed by `uv`

## Setup (One Time)

```bash
direnv allow                  # Nix dev shell (or do it manually below)
uv sync --all-extras          # Install all deps incl. dev + integration
uv run pip install -e .       # Editable install so `aom` works
uv run aom --help             # Verify
```

If you don't use Nix: skip `direnv`, just run the `uv` commands directly.

## Everyday Commands

```bash
uv run ruff format            # Format
uv run ruff check --fix       # Lint
uv run mypy src/ansible_aom   # Type check
uv run pytest tests/ -q       # All tests
uv run pytest tests/unit/ -q  # Unit only
uv run pytest tests/ -x -q    # Fail fast
uv run pytest tests/ --cov=src/ansible_aom --cov-report=term-missing
```

## Module Map (src/ansible_aom/)

```
cli.py                       # CLI entry: argument parsing, inspect subcommand routing
__main__.py                  # python -m ansible_aom
__init__.py                  # __version__ = "0.1.0"

renderer/
  protocol.py                # Renderer Protocol — both backends satisfy this
  factory.py                 # create_renderer(tui_mode=bool) → CompactRenderer or AOMApp

core/
  models.py                  # All dataclasses: PlayDefinition, TaskDefinition, HostRunState, etc.
  state.py                   # State machine: processes JSONL events, maintains run state
  parser.py                  # Parses --list-tasks and --list-hosts plaintext output (TAB-separated!)
  config.py                  # Pydantic-settings config (~/.config/aom/config.yaml)
  session.py                 # Session artifact writer (.aom/ directory)
  icons.py                   # Status icon map (● ◆ ✖ ⊝ ◐ □) + ASCII fallback (* + X @ .)
  redaction.py               # Defense-in-depth secret redaction for JSONL events

compact/
  renderer.py                # CompactRenderer: Rich Live + ANSI cursor positioning
  display.py                 # Status panel formatting/layout
  logs.py                    # Log line buffer and management
  password.py                # Terminal pass-through for password prompts

tui/
  app.py                     # AOMApp: Textual App subclass
  keybindings.py             # Keyboard shortcut registry
  screens/                   # main, help, settings, inspect, quit_confirm, rerun
  widgets/                   # task_tree, summary_panel, status_bar, log_panel, debug_panel

inspect/
  cli.py                     # `aom inspect` subcommand implementation
  display.py                 # Rich-formatted session output
  diff.py                    # Diff two sessions
```

## Data Flow

```
Startup:
  CLI → check ansible.posix installed
      → parallel: --list-tasks + --list-hosts
      → build tree + resolved hosts
      → factory creates CompactRenderer or AOMApp

Runtime:
  pexpect.spawn(ansible-playbook, env={ANSIBLE_STDOUT_CALLBACK=ansible.posix.jsonl})
      → stream lines via PTY
      → PtyStreamParser: classify phase, route JSONL events vs plaintext
      → State.update(event): mutate HostRunState, TaskRunState, PlayRunState
      → call_from_thread → renderer.update_state()
      → re-render (throttled to 4 FPS, debounced 250ms)

Completion:
  v2_playbook_on_stats → final aggregation
  optional PLAY RECAP → capture
  process exit → session.save_artifact()
```

## Key Architectural Decisions

1. **Renderer Protocol** — Both backends implement the same Protocol, chosen at startup by `--tui`. Never hardcode UI assumptions in core.

2. **Strategy Detection at Runtime** — The JSONL callback does NOT emit `strategy` field. Detect linear vs free by observing whether `v2_playbook_on_task_start` or `v2_runner_on_start` arrives first after a play begins.

3. **Role Grouping** — 5+ consecutive tasks sharing the same role → auto-collapse into a "Role: name (N tasks)" node.

4. **`include_tasks` Dynamic Expansion** — `--list-tasks` does NOT expand `include_tasks`. When JSONL events arrive for unknown tasks, create `TaskDefinition` with `is_dynamic=True`, `task_order=-1`, parented to the `include_tasks` node.

5. **Password Handling** — Compact mode: stop Rich Live, let terminal pass-through handle Ansible's getpass. TUI mode: Textual `Input(password=True)` modal. Both block the worker thread until complete (60s timeout).

6. **Secrets Redaction** — Three layers: (1) honor `_ansible_no_log`, (2) pattern-match field names against Ansible's `PASSWORD_MATCH` regex + known secret field names, (3) configurable whitelist for false positives like `passenger_version`.

## Development Philosophy

### TDD with Strict OODA Loop

ALL development follows a Test-Driven Development cycle with the OODA loop pattern:

```
1. OBSERVE:   Read the spec section and matching TC-XXX test cases
2. ORIENT:    Write the test FIRST — assert expected behavior
3. DECIDE:    Run the test — it MUST fail (red phase)
4. ACT:       Implement the minimum code to make it pass (green phase)
5. ABSTRACT:  Can this logic be abstracted into the core library?
              - If it's pure logic with no I/O → extract to core/
              - If it depends on pexpect/Textual/TTY → keep in infrastructure layer
              - If it's mixed → split into core logic + thin infrastructure wrapper
6. LOOP:      Refactor (clean), then next test case — NEVER skip a cycle
```

**Golden rules:**
- **More tests are better than fewer tests.** When in doubt, ADD another test.
- **Tests are specification.** If the spec says something should happen, there MUST be a test asserting it.
- **Never implement without a failing test first.** Code without a test is code that doesn't exist.
- **Run the full suite after every change.** `uv run pytest tests/ -q` — it should ALWAYS be green before pushing.
- **Coverage gaps are bugs waiting to happen.** Every `if` branch, every exception handler, every edge case needs a test.

### Anti-patterns (NEVER DO):
- Write implementation code first, then "add tests after"
- Skip writing tests because "it's a simple change"
- Accept "the tests pass" without checking coverage of the changed code
- Push when ANY test is failing

### Test Quality Standards:
- Unit tests: isolated, fast, no I/O, no network, mock external deps
- Integration tests: multiple real components, may require ansible-core
- Edge cases: test boundaries, empty inputs, malformed data, race conditions
- Error paths: test every `except` block, every error branch
- Property-based: invariants that must hold regardless of input

### Domain-Driven Development (DDD)

The project uses Domain-Driven Design to keep business logic decoupled from infrastructure:

**Core Domain (ansible_aom/core/):**
- `models.py` — Aggregate roots: `RunState`, `PlayRunState`, `TaskRunState`, `HostRunState`
- `state.py` — State machine (`ExecutionState`, `StateMachine`) as a domain service
- `parser.py` — Domain services for parsing Ansible output formats
- `session.py` — Session aggregate for recording run history
- `redaction.py` — Domain service for secret detection/redaction
- `icons.py` — Value objects for status display representation
- `config.py` — Domain configuration values

**Infrastructure Layer:**
- `renderer/` — Rendering adapters (CompactRenderer, AOMApp) implementing the Renderer Protocol
- `compact/` — ANSI/TTY infrastructure (Rich Live, blessed, pexpect)
- `tui/` — Textual UI infrastructure (screens, widgets, keybindings)
- `inspect/` — Session inspection adapters

**Rule:** Core domain modules must NEVER import from compact/, tui/, or renderer/. Infrastructure can depend on core. This prevents circular coupling and keeps the domain testable in isolation.

**DDD Patterns in Use:**
- **Entities**: `PlayRunState`, `TaskRunState`, `HostRunState` (mutable identity over time)
- **Value Objects**: `Status` enum, `WarningType` enum, `WarningEntry`, role/task definitions
- **Domain Services**: `StateMachine`, `PtyStreamParser`, redaction pipeline
- **Aggregates**: `RunState` (transactional boundary for all play/task/host state)
- **Protocols**: `Renderer` Protocol as a port/adapter boundary
- **Factories**: `create_renderer()` for creating infrastructure implementations

### Library-First Strategy

Every module in `ansible_aom/core/` should be designed as a reusable library, not coupled to the CLI or TUI.

**Before adding ANY feature, ask:**
1. "Does this logic belong in core/ or is it infrastructure-specific?"
2. "Could another Python project import this module and use it?"
3. "Does this function have any implicit dependency on pexpect, Textual, or the TTY?"

**Examples of library-first thinking:**
- ✅ `RunState.handle_event(event)` — pure logic, no I/O, fully testable
- ✅ `parse_list_tasks_output(output: str)` — string in, data out, no side effects
- ✅ `redact_event(event, config)` — pure transformation, no system calls
- ❌ A parser that also calls `print()` — mixed I/O, can't be used as a library
- ❌ State machine that assumes it's running inside Textual — breaks reusability

**The ABSTRACT step is MANDATORY.** After every AODA cycle, the OODA loop must include: "Can this logic be abstracted into our core library?" Code that belongs in core/ but lives in compact/ or tui/ is a design defect.

## Testing Convention

- **TDD by spec**: `TEST_SPECIFICATION.md` defines TC-001 through TC-200+. Write test FIRST, then implement.
- **Categories**: `tests/unit/` (isolated), `tests/integration/` (multi-component), `tests/tui/` (Textual widgets), `tests/compact/` (snapshot tests)
- **Fixtures**: `tests/fixtures/` — JSONL event samples, playbook snippets
- **Unit tests should pass without ansible-core**. Integration tests need it (`ansible-core≥2.16` in `[project.optional-dependencies] integration`).
- Pre-commit hooks: ruff format → ruff check → mypy (pre-commit) → pytest (pre-push only)

## Style Rules

- ruff: line-length 100, Python 3.14, rules E/F/W/I
- mypy: strict for `core/`, relaxed for `tui/` and `compact/` (Textual/Rich metaclass patterns don't type cleanly)
- Never suppress types with `# type: ignore` — use the module-level mypy override in `pyproject.toml` instead
- Test files: `F401`, `F811`, `F841`, `E501` allowed (fixtures often have unused imports and redefinitions)
- Don't add `# type: ignore` comments. Don't use `Any` unless truly unavoidable.

## Common Mistakes to Avoid

- `--list-tasks` has **no JSON mode**. Don't try to parse it as JSON. It's plain text with literal TAB characters (`\t`).
- `--list-tasks` and `--list-hosts` must run **in parallel** at startup. Sequential doubles startup time.
- `include_tasks` ≠ `import_tasks`. `include_tasks` is NOT expanded in `--list-tasks`; `import_tasks` IS.
- All `_timestamp` values are ISO 8601 UTC. Display converts to local timezone, elapsed time is UTC diff.
- Terminal minimum is 24×80. Check and show clear error, don't crash.
- The `task.path` field format in JSONL is `"file.yml:line_number"`.

## Key Files to Know About

| File | Why |
|------|-----|
| `SPECIFICATION.md` | Full technical spec — authoritative on behavior |
| `TEST_SPECIFICATION.md` | Every test case, organized by spec section |
| `TEST_PLAYBOOKS.md` | Test playbook docs and conventions |
| `pyproject.toml` | Dependencies, mypy overrides, pytest config |
| `flake.nix` | Nix dev shell + package build |
| `.pre-commit-config.yaml` | Pre-commit hook pipeline |
