"""R9 — searchwindowsize bound on pexpect.spawn().

R9 spec: pexpect's ``searchwindowsize`` controls how much of the
incoming PTY stream pexpect keeps for pattern matching. With the
default of ``None``, pexpect retains the *entire* buffer in memory
(``expect.py``: ``# copy the whole buffer (really slow for large
datasets)``). For a run that emits a multi-MB single-line event
(common with `debug: var=huge_object` or `register: huge`), this means
pexpect's internal StringIO holds the full line until the terminating
``\\n`` arrives.

Setting an explicit ``searchwindowsize`` matching the longest pattern
we use bounds the per-call buffer regardless of input line size:

- Newline pattern ``r"\\r?\\n"``: max 2 bytes per match.
- Password prompts: longest is ``r"\\[sudo\\] password for [^:\\n]+: "``
  (29 bytes plus dynamic hostname length).

A bound of ``512`` covers every pattern in ``_drive``'s pattern list
with comfortable headroom (longest prompt is well under 100 chars)
while bounding pexpect's internal buffer to ~512 bytes per call
instead of "however big the next line is". The choice matches the
documented R9 rationale that the bound only needs to exceed the
longest pattern.
"""

from __future__ import annotations

import os
from typing import Any
from unittest.mock import MagicMock

import pytest


class _FakeSpawn:
    """Stand-in for pexpect.spawn() with the kwargs the runner passes."""

    def __init__(
        self,
        executable: str,
        args: list[str],
        **_kwargs: Any,
    ) -> None:
        self.executable = executable
        self.args = list(args)
        self.kwargs = dict(_kwargs)
        self.pid = os.getpid()
        self.before: str = ""
        self.after: str = ""
        self.buffer: str = ""
        self.exitstatus: int | None = 0
        self.signalstatus: int | None = None

    def expect(self, patterns: Any, timeout: float = 0) -> int:  # noqa: ARG002
        pexpect = pytest.importorskip("pexpect")
        raise pexpect.exceptions.EOF("eof")

    def isalive(self) -> bool:
        return False

    def close(self, force: bool = False) -> None:  # noqa: ARG002
        pass

    def sendintr(self) -> None:
        pass

    def sendline(self, _: str) -> None:  # pragma: no cover
        pass

    def read_nonblocking(self, size: int = 0, timeout: float = 0) -> str:  # noqa: ARG002
        return ""


def _patch_runner_with_fake_spawn(
    monkeypatch: pytest.MonkeyPatch,
    captured: dict[str, Any],
) -> None:
    """Capture every kwarg passed to pexpect.spawn() inside the runner."""

    def fake_spawn(executable: str, args: list[str], **kwargs: Any) -> _FakeSpawn:
        captured["kwargs"] = dict(kwargs)
        return _FakeSpawn(executable, args, **kwargs)

    monkeypatch.setattr("ansible_aom.ansible.runner.pexpect.spawn", fake_spawn)
    monkeypatch.setattr(
        "ansible_aom.ansible.runner._build_command",
        lambda playbook, ansible_args: ("ansible-playbook", [playbook, *ansible_args]),
    )
    monkeypatch.setattr(
        "ansible_aom.ansible.runner.run_preflight",
        lambda **_: MagicMock(definitions=[], errors=[]),
    )


def test_runner_sets_explicit_searchwindowsize(monkeypatch: pytest.MonkeyPatch) -> None:
    """R9: the runner must pass an integer ``searchwindowsize`` to pexpect.

    With ``searchwindowsize=None`` (the pexpect default), a single
    multi-MB JSONL event bloats pexpect's internal StringIO buffer
    until the terminating newline arrives. Passing an explicit bound
    keeps the per-call buffer small regardless of input line size.
    """
    from ansible_aom.ansible.runner import run_playbook

    captured: dict[str, Any] = {}
    _patch_runner_with_fake_spawn(monkeypatch, captured)

    renderer = MagicMock()
    exit_code = run_playbook("playbook.yml", [], renderer, record=False)
    assert exit_code == 0

    kwargs = captured["kwargs"]
    assert "searchwindowsize" in kwargs, (
        f"runner must pass searchwindowsize to pexpect.spawn(); got kwargs={kwargs!r}"
    )
    bound = kwargs["searchwindowsize"]
    assert isinstance(bound, int), (
        f"searchwindowsize must be an int, got {type(bound).__name__}: {bound!r}"
    )
    assert bound > 0, f"searchwindowsize must be positive, got {bound!r}"


def test_runner_searchwindow_covers_longest_pattern(monkeypatch: pytest.MonkeyPatch) -> None:
    """R9: searchwindowsize must exceed every pattern the runner uses.

    The runner's pattern list at ``runner.py:_drive`` includes:
    - ``r"\\r?\\n"`` (2 bytes max per match)
    - password prompts like ``r"\\[sudo\\] password for [^:\\n]+: "``
      (~30 chars plus dynamic hostname length, comfortably under 100
      bytes in any realistic scenario)

    The bound must cover the longest realistic pattern or pexpect
    would clip legitimate matches. Pin the lower bound at the runner's
    documented value so an accidental constant drift is caught.
    """
    from ansible_aom.ansible.runner import run_playbook

    captured: dict[str, Any] = {}
    _patch_runner_with_fake_spawn(monkeypatch, captured)

    renderer = MagicMock()
    run_playbook("playbook.yml", [], renderer, record=False)

    bound = captured["kwargs"]["searchwindowsize"]
    # Documented R9 value: 512 bytes, which covers the longest realistic
    # password-prompt match with comfortable headroom.
    assert bound >= 256, (
        f"searchwindowsize={bound} is too small to cover the longest "
        f"password-prompt pattern (~100 bytes). Must be >= 256."
    )
    # And not absurdly large (defeats the purpose of bounding memory).
    assert bound <= 4096, (
        f"searchwindowsize={bound} is too large; the bound should "
        f"track the longest pattern, not the line size."
    )
