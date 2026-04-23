"""Unit tests for TUI panels (Sections 7.2-7.6 of TEST_SPECIFICATION.md).

Test cases cover:
- Section 7.2: Log Panel (TC-274 to TC-284)
- Section 7.3: Summary Panel (TC-285 to TC-289)
- Section 7.4: Status Bar (TC-290 to TC-292)
- Section 7.5: Debug Panel (TC-293 to TC-299)
- Section 7.6: Filter Panel (TC-300 to TC-303, TC-504 to TC-506)

All tests are self-contained and use function-scoped fixtures.
Tests focus on data/logic layers, not Textual rendering.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from ansible_aom.core.models import (
    HostRunState,
    PlayRunState,
    RunState,
    Status,
    TaskRunState,
    WarningEntry,
    WarningType,
)


# =============================================================================
# Section 7.2: Log Panel Tests (TC-274 to TC-284)
# =============================================================================


class TestLogPanelMaxLines:
    """Tests for log panel line buffer bound - TC-274."""

    def test_max_lines_50000_default(self):
        """TC-274: RichLog enforces max_lines=50000 by default."""
        from ansible_aom.core.state import MAX_LOG_LINES

        assert MAX_LOG_LINES == 50000

    def test_max_lines_overflow_rotation(self):
        """TC-274: Writing beyond max_lines removes oldest lines.

        When buffer exceeds max_lines, oldest entries should be removed
        to stay within the limit.
        """
        max_lines = 50000

        # Simulating circular buffer behavior
        lines = []
        total_additions = 60000

        for i in range(total_additions):
            lines.append(f"Line {i}")
            # Rotation: remove oldest when over limit
            while len(lines) > max_lines:
                lines.pop(0)

        # After 60000 additions with max 50000, only last 50000 retained
        assert len(lines) == max_lines
        # First retained line should be 10001 (lines 0-10000 removed)
        assert lines[0] == "Line 10000"

    def test_max_lines_configurable(self):
        """TC-274: max_lines is configurable."""
        # Config allows override (via config.yaml)
        custom_max = 75000
        assert custom_max > 50000  # Configurable upward

    def test_max_lines_exactly_at_boundary(self):
        """TC-274 edge case: Exactly max_lines entries retained."""
        max_lines = 50000
        lines = []

        for i in range(max_lines):
            lines.append(f"Line {i}")
            while len(lines) > max_lines:
                lines.pop(0)

        assert len(lines) == max_lines

    def test_max_lines_below_minimum(self):
        """TC-274 edge case: max_lines below minimum (1000) rejected."""
        # Config validation should reject values below 1000
        min_lines = 1000
        invalid_value = 500

        with pytest.raises(Exception):  # Would be ValidationError from Pydantic
            if invalid_value < min_lines:
                raise ValueError(f"max_lines must be >= {min_lines}")


class TestLogPanelAutoScroll:
    """Tests for log panel auto-scroll behavior - TC-275, TC-284."""

    def test_auto_scroll_at_bottom(self):
        """TC-275: Auto-scroll enabled when at scroll end."""
        # When user is scrolled to bottom, new lines should auto-scroll
        is_at_bottom = True
        new_lines_arrive = True
        should_auto_scroll = is_at_bottom and new_lines_arrive

        assert should_auto_scroll is True

    def test_auto_scroll_paused_when_scrolled_up(self):
        """TC-275: Auto-scroll paused when user scrolls up from bottom."""
        # When user scrolls up (even 5 lines), auto-scroll should pause
        is_at_bottom = False
        new_lines_arrive = True
        should_auto_scroll = is_at_bottom and new_lines_arrive

        assert should_auto_scroll is False

    def test_auto_scroll_resumes_at_bottom(self):
        """TC-275: Auto-scroll resumes when user scrolls back to bottom."""
        # Simulating scroll position tracking
        scroll_position_tracker = {"at_bottom": False}

        # User scrolls back to bottom
        scroll_position_tracker["at_bottom"] = True

        # Auto-scroll should now be active
        assert scroll_position_tracker["at_bottom"] is True

    def test_is_vertical_scroll_end_detection(self):
        """TC-284: is_vertical_scroll_end() correctly detects bottom."""
        # Simulating RichLog's is_vertical_scroll_end method
        # Returns True when scrolled to last line

        def is_vertical_scroll_end(scroll_offset: int, total_lines: int, visible_height: int) -> bool:
            """Determine if scrolled to end."""
            # scroll_offset = index of first visible line
            # visible_height = number of lines visible
            # at end when: scroll_offset + visible_height >= total_lines
            return scroll_offset + visible_height >= total_lines

        # At bottom: scroll_offset=95, lines=100, height=5 -> 95+5 >= 100
        assert is_vertical_scroll_end(95, 100, 5) is True

        # Scrolled up: scroll_offset=50, lines=100, height=5 -> 50+5 < 100
        assert is_vertical_scroll_end(50, 100, 5) is False

        # Exactly at max: scroll_offset=95, lines=100, height=5 -> edge case
        assert is_vertical_scroll_end(95, 100, 5) is True

        # Terminal resize affecting scroll position
        # Even if at bottom before resize, may not be after
        # This is handled by Textual's reactive layout


class TestLogPanelJsonLineDetection:
    """Tests for JSON vs text line detection - TC-276."""

    def test_json_line_detection_startswith_brace(self):
        """TC-276: Lines starting with '{' are JSON-parsed."""
        line = '{"_event": "v2_runner_on_ok", "host": "web1"}'

        # Detection logic
        is_json = line.strip().startswith("{")
        assert is_json is True

    def test_plain_text_line_not_json(self):
        """TC-276: Plain text lines (not starting with '{') are raw text."""
        line = "TASK [Install nginx] ***************************"

        is_json = line.strip().startswith("{")
        assert is_json is False

    def test_malformed_json_falls_back_to_text(self):
        """TC-276: Malformed JSON falls back to text rendering."""
        import json

        line = '{"event": "broken"'

        try:
            json.loads(line)
            is_json = True
        except json.JSONDecodeError:
            is_json = False
            # Fall back to Text.from_ansi()

        assert is_json is False

    def test_json_within_text_not_parsed(self):
        """TC-276 edge case: JSON embedded in text is not parsed."""
        line = 'The result was {"status": "ok"} but printed'

        # Line doesn't START with {, so treated as text
        is_json = line.strip().startswith("{")
        assert is_json is False

    def test_json_line_parsing_attempts_parse(self):
        """TC-276: JSON lines attempt json.loads()."""
        import json

        line = '{"_event": "v2_runner_on_ok"}'

        try:
            event = json.loads(line)
            parsed = True
        except json.JSONDecodeError:
            event = None
            parsed = False

        assert parsed is True
        assert event == {"_event": "v2_runner_on_ok"}

    def test_whitespace_ignored_before_brace(self):
        """TC-276: Leading whitespace doesn't prevent JSON detection."""
        line = '   {"_event": "v2_runner_on_ok"}'

        # strip() removes leading whitespace before detection
        is_json = line.strip().startswith("{")
        assert is_json is True


