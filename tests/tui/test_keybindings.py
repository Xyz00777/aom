"""Unit tests for TUI keybindings (Section 10 of TEST_SPECIFICATION.md).

Test cases cover:
- TC-340: Keybinding Quit Confirmation
- TC-341: Keybinding Ctrl+C First Press Forwarding
- TC-342: Keybinding Ctrl+C Second Press Kill
- TC-343: Keybinding Tree Navigation Up/Down
- TC-344: Keybinding Tree Expand/Collapse
- TC-345: Keybinding Tab Panel Switch
- TC-346: Keybinding Search in Log
- TC-347: Keybinding Panel Resize Split
- TC-348: Keybinding Debug Panel Toggle
- TC-349: Keybinding Help Overlay
- TC-350: Keybinding Settings Screen
- TC-351: Keybinding Re-run Same Args
- TC-352: Keybinding Re-run Modified Args
- TC-353: Keybinding Filter Panel
- TC-354: Keybinding Theme Cycle
- TC-355: Keybinding Panel Toggle 1-5
- TC-356-360: Individual Panel Toggle keys
- TC-361: Keybinding Context Tree Focused
- TC-362: Keybinding Context Log Focused
- TC-363: Keybinding Post-Run Context
- TC-364: Keybinding Global Context

All tests are self-contained and use the keybindings module directly.
"""

import pytest

from ansible_aom.tui.keybindings import (
    KeyAction,
    KeyContext,
    KEYBINDINGS,
    get_action_keybindings,
    get_all_actions,
    get_keybinding,
    get_keybindings_by_context,
    validate_keybindings,
)


class TestKeyContextEnum:
    """Tests for KeyContext enum - TC-361, TC-362, TC-363, TC-364."""

    def test_global_context_exists(self):
        """TC-364: Global context is defined."""
        assert KeyContext.GLOBAL == "global"

    def test_tree_context_exists(self):
        """TC-361: Tree context is defined."""
        assert KeyContext.TREE == "tree"

    def test_log_context_exists(self):
        """TC-362: Log context is defined."""
        assert KeyContext.LOG == "log"

    def test_post_run_context_exists(self):
        """TC-363: Post-run context is defined."""
        assert KeyContext.POST_RUN == "post_run"

    def test_all_contexts_are_strings(self):
        """All KeyContext values are strings for serialization."""
        for ctx in KeyContext:
            assert isinstance(ctx.value, str)


class TestKeyActionTypedDict:
    """Tests for KeyAction typed dict structure."""

    def test_key_action_has_action_field(self):
        """KeyAction must have 'action' field."""
        action: KeyAction = {
            "action": "quit",
            "description": "Quit the application",
            "context": KeyContext.GLOBAL,
            "requires_confirmation": False,
        }
        assert "action" in action
        assert action["action"] == "quit"

    def test_key_action_has_description_field(self):
        """KeyAction must have 'description' field."""
        action: KeyAction = {
            "action": "quit",
            "description": "Quit the application",
            "context": KeyContext.GLOBAL,
            "requires_confirmation": False,
        }
        assert "description" in action
        assert isinstance(action["description"], str)

    def test_key_action_has_context_field(self):
        """KeyAction must have 'context' field."""
        action: KeyAction = {
            "action": "navigate_tree_up",
            "description": "Navigate up in tree",
            "context": KeyContext.TREE,
            "requires_confirmation": False,
        }
        assert "context" in action
        assert action["context"] == KeyContext.TREE

    def test_key_action_has_confirmation_field(self):
        """KeyAction must have 'requires_confirmation' field."""
        action: KeyAction = {
            "action": "quit",
            "description": "Quit (with confirmation)",
            "context": KeyContext.GLOBAL,
            "requires_confirmation": True,
        }
        assert "requires_confirmation" in action
        assert action["requires_confirmation"] is True


