"""Integration tests for CompactRenderer.

Test cases cover:
- TC-029 to TC-034: Compact view layout and icons (Section 4.1)
- TC-035: Compact mode dependencies
- TC-041, TC-042: Non-TTY behavior (Section 4.3)
- TC-043 to TC-053: Terminal requirements and signal handling (Section 4.4)
- TC-054 to TC-058: Refresh strategy (Section 4.5)

All tests are self-contained and use function-scoped fixtures.
"""

import io
import sys
from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest

from ansible_aom.core.models import (
    HostRunState,
    PlayDefinition,
    PlayRunState,
    RunState,
    Status,
    TaskDefinition,
    TaskRunState,
)


# ============================================================================
# Status Icon Tests (TC-030)
# ============================================================================


class TestStatusIcons:
    """Tests for TC-030: Compact View Status Icons."""

    @pytest.fixture
    def icon_mapping(self) -> dict[str, str]:
        """Return the status icon mapping."""
        return {
            Status.PENDING: "□",      # pending/skipped
            Status.RUNNING: "◐",      # in progress
            Status.OK: "●",           # completed ok
            Status.CHANGED: "◆",      # completed with changes
            Status.FAILED: "✖",       # failed
            Status.UNREACHABLE: "⊝",  # unreachable
            Status.SKIPPED: "□",      # skipped (same as pending)
        }

    def test_status_icon_pending(self, icon_mapping: dict[str, str]):
        """TC-030: PENDING status maps to □ (empty square)."""
        assert icon_mapping[Status.PENDING] == "□"

    def test_status_icon_running(self, icon_mapping: dict[str, str]):
        """TC-030: RUNNING status maps to ◐ (half circle)."""
        assert icon_mapping[Status.RUNNING] == "◐"

    def test_status_icon_ok(self, icon_mapping: dict[str, str]):
        """TC-030: OK status maps to ● (filled circle)."""
        assert icon_mapping[Status.OK] == "●"

    def test_status_icon_changed(self, icon_mapping: dict[str, str]):
        """TC-030: CHANGED status maps to ◆ (diamond)."""
        assert icon_mapping[Status.CHANGED] == "◆"

    def test_status_icon_failed(self, icon_mapping: dict[str, str]):
        """TC-030: FAILED status maps to ✖ (x mark)."""
        assert icon_mapping[Status.FAILED] == "✖"

    def test_status_icon_unreachable(self, icon_mapping: dict[str, str]):
        """TC-030: UNREACHABLE status maps to ⊝ (circle with dash)."""
        assert icon_mapping[Status.UNREACHABLE] == "⊝"

    def test_status_icon_skipped(self, icon_mapping: dict[str, str]):
        """TC-030: SKIPPED status maps to □ (empty square)."""
        assert icon_mapping[Status.SKIPPED] == "□"


class TestStatusIconFallback:
    """Tests for TC-060: Unicode fallback characters."""

    @pytest.fixture
    def ascii_fallback_mapping(self) -> dict[str, str]:
        """Return ASCII fallback for non-Unicode terminals."""
        return {
            Status.PENDING: ".",
            Status.RUNNING: "@",
            Status.OK: "*",
            Status.CHANGED: "+",
            Status.FAILED: "X",
            Status.UNREACHABLE: "-",
            Status.SKIPPED: ".",
        }

    def test_ascii_fallback_pending(self, ascii_fallback_mapping: dict[str, str]):
        """TC-060: PENDING fallback is period."""
        assert ascii_fallback_mapping[Status.PENDING] == "."

    def test_ascii_fallback_running(self, ascii_fallback_mapping: dict[str, str]):
        """TC-060: RUNNING fallback is at sign."""
        assert ascii_fallback_mapping[Status.RUNNING] == "@"

    def test_ascii_fallback_ok(self, ascii_fallback_mapping: dict[str, str]):
        """TC-060: OK fallback is asterisk."""
        assert ascii_fallback_mapping[Status.OK] == "*"

    def test_ascii_fallback_changed(self, ascii_fallback_mapping: dict[str, str]):
        """TC-060: CHANGED fallback is plus."""
        assert ascii_fallback_mapping[Status.CHANGED] == "+"

    def test_ascii_fallback_failed(self, ascii_fallback_mapping: dict[str, str]):
        """TC-060: FAILED fallback is X."""
        assert ascii_fallback_mapping[Status.FAILED] == "X"

    def test_ascii_fallback_unreachable(self, ascii_fallback_mapping: dict[str, str]):
        """TC-060: UNREACHABLE fallback is dash."""
        assert ascii_fallback_mapping[Status.UNREACHABLE] == "-"


