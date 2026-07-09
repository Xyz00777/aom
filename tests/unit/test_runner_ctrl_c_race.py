"""R7 — Ctrl-C race guard.

If SIGINT arrives between the child exiting cleanly and
``run_playbook`` returning, the KeyboardInterrupt branch should not
overwrite the child's real exit code with ``130``. The spec-ideal:
"completion wins" — if the child has already exited cleanly, the
runner should report that exit code (0 for success) instead of
cancelling the run's outcome.

The fix lives in :func:`ansible_aom.ansible.runner.run_playbook`: the
except branch checks the child's liveness + exitstatus before
returning ``130``. If the child is already dead with a known exit
status, that status is reported instead.

These tests pin both halves of the contract:

- **Race window #2**: child exited cleanly, SIGINT during the
  post-``_drive`` cleanup → return the child's exit code (was 130,
  now 0).
- **Race window #1**: SIGINT mid-run while the child is still
  alive → still 130. The fix MUST NOT mask genuine cancels.
"""

from __future__ import annotations

import os
from typing import Any
from unittest.mock import MagicMock

import pytest


class _FakeSpawn:
    """Minimal pexpect.spawn-shaped stand-in.

    Emits a fixed list of newline-terminated JSONL lines, then exits
    with ``exit_code``. Mirrors the contract ``_drive`` depends on:
    newline-terminated ``expect`` returns, EOF raises to break the
    loop, ``isalive`` flips after the last line, and ``exitstatus``
    is read after the loop ends.
    """

    def __init__(self, lines: list[str], exit_code: int = 0) -> None:
        self.pid = os.getpid()
        self.before: str = ""
        self.after: str = ""
        self.buffer: str = ""
        self._lines = list(lines)
        self._idx = 0
        self._exit_code = exit_code
        self.exitstatus: int | None = None
        self.signalstatus: int | None = None

    def expect(self, patterns: Any, timeout: float = 0) -> int:  # noqa: ARG002
        pexpect = pytest.importorskip("pexpect")
        if self._idx >= len(self._lines):
            self.exitstatus = self.exitstatus if self.exitstatus is not None else self._exit_code
            raise pexpect.exceptions.EOF("eof")
        line = self._lines[self._idx]
        self._idx += 1
        self.before = line.rstrip("\n")
        self.after = "\n"
        return 0  # newline_idx

    def isalive(self) -> bool:
        return self._idx < len(self._lines)

    def close(self, force: bool = False) -> None:  # noqa: ARG002
        if self.exitstatus is None:
            self.exitstatus = self._exit_code

    def sendintr(self) -> None:
        pass

    def sendline(self, _: str) -> None:  # pragma: no cover
        pass

    def read_nonblocking(self, size: int = 0, timeout: float = 0) -> str:  # noqa: ARG002
        return ""


def _patch_runner_for_fake_subprocess(
    monkeypatch: pytest.MonkeyPatch,
    spawn: _FakeSpawn,
) -> dict[str, Any]:
    """Wire the runner's spawn/preflight/build-command seams to a fake."""
    spawned: dict[str, Any] = {}

    def fake_spawn(executable: str, args: list[str], **_kwargs: Any) -> _FakeSpawn:
        spawned["executable"] = executable
        spawned["args"] = list(args)
        return spawn

    monkeypatch.setattr("ansible_aom.ansible.runner.pexpect.spawn", fake_spawn)
    monkeypatch.setattr(
        "ansible_aom.ansible.runner._build_command",
        lambda playbook, ansible_args: ("ansible-playbook", [playbook, *ansible_args]),
    )
    monkeypatch.setattr(
        "ansible_aom.ansible.runner.run_preflight",
        lambda playbook, ansible_args: type("PR", (), {"definitions": [], "errors": []})(),
    )
    return spawned