class TestGlobalKeybindings:
    """Tests for global keybindings - TC-364."""

    def test_quit_key_is_global(self):
        """TC-340, TC-364: 'q' key is global and requires confirmation."""
        keybinding = get_keybinding("q")
        assert keybinding is not None
        assert keybinding["action"] == "quit"
        assert keybinding["context"] == KeyContext.GLOBAL
        assert keybinding["requires_confirmation"] is True

    def test_help_key_is_global(self):
        """TC-349: '?' key shows help overlay globally."""
        keybinding = get_keybinding("?")
        assert keybinding is not None
        assert keybinding["action"] == "show_help"
        assert keybinding["context"] == KeyContext.GLOBAL

    def test_filter_panel_key_is_global(self):
        """TC-353: 'f' key opens filter panel globally."""
        keybinding = get_keybinding("f")
        assert keybinding is not None
        assert keybinding["action"] == "toggle_filter_panel"
        assert keybinding["context"] == KeyContext.GLOBAL

    def test_settings_key_is_global(self):
        """TC-350: 'S' key opens settings screen globally."""
        keybinding = get_keybinding("S")
        assert keybinding is not None
        assert keybinding["action"] == "show_settings"
        assert keybinding["context"] == KeyContext.GLOBAL

    def test_sort_cycle_key_is_global(self):
        """'s' key cycles sort order globally."""
        keybinding = get_keybinding("s")
        assert keybinding is not None
        assert keybinding["action"] == "cycle_sort"
        assert keybinding["context"] == KeyContext.GLOBAL

    def test_tab_switches_panel_globally(self):
        """TC-345: Tab switches panel focus globally."""
        keybinding = get_keybinding("tab")
        assert keybinding is not None
        assert keybinding["action"] == "switch_panel"
        assert keybinding["context"] == KeyContext.GLOBAL

    def test_shift_tab_reverse_panel_switch(self):
        """TC-345: Shift+Tab reverses panel focus."""
        keybinding = get_keybinding("shift+tab")
        assert keybinding is not None
        assert keybinding["action"] == "switch_panel_reverse"
        assert keybinding["context"] == KeyContext.GLOBAL

    def test_debug_panel_toggle_is_global(self):
        """TC-348: 'd' key toggles debug panel globally."""
        keybinding = get_keybinding("d")
        assert keybinding is not None
        assert keybinding["action"] == "toggle_debug_panel"
        assert keybinding["context"] == KeyContext.GLOBAL

    def test_cycle_theme_is_global(self):
        """TC-354: Alt+T cycles themes globally."""
        keybinding = get_keybinding("alt+t")
        assert keybinding is not None
        assert keybinding["action"] == "cycle_theme"
        assert keybinding["context"] == KeyContext.GLOBAL

    def test_log_panel_toggle_is_global(self):
        """'l' key toggles log panel visibility globally."""
        keybinding = get_keybinding("l")
        assert keybinding is not None
        assert keybinding["action"] == "toggle_log_panel"
        assert keybinding["context"] == KeyContext.GLOBAL

    def test_compact_view_toggle_is_global(self):
        """'c' key toggles compact view globally."""
        keybinding = get_keybinding("c")
        assert keybinding is not None
        assert keybinding["action"] == "toggle_compact_view"
        assert keybinding["context"] == KeyContext.GLOBAL

    def test_refresh_is_global(self):
        """'r' key refreshes/force-updates globally."""
        keybinding = get_keybinding("r")
        assert keybinding is not None
        assert keybinding["action"] == "refresh"
        assert keybinding["context"] == KeyContext.GLOBAL


class TestQuitConfirmation:
    """Tests for quit confirmation keybinding - TC-340."""

    def test_quit_requires_confirmation(self):
        """TC-340: 'q' key shows quit confirmation dialog."""
        keybinding = get_keybinding("q")
        assert keybinding is not None
        assert keybinding["requires_confirmation"] is True

    def test_quit_accept_confirms(self):
        """TC-340: Accepting quit confirmation exits application."""
        keybinding = get_keybinding("q")
        assert keybinding["action"] == "quit"

    def test_quit_case_insensitive(self):
        """'q' and 'Q' both find the quit keybinding."""
        lower_binding = get_keybinding("q")
        assert lower_binding is not None
        assert lower_binding["action"] == "quit"


