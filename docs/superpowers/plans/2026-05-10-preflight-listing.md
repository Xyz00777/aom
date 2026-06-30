# Pre-Flight `--list-tasks` / `--list-hosts` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run `ansible-playbook --list-tasks` and `--list-hosts` in parallel before the JSONL run so AOM knows the playbook's plays, tasks, and resolved hosts before any event arrives.

**Architecture:** A pure assembler in `core/preflight.py` converts raw `parse_list_tasks_output` / `parse_list_hosts_output` results into `list[PlayDefinition]` (with `TaskDefinition` children + role grouping). A thin subprocess runner in the same module spawns both commands in parallel via `concurrent.futures.ThreadPoolExecutor` (the I/O is short and bounded — threads avoid pulling asyncio in). `runner.run_playbook` calls preflight before `pexpect.spawn`; the result is pushed to the renderer through a new `Renderer.set_definitions(definitions)` Protocol method. Failures are non-fatal: an empty/partial definition list plus a warning, so the existing JSONL-driven incremental population still works.

**Tech Stack:** Python 3.14 stdlib (`subprocess`, `concurrent.futures.ThreadPoolExecutor`), existing parsers in `core/parser.py`, existing `PlayDefinition` / `TaskDefinition` / `group_roles` in `core/models.py`.

---

## File Structure

**Create:**
- `src/ansible_aom/core/preflight.py` — pure-domain assembler + subprocess runner. Pure logic at the top of the file (no I/O), I/O wrapper at the bottom that calls subprocess.
- `tests/unit/test_preflight.py` — TDD tests for the assembler (pure, no subprocess).
- `tests/integration/test_preflight_runner.py` — TDD tests for the subprocess wrapper using a fake `ansible-playbook` (same pattern as `tests/integration/test_runner.py`).

**Modify:**
- `src/ansible_aom/core/models.py` — extend `PreParseResult` to carry assembled `definitions` and an `errors` field. (Currently `PreParseResult` lives in `core/parser.py` lines 274–279; we'll move it to `models.py` since it's now a domain aggregate, leaving a re-export shim only if existing imports break — verify by grep.)
- `src/ansible_aom/renderer/protocol.py` — add `set_definitions(definitions: list[PlayDefinition]) -> None` as a required method (Protocol).
- `src/ansible_aom/compact/renderer.py` — implement `set_definitions`: store definitions, recompute initial `hosts_total` from `resolved_hosts`, print a "playbook: X.yml" preamble line.
- `src/ansible_aom/tui/app.py` — implement `set_definitions` as a no-op for now (TUI already builds tree from RunState; preflight wiring there is a separate slice).
- `src/ansible_aom/runner.py` — call `run_preflight()` between `renderer.start()` and `pexpect.spawn()`; forward `result.definitions` to `renderer.set_definitions()`; forward each `result.errors` entry through `renderer.add_warning()`.

**Test fixtures:** Use existing `list_tasks_output` / `list_hosts_output` fixtures in `tests/conftest.py` for the assembler. For the subprocess wrapper, build a fake `ansible-playbook` shim (Python `-c`) that emits canned outputs based on flags — same trick `tests/integration/test_runner.py` uses.

---

## Task 1: PreParseResult shape — extend with `definitions` and `errors`

**Files:**
- Modify: `src/ansible_aom/core/parser.py:274-279` (existing `PreParseResult`)
- Test: `tests/unit/test_preflight.py` (new file)

The current `PreParseResult` only holds raw parsed dicts. Pre-flight needs to surface assembled `PlayDefinition` objects and any subprocess errors. We extend in place rather than creating a parallel type.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_preflight.py
"""Tests for the pre-flight orchestrator (--list-tasks + --list-hosts)."""

from ansible_aom.core.parser import PreParseResult


def test_preparseresult_has_definitions_and_errors_fields():
    """PreParseResult exposes assembled definitions plus an errors list."""
    result = PreParseResult(plays=[], play_hosts=[], definitions=[], errors=[])
    assert result.definitions == []
    assert result.errors == []


def test_preparseresult_definitions_and_errors_default_to_empty():
    """The new fields are optional with empty defaults so old call sites still work."""
    result = PreParseResult(plays=[], play_hosts=[])
    assert result.definitions == []
    assert result.errors == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_preflight.py -v`
Expected: FAIL — `PreParseResult.__init__()` rejects `definitions` / `errors` kwargs.

- [ ] **Step 3: Extend `PreParseResult`**

In `src/ansible_aom/core/parser.py`, replace the existing `PreParseResult` (around line 274) with:

```python
from ansible_aom.core.models import PlayDefinition  # add to existing imports if not present