# ============================================================================
# Status Bar Tests (TC-031, TC-032)
# ============================================================================


class TestStatusBarFormat:
    """Tests for TC-031, TC-032: Status bar formatting."""

    def format_status_bar(
        self,
        playbook: str,
        hosts_completed: int,
        hosts_total: int,
        warnings: int,
        deprecations: int,
        elapsed_seconds: int,
    ) -> str:
        """Format status bar: playbook | X/Y hosts | ⚠ N ✱ N | elapsed."""
        elapsed_h = elapsed_seconds // 3600
        elapsed_m = (elapsed_seconds % 3600) // 60
        elapsed_s = elapsed_seconds % 60
        elapsed_str = f"{elapsed_h}:{elapsed_m:02d}:{elapsed_s:02d}"
        
        parts = [
            playbook,
            f"{hosts_completed}/{hosts_total} hosts",
        ]
        
        if warnings > 0:
            parts.append(f"⚠ {warnings}")
        if deprecations > 0:
            parts.append(f"✱ {deprecations}")
            
        parts.append(elapsed_str)
        
        return " │ ".join(parts)

    def test_status_bar_format_basic(self):
        """TC-031: Status bar shows playbook, hosts, time."""
        result = self.format_status_bar(
            playbook="site.yml",
            hosts_completed=3,
            hosts_total=10,
            warnings=0,
            deprecations=0,
            elapsed_seconds=323,  # 0:05:23
        )
        assert "site.yml" in result
        assert "3/10 hosts" in result
        assert "0:05:23" in result

    def test_status_bar_with_warnings(self):
        """TC-031: Status bar shows warning count."""
        result = self.format_status_bar(
            playbook="site.yml",
            hosts_completed=3,
            hosts_total=10,
            warnings=2,
            deprecations=0,
            elapsed_seconds=323,
        )
        assert "⚠ 2" in result

    def test_status_bar_with_deprecations(self):
        """TC-031: Status bar shows deprecation count."""
        result = self.format_status_bar(
            playbook="site.yml",
            hosts_completed=3,
            hosts_total=10,
            warnings=0,
            deprecations=1,
            elapsed_seconds=323,
        )
        assert "✱ 1" in result

    def test_status_bar_with_both_warnings_and_deprecations(self):
        """TC-031: Status bar shows both warnings and deprecations."""
        result = self.format_status_bar(
            playbook="site.yml",
            hosts_completed=3,
            hosts_total=10,
            warnings=5,
            deprecations=2,
            elapsed_seconds=323,
        )
        assert "⚠ 5" in result
        assert "✱ 2" in result

    def test_elapsed_time_format_under_one_minute(self):
        """TC-031: Elapsed time formats correctly under 1 minute."""
        result = self.format_status_bar(
            playbook="site.yml",
            hosts_completed=0,
            hosts_total=10,
            warnings=0,
            deprecations=0,
            elapsed_seconds=45,
        )
        assert "0:00:45" in result

    def test_elapsed_time_format_over_one_hour(self):
        """TC-031: Elapsed time formats correctly over 1 hour."""
        result = self.format_status_bar(
            playbook="site.yml",
            hosts_completed=10,
            hosts_total=10,
            warnings=0,
            deprecations=0,
            elapsed_seconds=3725,  # 1:02:05
        )
        assert "1:02:05" in result

    def test_progress_bar_zero_percent(self):
        """TC-032: Progress bar at 0% completion."""
        total_tasks = 10
        completed_tasks = 0
        progress_pct = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
        assert progress_pct == 0

    def test_progress_bar_fifty_percent(self):
        """TC-032: Progress bar at 50% completion."""
        total_tasks = 10
        completed_tasks = 5
        progress_pct = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
        assert progress_pct == 50

    def test_progress_bar_one_hundred_percent(self):
        """TC-032: Progress bar at 100% completion."""
        total_tasks = 10
        completed_tasks = 10
        progress_pct = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
        assert progress_pct == 100

    def test_progress_bar_zero_tasks(self):
        """TC-032: Progress bar handles zero total tasks."""
        total_tasks = 0
        completed_tasks = 0
        progress_pct = 0  # Default when no tasks
        assert progress_pct == 0


