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
    RoleGroupDefinition,
    TaskDefinition,
    strip_role_prefix,
)
from ansible_aom.core.run_state import RunState

logger = logging.getLogger(__name__)


# Ansible supports both the bare directive name and the fully-qualified
# ``ansible.builtin.<name>`` form. Real-world playbooks (especially those
# following the FQCN best practice) use the longer form. The constants
# below cover both; ``_lookup_directive`` recognises either when given a
# single canonical name.
_ROLE_DIRECTIVE_KEYS = ("include_role", "import_role")
_PLAYBOOK_DIRECTIVE_KEYS = ("import_playbook", "include_playbook")
_TASK_DIRECTIVE_KEYS = ("include_tasks",)


def _lookup_directive(entry: dict, canonical: str) -> object | None:
    """Return the value of a directive, accepting both bare and FQCN keys."""
    value: object | None = entry.get(canonical)
    if value is not None:
        return value
    return entry.get(f"ansible.builtin.{canonical}")


def _include_target_value(entry: dict) -> str | None:
    """Return the literal ``include_tasks`` target from string or mapping form.

    ``include_tasks: "foo.yml"`` → ``"foo.yml"``
    ``include_tasks: {file: "foo.yml"}`` → ``"foo.yml"``
    ``include_tasks: {file: "{{ x }}"}`` → ``None`` (Jinja skipped)
    """
    value = _lookup_directive(entry, "include_tasks")
    if value is None:
        return None
    if isinstance(value, str):
        target = value
    elif isinstance(value, dict):
        file_value = value.get("file")
        if not isinstance(file_value, str):
            return None
        target = file_value
    else:
        return None
    if "{{" in target:
        return None
    return target


def _resolve_include_path(target: str, base_dirs: list[Path]) -> Path | None:
    """Resolve *target* against the first *base_dirs* entry where it exists."""
    for base in base_dirs:
        resolved = (base / target).resolve()
        if resolved.is_file():
            return resolved
    return None


def _load_task_list(path: Path) -> list:
    """Read a YAML task-list file and return the top-level list (across documents).

    Uses ``yaml.safe_load_all`` so multi-document YAML files (legal in
    ansible) are handled. Returns an empty list when the file is missing,
    unreadable, has no task entries, or contains YAML that PyYAML cannot
    parse (ansible's own loader is more permissive than PyYAML on a few
    edge cases — e.g. ``quadlet_options:`` blocks with raw unit-file
    content followed by sibling keys at the same indent). Parse errors
    are logged once at WARNING; missing files are silent.
    """
    try:
        with path.open("r") as fh:
            documents = list(yaml.safe_load_all(fh))
    except FileNotFoundError:
        return []
    except OSError as exc:
        logger.debug("Failed to read %s: %s", path, exc)
        return []
    except yaml.YAMLError as exc:
        logger.warning("Skipping unparseable YAML %s: %s", path, exc)
        return []

    tasks: list = []
    for doc in documents:
        if isinstance(doc, list):
            tasks.extend(doc)
        elif isinstance(doc, dict) and "tasks" in doc:
            inner = doc["tasks"]
            if isinstance(inner, list):
                tasks.extend(inner)
    return tasks


def parse_include_tasks_file_with_flags(path: Path) -> tuple[list[str], dict[str, bool]]:
    """Read a YAML task-list file; return task names and per-task ``run_once`` flags.

    Preserves Jinja2 template expressions (``{{ var }}``) verbatim — no
    resolution is attempted. The file is expected to be a plain list of
    task dicts, the same format as a playbook tasks section or a role
    ``tasks/main.yml``.

    The flags dict maps each task name to ``True`` only when the task has
    a literal YAML ``run_once: true``. ``run_once: "{{ var }}"`` (Jinja
    string) and ``run_once: false`` are NOT flagged — they cannot be known
    statically, so they are treated as False. Keys use the raw task name
    (no role-prefix stripping), matching the returned ``task_names`` list.

    Returns ``([], {})`` when the file cannot be opened, the YAML is
    malformed, or no entries are present.
    """
    tasks = _load_task_list(path)
    names: list[str] = []
    flags: dict[str, bool] = {}
    for entry in tasks:
        if isinstance(entry, dict) and "name" in entry:
            name = str(entry["name"])
            names.append(name)
            if entry.get("run_once") is True:
                flags[name] = True
    return names, flags


def parse_include_tasks_file(path: Path) -> list[str]:
    """Read a YAML task-list file and return the ``name`` of every task.

    Preserves Jinja2 template expressions (``{{ var }}``) verbatim — no
    resolution is attempted. The file is expected to be a plain list of
    task dicts, the same format as a playbook tasks section or a role
    ``tasks/main.yml``.

    Returns an empty list when the file cannot be opened, the YAML is
    malformed, or no entries are present.
    """
    names, _ = parse_include_tasks_file_with_flags(path)
    return names


