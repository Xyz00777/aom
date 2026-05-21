"""Record → replay determinism.

For a session recorded from a live run, replaying via
``replay_session`` must produce output byte-identical to the live
run — modulo timestamps, elapsed-time tokens, and ANSI cursor
motion. Two flavours:

1. **Compact renderer.** Drive a live run through the fake-ansible
   shim, capture stdout. Replay the same session, capture stdout.
   Normalise both with ``tests/_utils.normalize_render_output`` and
   diff.
2. **JSON renderer.** Same workflow, but the only output is a
   single ``RunSummary`` JSON line. Normalise the legitimately-
   different timestamp / duration fields, then assert exact JSON
   equality.

Plus an idempotency check: replaying the same session twice must
produce byte-identical output both times.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from ansible_aom.ansible.preflight import PreParseResult
from ansible_aom.ansible.runner import run_playbook
from ansible_aom.compact.renderer import CompactRenderer
from ansible_aom.drivers.replay import replay_session
from ansible_aom.formats.json import JsonRenderer
from tests._utils import normalize_json_summary, normalize_render_output


# Three event streams of increasing complexity. Each is a list of dicts
# the fake-ansible shim emits as JSONL — same shape ansible.posix.jsonl
# produces.
def _events_single_ok() -> list[dict]:
    return [
        {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-08T10:00:00Z"},
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-05-08T10:00:00.5Z",
            "play": {"id": "p1", "name": "Setup"},
        },
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-05-08T10:00:01Z",
            "task": {"id": "t1", "name": "Install nginx"},
        },
        {
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-05-08T10:00:01.5Z",
            "task": {"id": "t1", "name": "Install nginx"},
            "hosts": {"web1": {"ok": True, "changed": False}},
        },
        {
            "_event": "v2_playbook_on_stats",
            "_timestamp": "2026-05-08T10:00:02Z",
            "stats": {
                "web1": {
                    "ok": 1,
                    "changed": 0,
                    "failures": 0,
                    "skipped": 0,
                    "unreachable": 0,
                    "rescued": 0,
                    "ignored": 0,
                }
            },
        },
    ]


def _events_multi_host_mixed() -> list[dict]:
    return [
        {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-08T10:00:00Z"},
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-05-08T10:00:01Z",
            "play": {"id": "p1", "name": "Multi host"},
        },
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-05-08T10:00:02Z",
            "task": {"id": "t1", "name": "Install common"},
        },
        {
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-05-08T10:00:03Z",
            "task": {"id": "t1", "name": "Install common"},
            "hosts": {
                "web1": {"ok": True, "changed": False},
                "web2": {"ok": True, "changed": True},
            },
        },
        {
            "_event": "v2_runner_on_skipped",
            "_timestamp": "2026-05-08T10:00:03Z",
            "task": {"id": "t1", "name": "Install common"},
            "hosts": {"web3": {"skipped": True}},
        },
        {
            "_event": "v2_playbook_on_stats",
            "_timestamp": "2026-05-08T10:00:04Z",
            "stats": {
                "web1": {
                    "ok": 1,
                    "changed": 0,
                    "failures": 0,
                    "skipped": 0,
                    "unreachable": 0,
                    "rescued": 0,
                    "ignored": 0,
                },
                "web2": {
                    "ok": 1,
                    "changed": 1,
                    "failures": 0,
                    "skipped": 0,
                    "unreachable": 0,
                    "rescued": 0,
                    "ignored": 0,
                },
                "web3": {
                    "ok": 0,
                    "changed": 0,
                    "failures": 0,
                    "skipped": 1,
                    "unreachable": 0,
                    "rescued": 0,
                    "ignored": 0,
                },
            },
        },
    ]


def _events_with_failure() -> list[dict]:
    return [
        {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-08T10:00:00Z"},
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-05-08T10:00:01Z",
            "play": {"id": "p1", "name": "Configure"},
        },
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-05-08T10:00:02Z",
            "task": {"id": "t1", "name": "Deploy"},
        },
        {
            "_event": "v2_runner_on_failed",
            "_timestamp": "2026-05-08T10:00:03Z",
            "task": {"id": "t1", "name": "Deploy"},
            "hosts": {"server1": {"failed": True, "msg": "syntax error"}},
        },
        {
            "_event": "v2_playbook_on_stats",
            "_timestamp": "2026-05-08T10:00:04Z",
            "stats": {
                "server1": {
                    "ok": 0,
                    "changed": 0,
                    "failures": 1,
                    "skipped": 0,
                    "unreachable": 0,
                    "rescued": 0,
                    "ignored": 0,
                }
            },
        },
    ]


EVENT_STREAMS: tuple[tuple[str, list[dict], int], ...] = (
    ("single_ok", _events_single_ok(), 0),
    ("multi_host_mixed", _events_multi_host_mixed(), 0),
    ("with_failure", _events_with_failure(), 0),
)

# pytest-id pull: pull the human-readable name out of each tuple so the
# default repr (a JSON-stringified events list) doesn't dominate test
# names.
EVENT_IDS = [s[0] for s in EVENT_STREAMS]


def _fake_ansible_command(events: list[dict], exit_code: int = 0) -> tuple[str, list[str]]:
    """Build a (cmd, args) pair that emits ``events`` as JSONL then exits."""
    payload = json.dumps(events)
    code = (
        "import json, sys; "
        f"events = json.loads({payload!r}); "
        "[sys.stdout.write(json.dumps(e) + '\\n') for e in events]; "
        "sys.stdout.flush(); "
        f"sys.exit({exit_code})"
    )
    return sys.executable, ["-c", code]


def _empty_preflight() -> PreParseResult:
    """Preflight result that contributes nothing — mirrors a fake shim where
    ``--list-tasks`` / ``--list-hosts`` would error.

    Crucially: ``definitions=[]`` means ``CompactRenderer.set_definitions``
    has nothing to print, matching the replay path which never calls
    ``set_definitions``. Without this, the live preflight summary would
    appear in the live output but not in the replayed output.
    """
    return PreParseResult(plays=[], play_hosts=[], definitions=[], errors=[])


def _record_live_compact(
    events: list[dict], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> tuple[str, str]:
    """Run the compact renderer live; return (session_id, captured_stdout)."""
    renderer = CompactRenderer(is_tty=False)
    cmd, args = _fake_ansible_command(events, exit_code=0)
    with (
        patch("ansible_aom.ansible.runner._build_command", return_value=(cmd, args)),
        patch("ansible_aom.ansible.runner.run_preflight", return_value=_empty_preflight()),
    ):
        run_playbook("playbook.yml", [], renderer, session_dir=tmp_path)
    session_id = next(tmp_path.iterdir()).name
    captured = capsys.readouterr().out
    return session_id, captured


def _replay_compact(session_id: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> str:
    """Replay through a fresh CompactRenderer; return captured stdout."""
    renderer = CompactRenderer(is_tty=False)
    replay_session(tmp_path, session_id, renderer, speed=0)
    return capsys.readouterr().out


def _record_live_json(
    events: list[dict], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> tuple[str, str]:
    renderer = JsonRenderer()
    cmd, args = _fake_ansible_command(events, exit_code=0)
    with (
        patch("ansible_aom.ansible.runner._build_command", return_value=(cmd, args)),
        patch("ansible_aom.ansible.runner.run_preflight", return_value=_empty_preflight()),
    ):
        run_playbook("playbook.yml", [], renderer, session_dir=tmp_path)
    session_id = next(tmp_path.iterdir()).name
    captured = capsys.readouterr().out
    return session_id, captured


def _replay_json(session_id: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> str:
    renderer = JsonRenderer()
    replay_session(tmp_path, session_id, renderer, speed=0)
    return capsys.readouterr().out


@pytest.mark.parametrize("name,events,_exit_code", EVENT_STREAMS, ids=EVENT_IDS)
def test_compact_record_then_replay_matches(
    name: str,
    events: list[dict],
    _exit_code: int,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Live compact stdout, normalised, must equal replayed compact stdout."""
    session_id, live_out = _record_live_compact(events, tmp_path, capsys)
    replay_out = _replay_compact(session_id, tmp_path, capsys)

    live_norm = normalize_render_output(live_out)
    replay_norm = normalize_render_output(replay_out)

    assert live_norm == replay_norm, (
        f"compact live vs replay mismatch for {name}:\n"
        f"--- live (normalised) ---\n{live_norm!r}\n"
        f"--- replay (normalised) ---\n{replay_norm!r}"
    )


