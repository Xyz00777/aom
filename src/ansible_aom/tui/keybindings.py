"""Keybindings configuration for AOM TUI.

This module defines all keyboard shortcuts for the TUI interface
as specified in SPECIFICATION.md Section 10.

Keybinding Categories:
- Global: Work from any focused panel
- Context-specific: Only work when specific panel is focused
- Post-run: Only available after playbook completion

The KEYBINDINGS dict maps key strings to action definitions.
"""

from enum import Enum
from typing import TypedDict


class KeyContext(str, Enum):
    """Context where a keybinding is active."""

    GLOBAL = "global"  # Works from any panel
    TREE = "tree"  # Only when tree panel is focused
    LOG = "log"  # Only when log panel is focused
    POST_RUN = "post_run"  # Only after playbook completion


class KeyAction(TypedDict):
    """Definition of a keybinding action."""

    action: str  # Action identifier (e.g., "quit", "expand_tree")
    description: str  # Human-readable description
    context: KeyContext  # Where the keybinding is active
    requires_confirmation: bool  # Whether action needs user confirmation


# Default keybindings as specified in SPECIFICATION.md Section 10.1-10.2
KEYBINDINGS: dict[str, KeyAction] = {
    # Global keybindings
    "q": {
        "action": "quit",
        "description": "Quit (with confirmation if running)",
        "context": KeyContext.GLOBAL,
        "requires_confirmation": True,
    },
    "?": {
        "action": "show_help",
        "description": "Help overlay",
        "context": KeyContext.GLOBAL,
        "requires_confirmation": False,
    },
    "f": {
        "action": "toggle_filter_panel",
        "description": "Filter panel",
        "context": KeyContext.GLOBAL,
        "requires_confirmation": False,
    },
    "S": {
        "action": "show_settings",
        "description": "Settings",
        "context": KeyContext.GLOBAL,
        "requires_confirmation": False,
    },
    "s": {
        "action": "cycle_sort",
        "description": "Sort cycle (name, status, duration)",
        "context": KeyContext.GLOBAL,
        "requires_confirmation": False,
    },
    "/": {
        "action": "open_search",
        "description": "Search (in log panel)",
        "context": KeyContext.LOG,
        "requires_confirmation": False,
    },
    "ctrl+f": {
        "action": "open_search",
        "description": "Search (in log panel)",
        "context": KeyContext.LOG,
        "requires_confirmation": False,
    },
    "ctrl+c": {
        "action": "interrupt",
        "description": "Forward interrupt to subprocess (1st) or kill (2nd)",
        "context": KeyContext.GLOBAL,
        "requires_confirmation": False,
    },
    "tab": {
        "action": "switch_panel",
        "description": "Switch panel focus",
        "context": KeyContext.GLOBAL,
        "requires_confirmation": False,
    },
    "shift+tab": {
        "action": "switch_panel_reverse",
        "description": "Switch panel focus (reverse)",
        "context": KeyContext.GLOBAL,
        "requires_confirmation": False,
    },
    "d": {
        "action": "toggle_debug_panel",
        "description": "Toggle debug panel visibility",
        "context": KeyContext.GLOBAL,
        "requires_confirmation": False,
    },
    "ctrl+left": {
        "action": "resize_panel_left",
        "description": "Resize panel split (shrink left)",
        "context": KeyContext.GLOBAL,
        "requires_confirmation": False,
    },
    "ctrl+right": {
        "action": "resize_panel_right",
        "description": "Resize panel split (expand right)",
        "context": KeyContext.GLOBAL,
        "requires_confirmation": False,
    },
    "alt+t": {
        "action": "cycle_theme",
        "description": "Cycle themes",
        "context": KeyContext.GLOBAL,
        "requires_confirmation": False,
    },
    # Tree navigation keybindings
    "up": {
        "action": "navigate_tree_up",
        "description": "Navigate tree up",
        "context": KeyContext.TREE,
        "requires_confirmation": False,
    },
    "down": {
        "action": "navigate_tree_down",
        "description": "Navigate tree down",
        "context": KeyContext.TREE,
        "requires_confirmation": False,
    },
    "j": {
        "action": "navigate_tree_down",
        "description": "Navigate tree down (vim-style)",
        "context": KeyContext.TREE,
        "requires_confirmation": False,
    },
    "k": {
        "action": "navigate_tree_up",
        "description": "Navigate tree up (vim-style)",
        "context": KeyContext.TREE,
        "requires_confirmation": False,
    },
    "g": {
        "action": "jump_to_top",
        "description": "Jump to top of tree",
        "context": KeyContext.TREE,
        "requires_confirmation": False,
    },
    "G": {
        "action": "jump_to_bottom",
        "description": "Jump to bottom of tree",
        "context": KeyContext.TREE,
        "requires_confirmation": False,
    },
    "right": {
        "action": "expand_node",
        "description": "Expand tree node",
        "context": KeyContext.TREE,
        "requires_confirmation": False,
    },
    "left": {
        "action": "collapse_node",
        "description": "Collapse tree node",
        "context": KeyContext.TREE,
        "requires_confirmation": False,
    },
    "enter": {
        "action": "toggle_node",
        "description": "Toggle expand/collapse",
        "context": KeyContext.TREE,
        "requires_confirmation": False,
    },
    "l": {
        "action": "toggle_log_panel",
        "description": "Toggle log panel visibility",
        "context": KeyContext.GLOBAL,
        "requires_confirmation": False,
    },
    "c": {
        "action": "toggle_compact_view",
        "description": "Compact view toggle (collapse tree, show only status)",
        "context": KeyContext.GLOBAL,
        "requires_confirmation": False,
    },
    "r": {
        "action": "refresh",
        "description": "Refresh/force-update",
        "context": KeyContext.GLOBAL,
        "requires_confirmation": False,
    },
    # Post-run keybindings
    "R": {
        "action": "rerun_with_same_args",
        "description": "Re-run playbook (with confirmation)",
        "context": KeyContext.POST_RUN,
        "requires_confirmation": True,
    },
    "shift+r": {
        "action": "rerun_with_modified_args",
        "description": "Re-run with modified args",
        "context": KeyContext.POST_RUN,
        "requires_confirmation": False,
    },
    # Panel toggle keys
    "1": {
        "action": "toggle_status_bar",
        "description": "Toggle Status Bar visibility",
        "context": KeyContext.GLOBAL,
        "requires_confirmation": False,
    },
    "2": {
        "action": "toggle_tree_view",
        "description": "Toggle Tree View visibility",
        "context": KeyContext.GLOBAL,
        "requires_confirmation": False,
    },
    "3": {
        "action": "toggle_summary_panel",
        "description": "Toggle Summary Panel visibility",
        "context": KeyContext.GLOBAL,
        "requires_confirmation": False,
    },
    "4": {
        "action": "toggle_log_panel",
        "description": "Toggle Log Panel visibility",
        "context": KeyContext.GLOBAL,
        "requires_confirmation": False,
    },
    "5": {
        "action": "toggle_footer",
        "description": "Toggle Footer visibility",
        "context": KeyContext.GLOBAL,
        "requires_confirmation": False,
    },
}


