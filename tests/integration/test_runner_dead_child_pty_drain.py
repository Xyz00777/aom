"""Exercise dead-child draining through a real Linux subprocess and PTY."""

from __future__ import annotations

import json
import os
import select
import sys
import time as system_time
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from ansible_aom.ansible import runner


@pytest.mark.skipif(
    sys.platform != "linux" or not hasattr(os, "pidfd_open"),
    reason="deterministic child-exit barrier requires Linux pidfds",
)
def test_runner_records_events_buffered_after_child_exits_in_real_pty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    events = [
        {"_event": "v2_playbook_on_start", "_timestamp": "2026-11-21T00:00:00Z"},
        *[
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-11-21T00:00:01Z",
                "task": {"id": f"task-{index}", "name": f"Task {index}"},
                "hosts": {"localhost": {"changed": False}},
            }
            for index in range(10)
        ],
    ]
    payload = json.dumps(events)
    child_code = (
        "import json, os, sys; "
        f"payload = json.loads({payload!r}); "
        "os.write(sys.stdout.fileno(), "
        "b''.join((json.dumps(event) + '\\n').encode() for event in payload))"
    )
    spawn = runner.pexpect.spawn

    class _ExitSynchronizedPty:
        """Hold the first expect result until the real child has exited."""

        def __init__(self, child: Any) -> None:
            self._child = child
            self._pidfd = os.pidfd_open(child.pid)
            self._first_expect = True
            self._expect_calls = 0

        def expect(self, *args: Any, **kwargs: Any) -> int:
            self._expect_calls += 1
            if self._expect_calls == 2:
                delay_started = system_time.monotonic()
                system_time.sleep(0.075)
                assert system_time.monotonic() - delay_started >= 0.05
            result = self._child.expect(*args, **kwargs)
            if self._first_expect:
                self._first_expect = False
                assert result == 0, "the first PTY match must consume a JSONL newline"
                assert self._child.buffer, "pexpect must retain unread PTY output after that match"
                exit_signal = select.poll()
                exit_signal.register(self._pidfd, select.POLLIN)
                assert exit_signal.poll(5_000), "child did not exit within the bounded barrier"
            return result

        def close(self, *args: Any, **kwargs: Any) -> None:
            try:
                self._child.close(*args, **kwargs)
            finally:
                os.close(self._pidfd)

        def __getattr__(self, name: str) -> Any:
            return getattr(self._child, name)

        def __setattr__(self, name: str, value: Any) -> None:
            if name.startswith("_"):
                object.__setattr__(self, name, value)
            else:
                setattr(self._child, name, value)

    def spawn_with_small_reads(*args: Any, **kwargs: Any) -> _ExitSynchronizedPty:
        child = spawn(*args, maxread=256, **kwargs)
        return _ExitSynchronizedPty(child)

    monkeypatch.setattr(runner.pexpect, "spawn", spawn_with_small_reads)
    monkeypatch.setattr(
        runner, "_build_command", lambda *args: (sys.executable, ["-c", child_code])
    )
    monkeypatch.setattr(
        runner, "run_preflight", lambda **kwargs: MagicMock(definitions=[], errors=[])
    )

    class _RunnerDeadlineClock:
        def monotonic(self) -> float:
            return 0.0

        def monotonic_ns(self) -> int:
            return system_time.monotonic_ns()

    monkeypatch.setattr(runner, "time", _RunnerDeadlineClock())

    assert runner.run_playbook("site.yml", [], MagicMock(), session_dir=tmp_path) == 0

    [session_path] = [path for path in tmp_path.iterdir() if path.is_dir()]
    recorded = [
        json.loads(line)
        for line in (session_path / "events.jsonl").read_text().splitlines()
        if line.strip()
    ]
    assert recorded == events, (
        f"events.jsonl recorded {len(recorded)} of {len(events)} child events; "
        f"tail identifiers: {[event.get('task', {}).get('id') for event in recorded[-5:]]}"
    )
