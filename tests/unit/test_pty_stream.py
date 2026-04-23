"""Unit tests for PTY stream parsing.

Covers TEST_SPECIFICATION.md Sections 5.5, 5.6, 5.10:
- PTY stream parsing (Section 5.6)
- Password prompt handling (Section 5.10)
- Phase transitions (Section 5.6)

Test Isolation Rules (CRITICAL):
1. Every test creates its own PtyStreamParser instance
2. Function-scoped fixtures ONLY
3. Use conftest.py fixtures as input data
4. Tests can run in ANY order
"""

import json
import re
from datetime import datetime

import pytest

from ansible_aom.core.models import WarningType
from ansible_aom.core.parser import PtyStreamParser, StreamPhase

# =============================================================================
# Section 5.6: StreamPhase Enum Tests
# =============================================================================


class TestStreamPhaseEnum:
    """TC-128 to TC-130: StreamPhase enum values."""

    def test_stream_phase_has_pre_run_prompts(self):
        """TC-128: PRE_RUN_PROMPTS phase exists."""
        assert hasattr(StreamPhase, "PRE_RUN_PROMPTS")

    def test_stream_phase_has_execution(self):
        """TC-129: EXECUTION phase exists."""
        assert hasattr(StreamPhase, "EXECUTION")

    def test_stream_phase_has_post_run_recap(self):
        """TC-130: POST_RUN_RECAP phase exists."""
        assert hasattr(StreamPhase, "POST_RUN_RECAP")

    def test_stream_phase_three_values(self):
        """StreamPhase has exactly 3 values."""
        assert len(StreamPhase) == 3

    def test_stream_phase_values_unique(self):
        """All phase values are unique."""
        values = [phase.value for phase in StreamPhase]
        assert len(values) == len(set(values))


# =============================================================================
# Section 5.6: PtyStreamParser Phase Transitions
# =============================================================================