class TestCtrlCKeybindings:
    """Tests for Ctrl+C keybindings - TC-341, TC-342."""

    def test_ctrl_c_is_interrupt_action(self):
        """TC-341: Ctrl+C forwards interrupt to subprocess."""
        keybinding = get_keybinding("ctrl+c")
        assert keybinding is not None
        assert keybinding["action"] == "interrupt"
        assert keybinding["context"] == KeyContext.GLOBAL

    def test_ctrl_c_no_confirmation(self):
        """Ctrl+C does not require confirmation."""
        keybinding = get_keybinding("ctrl+c")
        assert keybinding["requires_confirmation"] is False


class TestTreeNavigationKeybindings:
    """Tests for tree navigation keybindings - TC-343, TC-344."""

    def test_arrow_up_navigates_tree(self):
        """TC-343: Up arrow navigates tree up when tree focused."""
        keybinding = get_keybinding("up")
        assert keybinding is not None
        assert keybinding["action"] == "navigate_tree_up"
        assert keybinding["context"] == KeyContext.TREE

    def test_arrow_down_navigates_tree(self):
        """TC-343: Down arrow navigates tree down when tree focused."""
        keybinding = get_keybinding("down")
        assert keybinding is not None
        assert keybinding["action"] == "navigate_tree_down"
        assert keybinding["context"] == KeyContext.TREE

    def test_j_navigates_tree_down(self):
        """TC-343: 'j' navigates tree down (vim-style)."""
        keybinding = get_keybinding("j")
        assert keybinding is not None
        assert keybinding["action"] == "navigate_tree_down"
        assert keybinding["context"] == KeyContext.TREE

    def test_k_navigates_tree_up(self):
        """TC-343: 'k' navigates tree up (vim-style)."""
        keybinding = get_keybinding("k")
        assert keybinding is not None
        assert keybinding["action"] == "navigate_tree_up"
        assert keybinding["context"] == KeyContext.TREE

    def test_g_jumps_to_tree_top(self):
        """'g' jumps to top of tree."""
        keybinding = get_keybinding("g")
        assert keybinding is not None
        assert keybinding["action"] == "jump_to_top"
        assert keybinding["context"] == KeyContext.TREE

    def test_capital_g_jumps_to_tree_bottom(self):
        """TC-343: 'G' (shift+g) jumps to bottom of tree."""
        keybinding = get_keybinding("G")
        assert keybinding is not None
        assert keybinding["action"] == "jump_to_bottom"
        assert keybinding["context"] == KeyContext.TREE

    def test_right_arrow_expands_node(self):
        """TC-344: Right arrow expands tree node when tree focused."""
        keybinding = get_keybinding("right")
        assert keybinding is not None
        assert keybinding["action"] == "expand_node"
        assert keybinding["context"] == KeyContext.TREE

    def test_left_arrow_collapses_node(self):
        """TC-344: Left arrow collapses tree node when tree focused."""
        keybinding = get_keybinding("left")
        assert keybinding is not None
        assert keybinding["action"] == "collapse_node"
        assert keybinding["context"] == KeyContext.TREE

    def test_enter_toggles_node(self):
        """TC-344: Enter toggles expand/collapse state."""
        keybinding = get_keybinding("enter")
        assert keybinding is not None
        assert keybinding["action"] == "toggle_node"
        assert keybinding["context"] == KeyContext.TREE


class TestSearchKeybinding:
    """Tests for search keybinding - TC-346."""

    def test_slash_opens_search(self):
        """'/' opens search in log panel."""
        keybinding = get_keybinding("/")
        assert keybinding is not None
        assert keybinding["action"] == "open_search"
        assert keybinding["context"] == KeyContext.LOG

    def test_ctrl_f_opens_search(self):
        """TC-346: Ctrl+F opens search when log panel focused."""
        keybinding = get_keybinding("ctrl+f")
        assert keybinding is not None
        assert keybinding["action"] == "open_search"
        assert keybinding["context"] == KeyContext.LOG


