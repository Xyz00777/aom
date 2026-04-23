"""Session diff logic for AOM inspect.

See SPECIFICATION.md Section 9.3 for diff details.
"""

from typing import Any


def diff_sessions(
    old_session: dict[str, Any],
    new_session: dict[str, Any],
    changes_only: bool = False,
) -> dict[str, Any]:
    """Compare two sessions and return diff result.

    Args:
        old_session: The baseline session
        new_session: The current session to compare
        changes_only: If True, filter to only show changed tasks

    Returns:
        Dictionary containing:
        - tasks: List of task comparisons with baseline and current status
        - classifications: Dict of task_id -> classification string
        - baseline_playbook: Name of baseline playbook
        - current_playbook: Name of current playbook
        - playbooks_differ: Boolean if playbook names differ
    """
    baseline_playbook = old_session.get("playbook", "")
    current_playbook = new_session.get("playbook", "")
    playbooks_differ = baseline_playbook != current_playbook

    old_tasks = _extract_tasks(old_session)
    new_tasks = _extract_tasks(new_session)

    matches = match_tasks(old_tasks, new_tasks)

    tasks = []
    classifications = {}

    for task_id, (old_task, new_task) in matches.items():
        old_status = old_task.get("status") if old_task else None
        new_status = new_task.get("status") if new_task else None

        classification = classify_change(old_status, new_status)

        if changes_only and classification == "unchanged":
            continue

        task_entry = {
            "task_id": task_id,
            "task_name": (new_task or old_task).get("name", ""),
            "baseline_status": old_status,
            "current_status": new_status,
            "classification": classification,
        }
        tasks.append(task_entry)
        classifications[task_id] = classification

    matched_ids = set(matches.keys())
    for task in new_tasks:
        task_id = task.get("uuid") or task.get("id") or task.get("name") or ""
        if task_id not in matched_ids:
            if changes_only:
                continue
            classification = "new"
            task_entry = {
                "task_id": task_id,
                "task_name": task.get("name", ""),
                "baseline_status": None,
                "current_status": task.get("status"),
                "classification": classification,
            }
            tasks.append(task_entry)
            classifications[task_id] = classification

    for task in old_tasks:
        task_id = task.get("uuid") or task.get("id") or task.get("name") or ""
        if task_id not in matched_ids:
            if changes_only:
                continue
            classification = "removed"
            task_entry = {
                "task_id": task_id,
                "task_name": task.get("name", ""),
                "baseline_status": task.get("status"),
                "current_status": None,
                "classification": classification,
            }
            tasks.append(task_entry)
            classifications[task_id] = classification

    return {
        "tasks": tasks,
        "classifications": classifications,
        "baseline_playbook": baseline_playbook,
        "current_playbook": current_playbook,
        "playbooks_differ": playbooks_differ,
    }


def match_tasks(
    old_tasks: list[Any],
    new_tasks: list[Any],
) -> dict[str, tuple[Any, Any]]:
    """Match tasks between sessions using UUID/path/name strategy.

    Priority:
    1. UUID matching (most reliable)
    2. Path matching (file:line format)
    3. Name matching (fallback)

    Args:
        old_tasks: List of tasks from baseline session
        new_tasks: List of tasks from current session

    Returns:
        Dict mapping task identifiers to (old_task, new_task) tuples.
        Tasks not matched have None for the missing side.
    """
    matches: dict[str, tuple[Any, Any]] = {}

    old_by_uuid: dict[str, Any] = {}
    old_by_path: dict[str, Any] = {}
    old_by_name: dict[str, Any] = {}

    for task in old_tasks:
        uuid = task.get("uuid") or task.get("id")
        path = task.get("path")
        name = task.get("name", "")

        if uuid:
            old_by_uuid[uuid] = task
        if path:
            old_by_path[path] = task
        if name:
            old_by_name[name] = task

    new_matched: set[str] = set()

    for task in new_tasks:
        uuid = task.get("uuid") or task.get("id")
        if uuid and uuid in old_by_uuid:
            matches[uuid] = (old_by_uuid[uuid], task)
            new_matched.add(uuid)

    for task in new_tasks:
        uuid = task.get("uuid") or task.get("id")
        if uuid in new_matched:
            continue

        path = task.get("path")
        if path and path in old_by_path:
            old_task = old_by_path[path]
            match_key = uuid or path
            matches[match_key] = (old_task, task)
            new_matched.add(match_key)

    for task in new_tasks:
        uuid = task.get("uuid") or task.get("id")
        if uuid in new_matched:
            continue

        name = task.get("name", "")
        if name and name in old_by_name:
            old_task = old_by_name[name]
            old_match_key = old_task.get("uuid") or old_task.get("path") or old_task.get("name")
            if old_match_key not in matches:
                match_key = uuid or name
                matches[match_key] = (old_task, task)
                new_matched.add(match_key)

    return matches


def classify_change(old_status: str | None, new_status: str | None) -> str:
    """Classify a task status change.

    Args:
        old_status: Status from baseline session (None if task didn't exist)
        new_status: Status from current session (None if task was removed)

    Returns:
        Classification string: 'regressed', 'improved', 'changed', 'unchanged', 'new', 'removed'
    """
    if old_status is None and new_status is not None:
        return "new"

    if old_status is not None and new_status is None:
        return "removed"

    if old_status == new_status:
        return "unchanged"

    ok_statuses = {"ok", "changed"}
    bad_statuses = {"failed", "unreachable"}

    if old_status in ok_statuses and new_status in bad_statuses:
        return "regressed"

    if old_status in bad_statuses and new_status in ok_statuses:
        return "improved"

    return "changed"


def _extract_tasks(session: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract task information from session events.

    Args:
        session: Session dictionary with events

    Returns:
        List of task dictionaries with name, status, uuid, path
    """
    tasks = []
    seen_tasks: set[str] = set()

    for event in session.get("events", []):
        event_type = event.get("_event", "")

        if event_type in (
            "v2_runner_on_ok",
            "v2_runner_on_failed",
            "v2_runner_on_skipped",
            "v2_runner_on_unreachable",
        ):
            task_data = event.get("task", {})
            task_id = task_data.get("id") or task_data.get("name")
            task_name = task_data.get("name", "")

            if task_id and task_id not in seen_tasks:
                if event_type == "v2_runner_on_ok":
                    hosts = event.get("hosts", {})
                    status = "changed" if any(h.get("changed") for h in hosts.values()) else "ok"
                elif event_type == "v2_runner_on_failed":
                    status = "failed"
                elif event_type == "v2_runner_on_skipped":
                    status = "skipped"
                elif event_type == "v2_runner_on_unreachable":
                    status = "unreachable"
                else:
                    status = "ok"

                tasks.append(
                    {
                        "uuid": task_id,
                        "id": task_id,
                        "name": task_name,
                        "status": status,
                        "path": task_data.get("path"),
                    }
                )
                seen_tasks.add(task_id)

    return tasks