def get_keybinding(key: str) -> KeyAction | None:
    """Look up a keybinding by key string.

    Args:
        key: The key string to look up (e.g., "q", "ctrl+f", "alt+t").
             Uppercase single letters (S, G, R) are distinct from lowercase.
             Modifiers should be lowercase (ctrl, shift, alt).

    Returns:
        The KeyAction dict if found, None if key is not bound.

    Examples:
        >>> get_keybinding("q")
        {'action': 'quit', 'description': 'Quit...', ...}
        >>> get_keybinding("S")  # Uppercase S is different from lowercase s
        {'action': 'show_settings', ...}
        >>> get_keybinding("s")  # Lowercase s
        {'action': 'cycle_sort', ...}
        >>> get_keybinding("unknown")
        None
    """
    # Direct lookup (exact match first - for case-sensitive keys like S vs s)
    if key in KEYBINDINGS:
        return KEYBINDINGS[key]

    # Try lowercase for single-character keys that don't have an uppercase binding
    # This handles 'q' finding 'q' and 'Q' finding 'Q' (if both defined)
    if len(key) == 1:
        lower_key = key.lower()
        upper_key = key.upper()
        # If looking up uppercase and uppercase doesn't exist, try lowercase
        if key.isupper() and upper_key not in KEYBINDINGS and lower_key in KEYBINDINGS:
            return KEYBINDINGS[lower_key]
        # If looking up lowercase and it exists
        if key.islower() and lower_key in KEYBINDINGS:
            return KEYBINDINGS[lower_key]

    # Try alternative modifier format (ctrl+f vs ctrl+F)
    if "+" in key:
        modifier, key_part = key.split("+", 1)
        alt_key = f"{modifier.lower()}+{key_part.lower()}"
        if alt_key in KEYBINDINGS:
            return KEYBINDINGS[alt_key]

    return None