@pytest.mark.parametrize("name,events,_exit_code", EVENT_STREAMS, ids=EVENT_IDS)
def test_compact_replay_is_idempotent(
    name: str,
    events: list[dict],
    _exit_code: int,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Replaying the same session twice produces byte-identical output."""
    session_id, _ = _record_live_compact(events, tmp_path, capsys)

    first = _replay_compact(session_id, tmp_path, capsys)
    second = _replay_compact(session_id, tmp_path, capsys)

    first_norm = normalize_render_output(first)
    second_norm = normalize_render_output(second)
    assert first_norm == second_norm, f"two replays of the same session diverged for {name}"


@pytest.mark.parametrize("name,events,_exit_code", EVENT_STREAMS, ids=EVENT_IDS)
def test_json_record_then_replay_matches(
    name: str,
    events: list[dict],
    _exit_code: int,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Live JSON summary, normalised, must equal replayed JSON summary.

    Only the run-specific timestamp fields (``started_at`` /
    ``ended_at`` / ``duration_s``) are normalised. Everything else —
    host counts, exit_code, tasks_failed — must match exactly.
    """
    session_id, live_out = _record_live_json(events, tmp_path, capsys)
    replay_out = _replay_json(session_id, tmp_path, capsys)

    live_norm = normalize_json_summary(live_out)
    replay_norm = normalize_json_summary(replay_out)
    assert live_norm == replay_norm, (
        f"JSON live vs replay mismatch for {name}:\n  live:   {live_norm}\n  replay: {replay_norm}"
    )