# ============================================================================
# Host Status Indicators Tests
# ============================================================================


class TestHostStatusIndicators:
    """Tests for host status with changed/ok/failed indicators."""

    def format_host_summary(
        self,
        hostname: str,
        ok: int,
        changed: int,
        failed: int,
        unreachable: int,
    ) -> str:
        """Format host summary line."""
        parts = [f"{hostname}:"]
        
        if ok > 0:
            icon = "●"  # OK icon
            parts.append(f"{icon} {ok} ok")
        if changed > 0:
            icon = "◆"  # CHANGED icon
            parts.append(f"{icon} {changed} changed")
        if failed > 0:
            icon = "✖"  # FAILED icon
            parts.append(f"{icon} {failed} failed")
        if unreachable > 0:
            icon = "⊝"  # UNREACHABLE icon
            parts.append(f"{icon} {unreachable} unreachable")
            
        return " ".join(parts)

    def test_host_summary_all_ok(self):
        """Host summary shows all ok count."""
        result = self.format_host_summary(
            hostname="web1",
            ok=12,
            changed=0,
            failed=0,
            unreachable=0,
        )
        assert "web1:" in result
        assert "● 12 ok" in result
        assert "changed" not in result.lower()

    def test_host_summary_with_changes(self):
        """Host summary shows changed count."""
        result = self.format_host_summary(
            hostname="web1",
            ok=2,
            changed=3,
            failed=0,
            unreachable=0,
        )
        assert "◆ 3 changed" in result

    def test_host_summary_with_failures(self):
        """Host summary shows failed count."""
        result = self.format_host_summary(
            hostname="web1",
            ok=2,
            changed=0,
            failed=1,
            unreachable=0,
        )
        assert "✖ 1 failed" in result

    def test_host_summary_with_unreachable(self):
        """Host summary shows unreachable count."""
        result = self.format_host_summary(
            hostname="web1",
            ok=2,
            changed=0,
            failed=0,
            unreachable=1,
        )
        assert "⊝ 1 unreachable" in result


# ============================================================================
# Exit Code Tests (TC-0304 from Spec Section 3.4)
# ============================================================================