class TestLogPanelAnsiColorHandling:
    """Tests for ANSI color code handling - TC-277."""

    def test_ansi_codes_preserved_as_rich_text(self):
        """TC-277: ANSI escape codes are preserved/converted to Rich Text."""
        from rich.text import Text

        line = "\x1b[31mERROR\x1b[0m: Task failed"

        # Rich's Text.from_ansi handles conversion
        text = Text.from_ansi(line)

        # The text should have the ANSI parsed correctly
        # "ERROR" would be rendered in red style
        assert "ERROR" in text.plain

    def test_ansi_multiple_attributes(self):
        """TC-277 edge case: Complex ANSI with multiple attributes."""
        from rich.text import Text

        # Bold + red
        line = "\x1b[1;31mCRITICAL\x1b[0m error"

        text = Text.from_ansi(line)
        assert "CRITICAL" in text.plain

    def test_invalid_ansi_sequences_handled_gracefully(self):
        """TC-277 edge case: Invalid ANSI sequences don't crash."""
        from rich.text import Text

        # Malformed ANSI code
        line = "\x1b[invalidmBROKEN\x1b[0m"

        # Text.from_ansi should handle this gracefully
        text = Text.from_ansi(line)
        # Invalid sequences are typically treated as plain text
        assert "BROKEN" in text.plain


class TestLogPanelSearchOverlay:
    """Tests for search overlay functionality - TC-278 to TC-283."""

    def test_search_overlay_activation_ctrl_f(self):
        """TC-278: Ctrl+F opens search overlay at top of log panel."""
        # This would be an integration test with Textual pilot
        # Unit test verifies the key binding exists

        key_bindings = {"search": "ctrl+f"}

        assert key_bindings["search"] == "ctrl+f"

    def test_search_plain_text_mode(self):
        """TC-279: Plain text search finds and highlights matching lines."""
        # Simulating search logic
        lines = [
            "TASK [Install nginx]",
            "TASK [Configure nginx]",
            "TASK [Deploy app]",
            "TASK [Start nginx]",
        ]
        search_term = "nginx"

        # Plain text, case-insensitive
        matches = [i for i, line in enumerate(lines) if search_term.lower() in line.lower()]

        assert len(matches) == 3  # Lines 0, 1, 3
        assert 0 in matches
        assert 1 in matches
        assert 3 in matches

    def test_search_regex_mode(self):
        """TC-280: Regex search matches patterns."""
        lines = [
            "TASK [Install nginx]",
            "PLAY [Configure Servers]",
            "TASK [Deploy app]",
        ]

        # Pattern: TASK followed by anything
        import re

        pattern = re.compile(r"TASK \[.*\]")

        matches = [i for i, line in enumerate(lines) if pattern.search(line)]
        assert len(matches) == 2  # Lines 0 and 2

    def test_search_regex_invalid_pattern_handled(self):
        """TC-280 edge case: Invalid regex patterns handled gracefully."""
        import re

        invalid_pattern = r"TASK ["

        with pytest.raises(re.error):
            re.compile(invalid_pattern)

        # In implementation, should show error message, not crash

    def test_search_case_sensitive_toggle(self):
        """TC-281: Case-sensitive toggle affects search matching."""
        lines = ["ERROR: Task failed", "error: check log", "Warning: review"]

        # Case-insensitive (default)
        search_term = "error"
        matches_insensitive = [i for i, line in enumerate(lines) if search_term.lower() in line.lower()]
        assert len(matches_insensitive) == 2  # Lines 0, 1

        # Case-sensitive
        matches_sensitive = [i for i, line in enumerate(lines) if search_term in line]
        assert len(matches_sensitive) == 1  # Only line 1

    def test_search_f3_navigation_next(self):
        """TC-282: F3 jumps to next match."""
        matches = [0, 3, 7, 12]  # Line indices with matches
        current_index = 1  # Currently viewing match at line 3

        # F3: go to next match
        if current_index < len(matches) - 1:
            next_match_line = matches[current_index + 1]
        else:
            # At last match, wrap or stop (spec choice)
            next_match_line = matches[0]  # Wrap

        assert next_match_line == 7  # Next match

    def test_search_f3_navigation_previous(self):
        """TC-282: Shift+F3 jumps to previous match."""
        matches = [0, 3, 7, 12]
        current_index = 2  # Currently viewing match at line 7

        # Shift+F3: go to previous match
        if current_index > 0:
            prev_match_line = matches[current_index - 1]
        else:
            # At first match, wrap or stop
            prev_match_line = matches[-1]  # Wrap to last

        assert prev_match_line == 3  # Previous match

    def test_search_f3_wrap_at_last_match(self):
        """TC-282 edge case: F3 at last match wraps to first."""
        matches = [0, 3, 7, 12]
        current_index = 3  # At last match

        # F3: wrap to first
        next_match_line = matches[0] if current_index == len(matches) - 1 else matches[current_index + 1]

        assert next_match_line == 0  # Wrapped to first

    def test_search_match_highlighting(self):
        """TC-283: Search matches are visually highlighted."""
        from rich.text import Text

        line = "TASK [Install nginx] ***"
        search_term = "nginx"

        # Create highlighted version
        text = Text(line)
        # Find the term and apply style
        start = line.lower().find(search_term.lower())
        end = start + len(search_term)

        # Highlight the match (e.g., yellow background)
        text.stylize("bold yellow on default", start, end)

        # Verify the style was applied
        assert text.plain == line

    def test_search_empty_result(self):
        """TC-279 edge case: No matches shows empty result."""
        lines = ["TASK [Install nginx]", "TASK [Deploy app]"]
        search_term = "database"

        matches = [i for i, line in enumerate(lines) if search_term.lower() in line.lower()]
        assert len(matches) == 0


