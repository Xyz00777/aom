"""End-to-end: write a v1.2 meta.json via SessionManager, look it up via find_previous_run.

This is the contract test that ties Task 2 (persistence) and Task 3
(lookup) together. If either side ever drifts on field names, format,
or semantics, this test fails first — before any user-facing surface
notices.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from ansible_aom.core.models import PlayDefinition
from ansible_aom.core.run_config import build_run_config_key
from ansible_aom.session.history import PriorRun, find_previous_run
from ansible_aom.session.store import SessionManager


def _fake_ansible_command(events: list[dict], exit_code: int = 0) -> tuple[str, list[str]]:
    """Build a (command, args) pair that emits ``events`` as JSONL then exits."""
    payload = json.dumps(events)
    code = (
        "import json, sys; "
        f"events = json.loads({payload!r}); "
        "[sys.stdout.write(json.dumps(e) + '\\n') for e in events]; "
        "sys.stdout.flush(); "
        f"sys.exit({exit_code})"
    )
    return sys.executable, ["-c", code]


def test_session_then_history_roundtrip(tmp_path: Path) -> None:
    pb = tmp_path / "play.yml"
    pb.write_text("")

    sessions_dir = tmp_path / "sessions"
    mgr = SessionManager(session_dir=sessions_dir)
    sid = mgr.start_session(str(pb), ansible_args=["--tags", "web"])
    mgr.end_session(sid, "completed", preflight_task_count=12, resolved_host_count=2)

    key = build_run_config_key(playbook=str(pb), ansible_args=["--tags", "web"])
    prior = find_previous_run(sessions_dir, key, host_count=2)
    assert prior is not None
    assert prior.session_id == sid
    assert prior.task_count == 12
    assert prior.host_count == 2
    assert prior.duration_seconds >= 0.0


def test_different_tags_do_not_match(tmp_path: Path) -> None:
    pb = tmp_path / "play.yml"
    pb.write_text("")

    sessions_dir = tmp_path / "sessions"
    mgr = SessionManager(session_dir=sessions_dir)
    sid = mgr.start_session(str(pb), ansible_args=["--tags", "web"])
    mgr.end_session(sid, "completed", preflight_task_count=12, resolved_host_count=2)

    key = build_run_config_key(playbook=str(pb), ansible_args=["--tags", "db"])
    assert find_previous_run(sessions_dir, key, host_count=2) is None


def test_different_host_count_does_not_match(tmp_path: Path) -> None:
    pb = tmp_path / "play.yml"
    pb.write_text("")

    sessions_dir = tmp_path / "sessions"
    mgr = SessionManager(session_dir=sessions_dir)
    sid = mgr.start_session(str(pb), ansible_args=[])
    mgr.end_session(sid, "completed", preflight_task_count=5, resolved_host_count=1)

    key = build_run_config_key(playbook=str(pb), ansible_args=[])
    assert find_previous_run(sessions_dir, key, host_count=3) is None


def test_failed_session_is_not_returned(tmp_path: Path) -> None:
    """End-of-run status==failed sessions are unreliable — skip them."""
    pb = tmp_path / "play.yml"
    pb.write_text("")

    sessions_dir = tmp_path / "sessions"
    mgr = SessionManager(session_dir=sessions_dir)
    sid = mgr.start_session(str(pb), ansible_args=[])
    mgr.end_session(sid, "failed", preflight_task_count=5, resolved_host_count=1)

    key = build_run_config_key(playbook=str(pb), ansible_args=[])
    assert find_previous_run(sessions_dir, key, host_count=1) is None


def test_most_recent_completed_wins(tmp_path: Path) -> None:
    pb = tmp_path / "play.yml"
    pb.write_text("")

    sessions_dir = tmp_path / "sessions"
    mgr = SessionManager(session_dir=sessions_dir)

    sid_old = mgr.start_session(str(pb), ansible_args=[])
    mgr.end_session(sid_old, "completed", preflight_task_count=5, resolved_host_count=1)

    sid_new = mgr.start_session(str(pb), ansible_args=[])
    mgr.end_session(sid_new, "completed", preflight_task_count=7, resolved_host_count=1)

    key = build_run_config_key(playbook=str(pb), ansible_args=[])
    prior = find_previous_run(sessions_dir, key, host_count=1)
    assert prior is not None
    assert prior.session_id == sid_new
    assert prior.task_count == 7


def test_runner_pushes_prior_run_into_renderer(tmp_path: Path) -> None:
    """The runner must look up history and call ``renderer.set_prior_run``.

    Pins the runner → renderer wire so a future refactor that removes
    the ``renderer.set_prior_run(prior)`` call breaks at least one test.
    Persistence and lookup are covered above; this is the integration
    sliver that proves they're wired through the runner.
    """
    from ansible_aom.ansible.runner import run_playbook

    pb = tmp_path / "play.yml"
    pb.write_text("")
    sessions_dir = tmp_path / "sessions"

    # Seed a completed prior run that the lookup will find.
    mgr = SessionManager(session_dir=sessions_dir)
    seed_id = mgr.start_session(str(pb), ansible_args=["--tags", "web"])
    mgr.end_session(seed_id, "completed", preflight_task_count=11, resolved_host_count=2)

    received_prior: list[object] = []

    class StubRenderer:
        def start(self, playbook: str, args: list[str]) -> None: ...
        def set_definitions(self, definitions: list) -> None: ...
        def set_prior_run(self, prior_run: object) -> None:
            received_prior.append(prior_run)

        def update_state(self, event: dict) -> None: ...
        def handle_password_prompt(self, prompt: str) -> str:
            return ""

        def handle_completion(self, exit_code: int, state: str) -> None: ...
        def stop(self) -> None: ...
        def note_pty_bytes(self) -> None: ...
        def note_subprocess_active(self, active: bool) -> None: ...
        def add_warning(self, message: str, is_deprecation: bool = False) -> None: ...

    # Preflight result that matches the seeded session (same hosts → same host_count).
    play = PlayDefinition(
        id="p1",
        name="P1",
        hosts="web",
        resolved_hosts=["web1", "web2"],
    )
    fake_pre_result = MagicMock()
    fake_pre_result.definitions = [play]
    fake_pre_result.errors = []

    cmd, args = _fake_ansible_command(
        [{"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:01Z"}],
        exit_code=0,
    )

    with (
        patch("ansible_aom.ansible.runner.run_preflight", return_value=fake_pre_result),
        patch("ansible_aom.ansible.runner._build_command", return_value=(cmd, args)),
    ):
        run_playbook(
            str(pb),
            ["--tags", "web"],
            StubRenderer(),
            session_dir=sessions_dir,
        )

    assert len(received_prior) == 1
    prior = received_prior[0]
    assert isinstance(prior, PriorRun)
    assert prior.session_id == seed_id
    assert prior.task_count == 11
    assert prior.host_count == 2
