# Implementation Learnings

## Redaction Module (src/ansible_aom/core/redaction.py)

### API to implement:
```python
# Constants
PASSWORD_MATCH = re.compile(r'^(?:.+[-_\s])?pass(?:[-_\s]?(?:word|phrase|wrd|wd))?(?:[-_\s].+)?$', re.IGNORECASE)
ANSIBLE_PASSWORD_FIELDS = frozenset({...})
GENERIC_SECRET_FIELDS = frozenset({...})
PASSWORD_WHITELIST = frozenset({"passenger_version", "passenger_pool", "bypass", "overpass", "compass", "underpass", "passport_number"})
URL_CRED_PATTERN = re.compile(r'([a-zA-Z]+://[^:]+:)([^@]+)(@)')
CLI_CRED_PATTERN = re.compile(r'(--(?:password|pass|pwd|token|secret|key|api-key)\s*[=: ]+)\S+', re.IGNORECASE)
REDACTED = '********'
MAX_DEPTH = 10

# Functions
def redact_event(event: dict, config: RedactionConfig) -> dict
def redact_dict(data: dict, config: RedactionConfig, depth: int = 0) -> dict
def sanitize_string(s: str, config: RedactionConfig) -> str
def should_redact(key: str, config: RedactionConfig) -> bool
```

### Layer Rules:
1. **Layer 1**: If `_ansible_no_log=True` is in a result dict (even nested in lists), replace that ENTIRE result with `{'censored': '(no_log)'}`.
2. **Layer 2**: For all result dict keys (except whitelisted), match `PASSWORD_MATCH` regex, `ANSIBLE_PASSWORD_FIELDS`, `GENERIC_SECRET_FIELDS`, or `config.custom_fields` → value replaced with `REDACTED`.
3. **Layer 3**: For specific string fields (`cmd`, `stdout`, `stderr`, `msg`), apply `URL_CRED_PATTERN` and `CLI_CRED_PATTERN` substitutions, plus `config.custom_patterns`.
4. **Layer 4**: If event has `res.invocation.module_args`, recursively redact with same logic (max depth 10).

## CLI Exit Code Tests (test_cli.py TC-027/TC-028)

Current tests are trivial constants. Need to mock actual behavior:
- TC-027: Mock subprocess execution to raise FileNotFoundError, verify `main()` returns 127
- TC-028: Mock signal handling or KeyboardInterrupt during main, verify `main()` returns 130

The `main()` currently handles inspect and playbook. For playbook, it calls `create_renderer()` → `print(...)`. Need to ensure `main()` properly handles `FileNotFoundError` for ansible-playbook → 127.
Since main() currently doesn't spawn ansible-playbook yet (returns 0 after print), the tests should test the DESIRED behavior defined in spec. The current code may need minor modifications to handle `FileNotFoundError` gracefully.

## Missing POSIX Callback Tests (TC-067 to TC-071)

These check:
- ansible.posix availability (via ansible-galaxy collection list or importlib)
- Install prompt
- ansible-core version >= 2.14
- ansible.posix version >= 1.5.0
- ANSIBLE_STDOUT_CALLBACK env var set

## Missing Host Resolution Tests (TC-149 to TC-152)

- resolved_hosts population
- Host cross-check warning
- Fallback after --list-hosts failure
- v2_playbook_on_stats cross-check

## TC-027 & TC-028: CLI Exit Codes for FileNotFoundError and KeyboardInterrupt (2026-04-23)

**Pattern**: Exception handling order matters in Python - specific exceptions must come before generic `Exception` handler.

**Implementation**:
- Added `FileNotFoundError` handler → return 127
- Added `KeyboardInterrupt` handler → return 130  
- Placed **before** the existing `NotImplementedError` and `Exception` handlers

**Test Pattern** for mocking exceptions in CLI:
```python
with patch("ansible_aom.renderer.factory.create_renderer") as mock_renderer:
    mock_renderer.side_effect = FileNotFoundError("ansible-playbook")
    with patch("sys.argv", ["aom", "playbook.yml"]):
        result = main()
        assert result == 127
```

