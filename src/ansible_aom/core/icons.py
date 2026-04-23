"""Status icon mapping for AOM display.

This module provides Unicode status icons and color mappings for task/host
execution states, following Section 11 of the specification.

Icons:
    - OK: ● (filled circle, green)
    - CHANGED: ◆ (diamond, yellow)
    - FAILED: ✖ (cross, red)
    - UNREACHABLE: ⊝ (circle dash, magenta)
    - RUNNING: ◐ ◓ ◑ ◒ (animated, cyan)
    - PENDING: □ (empty square, dim)
    - SKIPPED: ○ (empty circle, dim)

Running animation cycles through quadrants at 4 FPS.
"""

from enum import Enum

from ansible_aom.core.models import Status


# =============================================================================
# Status Icon Mappings
# =============================================================================

# Mapping from Status enum to Unicode icon string.
# See SPECIFICATION.md Section 11.1 for icon definitions.
STATUS_ICONS: dict[Status, str] = {
    Status.PENDING: "□",     # Empty square (U+25A1)
    Status.RUNNING: "◐",     # First frame of animation (U+25D0)
    Status.OK: "●",          # Filled circle (U+25CF)
    Status.CHANGED: "◆",     # Diamond (U+25C6)
    Status.FAILED: "✖",      # Cross/ballot X (U+2716)
    Status.SKIPPED: "○",     # Empty circle (U+25CB)
    Status.UNREACHABLE: "⊝", # Circle with dash (U+229D)
    Status.COMPLETED: "●",   # Same as OK (U+25CF)
}

# Running animation frames (4 frames cycling at 4 FPS)
RUNNING_FRAMES = ["◐", "◓", "◑", "◒"]

# ANSI color names for Rich/Textual rendering.
# See SPECIFICATION.md Section 11.1 for color definitions.
STATUS_COLORS: dict[Status, str] = {
    Status.PENDING: "dim",        # Dim/bright black
    Status.RUNNING: "cyan",       # Cyan for running animation
    Status.OK: "green",           # Green for success
    Status.CHANGED: "yellow",     # Yellow for changes
    Status.FAILED: "red",         # Red for failures
    Status.SKIPPED: "dim",        # Dim for skipped
    Status.UNREACHABLE: "magenta",# Magenta for unreachable
    Status.COMPLETED: "green",    # Green for completion
}


# =============================================================================
# Tree Icons
# =============================================================================

TREE_COLLAPSED = "▶"  # Right arrow for collapsed node (U+25B6)
TREE_EXPANDED = "▼"   # Down arrow for expanded node (U+25BC)


# =============================================================================
# ASCII Fallback Icons (for terminals without Unicode)
# =============================================================================

# ASCII fallback icons for terminals without Unicode support.
# See SPECIFICATION.md Section 4.6 and TC-377 for fallback mappings.
STATUS_ICONS_ASCII: dict[Status, str] = {
    Status.PENDING: ".",
    Status.RUNNING: "@",
    Status.OK: "*",
    Status.CHANGED: "+",
    Status.FAILED: "X",
    Status.SKIPPED: "o",
    Status.UNREACHABLE: "O",
    Status.COMPLETED: "*",
}


# =============================================================================
# Helper Functions
# =============================================================================


def get_status_icon(status: Status, frame: int = 0) -> str:
    """Get the icon for a given status.

    For RUNNING status, use the frame parameter to get the animation frame.
    For other statuses, frame is ignored.

    Args:
        status: The execution status (PENDING, RUNNING, OK, etc.)
        frame: Animation frame index (0-3) for RUNNING status

    Returns:
        Unicode icon string for the status

    Example:
        >>> get_status_icon(Status.OK)
        '●'
        >>> get_status_icon(Status.RUNNING, frame=2)
        '◑'
    """
    if status == Status.RUNNING:
        # Cycle through animation frames
        frame_index = frame % len(RUNNING_FRAMES)
        return RUNNING_FRAMES[frame_index]
    return STATUS_ICONS.get(status, "?")


def get_running_frame(counter: int) -> str:
    """Get the current animation frame for RUNNING status.

    Cycles through the 4 quadrant icons: ◐ → ◓ → ◑ → ◒ → ◐

    Args:
        counter: Animation frame counter (increments at 4 FPS)

    Returns:
        Single Unicode icon string for current frame

    Example:
        >>> get_running_frame(0)
        '◐'
        >>> get_running_frame(5)
        '◓'  # 5 % 4 = 1
    """
    frame_index = counter % len(RUNNING_FRAMES)
    return RUNNING_FRAMES[frame_index]


def get_status_color(status: Status) -> str:
    """Get the ANSI color name for a given status.

    Args:
        status: The execution status

    Returns:
        ANSI color name string for Rich/Textual styling

    Example:
        >>> get_status_color(Status.OK)
        'green'
        >>> get_status_color(Status.FAILED)
        'red'
    """
    return STATUS_COLORS.get(status, "white")


def get_tree_icon(expanded: bool) -> str:
    """Get tree expansion icon.

    Args:
        expanded: True for expanded node (▼), False for collapsed (▶)

    Returns:
        Unicode tree icon string

    Example:
        >>> get_tree_icon(False)
        '▶'
        >>> get_tree_icon(True)
        '▼'
    """
    return TREE_EXPANDED if expanded else TREE_COLLAPSED


def get_status_icon_ascii(status: Status) -> str:
    """Get ASCII fallback icon for terminals without Unicode support.

    Args:
        status: The execution status

    Returns:
        ASCII character string

    Example:
        >>> get_status_icon_ascii(Status.OK)
        '*'
        >>> get_status_icon_ascii(Status.FAILED)
        'X'
    """
    return STATUS_ICONS_ASCII.get(status, "?")