"""Unit tests for core/log_filter.py --hide-state helper functions."""

from __future__ import annotations

from ansible_aom.core.log_filter import (
    VALID_STATES,
    normalize_hide_states,
    should_hide_event,
    should_hide_host_result,
)


class TestNormalizeHideStates:
    """Tests for normalize_hide_states — input validation and normalisation."""

    def test_empty_input(self) -> None:
        """Empty iterable returns empty frozenset and empty unknown list."""
        valid, unknown = normalize_hide_states([])
        assert valid == frozenset()
        assert unknown == []

    def test_single_value(self) -> None:
        """Single known value returns frozenset with that value."""
        valid, unknown = normalize_hide_states(["ok"])
        assert valid == frozenset({"ok"})
        assert unknown == []

    def test_case_insensitive(self) -> None:
        """Mixed-case input is lowercased and matched against VALID_STATES."""
        valid, unknown = normalize_hide_states(["OK", "Skipped"])
        assert valid == frozenset({"ok", "skipped"})
        assert unknown == []

    def test_deduplicates(self) -> None:
        """Duplicate values produce a single entry in the frozenset."""
        valid, unknown = normalize_hide_states(["ok", "ok", "ok"])
        assert valid == frozenset({"ok"})
        assert unknown == []

    def test_all_valid_states_accepted(self) -> None:
        """Every entry in VALID_STATES is accepted individually."""
        for state in sorted(VALID_STATES):
            valid, unknown = normalize_hide_states([state])
            assert valid == frozenset({state}), f"state {state!r} not accepted"
            assert unknown == []

    def test_unknown_state_returns_in_unknown_list(self) -> None:
        """A value not in VALID_STATES appears in the unknown list."""
        valid, unknown = normalize_hide_states(["foo"])
        assert valid == frozenset()
        assert unknown == ["foo"]

    def test_mixed_known_and_unknown(self) -> None:
        """Known values go to the frozenset; unknown values go to the list."""
        valid, unknown = normalize_hide_states(["ok", "foo", "skipped", "bar"])
        assert valid == frozenset({"ok", "skipped"})
        assert unknown == ["foo", "bar"]

    def test_frozenset_return_type(self) -> None:
        """The first return value is a frozenset, not a plain set."""
        valid, _unknown = normalize_hide_states(["ok"])
        assert isinstance(valid, frozenset)

    def test_unknown_list_preserves_order(self) -> None:
        """Unknown values appear in the order they were encountered."""
        _valid, unknown = normalize_hide_states(["z", "a", "m"])
        assert unknown == ["z", "a", "m"]

    def test_iterable_not_just_list(self) -> None:
        """Accepts any iterable, e.g. a generator."""
        valid, unknown = normalize_hide_states(x for x in ["ok", "FAILED"])
        assert valid == frozenset({"ok", "failed"})
        assert unknown == []

    def test_whitespace_around_tokens_not_stripped(self) -> None:
        """Tokens with surrounding whitespace are treated as unknown.

        ``normalize_hide_states`` only lowercases; it does NOT strip
        whitespace. Whitespace stripping is the caller's job (the CLI's
        ``_comma_sep_state`` does it before this helper is called).
        This test pins the current behaviour so any future change to
        add stripping here is a conscious decision."""
        valid, unknown = normalize_hide_states([" ok ", "  skipped  "])
        assert valid == frozenset()
        assert unknown == [" ok ", "  skipped  "]