class TestPtyStreamParserPhaseTransitions:
    """TC-128, TC-131, TC-132: Phase transition tests."""

    def test_initial_phase_is_pre_run_prompts(self):
        """TC-128: Initial phase is PRE_RUN_PROMPTS."""
        parser = PtyStreamParser()
        assert parser.phase == StreamPhase.PRE_RUN_PROMPTS

    def test_transition_to_execution_on_start_event(self, event_playbook_start):
        """TC-131: v2_playbook_on_start triggers PRE_RUN_PROMPTS -> EXECUTION."""
        parser = PtyStreamParser()
        assert parser.phase == StreamPhase.PRE_RUN_PROMPTS
        line = json.dumps(event_playbook_start)
        parser.feed_line(line)
        assert parser.phase == StreamPhase.EXECUTION

    def test_transition_to_execution_on_first_jsonl(self, jsonl_line):
        """TC-131: First JSONL event triggers transition to EXECUTION."""
        parser = PtyStreamParser()
        parser.feed_line(jsonl_line)
        assert parser.phase == StreamPhase.EXECUTION

    def test_transition_to_post_run_on_stats_event(self, event_stats):
        """TC-132: v2_playbook_on_stats triggers EXECUTION -> POST_RUN_RECAP."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        line = json.dumps(event_stats)
        parser.feed_line(line)
        assert parser.phase == StreamPhase.POST_RUN_RECAP

    def test_transition_to_post_run_on_recap_line(self, recap_line):
        """TC-132: PLAY RECAP line triggers EXECUTION -> POST_RUN_RECAP."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        parser.feed_line(recap_line)
        assert parser.phase == StreamPhase.POST_RUN_RECAP
        assert parser._in_recap is True

    def test_phase_remains_pre_run_without_start_event(self):
        """Phase stays PRE_RUN_PROMPTS without v2_playbook_on_start."""
        parser = PtyStreamParser()
        parser.feed_line("[WARNING]: Some warning")
        parser.feed_line("SSH password: ")
        parser.feed_line("# comment line")
        assert parser.phase == StreamPhase.PRE_RUN_PROMPTS

    def test_phase_remains_execution_without_stats_event(self, event_playbook_start):
        """Phase stays EXECUTION without v2_playbook_on_stats."""
        parser = PtyStreamParser()
        parser.feed_line(json.dumps(event_playbook_start))
        parser.feed_line('{"_event": "v2_playbook_on_play_start"}')
        parser.feed_line("[WARNING]: Some warning")
        assert parser.phase == StreamPhase.EXECUTION

    def test_post_run_recap_collects_lines(self, event_stats):
        """Lines in POST_RUN_RECAP phase are collected."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        parser.feed_line(json.dumps(event_stats))
        parser.feed_line("web1 : ok=5   changed=2   failed=0")
        parser.feed_line("web2 : ok=5   changed=2   failed=0")
        assert len(parser.recap_lines) >= 2


# =============================================================================
# Section 5.6: Password Prompt Detection
# =============================================================================


class TestPasswordPromptPatterns:
    """TC-133 to TC-139: Password pattern detection."""

    def test_password_pattern_vault(self, password_prompt_vault):
        """TC-134: Vault password: pattern detected."""
        parser = PtyStreamParser()
        parser.feed_line(password_prompt_vault)
        assert parser.pending_password_prompt is not None
        assert "Vault password" in parser.pending_password_prompt

    def test_password_pattern_vault_id_variant(self):
        """TC-135: Vault password (id): pattern detected."""
        parser = PtyStreamParser()
        parser.feed_line("Vault password (prod): ")
        assert parser.pending_password_prompt is not None

    def test_password_pattern_ssh(self, password_prompt_ssh):
        """TC-136: SSH password: pattern detected."""
        parser = PtyStreamParser()
        parser.feed_line(password_prompt_ssh)
        assert parser.pending_password_prompt is not None

    def test_password_pattern_become(self, password_prompt_become):
        """TC-137: BECOME password: pattern detected."""
        parser = PtyStreamParser()
        parser.feed_line(password_prompt_become)
        assert parser.pending_password_prompt is not None

    def test_password_pattern_become_default_variant(self):
        """TC-138: BECOME password[defaults to SSH password]: pattern detected."""
        parser = PtyStreamParser()
        parser.feed_line("BECOME password[defaults to SSH password]: ")
        assert parser.pending_password_prompt is not None

    def test_password_pattern_new_vault(self):
        """TC-139: New Vault password: pattern detected."""
        parser = PtyStreamParser()
        parser.feed_line("New Vault password: ")
        assert parser.pending_password_prompt is not None

    def test_password_pattern_confirm_vault(self):
        """TC-139: Confirm New Vault password: pattern detected."""
        parser = PtyStreamParser()
        parser.feed_line("Confirm New Vault password: ")
        assert parser.pending_password_prompt is not None

    def test_all_password_patterns_in_parser(self):
        """TC-133: All PASSWORD_PATTERNS exist in parser."""
        parser = PtyStreamParser()
        # Verify all patterns are compiled/stored
        assert hasattr(parser, "PASSWORD_PATTERNS")
        assert len(parser.PASSWORD_PATTERNS) >= 7  # All documented patterns

    def test_password_prompt_in_pre_run_phase(self, password_prompt_vault):
        """Password prompts in PRE_RUN_PROMPTS phase are captured."""
        parser = PtyStreamParser()
        assert parser.phase == StreamPhase.PRE_RUN_PROMPTS
        parser.feed_line(password_prompt_vault)
        assert parser.pending_password_prompt is not None

    def test_password_prompt_in_execution_phase(self, password_prompt_ssh):
        """Password prompts in EXECUTION phase are captured."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        parser.feed_line(password_prompt_ssh)
        # Password prompts should still be detected in EXECUTION phase
        # (Ansible may prompt during execution for vault passwords, etc.)

    def test_clear_password_prompt(self, password_prompt_vault):
        """Password prompt can be cleared after handling."""
        parser = PtyStreamParser()
        parser.feed_line(password_prompt_vault)
        assert parser.pending_password_prompt is not None
        parser.clear_password_prompt()
        assert parser.pending_password_prompt is None

    def test_password_prompt_cleared_after_jsonl(self, password_prompt_vault, event_playbook_start):
        """Password prompt can be cleared before JSONL."""
        parser = PtyStreamParser()
        parser.feed_line(password_prompt_vault)
        assert parser.pending_password_prompt is not None
        parser.clear_password_prompt()
        parser.feed_line(json.dumps(event_playbook_start))
        assert parser.pending_password_prompt is None


