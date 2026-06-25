# aom — Ansible Output Monitor

A `nom`-style live view for `ansible-playbook`. Replaces ansible's stock
log-spew with a compact, persistent status panel that tells you *what's
running right now*, *what's failed*, and *what's still ahead* — without
losing the per-task log above it.

```
PLAY [Deploy webservers] (webservers, 3 hosts, 12 tasks)
PLAY [Deploy database]    (dbservers, 1 host, 4 tasks)
Tags: deploy, install, restart

TASK [Install nginx] ********************************************
ok: [web1]
changed: [web2]
fatal: [web3]: FAILED! => SSH connection failed
                                       ─────────────────────────────────
 site.yml │ 2/3 hosts │ 8/16 tasks │ ⚠ 1 │ 0:00:42 ●
  host  ok  changed  failed  on
  web1   5        3       0  (idle)
  web2   4        4       0  (idle)
  web3   0        0       1  (idle)
  FAILED: web3 — Install nginx
```

Two render modes:

- **Compact** (default) — single status panel pinned to the bottom of
  your terminal; ansible's normal log streams above it. No alternate
  screen, no full takeover. Works in pipes, CI, `tee`, anywhere.
- **TUI** (`--tui`) — full multi-panel Textual UI: task tree, summary,
  log, debug. Best for long playbooks where you want to drill in.

Every run is recorded to `~/.local/state/aom/sessions/<id>/` so
`aom inspect` can replay it later.

## Install

```bash
# Recommended: install as a uv tool, isolated env, on $PATH
uv tool install .

# Or with pipx
pipx install .

# Or for development (editable install in a uv-managed venv)
uv sync --all-extras
uv run pip install -e .
```

Requirements: Python ≥ 3.14, plus a working `ansible-playbook` on your
`$PATH`. AOM never imports `ansible-core`; it shells out and parses the
JSONL callback.

After install, sanity check:

```bash
aom --version
aom --help
```

## Usage

```bash
aom site.yml                          # compact view
aom --tui site.yml                    # full TUI
aom site.yml -i inv.ini --tags deploy # any ansible-playbook flag works
aom site.yml -vvv                     # ansible verbosity flows through
```

Anything after the playbook path is forwarded verbatim to
`ansible-playbook`. AOM never silently rewrites your arguments.

### Inspect past runs

```bash
aom inspect list                      # all recorded sessions, newest first
aom inspect <session-id>              # human summary of one run
aom inspect <session-id> --tree       # ASCII tree of plays/tasks/hosts
aom inspect <session-id> --failed     # only failed tasks
aom inspect <session-id> --host web1  # only events for one host
aom inspect diff <id1> <id2>          # what changed between two runs
aom inspect prune --days 30           # delete sessions older than N days
```

`--json` / `--jsonl` is available on `list` / `show` for piping into
`jq` and friends.

### Flags

| Flag | Effect |
|------|--------|
| `--tui` | Launch the full multi-panel TUI (default is compact). |
| `--verbose` | Print AOM diagnostics (resolved `ansible-playbook` path, env, terminal size), enable DEBUG logging, enable pexpect/event traces, and print post-run `[aom-debug]` summary. Equivalent to `AOM_DEBUG=1`. |
| `--version` | Print version and exit. |
| `--help` | Show built-in help. |

**`-v` is reserved for ansible-playbook.** `aom site.yml -v` raises
ansible verbosity, not AOM verbosity. The AOM debug flag is
`--verbose` (long form only).

## How it works

```
                       ┌──────────────────────┐
ansible-playbook ─────►│ PTY (pexpect)        │
  + ansible.posix.jsonl│                      │
                       └──────────┬───────────┘
                                  ▼
                       ┌──────────────────────┐
                       │ PtyStreamParser      │   3-phase:
                       │  • password prompts  │     PRE_RUN_PROMPTS
                       │  • JSONL events      │     EXECUTION
                       │  • PLAY RECAP        │     POST_RUN_RECAP
                       └──────────┬───────────┘
                                  ▼
                       ┌──────────────────────┐
                       │ RunState             │   pure-Python state
                       │  • plays / tasks     │   no I/O, no Textual
                       │  • dynamic include   │   include_tasks grafted
                       │    expansion         │     under parent at runtime
                       └──────────┬───────────┘
                                  ▼
                  ┌───────────────┴───────────────┐
                  ▼                               ▼
       ┌─────────────────┐             ┌──────────────────┐
       │ CompactRenderer │             │ AOMApp (Textual) │
       │ Rich Live panel │             │ full TUI         │
       └─────────────────┘             └──────────────────┘
                  │
                  ▼
          ~/.local/state/aom/sessions/<uuidv7>/
            ├── events.jsonl     ← every JSONL event the run saw
            ├── stderr.log       ← warnings + preflight errors
            └── meta.json        ← playbook, start/end, status
```

Before the run starts, AOM also fires `--list-tasks` and `--list-hosts`
**in parallel** so the panel shows host count, task count, and the
expected play layout from the very first frame.

## Status icons

| Icon | Meaning | ASCII fallback |
|------|---------|----------------|
| `●` | ok | `*` |
| `◆` | changed | `+` |
| `✖` | failed | `X` |
| `⊝` | unreachable | `!` |
| `○` | skipped | `o` |
| `◐` | running | `@` |
| `□` | pending | `.` |

ASCII fallback kicks in automatically when `LANG` / `LC_*` aren't UTF-8.

## File locations

| What | Where |
|------|-------|
| Session recordings | `~/.local/state/aom/sessions/<uuidv7>/` |
| User config | `~/.config/aom/config.yaml` (optional) |
| Inventory auto-detect | `./inventory.ini`, `./inventory.yml`, `./hosts`, … |

If a conventional inventory file sits in your current directory and
you didn't pass `-i`, AOM prepends `-i <file>` for you. Pass any
inventory flag explicitly and AOM keeps its hands off.

## Project layout

- `src/ansible_aom/` — source. See [`ARCHITECTURE.md`](ARCHITECTURE.md)
  for the module map.
- `SPECIFICATION.md` — authoritative behaviour spec.
- `TEST_SPECIFICATION.md` — every test case, indexed by spec section.
- `CLAUDE.md` — contributor guide: setup, commands, style, TDD rules.

## Development

```bash
uv sync --all-extras
uv run pip install -e .

uv run pytest tests/ -q
uv run ruff format && uv run ruff check --fix
uv run mypy src/ansible_aom
```

TDD-first; tests for `core/` must pass without `ansible-core`. See
[`CLAUDE.md`](CLAUDE.md) for the full rules.

## License

GPL-3.0-or-later. See [`LICENSE`](LICENSE).
