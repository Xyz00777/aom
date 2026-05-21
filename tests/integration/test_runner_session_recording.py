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

import pytest


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
        from ansible_aom.ansible.runner import run_playbook

        renderer = MagicMock()
        cmd, args = _fake_ansible_command(
            [
                {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-08T10:00:00Z"},
                {"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:01Z"},
            ],
            exit_code=0,
        )

        with patch("ansible_aom.ansible.runner._build_command", return_value=(cmd, args)):
            exit_code = run_playbook("playbook.yml", [], renderer, session_dir=tmp_path)

        assert exit_code == 0
        sessions = list(tmp_path.iterdir())
        assert len(sessions) == 1, f"expected 1 session dir, got {sessions}"
        session_path = sessions[0]
        assert (session_path / "events.jsonl").exists()
        assert (session_path / "meta.json").exists()
        assert (session_path / "stderr.log").exists()

    def test_records_every_jsonl_event_seen_by_runner(self, tmp_path: Path) -> None:
        from ansible_aom.ansible.runner import run_playbook

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

        with patch("ansible_aom.ansible.runner._build_command", return_value=(cmd, args)):
            run_playbook("playbook.yml", [], renderer, session_dir=tmp_path)

        session_path = next(tmp_path.iterdir())
        recorded = _read_jsonl(session_path / "events.jsonl")
        assert [e["_event"] for e in recorded] == [
            "v2_playbook_on_start",
            "v2_playbook_on_play_start",
            "v2_playbook_on_stats",
        ]

    def test_meta_records_status_completed_on_success(self, tmp_path: Path) -> None:
        from ansible_aom.ansible.runner import run_playbook

        renderer = MagicMock()
        cmd, args = _fake_ansible_command(
            [{"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:01Z"}],
            exit_code=0,
        )

        with patch("ansible_aom.ansible.runner._build_command", return_value=(cmd, args)):
            run_playbook("playbook.yml", [], renderer, session_dir=tmp_path)

        session_path = next(tmp_path.iterdir())
        meta = json.loads((session_path / "meta.json").read_text())
        assert meta["status"] == "completed"
        assert meta["playbook"] == "playbook.yml"
        assert meta["session_id"]
        assert meta["start_time"]
        assert meta["end_time"]

    def test_meta_records_status_failed_on_nonzero_exit(self, tmp_path: Path) -> None:
        from ansible_aom.ansible.runner import run_playbook

        renderer = MagicMock()
        cmd, args = _fake_ansible_command(
            [{"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:01Z"}],
            exit_code=2,
        )

        with patch("ansible_aom.ansible.runner._build_command", return_value=(cmd, args)):
            exit_code = run_playbook("playbook.yml", [], renderer, session_dir=tmp_path)

        assert exit_code == 2
        session_path = next(tmp_path.iterdir())
        meta = json.loads((session_path / "meta.json").read_text())
        assert meta["status"] == "failed"


class TestSessionRecordingFailureModes:
    """Recording is best-effort — disk failures don't crash the run."""

    def test_unwritable_session_dir_does_not_crash_run(self, tmp_path: Path) -> None:
        """If session_dir can't be written to, the playbook still runs and exits cleanly."""
        from ansible_aom.ansible.runner import run_playbook

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

        with patch("ansible_aom.ansible.runner._build_command", return_value=(cmd, args)):
            exit_code = run_playbook("playbook.yml", [], renderer, session_dir=blocker)

        # The run itself still succeeds.
        assert exit_code == 0
        renderer.handle_completion.assert_called_once()


class TestSessionRecordingDisableOnDiskError:
    """R3: an OSError mid-run (disk full, FS quota, NFS hiccup) disables
    further recording without flooding logs and surfaces a one-time
    warning so the user sees what happened — without losing the run."""

    def test_oserror_during_record_event_disables_sink_and_warns_once(self, tmp_path: Path) -> None:
        from ansible_aom.ansible.runner import run_playbook

        renderer = MagicMock()

        events = [
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-08T10:00:00Z"},
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-08T10:00:00Z",
                "play": {"id": "p1", "name": "Test"},
            },
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-08T10:00:00Z",
                "task": {"id": "t1", "name": "t1"},
            },
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-05-08T10:00:00Z",
                "task": {"id": "t1"},
                "hosts": {"web1": {"ok": True}},
            },
            {"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:01Z"},
        ]
        cmd, args = _fake_ansible_command(events, exit_code=0)

        original_record = None
        call_count = {"n": 0}

        def fail_after_two(self, session_id, event):
            call_count["n"] += 1
            if call_count["n"] > 2:
                raise OSError("No space left on device")
            assert original_record is not None
            return original_record(self, session_id, event)

        from ansible_aom.session.store import SessionManager

        original_record = SessionManager.record_event

        with (
            patch("ansible_aom.ansible.runner._build_command", return_value=(cmd, args)),
            patch.object(SessionManager, "record_event", fail_after_two),
        ):
            exit_code = run_playbook("playbook.yml", [], renderer, session_dir=tmp_path)

        # Run still completes cleanly.
        assert exit_code == 0
        renderer.handle_completion.assert_called_once()

        # Only the first two events made it to disk.
        session_path = next(tmp_path.iterdir())
        recorded = _read_jsonl(session_path / "events.jsonl")
        assert len(recorded) == 2

        # Renderer warned exactly once about disabled recording.
        warning_calls = [
            call
            for call in renderer.add_warning.call_args_list
            if "session recording disabled" in str(call).lower()
        ]
        assert len(warning_calls) == 1, (
            f"expected one 'session recording disabled' warning, "
            f"got {renderer.add_warning.call_args_list}"
        )


