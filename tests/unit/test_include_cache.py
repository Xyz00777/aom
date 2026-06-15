"""Unit tests for include/role file parsing and caching.

Covers all public functions in ``src/ansible_aom/core/includes.py``:
parse_include_tasks_file, parse_role_tasks, _discover_include,
_discover_role, discover_include_with_runtime_path,
resolve_includes_from_playbook, plus IncludeCacheEntry.task_count
and RoleCacheEntry.task_count properties.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from ansible_aom.core.includes import (
    _discover_include,
    _discover_role,
    discover_include_with_runtime_path,
    parse_include_tasks_file,
    parse_role_tasks,
    resolve_includes_from_playbook,
)
from ansible_aom.core.models import (
    IncludeCacheEntry,
    PlayDefinition,
    RoleCacheEntry,
    RunState,
)

# ---------------------------------------------------------------------------
# parse_include_tasks_file
# ---------------------------------------------------------------------------


class TestParseIncludeTasksFile:
    """Unit tests for parse_include_tasks_file()."""

    def test_parse_include_tasks_file_valid(self, tmp_path: Path) -> None:
        """Valid YAML task list returns all task names."""
        f = tmp_path / "included.yml"
        f.write_text("""
- name: Task A
  debug:
    msg: hello
- name: Task B
  debug:
    msg: world
""")
        result = parse_include_tasks_file(f)
        assert result == ["Task A", "Task B"]

    def test_parse_include_tasks_file_jinja2_template(self, tmp_path: Path) -> None:
        """Jinja2 template names are preserved verbatim."""
        f = tmp_path / "templated.yml"
        f.write_text("""
- name: "Setup {{ app_name }}"
  debug:
    msg: templated
- name: "Cleanup {{ app_name }} v{{ version }}"
  debug:
    msg: more
""")
        result = parse_include_tasks_file(f)
        assert result == ["Setup {{ app_name }}", "Cleanup {{ app_name }} v{{ version }}"]

    def test_parse_include_tasks_file_missing_file(self, tmp_path: Path) -> None:
        """Missing file returns empty list."""
        result = parse_include_tasks_file(tmp_path / "does_not_exist.yml")
        assert result == []

    def test_parse_include_tasks_file_malformed_yaml(self, tmp_path: Path) -> None:
        """Malformed YAML returns empty list."""
        f = tmp_path / "bad.yml"
        f.write_text("this: is: not: valid: [[[")
        result = parse_include_tasks_file(f)
        assert result == []

    def test_parse_include_tasks_file_non_list(self, tmp_path: Path) -> None:
        """Top-level value that is not a list returns empty list."""
        f = tmp_path / "not_a_list.yml"
        f.write_text("key: value\nanother: 42\n")
        result = parse_include_tasks_file(f)
        assert result == []

    def test_parse_include_tasks_file_skips_tasks_without_name(self, tmp_path: Path) -> None:
        """Tasks without a 'name' key are skipped."""
        f = tmp_path / "mixed.yml"
        f.write_text("""
- name: Named task
  debug:
    msg: has name
- debug:
    msg: no name here
- name: Another named
  debug:
    msg: also has name
- vars:
    foo: bar
""")
        result = parse_include_tasks_file(f)
        assert result == ["Named task", "Another named"]

    def test_parse_include_tasks_file_empty_list(self, tmp_path: Path) -> None:
        """Empty YAML list returns empty list."""
        f = tmp_path / "empty.yml"
        f.write_text("[]\n")
        result = parse_include_tasks_file(f)
        assert result == []


# ---------------------------------------------------------------------------
# parse_role_tasks
# ---------------------------------------------------------------------------


class TestParseRoleTasks:
    """Unit tests for parse_role_tasks()."""

    def test_parse_role_tasks_valid(self, tmp_path: Path) -> None:
        """Valid role directory with tasks/main.yml returns task names."""
        tasks_dir = tmp_path / "tasks"
        tasks_dir.mkdir()
        main_file = tasks_dir / "main.yml"
        main_file.write_text("""
- name: Install packages
  apt:
    name: nginx
- name: Configure service
  template:
    src: nginx.conf.j2
    dest: /etc/nginx/nginx.conf
