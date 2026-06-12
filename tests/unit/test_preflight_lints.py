"""Unit tests for the bypass-host-loop prompt detector (Phase 1.2)."""

from __future__ import annotations

from ansible_aom.core.preflight_lints import detect_bypass_host_loop_prompts


def _play(tasks, *, serial=None, name="Deploy"):
    play = {"name": name, "hosts": "all", "tasks": tasks}
    if serial is not None:
        play["serial"] = serial
    return play


PAUSE_TASK = {
    "name": "Confirm deployment",
    "ansible.builtin.pause": {"prompt": "Deploy to {{ inventory_hostname }}? Enter to go"},
}


def test_warns_when_host_prompt_in_non_serial_multihost_play():
    warnings = detect_bypass_host_loop_prompts([(_play([PAUSE_TASK]), 3)])
    assert len(warnings) == 1
    assert "Confirm deployment" in warnings[0]
    assert "3" in warnings[0]
    assert "serial" in warnings[0]


def test_no_warning_when_single_host():
    assert detect_bypass_host_loop_prompts([(_play([PAUSE_TASK]), 1)]) == []


def test_no_warning_when_serial_is_one():
    assert detect_bypass_host_loop_prompts([(_play([PAUSE_TASK], serial=1), 3)]) == []


def test_warns_when_serial_greater_than_one():
    # serial: 5 still bypasses within the batch -> still collapses.
    assert len(detect_bypass_host_loop_prompts([(_play([PAUSE_TASK], serial=5), 10)])) == 1


def test_no_warning_when_serial_list_all_ones():
    assert detect_bypass_host_loop_prompts([(_play([PAUSE_TASK], serial=[1, 1]), 3)]) == []


def test_warns_when_serial_list_has_larger_batch():
    # serial: [1, 5] -> the size-5 batch still collapses, so warn.
    assert len(detect_bypass_host_loop_prompts([(_play([PAUSE_TASK], serial=[1, 5]), 6)])) == 1


def test_no_warning_when_prompt_has_no_host_var():
    task = {"name": "Pause", "ansible.builtin.pause": {"prompt": "Continue? Enter to go"}}
    assert detect_bypass_host_loop_prompts([(_play([task]), 3)]) == []


def test_no_warning_for_non_pause_task():
    task = {"name": "Debug", "ansible.builtin.debug": {"msg": "{{ inventory_hostname }}"}}
    assert detect_bypass_host_loop_prompts([(_play([task]), 3)]) == []


def test_detects_bare_pause_key_and_action_form():
    bare = {"name": "P1", "pause": {"prompt": "{{ inventory_hostname }}: ok? "}}
    action = {
        "name": "P2",
        "action": {"module": "pause", "prompt": "{{ ansible_host }}: ok? "},
    }
    out = detect_bypass_host_loop_prompts([(_play([bare]), 2), (_play([action]), 2)])
    assert len(out) == 2


def test_prompt_as_plain_string_value_is_handled():
    # pause with no args at all (prompt is None) must not crash.
    task = {"name": "P", "ansible.builtin.pause": None}
    assert detect_bypass_host_loop_prompts([(_play([task]), 3)]) == []