class TestCtrlCAfterChildExitedCleanly:
    """Window #2: child already exited 0, then SIGINT fires during cleanup.

    Before the R7 fix, the KeyboardInterrupt branch unconditionally
    returned 130, overriding the run's clean 0. The fix detects that
    the child is no longer alive and reports its real exit code.
    """

    def test_sigint_during_handle_completion_returns_child_exit_code(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The race: child exits 0, ``_drive`` returns 0, then SIGINT
        fires while the runner is still in the try-body cleaning up.

        The fixture fires KeyboardInterrupt on the FIRST call to
        ``renderer.handle_completion`` (the legitimate one for the
        run's success). The R7 fix should detect that the child is
        already dead and has exitstatus 0, then route through
        ``handle_completion`` a second time with the real exit code
        — not 130.
        """
        from ansible_aom.ansible.runner import run_playbook

        lines = [
            '{"_event": "v2_playbook_on_start", "_timestamp": "2026-05-21T00:00:00Z"}\n',
            '{"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-21T00:00:01Z"}\n',
        ]
        spawn = _FakeSpawn(lines, exit_code=0)
        _patch_runner_for_fake_subprocess(monkeypatch, spawn)

        renderer = MagicMock()
        # First call (the legitimate completion) raises KeyboardInterrupt;
        # subsequent calls (the runner's recovery call) must NOT re-raise,
        # so feed a one-shot iterator.
        renderer.handle_completion.side_effect = [KeyboardInterrupt(), None]

        exit_code = run_playbook("playbook.yml", [], renderer, timeout=0.5, record=False)

        assert exit_code == 0, (
            f"After R7 fix, SIGINT after clean exit should preserve exit code 0, got {exit_code}"
        )
        renderer.handle_completion.assert_called_with(0, "completed")

    def test_sigint_after_failed_child_returns_child_exit_code(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """If the child exited non-zero (e.g. failed playbook) and SIGINT
        arrives during cleanup, the child's exit code STILL wins — not 130.

        The fix is not "preserve 0 specifically" but "preserve whatever
        the child's real exit code was".
        """
        from ansible_aom.ansible.runner import run_playbook

        lines = [
            '{"_event": "v2_playbook_on_start", "_timestamp": "2026-05-21T00:00:00Z"}\n',
            '{"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-21T00:00:01Z"}\n',
        ]
        spawn = _FakeSpawn(lines, exit_code=2)
        _patch_runner_for_fake_subprocess(monkeypatch, spawn)

        renderer = MagicMock()
        renderer.handle_completion.side_effect = [KeyboardInterrupt(), None]

        exit_code = run_playbook("playbook.yml", [], renderer, timeout=0.5, record=False)

        assert exit_code == 2, f"Child's real exit code 2 should win over 130, got {exit_code}"


class TestCtrlCDuringActiveRun:
    """Window #1: SIGINT arrives while the child is still alive.

    The fix MUST NOT mask genuine cancels — if the child is still
    running when SIGINT fires, 130 is the correct answer.
    """

    def test_sigint_mid_run_returns_130(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Simulate SIGINT during a real event: the renderer's
        ``update_state`` raises KeyboardInterrupt on the first call,
        before the run has completed. The runner's except branch
        sees a child that is still alive (``isalive`` returns True
        because more lines are pending) and returns 130.
        """
        from ansible_aom.ansible.runner import run_playbook

        lines = [
            '{"_event": "v2_playbook_on_start", "_timestamp": "2026-05-21T00:00:00Z"}\n',
        ]
        spawn = _FakeSpawn(lines, exit_code=0)
        _patch_runner_for_fake_subprocess(monkeypatch, spawn)

        renderer = MagicMock()
        renderer.update_state.side_effect = KeyboardInterrupt()

        exit_code = run_playbook("playbook.yml", [], renderer, timeout=0.5, record=False)

        assert exit_code == 130, (
            f"SIGINT mid-run while child alive must return 130, got {exit_code}"
        )
        renderer.handle_completion.assert_called_with(130, "crashed")