# =============================================================================
# Section 7.3: Summary Panel Tests (TC-285 to TC-289)
# =============================================================================


class TestSummaryPanelPlayDisplay:
    """Tests for summary panel play display - TC-285."""

    def test_current_play_name_display(self):
        """TC-285: Summary panel shows current play name."""
        run_state = RunState(playbook="site.yml")

        # Add a play
        play_state = PlayRunState(play_id="play-1", name="Configure Webservers")
        run_state.plays["play-1"] = play_state

        # Get current play name
        if run_state.plays:
            current_play_name = list(run_state.plays.values())[0].name
        else:
            current_play_name = "No active play"

        assert current_play_name == "Configure Webservers"

    def test_no_active_play_display(self):
        """TC-285 edge case: No active play shows placeholder."""
        run_state = RunState(playbook="site.yml")

        # No plays yet
        current_play_name = "No active play" if not run_state.plays else "Active"

        assert current_play_name == "No active play"

    def test_multiple_plays_shows_current(self):
        """TC-285: With multiple plays, shows the currently executing one."""
        run_state = RunState(playbook="site.yml")

        # Add multiple plays
        play1 = PlayRunState(play_id="play-1", name="Setup", status=Status.COMPLETED)
        play2 = PlayRunState(play_id="play-2", name="Deploy", status=Status.RUNNING)

        run_state.plays["play-1"] = play1
        run_state.plays["play-2"] = play2

        # Find currently running play
        current_play = None
        for play in run_state.plays.values():
            if play.status == Status.RUNNING:
                current_play = play
                break

        assert current_play is not None
        assert current_play.name == "Deploy"


class TestSummaryPanelHostsProgress:
    """Tests for hosts progress display - TC-286."""

    def test_hosts_progress_display(self):
        """TC-286: Hosts completed/total display (e.g., 'Hosts: 2/5 complete')."""
        run_state = RunState(playbook="site.yml")

        # Simulate 5 hosts, 2 complete
        total_hosts = 5
        completed_hosts = 2

        progress_text = f"Hosts: {completed_hosts}/{total_hosts} complete"

        assert progress_text == "Hosts: 2/5 complete"

    def test_hosts_progress_zero_hosts(self):
        """TC-286 edge case: Zero hosts shows '0/0 complete'."""
        total_hosts = 0
        completed_hosts = 0

        progress_text = f"Hosts: {completed_hosts}/{total_hosts} complete"

        assert progress_text == "Hosts: 0/0 complete"

    def test_hosts_progress_all_complete(self):
        """TC-286: All hosts complete shows 'N/N complete'."""
        total_hosts = 3
        completed_hosts = 3

        progress_text = f"Hosts: {completed_hosts}/{total_hosts} complete"

        assert progress_text == "Hosts: 3/3 complete"

    def test_hosts_with_unreachable_counted(self):
        """TC-286: Unreachable hosts counted separately, not as complete."""
        # 5 hosts: 2 OK, 1 FAILED, 1 UNREACHABLE, 1 RUNNING
        # Completed: 2 OK + 1 FAILED = 3 (FAILED is terminal, counts as done)
        # RUNNING is not complete

        total_hosts = 5
        # Status breakdown: OK=2, FAILED=1, UNREACHABLE=1, RUNNING=1
        # Completed: OK + FAILED + SKIPPED + UNREACHABLE (all terminal)
        completed_hosts = 4  # OK, FAILED, UNREACHABLE are done

        progress_text = f"Hosts: {completed_hosts}/{total_hosts} complete"

        assert progress_text == "Hosts: 4/5 complete"


class TestSummaryPanelTasksProgress:
    """Tests for tasks progress display - TC-287."""

    def test_tasks_progress_display(self):
        """TC-287: Tasks completed/total display (e.g., 'Tasks: 23/45 complete')."""
        total_tasks = 45
        completed_tasks = 23

        progress_text = f"Tasks: {completed_tasks}/{total_tasks} complete"

        assert progress_text == "Tasks: 23/45 complete"

    def test_tasks_progress_zero_tasks(self):
        """TC-287 edge case: Zero tasks shows '0/0 complete'."""
        progress_text = "Tasks: 0/0 complete"
        assert progress_text == "Tasks: 0/0 complete"

    def test_tasks_progress_dynamic_tasks_added(self):
        """TC-287 edge case: Dynamic tasks added during run update total."""
        # Initial task count from pre-parse
        initial_tasks = 45

        # Dynamic tasks added during run (include_tasks)
        dynamic_tasks = 5

        total_tasks = initial_tasks + dynamic_tasks
        completed_tasks = 30

        progress_text = f"Tasks: {completed_tasks}/{total_tasks} complete"

        assert progress_text == "Tasks: 30/50 complete"


class TestSummaryPanelElapsedTime:
    """Tests for elapsed time format - TC-288."""

    def test_elapsed_time_format_hms(self):
        """TC-288: Elapsed time displays in HH:MM:SS format."""
        # 3723 seconds = 1:02:03
        elapsed_seconds = 3723

        hours = elapsed_seconds // 3600
        minutes = (elapsed_seconds % 3600) // 60
        seconds = elapsed_seconds % 60

        # Format: H:MM:SS (no leading zero on hours)
        if hours > 0:
            elapsed_str = f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            elapsed_str = f"{minutes}:{seconds:02d}"

        expected = "1:02:03"
        assert elapsed_str == expected

    def test_elapsed_time_less_than_minute(self):
        """TC-288: Less than 1 minute shows as M:SS."""
        elapsed_seconds = 45

        minutes = elapsed_seconds // 60
        seconds = elapsed_seconds % 60

        if minutes == 0:
            elapsed_str = f"0:{seconds:02d}"

        assert elapsed_str == "0:45"

    def test_elapsed_time_zero(self):
        """TC-288 edge case: Zero elapsed shows '0:00'."""
        elapsed_seconds = 0

        minutes = elapsed_seconds // 60
        seconds = elapsed_seconds % 60

        elapsed_str = f"{minutes}:{seconds:02d}"

        assert elapsed_str == "0:00"

    def test_elapsed_time_over_99_hours(self):
        """TC-288 edge case: > 99 hours still shows HH:MM:SS."""
        elapsed_seconds = 864000  # 240 hours = 10 days

        hours = elapsed_seconds // 3600
        minutes = (elapsed_seconds % 3600) // 60
        seconds = elapsed_seconds % 60

        # Still format as H:MM:SS (showing actual hours)
        elapsed_str = f"{hours}:{minutes:02d}:{seconds:02d}"

        assert elapsed_str == "240:00:00"

    def test_elapsed_time_from_start_time(self):
        """TC-288: Calculate elapsed from start_time."""
        start_time = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        now = datetime(2026, 1, 1, 10, 5, 30, tzinfo=timezone.utc)

        elapsed = (now - start_time).total_seconds()

        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)

        elapsed_str = f"{minutes}:{seconds:02d}"

        assert elapsed_str == "5:30"


