"""Pure read-only parsing of include/role files.

This module discovers and parses ``include_tasks`` files and role
``tasks/main.yml`` files at runtime, populating ``RunState._include_cache``
and ``RunState._role_cache``. It also supports pre-execution scanning of
the playbook for static ``include_tasks`` directives.

All functions are I/O-light (``yaml.safe_load`` + ``pathlib``) and have
no dependency on compact/, tui/, renderer/, or ansible_runner.

Architectural rule: core/ never imports from compact/ or tui/.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

import yaml

from ansible_aom.core.models import (
    IncludeCacheEntry,
    PlayDefinition,
    RoleCacheEntry,
    RunState,
    strip_role_prefix,
)

logger = logging.getLogger(__name__)


def parse_include_tasks_file(path: Path) -> list[str]:
    """Read a YAML task-list file and return the ``name`` of every task.

    Preserves Jinja2 template expressions (``{{ var }}``) verbatim — no
    resolution is attempted. The file is expected to be a plain list of
    task dicts, the same format as a playbook tasks section or a role
    ``tasks/main.yml``.

    Returns an empty list when the file cannot be opened, the YAML is
    malformed, or the top-level value is not a list.
    """
    try:
        with path.open("r") as fh:
            data = yaml.safe_load(fh)
    except (FileNotFoundError, OSError, yaml.YAMLError) as exc:
        logger.debug("Failed to read/include parse %s: %s", path, exc)
        return []

    if not isinstance(data, list):
        return []

    names: list[str] = []
    for entry in data:
        if isinstance(entry, dict) and "name" in entry:
            names.append(str(entry["name"]))
    return names


def parse_role_tasks(role_dir: Path) -> list[str]:
    """Read ``role_dir/tasks/main.yml`` and return the list of task names.

    ``role : `` prefixes are stripped from every name so the cache matches
    the convention used by ``tree.py`` (which calls ``strip_role_prefix``
    during lookups). Returns an empty list on any error.
    """
    tasks_file = role_dir / "tasks" / "main.yml"
    try:
        with tasks_file.open("r") as fh:
            data = yaml.safe_load(fh)
    except (FileNotFoundError, OSError, yaml.YAMLError) as exc:
        logger.debug("Failed to read/parse role tasks %s: %s", tasks_file, exc)
        return []

    if not isinstance(data, list):
        return []

    names: list[str] = []
    for entry in data:
        if isinstance(entry, dict) and "name" in entry:
            name = str(entry["name"])
            names.append(strip_role_prefix(name))
    return names


def _scan_tasks_for_includes(
    tasks: list[dict],
    playbook_dir: Path,
    cache: dict[str, IncludeCacheEntry],
) -> None:
    """Walk a task list depth-first, caching every static ``include_tasks``.

    Skips entries whose file path contains ``{{`` (Jinja2 templates
    requiring runtime resolution). Descends into ``block``, ``rescue``,
    and ``always`` sub-lists.
    """
    for task in tasks:
        if not isinstance(task, dict):
            continue

        include_target = task.get("include_tasks")
        if (
            include_target is not None
            and isinstance(include_target, str)
            and "{{" not in include_target
        ):
            resolved = (playbook_dir / include_target).resolve()
            cache_key = str(resolved)
            if cache_key not in cache:
                task_names = parse_include_tasks_file(resolved)
                cache[cache_key] = IncludeCacheEntry(
                    path=cache_key,
                    task_names=task_names,
                    role=None,
                    parsed_at=datetime.now(timezone.utc),
                )

        # Recurse into block / rescue / always
        for sub_key in ("block", "rescue", "always"):
            sub_tasks = task.get(sub_key)
            if isinstance(sub_tasks, list):
                _scan_tasks_for_includes(sub_tasks, playbook_dir, cache)


def resolve_includes_from_playbook(
    playbook_path: str | Path,
    definitions: list[PlayDefinition],
    cache: dict[str, IncludeCacheEntry],
) -> None:
    """Parse the playbook YAML for static ``include_tasks`` directives.

    Reads the playbook file, walks every play's ``tasks``, ``pre_tasks``,
    ``post_tasks``, and ``handlers``, and populates *cache* with
    ``IncludeCacheEntry`` records for every ``include_tasks`` that uses a
    literal (non-Jinja2) path. Already-cached entries are skipped.

    *definitions* is accepted for signature compatibility but not currently
    used — preflight ``TaskDefinition`` objects do not carry file-path
    metadata for ``include_tasks``.
    """
    _ = definitions  # reserved for future use
    pb_path = Path(playbook_path)
    playbook_dir = pb_path.parent.resolve()

    try:
        with pb_path.open("r") as fh:
            playbook = yaml.safe_load(fh)
    except (FileNotFoundError, OSError, yaml.YAMLError) as exc:
        logger.debug("Failed to read/parse playbook %s: %s", pb_path, exc)
        cache.clear()
        return

    if not isinstance(playbook, list):
        return

    for entry in playbook:
        if not isinstance(entry, dict):
            continue
        for section in ("tasks", "pre_tasks", "post_tasks", "handlers"):
            tasks = entry.get(section)
            if isinstance(tasks, list):
                _scan_tasks_for_includes(tasks, playbook_dir, cache)


def _discover_include(
    state: RunState,
    include_path: str,
    parent_role: str | None,
) -> IncludeCacheEntry | None:
    """Resolve and parse an ``include_tasks`` file, caching the result.

    The file path is resolved relative to the playbook directory (the
    directory containing ``state.playbook``). If the resolved path is
    already in ``state._include_cache`` the cached entry is returned
    immediately. Returns ``None`` when the file cannot be read or parsed.
    """
    playbook_dir = Path(state.playbook).parent.resolve()
    resolved = (playbook_dir / include_path).resolve()
    cache_key = str(resolved)

    cached = state._include_cache.get(cache_key)
    if cached is not None:
        return cached

    task_names = parse_include_tasks_file(resolved)
    if not task_names:
        return None  # parse_include_tasks_file logged the reason

    entry = IncludeCacheEntry(
        path=cache_key,
        task_names=task_names,
        role=parent_role,
        parsed_at=datetime.now(timezone.utc),
    )
    state._include_cache[cache_key] = entry
    return entry


def _discover_role(
    state: RunState,
    role_name: str,
) -> RoleCacheEntry | None:
    """Resolve a role's ``tasks/main.yml``, caching the result.

    The role directory is resolved as ``<playbook_dir>/roles/<role_name>/``.
    If the role name is already in ``state._role_cache`` the cached entry
    is returned immediately. Returns ``None`` when the tasks file cannot
    be read or parsed.
    """
    cache_key = role_name.lower().strip()

    cached = state._role_cache.get(cache_key)
    if cached is not None:
        return cached

    playbook_dir = Path(state.playbook).parent.resolve()
    role_dir = playbook_dir / "roles" / role_name

    task_names = parse_role_tasks(role_dir)
    if not task_names:
        return None  # parse_role_tasks logged the reason

    entry = RoleCacheEntry(
        role_name=cache_key,
        task_names=task_names,
    )
    state._role_cache[cache_key] = entry
    return entry


def discover_include_with_runtime_path(
    state: RunState,
    task_path: str,
    parent_role: str | None,
) -> IncludeCacheEntry | None:
    """Discover an include from the runtime ``task.path`` JSONL field.

    The ``task.path`` field uses the format ``"file.yml:line_number"``
    (e.g. ``"included_tasks.yml:2"``). This function extracts the file
    path, resolves it relative to the playbook directory, parses and
    caches the result.

    Delegates to ``_discover_include`` after stripping the line-number
    suffix.
    """
    file_path = task_path.rsplit(":", 1)[0]
    return _discover_include(state, file_path, parent_role)
