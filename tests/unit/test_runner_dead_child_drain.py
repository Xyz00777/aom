"""A dead process can leave both buffered lines and unread PTY output.

Stopping after one more newline lost the tail of fast playbooks whenever
that newline came from pexpect's buffer instead of reading the PTY again.
The complete recorded stream must survive this scheduling boundary.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pexpect
import pytest

from ansible_aom.ansible import runner


class _DeadChildWithUnreadTail:
    def __init__(self, events: list[dict], terminal: str) -> None:
        self.lines = [json.dumps(event) + "\r\n" for event in events]
        self.terminal = terminal
        self.before = ""
        self.after: str | type[pexpect.EOF] | type[pexpect.TIMEOUT] = ""
        self.buffer = ""
        self.exitstatus = 0
        self.signalstatus = None
        self.closed = False
        self.reads = 0

    def expect(self, patterns, timeout):
        self.reads += 1
        if self.reads == 1:
            self.before = self.lines[0][:-2]
            self.after = "\r\n"
            self.buffer = "".join(self.lines[1:3])
            return 0
        if self.reads == 2:
            # This match consumes existing pexpect data. The remaining
            # events still wait in the kernel, despite the process exiting.
            self.before = self.lines[1][:-2]
            self.after = "\r\n"
            self.buffer = self.lines[2]
            return 0
        if self.reads == 3:
            self.before = "".join(self.lines[2:])
            self.after = "\r\n"
            self.buffer = ""
            return 0
        assert self.reads == 4, "runner must finish after the terminal read"
        assert 0 < timeout <= 0.05, "dead-child drain must retain its bounded wait"
        self.before = ""
        if self.terminal == "raised-eof":
            raise pexpect.EOF("PTY returned EIO after its output was drained")
        if self.terminal == "timeout":
            # A surviving descendant can keep the PTY open after the
            # watched process has exited. Do not wait for its EOF forever.
            self.after = pexpect.TIMEOUT
            return 2
        self.after = pexpect.EOF
        return 1

    def isalive(self) -> bool:
        return False

    def close(self) -> None:
        self.closed = True


@pytest.mark.parametrize("terminal", ["eof", "raised-eof", "timeout"])
def test_dead_child_records_buffered_lines_and_unread_pty_tail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, terminal: str
) -> None:
    events = [
        {"_event": "v2_playbook_on_start"},
        {"_event": "v2_playbook_on_play_start", "play": {"id": "p1", "name": "Deploy"}},
        {"_event": "v2_playbook_on_task_start", "task": {"id": "t1", "name": "Install"}},
        {"_event": "v2_runner_on_ok", "task": {"id": "t1"}, "hosts": {"web1": {}}},
        {"_event": "v2_runner_on_ok", "task": {"id": "t1"}, "hosts": {"web4": {}}},
        {"_event": "v2_runner_on_failed", "task": {"id": "t1"}, "hosts": {"web2": {}}},
        {"_event": "v2_runner_on_failed", "task": {"id": "t1"}, "hosts": {"web3": {}}},
        {"_event": "v2_playbook_on_stats"},
    ]
    child = _DeadChildWithUnreadTail(events, terminal)
    monkeypatch.setattr(runner.pexpect, "spawn", lambda *args, **kwargs: child)
    monkeypatch.setattr(runner, "_build_command", lambda *args: ("fake-ansible", []))
    monkeypatch.setattr(
        runner, "run_preflight", lambda **kwargs: MagicMock(definitions=[], errors=[])
    )

    assert runner.run_playbook("site.yml", [], MagicMock(), session_dir=tmp_path) == 0

    [session_path] = [path for path in tmp_path.iterdir() if path.is_dir()]
    recorded = [
        json.loads(line) for line in (session_path / "events.jsonl").read_text().splitlines()
    ]
    assert recorded == events
    assert child.closed


def test_dead_child_timeout_records_final_fragment_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    events = [{"_event": "v2_playbook_on_start"}, {"_event": "v2_playbook_on_stats"}]

    class _FinalFragmentChild(_DeadChildWithUnreadTail):
        def expect(self, patterns, timeout):
            self.reads += 1
            if self.reads == 1:
                self.before = self.lines[0][:-2]
                self.after = "\r\n"
                return 0
            assert self.reads == 2
            # On TIMEOUT, pexpect.before includes the unread buffer.
            self.before = self.lines[1][:-2]
            self.buffer = self.before
            self.after = pexpect.TIMEOUT
            return 2

    child = _FinalFragmentChild(events, "timeout")
    monkeypatch.setattr(runner.pexpect, "spawn", lambda *args, **kwargs: child)
    monkeypatch.setattr(runner, "_build_command", lambda *args: ("fake-ansible", []))
    monkeypatch.setattr(
        runner, "run_preflight", lambda **kwargs: MagicMock(definitions=[], errors=[])
    )

    assert runner.run_playbook("site.yml", [], MagicMock(), session_dir=tmp_path) == 0

    [session_path] = [path for path in tmp_path.iterdir() if path.is_dir()]
    recorded = [
        json.loads(line) for line in (session_path / "events.jsonl").read_text().splitlines()
    ]
    assert recorded == events


def test_dead_child_deadline_preserves_json_containing_password_prompt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    prompt = "[sudo] password for root: "
    events = [
        {"_event": "v2_playbook_on_start"},
        {"_event": "v2_runner_on_ok", "task": {"id": "t1"}, "hosts": {"web1": {"stdout": prompt}}},
        {"_event": "v2_playbook_on_stats"},
    ]
    clock = [0.0]

    class _JsonPromptChild(_DeadChildWithUnreadTail):
        def expect(self, patterns, timeout):
            self.reads += 1
            if self.reads == 1:
                self.before = self.lines[0][:-2]
                self.after = "\r\n"
                return 0
            assert self.reads == 2, "the expired deadline must flush the remaining buffer"
            self.before, self.after, remainder = self.lines[1].partition(prompt)
            self.buffer = remainder + self.lines[2]
            clock[0] = 0.1
            return 3  # password pattern matched inside the JSON string

    child = _JsonPromptChild(events, "timeout")
    renderer = MagicMock()
    monkeypatch.setattr(runner.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(runner.pexpect, "spawn", lambda *args, **kwargs: child)
    monkeypatch.setattr(runner, "_build_command", lambda *args: ("fake-ansible", []))
    monkeypatch.setattr(
        runner, "run_preflight", lambda **kwargs: MagicMock(definitions=[], errors=[])
    )

    assert runner.run_playbook("site.yml", [], renderer, session_dir=tmp_path) == 0

    [session_path] = [path for path in tmp_path.iterdir() if path.is_dir()]
    recorded = [
        json.loads(line) for line in (session_path / "events.jsonl").read_text().splitlines()
    ]
    assert recorded == events
    renderer.handle_password_prompt.assert_not_called()