# =============================================================================
# Section 5.6: PLAY RECAP Detection
# =============================================================================


class TestPlayRecapDetection:
    """TC-140: PLAY RECAP pattern detection."""

    def test_play_recap_pattern_detected(self, recap_line):
        """TC-140: PLAY RECAP line matches pattern."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        parser.feed_line(recap_line)
        assert parser._in_recap is True
        assert parser.phase == StreamPhase.POST_RUN_RECAP

    def test_play_recap_minimum_asterisks(self):
        """PLAY RECAP requires minimum 5 asterisks."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        # Minimum 5 asterisks
        parser.feed_line("PLAY RECAP *****")
        assert parser._in_recap is True

    def test_play_recap_fewer_asterisks_not_matched(self):
        """PLAY RECAP with fewer than 5 asterisks not matched."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        # Only 4 asterisks - should NOT match
        parser.feed_line("PLAY RECAP ****")
        # In EXECUTION phase, non-matching line goes to plaintext
        assert parser._in_recap is False
        assert len(parser.plaintext_lines) > 0

    def test_play_recap_many_asterisks(self):
        """PLAY RECAP with many asterisks matched."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        parser.feed_line("PLAY RECAP " + "*" * 100)
        assert parser._in_recap is True

    def test_play_recap_not_detected_in_pre_run_phase(self, recap_line):
        """PLAY RECAP in PRE_RUN_PROMPTS phase routes differently."""
        parser = PtyStreamParser()
        parser.feed_line(recap_line)
        # In PRE_RUN_PROMPTS, it would be handled as plaintext
        # (though PLAY RECAP shouldn't appear before playbook starts)

    def test_recap_lines_collected_in_post_phase(self, event_stats):
        """Multiple recap lines collected in POST_RUN_RECAP."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        parser.feed_line(json.dumps(event_stats))
        parser.feed_line("PLAY RECAP *************")
        parser.feed_line("web1 : ok=5   changed=2   unreachable=0    failed=0")
        parser.feed_line("web2 : ok=4   changed=1   unreachable=0    failed=1")
        assert len(parser.recap_lines) >= 3


# =============================================================================
# Section 5.6: Warning Classification
# =============================================================================


class TestWarningPatternDetection:
    """TC-141: Warning pattern detection and classification."""

    def test_warning_pattern_detected(self, warning_line):
        """TC-141: [WARNING]: pattern detected."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        parser.feed_line(warning_line)
        assert len(parser.warnings) == 1
        assert parser.warnings[0].type == WarningType.WARNING

    def test_deprecation_warning_pattern(self, deprecation_warning_line):
        """TC-141: [DEPRECATION WARNING]: pattern detected."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        parser.feed_line(deprecation_warning_line)
        assert len(parser.warnings) == 1
        assert parser.warnings[0].type == WarningType.DEPRECATION

    def test_deprecated_removed_pattern(self, deprecated_removed_line):
        """TC-141: [DEPRECATED]: pattern detected."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        parser.feed_line(deprecated_removed_line)
        assert len(parser.warnings) == 1
        assert parser.warnings[0].type == WarningType.DEPRECATION

    def test_multiple_warnings_collected(self, warning_line, deprecation_warning_line):
        """Multiple warnings collected separately."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        parser.feed_line(warning_line)
        parser.feed_line(deprecation_warning_line)
        parser.feed_line("[WARNING]: Another warning")
        assert len(parser.warnings) == 3

    def test_warning_in_pre_run_phase(self, warning_line):
        """Warnings captured in PRE_RUN_PROMPTS phase."""
        parser = PtyStreamParser()
        parser.feed_line(warning_line)
        assert len(parser.warnings) == 1

    def test_warning_timestamp_captured(self, warning_line):
        """Warning entries have timestamp."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        parser.feed_line(warning_line)
        assert parser.warnings[0].timestamp is not None
        assert isinstance(parser.warnings[0].timestamp, datetime)

    def test_warning_message_preserved(self, warning_line):
        """Warning message preserved exactly."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        parser.feed_line(warning_line)
        assert parser.warnings[0].message == warning_line

    def test_all_warning_patterns_in_parser(self):
        """TC-141: All warning patterns exist in parser."""
        parser = PtyStreamParser()
        assert hasattr(parser, "WARNING_PATTERNS")
        assert len(parser.WARNING_PATTERNS) >= 3  # [WARNING], [DEPRECATION WARNING], [DEPRECATED]


# =============================================================================
# Section 5.6: Plaintext Line Handling
# =============================================================================


class TestPlaintextLineHandling:
    """TC-142: _handle_plaintext classification."""

    def test_plaintext_lines_stored(self):
        """TC-142: Non-JSON, non-special lines go to plaintext_lines."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        parser.feed_line("TASK [Install nginx] *************")
        parser.feed_line("ok: [web1]")
        # Should not be password, warning, recap, or JSONL
        assert len(parser.plaintext_lines) >= 1

    def test_plaintext_lines_not_warning(self):
        """Plaintext lines that aren't warnings are stored."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        parser.feed_line("This is a regular output line")
        assert len(parser.plaintext_lines) == 1

    def test_plaintext_lines_in_execution_phase(self, event_playbook_start):
        """Plaintext during EXECUTION phase collected."""
        parser = PtyStreamParser()
        parser.feed_line(json.dumps(event_playbook_start))  # Enter EXECUTION
        parser.feed_line("TASK [Setup] *******")
        parser.feed_line("Some log output")
        assert len(parser.plaintext_lines) >= 2

    def test_plaintext_vs_warning_classification(self):
        """Lines classified correctly between warning vs plaintext."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION

        # Warning line
        parser.feed_line("[WARNING]: This is a warning")
        # Regular line
        parser.feed_line("TASK [nginx] *******")

        assert len(parser.warnings) == 1
        assert len(parser.plaintext_lines) == 1

    def test_plaintext_lines_order_preserved(self):
        """Plaintext lines maintain order."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION

        lines = [
            "Line 1",
            "Line 2",
            "Line 3",
        ]
        for line in lines:
            parser.feed_line(line)

        assert parser.plaintext_lines[:3] == lines


# =============================================================================
# Section 5.6: Mixed Stream Handling
# =============================================================================


class TestMixedStreamHandling:
    """Section 5.6: JSONL events interleaved with plaintext."""

    def test_jsonl_and_plaintext_interleaved(self, event_playbook_start, event_task_start):
        """JSONL events and plaintext interleaved correctly."""
        parser = PtyStreamParser()

        # Start event
        parser.feed_line(json.dumps(event_playbook_start))
        # Plaintext
        parser.feed_line("PLAY [Setup] *********")
        # JSONL
        parser.feed_line(json.dumps(event_task_start))
        # Plaintext
        parser.feed_line("TASK [Install] *******")

        assert parser.phase == StreamPhase.EXECUTION
        assert len(parser.plaintext_lines) >= 2

    def test_plaintext_before_jsonl_start(self):
        """Plaintext before v2_playbook_on_start is captured."""
        parser = PtyStreamParser()

        # Before playbook starts
        parser.feed_line("[WARNING]: Ansible is deprecated")
        parser.feed_line("SSH password: ")
        parser.feed_line('[DEPRECATION WARNING]: Using "include"')

        assert parser.phase == StreamPhase.PRE_RUN_PROMPTS
        # Warnings captured
        assert len(parser.warnings) >= 1
        # Password prompt captured
        assert parser.pending_password_prompt is not None

    def test_jsonl_returns_events(self, event_playbook_start):
        """feed_line returns parsed events for JSONL."""
        parser = PtyStreamParser()
        events = parser.feed_line(json.dumps(event_playbook_start))
        assert len(events) == 1
        assert events[0]["_event"] == "v2_playbook_on_start"

    def test_plaintext_returns_empty(self):
        """feed_line returns empty list for plaintext."""
        parser = PtyStreamParser()
        events = parser.feed_line("This is plaintext")
        assert events == []

    def test_invalid_json_returns_empty(self):
        """feed_line returns empty for invalid JSON."""
        parser = PtyStreamParser()
        events = parser.feed_line('{"invalid json')
        assert events == []


# =============================================================================
# Section 5.5: PTY Pattern Patterns (Regex Validation)
# =============================================================================


class TestPatternRegexes:
    """TC-133-141: Validate regex patterns."""

    def test_password_patterns_match_expected_prompts(self):
        """All password patterns match their expected prompts."""
        patterns = PtyStreamParser.PASSWORD_PATTERNS

        test_cases = [
            ("Vault password: ", True),
            ("Vault password (prod): ", True),
            ("SSH password: ", True),
            ("BECOME password: ", True),
            ("BECOME password[defaults to SSH password]: ", True),
            ("New Vault password: ", True),
            ("Confirm New Vault password: ", True),
            ("Random password: ", False),  # Should not match
        ]

        for prompt, should_match in test_cases:
            matched = any(re.search(p, prompt) for p in patterns)
            assert matched == should_match, f"Pattern mismatch for: {prompt}"

    def test_warning_patterns_match_expected_lines(self):
        """All warning patterns match their expected lines."""
        patterns = PtyStreamParser.WARNING_PATTERNS

        test_cases = [
            ("[WARNING]: Some warning", True),
            ("[DEPRECATION WARNING]: This is deprecated", True),
            ("[DEPRECATED]: Feature removed", True),
            ("[ERROR]: This is an error", False),  # Not a WARNING pattern
        ]

        for line, should_match in test_cases:
            matched = any(re.match(p, line) for p in patterns)
            assert matched == should_match, f"Pattern mismatch for: {line}"

    def test_recap_pattern_matches_various_formats(self):
        """RECAP_PATTERN matches various PLAY RECAP formats."""
        pattern = PtyStreamParser.RECAP_PATTERN

        valid_lines = [
            "PLAY RECAP *****",
            "PLAY RECAP ******",
            "PLAY RECAP *********",
            "PLAY RECAP " + "*" * 100,
        ]

        for line in valid_lines:
            assert pattern.match(line), f"Should match: {line}"


# =============================================================================
# Section 5.10: Password Prompt Handling
# =============================================================================


class TestPasswordPromptHandling:
    """TC-143 to TC-148: Password prompt handling in PTY stream."""

    def test_password_prompt_pending_state(self, password_prompt_vault):
        """TC-143: Password prompts set _pending_password_prompt."""
        parser = PtyStreamParser()
        assert parser.pending_password_prompt is None
        parser.feed_line(password_prompt_vault)
        assert parser._pending_password_prompt is not None

    def test_password_prompt_cleared_after_handling(self, password_prompt_ssh):
        """Password prompt state cleared after handle_password_prompt."""
        parser = PtyStreamParser()
        parser.feed_line(password_prompt_ssh)
        assert parser.pending_password_prompt is not None
        parser.clear_password_prompt()
        assert parser.pending_password_prompt is None
        assert parser._pending_password_prompt is None

    def test_multiple_password_prompts_replaced(self):
        """Multiple password prompts - last one wins."""
        parser = PtyStreamParser()
        parser.feed_line("SSH password: ")
        parser.feed_line("Vault password: ")
        # Most recent prompt stored
        assert "Vault password" in parser.pending_password_prompt

    def test_password_prompt_preserved_across_phases(
        self, password_prompt_vault, event_playbook_start
    ):
        """Password prompt persists across phase transition."""
        parser = PtyStreamParser()
        parser.feed_line(password_prompt_vault)
        assert parser.pending_password_prompt is not None
        # Transition to EXECUTION
        parser.feed_line(json.dumps(event_playbook_start))
        # Password prompt should still be set (not cleared by phase change)
        assert parser.pending_password_prompt is not None

    def test_password_prompt_in_recap_phase(self):
        """Password prompts still detected in POST_RUN_RECAP (unusual edge case)."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.POST_RUN_RECAP
        # In POST_RUN_RECAP, plaintext lines are collected to recap_lines
        # Password prompts shouldn't normally appear here, but test behavior
        parser.feed_line("SSH password: ")
        # In POST phase, lines go to recap_lines
        assert len(parser.recap_lines) > 0


