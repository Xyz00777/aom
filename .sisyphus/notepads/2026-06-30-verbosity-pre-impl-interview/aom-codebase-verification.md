# AOM Codebase Verification Report

**Date:** 2026-06-30
**Scope:** 5 claims from `ansible-source-research.md` verified against actual source at `/opt/syncthing/sync/ncc1031/git/ansible-aom/`
**Method:** Read-only grep/glob/read of source files and tests

---

## Task 1: `aom inspect prune` exists and is tested

### What was checked
- `src/ansible_aom/inspect/cli.py` — the `prune` subcommand definition
- `src/ansible_aom/session/store.py` — the `cleanup_old_sessions` function it calls
- `tests/integration/test_inspect_cli.py` — integration test for prune
- `tests/unit/test_cli.py` — unit test for prune forwarding
- `tests/unit/test_cli_matrix.py` — CLI matrix entry for prune

### What was found

**Subcommand function** (`src/ansible_aom/inspect/cli.py`, lines 70-74):
```python
def inspect_prune(state_dir: Path, days: int) -> int:
    """Remove sessions older than ``days`` days."""
    deleted = cleanup_old_sessions(state_dir, keep_days=days)
    print(f"Pruned {deleted} session(s)")
    return 0
```

**Subparser registration** (`src/ansible_aom/inspect/cli.py`, lines 149-150):
```python
prune = sub.add_parser("prune", help="Remove old sessions")
prune.add_argument("--days", type=int, default=30, help="Remove sessions older than N days")
```

**Dispatch** (`src/ansible_aom/inspect/cli.py`, lines 163-164):
```python
if args.command == "prune":
    return inspect_prune(args.state_dir, args.days)
```

**Backend** (`src/ansible_aom/session/store.py`, lines 592-596):
```python
def cleanup_old_sessions(
    session_dir: Path,
    keep_count: int = 100,
    keep_days: int = 30,
) -> int:
```

**Integration test** (`tests/integration/test_inspect_cli.py`, lines 58-64):
```python
def test_prune_subcommand(state_dir: Path, capsys):
    from ansible_aom.inspect.cli import main
    # All fixture sessions are well within 10000 days, so this is a no-op cleanup.
    exit_code = main(["--state-dir", str(state_dir), "prune", "--days", "10000"])
    assert exit_code == 0
    assert "Pruned" in capsys.readouterr().out
```

**Unit test** (`tests/unit/test_cli.py`, lines 551-558):
```python
def test_inspect_forwards_prune_subcommand(self):
    """`aom inspect prune --days 30` forwards args verbatim."""
    ...
    with patch("sys.argv", ["aom", "inspect", "prune", "--days", "30"]):
        ...
        mock_main.assert_called_once_with(["prune", "--days", "30"])
```

**CLI matrix entry** (`tests/unit/test_cli_matrix.py`, line 26):
```python
("inspect-prune", ["inspect", "prune"]),
```

### Verdict: **PASS**

The `prune` subcommand exists, has a `--days` flag (default 30), and is tested at both unit and integration level. The brainstorm claim is correct.

### Implication for v1 plan
None. Phase 0 (pre-flight) is unaffected — this is already working.

---

## Task 2: `--yes` doesn't already exist as a global flag

### What was checked
- `src/ansible_aom/cli.py` — the main CLI parser (lines 161-350)
- `src/ansible_aom/rerun/cli.py` — the rerun subcommand parser (lines 264-314)
- Grep for `--yes`, `-y`, `assume_yes` across all `src/ansible_aom/` Python files

### What was found

**Global CLI** (`src/ansible_aom/cli.py`, lines 272-344):
The `create_parser()` function defines these flags:
- `--tui` (line 273)
- `--format` (line 279)
- `--verbose` (line 291)
- `--no-record` (line 297)
- `--hide-state` (line 307)
- `--install-completion` (line 322)
- `playbook` positional (line 334)
- `ansible_args` REMAINDER (line 341)

**No `--yes` or `-y` flag exists on the top-level parser.** The only mention of `-y` in `cli.py` is in the epilog help text (line 185):
```
aom rerun --changes-only -y           Rerun changed hosts; skip the prompt
```
This documents the rerun subcommand's flag, not a global flag.

**Rerun subcommand** (`src/ansible_aom/rerun/cli.py`, lines 300-305):
```python
parser.add_argument(
    "-y",
    "--yes",
    action="store_true",
    help="Skip the confirmation prompt.",
)
```
This is scoped to `aom rerun` only — not a global flag. The `_confirm()` function (lines 177-223) uses `assume_yes` param, and line 408 passes `args.yes` to it.