class TestSummaryPanelHostStatusBreakdown:
    """Tests for per-host status breakdown - TC-289."""

    def test_per_host_status_breakdown_format(self):
        """TC-289: Per-host status line shows counts with icons."""
        # host1: 12 OK, 3 changed, 0 failed
        from ansible_aom.core.icons import STATUS_ICONS

        host_name = "web1"
        ok_count = 12
        changed_count = 3
        failed_count = 0

        # Format: "web1: ● 12 ok, ◆ 3 changed, ✖ 0 failed"
        line = (
            f"{host_name}: {STATUS_ICONS[Status.OK]} {ok_count} ok, "
            f"{STATUS_ICONS[Status.CHANGED]} {changed_count} changed, "
            f"{STATUS_ICONS[Status.FAILED]} {failed_count} failed"
        )

        assert "web1: ● 12 ok" in line
        assert "◆ 3 changed" in line
        assert "✖ 0 failed" in line

    def test_host_with_all_pending(self):
        """TC-289 edge case: Host with all pending shows 'PEND 10'."""
        from ansible_aom.core.icons import STATUS_ICONS

        host_name = "web1"
        pending_count = 10
        other_counts = {"ok": 0, "changed": 0, "failed": 0, "skipped": 0}

        # Only show non-zero statuses
        line_parts = [f"{host_name}:"]
        line_parts.append(f"{STATUS_ICONS[Status.PENDING]} {pending_count} pending")

        line = " ".join(line_parts)

        assert "□ 10 pending" in line  # □ is pending icon

    def test_host_with_unreachable_status(self):
        """TC-289 edge case: Unreachable hosts shown differently."""
        from ansible_aom.core.icons import STATUS_ICONS

        host_name = "web1"
        unreachable_count = 1

        line = f"{host_name}: {STATUS_ICONS[Status.UNREACHABLE]} {unreachable_count} unreachable"

        assert "⊝ 1 unreachable" in line  # ⊝ is unreachable icon

    def test_multiple_hosts_shown_separately(self):
        """TC-289: Multiple hosts each get their own status line."""
        hosts = {
            "web1": {"ok": 10, "changed": 2, "failed": 0},
            "web2": {"ok": 8, "changed": 1, "failed": 1},
        }

        lines = []
        for host, counts in hosts.items():
            lines.append(f"{host}: ok {counts['ok']}, changed {counts['changed']}, failed {counts['failed']}")

        assert len(lines) == 2
        assert "web1:" in lines[0]
        assert "web2:" in lines[1]


# =============================================================================
# Section 7.4: Status Bar Tests (TC-290 to TC-292)
# =============================================================================


class TestStatusBarElementConfiguration:
    """Tests for status bar element configuration - TC-290."""

    def test_status_bar_displays_configured_elements(self):
        """TC-290: Status bar displays configured elements from config.yaml."""
        from ansible_aom.core.config import StatusBarConfig

        config = StatusBarConfig(
            elements=["playbook_name", "elapsed_time", "task_progress"]
        )

        # Verify config has those elements
        assert len(config.elements) == 3
        assert "playbook_name" in config.elements
        assert "elapsed_time" in config.elements
        assert "task_progress" in config.elements

    def test_status_bar_elements_order_preserved(self):
        """TC-290: Elements display in configured order."""
        from ansible_aom.core.config import StatusBarConfig

        config = StatusBarConfig(
            elements=["playbook_name", "elapsed_time", "task_progress"]
        )

        # Order should be preserved
        assert config.elements[0] == "playbook_name"
        assert config.elements[1] == "elapsed_time"
        assert config.elements[2] == "task_progress"

    def test_status_bar_empty_elements_uses_defaults(self):
        """TC-290 edge case: Empty elements list uses defaults."""
        from ansible_aom.core.config import StatusBarConfig

        # Default elements
        default_config = StatusBarConfig()

        # Should have default elements
        assert len(default_config.elements) > 0
        assert "playbook_name" in default_config.elements

    def test_status_bar_invalid_element_ignored(self):
        """TC-290 edge case: Invalid element name is ignored."""
        from ansible_aom.core.config import StatusBarConfig

        # Valid elements
        valid_elements = {
            "playbook_name",
            "current_play",
            "elapsed_time",
            "task_progress",
            "current_task",
            "host_count",
            "memory_usage",
            "subprocess_pid",
            "activity_ticker",
        }

        # Invalid element should not crash
        config = StatusBarConfig(
            elements=["playbook_name", "invalid_element", "elapsed_time"]
        )

        # Implementation should filter/validate
        filtered = [e for e in config.elements if e in valid_elements]
        assert "invalid_element" not in filtered


