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

from ansible_aom.core.models import PlayDefinition, TaskDefinition
from ansible_aom.core.parser import group_roles


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