@dataclass
class PreParseResult:
    """Result from pre-parse phase (--list-tasks + --list-hosts)."""

    plays: list[dict]
    play_hosts: list[dict]
    definitions: list[PlayDefinition] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
```

If `PlayDefinition` import would create a cycle (parser.py → models.py is currently fine; double-check), keep the import at the bottom of the parser imports block. The existing `from dataclasses import dataclass, field` import at the top of `parser.py` is already in place — verify before adding `field`.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_preflight.py -v`
Expected: PASS — both tests green.

- [ ] **Step 5: Run the full suite**

Run: `uv run pytest tests/ -q`
Expected: 1594 → 1596 passing, 0 failing, 6 skipped. No regressions.

- [ ] **Step 6: Commit**

```bash
git add src/ansible_aom/core/parser.py tests/unit/test_preflight.py
git commit -m "feat(core): extend PreParseResult with definitions and errors"
```

---

## Task 2: Pure assembler — turn parsed dicts into `PlayDefinition` objects

**Files:**
- Create: `src/ansible_aom/core/preflight.py`
- Test: `tests/unit/test_preflight.py` (extend existing file)

Domain rule (per ARCHITECTURE.md): pure logic with no I/O lives in `core/`. The mapping from raw parsed dicts to `PlayDefinition`/`TaskDefinition` is pure — exactly the kind of thing that belongs in core.

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/test_preflight.py`:

```python
def test_assemble_definitions_combines_tasks_and_hosts(
    list_tasks_output: str, list_hosts_output: str
):
    """assemble_definitions builds a PlayDefinition per play with tasks + resolved_hosts."""
    from ansible_aom.core.parser import parse_list_hosts_output, parse_list_tasks_output
    from ansible_aom.core.preflight import assemble_definitions

    plays = parse_list_tasks_output(list_tasks_output)
    play_hosts = parse_list_hosts_output(list_hosts_output)

    defs = assemble_definitions(plays=plays, play_hosts=play_hosts)

    assert len(defs) == 2

    # Play #1 — webservers
    play1 = defs[0]
    assert play1.name == "Setup web servers"
    assert play1.id == "1"
    assert play1.hosts == "webservers"
    assert play1.resolved_hosts == ["web1.example.com", "web2.example.com"]
    assert len(play1.tasks) == 3
    assert play1.tasks[0].name == "install nginx"
    assert play1.tasks[0].play_order == 1
    assert play1.tasks[0].task_order == 0
    assert play1.tasks[0].tags == ["web"]
    assert play1.tasks[2].name == "deploy site"
    assert play1.tasks[2].tags == ["deploy"]

    # Play #2 — dbservers
    play2 = defs[1]
    assert play2.name == "Setup database"
    assert play2.resolved_hosts == ["db1.example.com"]
    assert len(play2.tasks) == 2


def test_assemble_definitions_empty_inputs_returns_empty_list():
    from ansible_aom.core.preflight import assemble_definitions

    assert assemble_definitions(plays=[], play_hosts=[]) == []


def test_assemble_definitions_missing_host_data_yields_empty_resolved_hosts():
    """When --list-hosts has no entry for a play, resolved_hosts stays empty."""
    from ansible_aom.core.preflight import assemble_definitions

    plays = [{"play_number": 1, "name": "Solo", "tasks": []}]
    defs = assemble_definitions(plays=plays, play_hosts=[])

    assert len(defs) == 1
    assert defs[0].resolved_hosts == []