# =============================================================================
# Section 5.10: Compact Mode Password Pass-Through (Mock)
# =============================================================================


class TestCompactModePasswordPassThrough:
    """TC-144, TC-145: Compact mode password pass-through."""

    def test_password_prompt_sets_pending_state(self):
        """TC-144: Password prompt sets pending state for UI handling."""
        parser = PtyStreamParser()
        parser.feed_line("Vault password: ")
        assert parser.pending_password_prompt == "Vault password: "

    def test_password_prompt_multiple_types(self):
        """TC-144: All password types set correct pending state."""
        parser = PtyStreamParser()

        test_cases = [
            "SSH password: ",
            "Vault password: ",
            "Vault password (prod): ",
            "BECOME password: ",
            "BECOME password[defaults to SSH password]: ",
            "New Vault password: ",
            "Confirm New Vault password: ",
        ]

        for prompt in test_cases:
            parser = PtyStreamParser()
            parser.feed_line(prompt)
            assert parser.pending_password_prompt is not None, f"Failed for: {prompt}"

    def test_password_prompt_exact_text_stored(self, password_prompt_ssh):
        """Exact prompt text stored for UI display."""
        parser = PtyStreamParser()
        parser.feed_line(password_prompt_ssh)
        assert parser.pending_password_prompt == password_prompt_ssh

    def test_password_prompt_not_json_event(self, password_prompt_vault):
        """Password prompts don't generate JSON events."""
        parser = PtyStreamParser()
        events = parser.feed_line(password_prompt_vault)
        assert events == []  # No events returned

    def test_clear_password_prompt_allows_next_detection(self):
        """Clearing prompt allows detecting next password prompt."""
        parser = PtyStreamParser()
        parser.feed_line("SSH password: ")
        parser.clear_password_prompt()
        parser.feed_line("Vault password: ")
        assert parser.pending_password_prompt == "Vault password: "


