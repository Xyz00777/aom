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

## Project Status

AOM is in active development. APIs, CLI behavior, configuration formats,
session formats, and documentation may change without notice. Test it in a
non-production environment before relying on it for critical automation.

This project uses AI-assisted development: parts of the code, tests,
documentation, and research were developed with assistance from generative AI
tools. Maintainers review and accept changes, but users should independently
verify behavior, security, and licensing.

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

### Replay past runs

```bash
aom replay <session-id>            # replay at original cadence
aom replay <session-id> --speed 10 # 10x faster
aom replay <session-id> --speed 0  # as fast as possible (no sleeps)
aom replay latest                  # replay the most recent session
```

Re-stream a recorded session's `events.jsonl` through the renderer at
the original pacing, scaled with `--speed N`. Replay reproduces only
the JSONL stream, not AOM-emitted warnings, the preflight summary, or
password-prompt log lines. Session IDs may be a full UUID, a unique
prefix, or `latest`.

### Rerun failed hosts

```bash
aom rerun                          # rerun latest session's failed hosts
aom rerun <session-id> --failed    # explicit session, failed hosts only
aom rerun <session-id> --unreachable  # failed + unreachable hosts
aom rerun --changes-only -y        # rerun changed hosts, skip the prompt
```

Reads a recorded session, derives a host set from
failed / unreachable / changed events, and re-invokes
`ansible-playbook` with the original args plus a `--limit` matching
those hosts. By default `aom rerun` behaves like `--failed`; flags
compose by union. A pre-existing `--limit` in the recorded args is
replaced, not intersected, because a rerun to a subset is rarely what
users want. Always prints the planned command line and a warning that
re-running may execute non-idempotent tasks, then prompts for
confirmation unless `-y` is set.

### Shell completion

```bash
aom --install-completion bash >> ~/.bashrc
aom --install-completion zsh >> ~/.zshrc
aom --install-completion fish > ~/.config/fish/completions/aom.fish
```

Prints the rc-file snippet for the chosen shell to stdout, then exits.
Powered by `argcomplete`; tab-completes subcommands (`inspect`,
`replay`, `rerun`), flags, and recorded session IDs from
`~/.local/state/aom/sessions/`.

### Flags

| Flag | Effect |
|------|--------|
| `--tui` | Launch the full multi-panel TUI (default is compact). |
| `--verbose` | Print AOM diagnostics (resolved `ansible-playbook` path, env, terminal size), enable DEBUG logging, enable pexpect/event traces, and print post-run `[aom-debug]` summary. Equivalent to `AOM_DEBUG=1`. |
| `--format {compact,json}` | `compact` (default) streams the nom-style live view. `json` is silent during the run and emits a single JSON object on stdout at completion, designed for CI and `jq` pipelines. Mutually exclusive with `--tui`. |
| `--hide-state <state>` | Suppress per-host lines of the given state from the live compact log. Accepts comma-separated values (e.g. `--hide-state ok,skipped`) or repeated invocations. Choices: `ok`, `changed`, `failed`, `skipped`, `unreachable`. The status panel, recording, and `aom inspect` are unaffected. Ignored under `--tui`. |
| `--no-record` | Disable session recording for this run. No directory is written under `~/.local/state/aom/sessions/`. Debug output from `--verbose` is unaffected. |
| `--install-completion {bash,zsh,fish}` | Print the rc-file snippet for the given shell to stdout, then exit. Pipe to your rc file (e.g. `aom --install-completion bash >> ~/.bashrc`). Powered by `argcomplete`; tab-completes subcommands, flags, and recorded session IDs. |
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
            ├── events.jsonl     ← immutable events, including aom_stderr_line
            ├── meta.json        ← playbook, start/end, status
            ├── diagnostics.json ← derived lifecycle and renderer diagnostics
            └── index.db         ← optional, disposable inspect index
```

`events.jsonl` is the session source of truth. Stderr is stored there as
synthetic `aom_stderr_line` events; `diagnostics.json` and `index.db` are
derived artifacts.

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
| User config | `~/.config/aom/aom_config.yaml` (optional) |
| Inventory auto-detect | `./inventory.ini`, `./inventory.yml`, `./hosts`, … |

If a conventional inventory file sits in your current directory and
you didn't pass `-i`, AOM prepends `-i <file>` for you. Pass any
inventory flag explicitly and AOM keeps its hands off.

Configuration layers are merged in this order: built-in defaults,
`/etc/aom/aom_config.yaml`, `~/.config/aom/aom_config.yaml`,
`./.aom_config.yaml`, an explicit `AOM_CONFIG` or `--config` file, then
supported CLI values. The older `~/.config/aom/config.yaml` is accepted only
as legacy migration input and is preserved as `config.yaml.migrated`.

### Disk usage

Verbose and setup capture bloat sessions in proportion to the host
count. A 200-host run with `--capture-verbose --capture-setup` lands
around `~50MB` of `events.jsonl`. At that rate, 100 sessions stack up
to roughly `5GB` under `~/.local/state/aom/sessions/`.

Reclaim space by pruning old runs:

```bash
aom inspect prune --days 30    # delete sessions older than 30 days
```

The prune command is safe to run on a schedule; it only removes
session directories whose recorded start time is older than the
threshold.

## Project layout

- `src/ansible_aom/` — source. See [`ARCHITECTURE.md`](ARCHITECTURE.md)
  for the module map.
- `SPECIFICATION.md` — authoritative behaviour spec.
- `TEST_SPECIFICATION.md` — every test case, indexed by spec section.
- `AGENTS.md` — contributor guide: setup, commands, style, TDD rules.

## Community

- [Contributing](CONTRIBUTING.md)
- [Security](SECURITY.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Support](SUPPORT.md)

## Development

```bash
uv sync --all-extras
uv run pip install -e .

uv run pytest tests/ -q
uv run ruff format && uv run ruff check --fix
uv run mypy src/ansible_aom
```

TDD-first; tests for `core/` must pass without `ansible-core`. See
[`AGENTS.md`](AGENTS.md) for the full rules.

## License

GPL-3.0-or-later. See [`LICENSE`](LICENSE). AOM is provided as-is, with no warranty.
The repository's reasoning for the GPL treatment of the bundled
callback is documented in [ARCHITECTURE.md section 10.1](ARCHITECTURE.md#101-gpl-subclass-concern-ansiblecallbackaom_jsonlpy).