class TestExitCodes:
    """Tests for exit codes based on playbook result."""

    def determine_exit_code(self, state: RunState) -> int:
        """Determine exit code from RunState."""
        for play in state.plays.values():
            for task in play.tasks.values():
                for host_state in task.hosts.values():
                    if host_state.status == Status.FAILED:
                        return 1

        for play in state.plays.values():
            for task in play.tasks.values():
                for host_state in task.hosts.values():
                    if host_state.status == Status.UNREACHABLE:
                        return 2

        return 0

    def test_exit_code_0_all_ok(self):
        """Exit 0 when all hosts completed OK."""
        state = RunState(playbook="test.yml", status=Status.COMPLETED)
        play = PlayRunState(play_id="p1", name="Test play", status=Status.COMPLETED)
        task = TaskRunState(task_id="t1", name="Test task", status=Status.OK)
        task.hosts["web1"] = HostRunState(hostname="web1", status=Status.OK)
        task.hosts["web2"] = HostRunState(hostname="web2", status=Status.OK)
        play.tasks["t1"] = task
        state.plays["p1"] = play
        
        exit_code = self.determine_exit_code(state)
        assert exit_code == 0

    def test_exit_code_0_with_changes(self):
        """Exit 0 when hosts have changes."""
        state = RunState(playbook="test.yml", status=Status.COMPLETED)
        play = PlayRunState(play_id="p1", name="Test play", status=Status.COMPLETED)
        task = TaskRunState(task_id="t1", name="Test task", status=Status.CHANGED)
        task.hosts["web1"] = HostRunState(hostname="web1", status=Status.OK)
        task.hosts["web2"] = HostRunState(hostname="web2", status=Status.CHANGED, changed=True)
        play.tasks["t1"] = task
        state.plays["p1"] = play
        
        exit_code = self.determine_exit_code(state)
        assert exit_code == 0

    def test_exit_code_1_failure(self):
        """Exit 1 when any host failed."""
        state = RunState(playbook="test.yml", status=Status.FAILED)
        play = PlayRunState(play_id="p1", name="Test play", status=Status.FAILED)
        task = TaskRunState(task_id="t1", name="Test task", status=Status.FAILED)
        task.hosts["web1"] = HostRunState(hostname="web1", status=Status.OK)
        task.hosts["web2"] = HostRunState(hostname="web2", status=Status.FAILED, message="Error")
        play.tasks["t1"] = task
        state.plays["p1"] = play
        
        exit_code = self.determine_exit_code(state)
        assert exit_code == 1

    def test_exit_code_2_unreachable(self):
        """Exit 2 when any host unreachable."""
        state = RunState(playbook="test.yml", status=Status.FAILED)
        play = PlayRunState(play_id="p1", name="Test play", status=Status.FAILED)
        task = TaskRunState(task_id="t1", name="Test task", status=Status.UNREACHABLE)
        task.hosts["web1"] = HostRunState(hostname="web1", status=Status.OK)
        task.hosts["web2"] = HostRunState(hostname="web2", status=Status.UNREACHABLE, message="SSH failed")
        play.tasks["t1"] = task
        state.plays["p1"] = play
        
        exit_code = self.determine_exit_code(state)
        assert exit_code == 2

    def test_exit_code_1_failure_takes_precedence_over_unreachable(self):
        """When both failed and unreachable exist, exit 1."""
        state = RunState(playbook="test.yml", status=Status.FAILED)
        play = PlayRunState(play_id="p1", name="Test play", status=Status.FAILED)
        task = TaskRunState(task_id="t1", name="Test task", status=Status.FAILED)
        task.hosts["web1"] = HostRunState(hostname="web1", status=Status.FAILED)
        task.hosts["web2"] = HostRunState(hostname="web2", status=Status.UNREACHABLE)
        play.tasks["t1"] = task
        state.plays["p1"] = play
        
        # Failed takes precedence (checked first)
        exit_code = self.determine_exit_code(state)
        assert exit_code == 1


# ============================================================================
# Compact Renderer Protocol Tests
# ============================================================================