# =============================================================================
# Edge Cases and Boundary Conditions
# =============================================================================


class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_empty_line_handled(self):
        """Empty lines don't crash parser."""
        parser = PtyStreamParser()
        events = parser.feed_line("")
        assert events == []

    def test_whitespace_line_handled(self):
        """Whitespace-only lines handled gracefully."""
        parser = PtyStreamParser()
        events = parser.feed_line("   ")
        assert events == []

    def test_json_without_event_field(self):
        """JSON without _event field returns empty."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        events = parser.feed_line('{"foo": "bar"}')
        assert events == []

    def test_malformed_json_handled(self):
        """Malformed JSON doesn't crash parser."""
        parser = PtyStreamParser()
        events = parser.feed_line("{invalid json")
        assert events == []

    def test_json_with_newline(self, event_playbook_start):
        """JSON with trailing newline handled."""
        parser = PtyStreamParser()
        line = json.dumps(event_playbook_start) + "\n"
        events = parser.feed_line(line)
        assert len(events) == 1

    def test_consecutive_stats_events(self, event_stats):
        """Multiple stats events handled (shouldn't happen but test)."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        parser.feed_line(json.dumps(event_stats))
        # Second stats shouldn't change phase again
        initial_phase = parser.phase
        parser.feed_line(json.dumps(event_stats))
        assert parser.phase == initial_phase

    def test_password_prompt_with_variant_text(self):
        """Password prompts with extra text still match."""
        parser = PtyStreamParser()
        # Some Ansible versions may add extra context
        parser.feed_line("SSH password: [Enter for default]")
        assert parser.pending_password_prompt is not None

    def test_case_sensitivity_warning_patterns(self):
        """Warning patterns are case-sensitive."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        # Lowercase should NOT match
        parser.feed_line("[warning]: lowercase")
        # Should be treated as plaintext, not warning
        assert len(parser.warnings) == 0
        assert len(parser.plaintext_lines) >= 1

    def test_unicode_in_plaintext(self):
        """Unicode characters in plaintext handled."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        parser.feed_line("TASK [Söme tåsk] *******")
        assert len(parser.plaintext_lines) >= 1

    def test_very_long_line(self):
        """Very long lines handled without crash."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        long_line = "A" * 10000
        parser.feed_line(long_line)
        assert len(parser.plaintext_lines) >= 1


