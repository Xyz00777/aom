"""Answered prompts stay consumed across blank PTY input echoes."""

from unittest.mock import MagicMock

import pytest

from ansible_aom.ansible.runner import _drive, _NullSink
from ansible_aom.core.models import RunState
from ansible_aom.core.parser import PtyStreamParser


@pytest.mark.parametrize("echo", ["", "\r"])
@pytest.mark.parametrize("prompt_count", [1, 2])
def test_blank_echo_does_not_rearm_answered_prompt(echo: str, prompt_count: int) -> None:
    # Given: each prompt is followed by an empty answer echo and another quiet
    # window, before the child exits or emits a genuine second prompt.
    child = MagicMock()
    child.buffer = ""
    child.pid = None
    child.exitstatus = 0
    child.isalive.return_value = True
    renderer = MagicMock()
    renderer.handle_interactive_prompt.return_value = ""
    responses = iter(
        [
            (0, '{"_event": "v2_playbook_on_start"}'),
            *[
                response
                for _ in range(prompt_count)
                for response in [(0, "Continue?"), (2, ""), (0, echo), (2, "")]
            ],
            (1, ""),
        ]
    )

    def expect(patterns: list[str | type[BaseException]], timeout: float) -> int:
        idx, before = next(responses)
        child.before = before
        child.after = "\r\n" if idx == 0 else ""
        return idx

    child.expect.side_effect = expect

    # When: the real pump consumes the scripted PTY boundaries.
    exit_code = _drive(
        child, PtyStreamParser(), RunState(playbook="test.yml"), renderer, 0.15, _NullSink()
    )

    # Then: one answer per actual prompt, even when the child stays quiet after
    # echoing Enter; an identical subsequent prompt still receives its answer.
    assert exit_code == 0
    assert renderer.handle_interactive_prompt.call_count == prompt_count
    assert child.sendline.call_count == prompt_count