""")
        result = parse_role_tasks(tmp_path)
        assert result == ["Install packages", "Configure service"]

    def test_parse_role_tasks_missing_dir(self, tmp_path: Path) -> None:
        """Missing role directory returns empty list."""
        result = parse_role_tasks(tmp_path / "nonexistent_role")
        assert result == []

    def test_parse_role_tasks_strips_prefix(self, tmp_path: Path) -> None:
        """Role prefix 'role : ' is stripped from task names."""
        tasks_dir = tmp_path / "tasks"
        tasks_dir.mkdir()
        main_file = tasks_dir / "main.yml"
        main_file.write_text("""
- name: "test_role : Install packages"
  apt:
    name: nginx
- name: "test_role : Configure service"
  template:
    src: config.j2
    dest: /etc/service.conf
""")
        result = parse_role_tasks(tmp_path)
        assert result == ["Install packages", "Configure service"]

    def test_parse_role_tasks_no_name_keys(self, tmp_path: Path) -> None:
        """Tasks without 'name' key are skipped in role parsing."""
        tasks_dir = tmp_path / "tasks"
        tasks_dir.mkdir()
        main_file = tasks_dir / "main.yml"
        main_file.write_text("""
- debug:
    msg: no name
- name: Named only
  debug:
    msg: has name
- set_fact:
    x: 1
""")
        result = parse_role_tasks(tmp_path)
        assert result == ["Named only"]

    def test_parse_role_tasks_malformed_yaml(self, tmp_path: Path) -> None:
        """Malformed YAML in tasks/main.yml returns empty list."""
        tasks_dir = tmp_path / "tasks"
        tasks_dir.mkdir()
        main_file = tasks_dir / "main.yml"
        main_file.write_text("{{{ broken yaml")
        result = parse_role_tasks(tmp_path)
        assert result == []


# ---------------------------------------------------------------------------
# _discover_include
# ---------------------------------------------------------------------------


class TestDiscoverInclude:
    """Unit tests for _discover_include()."""

    def test_discover_include_successful(self, tmp_path: Path) -> None:
        """Successful include file parsing creates and returns a cache entry."""
        playbook = tmp_path / "site.yml"
        playbook.touch()
        included = tmp_path / "included.yml"
        included.write_text("""
- name: Task A
  debug:
    msg: hello
- name: Task B
  debug:
    msg: world
""")
        state = RunState(playbook=str(playbook))
        entry = _discover_include(state, "included.yml", parent_role=None)
        assert entry is not None
        assert entry.task_names == ["Task A", "Task B"]
        assert entry.role is None
        assert str(included.resolve()) in state._include_cache

    def test_discover_include_dedup(self, tmp_path: Path) -> None:
        """Second call returns the cached entry without re-parsing."""
        playbook = tmp_path / "site.yml"
        playbook.touch()
        included = tmp_path / "included.yml"
        included.write_text("""
- name: Single task
  debug:
    msg: once
""")
        state = RunState(playbook=str(playbook))
        entry1 = _discover_include(state, "included.yml", parent_role=None)
        # Wipe the file so a re-parse would fail — dedup must prevent reading.
        included.unlink()
        entry2 = _discover_include(state, "included.yml", parent_role=None)
        assert entry2 is entry1
        assert entry2 is not None
        assert entry2.task_names == ["Single task"]

    def test_discover_include_missing_file(self, tmp_path: Path) -> None:
        """Missing include file returns None."""
        playbook = tmp_path / "site.yml"
        playbook.touch()
        state = RunState(playbook=str(playbook))
        entry = _discover_include(state, "nonexistent.yml", parent_role=None)
        assert entry is None

    def test_discover_include_with_parent_role(self, tmp_path: Path) -> None:
        """Parent role is recorded in the cache entry."""
        playbook = tmp_path / "site.yml"
        playbook.touch()
        included = tmp_path / "tasks.yml"
        included.write_text("""
- name: Child task
  debug:
    msg: hi