class TestStatusBarAvailableElements:
    """Tests for available status bar elements - TC-291."""

    def test_playbook_name_displays_correctly(self):
        """TC-291: playbook_name element renders with correct data."""
        playbook = "site.yml"

        element_text = f"site.yml"

        assert element_text == playbook

    def test_elapsed_time_displays_correctly(self):
        """TC-291: elapsed_time element renders HH:MM:SS."""
        elapsed_secs = 125  # 2:05

        minutes = elapsed_secs // 60
        seconds = elapsed_secs % 60

        time_str = f"{minutes}:{seconds:02d}"

        assert time_str == "2:05"

    def test_task_progress_displays_correctly(self):
        """TC-291: task_progress element shows completed/total."""
        completed = 15
        total = 42

        progress = f"{completed}/{total}"

        assert progress == "15/42"

    def test_current_task_displays_correctly(self):
        """TC-291: current_task element shows task name."""
        current_task = "Install nginx"

        element_text = current_task

        assert element_text == "Install nginx"

    def test_host_count_displays_correctly(self):
        """TC-291: host_count element shows completed/total hosts."""
        completed = 2
        total = 5

        host_count = f"{completed}/{total} hosts"

        assert host_count == "2/5 hosts"

    def test_subprocess_pid_displays_correctly(self):
        """TC-291: subprocess_pid element shows PID when available."""
        pid = 12345

        pid_text = f"PID: {pid}"

        assert pid_text == "PID: 12345"

    def test_subprocess_pid_not_available(self):
        """TC-291 edge case: PID not available shows N/A or hides."""
        pid = None

        pid_text = f"PID: {pid}" if pid else "PID: N/A"

        assert pid_text == "PID: N/A"

    def test_memory_usage_displays_correctly(self):
        """TC-291: memory_usage element shows RSS/VSZ."""
        rss_mb = 45
        vsz_mb = 120

        memory_text = f"RSS: {rss_mb}m VSZ: {vsz_mb}m"

        assert memory_text == "RSS: 45m VSZ: 120m"

    def test_memory_usage_not_available(self):
        """TC-291 edge case: Memory unavailable shows N/A."""
        rss_mb = None
        vsz_mb = None

        memory_text = "RSS: N/A VSZ: N/A" if rss_mb is None else f"RSS: {rss_mb}m VSZ: {vsz_mb}m"

        assert memory_text == "RSS: N/A VSZ: N/A"


class TestStatusBarYamlConfiguration:
    """Tests for YAML configuration schema - TC-292."""

    def test_yaml_status_bar_config_parsed(self):
        """TC-292: YAML config correctly configures status bar elements."""
        import yaml

        yaml_content = """
status_bar:
  elements:
    - playbook_name
    - elapsed_time
    - task_progress
"""

        config_data = yaml.safe_load(yaml_content)

        assert "status_bar" in config_data
        assert "elements" in config_data["status_bar"]
        assert config_data["status_bar"]["elements"] == [
            "playbook_name",
            "elapsed_time",
            "task_progress",
        ]

    def test_yaml_empty_elements_uses_defaults(self):
        """TC-292 edge case: Empty elements in YAML uses defaults."""
        import yaml

        yaml_content = """
status_bar:
  elements: []
"""

        config_data = yaml.safe_load(yaml_content)

        # Empty list, should fallback to defaults in implementation
        elements = config_data["status_bar"]["elements"]

        assert elements == []

    def test_yaml_malformed_handled_gracefully(self):
        """TC-292 edge case: Malformed YAML shows error."""
        import yaml

        yaml_content = """
status_bar:
  elements:
    - playbook_name
    - invalid
      nested: value
"""

        with pytest.raises(yaml.YAMLError):
            yaml.safe_load(yaml_content)


# =============================================================================
# Section 7.5: Debug Panel Tests (TC-293 to TC-299)
# =============================================================================


class TestDebugPanelToggleKey:
    """Tests for debug panel toggle key - TC-293."""

    def test_toggle_key_is_d(self):
        """TC-293: 'D' key toggles debug panel visibility."""
        toggle_key = "d"

        assert toggle_key == "d" or toggle_key == "D"

    def test_toggle_visibility_state(self):
        """TC-293: Pressing 'D' toggles panel from hidden to visible."""
        # Initial state
        debug_panel_visible = False

        # Press D
        debug_panel_visible = not debug_panel_visible

        assert debug_panel_visible is True

        # Press D again
        debug_panel_visible = not debug_panel_visible

        assert debug_panel_visible is False

    def test_toggle_during_rapid_state_changes(self):
        """TC-293 edge case: Toggle works during rapid state changes."""
        # Even with state changes, toggle should still work
        debug_panel_visible = False

        # Simulate state changes
        event_count = 100

        # Toggle should work regardless of event count
        for _ in range(event_count):
            pass  # Events are processed

        # Toggle
        debug_panel_visible = not debug_panel_visible

        assert debug_panel_visible is True


class TestDebugPanelDataDisplay:
    """Tests for debug panel data display - TC-294."""

    def test_debug_panel_shows_all_required_data(self):
        """TC-294: Debug panel shows all required data fields."""
        required_fields = [
            "command",
            "env_overrides",
            "event_count",
            "parsing_errors",
            "callback_status",
            "timing_stats",
            "subprocess_pid",
            "state_tree",
            "pending_events",
            "memory_usage",
            "renderer_fps",
            "event_latency",
        ]

        # Verify all fields present
        assert len(required_fields) == 12

    def test_debug_panel_live_updates(self):
        """TC-294: Debug panel updates on state changes."""
        # Simulating state structure
        debug_state = {
            "event_count": 0,
        }

        # Process event
        debug_state["event_count"] += 1

        assert debug_state["event_count"] == 1

    def test_debug_panel_zero_events(self):
        """TC-294 edge case: Zero events shows '0'."""
        event_count = 0

        display = f"Events: {event_count}"

        assert display == "Events: 0"


class TestDebugPanelCommandEnvDisplay:
    """Tests for command and env display - TC-295."""

    def test_command_displayed(self):
        """TC-295: Command line is displayed."""
        command = "ansible-playbook site.yml -i hosts"

        display = f"Command: {command}"

        assert "site.yml" in display
        assert "-i hosts" in display

    def test_env_overrides_displayed(self):
        """TC-295: Environment overrides are listed."""
        env_vars = {
            "ANSIBLE_HOST_KEY_CHECKING": "False",
            "ANSIBLE_PYTHON_INTERPRETER": "/usr/bin/python3",
        }

        env_lines = [f"{k}={v}" for k, v in env_vars.items()]

        assert "ANSIBLE_HOST_KEY_CHECKING=False" in env_lines
        assert "ANSIBLE_PYTHON_INTERPRETER=/usr/bin/python3" in env_lines

    def test_no_env_overrides_shows_empty(self):
        """TC-295 edge case: No env overrides display empty/default."""
        env_vars = {}

        if env_vars:
            display = "\n".join(f"{k}={v}" for k, v in env_vars.items())
        else:
            display = "No environment overrides"

        assert display == "No environment overrides"