class TestShouldHideEvent:
    """Tests for should_hide_event — JSONL event type → hide decision."""

    # --- v2_runner_on_ok (covers both ok and changed) ---

    def test_v2_runner_on_ok_true_when_ok_hidden(self) -> None:
        """Hiding 'ok' suppresses v2_runner_on_ok events."""
        assert should_hide_event("v2_runner_on_ok", frozenset({"ok"})) is True

    def test_v2_runner_on_ok_true_when_changed_hidden(self) -> None:
        """Hiding 'changed' also suppresses v2_runner_on_ok (same event branch)."""
        assert should_hide_event("v2_runner_on_ok", frozenset({"changed"})) is True

    def test_v2_runner_on_ok_false_when_not_hidden(self) -> None:
        """Empty hide set never suppresses."""
        assert should_hide_event("v2_runner_on_ok", frozenset()) is False

    def test_v2_runner_on_ok_false_when_only_failed_hidden(self) -> None:
        """Hiding only 'failed' does not affect v2_runner_on_ok."""
        assert should_hide_event("v2_runner_on_ok", frozenset({"failed"})) is False

    # --- v2_runner_on_failed ---

    def test_v2_runner_on_failed_true(self) -> None:
        assert should_hide_event("v2_runner_on_failed", frozenset({"failed"})) is True

    def test_v2_runner_on_failed_false_when_not_hidden(self) -> None:
        assert should_hide_event("v2_runner_on_failed", frozenset()) is False

    # --- v2_runner_on_unreachable ---

    def test_v2_runner_on_unreachable_true(self) -> None:
        assert should_hide_event("v2_runner_on_unreachable", frozenset({"unreachable"})) is True

    def test_v2_runner_on_unreachable_false_when_not_hidden(self) -> None:
        assert should_hide_event("v2_runner_on_unreachable", frozenset()) is False

    # --- v2_runner_on_skipped ---

    def test_v2_runner_on_skipped_true(self) -> None:
        assert should_hide_event("v2_runner_on_skipped", frozenset({"skipped"})) is True

    def test_v2_runner_on_skipped_false_when_not_hidden(self) -> None:
        assert should_hide_event("v2_runner_on_skipped", frozenset()) is False

    # --- v2_runner_item_on_* ---

    def test_v2_runner_item_on_ok_true(self) -> None:
        assert should_hide_event("v2_runner_item_on_ok", frozenset({"ok"})) is True

    def test_v2_runner_item_on_ok_true_when_changed_hidden(self) -> None:
        """v2_runner_item_on_ok also covers changed results."""
        assert should_hide_event("v2_runner_item_on_ok", frozenset({"changed"})) is True

    def test_v2_runner_item_on_failed_true(self) -> None:
        assert should_hide_event("v2_runner_item_on_failed", frozenset({"failed"})) is True

    def test_v2_runner_item_on_skipped_true(self) -> None:
        assert should_hide_event("v2_runner_item_on_skipped", frozenset({"skipped"})) is True

    # --- Non-runner events: never hidden ---

    def test_v2_playbook_on_task_start_never_hidden(self) -> None:
        assert should_hide_event("v2_playbook_on_task_start", frozenset({"ok"})) is False

    def test_v2_playbook_on_play_start_never_hidden(self) -> None:
        assert (
            should_hide_event("v2_playbook_on_play_start", frozenset({"ok", "skipped", "failed"}))
            is False
        )

    def test_v2_playbook_on_stats_never_hidden(self) -> None:
        assert should_hide_event("v2_playbook_on_stats", frozenset({"ok"})) is False

    def test_v2_playbook_on_start_never_hidden(self) -> None:
        assert should_hide_event("v2_playbook_on_start", frozenset({"ok"})) is False

    def test_v2_playbook_on_handler_task_start_never_hidden(self) -> None:
        assert should_hide_event("v2_playbook_on_handler_task_start", frozenset({"ok"})) is False

    def test_v2_runner_on_start_never_hidden(self) -> None:
        """v2_runner_on_start is a lifecycle event, not a result event."""
        assert should_hide_event("v2_runner_on_start", frozenset({"ok"})) is False

    # --- Unknown event types: never hidden ---

    def test_unknown_event_type_never_hidden(self) -> None:
        assert should_hide_event("v2_unknown_event", frozenset({"ok"})) is False

    def test_empty_event_type_never_hidden(self) -> None:
        """Empty string event type is never hidden."""
        assert should_hide_event("", frozenset({"ok", "failed"})) is False

    # --- Multiple hide states ---

    def test_multiple_hide_states_match_any(self) -> None:
        """If any hide state matches, the event is hidden."""
        assert (
            should_hide_event("v2_runner_on_failed", frozenset({"ok", "failed", "skipped"})) is True
        )

    def test_multiple_hide_states_no_match(self) -> None:
        """If no hide state matches, the event is not hidden."""
        assert (
            should_hide_event("v2_runner_on_failed", frozenset({"ok", "skipped", "unreachable"}))
            is False
        )