class TestSessionRecordingDefaults:
    """When no session_dir is passed, the runner picks the standard state dir."""

    def test_default_state_dir_is_used_when_none_given(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """run_playbook must produce a session under whatever the
        ``_default_session_dir`` helper returns when no override is
        supplied. The autouse isolation fixture monkeypatches that
        helper to a per-test tmp dir; we override it again here to
        point at this test's ``tmp_path`` so we can assert against it.
        """
        from ansible_aom.ansible.runner import run_playbook

        default_dir = tmp_path / ".local" / "state" / "aom" / "sessions"
        monkeypatch.setattr("ansible_aom.ansible.runner._default_session_dir", lambda: default_dir)

        renderer = MagicMock()
        cmd, args = _fake_ansible_command(
            [{"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:01Z"}],
            exit_code=0,
        )

        with patch("ansible_aom.ansible.runner._build_command", return_value=(cmd, args)):
            run_playbook("playbook.yml", [], renderer)

        assert default_dir.exists()
        sessions = list(default_dir.iterdir())
        assert len(sessions) == 1


class TestSessionRecordingPersistsArgs:
    """The runner must forward its ansible_args into meta.json (schema 1.1)."""

    def test_runner_records_ansible_args_in_meta(self, tmp_path: Path) -> None:
        """run_playbook persists the ansible_args it was invoked with into meta.json."""
        from ansible_aom.ansible.runner import run_playbook

        renderer = MagicMock()
        cmd, args = _fake_ansible_command(
            [{"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:01Z"}],
            exit_code=0,
        )

        with patch("ansible_aom.ansible.runner._build_command", return_value=(cmd, args)):
            run_playbook(
                "site.yml",
                ["-i", "inv.ini", "--tags", "web"],
                renderer,
                session_dir=tmp_path,
            )

        sessions = [p for p in tmp_path.iterdir() if p.is_dir()]
        assert len(sessions) == 1
        meta = json.loads((sessions[0] / "meta.json").read_text())
        assert meta["ansible_args"] == ["-i", "inv.ini", "--tags", "web"]