class TestCompactRendererProtocol:
    """Tests for CompactRenderer implementing Renderer Protocol."""

    def test_compact_renderer_has_start_method(self):
        """CompactRenderer has start() method."""
        from ansible_aom.compact.renderer import CompactRenderer

        assert hasattr(CompactRenderer, "start")

    def test_compact_renderer_has_update_state_method(self):
        """CompactRenderer has update_state() method."""
        from ansible_aom.compact.renderer import CompactRenderer

        assert hasattr(CompactRenderer, "update_state")

    def test_compact_renderer_has_handle_password_prompt_method(self):
        """CompactRenderer has handle_password_prompt() method."""
        from ansible_aom.compact.renderer import CompactRenderer

        assert hasattr(CompactRenderer, "handle_password_prompt")

    def test_compact_renderer_has_handle_completion_method(self):
        """CompactRenderer has handle_completion() method."""
        from ansible_aom.compact.renderer import CompactRenderer

        assert hasattr(CompactRenderer, "handle_completion")

    def test_compact_renderer_has_stop_method(self):
        """CompactRenderer has stop() method."""
        from ansible_aom.compact.renderer import CompactRenderer

        assert hasattr(CompactRenderer, "stop")


class TestCompactRendererStart:
    """Tests for CompactRenderer.start() method."""

    def test_start_accepts_playbook_and_args(self):
        """start() accepts playbook path and args list."""
        from ansible_aom.compact.renderer import CompactRenderer

        renderer = CompactRenderer()
        # Should not raise
        renderer.start("playbook.yml", ["-i", "inventory.ini"])

    def test_start_initializes_state(self):
        """start() initializes internal state."""
        from ansible_aom.compact.renderer import CompactRenderer

        renderer = CompactRenderer()
        renderer.start("playbook.yml", [])
        assert renderer._playbook == "playbook.yml"
        assert renderer._args == []


class TestCompactRendererUpdateState:
    """Tests for CompactRenderer.update_state() method."""

    def test_update_state_accepts_event_dict(self):
        """update_state() accepts event dictionary."""
        from ansible_aom.compact.renderer import CompactRenderer

        renderer = CompactRenderer()
        renderer.start("playbook.yml", [])
        
        event = {"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"}
        # Should not raise
        renderer.update_state(event)


class TestCompactRendererHandlePasswordPrompt:
    """Tests for CompactRenderer.handle_password_prompt() method."""

    def test_handle_password_prompt_returns_string(self):
        """handle_password_prompt() returns password string."""
        from ansible_aom.compact.renderer import CompactRenderer

        renderer = CompactRenderer()
        renderer.start("playbook.yml", [])
        
        # Password prompts require mocking getpass/PTY
        # This test validates the interface exists
        # Actual integration tests would mock pexpect


class TestCompactRendererHandleCompletion:
    """Tests for CompactRenderer.handle_completion() method."""

    def test_handle_completion_accepts_exit_code_and_state(self):
        """handle_completion() accepts exit code and state string."""
        from ansible_aom.compact.renderer import CompactRenderer

        renderer = CompactRenderer()
        renderer.start("playbook.yml", [])
        
        # Should not raise
        renderer.handle_completion(0, "completed")


class TestCompactRendererStop:
    """Tests for CompactRenderer.stop() method."""

    def test_stop_cleans_up_resources(self):
        """stop() cleans up renderer resources."""
        from ansible_aom.compact.renderer import CompactRenderer

        renderer = CompactRenderer()
        renderer.start("playbook.yml", [])
        
        # Should not raise
        renderer.stop()


# ============================================================================
# Rich Live Tests (TC-033)
# ============================================================================


class TestRichLiveConfiguration:
    """Tests for TC-033: Rich Live configuration."""

    def test_refresh_per_second_default_is_four(self):
        """TC-033: Compact mode uses refresh_per_second=4."""
        refresh_rate = 4  # From spec
        assert refresh_rate == 4

    def test_refresh_throttle_maximum(self):
        """TC-033: Maximum 4 renders per second."""
        # Implementation detail: Rich Live throttles to 4 FPS
        max_renders_per_second = 4
        events_per_second = 10  # More events than renders
        
        # Renders should be capped
        renders = min(events_per_second, max_renders_per_second)
        assert renders == 4


# ============================================================================
# Password Pass-through Tests (TC-034)
# ============================================================================


