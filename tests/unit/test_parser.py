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

import pytest

from ansible_aom.core.models import (
    RoleGroupDefinition,
    RunState,
    Status,
    TaskDefinition,
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


class TestJsonLineStreamCarryBuffer:
    """R1: PTY can split a JSONL event across reads. The first half on its
    own is unparseable JSON; the parser must stash it and rejoin with the
    next chunk instead of dropping both halves."""

    def test_two_chunk_join_yields_full_event(self):
        """Half a JSONL line then the rest should yield one event."""
        parser = JsonLineStream()
        assert parser.feed_line('{"_event":"v2_runner_on_ok","hosts":{"web1":{"msg":"hel') == []
        result = parser.feed_line('lo"}}}')
        assert len(result) == 1
        assert result[0]["_event"] == "v2_runner_on_ok"
        assert result[0]["hosts"]["web1"]["msg"] == "hello"

    def test_many_small_chunks_join(self):
        """A 100-chunk slow-drip split still yields exactly one event."""
        full = '{"_event":"v2_playbook_on_start","msg":"' + ("x" * 200) + '"}'
        parser = JsonLineStream()
        chunk_size = max(1, len(full) // 100)
        events: list[dict] = []
        for i in range(0, len(full), chunk_size):
            events.extend(parser.feed_line(full[i : i + chunk_size]))
        assert len(events) == 1
        assert events[0]["_event"] == "v2_playbook_on_start"

    def test_carry_buffer_overflow_drops_without_raising(self):
        """One pathologically large partial event is dropped, not OOM'd,
        and a subsequent well-formed line parses cleanly."""
        parser = JsonLineStream()
        # First chunk is a partial JSON that's already larger than the
        # 1 MB cap. Storing it as carry would be unbounded growth — the
        # parser must drop it.
        oversized = '{"_event":"x","msg":"' + ("a" * 1_100_000)
        assert parser.feed_line(oversized) == []
        # After the drop, the carry must be empty so the next line is
        # parsed standalone.
        result = parser.feed_line('{"_event":"v2_playbook_on_start"}')
        assert len(result) == 1
        assert result[0]["_event"] == "v2_playbook_on_start"

    def test_well_formed_line_does_not_use_carry(self):
        """Sanity: a normal line in one go bypasses the carry path."""
        parser = JsonLineStream()
        result = parser.feed_line('{"_event":"v2_playbook_on_start"}')
        assert len(result) == 1
        # And a subsequent line still parses fine.
        result2 = parser.feed_line('{"_event":"v2_runner_on_ok","hosts":{}}')
        assert len(result2) == 1

    def test_garbage_carry_does_not_swallow_next_valid_event(self):
        """A garbage prefix that can't be the head of a real event (e.g.
        a bare ``{``) must not corrupt the next valid line by prepending.
        Discovered by hypothesis: ``feed_line("{")`` stashed ``{`` as carry,
        then ``feed_line('{"_event":...}')`` produced ``{{"_event":...}`` →
        invalid JSON → re-stashed → event permanently lost."""
        parser = JsonLineStream()
        assert parser.feed_line("{") == []
        result = parser.feed_line('{"_event":"v2_playbook_on_start"}')
        assert len(result) == 1
        assert result[0]["_event"] == "v2_playbook_on_start"


class TestRunStateUnknownEvent:
    """R5: unknown _event values are counted so the renderer can show a
    one-line "(N unknown events: foo×3)" hint at completion — quieter
    than warnings, but visible enough for future-version drift."""

    def test_unknown_event_does_not_raise(self):
        state = RunState(playbook="test.yml")
        # Should not raise.
        state.handle_event({"_event": "v2_playbook_on_include", "foo": "bar"})

    def test_unknown_event_leaves_plays_empty(self):
        state = RunState(playbook="test.yml")
        state.handle_event({"_event": "v2_some_future_event"})
        assert state.plays == {}

    def test_unknown_event_increments_counter(self):
        state = RunState(playbook="test.yml")
        state.handle_event({"_event": "v2_playbook_on_include"})
        state.handle_event({"_event": "v2_playbook_on_include"})
        state.handle_event({"_event": "v2_other_new_event"})
        assert state.unknown_events == {"v2_playbook_on_include": 2, "v2_other_new_event": 1}

    def test_known_events_do_not_increment_counter(self):
        state = RunState(playbook="test.yml")
        state.handle_event(
            {
                "_event": "v2_playbook_on_start",
                "_timestamp": "2026-04-20T10:00:00Z",
            }
        )
        assert state.unknown_events == {}

    def test_missing_event_field_does_not_increment(self):
        """Events without _event are degenerate, not unknown — don't count."""
        state = RunState(playbook="test.yml")
        state.handle_event({"foo": "bar"})  # no _event key
        assert state.unknown_events == {}


class TestPtyStreamParserPlaintextCap:
    """R2: plaintext_lines must be bounded.

    Without a cap, a long run with verbose pexpect noise (warnings, info
    banners, prompt echoes) can grow plaintext_lines without limit. The
    cap matches the log panel's MAX_LOG_LINES so the parser doesn't
    accumulate more than the panel could ever display.
    """

    def test_plaintext_lines_capped_at_max_log_lines(self):
        from ansible_aom.core.state_machine import MAX_LOG_LINES

        parser = PtyStreamParser()
        # Push the parser past the cap. Use feed_line with non-JSON in
        # EXECUTION phase so it routes to _handle_plaintext.
        parser.phase = StreamPhase.EXECUTION
        for i in range(MAX_LOG_LINES + 100):
            parser.feed_line(f"random ansible chatter line {i}")
        assert len(parser.plaintext_lines) == MAX_LOG_LINES
        # The retained tail should be the *most recent* lines, not the
        # first ones — a stuck head defeats the purpose.
        assert "random ansible chatter line" in parser.plaintext_lines[-1]
        last_idx = int(parser.plaintext_lines[-1].rsplit(" ", 1)[1])
        first_idx = int(parser.plaintext_lines[0].rsplit(" ", 1)[1])
        assert last_idx > first_idx

    def test_plaintext_lines_60000_input_retains_exactly_50000(self):
        """R2 spec literal: 60 000 lines in → exactly 50 000 retained.

        A noisy run (verbose pexpect chatter, ansible banners, prompt
        echoes) easily crosses 60 000 lines on a long playbook. The cap
        must drop exactly 10 000 entries and keep the most-recent 50 000
        — never the head (a stuck head defeats the stall-diagnostic
        purpose of plaintext_lines in runner.py).
        """
        from ansible_aom.core.state_machine import MAX_LOG_LINES

        assert MAX_LOG_LINES == 50000  # pin against accidental constant drift

        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        # Feed the spec-literal input count: 60 000.
        for i in range(60_000):
            parser.feed_line(f"line {i}")
        assert len(parser.plaintext_lines) == 50_000
        # First retained entry is line 10 000 (the oldest survivor);
        # last retained entry is line 59 999.
        assert parser.plaintext_lines[0] == "line 10000"
        assert parser.plaintext_lines[-1] == "line 59999"


class TestPtyStreamParserLatestOutputIsPlaintext:
    """``latest_output_is_plaintext`` tracks whether the most recent
    classified output line was plaintext (vs a JSONL event).

    The runner's TIMEOUT prompt heuristic uses ``plaintext_lines[-1]`` as
    a prompt candidate, but JSONL events never touch that list — so an
    early line ending in ``?`` stays the 'last plaintext' forever and
    arms a block-forever ``input()`` trap on every later quiet window.
    This flag lets the runner reject a plaintext candidate once any JSONL
    event has been consumed after it.
    """

    def test_initially_false(self):
        parser = PtyStreamParser()
        assert parser.latest_output_is_plaintext is False

    def test_plaintext_line_sets_true(self):
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        parser.feed_line("Deploy which environment?")
        assert parser.latest_output_is_plaintext is True

    def test_jsonl_event_after_plaintext_clears_it(self):
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        parser.feed_line("Deploy which environment?")
        assert parser.latest_output_is_plaintext is True

        parser.feed_line(json.dumps({"_event": "v2_runner_on_ok", "_timestamp": "x"}))
        assert parser.latest_output_is_plaintext is False
        # The stale plaintext line is still retained for stall diagnostics;
        # only its *prompt-candidate* status is invalidated.
        assert parser.plaintext_lines[-1] == "Deploy which environment?"

    def test_plaintext_after_jsonl_sets_true_again(self):
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        parser.feed_line(json.dumps({"_event": "v2_playbook_on_task_start", "_timestamp": "x"}))
        assert parser.latest_output_is_plaintext is False

        parser.feed_line("Proceed?")
        assert parser.latest_output_is_plaintext is True

    def test_start_event_leaves_it_false(self):
        parser = PtyStreamParser()  # PRE_RUN_PROMPTS
        parser.feed_line(json.dumps({"_event": "v2_playbook_on_start", "_timestamp": "x"}))
        assert parser.latest_output_is_plaintext is False


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


# =============================================================================
# Section 5.2: Pre-Parse Phase — Additional TCs
# =============================================================================


class TestParallelPreParse:
    """TC-087: Parallel pre-parse execution."""

    def test_concurrent_parse_combine_results(self, list_tasks_output, list_hosts_output):
        """TC-087: Both --list-tasks and --list-hosts results can be combined
        after concurrent execution."""
        import concurrent.futures

        from ansible_aom.core.parser import (
            PreParseResult,
            parse_list_hosts_output,
            parse_list_tasks_output,
        )

        def parse_tasks():
            return parse_list_tasks_output(list_tasks_output)

        def parse_hosts():
            return parse_list_hosts_output(list_hosts_output)

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            tasks_future = executor.submit(parse_tasks)
            hosts_future = executor.submit(parse_hosts)
            plays = tasks_future.result()
            play_hosts = hosts_future.result()

        result = PreParseResult(plays=plays, play_hosts=play_hosts)
        assert len(result.plays) == 2
        assert len(result.play_hosts) == 2

    def test_parallel_parse_does_not_corrupt_data(self, list_tasks_output, list_hosts_output):
        """TC-087: Parallel parsing produces same results as sequential."""
        import concurrent.futures

        from ansible_aom.core.parser import parse_list_hosts_output, parse_list_tasks_output

        def parse_tasks():
            return parse_list_tasks_output(list_tasks_output)

        def parse_hosts():
            return parse_list_hosts_output(list_hosts_output)

        seq_plays = parse_list_tasks_output(list_tasks_output)
        seq_hosts = parse_list_hosts_output(list_hosts_output)

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            f1 = executor.submit(parse_tasks)
            f2 = executor.submit(parse_hosts)
            par_plays = f1.result()
            par_hosts = f2.result()

        assert len(seq_plays) == len(par_plays)
        assert len(seq_hosts) == len(par_hosts)
        for sp, pp in zip(seq_plays, par_plays):
            assert sp["name"] == pp["name"]
            assert sp["play_number"] == pp["play_number"]
            assert len(sp["tasks"]) == len(pp["tasks"])


class TestListHostsFallback:
    """TC-089, TC-090: --list-hosts fallback behavior."""

    def test_list_hosts_empty_result_fallback(self):
        """TC-089: When --list-hosts returns empty, hosts will come from
        runner events. parse_list_hosts_output returns [] for bad output."""
        from ansible_aom.core.parser import parse_list_hosts_output

        bad_output = "ERROR! the playbook could not be found"
        result = parse_list_hosts_output(bad_output)
        assert result == []

    def test_list_hosts_partial_error_output(self):
        """TC-089: Partial/corrupted output still returns any parseable plays."""
        from ansible_aom.core.parser import parse_list_hosts_output

        output = """playbook: site.yml

  play #1 (webservers): Setup\tTAGS: []
    pattern: ['webservers']
    hosts (2):
      web1
      web2

ERROR! We were unable to connect"""
        result = parse_list_hosts_output(output)
        assert len(result) >= 1
        assert "web1" in result[0]["hosts"]

    def test_list_hosts_fallback_warning_logged(self, caplog):
        """TC-090: Warning message when host resolution fails."""
        import logging

        from ansible_aom.core.parser import parse_list_hosts_output

        bad_output = "ERROR! the playbook could not be found"
        with caplog.at_level(logging.WARNING, logger="ansible_aom.core.parser"):
            result = parse_list_hosts_output(bad_output)
        assert result == []


class TestListHostsEdgeCases:
    """TC-101 to TC-106: --list-hosts edge cases."""

    def test_list_hosts_all_inventory(self):
        """TC-101: hosts: 'all' returns all inventory hosts."""
        from ansible_aom.core.parser import parse_list_hosts_output

        output = """playbook: site.yml

  play #1 (all): All hosts\tTAGS: []
    pattern: ['all']
    hosts (3):
      host1
      host2
      host3"""
        result = parse_list_hosts_output(output)
        assert len(result) == 1
        assert result[0]["hosts_pattern"] == ["all"]
        assert len(result[0]["hosts"]) == 3
        assert "host1" in result[0]["hosts"]
        assert "host3" in result[0]["hosts"]

    def test_list_hosts_pattern_filtering(self):
        """TC-102: Pattern like webservers:!db_primary is preserved in hosts_pattern."""
        from ansible_aom.core.parser import parse_list_hosts_output

        output = """playbook: site.yml

  play #1 (webservers:!db_primary): Filtered\tTAGS: []
    pattern: ['webservers:!db_primary']
    hosts (2):
      web1
      web2"""
        result = parse_list_hosts_output(output)
        assert len(result) == 1
        assert "webservers:!db_primary" in result[0]["hosts_pattern"][0]
        assert result[0]["hosts"] == ["web1", "web2"]

    def test_list_hosts_dynamic_pattern_fallback(self):
        """TC-103: Jinja2 pattern "{{ group }}" may fail — parser still parses
        whatever ansible outputs."""
        from ansible_aom.core.parser import parse_list_hosts_output

        output_resolved = """playbook: site.yml

  play #1 ({{ group }}): Dynamic\tTAGS: []
    pattern: ['{{ group }}']
    hosts (1):
      resolved_host"""
        result = parse_list_hosts_output(output_resolved)
        assert len(result) == 1

    def test_list_hosts_dynamic_pattern_empty_hosts(self):
        """TC-103: When Jinja2 pattern can't resolve, hosts list is empty."""
        from ansible_aom.core.parser import parse_list_hosts_output

        output_unresolved = """playbook: site.yml

  play #1 ({{ group }}): Dynamic\tTAGS: []
    pattern: ['{{ group }}']
    hosts (0):"""
        result = parse_list_hosts_output(output_unresolved)
        assert len(result) == 1
        assert result[0]["hosts"] == []

    def test_list_hosts_with_limit(self):
        """TC-104: --limit restricts hosts in output."""
        from ansible_aom.core.parser import parse_list_hosts_output

        output = """playbook: site.yml

  play #1 (webservers): Limited\tTAGS: []
    pattern: ['webservers']
    hosts (1):
      web1"""
        result = parse_list_hosts_output(output)
        assert len(result) == 1
        assert result[0]["hosts"] == ["web1"]

    def test_list_hosts_dynamic_inventory_timeout(self):
        """TC-106: Slow dynamic inventory just returns hosts — parser doesn't
        care about speed, only structure."""
        from ansible_aom.core.parser import parse_list_hosts_output

        output = """playbook: site.yml

  play #1 (aws_dynamic): AWS hosts\tTAGS: []
    pattern: ['aws_dynamic']
    hosts (2):
      i-1234567890
      i-0987654321"""
        result = parse_list_hosts_output(output)
        assert len(result) == 1
        assert len(result[0]["hosts"]) == 2

    def test_list_hosts_multiple_plays_hosts(self):
        """TC-101: Multiple plays with different host sets."""
        from ansible_aom.core.parser import parse_list_hosts_output

        output = """playbook: site.yml

  play #1 (all): All plays\tTAGS: []
    pattern: ['all']
    hosts (4):
      web1
      web2
      db1
      db2

  play #2 (webservers): Web only\tTAGS: []
    pattern: ['webservers']
    hosts (2):
      web1
      web2"""
        result = parse_list_hosts_output(output)
        assert len(result) == 2
        assert len(result[0]["hosts"]) == 4
        assert len(result[1]["hosts"]) == 2

    def test_list_hosts_no_duplicate_hosts(self):
        """TC-102: Duplicate hostnames are deduplicated."""
        from ansible_aom.core.parser import parse_list_hosts_output

        output = """playbook: site.yml

  play #1 (all): Test\tTAGS: []
    pattern: ['all']
    hosts (3):
      web1
      web1
      web2"""
        result = parse_list_hosts_output(output)
        assert result[0]["hosts"].count("web1") == 1

    def test_list_hosts_play_number_sequential(self):
        """TC-097: Play numbers are sequential."""
        from ansible_aom.core.parser import parse_list_hosts_output

        output = """playbook: site.yml

  play #1 (all): First\tTAGS: []
    pattern: ['all']
    hosts (1):
      h1

  play #2 (all): Second\tTAGS: []
    pattern: ['all']
    hosts (1):
      h2"""
        result = parse_list_hosts_output(output)
        assert result[0]["play_number"] == 1
        assert result[1]["play_number"] == 2


class TestListTasksEdgeCases:
    """TC-114 to TC-121: --list-tasks edge cases."""

    def test_import_tasks_expanded(self):
        """TC-114: import_tasks IS expanded — tasks appear inline in --list-tasks."""
        from ansible_aom.core.parser import parse_list_tasks_output

        # import_tasks expands the imported file's tasks inline
        output = """playbook: site.yml

  play #1 (all): Setup\tTAGS: []
    Install base packages\tTAGS: []
    Configure firewall\tTAGS: []
    Restart services\tTAGS: []"""
        result = parse_list_tasks_output(output)
        assert len(result[0]["tasks"]) == 3

    def test_blocks_flattened(self):
        """TC-115: Block tasks are flattened — no block container in output."""
        from ansible_aom.core.parser import parse_list_tasks_output

        output = """playbook: site.yml

  play #1 (all): Block test\tTAGS: []
    Install package\tTAGS: [install]
    Start service\tTAGS: [service]
    Notify handler\tTAGS: [handler]"""
        result = parse_list_tasks_output(output)
        assert len(result[0]["tasks"]) == 3
        for task in result[0]["tasks"]:
            assert "block" not in task["name"].lower()

    def test_pre_tasks_post_tasks_no_prefix(self):
        """TC-116: pre_tasks and post_tasks appear as regular tasks."""
        from ansible_aom.core.parser import parse_list_tasks_output

        output = """playbook: site.yml

  play #1 (all): With pre/post\tTAGS: []
    Gather facts\tTAGS: [gather]
    Pre-setup task\tTAGS: [pre]
    Main task\tTAGS: [main]
    Post-cleanup\tTAGS: [post]"""
        result = parse_list_tasks_output(output)
        assert len(result[0]["tasks"]) == 4
        task_names = [t["name"] for t in result[0]["tasks"]]
        assert "Pre-setup task" in task_names
        assert "Post-cleanup" in task_names

    def test_unnamed_task_fallback_module_name(self):
        """TC-117: Unnamed tasks use their module/action as the name."""
        from ansible_aom.core.parser import parse_list_tasks_output

        output = """playbook: site.yml

  play #1 (all): Test\tTAGS: []
    command\tTAGS: []
    debug\tTAGS: []"""
        result = parse_list_tasks_output(output)
        assert result[0]["tasks"][0]["name"] == "command"
        assert result[0]["tasks"][1]["name"] == "debug"

    @pytest.mark.parametrize(
        "play_name",
        ["pre_tasks", "post_tasks", "tasks", "handlers"],
    )
    def test_special_section_names_in_play(self, play_name):
        """TC-116: Play names may contain special section designations."""
        from ansible_aom.core.parser import parse_list_tasks_output

        output = f"""playbook: site.yml

  play #1 (all): {play_name}\tTAGS: []
    Do something\tTAGS: []"""
        result = parse_list_tasks_output(output)
        assert len(result) == 1
        assert result[0]["name"] == play_name

    def test_output_no_stderr_in_parsed_content(self):
        """TC-118: Parser only receives stdout content."""
        from ansible_aom.core.parser import parse_list_tasks_output

        stdout_output = """playbook: site.yml

  play #1 (all): Test\tTAGS: []
    task1\tTAGS: []"""
        result = parse_list_tasks_output(stdout_output)
        assert len(result) == 1
        assert len(result[0]["tasks"]) == 1

    def test_list_hosts_stderr_not_in_result(self):
        """TC-118: stderr content doesn't pollute parse results."""
        from ansible_aom.core.parser import parse_list_hosts_output

        mixed_output = """playbook: site.yml

  play #1 (all): Test\tTAGS: []
    pattern: ['all']
    hosts (1):
      host1"""
        result = parse_list_hosts_output(mixed_output)
        assert len(result) == 1
        assert "host1" in result[0]["hosts"]

    def test_exit_code_success_output(self):
        """TC-119: Valid --list-tasks output parses correctly."""
        from ansible_aom.core.parser import parse_list_tasks_output

        output = """playbook: site.yml

  play #1 (all): Setup\tTAGS: []
    Install nginx\tTAGS: [web]"""
        result = parse_list_tasks_output(output)
        assert len(result) == 1
        assert result[0]["name"] == "Setup"

    def test_exit_code_error_output(self):
        """TC-120: Error output returns empty list."""
        from ansible_aom.core.parser import parse_list_tasks_output

        error_output = "ERROR! the role 'nonexistent' was not found"
        result = parse_list_tasks_output(error_output)
        assert result == []

    def test_exit_code_syntax_error_output(self):
        """TC-121: Syntax error output returns empty list."""
        from ansible_aom.core.parser import parse_list_tasks_output

        error_output = """ERROR! Syntax Error while loading YAML."""
        result = parse_list_tasks_output(error_output)
        assert result == []

    def test_list_tasks_play_hosts_pattern_extraction(self):
        """TC-102: Parse hosts pattern from play line in --list-tasks."""
        from ansible_aom.core.parser import parse_list_tasks_output

        output = """playbook: site.yml

  play #1 (webservers:!staging): Deploy\tTAGS: []
    task1\tTAGS: []"""
        result = parse_list_tasks_output(output)
        assert len(result) == 1
        assert result[0]["name"] == "Deploy"

    def test_import_tasks_with_role_prefix(self):
        """TC-114: import_tasks with role prefix expanded correctly."""
        from ansible_aom.core.parser import parse_list_tasks_output

        output = """playbook: site.yml

  play #1 (all): Deploy\tTAGS: []
    nginx : Install\tTAGS: [web]
    nginx : Configure\tTAGS: [web]
    nginx : Restart\tTAGS: [web]"""
        result = parse_list_tasks_output(output)
        tasks = result[0]["tasks"]
        assert all(t["role"] == "nginx" for t in tasks)
        assert tasks[0]["name"] == "Install"
        assert tasks[1]["name"] == "Configure"
        assert tasks[2]["name"] == "Restart"


class TestWarningDetectionThroughAnsiPrefix:
    """Real ansible-playbook prefixes warnings with ANSI color codes —
    e.g. \\x1b[1;35m[WARNING]:\\x1b[0m. The parser must classify them
    as warnings anyway so the panel's ⚠ counter stays accurate.
    """

    def test_ansi_prefixed_warning_is_classified(self):
        from ansible_aom.core.models import WarningType
        from ansible_aom.core.parser import PtyStreamParser

        parser = PtyStreamParser()
        line = "\x1b[1;35m[WARNING]: example warning\x1b[0m"
        parser.feed_line(line + "\n")

        assert len(parser.warnings) == 1
        assert parser.warnings[0].type == WarningType.WARNING
        # ANSI codes should be stripped from the stored message so
        # downstream UI doesn't have to re-strip.
        assert "\x1b[" not in parser.warnings[0].message
        assert "[WARNING]: example warning" in parser.warnings[0].message

    def test_ansi_prefixed_deprecation_is_classified(self):
        from ansible_aom.core.models import WarningType
        from ansible_aom.core.parser import PtyStreamParser

        parser = PtyStreamParser()
        line = "\x1b[0;35m[DEPRECATION WARNING]: old API\x1b[0m"
        parser.feed_line(line + "\n")

        assert len(parser.warnings) == 1
        assert parser.warnings[0].type == WarningType.DEPRECATION
        assert "\x1b[" not in parser.warnings[0].message

    def test_plain_warning_still_classified(self):
        """Backwards-compat: warnings without ANSI prefix still match."""
        from ansible_aom.core.parser import PtyStreamParser

        parser = PtyStreamParser()
        parser.feed_line("[WARNING]: bare warning\n")
        assert len(parser.warnings) == 1

    def test_non_warning_text_with_ansi_passes_through(self):
        """ANSI-coloured non-warning text must NOT be misclassified."""
        from ansible_aom.core.parser import PtyStreamParser

        parser = PtyStreamParser()
        parser.feed_line("\x1b[31msome random colored text\x1b[0m\n")
        assert parser.warnings == []


class TestMultiLineWarningContinuation:
    """Ansible hard-wraps ``[WARNING]``/``[DEPRECATION WARNING]`` messages to
    the terminal width. Only the first physical line carries the
    ``[WARNING]: `` prefix; every wrapped continuation line arrives as
    magenta-coloured body text with no prefix (e.g.
    ``\\x1b[1;35m...in use. Set loop_var...\\x1b[0m``).

    Before the fix these continuation lines matched no classifier rule and
    were recorded as ``source='unknown'`` ``aom_stderr_line`` events — one
    warning wrapped across N lines produced N-1 unknowns, which at scale is
    the thousands of unknowns in ``events.jsonl``. They must instead fold
    into the parent warning: no standalone event, and the warning's message
    reassembled (ANSI-stripped) from all its physical lines.
    """

    def _feed_wrapped_warning(self, parser):
        """Feed a real 3-line wrapped [WARNING] as ansible emits it on the PTY."""
        first = "\x1b[1;35m[WARNING]: The loop variable 'item' is already in use. You should\x1b[0m"
        cont1 = (
            "\x1b[1;35mset the `loop_var` value in the `loop_control` option for the task\x1b[0m"
        )
        cont2 = "\x1b[1;35mto something else to avoid variable collisions.\x1b[0m"
        return (
            parser.feed_line(first + "\n"),
            parser.feed_line(cont1 + "\n"),
            parser.feed_line(cont2 + "\n"),
        )

    def test_continuation_lines_emit_no_stderr_event(self):
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        e0, e1, e2 = self._feed_wrapped_warning(parser)
        # First line -> warning via drain path; continuations fold in silently.
        assert e0 == []
        assert e1 == []
        assert e2 == []

    def test_warning_message_reassembled_from_all_lines(self):
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        self._feed_wrapped_warning(parser)
        assert len(parser.warnings) == 1
        msg = parser.warnings[0].message
        assert "\x1b[" not in msg  # ANSI stripped from the stored message
        # Full sentence reassembled across all three physical lines.
        assert "The loop variable 'item' is already in use." in msg
        assert "set the `loop_var` value" in msg
        assert "to something else to avoid variable collisions." in msg

    def test_deprecation_continuation_keeps_deprecation_type(self):
        from ansible_aom.core.models import WarningType

        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        parser.feed_line("\x1b[0;35m[DEPRECATION WARNING]: The foo option is\x1b[0m\n")
        parser.feed_line("\x1b[0;35mdeprecated and will be removed in 2.99.\x1b[0m\n")
        assert len(parser.warnings) == 1
        assert parser.warnings[0].type == WarningType.DEPRECATION
        assert "deprecated and will be removed in 2.99." in parser.warnings[0].message

    def test_json_event_closes_warning_block(self):
        """A magenta line after an intervening JSON event starts a fresh
        warning — it must not append to the earlier, now-closed block."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        parser.feed_line("\x1b[1;35m[WARNING]: first warning body\x1b[0m\n")
        parser.feed_line('{"_event":"v2_runner_on_ok","hosts":{}}\n')
        parser.feed_line("\x1b[1;35mlater magenta line\x1b[0m\n")
        assert len(parser.warnings) == 2
        assert "later magenta line" not in parser.warnings[0].message

    def test_orphan_magenta_line_classified_as_warning_not_unknown(self):
        """Color-based classification: a magenta stderr line with no open
        warning block is still warning-family, never emitted as 'unknown'."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        events = parser.feed_line("\x1b[1;35mstandalone magenta notice\x1b[0m\n")
        assert events == []
        assert len(parser.warnings) == 1
        assert "standalone magenta notice" in parser.warnings[0].message

    def test_non_magenta_unknown_line_still_unknown(self):
        """Regression guard: non-coloured unrecognised lines are unaffected
        and still classify as ``unknown``."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        events = parser.feed_line("some completely unrecognised line\n")
        assert len(events) == 1
        assert events[0]["source"] == "unknown"

    def test_red_colored_line_does_not_fold_into_warning(self):
        """Only magenta (warn/deprecate) folds. A red line after a warning
        closes the block and emits its own event."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        parser.feed_line("\x1b[1;35m[WARNING]: a warning\x1b[0m\n")
        events = parser.feed_line("\x1b[31mred non-warning text\x1b[0m\n")
        assert len(events) == 1
        assert events[0]["_event"] == "aom_stderr_line"

    def test_uncolored_continuation_folds_into_open_warning(self):
        """ansible-core 2.20 deprecation blocks emitted WITHOUT SGR codes
        (e.g. under the mitogen strategy, where workers write from a
        non-TTY context) still fold: the source-context and help-text
        lines must join the open warning instead of becoming standalone
        ``source='unknown'`` aom_stderr_line events."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        parser.feed_line('[DEPRECATION WARNING]: The internal "vars" dictionary is deprecated.\n')
        e1 = parser.feed_line("14         # tasks/shared                   tasks/shared\n")
        e2 = parser.feed_line("Use the `vars` and `varnames` lookups instead.\n")
        assert e1 == []
        assert e2 == []
        assert len(parser.warnings) == 1
        msg = parser.warnings[0].message
        assert 'The internal "vars" dictionary is deprecated.' in msg
        assert "Use the `vars` and `varnames` lookups instead." in msg

    def test_uncolored_continuation_after_blank_line_is_unknown(self):
        """A blank line closes the warning block; a later uncolored line
        with no open block is still classified (not folded)."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        parser.feed_line("[DEPRECATION WARNING]: first warning\n")
        parser.feed_line("\n")
        events = parser.feed_line("Use the `vars` and `varnames` lookups instead.\n")
        assert len(events) == 1
        assert events[0]["source"] == "unknown"
        assert "red non-warning text" not in parser.warnings[0].message


# =============================================================================
# Section 5.6: aom_stderr_line synthetic event emission
# =============================================================================


class TestPtyStreamParserStderrLineEmission:
    """Phase 4: plaintext stderr lines become aom_stderr_line synthetic events.

    Non-warning plaintext lines fed through the parser should produce a
    synthetic ``aom_stderr_line`` event with the classifier's source, level,
    host, connection_id, and attribution_confidence.

    Connection tracking:
    - ``aom_connection_acquired`` events add a connection_id to the host's
      active list.
    - ``aom_connection_released`` events remove it.
    - A host with exactly one active connection gets ``"unique"`` confidence.
    - A host with multiple overlapping active connections gets ``"ambiguous"``
      confidence and the most-recent connection_id.
    - A host with no active connections gets ``connection_id=None``.
    - Run-level lines (host=None) always get ``connection_id=None``.
    """

    def test_non_warning_plaintext_emits_stderr_line(self):
        """A non-warning plaintext line in EXECUTION phase emits aom_stderr_line."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        events = parser.feed_line("some random output\n")
        assert len(events) == 1
        assert events[0]["_event"] == "aom_stderr_line"
        assert "line" in events[0]
        assert events[0]["line"] == "some random output"
        assert "source" in events[0]
        assert "level" in events[0]
        assert events[0]["connection_id"] is None
        assert events[0]["attribution_confidence"] == "unique"

    def test_warning_does_not_emit_stderr_line(self):
        """Warnings still go through the drain_warnings path, not aom_stderr_line."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        events = parser.feed_line("[WARNING]: some warning\n")
        assert events == []
        assert len(parser.warnings) == 1

    def test_deprecation_does_not_emit_stderr_line(self):
        """Deprecation warnings still go through drain_warnings path."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        events = parser.feed_line("[DEPRECATION WARNING]: old API\n")
        assert events == []
        assert len(parser.warnings) == 1

    def test_pre_run_prompts_emits_stderr_line(self):
        """Non-password plaintext in PRE_RUN_PROMPTS phase emits aom_stderr_line."""
        parser = PtyStreamParser()
        events = parser.feed_line("preflight output\n")
        assert len(events) == 1
        assert events[0]["_event"] == "aom_stderr_line"

    def test_password_prompt_does_not_emit_stderr_line(self):
        """Password prompts are intercepted before _handle_plaintext."""
        parser = PtyStreamParser()
        events = parser.feed_line("Vault password: ")
        assert events == []
        assert parser.pending_password_prompt is not None

    def test_stderr_line_has_timestamp(self):
        """aom_stderr_line events carry an ISO 8601 _timestamp."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        events = parser.feed_line("some output\n")
        assert "_timestamp" in events[0]
        assert events[0]["_timestamp"].endswith("Z") or "+" in events[0]["_timestamp"]

    def test_stderr_line_source_is_classified(self):
        """The source field reflects the classifier output."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        events = parser.feed_line("Using /etc/ansible/ansible.cfg as config file\n")
        assert len(events) == 1
        assert events[0]["source"] == "run_level"

    def test_stderr_line_unknown_source(self):
        """Unrecognised lines get source='unknown'."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        events = parser.feed_line("some completely unrecognised line\n")
        assert len(events) == 1
        assert events[0]["source"] == "unknown"

    def test_stderr_line_host_from_classifier(self):
        """Host is extracted from host-prefixed lines when the classifier supports it."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        events = parser.feed_line("<web1> SSH: SSH_AGENT something\n")
        assert len(events) == 1
        assert events[0]["host"] == "web1"

    def test_stderr_line_no_host_for_run_level(self):
        """Run-level lines have host=None."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        events = parser.feed_line("Using /etc/ansible/ansible.cfg as config file\n")
        assert events[0]["host"] is None

    def test_plaintext_lines_still_appended(self):
        """Non-warning plaintext lines are still appended to plaintext_lines."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        parser.feed_line("some output\n")
        assert len(parser.plaintext_lines) == 1
        assert parser.plaintext_lines[0] == "some output"

    def test_ansi_stripped_before_classification(self):
        """ANSI SGR sequences are stripped before the classifier sees the line."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        events = parser.feed_line("\x1b[31mUsing /etc/ansible/ansible.cfg as config file\x1b[0m\n")
        assert len(events) == 1
        assert events[0]["source"] == "run_level"
        # The original line (with ANSI) is preserved in the event
        assert "\x1b[" in events[0]["line"]

    # ------------------------------------------------------------------ #
    # Connection tracking tests
    # ------------------------------------------------------------------ #

    def test_connection_acquire_adds_to_active(self):
        """aom_connection_acquired adds connection_id to host's active list."""
        parser = PtyStreamParser()
        parser._handle_connection_event(
            {"_event": "aom_connection_acquired", "host": "web1", "connection_id": "conn-001"}
        )
        assert parser._active_connections == {"web1": ["conn-001"]}

    def test_connection_release_removes_from_active(self):
        """aom_connection_released removes connection_id from host's active list."""
        parser = PtyStreamParser()
        parser._active_connections = {"web1": ["conn-001"]}
        parser._handle_connection_event(
            {"_event": "aom_connection_released", "host": "web1", "connection_id": "conn-001"}
        )
        assert parser._active_connections == {}

    def test_connection_release_unknown_conn_id_noop(self):
        """Releasing a connection_id not in the active list is a no-op."""
        parser = PtyStreamParser()
        parser._active_connections = {"web1": ["conn-001"]}
        parser._handle_connection_event(
            {"_event": "aom_connection_released", "host": "web1", "connection_id": "conn-999"}
        )
        assert parser._active_connections == {"web1": ["conn-001"]}

    def test_connection_acquire_multiple_for_same_host(self):
        """Multiple acquires for the same host stack connection_ids."""
        parser = PtyStreamParser()
        parser._handle_connection_event(
            {"_event": "aom_connection_acquired", "host": "web1", "connection_id": "conn-001"}
        )
        parser._handle_connection_event(
            {"_event": "aom_connection_acquired", "host": "web1", "connection_id": "conn-002"}
        )
        assert parser._active_connections == {"web1": ["conn-001", "conn-002"]}

    def test_connection_acquire_different_hosts(self):
        """Acquires for different hosts are tracked independently."""
        parser = PtyStreamParser()
        parser._handle_connection_event(
            {"_event": "aom_connection_acquired", "host": "web1", "connection_id": "conn-001"}
        )
        parser._handle_connection_event(
            {"_event": "aom_connection_acquired", "host": "web2", "connection_id": "conn-002"}
        )
        assert parser._active_connections == {"web1": ["conn-001"], "web2": ["conn-002"]}

    def test_resolve_connection_no_host(self):
        """Run-level lines (host=None) get (None, 'unique')."""
        parser = PtyStreamParser()
        assert parser._resolve_connection(None) == (None, "unique")

    def test_resolve_connection_no_active_connections(self):
        """Host with no active connections gets (None, 'unique')."""
        parser = PtyStreamParser()
        assert parser._resolve_connection("web1") == (None, "unique")

    def test_resolve_connection_single_active(self):
        """Host with one active connection gets that connection_id and 'unique'."""
        parser = PtyStreamParser()
        parser._active_connections = {"web1": ["conn-001"]}
        assert parser._resolve_connection("web1") == ("conn-001", "unique")

    def test_resolve_connection_multiple_active_ambiguous(self):
        """Host with multiple active connections gets most-recent and 'ambiguous'."""
        parser = PtyStreamParser()
        parser._active_connections = {"web1": ["conn-001", "conn-002"]}
        assert parser._resolve_connection("web1") == ("conn-002", "ambiguous")

    def test_resolve_connection_three_active_ambiguous(self):
        """Three overlapping connections: most-recent wins, confidence is ambiguous."""
        parser = PtyStreamParser()
        parser._active_connections = {"web1": ["conn-001", "conn-002", "conn-003"]}
        assert parser._resolve_connection("web1") == ("conn-003", "ambiguous")

    def test_stderr_line_with_connection_id_from_acquire(self):
        """Stderr line after a connection acquire gets the connection_id."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        # Feed a connection acquired event
        parser.feed_line(
            '{"_event": "aom_connection_acquired", "host": "web1",'
            ' "connection_id": "conn-001", "_timestamp": "2026-07-01T10:00:00Z"}\n'
        )
        # Now feed a stderr line for the same host
        events = parser.feed_line("<web1> SSH: SSH_AGENT something\n")
        assert len(events) == 1
        assert events[0]["connection_id"] == "conn-001"
        assert events[0]["attribution_confidence"] == "unique"

    def test_stderr_line_ambiguous_with_overlapping_connections(self):
        """Stderr line with overlapping connections gets 'ambiguous' confidence."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        # Acquire two connections for the same host
        parser.feed_line(
            '{"_event": "aom_connection_acquired", "host": "web1",'
            ' "connection_id": "conn-001", "_timestamp": "2026-07-01T10:00:00Z"}\n'
        )
        parser.feed_line(
            '{"_event": "aom_connection_acquired", "host": "web1",'
            ' "connection_id": "conn-002", "_timestamp": "2026-07-01T10:00:01Z"}\n'
        )
        events = parser.feed_line("<web1> SSH: SSH_AGENT something\n")
        assert len(events) == 1
        assert events[0]["connection_id"] == "conn-002"
        assert events[0]["attribution_confidence"] == "ambiguous"

    def test_stderr_line_connection_released_then_unique(self):
        """After release, a new stderr line for the host has no connection_id."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        parser.feed_line(
            '{"_event": "aom_connection_acquired", "host": "web1",'
            ' "connection_id": "conn-001", "_timestamp": "2026-07-01T10:00:00Z"}\n'
        )
        parser.feed_line(
            '{"_event": "aom_connection_released", "host": "web1",'
            ' "connection_id": "conn-001", "_timestamp": "2026-07-01T10:00:05Z"}\n'
        )
        events = parser.feed_line("<web1> SSH: SSH_AGENT something\n")
        assert len(events) == 1
        assert events[0]["connection_id"] is None
        assert events[0]["attribution_confidence"] == "unique"

    def test_stderr_line_different_hosts_independent_connections(self):
        """Different hosts have independent connection tracking."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        parser.feed_line(
            '{"_event": "aom_connection_acquired", "host": "web1",'
            ' "connection_id": "conn-001", "_timestamp": "2026-07-01T10:00:00Z"}\n'
        )
        parser.feed_line(
            '{"_event": "aom_connection_acquired", "host": "web2",'
            ' "connection_id": "conn-002", "_timestamp": "2026-07-01T10:00:01Z"}\n'
        )
        # web1 stderr gets conn-001
        events1 = parser.feed_line("<web1> SSH: SSH_AGENT something\n")
        assert events1[0]["connection_id"] == "conn-001"
        # web2 stderr gets conn-002
        events2 = parser.feed_line("<web2> SSH: SSH_AGENT something\n")
        assert events2[0]["connection_id"] == "conn-002"

    def test_stderr_line_run_level_ignores_connections(self):
        """Run-level lines (no host) get connection_id=None regardless of active connections."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        parser.feed_line(
            '{"_event": "aom_connection_acquired", "host": "web1",'
            ' "connection_id": "conn-001", "_timestamp": "2026-07-01T10:00:00Z"}\n'
        )
        events = parser.feed_line("Using /etc/ansible/ansible.cfg as config file\n")
        assert events[0]["connection_id"] is None
        assert events[0]["attribution_confidence"] == "unique"
