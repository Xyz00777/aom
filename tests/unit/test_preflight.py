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