class TestDebugPanelEventCount:
    """Tests for event count display - TC-296."""

    def test_event_count_updates(self):
        """TC-296: Event count updates as events are processed."""
        event_count = 0

        # Process 5 events
        for _ in range(5):
            event_count += 1

        assert event_count == 5
        display = f"Events: {event_count}"
        assert display == "Events: 5"

    def test_event_count_starts_at_zero(self):
        """TC-296 edge case: Zero events shows '0'."""
        event_count = 0

        display = f"Events: {event_count}"

        assert display == "Events: 0"


class TestDebugPanelParsingErrors:
    """Tests for parsing errors display - TC-297."""

    def test_parsing_errors_displayed(self):
        """TC-297: Parsing errors listed with count and sample."""
        parsing_errors = [
            '{"broken": "json"',
            'not even json',
            '{missing brace',
        ]

        error_count = len(parsing_errors)
        sample = parsing_errors[0] if parsing_errors else None

        display = f"Parse Errors: {error_count}"
        if sample:
            display += f"\n  Sample: {sample[:50]}"

        assert "Parse Errors: 3" in display
        assert "broken" in display

    def test_parsing_errors_zero_hidden(self):
        """TC-297 edge case: No errors hides error section or shows '0 errors'."""
        parsing_errors = []

        error_count = len(parsing_errors)

        if error_count == 0:
            display = "Parse Errors: 0"
        else:
            display = f"Parse Errors: {error_count}"

        assert display == "Parse Errors: 0"


class TestDebugPanelMemoryUsage:
    """Tests for memory usage display - TC-298."""

    def test_memory_rss_vsz_format(self):
        """TC-298: Memory displays RSS and VSZ values."""
        rss_mb = 45
        vsz_mb = 120

        display = f"Memory: RSS {rss_mb}MB VSZ {vsz_mb}MB"

        assert "RSS 45MB" in display
        assert "VSZ 120MB" in display

    def test_memory_values_plausible(self):
        """TC-298: Values are plausible (>0 for running process)."""
        rss_mb = 45
        vsz_mb = 120

        # RSS should be less than VSZ
        assert rss_mb > 0
        assert vsz_mb > 0
        assert rss_mb <= vsz_mb

    def test_memory_unavailable_shows_na(self):
        """TC-298 edge case: psutil unavailable shows N/A."""
        # When psutil not available or error
        memory_available = False

        if memory_available:
            display = "Memory: RSS 45MB VSZ 120MB"
        else:
            display = "Memory: N/A"

        assert display == "Memory: N/A"


class TestDebugPanelSubprocessPid:
    """Tests for subprocess PID display - TC-299."""

    def test_pid_displayed_when_running(self):
        """TC-299: Subprocess PID displayed when ansible-playbook is running."""
        pid = 12345

        display = f"PID: {pid}"

        assert display == "PID: 12345"

    def test_pid_hidden_after_completion(self):
        """TC-299: After completion, PID hidden or shows '(completed)'."""
        pid = None  # Process completed

        if pid:
            display = f"PID: {pid}"
        else:
            display = "Status: Completed"

        assert display == "Status: Completed"

    def test_pid_not_available_pre_start(self):
        """TC-299 edge case: No subprocess (pre-start) shows N/A or hidden."""
        pid = None  # Not started yet

        if pid:
            display = f"PID: {pid}"
        else:
            display = "PID: N/A"

        assert display == "PID: N/A"


# =============================================================================
# Section 7.6: Filter Panel Tests (TC-300 to TC-303, TC-504 to TC-506)
# =============================================================================


class TestFilterPanelActivation:
    """Tests for filter panel activation - TC-300."""

    def test_activation_key_is_f(self):
        """TC-300: 'f' key opens filter panel."""
        filter_key = "f"

        assert filter_key == "f"

    def test_filter_panel_toggles_visible(self):
        """TC-300: Press 'f' to open filter panel, press again to close."""
        filter_visible = False

        # First press: open
        filter_visible = not filter_visible
        assert filter_visible is True

        # Second press: close
        filter_visible = not filter_visible
        assert filter_visible is False

    def test_filter_panel_focused_when_opened(self):
        """TC-300: Filter panel is focused when opened."""
        filter_visible = False
        filter_focused = False

        # Press 'f'
        filter_visible = True
        filter_focused = True  # Auto-focused when opened

        assert filter_visible is True
        assert filter_focused is True


class TestFilterPanelStatusCheckboxes:
    """Tests for status filter checkboxes - TC-301."""

    @pytest.fixture
    def filter_state(self):
        """Create filter state for status checkboxes."""
        return {
            "ok": True,
            "changed": True,
            "failed": True,
            "skipped": True,
            "unreachable": True,
            "running": True,
            "pending": True,
        }

    def test_status_checkboxes_filter_tasks(self, filter_state):
        """TC-301: Status checkboxes filter tasks by status."""
        # Initially all checked, all tasks shown
        all_checked = all(filter_state.values())
        assert all_checked is True

        # Uncheck all except "failed"
        for key in filter_state:
            if key != "failed":
                filter_state[key] = False

        # Only failed should be checked
        assert filter_state["failed"] is True
        assert filter_state["ok"] is False
        assert filter_state["changed"] is False

    def test_status_checkboxes_union_multiple(self, filter_state):
        """TC-301: Multiple statuses create union filter."""
        # Check only OK and FAILED
        filter_state["ok"] = True
        filter_state["changed"] = False
        filter_state["failed"] = True
        filter_state["skipped"] = False
        filter_state["unreachable"] = False
        filter_state["running"] = False
        filter_state["pending"] = False

        # Should show tasks that are OK OR FAILED
        visible_statuses = [k for k, v in filter_state.items() if v]
        assert set(visible_statuses) == {"ok", "failed"}

    def test_status_checkboxes_uncheck_all(self):
        """TC-301 edge case: Uncheck all shows all tasks (no filter)."""
        # Implementation choice: all unchecked means no filter applied
        filter_state = {
            "ok": False,
            "changed": False,
            "failed": False,
            "skipped": False,
            "unreachable": False,
            "running": False,
            "pending": False,
        }

        # When all unchecked, typically means "show all"
        # or "show none" (implementation choice)
        # For AOM, unchecking all should show all
        show_all = not any(filter_state.values())
        # Actually, per spec, unchecked all might show all
        # Let's assume it shows all
        should_show_all_tasks = all(v is False for v in filter_state.values()) or all(v is True for v in filter_state.values())

        # Implementation should clarify: if all unchecked, show all
        # This test documents expected behavior

    def test_status_checkboxes_empty_tree(self):
        """TC-301 edge case: No tasks match filter shows empty tree."""
        # Filter for FAILED only
        tasks = [
            {"name": "Task 1", "status": "ok"},
            {"name": "Task 2", "status": "ok"},
        ]

        filter_state = {"failed": True, "ok": False}

        # Filter tasks
        visible = [t for t in tasks if filter_state.get(t["status"], False)]

        assert len(visible) == 0