def parse_role_tasks_with_flags(role_dir: Path) -> tuple[list[str], dict[str, bool]]:
    """Read ``role_dir/tasks/main.yml``; return task names and ``run_once`` flags.

    ``role : `` prefixes are stripped from every name so the cache matches
    the convention used by ``tree.py`` (which calls ``strip_role_prefix``
    during lookups). The flags dict uses the same stripped names and marks
    a task ``True`` only for a literal YAML ``run_once: true`` (Jinja and
    ``false`` values are not flagged). Returns ``([], {})`` on any error or
    when the file does not exist.
    """
    tasks_file = role_dir / "tasks" / "main.yml"
    if not tasks_file.is_file():
        return [], {}
    tasks = _load_task_list(tasks_file)
    names: list[str] = []
    flags: dict[str, bool] = {}
    for entry in tasks:
        if isinstance(entry, dict) and "name" in entry:
            name = str(entry["name"])
            stripped = strip_role_prefix(name)
            names.append(stripped)
            if entry.get("run_once") is True:
                flags[stripped] = True
    return names, flags


def parse_role_tasks(role_dir: Path) -> list[str]:
    """Read ``role_dir/tasks/main.yml`` and return the list of task names.

    ``role : `` prefixes are stripped from every name so the cache matches
    the convention used by ``tree.py`` (which calls ``strip_role_prefix``
    during lookups). Returns an empty list on any error or when the file
    does not exist.
    """
    names, _ = parse_role_tasks_with_flags(role_dir)
    return names


def _find_nested_role_includes(role_dir: Path) -> list[str]:
    """Return names of roles included from this role's ``tasks/main.yml``.

    Walks the role's task list looking for ``include_role:`` or
    ``import_role:`` directives and returns the inner role name(s).
    Accepts the three YAML forms ansible uses:

    - ``include_role: foo`` (bare string)
    - ``include_role: name=foo`` (kwargs string — we take the prefix
      before any space or ``=``)
    - ``include_role:\n  name: foo`` (mapping with a ``name`` key)

    Jinja-templated values (``foo_{{ var }}``) are skipped — they can't be
    resolved at preflight, so we don't know which role they refer to.
    Returns an empty list when ``tasks/main.yml`` is missing or
    unparseable.
    """
    tasks_file = role_dir / "tasks" / "main.yml"
    if not tasks_file.is_file():
        return []
    tasks = _load_task_list(tasks_file)

    nested: list[str] = []
    for entry in tasks:
        if not isinstance(entry, dict):
            continue
        for directive in ("include_role", "import_role"):
            target = entry.get(directive)
            if target is None:
                continue
            role_name: str | None = None
            if isinstance(target, str):
                # ``include_role: foo`` or ``include_role: name=foo``.
                # Take the first whitespace-separated token; strip any
                # leading ``name=`` or ``name:`` for the kwargs form.
                first = target.split(None, 1)[0].strip()
                if first.startswith("name=") or first.startswith("name:"):
                    first = first.split("=", 1)[1] if "=" in first else first.split(":", 1)[1]
                role_name = first.strip()
            elif isinstance(target, dict):
                # ``include_role:\n  name: foo``
                candidate = target.get("name")
                if isinstance(candidate, str):
                    role_name = candidate.strip()
            if role_name and "{{" not in role_name and role_name:
                nested.append(role_name)
    return nested


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
    _scan_tasks_for_includes_impl(tasks, playbook_dir, cache)


def _scan_tasks_for_includes_impl(
    tasks: list,
    base_dir: Path,
    cache: dict[str, IncludeCacheEntry],
    fallback_base_dir: Path | None = None,
) -> None:
    """Shared DFS scanner — resolves ``include_tasks`` paths under *base_dir*.

    When *fallback_base_dir* is given and the primary resolution does not
    exist on disk, the target is re-resolved against the fallback base.
    This mirrors ansible's role-relative resolution: a ``../`` include
    inside a role escapes the role's ``tasks/`` dir up to the roles dir.
    """
    base_dirs = [base_dir] if fallback_base_dir is None else [base_dir, fallback_base_dir]
    for task in tasks:
        if not isinstance(task, dict):
            continue

        include_target = _include_target_value(task)
        if include_target is not None:
            resolved = _resolve_include_path(include_target, base_dirs)
            if resolved is not None:
                cache_key = str(resolved)
                if cache_key not in cache:
                    task_names, task_run_once = parse_include_tasks_file_with_flags(resolved)
                    cache[cache_key] = IncludeCacheEntry(
                        path=cache_key,
                        task_names=task_names,
                        role=None,
                        parsed_at=datetime.now(timezone.utc),
                        task_run_once=task_run_once,
                    )

        for sub_key in ("block", "rescue", "always"):
            sub_tasks = task.get(sub_key)
            if isinstance(sub_tasks, list):
                _scan_tasks_for_includes_impl(
                    sub_tasks, base_dir, cache, fallback_base_dir=fallback_base_dir
                )