""")
        state = RunState(playbook=str(playbook))
        entry = _discover_include(state, "tasks.yml", parent_role="parent_role")
        assert entry is not None
        assert entry.role == "parent_role"


# ---------------------------------------------------------------------------
# _discover_role
# ---------------------------------------------------------------------------


class TestDiscoverRole:
    """Unit tests for _discover_role()."""

    def test_discover_role_successful(self, tmp_path: Path) -> None:
        """Successful role parsing creates and returns a RoleCacheEntry."""
        playbook = tmp_path / "site.yml"
        playbook.touch()
        role_tasks = tmp_path / "roles" / "test_role" / "tasks"
        role_tasks.mkdir(parents=True)
        (role_tasks / "main.yml").write_text("""
- name: Install things
  apt:
    name: stuff
- name: Configure things
  template:
    src: conf.j2
    dest: /etc/conf
""")
        state = RunState(playbook=str(playbook))
        entry = _discover_role(state, "test_role")
        assert entry is not None
        assert entry.role_name == "test_role"
        assert entry.task_names == ["Install things", "Configure things"]

    def test_discover_role_dedup(self, tmp_path: Path) -> None:
        """Second call returns the cached role entry."""
        playbook = tmp_path / "site.yml"
        playbook.touch()
        role_tasks = tmp_path / "roles" / "dup_role" / "tasks"
        role_tasks.mkdir(parents=True)
        main_file = role_tasks / "main.yml"
        main_file.write_text("""
- name: Only task
  debug:
    msg: once
""")
        state = RunState(playbook=str(playbook))
        entry1 = _discover_role(state, "dup_role")
        # Wipe file so re-parse would fail
        main_file.unlink()
        entry2 = _discover_role(state, "dup_role")
        assert entry2 is entry1
        assert entry2 is not None
        assert entry2.task_names == ["Only task"]

    def test_discover_role_missing_role(self, tmp_path: Path) -> None:
        """Missing role directory returns None."""
        playbook = tmp_path / "site.yml"
        playbook.touch()
        state = RunState(playbook=str(playbook))
        entry = _discover_role(state, "nonexistent_role")
        assert entry is None

    def test_discover_role_case_insensitive_cache_key(self, tmp_path: Path) -> None:
        """Role name is lowercased and stripped for the cache key."""
        playbook = tmp_path / "site.yml"
        playbook.touch()
        role_tasks = tmp_path / "roles" / "MixedCase" / "tasks"
        role_tasks.mkdir(parents=True)
        (role_tasks / "main.yml").write_text("""
- name: Mixed case task
  debug:
    msg: test
""")
        state = RunState(playbook=str(playbook))
        entry1 = _discover_role(state, "MixedCase")
        assert entry1 is not None
        # Call with different casing — must hit the cache
        entry2 = _discover_role(state, "MIXEDCASE")
        assert entry2 is entry1

    def test_discover_role_strips_whitespace(self, tmp_path: Path) -> None:
        """Role name whitespace is stripped for cache key normalisation.

        _discover_role strips only the cache key — the directory lookup
        still uses the original (unstripped) role_name. In practice,
        filesystem role names never have leading/trailing whitespace,
        so this test verifies the cache key normalisation only.
        """
        playbook = tmp_path / "site.yml"
        playbook.touch()
        role_tasks = tmp_path / "roles" / "spaced_role" / "tasks"
        role_tasks.mkdir(parents=True)
        (role_tasks / "main.yml").write_text("""
- name: Spaced task
  debug:
    msg: test
""")
        state = RunState(playbook=str(playbook))
        entry1 = _discover_role(state, "spaced_role")
        assert entry1 is not None
        assert entry1.role_name == "spaced_role"
        # Same role with whitespace around the name — must hit cache
        # (cache key is lowercased-and-stripped, so "  spaced_role  "
        # resolves to "spaced_role").
        entry2 = _discover_role(state, "  SPACED_ROLE  ")
        assert entry2 is entry1


# ---------------------------------------------------------------------------
# discover_include_with_runtime_path
# ---------------------------------------------------------------------------


class TestDiscoverIncludeWithRuntimePath:
    """Unit tests for discover_include_with_runtime_path()."""

    def test_discover_include_with_runtime_path_strips_line_number(self, tmp_path: Path) -> None:
        """task.path format 'file.yml:2' extracts 'file.yml'."""
        playbook = tmp_path / "site.yml"
        playbook.touch()
        included = tmp_path / "tasks.yml"
        included.write_text("""