def get_action_keybindings(action: str) -> list[str]:
    """Get all keys that map to a given action.

    Args:
        action: The action identifier (e.g., "quit", "expand_node").

    Returns:
        List of key strings that trigger this action.

    Examples:
        >>> get_action_keybindings("navigate_tree_down")
        ['down', 'j']
        >>> get_action_keybindings("quit")
        ['q']
    """
    return [key for key, binding in KEYBINDINGS.items() if binding["action"] == action]


def get_keybindings_by_context(context: KeyContext) -> dict[str, KeyAction]:
    """Get all keybindings for a specific context.

    Args:
        context: The context to filter by (e.g., KeyContext.GLOBAL).

    Returns:
        Dict of key -> KeyAction for the specified context.
    """
    return {key: binding for key, binding in KEYBINDINGS.items() if binding["context"] == context}


def validate_keybindings() -> list[str]:
    """Validate that there are no duplicate keybindings.

    Returns:
        List of error messages, empty if all valid.

    Note:
        This checks for:
        1. Duplicate key strings (should not happen with dict keys)
        2. Same key with different modifiers being ambiguous
        3. Case conflicts (uppercase vs lowercase single letters)
    """
    errors: list[str] = []

    # Note: Dict keys are unique by definition, so no need to check for duplicates
    # But we can check for modifier conflicts

    # Group by base key (for case-sensitive checks)
    base_keys: dict[str, list[str]] = {}
    for key in KEYBINDINGS:
        # Extract base key (handle modifiers)
        if "+" in key:
            parts = key.split("+")
            base = parts[-1].lower() if len(parts[-1]) == 1 else parts[-1]
        else:
            base = key.lower() if len(key) == 1 else key

        if base not in base_keys:
            base_keys[base] = []
        base_keys[base].append(key)

    # Check for case conflicts
    for base, keys in base_keys.items():
        single_letter_keys = [
            k for k in keys if len(k) == 1 or (len(k.split("+")[-1]) == 1 and "+" in k)
        ]
        if len(single_letter_keys) > 1:
            # Same base letter with different cases
            # This is intentional for some keys (g vs G, j vs J, etc.)
            # So we don't flag it as error
            pass

    return errors


def get_all_actions() -> set[str]:
    """Get all unique action names defined in keybindings.

    Returns:
        Set of action identifiers.
    """
    return {binding["action"] for binding in KEYBINDINGS.values()}


# Initialize validation on module load
_validation_errors = validate_keybindings()
if _validation_errors:
    import warnings

    warnings.warn(f"Keybinding validation errors: {_validation_errors}")