**Key insight**: The `patch` path must match where the function is imported/used, not where it's defined. Since `cli.py` does `from ansible_aom.renderer.factory import create_renderer`, we patch `ansible_aom.renderer.factory.create_renderer`.

## Host Status Display (resolved)

### Skipped status was missing from host overview (resolved 2026-05)

The host overview (`format_host_rows`) and host summary (`format_host_summary`) only showed ok/changed/failed/unreachable. `Status.SKIPPED` was tracked in `RunState` and `tree.py` but never surfaced in the display.

**Fix**: Added `skipped` parameter to `_format_count_cells`, `format_host_summary`, and conditional `skipped` column to `format_host_rows` (hidden when no host has skipped tasks, mirroring the `unreachable` column pattern). The `v2_runner_on_skipped` handler already created `HostRunState(status=Status.SKIPPED)` correctly.

### Per-host summary lines were duplicating the host table (resolved 2026-05)

After completion, the renderer printed both a column-aligned host table (`format_host_rows`) AND per-host summary lines (`format_host_summary`) with the same data. The summary lines were pure duplication.

**Fix**: Removed `_format_per_host_lines` method entirely. On completion, the host table now always prints (not just on failure). The tree snapshot only prints on failure/cancel — on success, stale running spinners would be misleading. `_capture_panel_snapshot` now returns `(tree_lines, host_lines)` tuple so callers can print them independently.

### Host leaves only showed RUNNING hosts (resolved 2026-05)

Tree host leaves under a running task only showed hosts with `Status.RUNNING`. This meant completed hosts disappeared from the tree before the task was done.

**Fix**: Removed the `if hs.status != Status.RUNNING: continue` filter in `_emit_runtime_play`. All hosts under a running task now appear with status-specific icons (● OK, ◐ RUNNING, ○ SKIPPED, etc.).

### Linear strategy tasks stayed RUNNING until playbook end (resolved 2026-05)

Under linear strategy, `task.status` only transitioned to COMPLETED at `v2_playbook_on_stats`. Previous tasks showed as "running" long after they finished.

**Fix**: In `_handle_v2_playbook_on_task_start`, when a new task starts under linear strategy, mark all other RUNNING tasks in the same play as COMPLETED (either all hosts terminal, or empty hosts meaning no runner events arrived). The `_classify` method respects `Status.COMPLETED` as an early exit returning "completed" so the tree prunes them immediately.

### Hostname fallback showed all hosts from all plays (resolved 2026-05)

The tree fallback `_all_known_hostnames` collected hostnames from every
task across every play when `runtime.hosts` was empty. On multi-play
playbooks, play 2 would show host leaves from play 1 (plus `localhost`
from test playbooks).

**Fix**: Replaced with `_play_target_hostnames(play, play_def)` that uses
`play_def.resolved_hosts` (preflight targets) when available, falling
back to the play's own runtime task hostnames. Call site already had both
`play` (PlayRunState) and `play_def` (PlayDefinition) in scope.

### Elapsed time stuck at 0s for fallback host leaves (resolved 2026-05)

Fallback host leaves (when `runtime.hosts` is empty) hardcoded
`elapsed_s=0.0` with `Status.RUNNING`. The elapsed counter never
advanced from zero, even for tasks that had been running for minutes.

**Fix**: Compute elapsed from `runtime.start_time` instead of hardcoding
0. When `start_time` is None (task hasn't started yet), 0 is correct.

### Dynamic children not shown as pending in tree (resolved 2026-05-23)

Grafted `include_tasks` children (in `TaskDefinition.children`) appeared only in role task counts, not as visual □ pending entries in the tree. Users couldn't see what dynamic tasks were coming.

**Fix**: Added a new loop in `_play_running_and_pending` after the runtime-only tasks loop. Iterates `play_def.tasks` for entries with `.children`, emitting each child as either "running" (if announced at runtime with a matching `TaskRunState`) or "pending" (if not yet seen). Completed children are filtered. Duplicates prevented via `emitted_names` — the runtime-only loop now also adds to `emitted_names` so dynamic children already picked up there don't re-appear.

**Tests added**: TC-320 (pending before announcement), TC-321 (running status), TC-322 (completed filtered), TC-323 (under role header), TC-324 (host leaves), + duplicate-prevention test.