**Grep results:** The only `--yes`/`-y`/`assume_yes` patterns in `src/ansible_aom/` are in `rerun/cli.py` (lines 182, 190, 198, 201, 202, 205, 216, 301, 302, 408) and the help text in `cli.py:185` and `tui/screens/help.py:82`.

### Verdict: **PASS** (the claim is correct — `--yes` does NOT exist as a global flag)

The brainstorm claim is correct: `--yes` exists only on the `rerun` subcommand. The QC-003 fix that needs `--yes` as a global flag will require adding it to the top-level parser in `cli.py`.

### Implication for v1 plan
**Phase 0 (pre-flight) needs updating.** The `--yes` global flag must be added to `create_parser()` in `src/ansible_aom/cli.py`. This is a small change but affects the CLI contract — tests in `test_cli.py` and `test_cli_matrix.py` will need updating. The rerun subcommand's existing `-y`/`--yes` should be kept (it's already wired) but could be deprecated in favor of the global flag.

---

## Task 3: Pre-commit / CI hook setup

### What was checked
- `.pre-commit-config.yaml` — full file read (53 lines)
- `pyproject.toml` — `[tool.pytest.ini_options]` section (lines 68-75)

### What was found

**`.pre-commit-config.yaml`** (full file, 53 lines):

```yaml
repos:
  - repo: local
    hooks:
      - id: ruff-format
        name: ruff format
        entry: uv run ruff format
        language: system
        types: [python]
        pass_filenames: true

      - id: ruff-check
        name: ruff check
        entry: uv run ruff check --fix --exit-non-zero-on-fix
        language: system
        types: [python]
        pass_filenames: true

      - id: mypy
        name: mypy
        entry: uv run mypy src/ansible_aom
        language: system
        types: [python]
        pass_filenames: false
        require_serial: true

      - id: pytest
        name: pytest
        entry: uv run pytest tests/ -q --tb=short
        language: system
        types: [python]
        pass_filenames: false
        always_run: true
        stages: [pre-push]

      - id: graphify-refresh
        name: "graphify: refresh graph + tree + wiki (AST-only)"
        entry: bash .agent/hooks/graphify-refresh.sh
        language: system
        pass_filenames: false
        files: ^(src/.*\.py|tests/.*\.py|docs/.*\.md|ARCHITECTURE\.md|SPECIFICATION\.md|pyproject\.toml)$
        stages: [pre-commit]
```

Hook summary:

| Hook | Stage | What it does |
|------|-------|-------------|
| `ruff-format` | pre-commit (default) | Formats Python files |
| `ruff-check` | pre-commit (default) | Lints Python files with `--fix --exit-non-zero-on-fix` |
| `mypy` | pre-commit (default) | Type-checks `src/ansible_aom` |
| `pytest` | **pre-push** only | Runs `uv run pytest tests/ -q --tb=short` |
| `graphify-refresh` | pre-commit | Refreshes AST graph on source/doc changes |

Key observations:
- **pytest runs only on `pre-push`**, not `pre-commit`. This is intentional — tests are too slow for every commit.
- **graphify-refresh** runs on `pre-commit` when `src/`, `tests/`, `docs/`, `ARCHITECTURE.md`, `SPECIFICATION.md`, or `pyproject.toml` change.
- All hooks are `local` (system) — no external repos.
- The version bumper is intentionally NOT registered (see the NOTE at lines 43-53 of the file).