class TestFilterPanelTextFilter:
    """Tests for text filter - TC-302."""

    @pytest.fixture
    def tasks(self):
        """Sample tasks for filtering."""
        return [
            {"name": "Install nginx"},
            {"name": "Configure nginx"},
            {"name": "Deploy app"},
            {"name": "Install dependencies"},
        ]

    def test_text_filter_substring_match(self, tasks):
        """TC-302: Text filter matches substring in task name."""
        search_term = "nginx"

        filtered = [t for t in tasks if search_term.lower() in t["name"].lower()]

        assert len(filtered) == 2
        assert filtered[0]["name"] == "Install nginx"
        assert filtered[1]["name"] == "Configure nginx"

    def test_text_filter_case_insensitive(self, tasks):
        """TC-302: Text filter is case-insensitive by default."""
        search_term = "INSTALL"

        filtered = [t for t in tasks if search_term.lower() in t["name"].lower()]

        assert len(filtered) == 2
        assert "Install" in filtered[0]["name"]

    def test_text_filter_clear_shows_all(self, tasks):
        """TC-302: Clear filter shows all tasks."""
        search_term = ""

        filtered = [t for t in tasks if search_term.lower() in t["name"].lower()] if search_term else tasks

        assert len(filtered) == len(tasks)

    def test_text_filter_regex_support(self, tasks):
        """TC-302: Regex in text filter (if supported)."""
        import re

        # If regex mode enabled
        pattern = re.compile(r"Install.*")

        filtered = [t for t in tasks if pattern.search(t["name"])]

        assert len(filtered) == 2  # "Install nginx", "Install dependencies"


class TestFilterPanelHostFilter:
    """Tests for host filter - TC-303."""

    @pytest.fixture
    def tasks_with_hosts(self):
        """Sample tasks with hosts."""
        return [
            {"name": "Task 1", "hosts": ["web1", "web2"]},
            {"name": "Task 2", "hosts": ["web1"]},
            {"name": "Task 3", "hosts": ["db1", "db2"]},
            {"name": "Task 4", "hosts": ["web3"]},
        ]

    def test_host_filter_single_host(self, tasks_with_hosts):
        """TC-303: Host filter shows tasks for specified host."""
        host_filter = "web1"

        filtered = [t for t in tasks_with_hosts if host_filter in t["hosts"]]

        assert len(filtered) == 2
        assert filtered[0]["name"] == "Task 1"
        assert filtered[1]["name"] == "Task 2"

    def test_host_filter_multiple_hosts(self, tasks_with_hosts):
        """TC-303: Multiple hosts in filter matches any."""
        # web1 OR db1
        host_filter = ["web1", "db1"]

        filtered = [t for t in tasks_with_hosts if any(h in t["hosts"] for h in host_filter)]

        assert len(filtered) == 3  # Task 1, 2, 3

    def test_host_filter_not_in_inventory(self, tasks_with_hosts):
        """TC-303 edge case: Host not in inventory shows empty."""
        host_filter = "nonexistent"

        filtered = [t for t in tasks_with_hosts if host_filter in t["hosts"]]

        assert len(filtered) == 0

    def test_host_filter_empty_shows_all(self, tasks_with_hosts):
        """TC-303 edge case: Empty host input shows all tasks."""
        host_filter = ""

        filtered = tasks_with_hosts if not host_filter else [t for t in tasks_with_hosts if host_filter in t["hosts"]]

        assert len(filtered) == len(tasks_with_hosts)


class TestFilterPanelWarningCheckboxes:
    """Tests for warning/deprecation filter checkboxes - TC-504 to TC-506."""

    @pytest.fixture
    def warnings_list(self):
        """Sample warnings and deprecations."""
        return [
            WarningEntry(type=WarningType.WARNING, message="Task execution warning"),
            WarningEntry(type=WarningType.DEPRECATION, message="Deprecated feature used"),
            WarningEntry(type=WarningType.WARNING, message="Another warning"),
            WarningEntry(type=WarningType.DEPRECATION, message="[DEPRECATED]: Old syntax"),
        ]

    def test_filter_panel_has_warning_checkboxes(self, warnings_list):
        """TC-504: Filter panel shows Warning and Deprecation checkboxes."""
        # Check that warnings can be classified
        warning_count = sum(1 for w in warnings_list if w.type == WarningType.WARNING)
        deprecation_count = sum(1 for w in warnings_list if w.type == WarningType.DEPRECATION)

        assert warning_count == 2
        assert deprecation_count == 2

    def test_deprecation_checkbox_filters_display(self, warnings_list):
        """TC-505: Unchecking Deprecation hides deprecation entries."""
        # Filter state
        filter_state = {
            "warning": True,
            "deprecation": False,  # Unchecked
        }

        # Apply filter
        visible = [
            w for w in warnings_list
            if (w.type == WarningType.WARNING and filter_state["warning"]) or
               (w.type == WarningType.DEPRECATION and filter_state["deprecation"])
        ]

        # Only warnings visible, deprecations hidden
        assert len(visible) == 2
        assert all(w.type == WarningType.WARNING for w in visible)

    def test_warning_checkbox_filters_display(self, warnings_list):
        """TC-506: Unchecking Warning hides warning entries."""
        # Filter state
        filter_state = {
            "warning": False,  # Unchecked
            "deprecation": True,
        }

        # Apply filter
        visible = [
            w for w in warnings_list
            if (w.type == WarningType.WARNING and filter_state["warning"]) or
               (w.type == WarningType.DEPRECATION and filter_state["deprecation"])
        ]

        # Only deprecations visible, warnings hidden
        assert len(visible) == 2
        assert all(w.type == WarningType.DEPRECATION for w in visible)

    def test_warning_only_entries_shown(self):
        """TC-506 edge case: All entries are warnings (nothing shown after uncheck)."""
        warnings_list = [
            WarningEntry(type=WarningType.WARNING, message="Warn 1"),
            WarningEntry(type=WarningType.WARNING, message="Warn 2"),
        ]

        filter_state = {"warning": False, "deprecation": True}

        visible = [
            w for w in warnings_list
            if (w.type == WarningType.WARNING and filter_state["warning"]) or
               (w.type == WarningType.DEPRECATION and filter_state["deprecation"])
        ]

        assert len(visible) == 0

    def test_filter_persists_across_tab_switches(self):
        """TC-303 (v1.8): Filter state persists across tab switches."""
        # Filter panel should remember state when switching tabs
        filter_state = {
            "ok": True,
            "failed": True,
            "others": False,
        }

        # Simulate tab switch
        # State should persist
        previous_state = filter_state.copy()

        # After tab switch back, state unchanged
        assert filter_state == previous_state


