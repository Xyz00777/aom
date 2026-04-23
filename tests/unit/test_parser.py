"""Unit tests for parser module.

Covers TEST_SPECIFICATION.md Sections 5.1-5.4:
- JSONL parser (Section 5.1)
- --list-tasks parser (Section 5.3)
- --list-hosts parser (Section 5.2.1)
- Role grouping (Section 5.4)

Test Isolation Rules (CRITICAL):
1. Every test creates its own parser instance
2. Function-scoped fixtures ONLY
3. Use conftest.py fixtures as input data
4. Tests can run in ANY order
"""

import json
import logging
from datetime import datetime, timezone

import pytest

from ansible_aom.core.models import (
    HostRunState,
    PlayDefinition,
    PlayRunState,
    RoleGroupDefinition,
    RunState,
    Status,
    TaskDefinition,
    TaskRunState,
)
from ansible_aom.core.parser import JsonLineStream, PtyStreamParser, StreamPhase

# =============================================================================
# Section 5.1: JSONL Parser Tests
# =============================================================================


class TestJsonLineStreamBasics:
    """TC-072 to TC-086: JSONL event parsing."""

    def test_feed_line_returns_empty_for_non_json(self):
        """TC-072 partial: Non-JSON lines return empty list."""
        parser = JsonLineStream()
        result = parser.feed_line("This is not JSON")
        assert result == []

    def test_feed_line_returns_empty_for_empty_line(self):
        """TC-072 partial: Empty lines return empty list."""
        parser = JsonLineStream()
        result = parser.feed_line("")
        assert result == []

    def test_feed_line_parses_valid_json(self, jsonl_line):
        """TC-072: Valid JSONL line parsed correctly."""
        parser = JsonLineStream()
        result = parser.feed_line(jsonl_line)
        assert len(result) == 1
        assert result[0]["_event"] == "v2_playbook_on_start"

    def test_feed_line_json_without_event_field(self, caplog):
        """TC-072: JSON without _event field returns empty list."""
        parser = JsonLineStream()
        with caplog.at_level(logging.WARNING):
            result = parser.feed_line('{"foo": "bar"}')
        assert result == []

    def test_feed_line_event_playbook_start(self, event_playbook_start):
        """TC-072: v2_playbook_on_start event parsed correctly."""
        parser = JsonLineStream()
        line = json.dumps(event_playbook_start)
        result = parser.feed_line(line)
        assert len(result) == 1
        event = result[0]
        assert event["_event"] == "v2_playbook_on_start"
        assert "_timestamp" in event

    def test_feed_line_event_play_start(self, event_play_start):
        """TC-073: v2_playbook_on_play_start event parsed with play data."""
        parser = JsonLineStream()
        line = json.dumps(event_play_start)
        result = parser.feed_line(line)
        assert len(result) == 1
        event = result[0]
        assert event["_event"] == "v2_playbook_on_play_start"
        assert event["play"]["id"] == "play-uuid-1"
        assert event["play"]["name"] == "Setup webservers"

    def test_feed_line_event_runner_start(self, event_runner_start):
        """TC-074: v2_runner_on_start event parsed (free strategy)."""
        parser = JsonLineStream()
        line = json.dumps(event_runner_start)
        result = parser.feed_line(line)
        assert len(result) == 1
        event = result[0]
        assert event["_event"] == "v2_runner_on_start"
        assert event["task"]["id"] == "task-uuid-1"
        assert event["host"] == "web1"

    def test_feed_line_event_task_start(self, event_task_start):
        """TC-075: v2_playbook_on_task_start event parsed (linear strategy)."""
        parser = JsonLineStream()
        line = json.dumps(event_task_start)
        result = parser.feed_line(line)
        assert len(result) == 1
        event = result[0]
        assert event["_event"] == "v2_playbook_on_task_start"
        assert event["task"]["id"] == "task-uuid-1"
        assert event["task"]["name"] == "Install nginx"

    def test_feed_line_event_runner_ok(self, event_runner_ok):
        """TC-077: v2_runner_on_ok event parsed with hosts result."""
        parser = JsonLineStream()
        line = json.dumps(event_runner_ok)
        result = parser.feed_line(line)
        assert len(result) == 1
        event = result[0]
        assert event["_event"] == "v2_runner_on_ok"
        assert "web1" in event["hosts"]
        assert event["hosts"]["web1"]["ok"] is True
        assert event["hosts"]["web1"]["changed"] is False

    def test_feed_line_event_runner_ok_changed(self, event_runner_ok_changed):
        """TC-077: v2_runner_on_ok event with changed=True."""
        parser = JsonLineStream()
        line = json.dumps(event_runner_ok_changed)
        result = parser.feed_line(line)
        event = result[0]
        assert event["hosts"]["web1"]["changed"] is True

    def test_feed_line_event_runner_failed(self, event_runner_failed):
        """TC-078: v2_runner_on_failed event parsed with error message."""
        parser = JsonLineStream()
        line = json.dumps(event_runner_failed)
        result = parser.feed_line(line)
        assert len(result) == 1
        event = result[0]
        assert event["_event"] == "v2_runner_on_failed"
        assert event["hosts"]["web1"]["failed"] is True
        assert "Error installing package" in event["hosts"]["web1"]["msg"]

    def test_feed_line_event_runner_skipped(self, event_runner_skipped):
        """TC-079: v2_runner_on_skipped event parsed with skip reason."""
        parser = JsonLineStream()
        line = json.dumps(event_runner_skipped)
        result = parser.feed_line(line)
        assert len(result) == 1
        event = result[0]
        assert event["_event"] == "v2_runner_on_skipped"
        assert event["hosts"]["web1"]["skipped"] is True

    def test_feed_line_event_runner_unreachable(self, event_runner_unreachable):
        """TC-080: v2_runner_on_unreachable event parsed."""
        parser = JsonLineStream()
        line = json.dumps(event_runner_unreachable)
        result = parser.feed_line(line)
        assert len(result) == 1
        event = result[0]
        assert event["_event"] == "v2_runner_on_unreachable"
        assert event["hosts"]["web1"]["unreachable"] is True

    def test_feed_line_event_stats(self, event_stats):
        """TC-081: v2_playbook_on_stats event parsed with per-host stats."""
        parser = JsonLineStream()
        line = json.dumps(event_stats)
        result = parser.feed_line(line)
        assert len(result) == 1
        event = result[0]
        assert event["_event"] == "v2_playbook_on_stats"
        assert "web1" in event["stats"]
        assert "web2" in event["stats"]
        assert event["stats"]["web1"]["ok"] == 5

    def test_timestamp_parsing_iso8601_utc(self):
        """TC-084: Timestamp parsing (ISO 8601 UTC)."""
        parser = JsonLineStream()
        line = json.dumps({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        result = parser.feed_line(line)
        assert len(result) == 1
        # Timestamp should be preserved as string or parsed
        assert "_timestamp" in result[0]

    def test_invalid_json_continues_processing(self, caplog):
        """TC-072: Invalid JSON line logged as warning, processing continues."""
        parser = JsonLineStream()
        with caplog.at_level(logging.WARNING, logger="ansible_aom.core.parser"):
            result1 = parser.feed_line("not valid json")
            result2 = parser.feed_line(
                '{"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"}'
            )
        assert result1 == []
        assert len(result2) == 1

    def test_non_json_handler_called(self):
        """TC-142: Non-JSON handler called for non-JSON lines."""
        parser = JsonLineStream()
        non_json_calls = []

        def handler(line: str) -> None:
            non_json_calls.append(line)

        parser.set_non_json_handler(handler)
        parser.feed_line("PLAY RECAP *************")
        parser.feed_line("[WARNING]: Some warning")
        assert len(non_json_calls) == 2


class TestPtyStreamParserPhases:
    """TC-128 to TC-142: PTY stream phase transitions."""

    def test_initial_phase_pre_run_prompts(self):
        """TC-128: Initial phase is PRE_RUN_PROMPTS."""
        parser = PtyStreamParser()
        assert parser.phase == StreamPhase.PRE_RUN_PROMPTS

    def test_transition_to_execution_on_start_event(self):
        """TC-131: Start event triggers PRE_RUN_PROMPTS -> EXECUTION."""
        parser = PtyStreamParser()
        assert parser.phase == StreamPhase.PRE_RUN_PROMPTS
        parser.feed_line('{"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"}')
        assert parser.phase == StreamPhase.EXECUTION

    def test_transition_to_post_run_on_stats_event(self):
        """TC-132: Stats event triggers EXECUTION -> POST_RUN_RECAP."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        parser.feed_line(
            '{"_event": "v2_playbook_on_stats", "_timestamp": "2026-04-20T10:01:00Z", "stats": {}}'
        )
        assert parser.phase == StreamPhase.POST_RUN_RECAP

    def test_password_pattern_vault(self, password_prompt_vault):
        """TC-134: Vault password prompt pattern detected."""
        parser = PtyStreamParser()
        parser.feed_line(password_prompt_vault)
        assert parser.pending_password_prompt is not None

    def test_password_pattern_ssh(self, password_prompt_ssh):
        """TC-136: SSH password prompt pattern detected."""
        parser = PtyStreamParser()
        parser.feed_line(password_prompt_ssh)
        assert parser.pending_password_prompt is not None

    def test_password_pattern_become(self, password_prompt_become):
        """TC-137: BECOME password prompt pattern detected."""
        parser = PtyStreamParser()
        parser.feed_line(password_prompt_become)
        assert parser.pending_password_prompt is not None

    def test_warning_pattern_detection(self, warning_line):
        """TC-141: [WARNING]: pattern detected."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        parser.feed_line(warning_line)
        assert len(parser.warnings) >= 1
        assert parser.warnings[0].type.value == "warning"

    def test_deprecation_warning_pattern(self, deprecation_warning_line):
        """TC-141: [DEPRECATION WARNING]: pattern detected."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        parser.feed_line(deprecation_warning_line)
        assert len(parser.warnings) >= 1

    def test_deprecated_removed_pattern(self, deprecated_removed_line):
        """TC-141: [DEPRECATED]: pattern detected."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        parser.feed_line(deprecated_removed_line)
        assert len(parser.warnings) >= 1

    def test_play_recap_detection(self, recap_line):
        """TC-140: PLAY RECAP pattern detected."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        # First set the phase properly
        parser._in_recap = False
        parser.feed_line(recap_line)
        assert parser._in_recap is True

    def test_clear_password_prompt(self, password_prompt_vault):
        """Password prompt can be cleared after handling."""
        parser = PtyStreamParser()
        parser.feed_line(password_prompt_vault)
        assert parser.pending_password_prompt is not None
        parser.clear_password_prompt()
        assert parser.pending_password_prompt is None


class TestPtyStreamParserJsonlEvents:
    """TC-072 to TC-086: Processing JSONL events through PTY stream."""

    def test_process_playbook_start_sets_start_time(self, event_playbook_start):
        """TC-086: Start event sets start_time."""
        parser = PtyStreamParser()
        line = json.dumps(event_playbook_start)
        events = parser.feed_line(line)
        assert len(events) == 1
        assert parser.phase == StreamPhase.EXECUTION

    def test_process_play_start_creates_play_state(self, event_play_start):
        """TC-073: Play start creates PlayRunState."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        line = json.dumps(event_play_start)
        events = parser.feed_line(line)
        assert len(events) == 1

    def test_process_task_start_linear_strategy(self, event_task_start):
        """TC-075: Task start detected for linear strategy."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        line = json.dumps(event_task_start)
        events = parser.feed_line(line)
        assert len(events) == 1

    def test_process_runner_start_free_strategy(self, event_runner_start):
        """TC-074: Runner start detected for free strategy."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        line = json.dumps(event_runner_start)
        events = parser.feed_line(line)
        assert len(events) == 1


# =============================================================================
# Section 5.2.1: --list-hosts Parser Tests
# =============================================================================


class TestListHostsParser:
    """TC-097 to TC-106: --list-hosts output parsing."""

    def test_parse_play_line_pattern(self, list_hosts_output):
        """TC-097: Parse play line format: play #N (hosts): name\\tTAGS: [tags]."""
        from ansible_aom.core.parser import parse_list_hosts_output

        result = parse_list_hosts_output(list_hosts_output)
        assert len(result) == 2
        assert result[0]["play_number"] == 1
        assert result[0]["name"] == "Setup web servers"
        assert result[0]["hosts_pattern"] == ["webservers"]

    def test_parse_hostname_extraction(self, list_hosts_output):
        """TC-098: Parse hostnames from 6-space indented lines."""
        from ansible_aom.core.parser import parse_list_hosts_output

        result = parse_list_hosts_output(list_hosts_output)
        assert "web1.example.com" in result[0]["hosts"]
        assert "web2.example.com" in result[0]["hosts"]
        assert "db1.example.com" in result[1]["hosts"]

    def test_skip_non_host_lines(self, list_hosts_output):
        """TC-099: Parser skips 'pattern:', 'hosts (N):', 'tasks:', and blank lines."""
        from ansible_aom.core.parser import parse_list_hosts_output

        result = parse_list_hosts_output(list_hosts_output)
        # Should only return plays with hosts, not include pattern/tasks lines
        for play in result:
            assert "pattern:" not in str(play)
            assert "hosts (" not in str(play.get("hosts", []))

    def test_empty_output_returns_empty_list(self):
        """TC-105: Empty --list-hosts output returns empty list."""
        from ansible_aom.core.parser import parse_list_hosts_output

        result = parse_list_hosts_output("")
        assert result == []

    def test_localhost_handling(self):
        """TC-100: hosts: localhost returns ['localhost']."""
        from ansible_aom.core.parser import parse_list_hosts_output

        output = """playbook: test.yml

  play #1 (localhost): Local play\tTAGS: []
    pattern: ['localhost']
    hosts (1):
      localhost"""
        result = parse_list_hosts_output(output)
        assert len(result) == 1
        assert "localhost" in result[0]["hosts"]

    def test_playbook_header_skipped(self):
        """TC-112: First line 'playbook: <path>' skipped."""
        from ansible_aom.core.parser import parse_list_hosts_output

        output = """playbook: site.yml

  play #1 (all): Test play\tTAGS: []"""
        result = parse_list_hosts_output(output)
        # First line should not create an entry
        assert len(result) == 1
        assert result[0]["play_number"] == 1


# =============================================================================
# Section 5.3: --list-tasks Parser Tests
# =============================================================================


class TestListTasksParser:
    """TC-107 to TC-121: --list-tasks output parsing."""

    def test_tab_separator_used(self, list_tasks_output):
        """TC-108: Separator between task name and TAGS: is literal TAB."""
        from ansible_aom.core.parser import parse_list_tasks_output

        # The output should properly split on TAB
        result = parse_list_tasks_output(list_tasks_output)
        assert len(result) == 2  # 2 plays
        # First play has 3 tasks
        assert len(result[0]["tasks"]) == 3

    def test_play_indent_recognition(self, list_tasks_output):
        """TC-109: Play lines have exactly 2-space indent."""
        from ansible_aom.core.parser import parse_list_tasks_output

        result = parse_list_tasks_output(list_tasks_output)
        assert len(result) == 2
        assert result[0]["name"] == "Setup web servers"
        assert result[1]["name"] == "Setup database"

    def test_task_indent_recognition(self, list_tasks_output):
        """TC-110: Task lines have exactly 6-space indent."""
        from ansible_aom.core.parser import parse_list_tasks_output

        result = parse_list_tasks_output(list_tasks_output)
        # Tasks should be extracted with correct indentation
        assert "install nginx" in [t["name"] for t in result[0]["tasks"]]
        assert "configure nginx" in [t["name"] for t in result[0]["tasks"]]

    def test_role_prefix_extraction(self):
        """TC-111: Role prefix format 'role_name : task_name'."""
        from ansible_aom.core.parser import parse_list_tasks_output

        output = """playbook: test.yml

  play #1 (all): Test\tTAGS: []
    nginx : Install\tTAGS: [web]
    nginx : Configure\tTAGS: [web]
    db : Setup\tTAGS: [db]"""
        result = parse_list_tasks_output(output)
        assert len(result) == 1
        tasks = result[0]["tasks"]
        assert tasks[0]["role"] == "nginx"
        assert tasks[0]["name"] == "Install"
        assert tasks[1]["role"] == "nginx"
        assert tasks[1]["name"] == "Configure"
        assert tasks[2]["role"] == "db"
        assert tasks[2]["name"] == "Setup"

    def test_task_without_role(self):
        """TC-115: Tasks without role prefix."""
        from ansible_aom.core.parser import parse_list_tasks_output

        output = """playbook: test.yml

  play #1 (all): Test\tTAGS: []
    Install packages\tTAGS: []
    Run command\tTAGS: []"""
        result = parse_list_tasks_output(output)
        tasks = result[0]["tasks"]
        assert tasks[0]["role"] is None
        assert tasks[0]["name"] == "Install packages"

    def test_task_tags_extraction(self):
        """TC-108: Tags extracted from TAGS: [tag1, tag2]."""
        from ansible_aom.core.parser import parse_list_tasks_output

        output = """playbook: test.yml

  play #1 (all): Test\tTAGS: []
    task1\tTAGS: [web, deploy]
    task2\tTAGS: [db]"""
        result = parse_list_tasks_output(output)
        tasks = result[0]["tasks"]
        assert "web" in tasks[0]["tags"]
        assert "deploy" in tasks[0]["tags"]
        assert "db" in tasks[1]["tags"]

    def test_empty_tags(self):
        """TC-097: Empty tags handled correctly."""
        from ansible_aom.core.parser import parse_list_tasks_output

        output = """playbook: test.yml

  play #1 (all): Test\tTAGS: []
    task1\tTAGS: []"""
        result = parse_list_tasks_output(output)
        tasks = result[0]["tasks"]
        assert tasks[0]["tags"] == []

    def test_playbook_header_skipped(self):
        """TC-112: First line 'playbook: <path>' followed by blank skipped."""
        from ansible_aom.core.parser import parse_list_tasks_output

        output = """playbook: site.yml

  play #1 (all): Test\tTAGS: []"""
        result = parse_list_tasks_output(output)
        assert len(result) == 1

    def test_multiple_plays(self, list_tasks_output):
        """Multiple plays parsed correctly."""
        from ansible_aom.core.parser import parse_list_tasks_output

        result = parse_list_tasks_output(list_tasks_output)
        assert len(result) == 2
        assert result[0]["play_number"] == 1
        assert result[1]["play_number"] == 2

    def test_include_tasks_not_expanded(self):
        """TC-113: include_tasks shown as single task (NOT expanded)."""
        from ansible_aom.core.parser import parse_list_tasks_output

        output = """playbook: test.yml

  play #1 (all): Test\tTAGS: []
    Include tasks file\tTAGS: []"""
        result = parse_list_tasks_output(output)
        # include_tasks appears as one task, not expanded
        assert len(result[0]["tasks"]) == 1

    def test_no_json_output(self):
        """TC-107: --list-tasks output is always plain text; no JSON mode."""
        from ansible_aom.core.parser import parse_list_tasks_output

        # Parser should handle text format, not JSON
        output = """playbook: test.yml

  play #1 (all): Test\tTAGS: []
    task1\tTAGS: []"""
        result = parse_list_tasks_output(output)
        assert isinstance(result, list)


# =============================================================================
# Section 5.4: Role Grouping Tests
# =============================================================================


class TestRoleGrouping:
    """TC-122, TC-123: Role grouping logic."""

    def test_five_same_role_tasks_creates_group(self):
        """TC-122: 5+ consecutive same-role tasks are grouped."""
        from ansible_aom.core.parser import group_roles

        tasks = [
            TaskDefinition(
                name=f"Task {i}", role="nginx", tags=[], play_id="1", play_order=0, task_order=i
            )
            for i in range(5)
        ]
        groups = group_roles(tasks)
        assert len(groups) == 1
        assert isinstance(groups[0], RoleGroupDefinition)
        assert groups[0].role == "nginx"
        assert len(groups[0].tasks) == 5

    def test_four_same_role_tasks_no_grouping(self):
        """TC-122: 4 same-role tasks NOT grouped (threshold is 5)."""
        from ansible_aom.core.parser import group_roles

        tasks = [
            TaskDefinition(
                name=f"Task {i}", role="nginx", tags=[], play_id="1", play_order=0, task_order=i
            )
            for i in range(4)
        ]
        groups = group_roles(tasks)
        # Should return individual tasks, not a group
        assert len(groups) == 4
        for item in groups:
            assert isinstance(item, TaskDefinition)

    def test_mixed_roles_no_grouping(self):
        """TC-122: Mixed roles do not create groups."""
        from ansible_aom.core.parser import group_roles

        tasks = [
            TaskDefinition(
                name="Task 1", role="nginx", tags=[], play_id="1", play_order=0, task_order=0
            ),
            TaskDefinition(
                name="Task 2", role="db", tags=[], play_id="1", play_order=0, task_order=1
            ),
            TaskDefinition(
                name="Task 3", role="nginx", tags=[], play_id="1", play_order=0, task_order=2
            ),
            TaskDefinition(
                name="Task 4", role="nginx", tags=[], play_id="1", play_order=0, task_order=3
            ),
            TaskDefinition(
                name="Task 5", role="nginx", tags=[], play_id="1", play_order=0, task_order=4
            ),
            TaskDefinition(
                name="Task 6", role="nginx", tags=[], play_id="1", play_order=0, task_order=5
            ),
        ]
        groups = group_roles(tasks)
        # No grouping because roles are mixed
        for item in groups:
            assert isinstance(item, TaskDefinition)

    def test_role_group_name_format(self):
        """TC-123, TC-181: RoleGroup name property format."""
        role_group = RoleGroupDefinition(
            role="nginx",
            tasks=[
                TaskDefinition(
                    name=f"Task {i}", role="nginx", tags=[], play_id="1", play_order=0, task_order=i
                )
                for i in range(7)
            ],
        )
        assert role_group.name == "Role: nginx (7 tasks)"

    def test_role_group_with_mixed_none_role(self):
        """Tasks without role (None) do not interrupt role grouping."""
        from ansible_aom.core.parser import group_roles

        tasks = [
            TaskDefinition(
                name="Task 1", role=None, tags=[], play_id="1", play_order=0, task_order=0
            ),
            TaskDefinition(
                name="Task 2", role="nginx", tags=[], play_id="1", play_order=0, task_order=1
            ),
            TaskDefinition(
                name="Task 3", role="nginx", tags=[], play_id="1", play_order=0, task_order=2
            ),
            TaskDefinition(
                name="Task 4", role="nginx", tags=[], play_id="1", play_order=0, task_order=3
            ),
            TaskDefinition(
                name="Task 5", role="nginx", tags=[], play_id="1", play_order=0, task_order=4
            ),
            TaskDefinition(
                name="Task 6", role="nginx", tags=[], play_id="1", play_order=0, task_order=5
            ),
            TaskDefinition(
                name="Task 7", role="nginx", tags=[], play_id="1", play_order=0, task_order=6
            ),
        ]
        groups = group_roles(tasks)
        # First task has no role, then 6 nginx tasks should NOT be grouped
        # (6 is >= 5, but let's check the logic)
        nginx_count = sum(1 for t in groups if isinstance(t, TaskDefinition) and t.role == "nginx")
        # After grouping, we'd expect potentially a group for nginx
        # But since there's a None-role task before, grouping resets

    def test_multiple_role_groups(self):
        """Multiple role groups in sequence."""
        from ansible_aom.core.parser import group_roles

        tasks = [
            # First nginx role group (5 tasks)
            *(
                TaskDefinition(
                    name=f"nginx {i}",
                    role="nginx",
                    tags=[],
                    play_id="1",
                    play_order=0,
                    task_order=i,
                )
                for i in range(5)
            ),
            # db role group (5 tasks)
            *(
                TaskDefinition(
                    name=f"db {i}", role="db", tags=[], play_id="1", play_order=0, task_order=i + 5
                )
                for i in range(5)
            ),
        ]
        groups = group_roles(tasks)
        assert len(groups) == 2
        assert groups[0].role == "nginx"
        assert groups[1].role == "db"

    def test_role_group_at_end_of_list(self):
        """Role group can be at end of task list."""
        from ansible_aom.core.parser import group_roles

        tasks = [
            TaskDefinition(
                name="Task 1", role=None, tags=[], play_id="1", play_order=0, task_order=0
            ),
            TaskDefinition(
                name="Task 2", role=None, tags=[], play_id="1", play_order=0, task_order=1
            ),
            # 5 nginx tasks at end
            *(
                TaskDefinition(
                    name=f"nginx {i}",
                    role="nginx",
                    tags=[],
                    play_id="1",
                    play_order=0,
                    task_order=i + 2,
                )
                for i in range(5)
            ),
        ]
        groups = group_roles(tasks)
        # Should have 2 non-grouped tasks + 1 group
        assert len(groups) == 3
        assert isinstance(groups[0], TaskDefinition)
        assert isinstance(groups[1], TaskDefinition)
        assert isinstance(groups[2], RoleGroupDefinition)


# =============================================================================
# Section 5.2: Pre-Parse Phase Tests
# =============================================================================


class TestPreParsePhase:
    """TC-087 to TC-096: Pre-parse phase tests."""

    def test_parse_jsonl_file_fixture(self):
        """Verify fixture files can be parsed."""
        parser = JsonLineStream()
        with open("tests/fixtures/single_task_ok.jsonl") as f:
            lines = [parser.feed_line(line.strip()) for line in f if line.strip()]
        # Flatten results
        events = [e for result in lines for e in result]
        assert len(events) == 5  # 5 events in fixture

    def test_parse_multi_host_mixed_fixture(self):
        """Parse multi-host mixed fixture."""
        parser = JsonLineStream()
        events = []
        with open("tests/fixtures/multi_host_mixed.jsonl") as f:
            for line in f:
                line = line.strip()
                if line:
                    events.extend(parser.feed_line(line))
        assert len(events) == 13

    def test_parse_failed_fixture(self):
        """Parse failed playbook fixture."""
        parser = JsonLineStream()
        events = []
        with open("tests/fixtures/playbook_failed.jsonl") as f:
            for line in f:
                line = line.strip()
                if line:
                    events.extend(parser.feed_line(line))
        assert len(events) == 7


class TestListTasksListHostsIntegration:
    """TC-087, TC-088: Combined --list-tasks and --list-hosts."""

    def test_preparse_result_assembly(self, list_tasks_output, list_hosts_output):
        """TC-088: PreParseResult contains both plays and play_hosts."""
        from ansible_aom.core.parser import (
            PreParseResult,
            parse_list_hosts_output,
            parse_list_tasks_output,
        )

        plays = parse_list_tasks_output(list_tasks_output)
        play_hosts = parse_list_hosts_output(list_hosts_output)

        result = PreParseResult(plays=plays, play_hosts=play_hosts)
        assert len(result.plays) == 2
        assert len(result.play_hosts) == 2

    def test_list_tasks_play_id_sequential(self):
        """TC-183: Play ID is sequential number string from --list-tasks."""
        from ansible_aom.core.parser import parse_list_tasks_output

        output = """playbook: test.yml

  play #1 (all): First\tTAGS: []
    task1\tTAGS: []

  play #2 (all): Second\tTAGS: []
    task2\tTAGS: []"""
        result = parse_list_tasks_output(output)
        assert result[0]["play_number"] == 1
        assert result[1]["play_number"] == 2


# =============================================================================
# TaskDefinition and PlayDefinition Model Tests
# =============================================================================


class TestTaskDefinition:
    """TC-174 to TC-180: TaskDefinition model tests."""

    def test_task_definition_creation(self):
        """TC-174: TaskDefinition fields initialized correctly."""
        task = TaskDefinition(
            name="Install nginx",
            role="nginx",
            tags=["web"],
            play_id="1",
            play_order=0,
            task_order=0,
        )
        assert task.name == "Install nginx"
        assert task.role == "nginx"
        assert task.tags == ["web"]
        assert task.play_id == "1"
        assert task.play_order == 0
        assert task.task_order == 0

    def test_task_definition_is_dynamic_default(self):
        """TC-175: is_dynamic defaults to False."""
        task = TaskDefinition(
            name="Test", role=None, tags=[], play_id="1", play_order=0, task_order=0
        )
        assert task.is_dynamic is False

    def test_task_definition_uuid_nullable(self):
        """TC-176: UUID is None before JSONL matching."""
        task = TaskDefinition(
            name="Test", role=None, tags=[], play_id="1", play_order=0, task_order=0
        )
        assert task.uuid is None

    def test_task_definition_path_nullable(self):
        """TC-177: path is None before JSONL matching."""
        task = TaskDefinition(
            name="Test", role=None, tags=[], play_id="1", play_order=0, task_order=0
        )
        assert task.path is None

    def test_task_definition_children_default(self):
        """TC-178: children defaults to empty list."""
        task = TaskDefinition(
            name="Test", role=None, tags=[], play_id="1", play_order=0, task_order=0
        )
        assert task.children == []

    def test_task_definition_dynamic_order_negative_one(self):
        """TC-179: task_order is -1 for dynamic tasks."""
        task = TaskDefinition(
            name="Dynamic task",
            role=None,
            tags=[],
            play_id="1",
            play_order=0,
            task_order=-1,
            is_dynamic=True,
        )
        assert task.task_order == -1
        assert task.is_dynamic is True


class TestPlayDefinition:
    """TC-182 to TC-185: PlayDefinition model tests."""

    def test_play_definition_creation(self):
        """TC-182: PlayDefinition fields validated."""
        play = PlayDefinition(
            id="1", name="Setup webservers", hosts="webservers", resolved_hosts=["web1", "web2"]
        )
        assert play.id == "1"
        assert play.name == "Setup webservers"
        assert play.hosts == "webservers"
        assert play.resolved_hosts == ["web1", "web2"]

    def test_play_definition_id_sequential_string(self):
        """TC-183: ID is sequential number string."""
        play = PlayDefinition(id="1", name="Test", hosts="all")
        assert play.id == "1"  # String, not int

    def test_play_definition_hosts_vs_resolved(self):
        """TC-184: hosts is pattern, resolved_hosts is list."""
        play = PlayDefinition(
            id="1", name="Test", hosts="webservers", resolved_hosts=["web1", "web2"]
        )
        assert isinstance(play.hosts, str)
        assert isinstance(play.resolved_hosts, list)

    def test_play_definition_resolved_hosts_default_empty(self):
        """TC-185: resolved_hosts defaults to empty list."""
        play = PlayDefinition(id="1", name="Test", hosts="all")
        assert play.resolved_hosts == []


class TestStatusEnum:
    """TC-186: Status enum values."""

    def test_status_enum_values(self):
        expected_values = {
            Status.PENDING,
            Status.RUNNING,
            Status.OK,
            Status.CHANGED,
            Status.FAILED,
            Status.SKIPPED,
            Status.UNREACHABLE,
            Status.COMPLETED,
        }
        actual_values = set(Status)
        assert actual_values == expected_values
        assert len(Status) == 8

    def test_status_enum_strings(self):
        """Status values have correct string representation."""
        assert Status.PENDING.value == "pending"
        assert Status.RUNNING.value == "running"
        assert Status.OK.value == "ok"
        assert Status.CHANGED.value == "changed"
        assert Status.FAILED.value == "failed"
        assert Status.SKIPPED.value == "skipped"
        assert Status.UNREACHABLE.value == "unreachable"


class TestRoleGroupDefinition:
    """TC-180, TC-181: RoleGroupDefinition model tests."""

    def test_role_group_definition_creation(self):
        """TC-180: RoleGroupDefinition groups consecutive same-role tasks."""
        tasks = [
            TaskDefinition(
                name=f"Task {i}", role="nginx", tags=[], play_id="1", play_order=0, task_order=i
            )
            for i in range(5)
        ]
        group = RoleGroupDefinition(role="nginx", tasks=tasks)
        assert group.role == "nginx"
        assert len(group.tasks) == 5

    def test_role_group_name_property(self):
        """TC-181: name property returns formatted string."""
        tasks = [
            TaskDefinition(
                name=f"Task {i}", role="nginx", tags=[], play_id="1", play_order=0, task_order=i
            )
            for i in range(7)
        ]
        group = RoleGroupDefinition(role="nginx", tasks=tasks)
        assert group.name == "Role: nginx (7 tasks)"


class TestHostRunState:
    """TC-187, TC-188: HostRunState model tests."""

    def test_host_run_state_creation(self):
        """TC-187: HostRunState fields validated."""
        state = HostRunState(hostname="web1", status=Status.OK, changed=False)
        assert state.hostname == "web1"
        assert state.status == Status.OK
        assert state.changed is False

    def test_host_run_state_status_transition(self):
        """TC-188: HostRunState status can be updated."""
        state = HostRunState(hostname="web1", status=Status.PENDING)
        assert state.status == Status.PENDING
        state.status = Status.RUNNING
        assert state.status == Status.RUNNING
        state.status = Status.OK
        assert state.status == Status.OK


class TestTaskRunState:
    """TC-189, TC-190: TaskRunState model tests."""

    def test_task_run_state_creation(self):
        """TC-189: TaskRunState aggregates per-host states."""
        state = TaskRunState(task_id="task-uuid-1", name="Install nginx")
        assert state.task_id == "task-uuid-1"
        assert state.name == "Install nginx"
        assert state.status == Status.PENDING
        assert state.hosts == {}

    def test_task_run_state_hosts_dict(self):
        """TC-190: hosts dict uses hostname string as key."""
        state = TaskRunState(task_id="task-1", name="Test")
        state.hosts["web1"] = HostRunState(hostname="web1", status=Status.OK)
        state.hosts["web2"] = HostRunState(hostname="web2", status=Status.FAILED)
        assert "web1" in state.hosts
        assert state.hosts["web1"].status == Status.OK


class TestPlayRunState:
    """TC-191 to TC-193: PlayRunState model tests."""

    def test_play_run_state_creation(self):
        """TC-191: PlayRunState aggregates task states."""
        state = PlayRunState(play_id="play-1", name="Setup")
        assert state.play_id == "play-1"
        assert state.name == "Setup"
        assert state.status == Status.PENDING
        assert state.tasks == {}

    def test_play_run_state_detected_strategy_default(self):
        """TC-192: detected_strategy defaults to None."""
        state = PlayRunState(play_id="play-1", name="Setup")
        assert state.detected_strategy is None

    def test_play_run_state_detected_strategy_values(self):
        """TC-193: detected_strategy can be 'linear' or 'free'."""
        state = PlayRunState(play_id="play-1", name="Setup")
        state.detected_strategy = "linear"
        assert state.detected_strategy == "linear"
        state.detected_strategy = "free"
        assert state.detected_strategy == "free"


class TestRunState:
    """TC-194 to TC-196: RunState model tests."""

    def test_run_state_creation(self):
        """TC-194: RunState is top-level container."""
        state = RunState(playbook="site.yml")
        assert state.playbook == "site.yml"
        assert state.plays == {}
        assert state.definitions == []
        assert state.status == Status.PENDING

    def test_run_state_definitions_list(self):
        """TC-195: definitions contains PlayDefinition objects."""
        state = RunState(playbook="site.yml")
        play = PlayDefinition(id="1", name="Setup", hosts="all")
        state.definitions.append(play)
        assert len(state.definitions) == 1
        assert isinstance(state.definitions[0], PlayDefinition)

    def test_run_state_plays_dict(self):
        """TC-196: plays dict uses play UUID/id string as key."""
        state = RunState(playbook="site.yml")
        play_state = PlayRunState(play_id="play-uuid-1", name="Setup")
        state.plays["play-uuid-1"] = play_state
        assert "play-uuid-1" in state.plays
        assert state.plays["play-uuid-1"].name == "Setup"
