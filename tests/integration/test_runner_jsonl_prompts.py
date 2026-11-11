"""Real PTY regressions for JSONL framing before password detection."""

from __future__ import annotations

import json
import sys
from unittest.mock import MagicMock

import pexpect
import pytest

from ansible_aom.ansible.runner import _SEARCH_WINDOW_BYTES, _drive, _NullSink
from ansible_aom.core.models import RunState
from ansible_aom.core.parser import PtyStreamParser


@pytest.mark.parametrize("padding", [0, 700, 5000])
@pytest.mark.parametrize("fragmented", [False, True])
@pytest.mark.parametrize("trailing_newline", [False, True])
def test_jsonl_password_text_is_parsed_without_requesting_input(
    padding: int, fragmented: bool, trailing_newline: bool
) -> None:
    # Given sudo -V output inside a JSON event, followed by normal task progress.
    events = [
        {"_event": "v2_playbook_on_start"},
        {
            "_event": "v2_runner_on_ok",
            "hosts": {
                "ipa1": {
                    "stdout": "x" * padding + "Default password prompt: [sudo] password for %p: ",
                }
            },
            "task": {"id": "sudo", "name": "Detect sudo rlimit_core support"},
        },
        {"_event": "v2_playbook_on_stats", "stats": {}},
    ]
    if not trailing_newline:
        events.pop()
    payload = "".join(json.dumps(event) + "\n" for event in events)
    if not trailing_newline:
        payload = payload.rstrip("\n")
    split = payload.index("[sudo]") + len("[sudo] password for %p: ")
    code = f"import sys, time; sys.stdout.write({payload!r}); sys.stdout.flush()"
    if fragmented:
        code = (
            f"import sys, time; sys.stdout.write({payload[:split]!r}); sys.stdout.flush(); "
            f"time.sleep(0.8); sys.stdout.write({payload[split:]!r}); sys.stdout.flush()"
        )
    renderer = MagicMock()
    renderer.handle_password_prompt.return_value = ""

    # When the real PTY delivers the structured stream to the runner.
    with pexpect.spawn(
        sys.executable,
        ["-c", code],
        encoding="utf-8",
        searchwindowsize=_SEARCH_WINDOW_BYTES,
    ) as child:
        exit_code = _drive(
            child, PtyStreamParser(), RunState(playbook="test.yml"), renderer, 0.1, _NullSink()
        )

    # Then every event is intact and no secret/input is requested or logged.
    assert exit_code == 0
    assert [call.args[0] for call in renderer.update_state.call_args_list] == events
    renderer.handle_password_prompt.assert_not_called()
    renderer.handle_interactive_prompt.assert_not_called()
    renderer.print_log.assert_not_called()


@pytest.mark.parametrize("padding", [0, 6000])
def test_real_password_prompt_still_works_after_jsonl_password_text(padding: int) -> None:
    events = [
        {"_event": "v2_playbook_on_start"},
        {"_event": "aom_test_event", "stdout": "Vault password: SSH password: " + "x" * padding},
    ]
    payload = "".join(json.dumps(event) + "\n" for event in events)
    code = (
        "import sys, signal; signal.alarm(3); "
        f"sys.stdout.write({payload!r} + 'BECOME password: '); "
        "sys.stdout.flush(); answer = sys.stdin.readline().strip(); "
        "sys.exit(0 if answer == 'test-secret' else 9)"
    )
    renderer = MagicMock()
    renderer.handle_password_prompt.return_value = "test-secret"
    with pexpect.spawn(
        sys.executable,
        ["-c", code],
        encoding="utf-8",
        searchwindowsize=_SEARCH_WINDOW_BYTES,
        echo=False,
    ) as child:
        exit_code = _drive(
            child, PtyStreamParser(), RunState(playbook="test.yml"), renderer, 0.1, _NullSink()
        )

    assert exit_code == 0
    assert [call.args[0] for call in renderer.update_state.call_args_list] == events
    renderer.handle_password_prompt.assert_called_once_with("BECOME password: ")


def test_backlogged_events_are_all_parsed(monkeypatch: pytest.MonkeyPatch) -> None:
    from ansible_aom.ansible.runner import run_playbook
    from ansible_aom.core.parser import PreParseResult

    # Given many short events queued in one subprocess write.
    events = [{"_event": "v2_playbook_on_start"}]
    events.extend({"_event": "aom_test_event", "sequence": n} for n in range(40))
    events.append({"_event": "v2_playbook_on_stats", "stats": {}})
    payload = "".join(json.dumps(event) + "\n" for event in events)
    monkeypatch.setattr(
        "ansible_aom.ansible.runner._build_command",
        lambda *_: (sys.executable, ["-c", f"import os; os.write(1, {payload.encode()!r})"]),
    )
    monkeypatch.setattr(
        "ansible_aom.ansible.runner.run_preflight",
        lambda **_: PreParseResult(plays=[], play_hosts=[]),
    )
    renderer = MagicMock()

    # When the production spawn configuration reads that backlog.
    exit_code = run_playbook("test.yml", [], renderer, record=False)

    # Then no earlier newline or event is skipped by the bounded search window.
    assert exit_code == 0
    assert [call.args[0] for call in renderer.update_state.call_args_list] == events
