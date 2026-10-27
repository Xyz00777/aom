"""Unit tests for core.run_config — argv normalization for the history key."""

from __future__ import annotations

from pathlib import Path

from ansible_aom.core.run_config import (
    RunConfigKey,
    build_run_config_key,
    resolve_stored_playbook,
)


def test_key_uses_resolved_playbook_path(tmp_path: Path) -> None:
    pb = tmp_path / "site.yml"
    pb.write_text("")
    key = build_run_config_key(playbook=str(pb), ansible_args=[])
    assert key.playbook == str(pb.resolve())


def test_key_ignores_verbosity_flags(tmp_path: Path) -> None:
    pb = tmp_path / "p.yml"
    pb.write_text("")
    a = build_run_config_key(playbook=str(pb), ansible_args=["-v"])
    b = build_run_config_key(playbook=str(pb), ansible_args=["-vvv"])
    c = build_run_config_key(playbook=str(pb), ansible_args=[])
    assert a == b == c


def test_key_inventory_order_matters(tmp_path: Path) -> None:
    pb = tmp_path / "p.yml"
    pb.write_text("")
    a = build_run_config_key(playbook=str(pb), ansible_args=["-i", "a.ini", "-i", "b.ini"])
    b = build_run_config_key(playbook=str(pb), ansible_args=["-i", "b.ini", "-i", "a.ini"])
    assert a != b


def test_key_tags_are_sorted(tmp_path: Path) -> None:
    pb = tmp_path / "p.yml"
    pb.write_text("")
    a = build_run_config_key(playbook=str(pb), ansible_args=["--tags", "web,db"])
    b = build_run_config_key(playbook=str(pb), ansible_args=["--tags", "db,web"])
    assert a == b
    assert a.tags == ("db", "web")


def test_key_skip_tags_are_sorted(tmp_path: Path) -> None:
    pb = tmp_path / "p.yml"
    pb.write_text("")
    a = build_run_config_key(playbook=str(pb), ansible_args=["--skip-tags", "x,y"])
    b = build_run_config_key(playbook=str(pb), ansible_args=["--skip-tags", "y,x"])
    assert a == b


def test_key_extra_vars_are_sorted(tmp_path: Path) -> None:
    pb = tmp_path / "p.yml"
    pb.write_text("")
    a = build_run_config_key(playbook=str(pb), ansible_args=["-e", "a=1", "-e", "b=2"])
    b = build_run_config_key(playbook=str(pb), ansible_args=["-e", "b=2", "-e", "a=1"])
    assert a == b


def test_key_check_and_diff_are_distinct(tmp_path: Path) -> None:
    pb = tmp_path / "p.yml"
    pb.write_text("")
    plain = build_run_config_key(playbook=str(pb), ansible_args=[])
    check = build_run_config_key(playbook=str(pb), ansible_args=["--check"])
    diff = build_run_config_key(playbook=str(pb), ansible_args=["--diff"])
    both = build_run_config_key(playbook=str(pb), ansible_args=["--check", "--diff"])
    assert len({plain, check, diff, both}) == 4


def test_key_start_at_task_buckets_separately(tmp_path: Path) -> None:
    pb = tmp_path / "p.yml"
    pb.write_text("")
    a = build_run_config_key(playbook=str(pb), ansible_args=[])
    b = build_run_config_key(playbook=str(pb), ansible_args=["--start-at-task", "install nginx"])
    c = build_run_config_key(playbook=str(pb), ansible_args=["--start-at-task", "restart nginx"])
    assert a != b
    assert b != c


def test_key_step_buckets_separately(tmp_path: Path) -> None:
    pb = tmp_path / "p.yml"
    pb.write_text("")
    a = build_run_config_key(playbook=str(pb), ansible_args=[])
    b = build_run_config_key(playbook=str(pb), ansible_args=["--step"])
    assert a != b


def test_key_limit_is_string(tmp_path: Path) -> None:
    pb = tmp_path / "p.yml"
    pb.write_text("")
    a = build_run_config_key(playbook=str(pb), ansible_args=["--limit", "web"])
    b = build_run_config_key(playbook=str(pb), ansible_args=["-l", "web"])
    assert a == b
    assert a.limit == "web"


def test_key_is_hashable_and_frozen(tmp_path: Path) -> None:
    pb = tmp_path / "p.yml"
    pb.write_text("")
    k = build_run_config_key(playbook=str(pb), ansible_args=["--tags", "web"])
    {k}  # must be hashable
    assert isinstance(k, RunConfigKey)


def test_key_unknown_flag_is_ignored_safely(tmp_path: Path) -> None:
    """Future ansible flags shouldn't crash us; they just don't contribute to the key."""
    pb = tmp_path / "p.yml"
    pb.write_text("")
    a = build_run_config_key(playbook=str(pb), ansible_args=[])
    b = build_run_config_key(playbook=str(pb), ansible_args=["--some-future-flag", "value"])
    assert a == b


def test_key_resolves_relative_playbook_against_explicit_cwd(tmp_path: Path) -> None:
    """Relative playbooks resolve against the supplied cwd rather than process cwd."""
    project_a = tmp_path / "project-a"
    project_b = tmp_path / "project-b"
    project_a.mkdir()
    project_b.mkdir()
    (project_a / "site.yml").write_text("")
    (project_b / "site.yml").write_text("")

    key_a = build_run_config_key(playbook="site.yml", ansible_args=[], cwd=project_a)
    key_b = build_run_config_key(playbook="site.yml", ansible_args=[], cwd=project_b)

    assert key_a.playbook == str((project_a / "site.yml").resolve())
    assert key_b.playbook == str((project_b / "site.yml").resolve())
    assert key_a != key_b


def test_resolve_stored_playbook_cases(tmp_path: Path) -> None:
    """Stored playbooks require an absolute path or a valid absolute cwd."""
    abs_pb = tmp_path / "site.yml"
    assert resolve_stored_playbook(str(abs_pb), cwd=None) == str(abs_pb.resolve())
    assert resolve_stored_playbook("site.yml", cwd=str(tmp_path)) == str(abs_pb.resolve())
    assert resolve_stored_playbook("site.yml", cwd=None) is None
    assert resolve_stored_playbook("site.yml", cwd="") is None
    assert resolve_stored_playbook("site.yml", cwd="relative/dir") is None
    assert resolve_stored_playbook("", cwd=str(tmp_path)) is None
    assert resolve_stored_playbook(None, cwd=str(tmp_path)) is None