- name: Runtime task
  debug:
    msg: found
""")
        state = RunState(playbook=str(playbook))
        entry = discover_include_with_runtime_path(state, "tasks.yml:3", parent_role=None)
        assert entry is not None
        assert entry.task_names == ["Runtime task"]

    def test_discover_include_with_runtime_path_no_line_number(self, tmp_path: Path) -> None:
        """Path without line number works unchanged."""
        playbook = tmp_path / "site.yml"
        playbook.touch()
        included = tmp_path / "plain.yml"
        included.write_text("""
- name: Plain task
  debug:
    msg: ok
""")
        state = RunState(playbook=str(playbook))
        entry = discover_include_with_runtime_path(state, "plain.yml", parent_role=None)
        assert entry is not None
        assert entry.task_names == ["Plain task"]

    def test_discover_include_with_runtime_path_missing_file(self, tmp_path: Path) -> None:
        """Missing file returns None even with runtime path format."""
        playbook = tmp_path / "site.yml"
        playbook.touch()
        state = RunState(playbook=str(playbook))
        entry = discover_include_with_runtime_path(state, "missing.yml:42", parent_role=None)
        assert entry is None


# ---------------------------------------------------------------------------
# resolve_includes_from_playbook
# ---------------------------------------------------------------------------


class TestResolveIncludesFromPlaybook:
    """Unit tests for resolve_includes_from_playbook()."""

    def test_resolve_includes_from_playbook_finds_static_include(self, tmp_path: Path) -> None:
        """Static include_tasks in a playbook are discovered and cached."""
        playbook = tmp_path / "site.yml"
        included = tmp_path / "setup.yml"
        included.write_text("""
- name: Install packages
  apt:
    name: nginx
- name: Start service
  service:
    name: nginx
    state: started
""")
        playbook.write_text("""
- hosts: all
  tasks:
    - include_tasks: setup.yml
    - debug:
        msg: done
""")
        cache: dict[str, IncludeCacheEntry] = {}
        resolve_includes_from_playbook(
            str(playbook),
            definitions=[],
            cache=cache,
        )
        resolved_key = str(included.resolve())
        assert resolved_key in cache
        assert cache[resolved_key].task_names == ["Install packages", "Start service"]

    def test_resolve_includes_from_playbook_skips_jinja2_paths(self, tmp_path: Path) -> None:
        """Include paths containing '{{' are skipped."""
        playbook = tmp_path / "site.yml"
        playbook.write_text("""
- hosts: all
  tasks:
    - include_tasks: "{{ env }}.yml"
    - include_tasks: "common/{{ role_prefix }}_setup.yml"
    - debug:
        msg: no includes
""")
        cache: dict[str, IncludeCacheEntry] = {}
        resolve_includes_from_playbook(
            str(playbook),
            definitions=[],
            cache=cache,
        )
        assert len(cache) == 0

    def test_resolve_includes_from_playbook_missing_playbook(self, tmp_path: Path) -> None:
        """Missing playbook clears the cache dict."""
        cache: dict[str, IncludeCacheEntry] = {
            "stale": IncludeCacheEntry(
                path="/stale",
                task_names=["old"],
                role=None,
                parsed_at=datetime.now(timezone.utc),
            )
        }
        resolve_includes_from_playbook(
            str(tmp_path / "does_not_exist.yml"),
            definitions=[],
            cache=cache,
        )
        assert len(cache) == 0

    def test_resolve_includes_from_playbook_scans_all_sections(self, tmp_path: Path) -> None:
        """Includes in pre_tasks, post_tasks, and handlers are all found."""
        playbook = tmp_path / "site.yml"
        (tmp_path / "pre.yml").write_text("- name: Pre task\n  debug:\n    msg: pre\n")
        (tmp_path / "post.yml").write_text("- name: Post task\n  debug:\n    msg: post\n")
        (tmp_path / "handler_tasks.yml").write_text(
            "- name: Handler task\n  debug:\n    msg: handler\n"
        )
        playbook.write_text("""
- hosts: all
  pre_tasks:
    - include_tasks: pre.yml
  tasks:
    - debug:
        msg: main
  post_tasks:
    - include_tasks: post.yml
  handlers:
    - include_tasks: handler_tasks.yml