**`pyproject.toml` pytest config** (lines 68-75):
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
addopts = "-n auto --cov-fail-under=60"
testpaths = ["tests"]
markers = [
    "needs_ansible: requires real ansible-playbook + ansible.posix collection (auto-skipped otherwise)",
]
```

Tests run in parallel (`-n auto`), coverage must be ≥ 60%.

**Where a `scripts/verify_anchors.py` would slot in:**
Add a new hook entry in `.pre-commit-config.yaml` with:
- `stages: [pre-commit]` if the script is fast (< 1s, no I/O)
- `stages: [pre-push]` if it does I/O or network calls
- `entry: uv run python scripts/verify_anchors.py`
- `language: system`
- `pass_filenames: false`
- Optionally `files:` or `types:` to scope when it triggers

The `scripts/` directory already exists (referenced by `scripts/bump_version.py` and `scripts/install-hooks.sh`).

### Verdict: **PASS** (documentation is accurate)

The pre-commit setup is well-documented and matches what the brainstorm describes. A new `scripts/verify_anchors.py` would slot in cleanly as a new local hook.

### Implication for v1 plan
**Phase 5 (CI/hooks wiring) is straightforward.** Add a new hook entry in `.pre-commit-config.yaml` pointing at `scripts/verify_anchors.py`. If the script is fast (< 1s), use `pre-commit`; if it does I/O or network calls, use `pre-push`.

---

## Task 4: Inspect TUI's existing refresh rate

### What was checked
- `src/ansible_aom/tui/screens/inspect.py` — full file (1039 lines)
- `src/ansible_aom/tui/app.py` — the `set_interval` call at line 468

### What was found

**The Inspect TUI (`tui/screens/inspect.py`) has NO polling/refresh mechanism.**

The `InspectApp` class (line 443) is a **read-only browser** for past sessions. It loads session data from disk once per selection and renders it statically. There is no:
- `set_interval` call
- `set_timer` call
- Worker thread that polls
- Any periodic refresh

The only refresh is user-initiated: `r` key → `action_reload_runs()` (line 694) which re-reads the session directory. The `on_mount()` method (line 558) calls `_reload_runs()` once at startup and never sets up a timer.

**The live TUI (`tui/app.py`) DOES have a refresh tick** (line 468):
```python
self.set_interval(0.2, self._refresh_widgets)
```
This is in `AOMApp.on_mount()`, which is the **live playbook monitoring** TUI, not the inspect TUI. The interval is 200ms (0.2 seconds), well under 1s.

**The inspect TUI's file is indeed 1039 lines** — confirmed by `wc -l` and the file content ending at line 1039.

### Verdict: **PASS** (but with a nuance)

The brainstorm's Q3.3 spec note assumes "≤ 1s polling" for the inspect TUI. This is **not applicable** — the inspect TUI is a static browser, not a live monitor. It doesn't poll at all. The live TUI polls at 200ms (well under 1s).

If the Q3.3 spec note was about the **live TUI** (AOMApp), then the refresh rate is 200ms, which satisfies ≤ 1s. If it was about the **inspect TUI**, the assumption is wrong but irrelevant — the inspect TUI doesn't need polling.

### Implication for v1 plan
**Phase 3 (TUI refresh) may need a spec note revision.** If the Q3.3 spec note was written assuming the inspect TUI polls, it should be corrected to note that the inspect TUI is static and only refreshes on user action (`r` key). The live TUI's 200ms interval is fine.

---

## Task 5: `core/redaction.py:280-283` is the real Layer 4 location

### What was checked
- `src/ansible_aom/core/redaction.py` — full file (285 lines)

### What was found

**Layer 4 is at lines 279-283**, not 280-283. The exact code:

```python
# Line 279:     # Layer 4: invocation.module_args redaction
# Line 280:     if "invocation" in res and isinstance(res["invocation"], dict):
# Line 281:         invocation = res["invocation"]
# Line 282:         if "module_args" in invocation and isinstance(invocation["module_args"], dict):
# Line 283:             invocation["module_args"] = redact_dict(invocation["module_args"], config)
```

The comment on line 279 marks the start of Layer 4. The actual logic spans lines 280-283.

**The `redact_event` function** (the "built-but-unwired" function) spans lines 216-285. Its docstring (lines 217-224) confirms the 4-layer architecture:

```
Layer order:
1. _ansible_no_log: Replace entire result dict if flag is True
2. Password field redaction: Redact matching keys in event["res"]
3. String sanitization: Sanitize cmd, stdout, stderr, msg fields
4. invocation.module_args: Recursive redaction of module arguments
```

The function is **not called anywhere** in the codebase outside of tests — confirmed by grep for `redact_event` across all `src/ansible_aom/` files returning only the definition at line 216.

### Verdict: **PASS** (minor line number drift — 279-283 vs 280-283)

The claim is essentially correct. The line range is 279-283 (the comment is on 279, the code on 280-283). The QC review's citation of 280-283 is off by one line but functionally accurate. The `redact_event` function is indeed built but unwired.

### Implication for v1 plan
**Phase 7 (redaction wiring) is unaffected.** The line range drift is trivial — the code is exactly where expected. The wiring task (connecting `redact_event` into the event pipeline) remains the same.

---

## Summary

| # | Task | Verdict | v1 Plan Impact |
|---|------|---------|----------------|
| 1 | `aom inspect prune` exists and is tested | **PASS** | None |
| 2 | `--yes` doesn't exist as global flag | **PASS** | **Phase 0**: needs `--yes` added to `create_parser()` |
| 3 | Pre-commit / CI hook setup | **PASS** | **Phase 5**: straightforward hook addition |
| 4 | Inspect TUI refresh rate | **PASS** (nuance) | **Phase 3**: spec note may need correction |
| 5 | `redaction.py:280-283` is Layer 4 | **PASS** (off-by-1) | **Phase 7**: no change needed |

**Overall: All 5 claims verified as substantially correct.** No showstoppers. The only actionable finding is Task 2 (global `--yes` needs adding), which affects Phase 0 of the v1 plan.