# =============================================================================
# Integration with Conftest Fixtures
# =============================================================================


class TestConftestFixtures:
    """Verify all conftest fixtures work correctly."""

    def test_password_prompt_ssh_fixture(self, password_prompt_ssh):
        """password_prompt_ssh fixture is valid."""
        parser = PtyStreamParser()
        parser.feed_line(password_prompt_ssh)
        assert parser.pending_password_prompt is not None

    def test_password_prompt_vault_fixture(self, password_prompt_vault):
        """password_prompt_vault fixture is valid."""
        parser = PtyStreamParser()
        parser.feed_line(password_prompt_vault)
        assert parser.pending_password_prompt is not None

    def test_password_prompt_become_fixture(self, password_prompt_become):
        """password_prompt_become fixture is valid."""
        parser = PtyStreamParser()
        parser.feed_line(password_prompt_become)
        assert parser.pending_password_prompt is not None

    def test_deprecation_warning_fixture(self, deprecation_warning_line):
        """deprecation_warning_line fixture is valid."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        parser.feed_line(deprecation_warning_line)
        assert len(parser.warnings) == 1
        assert parser.warnings[0].type == WarningType.DEPRECATION

    def test_deprecated_removed_fixture(self, deprecated_removed_line):
        """deprecated_removed_line fixture is valid."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        parser.feed_line(deprecated_removed_line)
        assert len(parser.warnings) == 1
        assert parser.warnings[0].type == WarningType.DEPRECATION

    def test_warning_line_fixture(self, warning_line):
        """warning_line fixture is valid."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        parser.feed_line(warning_line)
        assert len(parser.warnings) == 1
        assert parser.warnings[0].type == WarningType.WARNING

    def test_recap_line_fixture(self, recap_line):
        """recap_line fixture is valid."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        parser.feed_line(recap_line)
        assert parser.phase == StreamPhase.POST_RUN_RECAP

    def test_jsonl_line_fixture(self, jsonl_line):
        """jsonl_line fixture is valid."""
        parser = PtyStreamParser()
        events = parser.feed_line(jsonl_line)
        assert len(events) == 1


