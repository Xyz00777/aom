"""Tests for the pre-flight orchestrator (--list-tasks + --list-hosts)."""

from __future__ import annotations

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


def test_trim_stderr_returns_short_message_unchanged():
    from ansible_aom.core.preflight import _trim_stderr

    assert _trim_stderr("syntax error in foo.yml") == "syntax error in foo.yml"


def test_trim_stderr_extracts_only_error_line_from_argparse_wall():
    """ansible-playbook on bad args dumps usage + error + full --help. Keep only error."""
    from ansible_aom.core.preflight import _trim_stderr

    stderr = """usage: ansible-playbook [-h] [--version] [-v]
                        playbook [playbook ...]
ansible-playbook: error: unrecognized arguments: extra.yml

usage: ansible-playbook [-h] [--version] [-v]
                        playbook [playbook ...]

Runs Ansible playbooks, executing the defined tasks on the targeted hosts.

positional arguments:
  playbook              Playbook(s)

options:
  -h, --help            show this help message and exit
  ... many many lines ...
"""
    trimmed = _trim_stderr(stderr)
    assert "ansible-playbook: error: unrecognized arguments: extra.yml" in trimmed
    assert "usage:" not in trimmed
    assert "positional arguments" not in trimmed
    assert "show this help message" not in trimmed


def test_trim_stderr_handles_multiple_error_lines():
    from ansible_aom.core.preflight import _trim_stderr

    stderr = "ansible-playbook: error: first problem\nansible-playbook: error: second problem\n"
    trimmed = _trim_stderr(stderr)
    assert "first problem" in trimmed
    assert "second problem" in trimmed


def test_trim_stderr_falls_back_to_first_lines_without_error_marker():
    """When there's no `: error:` marker, keep the first few non-empty lines, capped."""
    from ansible_aom.core.preflight import _trim_stderr

    stderr = (
        "ERROR! couldn't resolve module/action 'foo'\n\nThe error appears to be in '/tmp/x.yml'."
    )
    trimmed = _trim_stderr(stderr)
    assert "ERROR! couldn't resolve" in trimmed


def test_trim_stderr_empty_returns_empty():
    from ansible_aom.core.preflight import _trim_stderr

    assert _trim_stderr("") == ""
    assert _trim_stderr("   \n\n  ") == ""


def test_assemble_definitions_invokes_role_grouping():
    """5+ consecutive same-role tasks collapse into a RoleGroupDefinition."""
    from ansible_aom.core.models import RoleGroupDefinition
    from ansible_aom.core.preflight import assemble_definitions

    plays = [
        {
            "play_number": 1,
            "name": "Bulk role",
            "tasks": [{"name": f"step {i}", "role": "bigrole", "tags": []} for i in range(6)],
        }
    ]
    defs = assemble_definitions(plays=plays, play_hosts=[])

    assert len(defs[0].tasks) == 1
    grouped = defs[0].tasks[0]
    assert isinstance(grouped, RoleGroupDefinition)
    assert grouped.role == "bigrole"
    assert len(grouped.tasks) == 6
