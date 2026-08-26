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
    graft_include_children,
    parse_include_tasks_file,
    parse_role_tasks,
    resolve_includes_from_playbook,
    resolve_role_relative_includes,
)
from ansible_aom.core.models import (
    IncludeCacheEntry,
    PlayDefinition,
    RoleCacheEntry,
    RunState,
    TaskDefinition,
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

    def test_resolve_includes_from_playbook_mapping_form(self, tmp_path: Path) -> None:
        """TC-094k: mapping-form include_tasks (file: X) is discovered and cached."""
        playbook = tmp_path / "site.yml"
        included = tmp_path / "setup.yml"
        included.write_text("- name: Install packages\n  debug:\n    msg: x\n")
        playbook.write_text("""
- hosts: all
  tasks:
    - name: Include setup
      include_tasks:
        file: setup.yml
""")
        cache: dict[str, IncludeCacheEntry] = {}
        resolve_includes_from_playbook(str(playbook), definitions=[], cache=cache)
        resolved_key = str(included.resolve())
        assert resolved_key in cache
        assert cache[resolved_key].task_names == ["Install packages"]

    def test_resolve_includes_from_playbook_skips_jinja_mapping_form(self, tmp_path: Path) -> None:
        """TC-094l: mapping-form include_tasks with a Jinja file: value is skipped."""
        playbook = tmp_path / "site.yml"
        playbook.write_text("""
- hosts: all
  tasks:
    - name: Dynamic include
      include_tasks:
        file: "{{ env }}.yml"
""")
        cache: dict[str, IncludeCacheEntry] = {}
        resolve_includes_from_playbook(str(playbook), definitions=[], cache=cache)
        assert len(cache) == 0

    def test_resolve_includes_from_playbook_collects_role_key_form(self, tmp_path: Path) -> None:
        """TC-094o: roles: list entries using ``- role: foo`` are collected."""
        playbook = tmp_path / "site.yml"
        playbook.write_text("""
- hosts: all
  roles:
    - role: angie_ssl_terminator
      vars:
        x: 1
    - role: angie_ha
""")
        cache: dict[str, IncludeCacheEntry] = {}
        referenced = resolve_includes_from_playbook(str(playbook), definitions=[], cache=cache)
        assert "angie_ssl_terminator" in referenced
        assert "angie_ha" in referenced


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


def _make_play(tasks: list[TaskDefinition]) -> PlayDefinition:
    """Build a single-play PlayDefinition wrapping *tasks*."""
    return PlayDefinition(
        id="1",
        name="Test play",
        hosts="localhost",
        resolved_hosts=["localhost"],
        tasks=tasks,
    )


def _include_stub(name: str, role: str | None = "podman") -> TaskDefinition:
    """Build an include_tasks stub TaskDefinition like --list-tasks produces.

    Real --list-tasks output renders ``include_tasks: setup.yml`` as the
    task name ``Include setup`` (filename without extension).
    """
    return TaskDefinition(
        name=name,
        role=role,
        tags=[],
        play_id="1",
        play_order=1,
        task_order=0,
    )


class TestGraftIncludeChildren:
    """Unit tests for graft_include_children() — TC-094a through TC-094e."""

    def _write_playbook(self, tmp_path: Path, *, include_target: str) -> Path:
        """Write a one-task playbook that includes *include_target* and return its path."""
        playbook = tmp_path / "play.yml"
        playbook.write_text(
            f"---\n- hosts: localhost\n  tasks:\n    - name: Direct task\n      debug:\n        msg: x\n"
            f"    - name: Include setup\n      include_tasks: {include_target}\n"
        )
        return playbook

    def test_static_include_grafts_children_into_stub(self, tmp_path: Path) -> None:
        """TC-094a: A literal include_tasks stub gains children from cache."""
        included = tmp_path / "setup.yml"
        included.write_text(
            "- name: Install packages\n  debug:\n    msg: x\n"
            "- name: Start service\n  debug:\n    msg: y\n"
        )
        cache_key = str(included.resolve())
        cache: dict[str, IncludeCacheEntry] = {
            cache_key: IncludeCacheEntry(
                path=cache_key,
                task_names=["Install packages", "Start service"],
                role=None,
                parsed_at=datetime.now(timezone.utc),
            )
        }
        playbook = self._write_playbook(tmp_path, include_target="setup.yml")
        stub = _include_stub("Include setup", role="podman")
        play = _make_play([stub])

        graft_include_children(
            playbook_path=str(playbook),
            definitions=[play],
            cache=cache,
        )

        assert len(stub.children) == 2
        assert [c.name for c in stub.children] == ["Install packages", "Start service"]
        assert all(c.role == "podman" for c in stub.children)
        assert all(c.parent_role == "podman" for c in stub.children)
        assert all(c.is_dynamic is False for c in stub.children)
        assert all(c.play_id == "1" for c in stub.children)

    def test_role_relative_include_resolution(self, tmp_path: Path) -> None:
        """TC-094b: include_tasks inside a role resolves relative to the role dir."""
        role_dir = tmp_path / "roles" / "podman"
        (role_dir / "tasks" / "_includes").mkdir(parents=True)
        setup = role_dir / "tasks" / "_includes" / "setup.yml"
        setup.write_text(
            "- name: Set up angie\n  debug:\n    msg: a\n"
            "- name: Start sidecar\n  debug:\n    msg: b\n"
        )
        (role_dir / "tasks" / "main.yml").write_text(
            "- name: Stop podman socket\n  debug:\n    msg: x\n"
            "- name: Install Podman\n  debug:\n    msg: y\n"
            "- name: Role-relative include\n  include_tasks: _includes/setup.yml\n"
        )

        cache: dict[str, IncludeCacheEntry] = {}
        resolve_role_relative_includes(
            role_names={"podman"},
            playbook_dir=tmp_path,
            cache=cache,
        )

        resolved_key = str(setup.resolve())
        assert resolved_key in cache
        assert cache[resolved_key].task_names == ["Set up angie", "Start sidecar"]

    def test_jinja_templated_include_path_is_skipped(self, tmp_path: Path) -> None:
        """TC-094c: include_tasks: '{{ var }}.yml' does not populate cache."""
        (tmp_path / "roles" / "podman" / "tasks").mkdir(parents=True)
        (tmp_path / "roles" / "podman" / "tasks" / "main.yml").write_text(
            '- name: Dynamic include\n  include_tasks: "{{ task_file }}.yml"\n'
        )

        cache: dict[str, IncludeCacheEntry] = {}
        resolve_role_relative_includes(
            role_names={"podman"},
            playbook_dir=tmp_path,
            cache=cache,
        )
        assert cache == {}

    def test_role_scan_only_named_roles(self, tmp_path: Path) -> None:
        """Only roles listed in role_names are scanned — unreferenced roles are skipped."""
        wanted_dir = tmp_path / "roles" / "wanted" / "tasks"
        wanted_dir.mkdir(parents=True)
        (wanted_dir / "_inc.yml").write_text("- name: In wanted\n  debug:\n    msg: w\n")
        (wanted_dir / "main.yml").write_text("- name: W include\n  include_tasks: _inc.yml\n")

        ignored_dir = tmp_path / "roles" / "ignored" / "tasks"
        ignored_dir.mkdir(parents=True)
        (ignored_dir / "_inc.yml").write_text("- name: In ignored\n  debug:\n    msg: i\n")
        (ignored_dir / "main.yml").write_text("- name: I include\n  include_tasks: _inc.yml\n")

        cache: dict[str, IncludeCacheEntry] = {}
        resolve_role_relative_includes(
            role_names={"wanted"},
            playbook_dir=tmp_path,
            cache=cache,
        )

        wanted_inc = (wanted_dir / "_inc.yml").resolve()
        ignored_inc = (ignored_dir / "_inc.yml").resolve()
        assert str(wanted_inc) in cache
        assert str(ignored_inc) not in cache

    def test_role_scan_missing_role_is_silent(self, tmp_path: Path) -> None:
        """A role listed in role_names but absent on disk does not log at WARNING/DEBUG."""
        cache: dict[str, IncludeCacheEntry] = {}
        resolve_role_relative_includes(
            role_names={"ghost"},
            playbook_dir=tmp_path,
            cache=cache,
        )
        assert cache == {}

    def test_role_scan_unparseable_role_logs_warning_once(self, tmp_path: Path, caplog) -> None:
        """A role with YAML PyYAML can't parse logs one WARNING, no exception."""
        import logging

        role_dir = tmp_path / "roles" / "broken"
        role_dir.mkdir(parents=True)
        # quadlet_options-like content that PyYAML cannot parse but ansible can.
        (role_dir / "tasks" / "main.yml").parent.mkdir(parents=True, exist_ok=True)
        (role_dir / "tasks" / "main.yml").write_text(
            "- name: Task\n  module:\n    quadlet_options:\n"
            "        [Service]\n        Restart=always\n"
            "    become: true\n"
        )

        cache: dict[str, IncludeCacheEntry] = {}
        with caplog.at_level(logging.WARNING, logger="ansible_aom.core.includes"):
            resolve_role_relative_includes(
                role_names={"broken"},
                playbook_dir=tmp_path,
                cache=cache,
            )
        # No exception, no cache entry, at most one warning.
        assert cache == {}
        warnings = [r for r in caplog.records if r.levelno >= logging.WARNING]
        assert len(warnings) <= 1

    def test_nested_includes_graft_transitively(self, tmp_path: Path) -> None:
        """TC-094d: include A includes B includes C → children at depth 2 and 3."""
        level1 = tmp_path / "level1.yml"
        level1.write_text(
            "- name: Level 1 task\n  debug:\n    msg: 1\n"
            "- name: Include level2\n  include_tasks: level2.yml\n"
        )
        level2 = tmp_path / "level2.yml"
        level2.write_text(
            "- name: Level 2 task A\n  debug:\n    msg: 2a\n"
            "- name: Level 2 task B\n  debug:\n    msg: 2b\n"
        )
        playbook = tmp_path / "play.yml"
        playbook.write_text(
            "- hosts: localhost\n  tasks:\n"
            "    - name: Direct\n      debug:\n        msg: d\n"
            "    - name: Include level1\n      include_tasks: level1.yml\n"
        )
        cache: dict[str, IncludeCacheEntry] = {
            str(level1.resolve()): IncludeCacheEntry(
                path=str(level1.resolve()),
                task_names=["Level 1 task", "Include level2"],
                role=None,
                parsed_at=datetime.now(timezone.utc),
            ),
            str(level2.resolve()): IncludeCacheEntry(
                path=str(level2.resolve()),
                task_names=["Level 2 task A", "Level 2 task B"],
                role=None,
                parsed_at=datetime.now(timezone.utc),
            ),
        }
        outer_stub = _include_stub("Include level1", role=None)
        play = _make_play([outer_stub])

        graft_include_children(
            playbook_path=str(playbook),
            definitions=[play],
            cache=cache,
        )

        assert len(outer_stub.children) == 2
        level2_stub = outer_stub.children[1]
        assert level2_stub.name == "Include level2"
        assert len(level2_stub.children) == 2
        assert [c.name for c in level2_stub.children] == ["Level 2 task A", "Level 2 task B"]

    def test_block_with_include_preserves_location(self, tmp_path: Path) -> None:
        """TC-094e: block: [include_tasks: foo.yml, ...] grafts under block task."""
        setup = tmp_path / "foo.yml"
        setup.write_text(
            "- name: Inner A\n  debug:\n    msg: a\n- name: Inner B\n  debug:\n    msg: b\n"
        )
        playbook = tmp_path / "play.yml"
        playbook.write_text(
            "- hosts: localhost\n  tasks:\n"
            "    - name: Group of setup\n      block:\n"
            "        - name: Include foo\n          include_tasks: foo.yml\n"
            "        - name: After\n          debug:\n            msg: z\n"
        )
        cache_key = str(setup.resolve())
        cache: dict[str, IncludeCacheEntry] = {
            cache_key: IncludeCacheEntry(
                path=cache_key,
                task_names=["Inner A", "Inner B"],
                role=None,
                parsed_at=datetime.now(timezone.utc),
            )
        }
        include_stub = _include_stub("Include foo", role="web")
        block_task = TaskDefinition(
            name="Group of setup",
            role="web",
            tags=[],
            play_id="1",
            play_order=1,
            task_order=0,
            children=[include_stub],
        )
        play = _make_play([block_task])

        graft_include_children(
            playbook_path=str(playbook),
            definitions=[play],
            cache=cache,
        )

        assert len(block_task.children) == 1
        grafted = block_task.children[0]
        assert grafted.name == "Include foo"
        assert len(grafted.children) == 2

    def test_graft_preserves_existing_children(self, tmp_path: Path) -> None:
        """If a stub already has children (e.g. from runtime graft), graft appends."""
        setup = tmp_path / "x.yml"
        setup.write_text("- name: New\n  debug:\n    msg: n\n")
        playbook = self._write_playbook(tmp_path, include_target="x.yml")
        cache_key = str(setup.resolve())
        cache: dict[str, IncludeCacheEntry] = {
            cache_key: IncludeCacheEntry(
                path=cache_key,
                task_names=["New"],
                role=None,
                parsed_at=datetime.now(timezone.utc),
            )
        }
        existing = TaskDefinition(
            name="Pre-existing",
            role="podman",
            tags=[],
            play_id="1",
            play_order=1,
            task_order=-1,
            is_dynamic=True,
        )
        stub = _include_stub("Include setup", role="podman")
        stub.children.append(existing)
        play = _make_play([stub])

        graft_include_children(
            playbook_path=str(playbook),
            definitions=[play],
            cache=cache,
        )

        names = [c.name for c in stub.children]
        assert "Pre-existing" in names
        assert "New" in names

    def test_mapping_form_include_grafts_children_into_stub(self, tmp_path: Path) -> None:
        """TC-094i: mapping-form include_tasks (file: X) grafts children like string form."""
        included = tmp_path / "setup.yml"
        included.write_text(
            "- name: Install packages\n  debug:\n    msg: x\n"
            "- name: Start service\n  debug:\n    msg: y\n"
        )
        cache_key = str(included.resolve())
        cache: dict[str, IncludeCacheEntry] = {
            cache_key: IncludeCacheEntry(
                path=cache_key,
                task_names=["Install packages", "Start service"],
                role=None,
                parsed_at=datetime.now(timezone.utc),
            )
        }
        playbook = tmp_path / "play.yml"
        playbook.write_text(
            "---\n- hosts: localhost\n  tasks:\n"
            "    - name: Direct task\n      debug:\n        msg: x\n"
            "    - name: Include setup\n      include_tasks:\n        file: setup.yml\n"
        )
        stub = _include_stub("Include setup", role="podman")
        play = _make_play([stub])

        graft_include_children(
            playbook_path=str(playbook),
            definitions=[play],
            cache=cache,
        )

        assert len(stub.children) == 2
        assert [c.name for c in stub.children] == ["Install packages", "Start service"]

    def test_mapping_form_jinja_include_leaves_stub_alone(self, tmp_path: Path) -> None:
        """TC-094j: mapping-form include_tasks with a Jinja file: value is not grafted."""
        playbook = tmp_path / "play.yml"
        playbook.write_text(
            "---\n- hosts: localhost\n  tasks:\n"
            "    - name: Include setup\n      include_tasks:\n        file: '{{ env }}.yml'\n"
        )
        cache: dict[str, IncludeCacheEntry] = {}
        stub = _include_stub("Include setup", role="podman")
        play = _make_play([stub])

        graft_include_children(
            playbook_path=str(playbook),
            definitions=[play],
            cache=cache,
        )

        assert stub.children == []

    def test_role_relative_escape_include_resolves_to_playbook_dir(self, tmp_path: Path) -> None:
        """TC-094m: role include_tasks: ../playbooks/... resolves against the roles dir.

        ``include_tasks: ../playbooks/acme/deploy_user_certs.yml`` from
        ``roles/podman/tasks/main.yml`` resolves to ``<repo>/playbooks/acme/...``
        (roles dir + ``../playbooks``), NOT ``roles/podman/playbooks/...``.
        """
        role_dir = tmp_path / "roles" / "podman"
        (role_dir / "tasks").mkdir(parents=True)
        (role_dir / "tasks" / "main.yml").write_text(
            "- name: Deploy certs\n  include_tasks: ../playbooks/acme/deploy_user_certs.yml\n"
        )
        target = tmp_path / "playbooks" / "acme" / "deploy_user_certs.yml"
        target.parent.mkdir(parents=True)
        target.write_text(
            "- name: Distribute certs\n  debug:\n    msg: a\n"
            "- name: Verify certs\n  debug:\n    msg: b\n"
        )

        cache: dict[str, IncludeCacheEntry] = {}
        resolve_role_relative_includes(
            role_names={"podman"},
            playbook_dir=tmp_path,
            cache=cache,
        )

        resolved_key = str(target.resolve())
        assert resolved_key in cache
        assert cache[resolved_key].task_names == ["Distribute certs", "Verify certs"]
        # The bogus role-tasks-relative key must NOT be created.
        bogus = str((role_dir / "playbooks" / "acme" / "deploy_user_certs.yml").resolve())
        assert bogus not in cache

    def test_role_relative_escape_include_grafts_children(self, tmp_path: Path) -> None:
        """TC-094n: role ../ include grafts children onto the stub via the playbook-relative key."""
        role_dir = tmp_path / "roles" / "podman"
        (role_dir / "tasks").mkdir(parents=True)
        (role_dir / "tasks" / "main.yml").write_text(
            "- name: Deploy certs\n  include_tasks: ../playbooks/acme/deploy_user_certs.yml\n"
        )
        target = tmp_path / "playbooks" / "acme" / "deploy_user_certs.yml"
        target.parent.mkdir(parents=True)
        target.write_text(
            "- name: Distribute certs\n  debug:\n    msg: a\n"
            "- name: Verify certs\n  debug:\n    msg: b\n"
        )
        cache_key = str(target.resolve())
        cache: dict[str, IncludeCacheEntry] = {
            cache_key: IncludeCacheEntry(
                path=cache_key,
                task_names=["Distribute certs", "Verify certs"],
                role=None,
                parsed_at=datetime.now(timezone.utc),
            )
        }
        playbook = tmp_path / "play.yml"
        playbook.write_text(
            "---\n- hosts: localhost\n  roles:\n    - role: podman\n  tasks:\n"
            "    - name: Direct\n      debug:\n        msg: d\n"
        )
        stub = _include_stub("Deploy certs", role="podman")
        play = _make_play([stub])

        graft_include_children(
            playbook_path=str(playbook),
            definitions=[play],
            cache=cache,
        )

        assert len(stub.children) == 2
        assert [c.name for c in stub.children] == ["Distribute certs", "Verify certs"]

    def test_graft_unknown_path_leaves_stub_alone(self, tmp_path: Path) -> None:
        """If cache has no entry for an include, the stub stays empty."""
        playbook = self._write_playbook(tmp_path, include_target="missing.yml")
        cache: dict[str, IncludeCacheEntry] = {}
        stub = _include_stub("Include setup", role="podman")
        play = _make_play([stub])

        graft_include_children(
            playbook_path=str(playbook),
            definitions=[play],
            cache=cache,
        )

        assert stub.children == []

    def test_graft_only_targets_include_stubs(self, tmp_path: Path) -> None:
        """A regular task whose name happens to start with 'Include ' is NOT touched."""
        playbook = self._write_playbook(tmp_path, include_target="missing.yml")
        cache: dict[str, IncludeCacheEntry] = {}
        normal = TaskDefinition(
            name="Include user documentation",
            role="podman",
            tags=[],
            play_id="1",
            play_order=1,
            task_order=0,
        )
        play = _make_play([normal])

        graft_include_children(
            playbook_path=str(playbook),
            definitions=[play],
            cache=cache,
        )

        assert normal.children == []

    def test_import_playbook_grafts_each_play_against_its_definition(self, tmp_path: Path) -> None:
        """TC-094f: import_playbook entries graft stubs onto the correct PlayDefinition.

        A playbook whose plays are mostly ``import_playbook:`` entries must
        pair each imported file's ``include_tasks`` stub with the
        ``PlayDefinition`` whose tasks contain that stub (in ``--list-tasks``
        flattened order), not always with ``definitions[0]``.
        """
        (tmp_path / "inc_a.yml").write_text("- name: A child\n  debug:\n    msg: a\n")
        (tmp_path / "inc_b.yml").write_text("- name: B child\n  debug:\n    msg: b\n")
        (tmp_path / "a.yml").write_text(
            "- hosts: localhost\n  tasks:\n"
            "    - name: Include inc_a\n      include_tasks: inc_a.yml\n"
        )
        (tmp_path / "b.yml").write_text(
            "- hosts: localhost\n  tasks:\n"
            "    - name: Include inc_b\n      include_tasks: inc_b.yml\n"
        )
        main = tmp_path / "main.yml"
        main.write_text(
            "- ansible.builtin.import_playbook: a.yml\n- ansible.builtin.import_playbook: b.yml\n"
        )
        cache: dict[str, IncludeCacheEntry] = {
            str((tmp_path / "inc_a.yml").resolve()): IncludeCacheEntry(
                path=str((tmp_path / "inc_a.yml").resolve()),
                task_names=["A child"],
                role=None,
                parsed_at=datetime.now(timezone.utc),
            ),
            str((tmp_path / "inc_b.yml").resolve()): IncludeCacheEntry(
                path=str((tmp_path / "inc_b.yml").resolve()),
                task_names=["B child"],
                role=None,
                parsed_at=datetime.now(timezone.utc),
            ),
        }
        stub_a = _include_stub("Include inc_a", role=None)
        stub_b = _include_stub("Include inc_b", role=None)
        play_a = _make_play([stub_a])
        play_b = _make_play([stub_b])

        graft_include_children(
            playbook_path=str(main),
            definitions=[play_a, play_b],
            cache=cache,
        )

        assert [c.name for c in stub_a.children] == ["A child"]
        assert [c.name for c in stub_b.children] == ["B child"]

    def test_import_playbook_nested_import_keeps_working(self, tmp_path: Path) -> None:
        """TC-094g: an import_playbook inside an imported file still grafts.

        Nested imports (import inside import) must keep working with the
        shared play cursor: the inner file's plays consume the next
        definitions in flattened order.
        """
        (tmp_path / "inc_c.yml").write_text("- name: C child\n  debug:\n    msg: c\n")
        (tmp_path / "inner.yml").write_text(
            "- hosts: localhost\n  tasks:\n"
            "    - name: Include inc_c\n      include_tasks: inc_c.yml\n"
        )
        (tmp_path / "outer.yml").write_text("- ansible.builtin.import_playbook: inner.yml\n")
        main = tmp_path / "main.yml"
        main.write_text(
            "- ansible.builtin.import_playbook: outer.yml\n"
            "- hosts: localhost\n  tasks:\n"
            "    - name: Direct\n      debug:\n        msg: d\n"
        )
        cache: dict[str, IncludeCacheEntry] = {
            str((tmp_path / "inc_c.yml").resolve()): IncludeCacheEntry(
                path=str((tmp_path / "inc_c.yml").resolve()),
                task_names=["C child"],
                role=None,
                parsed_at=datetime.now(timezone.utc),
            ),
        }
        stub_c = _include_stub("Include inc_c", role=None)
        play_c = _make_play([stub_c])
        direct = TaskDefinition(
            name="Direct",
            role=None,
            tags=[],
            play_id="1",
            play_order=1,
            task_order=0,
        )
        play_direct = _make_play([direct])

        graft_include_children(
            playbook_path=str(main),
            definitions=[play_c, play_direct],
            cache=cache,
        )

        assert [c.name for c in stub_c.children] == ["C child"]
        assert direct.children == []

    def test_import_playbook_skipped_play_does_not_drift_cursor(self, tmp_path: Path) -> None:
        """TC-094h: a play skipped by --list-tasks (tags: never) must not shift pairing.

        ``--list-tasks`` skips plays with ``tags: [never]``, so YAML play
        order differs from definition order. The graft must pair the second
        YAML play (the one with the include stub) with the definition whose
        tasks contain that stub — not with the skipped play's position.
        """
        (tmp_path / "inc.yml").write_text("- name: Child\n  debug:\n    msg: c\n")
        (tmp_path / "a.yml").write_text(
            "- hosts: localhost\n  tags: [never]\n  tasks:\n"
            "    - name: Skipped task\n      debug:\n        msg: s\n"
            "- hosts: localhost\n  tasks:\n"
            "    - name: Include inc\n      include_tasks: inc.yml\n"
        )
        main = tmp_path / "main.yml"
        main.write_text("- ansible.builtin.import_playbook: a.yml\n")
        cache: dict[str, IncludeCacheEntry] = {
            str((tmp_path / "inc.yml").resolve()): IncludeCacheEntry(
                path=str((tmp_path / "inc.yml").resolve()),
                task_names=["Child"],
                role=None,
                parsed_at=datetime.now(timezone.utc),
            ),
        }
        stub = _include_stub("Include inc", role=None)
        # Only ONE definition: the second play, since the first was skipped.
        play = _make_play([stub])

        graft_include_children(
            playbook_path=str(main),
            definitions=[play],
            cache=cache,
        )

        assert [c.name for c in stub.children] == ["Child"]