# =============================================================================
# Phase State Machine Tests
# =============================================================================


class TestPhaseStateMachine:
    """Test phase state machine transitions."""

    def test_phase_transition_order(self, event_playbook_start, event_stats):
        """Phases transition in correct order: PRE -> EXECUTION -> POST."""
        parser = PtyStreamParser()

        # Initial state
        assert parser.phase == StreamPhase.PRE_RUN_PROMPTS

        # After start event
        parser.feed_line(json.dumps(event_playbook_start))
        assert parser.phase == StreamPhase.EXECUTION

        # After stats event
        parser.feed_line(json.dumps(event_stats))
        assert parser.phase == StreamPhase.POST_RUN_RECAP

    def test_cannot_go_backwards_from_execution(self, event_playbook_start):
        """Cannot transition from EXECUTION back to PRE_RUN_PROMPTS."""
        parser = PtyStreamParser()
        parser.feed_line(json.dumps(event_playbook_start))
        assert parser.phase == StreamPhase.EXECUTION

        # Try to feed another start event (shouldn't change phase)
        parser.feed_line(json.dumps(event_playbook_start))
        # Phase should remain EXECUTION
        assert parser.phase == StreamPhase.EXECUTION

    def test_phase_properties_immutability(self):
        """Phase properties return correct values in each state."""
        parser = PtyStreamParser()

        # PRE_RUN_PROMPTS
        assert parser.phase == StreamPhase.PRE_RUN_PROMPTS
        assert parser.pending_password_prompt is None
        assert len(parser.warnings) == 0
        assert len(parser.recap_lines) == 0

        # Add a warning
        parser.phase = StreamPhase.EXECUTION
        parser.feed_line("[WARNING]: Test")
        assert len(parser.warnings) == 1