class TestShouldHideHostResult:
    """Tests for should_hide_host_result — per-host hide decision."""

    # --- v2_runner_on_ok / v2_runner_item_on_ok: per-host changed field ---

    def test_ok_result_hidden_when_ok_in_hide_states(self) -> None:
        assert should_hide_host_result({"changed": False}, "v2_runner_on_ok", frozenset({"ok"})) is True

    def test_ok_result_visible_when_only_changed_in_hide_states(self) -> None:
        assert should_hide_host_result({"changed": False}, "v2_runner_on_ok", frozenset({"changed"})) is False

    def test_changed_result_hidden_when_changed_in_hide_states(self) -> None:
        assert should_hide_host_result({"changed": True}, "v2_runner_on_ok", frozenset({"changed"})) is True

    def test_changed_result_visible_when_only_ok_in_hide_states(self) -> None:
        assert should_hide_host_result({"changed": True}, "v2_runner_on_ok", frozenset({"ok"})) is False

    def test_ok_result_hidden_when_both_ok_and_changed_hidden(self) -> None:
        assert (
            should_hide_host_result({"changed": False}, "v2_runner_on_ok", frozenset({"ok", "changed"}))
            is True
        )

    def test_changed_result_hidden_when_both_ok_and_changed_hidden(self) -> None:
        assert (
            should_hide_host_result({"changed": True}, "v2_runner_on_ok", frozenset({"ok", "changed"}))
            is True
        )

    def test_ok_result_visible_with_empty_hide_states(self) -> None:
        assert should_hide_host_result({"changed": False}, "v2_runner_on_ok", frozenset()) is False

    def test_changed_result_visible_with_empty_hide_states(self) -> None:
        assert should_hide_host_result({"changed": True}, "v2_runner_on_ok", frozenset()) is False

    def test_ok_result_visible_when_only_failed_in_hide_states(self) -> None:
        assert should_hide_host_result({"changed": False}, "v2_runner_on_ok", frozenset({"failed"})) is False

    def test_missing_changed_defaults_to_false(self) -> None:
        """Result dict without 'changed' key is treated as ok (not changed)."""
        assert should_hide_host_result({}, "v2_runner_on_ok", frozenset({"ok"})) is True

    def test_missing_changed_visible_when_only_changed_hidden(self) -> None:
        assert should_hide_host_result({}, "v2_runner_on_ok", frozenset({"changed"})) is False

    # --- v2_runner_item_on_ok: same per-host logic ---

    def test_item_ok_hidden_when_ok_in_hide_states(self) -> None:
        assert (
            should_hide_host_result({"changed": False}, "v2_runner_item_on_ok", frozenset({"ok"})) is True
        )

    def test_item_changed_visible_when_only_ok_in_hide_states(self) -> None:
        assert (
            should_hide_host_result({"changed": True}, "v2_runner_item_on_ok", frozenset({"ok"})) is False
        )

    def test_item_changed_hidden_when_changed_in_hide_states(self) -> None:
        assert (
            should_hide_host_result({"changed": True}, "v2_runner_item_on_ok", frozenset({"changed"})) is True
        )

    # --- v2_runner_on_failed / v2_runner_item_on_failed ---

    def test_failed_hidden_when_failed_in_hide_states(self) -> None:
        assert should_hide_host_result({}, "v2_runner_on_failed", frozenset({"failed"})) is True

    def test_failed_visible_with_empty_hide_states(self) -> None:
        assert should_hide_host_result({}, "v2_runner_on_failed", frozenset()) is False

    def test_item_failed_hidden_when_failed_in_hide_states(self) -> None:
        assert should_hide_host_result({}, "v2_runner_item_on_failed", frozenset({"failed"})) is True

    # --- v2_runner_on_unreachable ---

    def test_unreachable_hidden_when_unreachable_in_hide_states(self) -> None:
        assert should_hide_host_result({}, "v2_runner_on_unreachable", frozenset({"unreachable"})) is True

    def test_unreachable_visible_with_empty_hide_states(self) -> None:
        assert should_hide_host_result({}, "v2_runner_on_unreachable", frozenset()) is False

    # --- v2_runner_on_skipped / v2_runner_item_on_skipped ---

    def test_skipped_hidden_when_skipped_in_hide_states(self) -> None:
        assert should_hide_host_result({}, "v2_runner_on_skipped", frozenset({"skipped"})) is True

    def test_skipped_visible_with_empty_hide_states(self) -> None:
        assert should_hide_host_result({}, "v2_runner_on_skipped", frozenset()) is False

    def test_item_skipped_hidden_when_skipped_in_hide_states(self) -> None:
        assert should_hide_host_result({}, "v2_runner_item_on_skipped", frozenset({"skipped"})) is True

    # --- Unknown event types: never hidden ---

    def test_unknown_event_type_never_hidden(self) -> None:
        assert should_hide_host_result({}, "v2_playbook_on_task_start", frozenset({"ok"})) is False

    def test_empty_event_type_never_hidden(self) -> None:
        assert should_hide_host_result({}, "", frozenset({"ok", "failed"})) is False
