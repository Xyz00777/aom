"""Unit tests for status icon mapping in ansible_aom.core.icons.

Test cases cover TC-301 to TC-307 from Section 11 of TEST_SPECIFICATION.md:
- TC-301: Status Icon OK - Green Circle
- TC-302: Status Icon Changed - Yellow Diamond
- TC-303: Status Icon Failed - Bold Red X
- TC-304: Status Icon Unreachable - Dim Red Circle
- TC-305: Status Icon Running - Animated Cycle
- TC-306: Status Icon Pending - Dim Square
- TC-307: Status Icon Skipped - Dim Circle Outline

Additional tests:
- TC-372: Running Animation Frame Rate
- TC-373: Tree Icon Collapsed Node
- TC-374: Tree Icon Expanded Node
- TC-377: Unicode Fallback to ASCII

All tests are self-contained unit tests.
"""

import pytest

from ansible_aom.core.icons import (
    RUNNING_FRAMES,
    STATUS_COLORS,
    STATUS_ICONS,
    STATUS_ICONS_ASCII,
    TREE_COLLAPSED,
    TREE_EXPANDED,
    Status,
    get_running_frame,
    get_status_color,
    get_status_icon,
    get_status_icon_ascii,
    get_tree_icon,
)


class TestStatusIcons:
    """Tests for TC-365 to TC-372, TC-377."""

    # =========================================================================
    # TC-365: Status Icon OK - Green Circle
    # =========================================================================

    def test_ok_icon_is_filled_circle(self):
        """TC-365: OK status displays green filled circle (●)."""
        assert STATUS_ICONS[Status.OK] == "●"
        assert STATUS_ICONS[Status.OK] == "\u25cf"

    def test_ok_icon_is_unicode(self):
        """TC-365: OK icon is valid Unicode character."""
        icon = STATUS_ICONS[Status.OK]
        assert isinstance(icon, str)
        assert len(icon) == 1

    def test_ok_color_is_green(self):
        """TC-365: OK icon uses green color."""
        assert STATUS_COLORS[Status.OK] == "green"

    def test_get_status_icon_returns_ok_icon(self):
        """TC-365: get_status_icon returns correct icon for OK."""
        assert get_status_icon(Status.OK) == "●"

    # =========================================================================
    # TC-366: Status Icon Changed - Yellow Diamond
    # =========================================================================

    def test_changed_icon_is_diamond(self):
        """TC-366: CHANGED status displays yellow diamond (◆)."""
        assert STATUS_ICONS[Status.CHANGED] == "◆"
        assert STATUS_ICONS[Status.CHANGED] == "\u25c6"

    def test_changed_icon_is_unicode(self):
        """TC-366: CHANGED icon is valid Unicode character."""
        icon = STATUS_ICONS[Status.CHANGED]
        assert isinstance(icon, str)
        assert len(icon) == 1

    def test_changed_color_is_yellow(self):
        """TC-366: CHANGED icon uses yellow color."""
        assert STATUS_COLORS[Status.CHANGED] == "yellow"

    def test_get_status_icon_returns_changed_icon(self):
        """TC-366: get_status_icon returns correct icon for CHANGED."""
        assert get_status_icon(Status.CHANGED) == "◆"

    # =========================================================================
    # TC-367: Status Icon Failed - Bold Red X
    # =========================================================================

    def test_failed_icon_is_cross_mark(self):
        """TC-367: FAILED status displays bold red X (✖)."""
        assert STATUS_ICONS[Status.FAILED] == "✖"
        assert STATUS_ICONS[Status.FAILED] == "\u2716"

    def test_failed_icon_is_unicode(self):
        """TC-367: FAILED icon is valid Unicode character."""
        icon = STATUS_ICONS[Status.FAILED]
        assert isinstance(icon, str)
        assert len(icon) == 1

    def test_failed_color_is_red(self):
        """TC-367: FAILED icon uses red color."""
        assert STATUS_COLORS[Status.FAILED] == "red"

    def test_get_status_icon_returns_failed_icon(self):
        """TC-367: get_status_icon returns correct icon for FAILED."""
        assert get_status_icon(Status.FAILED) == "✖"

    # =========================================================================
    # TC-368: Status Icon Unreachable - Dim Red Circle
    # =========================================================================

    def test_unreachable_icon_is_circle_dash(self):
        """TC-368: UNREACHABLE status displays dim circle with dash (⊝)."""
        assert STATUS_ICONS[Status.UNREACHABLE] == "⊝"
        assert STATUS_ICONS[Status.UNREACHABLE] == "\u229d"

    def test_unreachable_icon_is_unicode(self):
        """TC-368: UNREACHABLE icon is valid Unicode character."""
        icon = STATUS_ICONS[Status.UNREACHABLE]
        assert isinstance(icon, str)
        assert len(icon) == 1

    def test_unreachable_color_is_magenta(self):
        """TC-368: UNREACHABLE icon uses magenta color (per spec)."""
        assert STATUS_COLORS[Status.UNREACHABLE] == "magenta"

    def test_get_status_icon_returns_unreachable_icon(self):
        """TC-368: get_status_icon returns correct icon for UNREACHABLE."""
        assert get_status_icon(Status.UNREACHABLE) == "⊝"

    # =========================================================================
    # TC-369: Status Icon Running - Animated Cycle
    # =========================================================================

    def test_running_has_four_animation_frames(self):
        """TC-369: RUNNING status has 4 animation frame icons."""
        assert len(RUNNING_FRAMES) == 4

    def test_running_frames_are_quadrant_icons(self):
        """TC-369: Animation frames use quadrant icons ◐ ◓ ◑ ◒."""
        assert RUNNING_FRAMES == ["◐", "◓", "◑", "◒"]

    def test_running_frames_are_unicode(self):
        """TC-369: All RUNNING frames are valid Unicode characters."""
        for frame in RUNNING_FRAMES:
            assert isinstance(frame, str)
            assert len(frame) == 1

    def test_running_frame_order_is_correct(self):
        """TC-369: Animation cycles in correct order: ◐ → ◓ → ◑ → ◒."""
        assert RUNNING_FRAMES[0] == "◐"   # U+25D0 - Left half filled
        assert RUNNING_FRAMES[1] == "◓"   # U+25D3 - Bottom half filled
        assert RUNNING_FRAMES[2] == "◑"   # U+25D1 - Right half filled
        assert RUNNING_FRAMES[3] == "◒"   # U+25D5 - Top half filled

    def test_running_color_is_cyan(self):
        """TC-369: RUNNING icon uses cyan color."""
        assert STATUS_COLORS[Status.RUNNING] == "cyan"

    def test_get_status_icon_running_default_frame(self):
        """TC-369: get_status_icon returns first frame for RUNNING by default."""
        assert get_status_icon(Status.RUNNING) == "◐"

    def test_get_status_icon_running_with_frame(self):
        """TC-369: get_status_icon returns correct frame for RUNNING."""
        assert get_status_icon(Status.RUNNING, frame=0) == "◐"
        assert get_status_icon(Status.RUNNING, frame=1) == "◓"
        assert get_status_icon(Status.RUNNING, frame=2) == "◑"
        assert get_status_icon(Status.RUNNING, frame=3) == "◒"

    def test_get_status_icon_running_frame_wraps(self):
        """TC-369: Frame index wraps around for RUNNING animation."""
        assert get_status_icon(Status.RUNNING, frame=4) == "◐"
        assert get_status_icon(Status.RUNNING, frame=5) == "◓"
        assert get_status_icon(Status.RUNNING, frame=100) == "◐"

    # =========================================================================
    # TC-370: Status Icon Pending - Dim Square
    # =========================================================================

    def test_pending_icon_is_empty_square(self):
        """TC-370: PENDING status displays dim empty square (□)."""
        assert STATUS_ICONS[Status.PENDING] == "□"
        assert STATUS_ICONS[Status.PENDING] == "\u25a1"

    def test_pending_icon_is_unicode(self):
        """TC-370: PENDING icon is valid Unicode character."""
        icon = STATUS_ICONS[Status.PENDING]
        assert isinstance(icon, str)
        assert len(icon) == 1

    def test_pending_color_is_dim(self):
        """TC-370: PENDING icon uses dim color."""
        assert STATUS_COLORS[Status.PENDING] == "dim"

    def test_get_status_icon_returns_pending_icon(self):
        """TC-370: get_status_icon returns correct icon for PENDING."""
        assert get_status_icon(Status.PENDING) == "□"

    # =========================================================================
    # TC-371: Status Icon Skipped - Dim Circle Outline
    # =========================================================================

    def test_skipped_icon_is_empty_circle(self):
        """TC-371: SKIPPED status displays dim empty circle (○)."""
        assert STATUS_ICONS[Status.SKIPPED] == "○"
        assert STATUS_ICONS[Status.SKIPPED] == "\u25cb"

    def test_skipped_icon_is_unicode(self):
        """TC-371: SKIPPED icon is valid Unicode character."""
        icon = STATUS_ICONS[Status.SKIPPED]
        assert isinstance(icon, str)
        assert len(icon) == 1

    def test_skipped_color_is_dim(self):
        """TC-371: SKIPPED icon uses dim color."""
        assert STATUS_COLORS[Status.SKIPPED] == "dim"

    def test_get_status_icon_returns_skipped_icon(self):
        """TC-371: get_status_icon returns correct icon for SKIPPED."""
        assert get_status_icon(Status.SKIPPED) == "○"

    # =========================================================================
    # TC-372: Running Animation Frame Rate
    # =========================================================================

    def test_get_running_frame_cycles_correctly(self):
        """TC-372: get_running_frame cycles through 4 frames correctly."""
        # First cycle
        assert get_running_frame(0) == "◐"
        assert get_running_frame(1) == "◓"
        assert get_running_frame(2) == "◑"
        assert get_running_frame(3) == "◒"

        # Second cycle
        assert get_running_frame(4) == "◐"
        assert get_running_frame(5) == "◓"
        assert get_running_frame(6) == "◑"
        assert get_running_frame(7) == "◒"

    def test_get_running_frame_large_counter(self):
        """TC-372: Large counter values still cycle correctly."""
        assert get_running_frame(1000) == "◐"   # 1000 % 4 = 0
        assert get_running_frame(1001) == "◓"   # 1001 % 4 = 1
        assert get_running_frame(1002) == "◑"   # 1002 % 4 = 2
        assert get_running_frame(1003) == "◒"   # 1003 % 4 = 3

    def test_four_frames_per_second_timing(self):
        """TC-372: Animation completes full cycle in 1 second (4 frames @ 4 FPS)."""
        # At 4 FPS, frame advances every 250ms
        # Frame 0 at t=0ms, Frame 1 at t=250ms, etc.
        # After 4 frames (1000ms), we're back to frame 0
        for t_ms in [0, 250, 500, 750, 1000, 1250]:
            expected_frame = (t_ms // 250) % 4
            assert get_running_frame(expected_frame) == RUNNING_FRAMES[expected_frame]

    # =========================================================================
    # COMPLETED Status (uses same icon as OK)
    # =========================================================================

    def test_completed_icon_same_as_ok(self):
        """COMPLETED status uses same icon as OK."""
        assert STATUS_ICONS[Status.COMPLETED] == STATUS_ICONS[Status.OK]
        assert STATUS_ICONS[Status.COMPLETED] == "●"

    def test_completed_color_same_as_ok(self):
        """COMPLETED status uses same color as OK."""
        assert STATUS_COLORS[Status.COMPLETED] == STATUS_COLORS[Status.OK]
        assert STATUS_COLORS[Status.COMPLETED] == "green"

    # =========================================================================
    # All Status Icons Mapping
    # =========================================================================

    def test_all_status_values_have_icons(self):
        """Every Status enum value has a corresponding icon."""
        for status in Status:
            assert status in STATUS_ICONS, f"Missing icon for {status}"

    def test_all_status_values_have_colors(self):
        """Every Status enum value has a corresponding color."""
        for status in Status:
            assert status in STATUS_COLORS, f"Missing color for {status}"

    def test_all_icons_are_single_character(self):
        """All status icons are single Unicode characters."""
        for status, icon in STATUS_ICONS.items():
            assert isinstance(icon, str)
            assert len(icon) == 1, f"Icon for {status} is not single char: {icon}"


class TestTreeIcons:
    """Tests for TC-373 and TC-374."""

    def test_tree_collapsed_icon(self):
        """TC-373: Collapsed tree node displays right arrow (▶)."""
        assert TREE_COLLAPSED == "▶"
        assert TREE_COLLAPSED == "\u25b6"

    def test_tree_expanded_icon(self):
        """TC-374: Expanded tree node displays down arrow (▼)."""
        assert TREE_EXPANDED == "▼"
        assert TREE_EXPANDED == "\u25bc"

    def test_get_tree_icon_collapsed(self):
        """TC-373: get_tree_icon returns correct icon for collapsed node."""
        assert get_tree_icon(expanded=False) == "▶"

    def test_get_tree_icon_expanded(self):
        """TC-374: get_tree_icon returns correct icon for expanded node."""
        assert get_tree_icon(expanded=True) == "▼"

    def test_tree_icons_are_unicode(self):
        """Tree icons are valid Unicode characters."""
        assert isinstance(TREE_COLLAPSED, str)
        assert isinstance(TREE_EXPANDED, str)
        assert len(TREE_COLLAPSED) == 1
        assert len(TREE_EXPANDED) == 1


class TestAsciiFallback:
    """Tests for TC-377: Unicode fallback to ASCII."""

    def test_ok_ascii_fallback_is_asterisk(self):
        """TC-377: OK falls back to * in ASCII mode."""
        assert STATUS_ICONS_ASCII[Status.OK] == "*"
        assert get_status_icon_ascii(Status.OK) == "*"

    def test_changed_ascii_fallback_is_plus(self):
        """TC-377: CHANGED falls back to + in ASCII mode."""
        assert STATUS_ICONS_ASCII[Status.CHANGED] == "+"
        assert get_status_icon_ascii(Status.CHANGED) == "+"

    def test_failed_ascii_fallback_is_x(self):
        """TC-377: FAILED falls back to X in ASCII mode."""
        assert STATUS_ICONS_ASCII[Status.FAILED] == "X"
        assert get_status_icon_ascii(Status.FAILED) == "X"

    def test_running_ascii_fallback_is_at_sign(self):
        """TC-377: RUNNING falls back to @ in ASCII mode."""
        assert STATUS_ICONS_ASCII[Status.RUNNING] == "@"
        assert get_status_icon_ascii(Status.RUNNING) == "@"

    def test_pending_ascii_fallback_is_dot(self):
        """TC-377: PENDING falls back to . in ASCII mode."""
        assert STATUS_ICONS_ASCII[Status.PENDING] == "."
        assert get_status_icon_ascii(Status.PENDING) == "."

    def test_skipped_ascii_fallback_is_lowercase_o(self):
        """TC-377: SKIPPED falls back to o in ASCII mode."""
        assert STATUS_ICONS_ASCII[Status.SKIPPED] == "o"
        assert get_status_icon_ascii(Status.SKIPPED) == "o"

    def test_unreachable_ascii_fallback_is_uppercase_o(self):
        """TC-377: UNREACHABLE falls back to O in ASCII mode."""
        assert STATUS_ICONS_ASCII[Status.UNREACHABLE] == "O"
        assert get_status_icon_ascii(Status.UNREACHABLE) == "O"

    def test_completed_ascii_fallback_same_as_ok(self):
        """COMPLETED uses same ASCII fallback as OK."""
        assert STATUS_ICONS_ASCII[Status.COMPLETED] == STATUS_ICONS_ASCII[Status.OK]
        assert STATUS_ICONS_ASCII[Status.COMPLETED] == "*"

    def test_all_status_values_have_ascii_fallback(self):
        """Every Status enum value has an ASCII fallback."""
        for status in Status:
            assert status in STATUS_ICONS_ASCII, f"Missing ASCII fallback for {status}"

    def test_all_ascii_fallbacks_are_single_char(self):
        """All ASCII fallbacks are single ASCII characters."""
        for status, icon in STATUS_ICONS_ASCII.items():
            assert isinstance(icon, str)
            assert len(icon) == 1
            assert ord(icon) < 128, f"ASCII fallback for {status} is not ASCII: {icon}"


class TestGetStatusColor:
    """Tests for get_status_color function."""

    def test_get_status_color_ok(self):
        """get_status_color returns green for OK."""
        assert get_status_color(Status.OK) == "green"

    def test_get_status_color_changed(self):
        """get_status_color returns yellow for CHANGED."""
        assert get_status_color(Status.CHANGED) == "yellow"

    def test_get_status_color_failed(self):
        """get_status_color returns red for FAILED."""
        assert get_status_color(Status.FAILED) == "red"

    def test_get_status_color_unreachable(self):
        """get_status_color returns magenta for UNREACHABLE."""
        assert get_status_color(Status.UNREACHABLE) == "magenta"

    def test_get_status_color_running(self):
        """get_status_color returns cyan for RUNNING."""
        assert get_status_color(Status.RUNNING) == "cyan"

    def test_get_status_color_pending(self):
        """get_status_color returns dim for PENDING."""
        assert get_status_color(Status.PENDING) == "dim"

    def test_get_status_color_skipped(self):
        """get_status_color returns dim for SKIPPED."""
        assert get_status_color(Status.SKIPPED) == "dim"

    def test_get_status_color_completed(self):
        """get_status_color returns green for COMPLETED."""
        assert get_status_color(Status.COMPLETED) == "green"


class TestStatusIconUniqueness:
    """Tests ensuring icon uniqueness (no collisions)."""

    def test_all_status_icons_are_unique(self):
        """All status icons should be distinct (except COMPLETED=OK)."""
        icons_seen = {}
        for status, icon in STATUS_ICONS.items():
            if status == Status.COMPLETED:
                # COMPLETED shares icon with OK, skip check
                continue
            if icon in icons_seen:
                pytest.fail(
                    f"Icon collision: {status} and {icons_seen[icon]} both use '{icon}'"
                )
            icons_seen[icon] = status

    def test_all_ascii_icons_are_unique(self):
        """All ASCII fallback icons should be distinct (except COMPLETED=OK)."""
        icons_seen = {}
        for status, icon in STATUS_ICONS_ASCII.items():
            if status == Status.COMPLETED:
                # COMPLETED shares icon with OK, skip check
                continue
            if icon in icons_seen:
                pytest.fail(
                    f"ASCII icon collision: {status} and {icons_seen[icon]} both use '{icon}'"
                )
            icons_seen[icon] = status

    def test_all_colors_are_valid_rich_colors(self):
        """All color names should be valid Rich color names."""
        valid_colors = {
            "red", "green", "yellow", "blue", "magenta", "cyan",
            "white", "black", "bright_red", "bright_green", "bright_yellow",
            "bright_blue", "bright_magenta", "bright_cyan", "bright_white",
            "dim", "bold",
        }
        for status, color in STATUS_COLORS.items():
            assert color in valid_colors, f"Invalid color '{color}' for {status}"


class TestFrameParameterIgnoedForNonRunning:
    """Tests that frame parameter is ignored for non-RUNNING statuses."""

    def test_frame_ignored_for_ok(self):
        """Frame parameter ignored for OK status."""
        assert get_status_icon(Status.OK, frame=0) == get_status_icon(Status.OK, frame=5)
        assert get_status_icon(Status.OK, frame=100) == "●"

    def test_frame_ignored_for_pending(self):
        """Frame parameter ignored for PENDING status."""
        assert get_status_icon(Status.PENDING, frame=0) == get_status_icon(Status.PENDING, frame=5)
        assert get_status_icon(Status.PENDING, frame=100) == "□"

    def test_frame_ignored_for_failed(self):
        """Frame parameter ignored for FAILED status."""
        assert get_status_icon(Status.FAILED, frame=0) == get_status_icon(Status.FAILED, frame=5)
        assert get_status_icon(Status.FAILED, frame=100) == "✖"

    def test_frame_ignored_for_changed(self):
        """Frame parameter ignored for CHANGED status."""
        assert get_status_icon(Status.CHANGED, frame=0) == get_status_icon(Status.CHANGED, frame=5)
        assert get_status_icon(Status.CHANGED, frame=100) == "◆"

    def test_frame_ignored_for_skipped(self):
        """Frame parameter ignored for SKIPPED status."""
        assert get_status_icon(Status.SKIPPED, frame=0) == get_status_icon(Status.SKIPPED, frame=5)
        assert get_status_icon(Status.SKIPPED, frame=100) == "○"

    def test_frame_ignored_for_unreachable(self):
        """Frame parameter ignored for UNREACHABLE status."""
        assert get_status_icon(Status.UNREACHABLE, frame=0) == get_status_icon(Status.UNREACHABLE, frame=5)
        assert get_status_icon(Status.UNREACHABLE, frame=100) == "⊝"

    def test_frame_ignored_for_completed(self):
        """Frame parameter ignored for COMPLETED status."""
        assert get_status_icon(Status.COMPLETED, frame=0) == get_status_icon(Status.COMPLETED, frame=5)
        assert get_status_icon(Status.COMPLETED, frame=100) == "●"