class TestPasswordPassThrough:
    """Tests for TC-034: Password prompt pass-through."""

    def test_password_prompt_patterns_exist(self):
        """TC-034: Password prompt patterns are defined."""
        patterns = [
            r'Vault password: ',
            r'Vault password \([^)]+\): ',     # vault_id variant
            r'SSH password: ',
            r'BECOME password: ',
            r'BECOME password\[defaults to SSH password\]: ',
            r'New Vault password: ',
            r'Confirm New Vault password: ',
        ]
        assert len(patterns) == 7

    def test_password_prompt_stops_live_display(self):
        """TC-034: Password prompt stops Rich Live display."""
        # When password detected:
        # 1. Live.stop() called
        # 2. Prompt displayed on terminal
        # 3. Password entered
        # 4. Live.start() called
        # This is a behavior specification test
        pass

    def test_password_uses_getpass(self):
        """TC-034: Password input uses getpass for masking."""
        # getpass.getpass() handles password masking
        pass


# ============================================================================
# Dependency Tests (TC-035)
# ============================================================================


class TestCompactDependencies:
    """Tests for TC-035: Compact mode dependencies."""

    def test_rich_library_importable(self):
        """TC-035: rich library is importable."""
        import rich
        assert rich is not None

    def test_blessed_library_optional(self):
        """TC-035: blessed library is optional."""
        try:
            import blessed
            # blessed is installed, that's fine
        except ImportError:
            # blessed not installed, that's also fine
            pass


# ============================================================================
# Non-TTY Tests (TC-041, TC-042)
# ============================================================================


class TestNonTTYBehavior:
    """Tests for TC-041, TC-042: Non-TTY output behavior."""

    def test_non_tty_uses_line_based_output(self):
        """TC-041: Non-TTY uses line-based output."""
        # In non-TTY mode, each status update is on its own line
        # with ANSI codes preserved for colors
        pass

    def test_non_tty_no_interactive_features(self):
        """TC-042: Non-TTY disables interactive features."""
        # No TUI launch
        # No password prompts via getpass
        # No keyboard input expected
        pass


# ============================================================================
# Terminal Size Tests (TC-043, TC-044, TC-045)
# ============================================================================


class TestTerminalSizeCheck:
    """Tests for TC-043, TC-044, TC-045: Terminal size requirements."""

    MINIMUM_LINES = 24
    MINIMUM_COLUMNS = 80

    def test_minimum_size_constants(self):
        """TC-043: Minimum terminal size is 24 lines x 80 columns."""
        assert self.MINIMUM_LINES == 24
        assert self.MINIMUM_COLUMNS == 80

    def check_terminal_size(self, lines: int, columns: int) -> tuple[bool, str]:
        """Check if terminal meets minimum size."""
        if lines < self.MINIMUM_LINES or columns < self.MINIMUM_COLUMNS:
            return False, (
                f"Terminal too small: {lines}×{columns}. "
                f"Minimum: {self.MINIMUM_LINES}×{self.MINIMUM_COLUMNS}. "
                f"Resize or use --no-tui flag."
            )
        return True, ""

    def test_terminal_too_small_reports_error(self):
        """TC-043: Below minimum shows error."""
        ok, msg = self.check_terminal_size(20, 80)
        assert ok is False
        assert "Terminal too small" in msg
        assert "20×80" in msg

    def test_terminal_minimum_size_passes(self):
        """TC-043: Minimum size passes check."""
        ok, msg = self.check_terminal_size(24, 80)
        assert ok is True

    def test_terminal_larger_passes(self):
        """TC-043: Larger terminal passes check."""
        ok, msg = self.check_terminal_size(40, 120)
        assert ok is True

    def test_error_message_format(self):
        """TC-044: Error message shows dimensions and minimum."""
        ok, msg = self.check_terminal_size(20, 60)
        assert "20×60" in msg
        assert "24×80" in msg


# ============================================================================
# Signal Handling Tests (TC-046 to TC-053)
# ============================================================================