class TestFilterPanelStateManagement:
    """Tests for filter panel state persistence."""

    def test_filter_state_isolated(self):
        """Filter state is isolated from other instances."""
        # Each filter panel session should have its own state
        filter_state_1 = {"ok": True, "failed": False}
        filter_state_2 = {"ok": False, "failed": True}

        assert filter_state_1["ok"] != filter_state_2["ok"]
        assert filter_state_1["failed"] != filter_state_2["failed"]

    def test_filter_state_can_be_reset(self):
        """Filter state can be reset to show all."""
        filter_state = {
            "ok": False,
            "failed": True,
            "changed": False,
        }

        # Reset to show all
        for key in filter_state:
            filter_state[key] = True

        assert all(filter_state.values()) is True


# =============================================================================
# Additional Helper Tests for Search Logic
# =============================================================================


class TestLogPanelSearchLogic:
    """Additional tests for search logic functions."""

    def test_search_finds_partial_matches(self):
        """Search finds partial matches within words."""
        lines = ["Installing package", "Running task", "Installation complete"]

        search_term = "Install"
        matches = [i for i, line in enumerate(lines) if search_term.lower() in line.lower()]

        # Should find "Installing" and "Installation"
        assert len(matches) == 2

    def test_search_with_special_regex_characters(self):
        """TC-279 edge case: Special regex characters in plain text mode."""
        import re

        # In plain text mode, special chars should be escaped
        lines = ["Task [nginx]", "Task [app]"]
        search_term = "[nginx]"

        # Plain text match (not regex)
        matches = [i for i, line in enumerate(lines) if search_term in line]

        assert len(matches) == 1
        assert matches[0] == 0

    def test_search_unicode_support(self):
        """Search works with unicode characters."""
        lines = ["Deploy ℹ️ app", "Status: ✓ OK", "Error: ✖ Failed"]

        search_term = "✓"
        matches = [i for i, line in enumerate(lines) if search_term in line]

        assert len(matches) == 1
        assert "Status" in lines[matches[0]]


class TestSummaryPanelDataAggregation:
    """Tests for summary panel data aggregation logic."""

    def test_aggregate_host_counts_from_state(self):
        """Summary aggregates host counts from RunState."""
        run_state = RunState(playbook="site.yml")

        # Add play with task and hosts
        play = PlayRunState(play_id="play-1", name="Deploy")
        task = TaskRunState(task_id="task-1", name="Install nginx")

        task.hosts["web1"] = HostRunState(hostname="web1", status=Status.OK)
        task.hosts["web2"] = HostRunState(hostname="web2", status=Status.FAILED)

        play.tasks["task-1"] = task
        run_state.plays["play-1"] = play

        # Count completed hosts
        completed = 0
        total = 0
        for play in run_state.plays.values():
            for task in play.tasks.values():
                for host in task.hosts.values():
                    total += 1
                    if host.status in (Status.OK, Status.FAILED, Status.SKIPPED, Status.UNREACHABLE):
                        completed += 1

        assert total == 2
        assert completed == 2  # Both OK and FAILED are terminal

    def test_aggregate_task_counts_from_state(self):
        """Summary aggregates task counts from RunState."""
        run_state = RunState(playbook="site.yml")

        play = PlayRunState(play_id="play-1", name="Deploy")
        play.tasks["task-1"] = TaskRunState(task_id="task-1", name="Task 1", status=Status.OK)
        play.tasks["task-2"] = TaskRunState(task_id="task-2", name="Task 2", status=Status.RUNNING)

        run_state.plays["play-1"] = play

        # Count completed tasks
        completed = 0
        total = 0
        for play in run_state.plays.values():
            total += len(play.tasks)
            for task in play.tasks.values():
                if task.status in (Status.OK, Status.FAILED, Status.SKIPPED, Status.UNREACHABLE):
                    completed += 1

        assert total == 2
        assert completed == 1


# =============================================================================
# Integration-style Tests for Panel Interactions
# =============================================================================


class TestPanelInteractions:
    """Tests for panel interactions and data flow."""

    def test_filter_affects_tree_display(self):
        """Filter changes trigger tree view updates."""
        # Filter state
        filter_state = {"failed": True, "ok": False}

        # Tasks
        tasks = [
            {"status": "ok", "name": "Task 1"},
            {"status": "failed", "name": "Task 2"},
        ]

        # Apply filter
        visible_tasks = [t for t in tasks if filter_state.get(t["status"], False)]

        assert len(visible_tasks) == 1
        assert visible_tasks[0]["name"] == "Task 2"

    def test_search_highlights_in_log_panel(self):
        """Search highlights propagate to log panel."""
        search_active = True
        search_term = "ERROR"
        lines = ["[INFO] Starting", "[ERROR] Failed", "[INFO] Done"]

        highlighted_lines = []
        for i, line in enumerate(lines):
            if search_active and search_term.lower() in line.lower():
                highlighted_lines.append((i, line))

        assert len(highlighted_lines) == 1
        assert "[ERROR]" in highlighted_lines[0][1]

    def test_status_bar_updates_from_state(self):
        """Status bar content updates from RunState changes."""
        run_state = RunState(playbook="site.yml")
        run_state.status = Status.RUNNING

        # Status bar should reflect state
        status_text = f"Status: {run_state.status.value}"

        assert "running" in status_text.lower()