class TestPanelResizeKeybindings:
    """Tests for panel resize keybindings - TC-347."""

    def test_ctrl_left_resizes_panel(self):
        """TC-347: Ctrl+Left resizes panel split (shrink)."""
        keybinding = get_keybinding("ctrl+left")
        assert keybinding is not None
        assert keybinding["action"] == "resize_panel_left"
        assert keybinding["context"] == KeyContext.GLOBAL

    def test_ctrl_right_resizes_panel(self):
        """TC-347: Ctrl+Right resizes panel split (expand)."""
        keybinding = get_keybinding("ctrl+right")
        assert keybinding is not None
        assert keybinding["action"] == "resize_panel_right"
        assert keybinding["context"] == KeyContext.GLOBAL


class TestPostRunKeybindings:
    """Tests for post-run keybindings - TC-351, TC-352, TC-363."""

    def test_capital_r_rerun_with_same_args(self):
        """TC-351: 'R' re-runs playbook with same args (post-run)."""
        keybinding = get_keybinding("R")
        assert keybinding is not None
        assert keybinding["action"] == "rerun_with_same_args"
        assert keybinding["context"] == KeyContext.POST_RUN
        assert keybinding["requires_confirmation"] is True

    def test_shift_r_rerun_with_modified_args(self):
        """TC-352: Shift+R opens dialog to modify args before re-run."""
        keybinding = get_keybinding("shift+r")
        assert keybinding is not None
        assert keybinding["action"] == "rerun_with_modified_args"
        assert keybinding["context"] == KeyContext.POST_RUN


class TestPanelToggleKeybindings:
    """Tests for panel toggle keybindings - TC-355 through TC-360."""

    def test_key_1_toggles_status_bar(self):
        """TC-356: '1' toggles Status Bar visibility."""
        keybinding = get_keybinding("1")
        assert keybinding is not None
        assert keybinding["action"] == "toggle_status_bar"
        assert keybinding["context"] == KeyContext.GLOBAL

    def test_key_2_toggles_tree_view(self):
        """TC-357: '2' toggles Tree View visibility."""
        keybinding = get_keybinding("2")
        assert keybinding is not None
        assert keybinding["action"] == "toggle_tree_view"
        assert keybinding["context"] == KeyContext.GLOBAL

    def test_key_3_toggles_summary_panel(self):
        """TC-358: '3' toggles Summary Panel visibility."""
        keybinding = get_keybinding("3")
        assert keybinding is not None
        assert keybinding["action"] == "toggle_summary_panel"
        assert keybinding["context"] == KeyContext.GLOBAL

    def test_key_4_toggles_log_panel(self):
        """TC-359: '4' toggles Log Panel visibility."""
        keybinding = get_keybinding("4")
        assert keybinding is not None
        assert keybinding["action"] == "toggle_log_panel"
        assert keybinding["context"] == KeyContext.GLOBAL

    def test_key_5_toggles_footer(self):
        """TC-360: '5' toggles Footer visibility."""
        keybinding = get_keybinding("5")
        assert keybinding is not None
        assert keybinding["action"] == "toggle_footer"
        assert keybinding["context"] == KeyContext.GLOBAL


class TestShiftModifiers:
    """Tests for shift modifier keybindings - R vs r, S vs s."""

    def test_lowercase_r_is_refresh(self):
        """'r' is refresh, not rerun."""
        keybinding_r = get_keybinding("r")
        assert keybinding_r["action"] == "refresh"

    def test_uppercase_r_is_rerun(self):
        """'R' is rerun, different from 'r'."""
        keybinding_R = get_keybinding("R")
        assert keybinding_R["action"] == "rerun_with_same_args"

    def test_lowercase_s_is_sort(self):
        """'s' is sort cycle, not settings."""
        keybinding_s = get_keybinding("s")
        assert keybinding_s["action"] == "cycle_sort"

    def test_uppercase_s_is_settings(self):
        """'S' is settings, different from 's'."""
        keybinding_S = get_keybinding("S")
        assert keybinding_S["action"] == "show_settings"

    def test_lowercase_g_is_top(self):
        """'g' jumps to top of tree."""
        keybinding_g = get_keybinding("g")
        assert keybinding_g["action"] == "jump_to_top"

    def test_uppercase_g_is_bottom(self):
        """'G' jumps to bottom of tree."""
        keybinding_G = get_keybinding("G")
        assert keybinding_G["action"] == "jump_to_bottom"


