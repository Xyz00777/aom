"""Integration tests for the runner's session recording (roadmap #14).

Every `run_playbook` invocation creates a session directory under the
state dir, recording JSONL events, meta, and any stderr so that
`aom inspect` can re-open the run afterwards.

These tests substitute a fake ansible-playbook executable (a small
Python one-liner that prints canned JSONL) so the wiring can be
exercised without needing a real Ansible install.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch


def _fake_ansible_command(events: list[dict], exit_code: int = 0) -> tuple[str, list[str]]:
    """(command, args) pair emitting `events` then exiting with `exit_code`."""
    payload = json.dumps(events)
    code = (
        "import json, sys; "
        f"events = json.loads({payload!r}); "
        "[sys.stdout.write(json.dumps(e) + '\\n') for e in events]; "
        "sys.stdout.flush(); "
        f"sys.exit({exit_code})"
    )
    return sys.executable, ["-c", code]


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


class TestSessionRecordingHappyPath:
    """A normal run produces a session directory with events + meta."""

    def test_creates_session_directory_with_events_and_meta(self, tmp_path: Path) -> None:
        from ansible_aom.runner import run_playbook

        renderer = MagicMock()
        cmd, args = _fake_ansible_command(
            [
                {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-08T10:00:00Z"},
                {"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:01Z"},
            ],
            exit_code=0,
        )

        with patch("ansible_aom.runner._build_command", return_value=(cmd, args)):
            exit_code = run_playbook("playbook.yml", [], renderer, session_dir=tmp_path)

        assert exit_code == 0
        sessions = list(tmp_path.iterdir())
        assert len(sessions) == 1, f"expected 1 session dir, got {sessions}"
        session_path = sessions[0]
        assert (session_path / "events.jsonl").exists()
        assert (session_path / "meta.json").exists()
        assert (session_path / "stderr.log").exists()

    def test_records_every_jsonl_event_seen_by_runner(self, tmp_path: Path) -> None:
        from ansible_aom.runner import run_playbook

        renderer = MagicMock()
        events = [
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-08T10:00:00Z"},
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-08T10:00:00Z",
                "play": {"id": "p1", "name": "Test"},
            },
            {"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:01Z"},
        ]
        cmd, args = _fake_ansible_command(events, exit_code=0)

        with patch("ansible_aom.runner._build_command", return_value=(cmd, args)):
            run_playbook("playbook.yml", [], renderer, session_dir=tmp_path)

        session_path = next(tmp_path.iterdir())
        recorded = _read_jsonl(session_path / "events.jsonl")
        assert [e["_event"] for e in recorded] == [
            "v2_playbook_on_start",
            "v2_playbook_on_play_start",
            "v2_playbook_on_stats",
        ]

    def test_meta_records_status_completed_on_success(self, tmp_path: Path) -> None:
        from ansible_aom.runner import run_playbook

        renderer = MagicMock()
        cmd, args = _fake_ansible_command(
            [{"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:01Z"}],
            exit_code=0,
        )

        with patch("ansible_aom.runner._build_command", return_value=(cmd, args)):
            run_playbook("playbook.yml", [], renderer, session_dir=tmp_path)

        session_path = next(tmp_path.iterdir())
        meta = json.loads((session_path / "meta.json").read_text())
        assert meta["status"] == "completed"
        assert meta["playbook"] == "playbook.yml"
        assert meta["session_id"]
        assert meta["start_time"]
        assert meta["end_time"]

    def test_meta_records_status_failed_on_nonzero_exit(self, tmp_path: Path) -> None:
        from ansible_aom.runner import run_playbook

        renderer = MagicMock()
        cmd, args = _fake_ansible_command(
            [{"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:01Z"}],
            exit_code=2,
        )

        with patch("ansible_aom.runner._build_command", return_value=(cmd, args)):
            exit_code = run_playbook("playbook.yml", [], renderer, session_dir=tmp_path)

        assert exit_code == 2
        session_path = next(tmp_path.iterdir())
        meta = json.loads((session_path / "meta.json").read_text())
        assert meta["status"] == "failed"


class TestSessionRecordingFailureModes:
    """Recording is best-effort — disk failures don't crash the run."""

    def test_unwritable_session_dir_does_not_crash_run(self, tmp_path: Path) -> None:
        """If session_dir can't be written to, the playbook still runs and exits cleanly."""
        from ansible_aom.runner import run_playbook

        # Point session_dir at a file instead of a directory: trying to
        # create subdirs underneath will OSError. The runner must absorb
        # that and complete normally.
        blocker = tmp_path / "not-a-dir"
        blocker.write_text("blocked")

        renderer = MagicMock()
        cmd, args = _fake_ansible_command(
            [{"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:01Z"}],
            exit_code=0,
        )

        with patch("ansible_aom.runner._build_command", return_value=(cmd, args)):
            exit_code = run_playbook("playbook.yml", [], renderer, session_dir=blocker)

        # The run itself still succeeds.
        assert exit_code == 0
        renderer.handle_completion.assert_called_once()


class TestSessionRecordingDefaults:
    """When no session_dir is passed, the runner picks the standard state dir."""

    def test_default_state_dir_is_used_when_none_given(self, tmp_path: Path) -> None:
        """run_playbook must produce a session under the spec-standard default
        when no override is supplied; we patch home() to keep the test clean."""
        from ansible_aom.runner import run_playbook

        renderer = MagicMock()
        cmd, args = _fake_ansible_command(
            [{"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:01Z"}],
            exit_code=0,
        )

        with (
            patch("ansible_aom.runner._build_command", return_value=(cmd, args)),
            patch("ansible_aom.runner.Path.home", return_value=tmp_path),
        ):
            run_playbook("playbook.yml", [], renderer)

        default_dir = tmp_path / ".local" / "state" / "aom" / "sessions"
        assert default_dir.exists()
        sessions = list(default_dir.iterdir())
        assert len(sessions) == 1