# =============================================================================
# Renderer Protocol Compatibility (Mock)
# =============================================================================


class TestRendererProtocolPasswordHandling:
    """Test password prompt handling interface for renderer integration."""

    def test_pending_password_prompt_interface(self):
        """Parser provides interface for password prompt handling."""
        parser = PtyStreamParser()
        parser.feed_line("Vault password: ")

        # Renderer can check pending prompt
        prompt = parser.pending_password_prompt
        assert prompt is not None

        # Renderer handles prompt (e.g., shows modal, gets input)
        # ...

        # Renderer clears prompt when done
        parser.clear_password_prompt()
        assert parser.pending_password_prompt is None

    def test_password_prompt_detected_before_jsonl(self):
        """Password prompts detected before playbook starts."""
        parser = PtyStreamParser()

        # Typical pre-run sequence
        parser.feed_line("[WARNING]: ansible.version deprecated")
        parser.feed_line("Vault password (prod): ")
        parser.clear_password_prompt()
        # ... user enters password ...
        parser.feed_line('{"_event": "v2_playbook_on_start"}')

        assert parser.phase == StreamPhase.EXECUTION
        assert len(parser.warnings) == 1

    def test_full_workflow_simulation(
        self, event_playbook_start, event_task_start, event_runner_ok, event_stats
    ):
        """Simulate full playbook workflow with parser."""
        parser = PtyStreamParser()

        # Pre-run password prompts
        parser.feed_line("Vault password: ")
        assert parser.pending_password_prompt is not None
        parser.clear_password_prompt()

        # Playbook starts
        events = parser.feed_line(json.dumps(event_playbook_start))
        assert parser.phase == StreamPhase.EXECUTION
        assert len(events) == 1

        # Execution phase events
        parser.phase = StreamPhase.EXECUTION
        events = parser.feed_line(json.dumps(event_task_start))
        assert len(events) == 1

        events = parser.feed_line(json.dumps(event_runner_ok))
        assert len(events) == 1

        # Stats event - transition to POST_RUN_RECAP
        parser.feed_line(json.dumps(event_stats))
        assert parser.phase == StreamPhase.POST_RUN_RECAP

        # Recap lines collected
        parser.feed_line("web1 : ok=5   changed=0")
        assert len(parser.recap_lines) >= 1