""")
        cache: dict[str, IncludeCacheEntry] = {}
        resolve_includes_from_playbook(str(playbook), definitions=[], cache=cache)
        assert len(cache) == 3
        names_by_key = {k: v.task_names for k, v in cache.items()}
        assert any(names == ["Pre task"] for names in names_by_key.values())
        assert any(names == ["Post task"] for names in names_by_key.values())
        assert any(names == ["Handler task"] for names in names_by_key.values())

    def test_resolve_includes_from_playbook_deduplicates(self, tmp_path: Path) -> None:
        """Same include_tasks referenced multiple times only parsed once."""
        playbook = tmp_path / "site.yml"
        included = tmp_path / "common.yml"
        included.write_text("- name: Shared task\n  debug:\n    msg: shared\n")
        playbook.write_text("""
- hosts: webservers
  tasks:
    - include_tasks: common.yml
- hosts: dbservers
  tasks:
    - include_tasks: common.yml
""")
        cache: dict[str, IncludeCacheEntry] = {}
        resolve_includes_from_playbook(str(playbook), definitions=[], cache=cache)
        assert len(cache) == 1

    def test_resolve_includes_from_playbook_nested_blocks(self, tmp_path: Path) -> None:
        """Includes inside block/rescue/always subsections are found."""
        playbook = tmp_path / "site.yml"
        (tmp_path / "block_include.yml").write_text(
            "- name: Block task\n  debug:\n    msg: block\n"
        )
        (tmp_path / "rescue_include.yml").write_text(
            "- name: Rescue task\n  debug:\n    msg: rescue\n"
        )
        (tmp_path / "always_include.yml").write_text(
            "- name: Always task\n  debug:\n    msg: always\n"
        )
        playbook.write_text("""
- hosts: all
  tasks:
    - block:
        - debug:
            msg: main block
        - include_tasks: block_include.yml
      rescue:
        - debug:
            msg: rescue block
        - include_tasks: rescue_include.yml
      always:
        - debug:
            msg: always block
        - include_tasks: always_include.yml
""")
        cache: dict[str, IncludeCacheEntry] = {}
        resolve_includes_from_playbook(str(playbook), definitions=[], cache=cache)
        assert len(cache) == 3

    def test_resolve_includes_from_playbook_non_dict_entries_skipped(self, tmp_path: Path) -> None:
        """Non-dict entries in the playbook list are safely skipped."""
        playbook = tmp_path / "site.yml"
        playbook.write_text("""
- hosts: all
  tasks:
    - debug:
        msg: hello
- 42
- "just a string"
""")
        cache: dict[str, IncludeCacheEntry] = {}
        resolve_includes_from_playbook(str(playbook), definitions=[], cache=cache)
        # Should not raise — just no includes found
        assert len(cache) == 0


# ---------------------------------------------------------------------------
# CacheEntry property tests
# ---------------------------------------------------------------------------


class TestCacheEntryProperties:
    """Unit tests for IncludeCacheEntry.task_count and RoleCacheEntry.task_count."""

    def test_include_cache_entry_task_count(self) -> None:
        """task_count property equals len(task_names)."""
        entry = IncludeCacheEntry(
            path="/tmp/test.yml",
            task_names=["A", "B", "C"],
            role=None,
            parsed_at=datetime.now(timezone.utc),
        )
        assert entry.task_count == 3

    def test_include_cache_entry_task_count_empty(self) -> None:
        """Empty task_names yields task_count of 0."""
        entry = IncludeCacheEntry(
            path="/tmp/empty.yml",
            task_names=[],
            role=None,
            parsed_at=datetime.now(timezone.utc),
        )
        assert entry.task_count == 0

    def test_role_cache_entry_task_count(self) -> None:
        """task_count property equals len(task_names)."""
        entry = RoleCacheEntry(
            role_name="test_role",
            task_names=["Install", "Configure", "Start", "Verify"],
        )
        assert entry.task_count == 4

    def test_role_cache_entry_task_count_empty(self) -> None:
        """Empty task_names yields task_count of 0."""
        entry = RoleCacheEntry(role_name="empty_role", task_names=[])
        assert entry.task_count == 0