def test_assemble_definitions_invokes_role_grouping():
    """5+ consecutive same-role tasks collapse into a RoleGroupDefinition."""
    from ansible_aom.core.models import RoleGroupDefinition
    from ansible_aom.core.preflight import assemble_definitions

    plays = [
        {
            "play_number": 1,
            "name": "Bulk role",
            "tasks": [
                {"name": f"step {i}", "role": "bigrole", "tags": []} for i in range(6)
            ],
        }
    ]
    defs = assemble_definitions(plays=plays, play_hosts=[])

    assert len(defs[0].tasks) == 1
    grouped = defs[0].tasks[0]
    assert isinstance(grouped, RoleGroupDefinition)
    assert grouped.role == "bigrole"
    assert len(grouped.tasks) == 6
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_preflight.py -v`
Expected: FAIL — `ansible_aom.core.preflight` module does not exist.

- [ ] **Step 3: Implement `assemble_definitions`**

Create `src/ansible_aom/core/preflight.py`:

```python
"""Pre-flight: parallel `--list-tasks` + `--list-hosts` orchestration.

This module has two responsibilities, split by purity:

1. **Pure** — `assemble_definitions()` converts raw parsed output dicts
   (from `core.parser.parse_list_tasks_output` / `parse_list_hosts_output`)
   into a `list[PlayDefinition]` with `TaskDefinition` children, applies
   role grouping, and stitches in resolved hosts. No I/O. Lives in core
   because the mapping is domain logic.

2. **Infrastructure** — `run_preflight()` spawns the two ansible-playbook
   subprocesses in parallel and feeds their stdout to the parsers. This
   is the only I/O in the module; tests cover it with a fake executable.
"""

from __future__ import annotations

import subprocess
from concurrent.futures import ThreadPoolExecutor

from ansible_aom.core.models import PlayDefinition, TaskDefinition
from ansible_aom.core.parser import (
    PreParseResult,
    group_roles,
    parse_list_hosts_output,
    parse_list_tasks_output,
)

_PREFLIGHT_TIMEOUT_S = 30.0


def assemble_definitions(
    *, plays: list[dict], play_hosts: list[dict]
) -> list[PlayDefinition]:
    """Build PlayDefinition objects from parsed --list-tasks / --list-hosts dicts.

    Args:
        plays: Output of `parse_list_tasks_output()`.
        play_hosts: Output of `parse_list_hosts_output()`.

    Returns:
        One `PlayDefinition` per play, with `tasks` populated (post-role-grouping)
        and `resolved_hosts` filled from the matching `play_hosts` entry (matched
        by `play_number`). Plays with no matching host entry get an empty
        `resolved_hosts`.
    """
    hosts_by_play_number: dict[int, dict] = {p["play_number"]: p for p in play_hosts}
    result: list[PlayDefinition] = []

    for play in plays:
        play_number: int = play["play_number"]
        host_entry = hosts_by_play_number.get(play_number, {})
        resolved_hosts = list(host_entry.get("hosts", []))
        hosts_pattern_parts = host_entry.get("hosts_pattern", [])
        hosts_pattern = ",".join(hosts_pattern_parts) if hosts_pattern_parts else ""

        play_id = str(play_number)
        task_defs: list[TaskDefinition] = []
        for task_idx, task in enumerate(play["tasks"]):
            task_defs.append(
                TaskDefinition(
                    name=task["name"],
                    role=task.get("role"),
                    tags=list(task.get("tags", [])),
                    play_id=play_id,
                    play_order=play_number,
                    task_order=task_idx,
                )
            )

        grouped = group_roles(task_defs)

        result.append(
            PlayDefinition(
                id=play_id,
                name=play["name"],
                hosts=hosts_pattern,
                resolved_hosts=resolved_hosts,
                tasks=grouped,
            )
        )

    return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_preflight.py -v`
Expected: PASS — all four assembler tests green.

- [ ] **Step 5: Run the full suite**

Run: `uv run pytest tests/ -q`
Expected: 1600 passing, 0 failing, 6 skipped. No regressions.

- [ ] **Step 6: Commit**

```bash
git add src/ansible_aom/core/preflight.py tests/unit/test_preflight.py
git commit -m "feat(core): add assemble_definitions for preflight result"
```

---

## Task 3: Subprocess wrapper — run both commands in parallel

**Files:**
- Modify: `src/ansible_aom/core/preflight.py` (add `run_preflight`)
- Test: `tests/integration/test_preflight_runner.py` (new file)

The wrapper runs `ansible-playbook --list-tasks <playbook> [args]` and `ansible-playbook --list-hosts <playbook> [args]` concurrently. Each gets a 30s timeout. Both stdout streams flow to the corresponding parser. Errors (non-zero exit, timeout, FileNotFoundError) become entries in `result.errors` rather than exceptions — pre-flight is best-effort and must never block the actual run.

- [ ] **Step 1: Write the failing test**

Create `tests/integration/test_preflight_runner.py`:

```python
"""Integration tests for run_preflight against a fake ansible-playbook."""

from __future__ import annotations

import shlex
import sys
import textwrap
from pathlib import Path

import pytest


