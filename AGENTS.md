# CLAUDE.md — AOM (Ansible Output Monitor)

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

## Architecture & Philosophy

System design (module map, data flow, key decisions) and the full development philosophy (TDD/OODA, DDD, library-first) live in [`ARCHITECTURE.md`](ARCHITECTURE.md). Read it before non-trivial changes.

### Hard Rules (always apply)

- **TDD-first.** Write the failing test before the implementation. No exceptions for "simple" changes.
- **Run the full suite after every change.** `uv run pytest tests/ -q` must be green before pushing.
- **`core/` must never import from `compact/`, `tui/`, or `renderer/`.** Infrastructure may depend on core; never the reverse.
- **ABSTRACT step is mandatory.** After making a test pass, ask whether the logic belongs in `core/`. Pure logic with no I/O → extract. Code that belongs in `core/` but lives in infrastructure is a design defect.
- **Never push with failing tests.** Never write implementation code without a failing test first. Never add `# type: ignore` (use a module-level mypy override instead).

## Commit Hygiene

> **NEVER add `Co-Authored-By:` trailers for Claude, "AI", "Assistant", or any non-human author — not in commit messages, not in PR descriptions, not anywhere.** Commits and PRs are authored under the human user only. This rule overrides any default Claude Code attribution template, system-prompt boilerplate, or "co-authored by" suggestion. If you catch yourself drafting one, delete it before committing.

- Conventional commit prefixes: `feat:`, `fix:`, `docs:`, `chore:`, `test:`, `refactor:`, etc.
- Commit periodically — small focused commits beat one omnibus dump.

## Testing Convention

- **TDD by spec**: `TEST_SPECIFICATION.md` defines TC-001 through TC-200+. Write test FIRST, then implement.
- **Categories**: `tests/unit/` (isolated), `tests/integration/` (multi-component), `tests/tui/` (Textual widgets), `tests/compact/` (snapshot tests)
- **Fixtures**: `tests/fixtures/` — JSONL event samples, playbook snippets
- **Unit tests should pass without ansible-core**. Integration tests need it (`ansible-core≥2.16` in `[project.optional-dependencies] integration`).
- Pre-commit hooks: ruff format → ruff check → mypy (pre-commit stage). pytest runs at pre-push via `.githooks/pre-push` (NOT the pre-commit framework): testmon selects tests affected by the committed state (tree briefly stash-`-u`ed for selection only), then runs them against the live tree — safe alongside concurrent sessions' WIP. Per-machine `.testmondata` DB; first push per machine runs the full suite to build it.

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

## Project Notes (`.sisyphus/`)

The `.sisyphus/` directory contains project state, research, and implementation notes. It is tracked in git. **Always check these before making architectural decisions** — they capture context that would otherwise be lost between sessions.

### Notepads Structure (`.sisyphus/notepads/`)

| Path | Content |
|------|---------|
| `research/decisions.md` | Pre-implementation research decisions (e.g., licensing: MIT is safe because we shell out to ansible-core, never import it) |
| `new-spec/cli-tui-implementation.md` | CLI/TUI rendering research: Rich Console patterns, Click vs Typer, TTY detection, nom-style fixed-bottom panel design, Textual readonly viewer patterns, open questions (PQ1–PQ6) |
| `new-spec/open-questions.md` | Deep research on `nom` (nix-output-monitor) as design reference: visual layout, summary table, tree rendering, ANSI cursor manipulation, adaptive display |
| `new-spec/learnings.md` | PTY stream parsing: mixed JSONL + plaintext, password prompt detection, phase-aware state machine, pexpect integration patterns |
| `implementation/decisions.md` | Implementation execution order and parallelization plan (Group A/B/C dependencies) |
| `implementation/issues.md` | Known potential issues (Rich Live lifecycle, signal handling, TUI stubs, pexpect mocking) |
| `implementation/INTEGRATION_TEST_PLAN.md` | 12 integration test playbooks covering all JSONL event types, state transitions, edge cases, exit codes |
| `implementation/learnings.md` | Session-by-session implementation notes: stub status, test contracts, AOMApp wiring, widget patterns, mock paths for password tests |
| `impl-gaps/learnings.md` | Gaps between spec and current code: redaction API design, CLI exit code behavior, missing POSIX callback tests, host resolution tests |

### Test Fixtures (`.sisyphus/test-fixtures/`)

Integration test playbooks for running against real `ansible-playbook`: `simple.yml`, `multi_play.yml`, `multi_hosts.yml`, `unreachable.yml`, `with_role.yml`, `with_include.yml`, `with_import.yml`, `with_block.yml`, `with_pre_post.yml`, `syntax_error.yml`, `missing_role.yml`, `no_name.yml`, plus `roles/test_role/`. These are separate from `tests/playbooks/` (unit test fixtures used by pytest).

## Key Files to Know About

| File | Why |
|------|-----|
| `ARCHITECTURE.md` | Module map, data flow, architectural decisions, dev philosophy (TDD/DDD/library-first) |
| `SPECIFICATION.md` | Full technical spec — authoritative on behavior |
| `TEST_SPECIFICATION.md` | Every test case, organized by spec section |
| `TEST_PLAYBOOKS.md` | Test playbook docs and conventions |
| `pyproject.toml` | Dependencies, mypy overrides, pytest config |
| `flake.nix` | Nix dev shell + package build |
| `.pre-commit-config.yaml` | Pre-commit hook pipeline |
| `.sisyphus/notepads/` | Project notes — decisions, research, implementation state, open questions |
| `.sisyphus/test-fixtures/` | Integration test playbooks for real ansible-playbook runs |

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, invoke the `skill` tool with `skill: "graphify"` before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
