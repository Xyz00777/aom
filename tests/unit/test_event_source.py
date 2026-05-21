"""Tests for the EventSource Protocol and its two production drivers.

The Protocol is intentionally tiny — one ``drive(renderer)`` method — so
these tests serve as both contract documentation and smoke checks that
the concrete drivers in ``ansible_aom.drivers`` actually satisfy it.

Replay is exercised end-to-end through a recorded fixture session
(``tests/fixtures/sessions/minimal_replay``) so the driver is wired
against the real ``replay_session`` body via a FakeRenderer that just
records what it was told.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

from ansible_aom.drivers.protocol import EventSource
from ansible_aom.drivers.replay import ReplayDriver


class FakeRenderer:
    """Minimal Renderer-shaped sink used by the driver smoke tests."""

    def __init__(self) -> None:
        self.start_calls: list[tuple[str, list[str]]] = []
        self.stopped: bool = False
        self.events: list[dict[str, Any]] = []
        self.warnings: list[tuple[str, bool]] = []
        self.logs: list[str] = []
        self.completion: tuple[int, str] | None = None
        self.definitions: list[Any] = []
        self.ticks: int = 0
        self.pty_bytes_calls: int = 0
        self.subprocess_active_calls: list[bool] = []

    def start(self, playbook: str, args: list[str]) -> None:
        self.start_calls.append((playbook, list(args)))

    def stop(self) -> None:
        self.stopped = True

    def set_definitions(self, definitions: list[Any]) -> None:
        self.definitions = list(definitions)

    def update_state(self, event: dict[str, Any]) -> None:
        self.events.append(event)

    def add_warning(self, message: str, is_deprecation: bool = False) -> None:
        self.warnings.append((message, is_deprecation))

    def print_log(self, message: str) -> None:
        self.logs.append(message)

    def tick(self) -> None:
        self.ticks += 1

    def note_pty_bytes(self) -> None:
        self.pty_bytes_calls += 1

    def note_subprocess_active(self, active: bool) -> None:
        self.subprocess_active_calls.append(active)

    def handle_password_prompt(self, prompt: str) -> str:  # pragma: no cover
        return ""

    def handle_interactive_prompt(self, prompt: str) -> str:  # pragma: no cover
        return ""

    def handle_completion(self, exit_code: int, state: str) -> None:
        self.completion = (exit_code, state)


def _write_session(tmp_path: Path, events: list[dict[str, Any]]) -> tuple[Path, str]:
    """Materialise a minimum-viable session directory the replay loader will accept."""
    session_id = "test-replay-session"
    sdir = tmp_path / "sessions" / session_id
    sdir.mkdir(parents=True)
    meta = {
        "session_id": session_id,
        "playbook": "fixture.yml",
        "ansible_args": [],
        "started_at": "2026-05-21T00:00:00+00:00",
        "ended_at": "2026-05-21T00:00:00+00:00",
        "status": "completed",
    }
    (sdir / "meta.json").write_text(json.dumps(meta))
    with (sdir / "events.jsonl").open("w") as fh:
        for event in events:
            fh.write(json.dumps(event) + "\n")
    return tmp_path / "sessions", session_id


# ---------------------------------------------------------------------------
# Protocol shape
# ---------------------------------------------------------------------------


def test_event_source_is_runtime_checkable() -> None:
    """``EventSource`` must be ``@runtime_checkable`` so structural checks work.

    Without runtime-checkable, ``isinstance(obj, EventSource)`` raises
    ``TypeError`` and we can't substitute fakes in tests.
    """

    class Conforming:
        def drive(self, renderer: object) -> int:
            return 0

    assert isinstance(Conforming(), EventSource)


def test_event_source_rejects_non_conforming() -> None:
    class NoDrive:
        pass

    assert not isinstance(NoDrive(), EventSource)


# ---------------------------------------------------------------------------
# LiveDriver — exists, ships drive(), satisfies the protocol
# ---------------------------------------------------------------------------


def test_live_driver_satisfies_event_source() -> None:
    """LiveDriver is the production EventSource for ansible-playbook runs."""
    from ansible_aom.drivers.live import LiveDriver

    driver = LiveDriver(playbook="dummy.yml", ansible_args=[], record=False)
    assert isinstance(driver, EventSource)


# ---------------------------------------------------------------------------
# ReplayDriver — exercise the full drive() body with a recorded fixture
# ---------------------------------------------------------------------------


def test_replay_driver_satisfies_event_source(tmp_path: Path) -> None:
    state_dir, session_id = _write_session(tmp_path, [])
    driver = ReplayDriver(session_dir=state_dir, session_id=session_id, speed=0)
    assert isinstance(driver, EventSource)


def test_replay_driver_drives_renderer_end_to_end(tmp_path: Path) -> None:
    """Drive a synthetic 2-event session into a FakeRenderer and assert
    the full Renderer lifecycle fired in the right order with the right data.
    """
    state_dir, session_id = _write_session(
        tmp_path,
        [
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-21T00:00:00+00:00"},
            {"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-21T00:00:01+00:00"},
        ],
    )
    driver = ReplayDriver(session_dir=state_dir, session_id=session_id, speed=0)
    renderer = FakeRenderer()

    exit_code = driver.drive(renderer)

    assert exit_code == 0
    assert renderer.start_calls == [("fixture.yml", [])]
    assert [e["_event"] for e in renderer.events] == [
        "v2_playbook_on_start",
        "v2_playbook_on_stats",
    ]
    assert renderer.completion == (0, "completed")
    assert renderer.stopped is True


def test_replay_driver_missing_session_returns_1(tmp_path: Path) -> None:
    """Replay against a non-existent session id propagates a 1 exit code."""
    driver = ReplayDriver(session_dir=tmp_path, session_id="does-not-exist", speed=0)
    renderer = FakeRenderer()

    exit_code = driver.drive(renderer)

    assert exit_code == 1


# ---------------------------------------------------------------------------
# LiveDriver end-to-end smoke — uses a fake ansible-playbook that emits JSONL
# ---------------------------------------------------------------------------


def test_live_driver_drives_renderer_with_fake_subprocess(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A LiveDriver should drive renderer.start -> events -> completion when
    the runner is fed by a stubbed subprocess.

    We don't shell out to real ansible-playbook here — instead we patch
    pexpect.spawn so the runner consumes a canned line stream. The test
    proves the driver wires the existing run_playbook loop end-to-end
    via FakeRenderer.
    """
    pexpect = pytest.importorskip("pexpect")

    from ansible_aom.drivers.live import LiveDriver

    class FakeSpawn:
        def __init__(self) -> None:
            self.pid = os.getpid()
            self.before: str = ""
            self.after: str = ""
            self.buffer: str = ""
            self._lines = [
                '{"_event": "v2_playbook_on_start", "_timestamp": "2026-05-21T00:00:00Z"}\n',
                '{"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-21T00:00:01Z"}\n',
            ]
            self._idx = 0
            self.exitstatus: int | None = None
            self.signalstatus: int | None = None

        def expect(self, patterns: Any, timeout: float = 0) -> int:  # noqa: ARG002
            if self._idx >= len(self._lines):
                self.exitstatus = 0
                raise pexpect.exceptions.EOF("eof")
            line = self._lines[self._idx]
            self._idx += 1
            # Mimic pexpect's split-on-newline contract:
            #   before = content up to the newline, after = the newline.
            self.before = line.rstrip("\n")
            self.after = "\n"
            return 0  # newline_idx in _drive

        def isalive(self) -> bool:
            return self._idx < len(self._lines)

        def close(self, force: bool = False) -> None:  # noqa: ARG002
            self.exitstatus = self.exitstatus or 0

        def sendintr(self) -> None:  # pragma: no cover
            pass

        def sendline(self, _: str) -> None:  # pragma: no cover
            pass

        def read_nonblocking(self, size: int = 0, timeout: float = 0) -> str:  # noqa: ARG002
            return ""

    spawned: dict[str, Any] = {}

    def fake_spawn(executable: str, args: list[str], **_kwargs: Any) -> FakeSpawn:
        spawned["executable"] = executable
        spawned["args"] = args
        return FakeSpawn()

    monkeypatch.setattr("ansible_aom.ansible.runner.pexpect.spawn", fake_spawn)
    # Restore the canonical command builder. Other tests in the
    # integration suite patch it via context managers, but if pytest is
    # mid-teardown when this test runs the patch can momentarily leak.
    # Asserting against a known builder makes the test order-independent.
    monkeypatch.setattr(
        "ansible_aom.ansible.runner._build_command",
        lambda playbook, ansible_args: ("ansible-playbook", [playbook, *ansible_args]),
    )
    # Skip the real preflight subprocess (no ansible-playbook available
    # in unit-test env). The driver only needs the smoke loop to fire.
    monkeypatch.setattr(
        "ansible_aom.ansible.runner.run_preflight",
        lambda playbook, ansible_args: type("PR", (), {"definitions": [], "errors": []})(),
    )

    renderer = FakeRenderer()
    driver = LiveDriver(playbook="x.yml", ansible_args=["-vv"], record=False)
    exit_code = driver.drive(renderer)

    assert exit_code == 0
    assert renderer.start_calls == [("x.yml", ["-vv"])]
    assert [e["_event"] for e in renderer.events] == [
        "v2_playbook_on_start",
        "v2_playbook_on_stats",
    ]
    assert renderer.completion == (0, "completed")
    assert renderer.stopped is True
    assert spawned["executable"] == "ansible-playbook"
    assert spawned["args"] == ["x.yml", "-vv"]
