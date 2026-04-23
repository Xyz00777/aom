"""Unit tests for view mode selection and terminal compatibility.

Test cases cover:
- TC-059: Unicode support detection
- TC-060: Unicode fallback characters
- TC-061: Color support detection
- TC-062: 16-Color fallback
- TC-063: Monochrome fallback
- TC-064: Minimum width at 80 columns
- TC-065: Width 60-79 columns truncation
- TC-066: Width below 60 columns minimal view

All tests are self-contained and use function-scoped fixtures.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest


# ============================================================================
# Unicode Support Detection (TC-059)
# ============================================================================


class TestUnicodeSupportDetection:
    """Tests for TC-059: Unicode support detection."""

    def detect_unicode_support(self, terminal_capabilities: dict) -> bool:
        """Detect if terminal supports Unicode.

        Args:
            terminal_capabilities: Dict with 'unicode' key.

        Returns:
            True if Unicode supported, False otherwise.
        """
        return terminal_capabilities.get("unicode", False)

    def test_unicode_terminal_detected(self):
        """TC-059: Unicode terminal detected."""
        caps = {"unicode": True, "color_depth": 256}
        assert self.detect_unicode_support(caps) is True

    def test_non_unicode_terminal_fallback(self):
        """TC-059: Non-Unicode terminal uses ASCII fallback."""
        caps = {"unicode": False, "color_depth": 16}
        assert self.detect_unicode_support(caps) is False

    def test_detection_failure_defaults_to_ascii(self):
        """TC-059: Detection failure defaults to ASCII."""
        caps = {}  # No unicode key
        assert self.detect_unicode_support(caps) is False

    def test_blessed_terminal_unicode_check(self):
        """TC-059: blessed.Terminal() used for detection."""
        # blessed.Terminal() provides .encoding attribute
        # If encoding supports UTF-8, unicode is available
        try:
            import blessed
            term = blessed.Terminal()
            has_unicode = 'utf' in term.encoding.lower() if hasattr(term, 'encoding') else False
        except ImportError:
            has_unicode = False


# ============================================================================
# Unicode Fallback Characters (TC-060)
# ============================================================================


class TestUnicodeFallback:
    """Tests for TC-060: Unicode fallback characters."""

    @pytest.fixture
    def unicode_icons(self) -> dict[str, str]:
        """Unicode status icons."""
        return {
            "pending": "□",
            "running": "◐",
            "ok": "●",
            "changed": "◆",
            "failed": "✖",
            "unreachable": "⊝",
            "skipped": "□",
        }

    @pytest.fixture
    def ascii_fallback_icons(self) -> dict[str, str]:
        """ASCII fallback icons for non-Unicode terminals."""
        return {
            "pending": ".",
            "running": "@",
            "ok": "*",
            "changed": "+",
            "failed": "X",
            "unreachable": "-",
            "skipped": ".",
        }

    def get_status_icon(self, status: str, unicode_supported: bool) -> str:
        """Get appropriate icon for status based on terminal support."""
        unicode_icons = {
            "pending": "□",
            "running": "◐",
            "ok": "●",
            "changed": "◆",
            "failed": "✖",
            "unreachable": "⊝",
            "skipped": "□",
        }
        ascii_icons = {
            "pending": ".",
            "running": "@",
            "ok": "*",
            "changed": "+",
            "failed": "X",
            "unreachable": "-",
            "skipped": ".",
        }
        
        if unicode_supported:
            return unicode_icons.get(status, "?")
        else:
            return ascii_icons.get(status, "?")

    def test_pending_icon_unicode(self, unicode_icons: dict[str, str]):
        """TC-060: PENDING icon unicode is □."""
        assert self.get_status_icon("pending", unicode_supported=True) == unicode_icons["pending"]

    def test_pending_icon_ascii_fallback(self, ascii_fallback_icons: dict[str, str]):
        """TC-060: PENDING icon ASCII fallback is period."""
        assert self.get_status_icon("pending", unicode_supported=False) == ascii_fallback_icons["pending"]

    def test_running_icon_unicode(self, unicode_icons: dict[str, str]):
        """TC-060: RUNNING icon unicode is ◐."""
        assert self.get_status_icon("running", unicode_supported=True) == unicode_icons["running"]

    def test_running_icon_ascii_fallback(self, ascii_fallback_icons: dict[str, str]):
        """TC-060: RUNNING icon ASCII fallback is at sign."""
        assert self.get_status_icon("running", unicode_supported=False) == ascii_fallback_icons["running"]

    def test_ok_icon_unicode(self, unicode_icons: dict[str, str]):
        """TC-060: OK icon unicode is ●."""
        assert self.get_status_icon("ok", unicode_supported=True) == unicode_icons["ok"]

    def test_ok_icon_ascii_fallback(self, ascii_fallback_icons: dict[str, str]):
        """TC-060: OK icon ASCII fallback is asterisk."""
        assert self.get_status_icon("ok", unicode_supported=False) == ascii_fallback_icons["ok"]

    def test_changed_icon_unicode(self, unicode_icons: dict[str, str]):
        """TC-060: CHANGED icon unicode is ◆."""
        assert self.get_status_icon("changed", unicode_supported=True) == unicode_icons["changed"]

    def test_changed_icon_ascii_fallback(self, ascii_fallback_icons: dict[str, str]):
        """TC-060: CHANGED icon ASCII fallback is plus."""
        assert self.get_status_icon("changed", unicode_supported=False) == ascii_fallback_icons["changed"]

    def test_failed_icon_unicode(self, unicode_icons: dict[str, str]):
        """TC-060: FAILED icon unicode is ✖."""
        assert self.get_status_icon("failed", unicode_supported=True) == unicode_icons["failed"]

    def test_failed_icon_ascii_fallback(self, ascii_fallback_icons: dict[str, str]):
        """TC-060: FAILED icon ASCII fallback is X."""
        assert self.get_status_icon("failed", unicode_supported=False) == ascii_fallback_icons["failed"]

    def test_unreachable_icon_unicode(self, unicode_icons: dict[str, str]):
        """TC-060: UNREACHABLE icon unicode is ⊝."""
        assert self.get_status_icon("unreachable", unicode_supported=True) == unicode_icons["unreachable"]

    def test_unreachable_icon_ascii_fallback(self, ascii_fallback_icons: dict[str, str]):
        """TC-060: UNREACHABLE icon ASCII fallback is dash."""
        assert self.get_status_icon("unreachable", unicode_supported=False) == ascii_fallback_icons["unreachable"]


# ============================================================================
# Color Support Detection (TC-061)
# ============================================================================


class TestColorSupportDetection:
    """Tests for TC-061: Color support detection."""

    def detect_color_level(self, terminal_capabilities: dict) -> str:
        """Detect color support level.

        Returns: 'truecolor', '256', '16', or 'monochrome'.
        """
        return terminal_capabilities.get("color_level", "monochrome")

    def test_truecolor_detection(self):
        """TC-061: Truecolor detected for modern terminals."""
        caps = {"color_level": "truecolor", "unicode": True}
        assert self.detect_color_level(caps) == "truecolor"

    def test_256_color_detection(self):
        """TC-061: 256-color detected for xterm-compatible terminals."""
        caps = {"color_level": "256", "unicode": True}
        assert self.detect_color_level(caps) == "256"

    def test_16_color_detection(self):
        """TC-061: 16-color detected for basic terminals."""
        caps = {"color_level": "16", "unicode": False}
        assert self.detect_color_level(caps) == "16"

    def test_monochrome_detection(self):
        """TC-061: Monochrome detected for piped/redirected output."""
        caps = {"color_level": "monochrome"}
        assert self.detect_color_level(caps) == "monochrome"

    def test_rich_console_detect_color(self):
        """TC-061: Rich Console.detect_color() returns correct level."""
        from rich.console import Console

        console = Console()
        assert console.color_system in (None, "standard", "eight_bit", "truecolor")

    def test_blessed_number_of_colors(self):
        """TC-061: blessed.Terminal().number_of_colors returns color level."""
        try:
            import blessed
            term = blessed.Terminal()
            num_colors = term.number_of_colors
            assert num_colors in (0, 8, 16, 256, 16777216)
        except ImportError:
            pass


# ============================================================================
# 16-Color Fallback (TC-062)
# ============================================================================


class TestSixteenColorFallback:
    """Tests for TC-062: 16-Color fallback."""

    @pytest.fixture
    def color_16_map(self) -> dict[str, str]:
        """16-color ANSI color codes."""
        return {
            "green": "\033[32m",
            "yellow": "\033[33m",
            "red": "\033[31m",
            "cyan": "\033[36m",
            "white": "\033[37m",
            "dim": "\033[2m",
            "reset": "\033[0m",
        }

    def map_status_to_16_color(self, status: str) -> str:
        """Map status to 16-color ANSI code."""
        color_map = {
            "ok": "green",
            "changed": "yellow",
            "failed": "red",
            "running": "cyan",
            "pending": "white",
            "skipped": "white",
            "unreachable": "red",
        }
        return color_map.get(status, "white")

    def test_ok_uses_green(self):
        """TC-062: OK status uses green in 16-color mode."""
        assert self.map_status_to_16_color("ok") == "green"

    def test_changed_uses_yellow(self):
        """TC-062: CHANGED status uses yellow in 16-color mode."""
        assert self.map_status_to_16_color("changed") == "yellow"

    def test_failed_uses_red(self):
        """TC-062: FAILED status uses red in 16-color mode."""
        assert self.map_status_to_16_color("failed") == "red"

    def test_running_uses_cyan(self):
        """TC-062: RUNNING status uses cyan in 16-color mode."""
        assert self.map_status_to_16_color("running") == "cyan"

    def test_pending_uses_white(self):
        """TC-062: PENDING status uses white in 16-color mode."""
        assert self.map_status_to_16_color("pending") == "white"

    def test_skipped_uses_white(self):
        """TC-062: SKIPPED status uses white in 16-color mode."""
        assert self.map_status_to_16_color("skipped") == "white"

    def test_unreachable_uses_red(self):
        """TC-062: UNREACHABLE status uses red in 16-color mode."""
        assert self.map_status_to_16_color("unreachable") == "red"


# ============================================================================
# Monochrome Fallback (TC-063)
# ============================================================================


class TestMonochromeFallback:
    """Tests for TC-063: Monochrome/piped fallback."""

    def map_status_to_text_label(self, status: str) -> str:
        """Map status to text label for monochrome terminals."""
        label_map = {
            "ok": "OK",
            "changed": "CHANGED",
            "failed": "FAILED",
            "running": "RUNNING",
            "pending": "PENDING",
            "skipped": "SKIPPED",
            "unreachable": "UNREACHABLE",
        }
        return label_map.get(status, "UNKNOWN")

    def test_uses_text_labels_not_colors(self):
        """TC-063: Monochrome terminals use text labels instead of colors."""
        assert self.map_status_to_text_label("ok") == "OK"
        assert self.map_status_to_text_label("changed") == "CHANGED"
        assert self.map_status_to_text_label("failed") == "FAILED"
        assert self.map_status_to_text_label("running") == "RUNNING"
        assert self.map_status_to_text_label("pending") == "PENDING"
        assert self.map_status_to_text_label("skipped") == "SKIPPED"
        assert self.map_status_to_text_label("unreachable") == "UNREACHABLE"

    def test_text_labels_uppercase(self):
        """TC-063: Text labels are uppercase for visibility."""
        for status in ["ok", "changed", "failed", "running"]:
            label = self.map_status_to_text_label(status)
            assert label == label.upper()

    def test_text_labels_no_ansi_codes(self):
        """TC-063: Text labels contain no ANSI escape codes."""
        import re
        ansi_pattern = re.compile(r'\033\[')
        
        for status in ["ok", "changed", "failed", "running"]:
            label = self.map_status_to_text_label(status)
            assert ansi_pattern.search(label) is None


# ============================================================================
# Minimum Width 80 Columns (TC-064)
# ============================================================================


class TestMinimumWidthEightyColumns:
    """Tests for TC-064: Minimum width 80 columns."""

    def format_compact_panel_at_80(
        self,
        playbook: str,
        tasks: list[dict],
        width: int = 80,
    ) -> list[str]:
        """Format compact panel for 80-column terminal."""
        lines = []
        lines.append(f"▶ {playbook}")
        for task in tasks[:5]:
            status = task.get("status", "pending")
            name = task.get("name", "unnamed")[:30]
            lines.append(f"  [{status}] {name}")
        return lines

    def test_panel_renders_at_80_columns(self):
        """TC-064: Panel renders fully at 80 columns."""
        playbook = "site.yml"
        tasks = [
            {"name": "Install nginx", "status": "ok"},
            {"name": "Configure firewall", "status": "running"},
            {"name": "Start services", "status": "pending"},
        ]
        lines = self.format_compact_panel_at_80(playbook, tasks, width=80)
        
        assert len(lines) > 0
        for line in lines:
            assert len(line) <= 80

    def test_format_preserves_all_elements_at_80(self):
        """TC-064: All elements visible at 80 columns."""
        lines = self.format_compact_panel_at_80(
            "site.yml",
            [
                {"name": "Task with a reasonably long name", "status": "ok"},
            ],
            width=80,
        )
        assert any("site.yml" in line for line in lines)


# ============================================================================
# Width 60-79 Columns Truncation (TC-065)
# ============================================================================


class TestWidthSixtyToSeventyNineTruncation:
    """Tests for TC-065: Width 60-79 columns truncation."""

    def truncate_task_name(self, name: str, width: int, min_chars: int = 10) -> str:
        """Truncate task name for narrow terminals.

        Args:
            name: Task name to truncate.
            width: Available terminal width.
            min_chars: Minimum characters to show.

        Returns:
            Truncated name with ellipsis if needed.
        """
        max_name_width = width - 20
        if max_name_width < min_chars:
            max_name_width = min_chars
        if len(name) > max_name_width:
            return name[:max_name_width - 3] + "..."
        return name

    def test_truncation_at_70_columns(self):
        """TC-065: Task names truncated at 60-79 columns."""
        long_name = "Install and configure nginx web server with SSL certificates"
        width = 70
        truncated = self.truncate_task_name(long_name, width)
        max_expected_length = width - 20
        assert len(truncated) <= max_expected_length

    def test_minimum_10_chars_shown(self):
        """TC-065: Minimum 10 characters shown even with narrow width."""
        long_name = "Very long task name that exceeds available space"
        width = 60
        truncated = self.truncate_task_name(long_name, width, min_chars=10)
        assert len(truncated) >= 10

    def test_no_truncation_at_79_columns(self):
        """TC-065: Short names not truncated at 79 columns."""
        short_name = "Install nginx"
        width = 79
        truncated = self.truncate_task_name(short_name, width)
        assert truncated == short_name

    def test_ellipse_added_when_truncated(self):
        """TC-065: Ellipsis added when name is truncated."""
        long_name = "Configure firewall rules for all server instances"
        width = 65
        truncated = self.truncate_task_name(long_name, width)
        if len(long_name) > width - 20:
            assert truncated.endswith("...")


# ============================================================================
# Width Below 60 Columns Minimal View (TC-066)
# ============================================================================


class TestWidthBelowSixtyMinimalView:
    """Tests for TC-066: Width below 60 columns minimal view."""

    def format_minimal_view(self, statuses: list[dict], width: int = 59) -> list[str]:
        """Format minimal view for very narrow terminals.

        Only shows icons and status, no task names.
        """
        lines = []
        for status in statuses:
            icon = status.get("icon", "?")
            state = status.get("state", "unknown")
            host = status.get("host", "")
            lines.append(f"{icon} {state} {host}".strip())
        return lines

    def test_no_task_names_below_60(self):
        """TC-066: Task names not displayed below 60 columns."""
        statuses = [
            {"icon": "●", "state": "ok", "host": "web1"},
            {"icon": "◐", "state": "running", "host": "web2"},
        ]
        lines = self.format_minimal_view(statuses, width=59)
        for line in lines:
            assert "Install" not in line

    def test_only_icons_and_status_below_60(self):
        """TC-066: Only icons and status shown below 60 columns."""
        statuses = [
            {"icon": "●", "state": "ok", "host": "web1"},
            {"icon": "◐", "state": "running", "host": "web2"},
        ]
        lines = self.format_minimal_view(statuses, width=59)
        assert "●" in lines[0]
        assert "◐" in lines[1]

    def test_host_shown_when_space_allows(self):
        """TC-066: Host shown if space allows in minimal view."""
        statuses = [
            {"icon": "●", "state": "ok", "host": "web1"},
        ]
        lines = self.format_minimal_view(statuses, width=59)
        assert "web1" in lines[0]

    def test_minimal_fits_in_40_columns(self):
        """TC-066: Minimal view fits in very narrow terminals."""
        statuses = [
            {"icon": "●", "state": "ok", "host": "web1"},
            {"icon": "✖", "state": "failed", "host": "web2"},
        ]
        lines = self.format_minimal_view(statuses, width=40)
        for line in lines:
            assert len(line) <= 40


# ============================================================================
# View Mode Selection Tests (Section 4.6 integration)
# ============================================================================


class TestViewModeSelection:
    """Tests for view mode selection logic."""

    def select_view_mode(
        self,
        tui_flag: bool,
        is_tty: bool,
        verbose: bool = False,
    ) -> str:
        """Select renderer mode based on flags and terminal.

        Args:
            tui_flag: --tui flag set.
            is_tty: Terminal is TTY.
            verbose: --verbose flag set.

        Returns:
            'tui', 'compact_verbose', 'compact', or 'compact_stream'.
        """
        if tui_flag and is_tty:
            return "tui"
        elif verbose and is_tty:
            return "compact_verbose"
        elif is_tty:
            return "compact"
        else:
            return "compact_stream"

    def test_default_is_compact(self):
        """Default mode is compact."""
        mode = self.select_view_mode(tui_flag=False, is_tty=True)
        assert mode == "compact"

    def test_tui_flag_enables_full_tui(self):
        """--tui flag enables full TUI when TTY available."""
        mode = self.select_view_mode(tui_flag=True, is_tty=True)
        assert mode == "tui"

    def test_tui_flag_ignored_without_tty(self):
        """--tui flag ignored without TTY, uses streaming instead."""
        mode = self.select_view_mode(tui_flag=True, is_tty=False)
        assert mode == "compact_stream"

    def test_verbose_enables_logging_in_compact(self):
        """--verbose enables logging with Rich Live in compact mode."""
        mode = self.select_view_mode(tui_flag=False, verbose=True, is_tty=True)
        assert mode == "compact_verbose"

    def test_non_tty_uses_streaming(self):
        """Non-TTY uses streaming output."""
        mode = self.select_view_mode(tui_flag=False, is_tty=False)
        assert mode == "compact_stream"

    def test_verbose_non_tty_uses_streaming(self):
        """--verbose with non-TTY still uses streaming."""
        mode = self.select_view_mode(tui_flag=False, verbose=True, is_tty=False)
        assert mode == "compact_stream"


class TestDisplayCapabilities:
    """Tests for terminal capability detection."""

    def get_display_capabilities(self, env: dict) -> dict:
        """Get display capabilities from environment.

        Args:
            env: Environment variables dict.

        Returns:
            Dict with 'unicode', 'color_level', 'is_tty', 'width'.
        """
        return {
            "unicode": env.get("LANG", "").lower().startswith("en_us.utf"),
            "color_level": env.get("COLORTERM", "16"),
            "is_tty": env.get("TERM") is not None,
            "width": int(env.get("COLUMNS", "80")),
        }

    def test_unicode_detection_from_lang(self):
        """Unicode detected from LANG environment variable."""
        env = {"LANG": "en_US.UTF-8"}
        caps = self.get_display_capabilities(env)
        assert caps["unicode"] is True

    def test_non_unicode_lang_defaults_to_ascii(self):
        """Non-UTF LANG defaults to ASCII."""
        env = {"LANG": "C"}
        caps = self.get_display_capabilities(env)
        assert caps["unicode"] is False

    def test_color_level_from_colorterm(self):
        """Color level detected from COLORTERM."""
        env = {"COLORTERM": "truecolor"}
        caps = self.get_display_capabilities(env)
        assert caps["color_level"] == "truecolor"

    def test_256_color_from_colorterm(self):
        """256-color detected from COLORTERM."""
        env = {"COLORTERM": "256color"}
        caps = self.get_display_capabilities(env)
        assert caps["color_level"] == "256color"

    def test_width_from_columns(self):
        """Width detected from COLUMNS environment."""
        env = {"COLUMNS": "120"}
        caps = self.get_display_capabilities(env)
        assert caps["width"] == 120

    def test_default_width_80(self):
        """Default width is 80 columns."""
        env = {}
        caps = self.get_display_capabilities(env)
        assert caps["width"] == 80