def _make_fake_ansible(
    tmp_path: Path,
    *,
    list_tasks_stdout: str = "",
    list_hosts_stdout: str = "",
    list_tasks_exit: int = 0,
    list_hosts_exit: int = 0,
) -> Path:
    """Create a Python script that mimics ansible-playbook --list-tasks/--list-hosts."""
    script = tmp_path / "ansible-playbook"
    body = textwrap.dedent(
        f"""
        #!{sys.executable}
        import sys

        args = sys.argv[1:]
        if "--list-tasks" in args:
            sys.stdout.write({list_tasks_stdout!r})
            sys.exit({list_tasks_exit})
        elif "--list-hosts" in args:
            sys.stdout.write({list_hosts_stdout!r})
            sys.exit({list_hosts_exit})
        else:
            sys.exit(2)
        """
    ).lstrip()
    script.write_text(body)
    script.chmod(0o755)
    return script


def test_run_preflight_runs_both_commands_and_assembles_definitions(
    tmp_path: Path, list_tasks_output: str, list_hosts_output: str
) -> None:
    from ansible_aom.core.preflight import run_preflight

    fake = _make_fake_ansible(
        tmp_path,
        list_tasks_stdout=list_tasks_output,
        list_hosts_stdout=list_hosts_output,
    )

    result = run_preflight(
        playbook="site.yml",
        ansible_args=[],
        executable=str(fake),
    )

    assert result.errors == []
    assert len(result.plays) == 2
    assert len(result.play_hosts) == 2
    assert len(result.definitions) == 2
    assert result.definitions[0].resolved_hosts == ["web1.example.com", "web2.example.com"]


def test_run_preflight_executable_not_found_records_error(tmp_path: Path) -> None:
    from ansible_aom.core.preflight import run_preflight

    result = run_preflight(
        playbook="site.yml",
        ansible_args=[],
        executable=str(tmp_path / "does-not-exist"),
    )

    assert result.definitions == []
    assert result.plays == []
    assert any("not found" in err.lower() or "no such" in err.lower() for err in result.errors)


def test_run_preflight_list_hosts_failure_yields_definitions_without_resolved_hosts(
    tmp_path: Path, list_tasks_output: str
) -> None:
    from ansible_aom.core.preflight import run_preflight

    fake = _make_fake_ansible(
        tmp_path,
        list_tasks_stdout=list_tasks_output,
        list_hosts_stdout="",
        list_hosts_exit=1,
    )

    result = run_preflight(
        playbook="site.yml",
        ansible_args=[],
        executable=str(fake),
    )

    # --list-tasks succeeded so we still get plays and definitions
    assert len(result.plays) == 2
    assert len(result.definitions) == 2
    # ...but resolved_hosts is empty because --list-hosts failed
    assert result.definitions[0].resolved_hosts == []
    # error surfaced
    assert any("--list-hosts" in err for err in result.errors)


def test_run_preflight_passes_ansible_args(tmp_path: Path) -> None:
    """Args like -i inventory.ini must reach both subprocess invocations."""
    from ansible_aom.core.preflight import run_preflight

    log = tmp_path / "args.log"
    script = tmp_path / "ansible-playbook"
    body = (
        f"#!{sys.executable}\n"
        "import sys\n"
        f"open({str(log)!r}, 'a').write(' '.join(sys.argv[1:]) + chr(10))\n"
        "sys.exit(0)\n"
    )
    script.write_text(body)
    script.chmod(0o755)

    run_preflight(
        playbook="site.yml",
        ansible_args=["-i", "inv.ini", "-c", "local"],
        executable=str(script),
    )

    lines = log.read_text().splitlines()
    assert len(lines) == 2
    for line in lines:
        parts = shlex.split(line)
        assert "site.yml" in parts
        assert "-i" in parts and "inv.ini" in parts
        assert "-c" in parts and "local" in parts
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/integration/test_preflight_runner.py -v`
Expected: FAIL — `run_preflight` does not exist in `ansible_aom.core.preflight`.

- [ ] **Step 3: Implement `run_preflight`**

Append to `src/ansible_aom/core/preflight.py`:

```python
def _spawn_one(
    executable: str, mode_flag: str, playbook: str, ansible_args: list[str]
) -> tuple[int, str, str]:
    """Spawn a single `ansible-playbook` invocation; return (exit_code, stdout, stderr).

    Mode-flag is `--list-tasks` or `--list-hosts`. Errors (FileNotFoundError,
    PermissionError, OSError, TimeoutExpired) are caught and surfaced as a
    non-zero exit with a synthetic stderr — preflight is best-effort.
    """
    try:
        completed = subprocess.run(
            [executable, mode_flag, playbook, *ansible_args],
            capture_output=True,
            text=True,
            timeout=_PREFLIGHT_TIMEOUT_S,
            check=False,
        )
        return completed.returncode, completed.stdout, completed.stderr
    except FileNotFoundError as exc:
        return 127, "", f"executable not found: {exc}"
    except PermissionError as exc:
        return 126, "", f"executable not executable: {exc}"
    except subprocess.TimeoutExpired:
        return 124, "", f"{mode_flag} timed out after {_PREFLIGHT_TIMEOUT_S}s"
    except OSError as exc:
        return 1, "", f"{mode_flag} failed: {exc}"