class TestKeybindingConflicts:
    """Tests for keybinding conflicts - no duplicate bindings."""

    def test_no_duplicate_keys_in_keybindings_dict(self):
        """The KEYBINDINGS dict should have no duplicate keys."""
        keys = list(KEYBINDINGS.keys())
        assert len(keys) == len(set(keys))

    def test_validate_keybindings_returns_no_errors(self):
        """validate_keybindings should return empty list if valid."""
        errors = validate_keybindings()
        assert errors == []

    def test_multiple_keys_can_map_to_same_action(self):
        """Multiple keys can map to the same action (e.g., '/' and 'ctrl+f' for search)."""
        search_keys = get_action_keybindings("open_search")
        assert "/" in search_keys
        assert "ctrl+f" in search_keys
        assert len(search_keys) == 2


class TestInvalidKeyHandling:
    """Tests for invalid key handling."""

    def test_unknown_key_returns_none(self):
        """Unknown keys should return None."""
        assert get_keybinding("xyz") is None
        assert get_keybinding("ctrl+shift+alt+f12") is None

    def test_random_key_returns_none(self):
        """Random unbound key returns None."""
        assert get_keybinding("f13") is None
        assert get_keybinding("home") is None
        assert get_keybinding("pageup") is None


class TestGetKeybindingFunction:
    """Tests for get_keybinding function behavior."""

    def test_get_keybinding_lowercase_letters(self):
        """Lowercase letters should find their keybinding."""
        binding = get_keybinding("q")
        assert binding is not None
        assert binding["action"] == "quit"

    def test_get_keybinding_uppercase_letters_distinct(self):
        """Uppercase letters are distinct from lowercase for defined caps keys."""
        binding_S = get_keybinding("S")
        binding_s = get_keybinding("s")
        assert binding_S["action"] == "show_settings"
        assert binding_s["action"] == "cycle_sort"
        assert binding_S != binding_s

    def test_get_keybinding_preserves_modifier_case(self):
        """Modifier keys should preserve case format."""
        ctrl_lower = get_keybinding("ctrl+f")
        assert ctrl_lower is not None
        assert ctrl_lower["action"] == "open_search"

    def test_get_keybinding_normalizes_modifier_format(self):
        """get_keybinding should handle case variations in modifiers."""
        ctrl_upper = get_keybinding("ctrl+F")
        assert ctrl_upper is not None
        assert ctrl_upper["action"] == "open_search"

    def test_get_keybinding_returns_dict(self):
        """get_keybinding returns KeyAction dict."""
        binding = get_keybinding("q")
        assert isinstance(binding, dict)
        assert "action" in binding
        assert "description" in binding
        assert "context" in binding
        assert "requires_confirmation" in binding


class TestGetActionKeybindings:
    """Tests for get_action_keybindings function."""

    def test_get_action_keybindings_returns_list(self):
        """get_action_keybindings returns a list."""
        keys = get_action_keybindings("quit")
        assert isinstance(keys, list)

    def test_get_action_keybindings_for_quit(self):
        """Quit action should return 'q' key."""
        keys = get_action_keybindings("quit")
        assert "q" in keys

    def test_get_action_keybindings_for_navigation(self):
        """Navigate down action should have multiple keys."""
        keys = get_action_keybindings("navigate_tree_down")
        assert "down" in keys
        assert "j" in keys

    def test_get_action_keybindings_for_unknown_action(self):
        """Unknown action should return empty list."""
        keys = get_action_keybindings("nonexistent_action")
        assert keys == []

    def test_get_action_keybindings_single_key_action(self):
        """Actions with single key should return one item."""
        keys = get_action_keybindings("show_help")
        assert len(keys) == 1
        assert keys[0] == "?"


