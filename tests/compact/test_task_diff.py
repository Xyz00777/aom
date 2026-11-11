"""Changed task/item results show captured diffs once, with their owning result."""

from unittest.mock import MagicMock

import pytest

from ansible_aom.compact.renderer import _CYAN, _GREEN, _RED, _RESET, _YELLOW, CompactRenderer


def _renderer(*, colorize=False, hide_states=()) -> CompactRenderer:
    renderer = CompactRenderer(is_tty=False, hide_states=list(hide_states))
    # Replay starts the renderer with empty args, even when the recorded run used --diff.
    renderer.start("test.yml", [])
    renderer._colorize = colorize
    renderer._display = MagicMock()
    renderer.update_state(
        {
            "_event": "v2_playbook_on_task_start",
            "play": {"id": "p1"},
            "task": {"id": "t1", "name": "Edit config"},
        }
    )
    renderer._display.reset_mock()
    return renderer


def _result(old="old", new="new", **extra):
    return {"changed": True, "diff": {"before": old + "\n", "after": new + "\n"}, **extra}


def _event(hosts, name="v2_runner_on_ok"):
    return {"_event": name, "play": {"id": "p1"}, "task": {"id": "t1"}, "hosts": hosts}


def _block(old="old", new="new"):
    return "\n".join(
        ["    --- before", "    +++ after", "    @@ -1 +1 @@", f"    -{old}", f"    +{new}"]
    )


def _logged(renderer):
    return [call.args[0] for call in renderer._display.print_log.call_args_list]


def test_multi_host_diffs_follow_each_result_in_one_event_batch_with_empty_startup_args():
    renderer = _renderer()
    renderer.update_state(
        _event({"web": _result("web-old", "web-new"), "db": _result("db-old", "db-new")})
    )
    assert _logged(renderer) == [
        "changed: [web]\n"
        + _block("web-old", "web-new")
        + "\nchanged: [db]\n"
        + _block("db-old", "db-new")
    ]


def test_streamed_loop_diffs_are_not_repeated_by_the_aggregate():
    renderer = _renderer()
    apple = _result("apple-old", "apple-new", item="apple")
    pear = _result("pear-old", "pear-new", item="pear")
    renderer.update_state(_event({"web": apple}, "v2_runner_item_on_ok"))
    renderer.update_state(_event({"web": pear}, "v2_runner_item_on_ok"))
    renderer.update_state(_event({"web": {"changed": True, "results": [apple, pear]}}))
    assert _logged(renderer) == [
        "changed: [web] => (item=apple)\n" + _block("apple-old", "apple-new"),
        "changed: [web] => (item=pear)\n" + _block("pear-old", "pear-new"),
    ]


def test_aggregate_only_loop_diffs_follow_their_own_item_once():
    renderer = _renderer()
    renderer.update_state(
        _event(
            {
                "web": {
                    "changed": True,
                    "results": [
                        _result("apple-old", "apple-new", item="apple"),
                        _result("pear-old", "pear-new", item="pear"),
                    ],
                }
            }
        )
    )
    assert _logged(renderer) == [
        "changed: [web] => (item=apple)\n"
        + _block("apple-old", "apple-new")
        + "\nchanged: [web] => (item=pear)\n"
        + _block("pear-old", "pear-new")
    ]


@pytest.mark.parametrize("name", ["v2_runner_on_ok", "v2_runner_item_on_ok"])
def test_hidden_changed_results_also_hide_their_diff(name):
    renderer = _renderer(hide_states=["changed"])
    renderer.update_state(_event({"web": _result(item="apple")}, name))
    assert _logged(renderer) == []


@pytest.mark.parametrize("guard", [{"_ansible_no_log": True}, {"censored": "hidden"}])
@pytest.mark.parametrize("loop", [False, True])
def test_parent_censoring_suppresses_diffs_including_nested_loop_fallback(guard, loop):
    renderer = _renderer()
    result = _result(**guard)
    if loop:
        result["results"] = [_result("secret-old", "secret-new", item="apple")]
    renderer.update_state(_event({"web": result}))
    assert _logged(renderer) == ["changed: [web] => (item=apple)" if loop else "changed: [web]"]


@pytest.mark.parametrize("guard", [{"_ansible_no_log": True}, {"censored": "hidden"}])
@pytest.mark.parametrize("streamed", [False, True])
def test_item_censoring_suppresses_diff_in_streamed_and_aggregate_paths(guard, streamed):
    renderer = _renderer()
    item = _result(item="apple", **guard)
    if streamed:
        renderer.update_state(_event({"web": item}, "v2_runner_item_on_ok"))
    else:
        renderer.update_state(_event({"web": {"changed": True, "results": [item]}}))
    assert _logged(renderer) == ["changed: [web] => (item=apple)"]


def test_diff_colors_match_existing_removed_added_and_hunk_colors():
    renderer = _renderer(colorize=True)
    renderer.update_state(_event({"web": _result()}))
    assert _logged(renderer) == [
        "\n".join(
            [
                f"{_YELLOW}changed: [web]{_RESET}",
                f"    {_RED}--- before{_RESET}",
                f"    {_GREEN}+++ after{_RESET}",
                f"    {_CYAN}@@ -1 +1 @@{_RESET}",
                f"    {_RED}-old{_RESET}",
                f"    {_GREEN}+new{_RESET}",
            ]
        )
    ]


def test_unchanged_result_with_diff_stays_one_plain_result_line():
    renderer = _renderer()
    renderer.update_state(_event({"web": _result(changed=False)}))
    assert _logged(renderer) == ["ok: [web]"]


def test_failed_changed_item_keeps_diff_and_existing_failure_message():
    renderer = _renderer()
    renderer.update_state(
        _event({"web": _result(item="apple", msg="reload failed")}, "v2_runner_item_on_failed")
    )
    assert _logged(renderer) == ["failed: [web] => (item=apple) => reload failed\n" + _block()]


def test_failed_changed_host_keeps_diff_and_existing_failure_message():
    renderer = _renderer()
    renderer.update_state(_event({"web": _result(msg="reload failed")}, "v2_runner_on_failed"))
    assert _logged(renderer) == ["fatal: [web]: FAILED! => reload failed\n" + _block()]


@pytest.mark.parametrize("guard", [{"_ansible_no_log": True}, {"censored": "hidden"}])
def test_failed_loop_parent_censoring_suppresses_nested_item_diff(guard):
    renderer = _renderer()
    renderer.update_state(
        _event(
            {
                "web": {
                    "changed": True,
                    "results": [_result(item="apple", failed=True)],
                    **guard,
                }
            },
            "v2_runner_on_failed",
        )
    )
    assert _logged(renderer) == ["failed: [web] => (item=apple)"]