def resolve_includes_from_playbook(
    playbook_path: str | Path,
    definitions: list[PlayDefinition],
    cache: dict[str, IncludeCacheEntry],
) -> set[str]:
    """Parse the playbook YAML for static ``include_tasks`` directives and roles.

    Reads the playbook file (multi-document aware), walks every play's
    ``tasks``, ``pre_tasks``, ``post_tasks``, and ``handlers``, and
    populates *cache* with ``IncludeCacheEntry`` records for every
    ``include_tasks`` that uses a literal (non-Jinja2) path. Also
    collects role names referenced from ``roles:``, ``include_role:``,
    ``import_role:``, and recursively from ``import_playbook:`` —
    callers should hand that set to ``resolve_role_relative_includes``
    so only referenced roles are scanned.

    Already-cached entries are skipped. Parse errors are logged at
    WARNING (matches ``_load_task_list``).

    *definitions* is accepted for signature compatibility but not
    currently used — preflight ``TaskDefinition`` objects do not carry
    file-path metadata for ``include_tasks``.

    Returns the set of referenced role names.
    """
    _ = definitions  # reserved for future use
    pb_path = Path(playbook_path)
    playbook_dir = pb_path.parent.resolve()

    try:
        with pb_path.open("r") as fh:
            documents = list(yaml.safe_load_all(fh))
    except FileNotFoundError:
        cache.clear()
        return set()
    except OSError as exc:
        logger.debug("Failed to read playbook %s: %s", pb_path, exc)
        cache.clear()
        return set()
    except yaml.YAMLError as exc:
        logger.warning("Skipping unparseable playbook %s: %s", pb_path, exc)
        cache.clear()
        return set()

    referenced_roles: set[str] = set()
    visited: set[str] = set()
    _walk_documents_for_includes(
        documents,
        playbook_dir=playbook_dir,
        cache=cache,
        referenced_roles=referenced_roles,
        visited=visited,
    )
    return referenced_roles


def _walk_documents_for_includes(
    documents: list,
    *,
    playbook_dir: Path,
    cache: dict[str, IncludeCacheEntry],
    referenced_roles: set[str],
    visited: set[str],
) -> None:
    """Walk a list of play dicts; scan ``include_tasks``, collect role refs,
    recurse into ``import_playbook:``.

    ``documents`` is what ``yaml.safe_load_all`` returned. A top-level
    playbook is typically a list of plays, which PyYAML yields as a
    single document whose value is the list — so we treat a list
    document as "many plays" and a dict document as "one play". This
    matches ansible's parser behaviour for both single-play and
    multi-play playbooks.

    Called once for the top-level playbook and again for each imported
    playbook. The ``visited`` set prevents infinite loops on cycles
    (rare but possible with hand-written playbook DAGs).
    """
    plays: list = []
    for doc in documents:
        if isinstance(doc, list):
            plays.extend(p for p in doc if isinstance(p, dict))
        elif isinstance(doc, dict):
            plays.append(doc)

    for entry in plays:
        for section in ("pre_tasks", "tasks", "post_tasks", "handlers"):
            tasks = entry.get(section)
            if isinstance(tasks, list):
                _scan_tasks_for_includes(tasks, playbook_dir, cache)
                _collect_role_refs_from_tasks(tasks, referenced_roles)

        if isinstance(entry.get("roles"), list):
            for role in entry["roles"]:
                name = _extract_role_name(role)
                if name:
                    referenced_roles.add(name)

        for directive in _ROLE_DIRECTIVE_KEYS:
            value = _lookup_directive(entry, directive)
            name = _extract_role_name(value)
            if name:
                referenced_roles.add(name)

        for directive in _PLAYBOOK_DIRECTIVE_KEYS:
            value = _lookup_directive(entry, directive)
            if not isinstance(value, str) or not value:
                continue
            if "{{" in value:
                continue
            resolved = (playbook_dir / value).resolve()
            key = str(resolved)
            if key in visited:
                continue
            visited.add(key)
            try:
                with resolved.open("r") as fh:
                    sub_docs = list(yaml.safe_load_all(fh))
            except (FileNotFoundError, OSError) as exc:
                logger.debug("Could not read imported playbook %s: %s", resolved, exc)
                continue
            except yaml.YAMLError as exc:
                logger.warning("Skipping unparseable imported playbook %s: %s", resolved, exc)
                continue
            _walk_documents_for_includes(
                sub_docs,
                playbook_dir=resolved.parent,
                cache=cache,
                referenced_roles=referenced_roles,
                visited=visited,
            )


def _extract_role_name(value: object) -> str | None:
    """Return the bare role name from any of the ``include_role`` forms."""
    if isinstance(value, str):
        first = value.split(None, 1)[0].strip()
        if first.startswith("name=") or first.startswith("name:"):
            first = first.split("=", 1)[1] if "=" in first else first.split(":", 1)[1]
        first = first.strip()
        if first and "{{" not in first:
            return first
        return None
    if isinstance(value, dict):
        # ``roles:`` list entries use ``- role: foo``; ``include_role:``
        # mapping form uses ``name: foo``. Accept either key.
        candidate = value.get("role")
        if not isinstance(candidate, str):
            candidate = value.get("name")
        if isinstance(candidate, str) and candidate and "{{" not in candidate:
            return candidate.strip()
    return None