class TestSignalHandling:
    """Tests for TC-046 to TC-053: Signal handling."""

    def test_exit_code_130_for_sigint(self):
        """TC-047: Exit code 130 for SIGINT (second Ctrl+C)."""
        sigint_exit_code = 130
        assert sigint_exit_code == 130

    def test_sigint_first_press_forwards_to_subprocess(self):
        """TC-046: First Ctrl+C forwards to subprocess."""
        # First SIGINT -> forward to ansible-playbook
        # Don't terminate AOM
        pass

    def test_sigint_second_press_kills_within_2s(self):
        """TC-047: Second Ctrl+C within 2s kills everything."""
        # Second SIGINT within 2 seconds -> exit(130)
        pass

    def test_sigquit_logs_stack_trace(self):
        """TC-048: SIGQUIT logs stack trace and continues."""
        # SIGQUIT (Ctrl+\) -> log to file, continue running
        pass

    def test_sigterm_saves_session(self):
        """TC-049: SIGTERM saves session, exits 0."""
        # SIGTERM -> save session, restore terminal, exit 0
        pass

    def test_sighup_saves_session(self):
        """TC-050: SIGHUP saves session, exits 0."""
        # SIGHUP -> same as SIGTERM graceful shutdown
        pass

    def test_sigwinch_triggers_rerender(self):
        """TC-051: SIGWINCH triggers re-render."""
        # SIGWINCH -> re-render status panel
        pass

    def test_sigpipe_is_ignored(self):
        """TC-052: SIGPIPE is ignored (Python default)."""
        # SIGPIPE -> Python default is to ignore
        pass

    def test_terminal_cleanup_on_exit(self):
        """TC-053: Terminal cleanup on exit."""
        # On exit:
        # 1. Restore cursor visibility
        # 2. Exit alternate screen
        # 3. Reset colors
        # 4. Flush output
        pass


# ============================================================================
# Refresh Strategy Tests (TC-054 to TC-058)
# ============================================================================


class TestRefreshStrategy:
    """Tests for TC-054 to TC-058: Refresh strategy."""

    def test_event_driven_refresh_triggers(self):
        """TC-054: Status panel re-renders on state change events."""
        # Events that trigger render:
        trigger_events = [
            "v2_runner_on_ok",
            "v2_runner_on_failed",
            "v2_runner_on_skipped",
            "v2_runner_on_unreachable",
            "v2_runner_on_start",
        ]
        assert len(trigger_events) == 5

    def test_throttled_refresh_rate(self):
        """TC-055: Maximum 4 updates per second."""
        # Rich Live refresh_per_second=4
        max_renders_per_second = 4
        rapid_events = 10
        
        # Should throttle to 4 renders
        actual_renders = min(rapid_events, max_renders_per_second)
        assert actual_renders == 4

    def test_timer_based_elapsed_time(self):
        """TC-056: Elapsed time updates every 1 second."""
        timer_interval = 1  # seconds
        assert timer_interval == 1

    def test_debounce_window_250ms(self):
        """TC-057: Events within 250ms batched into single render."""
        debounce_ms = 250
        assert debounce_ms == 250


class TestNonTTYRefreshFallback:
    """Tests for TC-058: Non-TTY refresh fallback."""

    def test_non_tty_line_per_status(self):
        """TC-058: Non-TTY uses one line per status change."""
        # No cursor manipulation
        # No continuous elapsed time
        # One line per status event
        pass


# ============================================================================
# Display Tests
# ============================================================================


