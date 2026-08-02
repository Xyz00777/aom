"""Integration tests for include/import/role task variants.

Covers TC-330 through TC-338: import_tasks (static expansion),
include_tasks (dynamic grafting), include_role, nested includes,
dynamic path includes, and role keyword at play level.

All tests require a real ansible-playbook and ansible.posix collection.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "ansible"


def _ansible_collection_paths() -> list[str]:
    """Search-path entries reported by ``ansible-galaxy collection list``.

    We republish them into the test subprocess's ``ANSIBLE_COLLECTIONS_PATH``
    so the JSONL callback resolves even when HOME has been redirected to a
    temp dir.
    """
    try:
        result = subprocess.run(
            ["ansible-galaxy", "collection", "list"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except FileNotFoundError, subprocess.TimeoutExpired:
        return []
    if result.returncode != 0:
        return []
    paths: list[str] = []
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("# /"):
            paths.append(stripped[2:])
    # Include known Nix collection paths not discoverable from the venv.
    nix_paths = os.environ.get("ANSIBLE_COLLECTIONS_PATH", "")
    if nix_paths:
        for p in nix_paths.split(":"):
            if p and p not in paths:
                paths.append(p)
    return paths


def _has_ansible_posix() -> bool:
    """True if the ``ansible.posix`` collection is installed and discoverable."""
    env = os.environ.copy()
    # The venv's ansible-galaxy may not see Nix-installed collections;
    # republish any ANSIBLE_COLLECTIONS_PATH from the parent env.
    nix_paths = os.environ.get("ANSIBLE_COLLECTIONS_PATH", "")
    if nix_paths:
        env["ANSIBLE_COLLECTIONS_PATH"] = nix_paths
    try:
        result = subprocess.run(
            ["ansible-galaxy", "collection", "list", "ansible.posix"],
            capture_output=True,
            text=True,
            timeout=15,
            env=env,
        )
    except FileNotFoundError, subprocess.TimeoutExpired:
        return False
    if result.returncode != 0:
        return False
    return "ansible.posix" in result.stdout


_NEEDS_ANSIBLE = pytest.mark.skipif(
    shutil.which("ansible-playbook") is None or not _has_ansible_posix(),
    reason="ansible-playbook or ansible.posix collection unavailable",
)


def _run_aom(
    playbook: Path,
    home_dir: Path,
    *extra_args: str,
) -> subprocess.CompletedProcess[str]:
    """Spawn ``python -m ansible_aom <playbook>`` against a sandboxed HOME.

    Extra args after the baseline ``-i localhost, -c local`` are forwarded
    to ansible-playbook (e.g. ``-e task_file=...``).
    """
    env = os.environ.copy()
    env["HOME"] = str(home_dir)
    collection_paths = _ansible_collection_paths()
    if collection_paths:
        env["ANSIBLE_COLLECTIONS_PATH"] = ":".join(collection_paths)
    cmd = [
        sys.executable,
        "-m",
        "ansible_aom",
        str(playbook),
        "-i",
        "localhost,",
        "-c",
        "local",
    ]
    if extra_args:
        cmd.extend(extra_args)
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )


@_NEEDS_ANSIBLE
class TestImportTasksTree:
    """TC-330 / TC-331: import_tasks tree rendering and counter accuracy."""

    def test_imported_tasks_appear_in_output(self, tmp_path: Path) -> None:
        """TC-330: import_tasks are expanded — all task names visible."""
        result = _run_aom(FIXTURES_DIR / "with_import.yml", tmp_path)

        assert result.returncode == 0, (
            f"aom returned {result.returncode}\n"
            f"--- stdout ---\n{result.stdout}\n"
            f"--- stderr ---\n{result.stderr}"
        )

        assert "Task before import" in result.stdout
        assert "Imported task 1" in result.stdout
        assert "Imported task 2" in result.stdout
        assert "Task after import" in result.stdout

    def test_import_tasks_counter(self, tmp_path: Path) -> None:
        """TC-331: import_tasks counter = 4 runtime tasks."""
        result = _run_aom(FIXTURES_DIR / "with_import.yml", tmp_path)

        assert result.returncode == 0
        assert "4/4 tasks" in result.stdout


@_NEEDS_ANSIBLE
class TestIncludeTasksDynamic:
    """TC-332 / TC-338: include_tasks dynamic grafting and counter accuracy."""

    def test_dynamic_include_children_appear(self, tmp_path: Path) -> None:
        """TC-332: dynamic include children appear with status icons."""
        result = _run_aom(FIXTURES_DIR / "with_include.yml", tmp_path)

        assert result.returncode == 0
        assert "Included task 1" in result.stdout
        assert "Included task 2" in result.stdout
        assert "●" in result.stdout or "*" in result.stdout, (
            "Expected status icons in compact output"
        )

    def test_completion_counter_matches_runtime_tasks(self, tmp_path: Path) -> None:
        """TC-338: completion counter = total runtime tasks."""
        result = _run_aom(FIXTURES_DIR / "with_include.yml", tmp_path)

        assert result.returncode == 0
        assert "4/4 tasks" in result.stdout


@_NEEDS_ANSIBLE
class TestNestedInclude:
    """TC-333: nested include_tasks — all 3 levels in tree output."""

    def test_all_three_levels_visible(self, tmp_path: Path) -> None:
        """TC-333: verify all 3 nesting levels appear in output."""
        result = _run_aom(FIXTURES_DIR / "with_nested_include.yml", tmp_path)

        assert result.returncode == 0, (
            f"aom returned {result.returncode}\n"
            f"--- stdout ---\n{result.stdout}\n"
            f"--- stderr ---\n{result.stderr}"
        )

        assert "Level 1 task" in result.stdout
        assert "Level 2 task A" in result.stdout
        assert "Level 2 task B" in result.stdout
        assert "6/6 tasks" in result.stdout


@_NEEDS_ANSIBLE
class TestIncludeRole:
    """TC-334: include_role — dynamic role tasks with role grouping."""

    def test_dynamic_role_tasks_with_grouping(self, tmp_path: Path) -> None:
        """TC-334: dynamic role tasks appear with role grouping in output."""
        result = _run_aom(FIXTURES_DIR / "with_include_role.yml", tmp_path)

        assert result.returncode == 0, (
            f"aom returned {result.returncode}\n"
            f"--- stdout ---\n{result.stdout}\n"
            f"--- stderr ---\n{result.stderr}"
        )

        assert "Role task 1" in result.stdout
        assert "Role task 2" in result.stdout
        assert "Role task 3" in result.stdout
        assert "Task before role" in result.stdout
        assert "Task after role" in result.stdout
        assert "6/6 tasks" in result.stdout


@_NEEDS_ANSIBLE
class TestStaticRoleKeyword:
    """TC-335: Counter accuracy for static ``roles:`` keyword at play level."""

    def test_static_role_counter(self, tmp_path: Path) -> None:
        """TC-335: verify counter accuracy for static roles keyword."""
        result = _run_aom(FIXTURES_DIR / "with_role.yml", tmp_path)

        assert result.returncode == 0
        assert "Role task 1" in result.stdout
        assert "Role task 2" in result.stdout
        assert "Role task 3" in result.stdout
        assert "Task after role" in result.stdout
        assert "4/4 tasks" in result.stdout


@_NEEDS_ANSIBLE
class TestDynamicIncludePath:
    """TC-336: Dynamic path include — ``include_tasks: \"{{ task_file }}\"``."""

    def test_dynamic_path_include(self, tmp_path: Path) -> None:
        """TC-336: dynamic include path works, tasks grafted one-by-one."""
        result = _run_aom(
            FIXTURES_DIR / "with_dynamic_include.yml",
            tmp_path,
            "-e",
            "task_file=dynamic_target.yml",
        )

        assert result.returncode == 0, (
            f"aom returned {result.returncode}\n"
            f"--- stdout ---\n{result.stdout}\n"
            f"--- stderr ---\n{result.stderr}"
        )

        assert "Dynamic task A" in result.stdout
        assert "Dynamic task B" in result.stdout
        assert "Dynamic task C" in result.stdout
        assert "4/4 tasks" in result.stdout


@_NEEDS_ANSIBLE
class TestMultiPlayCrossPlay:
    """TC-337: Multi-play playbook — cross-play counters are correct."""

    def test_cross_play_counters(self, tmp_path: Path) -> None:
        """TC-337: verify cross-play counters for multi_play.yml."""
        result = _run_aom(FIXTURES_DIR / "multi_play.yml", tmp_path)

        assert result.returncode == 0, (
            f"aom returned {result.returncode}\n"
            f"--- stdout ---\n{result.stdout}\n"
            f"--- stderr ---\n{result.stderr}"
        )

        assert "Task in play 1" in result.stdout
        assert "Task in play 2" in result.stdout
        assert "Another task in play 2" in result.stdout
        assert "3/3 tasks" in result.stdout