def _collect_role_refs_from_tasks(tasks: list, referenced_roles: set[str]) -> None:
    """Walk a task list and gather any ``include_role`` / ``import_role`` refs."""
    for task in tasks:
        if not isinstance(task, dict):
            continue
        for directive in _ROLE_DIRECTIVE_KEYS:
            name = _extract_role_name(_lookup_directive(task, directive))
            if name:
                referenced_roles.add(name)
        for sub_key in ("block", "rescue", "always"):
            sub = task.get(sub_key)
            if isinstance(sub, list):
                _collect_role_refs_from_tasks(sub, referenced_roles)


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

    task_names, task_run_once = parse_include_tasks_file_with_flags(resolved)
    if not task_names:
        return None  # parse_include_tasks_file_with_flags logged the reason

    entry = IncludeCacheEntry(
        path=cache_key,
        task_names=task_names,
        role=parent_role,
        parsed_at=datetime.now(timezone.utc),
        task_run_once=task_run_once,
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

    As a post-processing pass after caching this role's own tasks, walks
    ``tasks/main.yml`` for ``include_role:`` / ``import_role:`` directives
    and registers each nested role in ``state._role_cache`` with
    ``parent_role=<this role>``. The nested entry's task list comes from
    ``parse_role_tasks`` on its own ``tasks/main.yml``; if that file is
    missing the entry is still registered (so the runtime cache knows the
    parent relationship) with an empty task list.
    """
    cache_key = role_name.lower().strip()

    cached = state._role_cache.get(cache_key)
    if cached is not None:
        return cached

    playbook_dir = Path(state.playbook).parent.resolve()
    role_dir = playbook_dir / "roles" / role_name

    task_names, task_run_once = parse_role_tasks_with_flags(role_dir)
    if not task_names:
        return None  # parse_role_tasks_with_flags logged the reason

    entry = RoleCacheEntry(
        role_name=cache_key,
        task_names=task_names,
        task_run_once=task_run_once,
    )
    state._role_cache[cache_key] = entry

    # Post-processing pass: discover roles included from this role's
    # ``tasks/main.yml`` and register each with ``parent_role`` pointing
    # back here. The inner cache key stays the inner role's name so the
    # same role included from multiple parents is deduplicated; the
    # first parent to register wins (the field is informational — T5
    # uses it only to populate ``TaskRunState.parent_role``).
    for nested_name in _find_nested_role_includes(role_dir):
        nested_key = nested_name.lower().strip()
        if not nested_key or nested_key in state._role_cache:
            continue
        nested_role_dir = playbook_dir / "roles" / nested_name
        nested_task_names, nested_task_run_once = parse_role_tasks_with_flags(nested_role_dir)
        state._role_cache[nested_key] = RoleCacheEntry(
            role_name=nested_key,
            task_names=nested_task_names,
            parent_role=cache_key,
            task_run_once=nested_task_run_once,
        )

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


def _scan_role_tasks_for_includes(
    role_dir: Path,
    cache: dict[str, IncludeCacheEntry],
) -> None:
    """Walk a role's ``tasks/main.yml`` for ``include_tasks`` (role-relative paths).

    Resolves ``include_tasks: _includes/foo.yml`` from inside
    ``roles/<name>/tasks/main.yml`` to ``<role_dir>/tasks/_includes/foo.yml``,
    not the playbook directory. Caches the result under the absolute path.
    Jinja-templated paths are skipped. Descends into ``block``, ``rescue``,
    and ``always``. Silently no-ops when ``tasks/main.yml`` is missing
    or unparseable — those failures are logged at WARNING once by
    ``_load_task_list`` if they reach that point.
    """
    tasks_file = role_dir / "tasks" / "main.yml"
    if not tasks_file.is_file():
        return
    tasks = _load_task_list(tasks_file)
    if not tasks:
        return
    _scan_tasks_for_includes_impl(
        tasks,
        role_dir / "tasks",
        cache,
        fallback_base_dir=role_dir.parent,
    )


def resolve_role_relative_includes(
    role_names: set[str] | list[str],
    playbook_dir: Path,
    cache: dict[str, IncludeCacheEntry],
) -> None:
    """Scan a specific set of roles' ``tasks/main.yml`` for ``include_tasks``.

    Only walks the role directories listed in *role_names* (extracted
    from the playbook YAML's ``roles:`` / ``include_role:`` /
    ``import_role:`` directives, transitively). Roles whose
    ``tasks/main.yml`` is missing, unparseable by PyYAML, or absent
    from disk are silently skipped. Designed to be called after
    ``resolve_includes_from_playbook`` so that includes declared at
    the play level are scanned first; ``_scan_role_tasks_for_includes``
    short-circuits on cache hits so already-known files aren't re-parsed.

    Scanning only referenced roles (vs. every directory under
    ``roles/``) matters in real playbooks where ``roles/`` contains
    dozens of roles and the playbook imports only a handful — without
    this filter, pre-flight opens every role's YAML, including ones
    with Jinja-only or ansible-specific syntax that PyYAML cannot
    parse and that the user never asked AOM to look at.
    """
    roles_dir = playbook_dir / "roles"
    if not roles_dir.is_dir():
        return
    for role_name in sorted(role_names):
        if not isinstance(role_name, str) or not role_name:
            continue
        if "{{" in role_name or "}}" in role_name:
            continue
        role_dir = roles_dir / role_name
        if not role_dir.is_dir():
            continue
        _scan_role_tasks_for_includes(role_dir, cache)


def graft_include_children(
    *,
    playbook_path: str | Path,
    definitions: list[PlayDefinition],
    cache: dict[str, IncludeCacheEntry],
) -> None:
    """Replace each ``include_tasks`` stub with its resolved children.

    Single linear DFS: walks the playbook YAML AND every referenced
    role's ``tasks/main.yml``, pairing each ``include_tasks:``
    directive with a ``TaskDefinition`` whose name matches the
    directive's ``name:`` field. For each match, appends the cached
    task names as children of the stub. When a matched stub contains
    a further ``include_tasks:`` directive (the cached file itself
    includes another), the DFS recurses into that file so nested
    includes graft in one pass — no re-walk of the cache, no
    re-parsing of YAML, and the per-include scan cost is O(1) file
    read per unique include.

    Role paths are pulled from the playbook's ``definitions.tasks``
    role grouping (existing preflight data, no extra YAML walk needed).

    Stubs with no matching cache entry are left untouched — the
    runtime graft remains the fallback for Jinja-path includes and
    loop-resolved filenames. Children are appended to ``stub.children``;
    existing children (e.g. from an earlier runtime graft) are preserved.
    """
    pb_path = Path(playbook_path)
    playbook_dir = pb_path.parent.resolve()

    try:
        with pb_path.open("r") as fh:
            documents = list(yaml.safe_load_all(fh))
    except FileNotFoundError:
        return
    except OSError as exc:
        logger.debug("Failed to read playbook %s for graft: %s", pb_path, exc)
        return
    except yaml.YAMLError as exc:
        logger.warning("Skipping unparseable playbook %s: %s", pb_path, exc)
        return

    # Shared pairing state: pairs each YAML play (inline or inside an
    # imported file) with a ``PlayDefinition`` by play name first, falling
    # back to a positional cursor. ``--list-tasks`` skips plays (tags:
    # never, false play-level when:), so YAML order != definition order;
    # name matching is the primary pairing, the cursor is the fallback.
    state = _GraftState(definitions)
    visited_imports: set[str] = set()
    plays: list = []
    for doc in documents:
        if isinstance(doc, list):
            plays.extend(p for p in doc if isinstance(p, dict))
        elif isinstance(doc, dict):
            plays.append(doc)

    for entry in plays:
        # An inline play (has task sections) consumes the next definition,
        # unless --list-tasks skips it (tags: never / when: false).
        if _has_inline_sections(entry) and not _is_skipped_play(entry):
            play_def = state.next_definition(entry.get("name"))
            if play_def is None:
                break

            name_index = _build_name_index(play_def)

            for section in ("pre_tasks", "tasks", "post_tasks", "handlers"):
                section_tasks = entry.get(section)
                if isinstance(section_tasks, list):
                    _graft_section_dfs(
                        section_tasks,
                        base_dir=playbook_dir,
                        cache=cache,
                        name_index=name_index,
                    )

            for role_name in _roles_referenced(play_def):
                role_dir = playbook_dir / "roles" / role_name
                tasks_file = role_dir / "tasks" / "main.yml"
                if not tasks_file.is_file():
                    continue
                tasks = _load_task_list(tasks_file)
                if tasks:
                    _graft_section_dfs(
                        tasks,
                        base_dir=role_dir / "tasks",
                        cache=cache,
                        name_index=name_index,
                        fallback_base_dir=role_dir.parent,
                    )

        # Recurse into imported playbooks so their includes are also
        # grafted. Reuse the import-playbook walker — it knows how to
        # recurse without infinite loops via the visited set. The import
        # play itself consumes no definition; the imported file's plays
        # consume them via the shared state.
        for directive in _PLAYBOOK_DIRECTIVE_KEYS:
            value = _lookup_directive(entry, directive)
            if not isinstance(value, str) or not value or "{{" in value:
                continue
            resolved = (playbook_dir / value).resolve()
            if str(resolved) in visited_imports:
                continue
            visited_imports.add(str(resolved))
            _graft_imported_playbook(
                resolved,
                cache=cache,
                play_defs=definitions,
                playbook_dir=resolved.parent,
                visited_imports=visited_imports,
                state=state,
                roles_base_dir=playbook_dir,
            )


class _GraftState:
    """Shared pairing state threaded through the graft walk.

    Pairs each YAML play with a ``PlayDefinition`` by play name first
    (exact, then normalized), falling back to a positional cursor. Tracks
    consumed definitions so duplicate play names don't double-consume and
    the cursor skips already-paired definitions.
    """

    __slots__ = ("_definitions", "_by_exact", "_by_norm", "_consumed", "_cursor")

    def __init__(self, definitions: list[PlayDefinition]) -> None:
        self._definitions = definitions
        self._by_exact: dict[str, int] = {}
        self._by_norm: dict[str, int] = {}
        for idx, play_def in enumerate(definitions):
            name = play_def.name
            if not name:
                continue
            self._by_exact.setdefault(name, idx)
            self._by_norm.setdefault(name.strip().lower(), idx)
        self._consumed: set[int] = set()
        self._cursor = 0

    def next_definition(self, name: object | None) -> PlayDefinition | None:
        """Return the next unconsumed definition for a YAML play.

        Prefers a definition whose name matches *name* (exact, then
        normalized); otherwise advances the positional cursor past
        already-consumed definitions.
        """
        if isinstance(name, str) and name:
            idx = self._by_exact.get(name)
            if idx is None:
                idx = self._by_norm.get(name.strip().lower())
            if idx is not None and idx not in self._consumed:
                self._consumed.add(idx)
                return self._definitions[idx]
        while self._cursor < len(self._definitions):
            idx = self._cursor
            self._cursor += 1
            if idx not in self._consumed:
                self._consumed.add(idx)
                return self._definitions[idx]
        return None


def _graft_imported_playbook(
    imported_path: Path,
    *,
    cache: dict[str, IncludeCacheEntry],
    play_defs: list,
    playbook_dir: Path,
    visited_imports: set[str],
    state: _GraftState,
    roles_base_dir: Path,
) -> None:
    """Apply the graft pass to one ``import_playbook:`` file.

    Pairs each play in the imported file with a ``PlayDefinition`` via the
    shared *state* (name-first, cursor fallback), so ``include_tasks``
    stubs inside the imported file graft onto the definition whose tasks
    contain them. Nested imports recurse with the same state. Best-effort:
    stubs with no matching cache entry are left untouched; the runtime
    graft remains authoritative for those cases.

    *roles_base_dir* is the top-level playbook directory (the one holding
    ``roles/``), which stays constant across nested imports — role paths
    resolve against it, not against the imported file's own directory.
    """
    documents: list = []
    try:
        with imported_path.open("r") as fh:
            documents = list(yaml.safe_load_all(fh))
    except (FileNotFoundError, OSError) as exc:
        logger.debug("Could not read imported playbook %s: %s", imported_path, exc)
        return
    except yaml.YAMLError as exc:
        logger.warning("Skipping unparseable imported playbook %s: %s", imported_path, exc)
        return

    plays: list = []
    for doc in documents:
        if isinstance(doc, list):
            plays.extend(p for p in doc if isinstance(p, dict))
        elif isinstance(doc, dict):
            plays.append(doc)

    for entry in plays:
        if not _has_inline_sections(entry):
            # An import_playbook entry consumes no definition; its
            # imported file's plays consume them via the shared state.
            for directive in _PLAYBOOK_DIRECTIVE_KEYS:
                value = _lookup_directive(entry, directive)
                if not isinstance(value, str) or not value or "{{" in value:
                    continue
                resolved = (playbook_dir / value).resolve()
                if str(resolved) in visited_imports:
                    continue
                visited_imports.add(str(resolved))
                _graft_imported_playbook(
                    resolved,
                    cache=cache,
                    play_defs=play_defs,
                    playbook_dir=resolved.parent,
                    visited_imports=visited_imports,
                    state=state,
                    roles_base_dir=roles_base_dir,
                )
            continue

        if _is_skipped_play(entry):
            continue

        play_def = state.next_definition(entry.get("name"))
        if play_def is None:
            break

        name_index = _build_name_index(play_def)

        for section in ("pre_tasks", "tasks", "post_tasks", "handlers"):
            section_tasks = entry.get(section)
            if isinstance(section_tasks, list):
                _graft_section_dfs(
                    section_tasks,
                    base_dir=playbook_dir,
                    cache=cache,
                    name_index=name_index,
                )

        for role_name in _roles_referenced(play_def):
            role_dir = roles_base_dir / "roles" / role_name
            tasks_file = role_dir / "tasks" / "main.yml"
            if not tasks_file.is_file():
                continue
            tasks = _load_task_list(tasks_file)
            if tasks:
                _graft_section_dfs(
                    tasks,
                    base_dir=role_dir / "tasks",
                    cache=cache,
                    name_index=name_index,
                    fallback_base_dir=role_dir.parent,
                )

        for directive in _PLAYBOOK_DIRECTIVE_KEYS:
            value = _lookup_directive(entry, directive)
            if not isinstance(value, str) or not value or "{{" in value:
                continue
            resolved = (playbook_dir / value).resolve()
            if str(resolved) in visited_imports:
                continue
            visited_imports.add(str(resolved))
            _graft_imported_playbook(
                resolved,
                cache=cache,
                play_defs=play_defs,
                playbook_dir=resolved.parent,
                visited_imports=visited_imports,
                state=state,
                roles_base_dir=roles_base_dir,
            )


def _has_inline_sections(entry: dict) -> bool:
    """True if *entry* is an inline play (has task-bearing sections or roles).

    An ``import_playbook:`` entry has no task sections and consumes no
    ``PlayDefinition`` — its imported file's plays consume them instead.
    A play with only a ``roles:`` list still consumes a definition
    (``--list-tasks`` expands the role's tasks into it), so it counts.
    """
    if any(
        isinstance(entry.get(section), list)
        for section in ("pre_tasks", "tasks", "post_tasks", "handlers")
    ):
        return True
    return isinstance(entry.get("roles"), list)


def _is_skipped_play(entry: dict) -> bool:
    """True if ``--list-tasks`` would skip *entry* (so it consumes no definition).

    ``--list-tasks`` omits plays tagged ``never`` and plays whose
    play-level ``when:`` is statically false. Such plays appear in the
    YAML but not in the definitions list, so they must not consume a
    ``PlayDefinition`` — otherwise the positional pairing drifts.
    """
    tags = entry.get("tags")
    if isinstance(tags, list) and "never" in tags:
        return True
    if isinstance(tags, str) and tags.strip() == "never":
        return True
    when = entry.get("when")
    if when is False:
        return True
    if isinstance(when, str) and when.strip().lower() == "false":
        return True
    return False


def _build_name_index(play_def: PlayDefinition) -> dict[str, TaskDefinition]:
    """Map ``name`` → ``TaskDefinition`` for every task def in *play_def*.

    Includes flat tasks and those inside ``RoleGroupDefinition``s. Used
    to pair ``include_tasks:`` directives (which carry the directive's
    own ``name:``) with their corresponding preflight stub.
    """
    index: dict[str, TaskDefinition] = {}
    _index_into(play_def.tasks, index)
    return index


def _index_into(entries: list, index: dict[str, TaskDefinition]) -> None:
    for entry in entries:
        if isinstance(entry, RoleGroupDefinition):
            _index_into(entry.tasks, index)
        elif isinstance(entry, TaskDefinition):
            if entry.name:
                index.setdefault(entry.name, entry)
            if entry.children:
                _index_into(entry.children, index)


def _roles_referenced(play_def: PlayDefinition) -> set[str]:
    names: set[str] = set()
    for entry in play_def.tasks:
        if isinstance(entry, TaskDefinition) and entry.role:
            names.add(entry.role)
        elif isinstance(entry, RoleGroupDefinition):
            names.add(entry.role)
    return names


def _graft_section_dfs(
    section_tasks: list,
    *,
    base_dir: Path,
    cache: dict[str, IncludeCacheEntry],
    name_index: dict[str, TaskDefinition],
    visited_files: set[str] | None = None,
    fallback_base_dir: Path | None = None,
) -> None:
    """Walk *section_tasks* for literal ``include_tasks`` directives and graft.

    For each directive:
    1. Resolve the cache key from *base_dir* (falling back to
       *fallback_base_dir* when the primary path does not exist — used for
       role ``../`` includes that escape the role's ``tasks/`` dir).
    2. Find the matching ``TaskDefinition`` by the directive's ``name:``.
    3. Append the cached task names as children of the stub.
    4. Recurse into the cached file's YAML so any nested
       ``include_tasks:`` is grafted in the same pass.

    *visited_files* prevents infinite recursion on cycles (rare but
    possible if an included file includes itself via a non-Jinja path).
    The walker descends into ``block:``/``rescue:``/``always:``
    sub-lists before checking the task-level ``include_tasks:``.
    """
    if visited_files is None:
        visited_files = set()
    base_dirs = [base_dir] if fallback_base_dir is None else [base_dir, fallback_base_dir]
    for task in section_tasks:
        if not isinstance(task, dict):
            continue
        # Stamp literal ``run_once: true`` inline tasks (playbook or role
        # YAML) onto their preflight stub. Only a literal YAML ``true``
        # counts; Jinja-templated and ``false`` values are left unstamped.
        if task.get("run_once") is True:
            yaml_name = str(task.get("name") or "")
            stub = name_index.get(yaml_name)
            if stub is None and yaml_name:
                for k, v in name_index.items():
                    if strip_role_prefix(k) == yaml_name or k.endswith(f" : {yaml_name}"):
                        stub = v
                        break
            if stub is not None:
                stub.run_once = True
        for sub_key in ("block", "rescue", "always"):
            sub = task.get(sub_key)
            if isinstance(sub, list):
                _graft_section_dfs(
                    sub,
                    base_dir=base_dir,
                    cache=cache,
                    name_index=name_index,
                    visited_files=visited_files,
                    fallback_base_dir=fallback_base_dir,
                )
        target = _include_target_value(task)
        if target is not None:
            resolved = _resolve_include_path(target, base_dirs)
            if resolved is not None:
                cache_key = str(resolved)
                if cache_key not in visited_files:
                    visited_files.add(cache_key)
                    cache_entry = cache.get(cache_key)
                    if cache_entry is not None:
                        yaml_name = str(task.get("name") or "")
                        stub = name_index.get(yaml_name)
                        if stub is None and yaml_name:
                            for k, v in name_index.items():
                                if strip_role_prefix(k) == yaml_name or k.endswith(
                                    f" : {yaml_name}"
                                ):
                                    stub = v
                                    break
                        if stub is None and not yaml_name:
                            stub = _find_stub_by_role(name_index)
                        if stub is not None:
                            _graft_children(stub, cache_entry)
                            nested_tasks = _load_task_list(resolved)
                            if nested_tasks:
                                child_index: dict[str, TaskDefinition] = {
                                    c.name: c for c in stub.children if c.name
                                }
                                _graft_section_dfs(
                                    nested_tasks,
                                    base_dir=resolved.parent,
                                    cache=cache,
                                    name_index=child_index,
                                    visited_files=visited_files,
                                )

        # Check include_role / import_role
        role_name = None
        for directive in _ROLE_DIRECTIVE_KEYS:
            role_name = _extract_role_name(_lookup_directive(task, directive))
            if role_name:
                break

        if role_name:
            role_dir = _resolve_role_dir(role_name, base_dir=base_dir)
            if role_dir is not None:
                tasks_file = role_dir / "tasks" / "main.yml"
                if not tasks_file.is_file():
                    tasks_file = role_dir / "tasks" / "main.yaml"
                cache_key = f"role:{role_name.lower().strip()}"
                if cache_key not in visited_files and tasks_file.is_file():
                    visited_files.add(cache_key)
                    task_names, task_run_once = parse_role_tasks_with_flags(role_dir)
                    if task_names:
                        yaml_name = str(task.get("name") or "")
                        stub = name_index.get(yaml_name)
                        if stub is None and yaml_name:
                            for k, v in name_index.items():
                                if strip_role_prefix(k) == yaml_name or k.endswith(
                                    f" : {yaml_name}"
                                ):
                                    stub = v
                                    break
                        if stub is None:
                            for k, v in name_index.items():
                                if role_name in k:
                                    stub = v
                                    break
                        if stub is None and not yaml_name:
                            stub = _find_stub_by_role(name_index)
                        if stub is not None:
                            base_idx = len(stub.children)
                            existing_names = {c.name for c in stub.children}
                            for offset, name in enumerate(task_names):
                                if name in existing_names:
                                    continue
                                child = TaskDefinition(
                                    name=name,
                                    role=role_name,
                                    tags=[],
                                    play_id=stub.play_id,
                                    play_order=stub.play_order,
                                    task_order=base_idx + offset,
                                    is_dynamic=False,
                                    parent_role=stub.parent_role or stub.role,
                                    run_once=task_run_once.get(name, False),
                                )
                                stub.children.append(child)

                            nested_tasks = _load_task_list(tasks_file)
                            if nested_tasks:
                                child_index = {c.name: c for c in stub.children if c.name}
                                _graft_section_dfs(
                                    nested_tasks,
                                    base_dir=role_dir / "tasks",
                                    cache=cache,
                                    name_index=child_index,
                                    visited_files=visited_files,
                                )


def _resolve_role_dir(role_name: str, base_dir: Path) -> Path | None:
    """Find the directory for *role_name* relative to *base_dir* or its ancestors."""
    candidates = [
        base_dir / "roles" / role_name,
        base_dir / role_name,
        base_dir.parent / "roles" / role_name,
        base_dir.parent / role_name,
    ]
    if len(base_dir.parents) > 1:
        candidates.append(base_dir.parents[1] / "roles" / role_name)
    for candidate in candidates:
        if (candidate / "tasks" / "main.yml").is_file() or (
            candidate / "tasks" / "main.yaml"
        ).is_file():
            return candidate
    return None


def _find_stub_by_role(
    name_index: dict[str, TaskDefinition],
) -> TaskDefinition | None:
    """Last-resort fallback: pick the first stub whose role is unset.

    Used when the YAML directive had no ``name:`` and ``--list-tasks``
    synthesised one (``include_tasks`` with bare filename). The
    heuristic is correct for the common "one include per role"
    pattern but may mis-pair when there are multiple role-less stubs
    in the same role — the runtime graft remains authoritative there.
    """
    for stub in name_index.values():
        if stub.role is None:
            return stub
    return None


def _graft_children(stub: TaskDefinition, cache_entry: IncludeCacheEntry) -> None:
    """Append cached task names as children of *stub*."""
    base_idx = len(stub.children)
    existing_names = {c.name for c in stub.children}
    for offset, name in enumerate(cache_entry.task_names):
        if name in existing_names:
            continue
        child = TaskDefinition(
            name=name,
            role=stub.role,
            tags=[],
            play_id=stub.play_id,
            play_order=stub.play_order,
            task_order=base_idx + offset,
            is_dynamic=False,
            parent_role=stub.parent_role or stub.role,
            run_once=cache_entry.task_run_once.get(name, False),
        )
        stub.children.append(child)