def run_preflight(
    *,
    playbook: str,
    ansible_args: list[str],
    executable: str = "ansible-playbook",
) -> PreParseResult:
    """Run --list-tasks and --list-hosts in parallel; return assembled result.

    Both subprocesses run concurrently in a thread pool — the I/O dominates
    so threads + subprocess.run is sufficient (no need for asyncio).

    Failure mode: any subprocess error becomes an entry in `result.errors`
    rather than an exception. Whichever subprocess succeeded still
    contributes its data; the renderer falls back to incremental
    JSONL-driven population for whatever's missing.
    """
    errors: list[str] = []

    with ThreadPoolExecutor(max_workers=2) as pool:
        f_tasks = pool.submit(_spawn_one, executable, "--list-tasks", playbook, ansible_args)
        f_hosts = pool.submit(_spawn_one, executable, "--list-hosts", playbook, ansible_args)
        tasks_rc, tasks_stdout, tasks_stderr = f_tasks.result()
        hosts_rc, hosts_stdout, hosts_stderr = f_hosts.result()

    if tasks_rc != 0:
        errors.append(f"--list-tasks failed (exit {tasks_rc}): {tasks_stderr.strip() or '(no stderr)'}")
    if hosts_rc != 0:
        errors.append(f"--list-hosts failed (exit {hosts_rc}): {hosts_stderr.strip() or '(no stderr)'}")

    plays = parse_list_tasks_output(tasks_stdout) if tasks_rc == 0 else []
    play_hosts = parse_list_hosts_output(hosts_stdout) if hosts_rc == 0 else []
    definitions = assemble_definitions(plays=plays, play_hosts=play_hosts)

    return PreParseResult(
        plays=plays,
        play_hosts=play_hosts,
        definitions=definitions,
        errors=errors,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/integration/test_preflight_runner.py -v`
Expected: PASS — all four tests green.

- [ ] **Step 5: Run the full suite**

Run: `uv run pytest tests/ -q`
Expected: 1604 passing, 0 failing, 6 skipped.

- [ ] **Step 6: Commit**

```bash
git add src/ansible_aom/core/preflight.py tests/integration/test_preflight_runner.py
git commit -m "feat(core): add run_preflight wrapper for parallel --list-tasks/--list-hosts"
```

---

## Task 4: Add `set_definitions` to Renderer Protocol

**Files:**
- Modify: `src/ansible_aom/renderer/protocol.py`
- Modify: `src/ansible_aom/compact/renderer.py`
- Modify: `src/ansible_aom/tui/app.py`
- Test: `tests/unit/test_renderer_protocol.py` (extend) or `tests/compact/test_renderer_set_definitions.py` (new)

The Protocol gains one method. Both renderers implement it; CompactRenderer stores definitions and recomputes initial host count, TUI is no-op for now.

- [ ] **Step 1: Write the failing test**

Create `tests/compact/test_renderer_set_definitions.py`:

```python
"""Tests for CompactRenderer.set_definitions (preflight result wiring)."""

from __future__ import annotations

from ansible_aom.compact.renderer import CompactRenderer
from ansible_aom.core.models import PlayDefinition, TaskDefinition


def _build_definitions() -> list[PlayDefinition]:
    return [
        PlayDefinition(
            id="1",
            name="Web setup",
            hosts="webservers",
            resolved_hosts=["web1", "web2"],
            tasks=[
                TaskDefinition(
                    name="install nginx",
                    role=None,
                    tags=[],
                    play_id="1",
                    play_order=1,
                    task_order=0,
                ),
            ],
        ),
        PlayDefinition(
            id="2",
            name="DB setup",
            hosts="dbservers",
            resolved_hosts=["db1"],
            tasks=[],
        ),
    ]


def test_set_definitions_stores_definitions_on_renderer():
    renderer = CompactRenderer(is_tty=False)
    renderer.start("site.yml", [])

    defs = _build_definitions()
    renderer.set_definitions(defs)

    assert renderer._definitions == defs


def test_set_definitions_updates_initial_hosts_total_in_status_bar(capsys):
    """After preflight, the status bar should show the total resolved hosts immediately."""
    renderer = CompactRenderer(is_tty=False)
    renderer.start("site.yml", [])

    renderer.set_definitions(_build_definitions())
    renderer.handle_completion(0, "completed")

    captured = capsys.readouterr()
    # 2 hosts in play 1 + 1 in play 2 = 3 unique
    assert "0/3 hosts" in captured.out or "3/3 hosts" in captured.out


def test_set_definitions_called_before_start_is_safe():
    """Defensive: calling set_definitions before start should not crash."""
    renderer = CompactRenderer(is_tty=False)
    # Should not raise
    renderer.set_definitions(_build_definitions())
    assert renderer._definitions == _build_definitions()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/compact/test_renderer_set_definitions.py -v`
Expected: FAIL — `set_definitions` method does not exist.

- [ ] **Step 3: Add to Protocol**

Modify `src/ansible_aom/renderer/protocol.py` — add inside the `Renderer` Protocol class, after `start`:

```python
    def set_definitions(self, definitions: list) -> None:
        """Receive pre-flight playbook definitions (plays/tasks/hosts).

        Called once between start() and the first update_state(). Renderers
        use this to seed the task tree and total host count before any
        JSONL events arrive. May receive an empty list when preflight
        failed; renderers must tolerate that.
        """
        ...
```

(Use `list` not `list[PlayDefinition]` to keep the Protocol module free of model imports — runtime checks only verify presence of the method.)

- [ ] **Step 4: Implement on CompactRenderer**

In `src/ansible_aom/compact/renderer.py`, add `_definitions` to `__init__`:

```python
        self._definitions: list = []
```

Add the method (after `start`, before `update_state`):

```python
    def set_definitions(self, definitions: list) -> None:
        """Store preflight definitions and recompute the initial status bar.

        The host count in the status bar is the union of every play's
        resolved_hosts. We compute it once here so the user sees `0/N hosts`
        from the very first frame instead of `0/0 hosts` until JSONL
        events start filling in hosts incrementally.
        """
        self._definitions = list(definitions)
        if self._state is None:
            return
        self._render_status_bar()
```

Then update `_render_status_bar` to prefer `len(union of resolved_hosts)` over `len(host_statuses)` when the latter is zero:

```python
    def _render_status_bar(self) -> None:
        """Compute and push the current status bar to the display."""
        if self._state is None:
            return

        host_statuses: dict[str, Status] = {}
        for play in self._state.plays.values():
            for task in play.tasks.values():
                for hostname, host_state in task.hosts.items():
                    host_statuses[hostname] = host_state.status

        # Prefer the preflight-resolved host count when JSONL hasn't
        # filled in any host states yet, so the user sees `0/3 hosts`
        # immediately instead of `0/0 hosts`.
        preflight_hosts: set[str] = set()
        for play_def in self._definitions:
            preflight_hosts.update(play_def.resolved_hosts)
        hosts_total = max(len(host_statuses), len(preflight_hosts))

        hosts_completed = sum(
            1
            for s in host_statuses.values()
            if s in (Status.OK, Status.CHANGED, Status.SKIPPED, Status.COMPLETED)
        )

        elapsed = time.time() - self._start_time
        status_bar = format_status_bar(
            playbook=self._playbook,
            hosts_completed=hosts_completed,
            hosts_total=hosts_total,
            warnings=self._warnings_count,
            deprecations=self._deprecations_count,
            elapsed_seconds=elapsed,
        )
        self._display.update(status_bar)
```

`handle_completion` does the same `len(host_statuses)` calculation — apply the identical max with preflight hosts there too.

- [ ] **Step 5: Implement on AOMApp**

In `src/ansible_aom/tui/app.py`, add a no-op:

```python
    def set_definitions(self, definitions: list) -> None:
        """Receive preflight definitions. TUI builds tree from RunState today; this is a no-op."""
        return None
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/compact/test_renderer_set_definitions.py -v`
Expected: PASS — all three tests green.

- [ ] **Step 7: Run the full suite**

Run: `uv run pytest tests/ -q`
Expected: 1607 passing, 0 failing, 6 skipped. No regressions.

- [ ] **Step 8: Commit**

```bash
git add src/ansible_aom/renderer/protocol.py src/ansible_aom/compact/renderer.py src/ansible_aom/tui/app.py tests/compact/test_renderer_set_definitions.py
git commit -m "feat(renderer): add set_definitions protocol method"
```

---

## Task 5: Wire preflight into runner.run_playbook

**Files:**
- Modify: `src/ansible_aom/runner.py`
- Test: `tests/integration/test_runner.py` (extend)

The runner now calls `run_preflight()` between `renderer.start()` and `pexpect.spawn()`. Errors become warnings.

- [ ] **Step 1: Write the failing test**

Append to `tests/integration/test_runner.py` (study the existing `_make_fake_ansible_playbook` helper there to extend it):

```python
def test_run_playbook_calls_preflight_and_forwards_definitions(
    tmp_path, list_tasks_output, list_hosts_output, monkeypatch
):
    """run_playbook should call run_preflight and pass definitions to the renderer."""
    from ansible_aom.runner import run_playbook
    from unittest.mock import MagicMock

    captured_defs: list = []

    class StubRenderer:
        def start(self, playbook, args): ...
        def set_definitions(self, definitions): captured_defs.extend(definitions)
        def update_state(self, event): ...
        def handle_password_prompt(self, prompt): return ""
        def handle_completion(self, exit_code, state): ...
        def stop(self): ...

    fake_pre_result = MagicMock()
    fake_pre_result.definitions = ["DEF1", "DEF2"]
    fake_pre_result.errors = []

    monkeypatch.setattr(
        "ansible_aom.runner.run_preflight",
        lambda *, playbook, ansible_args: fake_pre_result,
    )
    # Stub out the actual pexpect run so we don't need a real ansible-playbook
    monkeypatch.setattr("ansible_aom.runner._drive", lambda *a, **kw: 0)

    class _FakeChild:
        exitstatus = 0
        signalstatus = None
        def isalive(self): return False
        def close(self, force=False): ...
    monkeypatch.setattr("pexpect.spawn", lambda *a, **kw: _FakeChild())

    exit_code = run_playbook("site.yml", [], StubRenderer())

    assert exit_code == 0
    assert captured_defs == ["DEF1", "DEF2"]


def test_run_playbook_forwards_preflight_errors_as_warnings(monkeypatch):
    from ansible_aom.runner import run_playbook
    from unittest.mock import MagicMock

    received_warnings: list[tuple[str, bool]] = []

    class StubRenderer:
        def start(self, playbook, args): ...
        def set_definitions(self, definitions): ...
        def add_warning(self, message, is_deprecation=False):
            received_warnings.append((message, is_deprecation))
        def update_state(self, event): ...
        def handle_password_prompt(self, prompt): return ""
        def handle_completion(self, exit_code, state): ...
        def stop(self): ...

    fake_pre_result = MagicMock()
    fake_pre_result.definitions = []
    fake_pre_result.errors = ["--list-hosts failed (exit 1): nope"]

    monkeypatch.setattr(
        "ansible_aom.runner.run_preflight",
        lambda *, playbook, ansible_args: fake_pre_result,
    )
    monkeypatch.setattr("ansible_aom.runner._drive", lambda *a, **kw: 0)

    class _FakeChild:
        exitstatus = 0
        signalstatus = None
        def isalive(self): return False
        def close(self, force=False): ...
    monkeypatch.setattr("pexpect.spawn", lambda *a, **kw: _FakeChild())

    run_playbook("site.yml", [], StubRenderer())

    assert any("--list-hosts failed" in msg for msg, _ in received_warnings)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/integration/test_runner.py -k "preflight" -v`
Expected: FAIL — `run_preflight` not imported in runner; `set_definitions` not called.

- [ ] **Step 3: Wire preflight into runner.py**

In `src/ansible_aom/runner.py`, update imports:

```python
from ansible_aom.core.preflight import run_preflight
```

Modify `run_playbook`, immediately after `renderer.start(playbook, ansible_args)` and before the `pexpect.spawn` block:

```python
    pre_result = run_preflight(playbook=playbook, ansible_args=ansible_args)

    set_definitions = getattr(renderer, "set_definitions", None)
    if callable(set_definitions):
        set_definitions(pre_result.definitions)

    if pre_result.errors:
        add_warning = getattr(renderer, "add_warning", None)
        if callable(add_warning):
            for err in pre_result.errors:
                add_warning(err, False)
```

(`set_definitions` is in the Protocol now but we still `getattr`-guard for ergonomic compatibility with stub renderers in tests. Same getattr pattern already used for `tick`/`add_warning`.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/integration/test_runner.py -v`
Expected: PASS — both new tests + all existing runner tests green.

- [ ] **Step 5: Run the full suite**

Run: `uv run pytest tests/ -q`
Expected: 1609 passing, 0 failing, 6 skipped.

- [ ] **Step 6: Commit**

```bash
git add src/ansible_aom/runner.py tests/integration/test_runner.py
git commit -m "feat(runner): call preflight before spawn and forward definitions/errors"
```

---

## Task 6: End-to-end smoke test (manual verification)

**Files:**
- No code changes — manual verification step
- Modify: `.sisyphus/notepads/implementation/learnings.md` (record results)

- [ ] **Step 1: Run against `simple.yml` and confirm hosts count appears immediately**

Run: `uv run aom .sisyphus/test-fixtures/simple.yml -i localhost, -c local`

Expected output (paraphrased):
```
PLAY [Simple test playbook] *********...
TASK [First task] *********...
ok: [localhost]
TASK [Second task with tags] *********...
ok: [localhost]
TASK [Third task] *********...
ok: [localhost]
.sisyphus/test-fixtures/simple.yml │ 1/1 hosts │ ⚠ 1 │ ✱ 1 │ 0:00:00 ●
```

Specifically: at the *very first frame* (before any JSONL event), the status bar should already say `0/1 hosts` rather than `0/0 hosts`. Confirm by piping through `head -1` or running with `--verbose`.

- [ ] **Step 2: Run against `multi_hosts.yml` and confirm multi-host count**

Run: `uv run aom .sisyphus/test-fixtures/multi_hosts.yml -i localhost, -c local` (adjust inventory if needed for the fixture).

Expected: status bar reflects total hosts from preflight resolution.

- [ ] **Step 3: Run against `syntax_error.yml` and confirm graceful preflight failure**

Run: `uv run aom .sisyphus/test-fixtures/syntax_error.yml -i localhost, -c local`

Expected: preflight `--list-tasks` errors are surfaced as warnings (`⚠` count > 0), the run continues and exits 4.

- [ ] **Step 4: Record findings in learnings**

Append a dated section to `.sisyphus/notepads/implementation/learnings.md` summarizing:
- What changed (preflight orchestrator + Protocol method)
- Test count delta
- End-to-end smoke results
- Any remaining gaps (e.g., compact renderer still doesn't render the *task tree* — only the host count uses preflight data; task-tree rendering is a follow-up slice)

- [ ] **Step 5: Commit the learnings note**

```bash
git add .sisyphus/notepads/implementation/learnings.md
git commit -m "docs(sisyphus): record preflight wiring and smoke results"
```

---

## Self-Review

**Spec coverage:**
- TC-087 (Parallel pre-parse execution) — Task 3 covers via threadpool with two concurrent `subprocess.run`.
- TC-088 (PreParseResult assembly) — Task 1 + Task 2.
- TC-089/TC-090 (--list-hosts fallback) — Task 3 (`test_run_preflight_list_hosts_failure_yields_definitions_without_resolved_hosts`).
- TC-097–TC-099 (--list-hosts parsing) — Already covered by existing tests in `tests/unit/test_parser.py`; no new tests needed.
- TC-107–TC-117 (--list-tasks parsing) — Already covered by existing tests.

**Out of scope (deferred to follow-up plan):**
- Task-tree rendering in compact view (panel still single-line; tree drawing needs row-count + width-aware wrapping work). Notes left in Task 6 step 4.
- TUI integration of preflight definitions (TUI sets `set_definitions` as no-op for now).
- TC-091–TC-096 (UUID matching, dynamic include_tasks expansion) — separate slice.

**Placeholder scan:** No "TBD" / "implement later" / "similar to Task N" — all code is concrete.

**Type consistency:** `set_definitions(definitions: list)` used identically across Protocol, CompactRenderer, AOMApp. `assemble_definitions(plays=, play_hosts=)` keyword-only; same signature in test callers.