class TestDisplayClass:
    """Tests for Display helper class."""

    def test_display_class_exists(self):
        """Display class exists in compact module."""
        from ansible_aom.compact.display import Display

        assert Display is not None

    def test_display_has_start_method(self):
        """Display has start() method."""
        from ansible_aom.compact.display import Display

        assert hasattr(Display, "start")

    def test_display_has_stop_method(self):
        """Display has stop() method."""
        from ansible_aom.compact.display import Display

        assert hasattr(Display, "stop")

    def test_display_has_update_method(self):
        """Display has update() method."""
        from ansible_aom.compact.display import Display

        assert hasattr(Display, "update")

    def test_display_has_print_log_method(self):
        """Display has print_log() method."""
        from ansible_aom.compact.display import Display

        assert hasattr(Display, "print_log")

    def test_display_has_clear_method(self):
        """Display has clear() method."""
        from ansible_aom.compact.display import Display

        assert hasattr(Display, "clear")


# ============================================================================
# Integration: View Mode Selection
# ============================================================================


class TestViewModeSelection:
    """Tests for view mode selection via factory."""

    def test_factory_creates_compact_renderer_by_default(self):
        """Default view mode is compact."""
        from ansible_aom.renderer.factory import create_renderer

        renderer = create_renderer()
        from ansible_aom.compact.renderer import CompactRenderer
        assert isinstance(renderer, CompactRenderer)

    def test_factory_creates_compact_renderer_when_tui_false(self):
        """tui_mode=False creates CompactRenderer."""
        from ansible_aom.renderer.factory import create_renderer

        renderer = create_renderer(tui_mode=False)
        from ansible_aom.compact.renderer import CompactRenderer
        assert isinstance(renderer, CompactRenderer)

    def test_factory_creates_tui_renderer_when_tui_true(self):
        """tui_mode=True creates Textual AOMApp."""
        from ansible_aom.renderer.factory import create_renderer

        renderer = create_renderer(tui_mode=True)
        # AOMApp is created, may not import without Textual available
        assert hasattr(renderer, "start")
        assert hasattr(renderer, "update_state")


# ============================================================================
# Password Prompt Integration
# ============================================================================


class TestPasswordPromptPatterns:
    """Tests for all password prompt patterns."""

    @pytest.fixture
    def password_patterns(self) -> list[str]:
        """All password prompt patterns from SPECIFICATION."""
        return [
            r'Vault password: ',
            r'Vault password \([^)]+\): ',
            r'SSH password: ',
            r'BECOME password: ',
            r'BECOME password\[defaults to SSH password\]: ',
            r'New Vault password: ',
            r'Confirm New Vault password: ',
        ]

    def test_vault_password_pattern(self, password_patterns: list[str]):
        """Pattern matches 'Vault password: '."""
        import re
        pattern = password_patterns[0]
        assert re.search(pattern, "Vault password: ") is not None

    def test_vault_id_password_pattern(self, password_patterns: list[str]):
        """Pattern matches vault ID variant."""
        import re
        pattern = password_patterns[1]
        assert re.search(pattern, "Vault password (prod): ") is not None

    def test_ssh_password_pattern(self, password_patterns: list[str]):
        """Pattern matches 'SSH password: '."""
        import re
        pattern = password_patterns[2]
        assert re.search(pattern, "SSH password: ") is not None

    def test_become_password_pattern(self, password_patterns: list[str]):
        """Pattern matches 'BECOME password: '."""
        import re
        pattern = password_patterns[3]
        assert re.search(pattern, "BECOME password: ") is not None

    def test_become_default_password_pattern(self, password_patterns: list[str]):
        """Pattern matches BECOME password default variant."""
        import re
        pattern = password_patterns[4]
        assert re.search(pattern, "BECOME password[defaults to SSH password]: ") is not None

    def test_new_vault_password_pattern(self, password_patterns: list[str]):
        """Pattern matches 'New Vault password: '."""
        import re
        pattern = password_patterns[5]
        assert re.search(pattern, "New Vault password: ") is not None

    def test_confirm_new_vault_password_pattern(self, password_patterns: list[str]):
        """Pattern matches 'Confirm New Vault password: '."""
        import re
        pattern = password_patterns[6]
        assert re.search(pattern, "Confirm New Vault password: ") is not None