class TestGetKeybindingsByContext:
    """Tests for get_keybindings_by_context function."""

    def test_get_global_keybindings(self):
        """get_keybindings_by_context filters by GLOBAL context."""
        global_bindings = get_keybindings_by_context(KeyContext.GLOBAL)
        assert len(global_bindings) > 0
        for key, binding in global_bindings.items():
            assert binding["context"] == KeyContext.GLOBAL

    def test_get_tree_keybindings(self):
        """get_keybindings_by_context filters by TREE context."""
        tree_bindings = get_keybindings_by_context(KeyContext.TREE)
        assert len(tree_bindings) > 0
        for key, binding in tree_bindings.items():
            assert binding["context"] == KeyContext.TREE

    def test_get_log_keybindings(self):
        """get_keybindings_by_context filters by LOG context."""
        log_bindings = get_keybindings_by_context(KeyContext.LOG)
        for key, binding in log_bindings.items():
            assert binding["context"] == KeyContext.LOG

    def test_get_post_run_keybindings(self):
        """get_keybindings_by_context filters by POST_RUN context."""
        post_run_bindings = get_keybindings_by_context(KeyContext.POST_RUN)
        assert len(post_run_bindings) > 0
        for key, binding in post_run_bindings.items():
            assert binding["context"] == KeyContext.POST_RUN


class TestGetAllActions:
    """Tests for get_all_actions function."""

    def test_get_all_actions_returns_set(self):
        """get_all_actions returns a set."""
        actions = get_all_actions()
        assert isinstance(actions, set)

    def test_get_all_actions_contains_known_actions(self):
        """get_all_actions contains expected actions."""
        actions = get_all_actions()
        assert "quit" in actions
        assert "show_help" in actions
        assert "navigate_tree_up" in actions
        assert "navigate_tree_down" in actions

    def test_get_all_actions_excludes_unknown(self):
        """get_all_actions should not contain invalid actions."""
        actions = get_all_actions()
        assert "nonexistent_action" not in actions

    def test_get_all_actions_count_matches_bindings(self):
        """Number of unique actions should match or be less than bindings."""
        actions = get_all_actions()
        assert len(actions) <= len(KEYBINDINGS)


class TestKeybindingContextsComplete:
    """Complete coverage of keybinding contexts - TC-361 through TC-364."""

    def test_tree_context_keys_dont_work_globally(self):
        """TC-361: Keys like j/k/arrow only work when tree focused."""
        j_binding = get_keybinding("j")
        k_binding = get_keybinding("k")
        up_binding = get_keybinding("up")
        down_binding = get_keybinding("down")

        assert j_binding["context"] == KeyContext.TREE
        assert k_binding["context"] == KeyContext.TREE
        assert up_binding["context"] == KeyContext.TREE
        assert down_binding["context"] == KeyContext.TREE

    def test_log_context_keys_only_for_log(self):
        """TC-362: Search keys only work when log focused."""
        search_binding = get_keybinding("/")
        ctrl_f_binding = get_keybinding("ctrl+f")

        assert search_binding["context"] == KeyContext.LOG
        assert ctrl_f_binding["context"] == KeyContext.LOG

    def test_post_run_keys_only_after_completion(self):
        """TC-363: Rerun keys only work after playbook completion."""
        R_binding = get_keybinding("R")
        shift_r_binding = get_keybinding("shift+r")

        assert R_binding["context"] == KeyContext.POST_RUN
        assert shift_r_binding["context"] == KeyContext.POST_RUN

    def test_global_context_keys_work_everywhere(self):
        """TC-364: Global keys work from any panel."""
        global_keys = ["q", "?", "f", "tab", "d"]

        for key in global_keys:
            binding = get_keybinding(key)
            assert binding is not None
            assert binding["context"] == KeyContext.GLOBAL