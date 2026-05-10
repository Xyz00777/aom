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


def _spawn_one(
    executable: str, mode_flag: str, playbook: str, ansible_args: list[str]
) -> tuple[int, str, str]:
    """Spawn a single ansible-playbook invocation; return (exit_code, stdout, stderr).

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
    except FileNotFoundError as exc:
        return 127, "", f"executable not found: {exc}"
    except PermissionError as exc:
        return 126, "", f"executable not executable: {exc}"
    except subprocess.TimeoutExpired:
        return 124, "", f"{mode_flag} timed out after {_PREFLIGHT_TIMEOUT_S}s"
    except OSError as exc:
        return 1, "", f"{mode_flag} failed: {exc}"
    return completed.returncode, completed.stdout, completed.stderr


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
        errors.append(
            f"--list-tasks failed (exit {tasks_rc}): {tasks_stderr.strip() or '(no stderr)'}"
        )
    if hosts_rc != 0:
        errors.append(
            f"--list-hosts failed (exit {hosts_rc}): {hosts_stderr.strip() or '(no stderr)'}"
        )

    plays = parse_list_tasks_output(tasks_stdout) if tasks_rc == 0 else []
    play_hosts = parse_list_hosts_output(hosts_stdout) if hosts_rc == 0 else []
    definitions = assemble_definitions(plays=plays, play_hosts=play_hosts)

    return PreParseResult(
        plays=plays,
        play_hosts=play_hosts,
        definitions=definitions,
        errors=errors,
    )
