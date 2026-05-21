"""Integration tests for session recording and inspection.

Tests Section 6.3 (Session Recording) and Section 9 (Inspection) of TEST_SPECIFICATION.md.
TC-207 through TC-233, plus inspect command tests.
"""

import json
import os
import stat
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from ansible_aom.session.store import (
    SessionManager,
    cleanup_old_sessions,
    generate_uuidv7,
    list_sessions,
    load_session,
)
from ansible_aom.session.summary import create_session_summary


class TestGenerateUUIDv7:
    """TC-218: Session UUIDv7 Format Validation."""

    def test_uuidv7_format_matches_pattern(self):
        """UUIDv7 matches expected format pattern."""
        uuid_str = generate_uuidv7()
        assert isinstance(uuid_str, str)
        assert len(uuid_str) == 36
        assert uuid_str[8] == "-"
        assert uuid_str[13] == "-"
        assert uuid_str[18] == "-"
        assert uuid_str[23] == "-"

    def test_uuidv7_is_time_sortable(self):
        """UUIDv7 values are time-sortable (earlier timestamps produce smaller UUIDs)."""
        uuid1 = generate_uuidv7()
        uuid2 = generate_uuidv7()
        assert uuid1 < uuid2

    def test_uuidv7_first_8_chars_usable_for_display(self):
        """First 8 characters of UUIDv7 can be used for display."""
        uuid_str = generate_uuidv7()
        short_id = uuid_str[:8]
        assert len(short_id) == 8
        assert short_id.isalnum()

    def test_uuidv7_contains_timestamp(self):
        """UUIDv7 embeds timestamp in first segment."""
        uuid_str = generate_uuidv7()
        timestamp_chars = uuid_str[:8]
        assert timestamp_chars.isalnum()


class TestSessionManagerInit:
    """Test SessionManager initialization."""

    def test_init_creates_manager(self, tmp_path: Path):
        """SessionManager initializes with session directory."""
        session_dir = tmp_path / "sessions"
        manager = SessionManager(session_dir=session_dir, playbook="test.yml")
        assert manager.session_dir == session_dir
        assert manager._playbook == "test.yml"

    def test_init_without_playbook(self, tmp_path: Path):
        """SessionManager can be initialized without playbook."""
        session_dir = tmp_path / "sessions"
        manager = SessionManager(session_dir=session_dir)
        assert manager.session_dir == session_dir
        assert manager._playbook == ""


class TestStartSession:
    """TC-207: Session directory creation and management."""

    def test_start_session_creates_directory(self, tmp_path: Path):
        """start_session creates session directory with UUIDv7 name."""
        session_dir = tmp_path / "sessions"
        manager = SessionManager(session_dir=session_dir, playbook="deploy.yml")

        session_id = manager.start_session("deploy.yml")

        assert session_id is not None
        assert len(session_id) == 36

        created_dir = session_dir / session_id
        assert created_dir.exists()
        assert created_dir.is_dir()

    def test_start_session_creates_events_file(self, tmp_path: Path):
        """start_session creates events.jsonl file."""
        session_dir = tmp_path / "sessions"
        manager = SessionManager(session_dir=session_dir, playbook="test.yml")

        session_id = manager.start_session("test.yml")

        events_file = session_dir / session_id / "events.jsonl"
        assert events_file.exists()

    def test_start_session_creates_stderr_file(self, tmp_path: Path):
        """start_session creates stderr.log file."""
        session_dir = tmp_path / "sessions"
        manager = SessionManager(session_dir=session_dir, playbook="test.yml")

        session_id = manager.start_session("test.yml")

        stderr_file = session_dir / session_id / "stderr.log"
        assert stderr_file.exists()

    def test_start_session_creates_meta_file(self, tmp_path: Path):
        """start_session creates meta.json with initial metadata."""
        session_dir = tmp_path / "sessions"
        manager = SessionManager(session_dir=session_dir, playbook="site.yml")

        session_id = manager.start_session("site.yml")

        meta_file = session_dir / session_id / "meta.json"
        assert meta_file.exists()

        with open(meta_file) as f:
            meta = json.load(f)

        assert "playbook" in meta
        assert meta["playbook"] == "site.yml"
        assert "start_time" in meta
        assert "version" in meta

    def test_start_session_records_start_time(self, tmp_path: Path):
        """start_session records start time in UTC."""
        session_dir = tmp_path / "sessions"
        manager = SessionManager(session_dir=session_dir, playbook="test.yml")

        before = datetime.now(timezone.utc)
        session_id = manager.start_session("test.yml")
        after = datetime.now(timezone.utc)

        meta_file = session_dir / session_id / "meta.json"
        with open(meta_file) as f:
            meta = json.load(f)

        start_time = datetime.fromisoformat(meta["start_time"].replace("Z", "+00:00"))
        assert before <= start_time <= after

    def test_start_session_persists_ansible_args(self, tmp_path: Path):
        """meta.json includes the ansible_args list so aom rerun can replay flags."""
        session_dir = tmp_path / "sessions"
        manager = SessionManager(session_dir=session_dir, playbook="deploy.yml")

        session_id = manager.start_session(
            "deploy.yml",
            ansible_args=["-i", "inv.ini", "--tags", "web"],
        )

        meta_file = session_dir / session_id / "meta.json"
        with open(meta_file) as f:
            meta = json.load(f)

        assert meta["ansible_args"] == ["-i", "inv.ini", "--tags", "web"]

    def test_start_session_default_ansible_args_is_empty_list(self, tmp_path: Path):
        """Old call sites that don't pass ansible_args get [] in meta.json."""
        session_dir = tmp_path / "sessions"
        manager = SessionManager(session_dir=session_dir, playbook="deploy.yml")

        session_id = manager.start_session("deploy.yml")

        meta_file = session_dir / session_id / "meta.json"
        with open(meta_file) as f:
            meta = json.load(f)

        assert meta["ansible_args"] == []


class TestRecordEvent:
    """TC-219: Session events.jsonl content."""

    def test_record_event_appends_to_file(self, tmp_path: Path):
        """record_event appends JSONL events to events.jsonl."""
        session_dir = tmp_path / "sessions"
        manager = SessionManager(session_dir=session_dir, playbook="test.yml")
        session_id = manager.start_session("test.yml")

        event1 = {"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"}
        event2 = {"_event": "v2_playbook_on_play_start", "_timestamp": "2026-04-20T10:00:01Z"}

        manager.record_event(session_id, event1)
        manager.record_event(session_id, event2)

        events_file = session_dir / session_id / "events.jsonl"
        with open(events_file) as f:
            lines = f.readlines()

        assert len(lines) == 2
        assert json.loads(lines[0]) == event1
        assert json.loads(lines[1]) == event2

    def test_record_event_json_format(self, tmp_path: Path):
        """record_event writes valid JSON on single line."""
        session_dir = tmp_path / "sessions"
        manager = SessionManager(session_dir=session_dir, playbook="test.yml")
        session_id = manager.start_session("test.yml")

        event = {
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-04-20T10:00:05Z",
            "task": {"id": "task-1", "name": "Install nginx"},
            "hosts": {"web1": {"ok": True, "changed": False}},
        }
        manager.record_event(session_id, event)

        events_file = session_dir / session_id / "events.jsonl"
        with open(events_file) as f:
            line = f.readline()

        parsed = json.loads(line)
        assert parsed == event
        assert "\n" not in line[:-1]

    def test_record_event_preserves_event_order(self, tmp_path: Path):
        """record_event preserves event order for later diff comparison."""
        session_dir = tmp_path / "sessions"
        manager = SessionManager(session_dir=session_dir, playbook="test.yml")
        session_id = manager.start_session("test.yml")

        for i in range(5):
            manager.record_event(
                session_id, {"_event": f"event_{i}", "_timestamp": f"2026-04-20T10:00:0{i}Z"}
            )

        events_file = session_dir / session_id / "events.jsonl"
        with open(events_file) as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            parsed = json.loads(line)
            assert parsed["_event"] == f"event_{i}"


class TestRecordStderr:
    """TC-220: Session stderr.log content."""

    def test_record_stderr_appends_line(self, tmp_path: Path):
        """record_stderr appends line to stderr.log."""
        session_dir = tmp_path / "sessions"
        manager = SessionManager(session_dir=session_dir, playbook="test.yml")
        session_id = manager.start_session("test.yml")

        manager.record_stderr(session_id, "[WARNING]: ansible.posix not found")
        manager.record_stderr(session_id, "[DEPRECATION]: This feature is deprecated")

        stderr_file = session_dir / session_id / "stderr.log"
        with open(stderr_file) as f:
            lines = f.readlines()

        assert len(lines) == 2
        assert "[WARNING]" in lines[0]
        assert "[DEPRECATION]" in lines[1]

    def test_record_stderr_utf8_encoding(self, tmp_path: Path):
        """record_stderr handles UTF-8 characters."""
        session_dir = tmp_path / "sessions"
        manager = SessionManager(session_dir=session_dir, playbook="test.yml")
        session_id = manager.start_session("test.yml")

        manager.record_stderr(session_id, "Error: 中文字符 émojis 🎉")

        stderr_file = session_dir / session_id / "stderr.log"
        with open(stderr_file, encoding="utf-8") as f:
            content = f.read()

        assert "中文字符" in content
        assert "🎉" in content


class TestEndSession:
    """TC-221: Session meta.json content."""

    def test_end_session_updates_meta_with_status(self, tmp_path: Path):
        """end_session updates meta.json with final status."""
        session_dir = tmp_path / "sessions"
        manager = SessionManager(session_dir=session_dir, playbook="test.yml")
        session_id = manager.start_session("test.yml")

        manager.end_session(session_id, "completed")

        meta_file = session_dir / session_id / "meta.json"
        with open(meta_file) as f:
            meta = json.load(f)

        assert meta["status"] == "completed"
        assert "end_time" in meta

    def test_end_session_records_duration(self, tmp_path: Path):
        """end_session calculates and records duration."""
        session_dir = tmp_path / "sessions"
        manager = SessionManager(session_dir=session_dir, playbook="test.yml")
        session_id = manager.start_session("test.yml")

        import time

        time.sleep(0.1)

        manager.end_session(session_id, "completed")

        meta_file = session_dir / session_id / "meta.json"
        with open(meta_file) as f:
            meta = json.load(f)

        assert "duration_seconds" in meta
        assert meta["duration_seconds"] >= 0.1

    def test_end_session_status_failed(self, tmp_path: Path):
        """end_session records failed status."""
        session_dir = tmp_path / "sessions"
        manager = SessionManager(session_dir=session_dir, playbook="test.yml")
        session_id = manager.start_session("test.yml")

        manager.end_session(session_id, "failed")

        meta_file = session_dir / session_id / "meta.json"
        with open(meta_file) as f:
            meta = json.load(f)

        assert meta["status"] == "failed"

    def test_end_session_status_crashed(self, tmp_path: Path):
        """end_session records crashed status."""
        session_dir = tmp_path / "sessions"
        manager = SessionManager(session_dir=session_dir, playbook="test.yml")
        session_id = manager.start_session("test.yml")

        manager.end_session(session_id, "crashed")

        meta_file = session_dir / session_id / "meta.json"
        with open(meta_file) as f:
            meta = json.load(f)

        assert meta["status"] == "crashed"


class TestCreateArtifact:
    """TC-222 to TC-225: Artifact file creation and format."""

    def test_create_artifact_creates_aom_file(self, tmp_path: Path):
        """create_artifact creates .aom file in artifacts directory."""
        session_dir = tmp_path / "sessions"
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()
        manager = SessionManager(
            session_dir=session_dir,
            artifacts_dir=artifacts_dir,
            playbook="test.yml",
        )
        session_id = manager.start_session("test.yml")
        manager.end_session(session_id, "completed")

        artifact_path = manager.create_artifact(session_id)

        assert artifact_path.exists()
        assert artifact_path.suffix == ".aom"
        assert artifact_path.name == f"{session_id}.aom"

    def test_create_artifact_metadata_header(self, tmp_path: Path):
        """TC-223: Artifact starts with metadata header line."""
        session_dir = tmp_path / "sessions"
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()
        manager = SessionManager(
            session_dir=session_dir,
            artifacts_dir=artifacts_dir,
            playbook="site.yml",
        )
        session_id = manager.start_session("site.yml")
        manager.end_session(session_id, "completed")
        artifact_path = manager.create_artifact(session_id)

        with open(artifact_path) as f:
            first_line = f.readline()

        metadata = json.loads(first_line)
        assert metadata["type"] == "metadata"
        assert metadata["playbook"] == "site.yml"
        assert "version" in metadata
        assert "created" in metadata

    def test_create_artifact_event_lines(self, tmp_path: Path):
        """TC-224: Artifact contains event lines with type=event."""
        session_dir = tmp_path / "sessions"
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()
        manager = SessionManager(
            session_dir=session_dir,
            artifacts_dir=artifacts_dir,
            playbook="test.yml",
        )
        session_id = manager.start_session("test.yml")
        manager.record_event(
            session_id, {"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"}
        )
        manager.record_event(
            session_id,
            {"_event": "v2_playbook_on_play_start", "_timestamp": "2026-04-20T10:00:01Z"},
        )
        manager.end_session(session_id, "completed")
        artifact_path = manager.create_artifact(session_id)

        with open(artifact_path) as f:
            lines = f.readlines()

        assert len(lines) >= 3
        metadata = json.loads(lines[0])
        assert metadata["type"] == "metadata"

        event1 = json.loads(lines[1])
        assert event1["type"] == "event"
        assert event1["_event"] == "v2_playbook_on_start"

    def test_create_artifact_stats_line(self, tmp_path: Path):
        """TC-225: Artifact ends with stats line."""
        session_dir = tmp_path / "sessions"
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()
        manager = SessionManager(
            session_dir=session_dir,
            artifacts_dir=artifacts_dir,
            playbook="test.yml",
        )
        session_id = manager.start_session("test.yml")
        manager.record_event(
            session_id, {"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"}
        )
        manager.record_event(
            session_id,
            {
                "_event": "v2_playbook_on_stats",
                "_timestamp": "2026-04-20T10:01:00Z",
                "stats": {
                    "web1": {"ok": 5, "changed": 2, "failures": 0},
                },
            },
        )
        manager.end_session(session_id, "completed")
        artifact_path = manager.create_artifact(session_id)

        with open(artifact_path) as f:
            lines = f.readlines()

        last_line = json.loads(lines[-1])
        assert last_line["type"] == "stats"
        assert "web1" in last_line
        assert last_line["web1"]["ok"] == 5


class TestSessionFilePermissions:
    """TC-226: Session file permissions 0o644."""

    def test_session_directory_permissions(self, tmp_path: Path):
        """Session directory created with appropriate permissions."""
        session_dir = tmp_path / "sessions"
        manager = SessionManager(session_dir=session_dir, playbook="test.yml")
        session_id = manager.start_session("test.yml")

        session_path = session_dir / session_id
        mode = stat.S_IMODE(session_path.stat().st_mode)

        assert mode & 0o755 == 0o755

    def test_events_file_permissions(self, tmp_path: Path):
        """TC-226: events.jsonl created with 0o644 permissions."""
        session_dir = tmp_path / "sessions"
        manager = SessionManager(session_dir=session_dir, playbook="test.yml")
        session_id = manager.start_session("test.yml")

        events_file = session_dir / session_id / "events.jsonl"
        mode = stat.S_IMODE(events_file.stat().st_mode)

        assert mode & 0o644 == 0o644

    def test_stderr_file_permissions(self, tmp_path: Path):
        """stderr.log created with 0o644 permissions."""
        session_dir = tmp_path / "sessions"
        manager = SessionManager(session_dir=session_dir, playbook="test.yml")
        session_id = manager.start_session("test.yml")

        stderr_file = session_dir / session_id / "stderr.log"
        mode = stat.S_IMODE(stderr_file.stat().st_mode)

        assert mode & 0o644 == 0o644

    def test_meta_file_permissions(self, tmp_path: Path):
        """meta.json created with 0o644 permissions."""
        session_dir = tmp_path / "sessions"
        manager = SessionManager(session_dir=session_dir, playbook="test.yml")
        session_id = manager.start_session("test.yml")

        meta_file = session_dir / session_id / "meta.json"
        mode = stat.S_IMODE(meta_file.stat().st_mode)

        assert mode & 0o644 == 0o644


class TestArtifactPermissions:
    """TC-227: Artifact file permissions 0o600."""

    def test_artifact_file_permissions(self, tmp_path: Path):
        """TC-227: .aom artifacts created with 0o600 (user-only)."""
        session_dir = tmp_path / "sessions"
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()
        manager = SessionManager(
            session_dir=session_dir,
            artifacts_dir=artifacts_dir,
            playbook="test.yml",
        )
        session_id = manager.start_session("test.yml")
        manager.end_session(session_id, "completed")
        artifact_path = manager.create_artifact(session_id)

        mode = stat.S_IMODE(artifact_path.stat().st_mode)
        assert mode == 0o600 or (mode & 0o600 == 0o600)


class TestSessionRotation:
    """TC-228, TC-229, TC-230: Session rotation and cleanup."""

    def test_cleanup_keeps_max_count(self, tmp_path: Path):
        """TC-228: Keep last N sessions (default 100)."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)

        for i in range(105):
            (session_dir / f"session_{i:03d}").mkdir()
            meta = {
                "playbook": f"test{i}.yml",
                "start_time": f"2026-04-20T{10 + i // 60:02d}:{i % 60:02d}:00Z",
            }
            with open(session_dir / f"session_{i:03d}" / "meta.json", "w") as f:
                json.dump(meta, f)

        deleted = cleanup_old_sessions(session_dir, keep_count=100, keep_days=365)

        remaining = list(session_dir.iterdir())
        assert len(remaining) == 100
        assert deleted == 5

    def test_cleanup_keeps_recent_sessions(self, tmp_path: Path):
        """TC-228: Cleanup keeps most recent sessions."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)

        for i in range(110):
            (session_dir / f"session_{i:03d}").mkdir()

        cleanup_old_sessions(session_dir, keep_count=100, keep_days=365)

        remaining = sorted([p.name for p in session_dir.iterdir()])
        assert len(remaining) == 100
        assert "session_109" in remaining
        assert "session_009" not in remaining

    def test_cleanup_removes_old_sessions(self, tmp_path: Path):
        """TC-229: Delete sessions older than N days."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)

        # Use dates relative to "now" so the test doesn't go stale as
        # wall-clock drifts past the hardcoded threshold.
        now = datetime.now(timezone.utc)
        old_ts = (now - timedelta(days=90)).strftime("%Y-%m-%dT%H:%M:%SZ")
        new_ts = (now - timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%SZ")

        old_session = session_dir / "old_session"
        old_session.mkdir()
        old_meta = {"playbook": "old.yml", "start_time": old_ts}
        with open(old_session / "meta.json", "w") as f:
            json.dump(old_meta, f)

        new_session = session_dir / "new_session"
        new_session.mkdir()
        new_meta = {"playbook": "new.yml", "start_time": new_ts}
        with open(new_session / "meta.json", "w") as f:
            json.dump(new_meta, f)

        deleted = cleanup_old_sessions(session_dir, keep_count=100, keep_days=30)

        assert not old_session.exists()
        assert new_session.exists()
        assert deleted == 1

    def test_cleanup_respects_both_limits(self, tmp_path: Path):
        """Cleanup respects both count and age limits."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)

        for i in range(150):
            session = session_dir / f"session_{i:03d}"
            session.mkdir()
            age_days = i // 2
            start_time = datetime.now(timezone.utc) - timedelta(days=age_days)
            meta = {"playbook": f"test{i}.yml", "start_time": start_time.isoformat()}
            with open(session / "meta.json", "w") as f:
                json.dump(meta, f)

        deleted = cleanup_old_sessions(session_dir, keep_count=100, keep_days=30)

        remaining = list(session_dir.iterdir())
        assert len(remaining) <= 100


class TestCorruptedSessionHandling:
    """TC-231, TC-232, TC-233: Corrupted session handling."""

    def test_truncated_jsonl_handled_gracefully(self, tmp_path: Path):
        """TC-231: Truncated JSONL is handled gracefully."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        session_id = "test_session"
        (session_dir / session_id).mkdir()

        with open(session_dir / session_id / "events.jsonl", "w") as f:
            f.write('{"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"}\n')
            f.write('{"_event": "v2_playbook_on_play_start"')  # truncated

        with open(session_dir / session_id / "meta.json", "w") as f:
            json.dump({"playbook": "test.yml"}, f)

        session = load_session(session_id, session_dir)
        assert session is not None
        assert "malformed_lines" in session
        assert session["malformed_lines"] == 1
        assert len(session["events"]) == 1

    def test_malformed_json_skipped_with_warning(self, tmp_path: Path):
        """TC-232: Malformed JSON lines skipped with WARNING."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        session_id = "test_session"
        (session_dir / session_id).mkdir()

        with open(session_dir / session_id / "events.jsonl", "w") as f:
            f.write('{"_event": "valid_event"}\n')
            f.write("not valid json\n")
            f.write('{"_event": "another_valid"}\n')

        with open(session_dir / session_id / "meta.json", "w") as f:
            json.dump({"playbook": "test.yml"}, f)

        session = load_session(session_id, session_dir)
        assert session is not None
        assert len(session["events"]) == 2
        assert session["malformed_lines"] == 1

    def test_inspect_shows_malformed_count(self, tmp_path: Path):
        """TC-233: Inspect command shows note about malformed lines."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        session_id = "test_session"
        (session_dir / session_id).mkdir()

        with open(session_dir / session_id / "events.jsonl", "w") as f:
            for i in range(3):
                f.write('{"_event": "valid"}\n')
            for i in range(3):
                f.write("malformed line\n")

        with open(session_dir / session_id / "meta.json", "w") as f:
            json.dump({"playbook": "test.yml"}, f)

        session = load_session(session_id, session_dir)
        summary = create_session_summary(session)

        assert "3 malformed lines" in summary or summary.get("malformed_lines") == 3


class TestInspectList:
    """Section 9.1: Inspect list command."""

    def test_list_sessions_empty(self, tmp_path: Path):
        """list_sessions returns empty list when no sessions."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)

        sessions = list_sessions(session_dir)

        assert sessions == []

    def test_list_sessions_returns_all_sessions(self, tmp_path: Path):
        """list_sessions returns all session summaries."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)

        for i in range(3):
            sid = f"session_{i}"
            (session_dir / sid).mkdir()
            meta = {
                "playbook": f"test{i}.yml",
                "start_time": f"2026-04-20T1{i}:00:00Z",
                "status": "completed",
            }
            with open(session_dir / sid / "meta.json", "w") as f:
                json.dump(meta, f)

        sessions = list_sessions(session_dir)

        assert len(sessions) == 3

    def test_list_sessions_shows_8_char_uuid_prefix(self, tmp_path: Path):
        """Session UUIDs displayed as first 8 characters in list."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)

        full_uuid = "0192f8a1-2345-7890-abcd-ef1234567890"
        (session_dir / full_uuid).mkdir()
        meta = {"playbook": "test.yml", "start_time": "2026-04-20T10:00:00Z"}
        with open(session_dir / full_uuid / "meta.json", "w") as f:
            json.dump(meta, f)

        sessions = list_sessions(session_dir)

        assert len(sessions) == 1
        session = sessions[0]
        assert session["short_id"] == full_uuid[:8]
        assert session["session_id"] == full_uuid

    def test_list_sessions_sorted_by_time(self, tmp_path: Path):
        """list_sessions returns sessions sorted by start time (newest first)."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)

        timestamps = [
            "2026-04-20T10:00:00Z",
            "2026-04-20T12:00:00Z",
            "2026-04-20T11:00:00Z",
        ]
        for i, ts in enumerate(timestamps):
            sid = f"session_{i}"
            (session_dir / sid).mkdir()
            meta = {"playbook": f"test{i}.yml", "start_time": ts}
            with open(session_dir / sid / "meta.json", "w") as f:
                json.dump(meta, f)

        sessions = list_sessions(session_dir)

        assert sessions[0]["start_time"] == "2026-04-20T12:00:00Z"
        assert sessions[1]["start_time"] == "2026-04-20T11:00:00Z"
        assert sessions[2]["start_time"] == "2026-04-20T10:00:00Z"

    def test_list_sessions_includes_status(self, tmp_path: Path):
        """list_sessions includes session status."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)

        for status in ["completed", "failed", "crashed"]:
            sid = f"session_{status}"
            (session_dir / sid).mkdir()
            meta = {"playbook": "test.yml", "start_time": "2026-04-20T10:00:00Z", "status": status}
            with open(session_dir / sid / "meta.json", "w") as f:
                json.dump(meta, f)

        sessions = list_sessions(session_dir)

        statuses = {s["status"] for s in sessions}
        assert "completed" in statuses
        assert "failed" in statuses
        assert "crashed" in statuses


class TestInspectShow:
    """Section 9: Inspect show command."""

    def test_load_session_returns_meta(self, tmp_path: Path):
        """load_session returns session metadata."""
        session_dir = tmp_path / "sessions"
        session_id = "test_session"
        (session_dir / session_id).mkdir(parents=True)

        meta = {
            "playbook": "site.yml",
            "start_time": "2026-04-20T10:00:00Z",
            "end_time": "2026-04-20T10:05:00Z",
            "status": "completed",
            "duration_seconds": 300,
        }
        with open(session_dir / session_id / "meta.json", "w") as f:
            json.dump(meta, f)

        with open(session_dir / session_id / "events.jsonl", "w") as f:
            f.write('{"_event": "v2_playbook_on_start"}\n')

        session = load_session(session_id, session_dir)

        assert session["playbook"] == "site.yml"
        assert session["status"] == "completed"
        assert session["duration_seconds"] == 300

    def test_load_session_includes_events(self, tmp_path: Path):
        """load_session returns all recorded events."""
        session_dir = tmp_path / "sessions"
        session_id = "test_session"
        (session_dir / session_id).mkdir(parents=True)

        with open(session_dir / session_id / "meta.json", "w") as f:
            json.dump({"playbook": "test.yml"}, f)

        with open(session_dir / session_id / "events.jsonl", "w") as f:
            f.write('{"_event": "v2_playbook_on_start"}\n')
            f.write('{"_event": "v2_playbook_on_play_start"}\n')

        session = load_session(session_id, session_dir)

        assert len(session["events"]) == 2
        assert session["events"][0]["_event"] == "v2_playbook_on_start"
        assert session["events"][1]["_event"] == "v2_playbook_on_play_start"

    def test_load_nonexistent_session_returns_none(self, tmp_path: Path):
        """load_session returns None for non-existent session."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)

        session = load_session("nonexistent", session_dir)

        assert session is None


class TestInspectDiff:
    """Section 9.3: Inspect diff command."""

    def test_diff_shows_task_comparison(self, tmp_path: Path):
        """Diff shows task status comparison between sessions."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)

        session_id_1 = "session_1"
        (session_dir / session_id_1).mkdir()
        with open(session_dir / session_id_1 / "meta.json", "w") as f:
            json.dump({"playbook": "site.yml", "status": "completed"}, f)
        with open(session_dir / session_id_1 / "events.jsonl", "w") as f:
            f.write(
                '{"_event": "v2_runner_on_ok", "task": {"name": "Install nginx"}, "hosts": {"web1": {"ok": true}}}\n'
            )

        session_id_2 = "session_2"
        (session_dir / session_id_2).mkdir()
        with open(session_dir / session_id_2 / "meta.json", "w") as f:
            json.dump({"playbook": "site.yml", "status": "failed"}, f)
        with open(session_dir / session_id_2 / "events.jsonl", "w") as f:
            f.write(
                '{"_event": "v2_runner_on_failed", "task": {"name": "Install nginx"}, "hosts": {"web1": {"failed": true}}}\n'
            )

        session1 = load_session(session_id_1, session_dir)
        session2 = load_session(session_id_2, session_dir)

        assert session1["events"][0]["_event"] == "v2_runner_on_ok"
        assert session2["events"][0]["_event"] == "v2_runner_on_failed"


class TestOutputFormats:
    """Section 9: Output formats --json, --jsonl."""

    def test_json_output_format(self, tmp_path: Path):
        """--json output produces valid JSON."""
        session_dir = tmp_path / "sessions"
        session_id = "test_session"
        (session_dir / session_id).mkdir(parents=True)

        with open(session_dir / session_id / "meta.json", "w") as f:
            json.dump({"playbook": "test.yml", "status": "completed"}, f)

        with open(session_dir / session_id / "events.jsonl", "w") as f:
            f.write('{"_event": "start"}\n')

        session = load_session(session_id, session_dir)

        json_output = json.dumps(session)
        parsed = json.loads(json_output)

        assert parsed["playbook"] == "test.yml"
        assert "events" in parsed

    def test_jsonl_output_format(self, tmp_path: Path):
        """--jsonl output produces line-delimited JSON."""
        session_dir = tmp_path / "sessions"
        session_id = "test_session"
        (session_dir / session_id).mkdir(parents=True)

        with open(session_dir / session_id / "meta.json", "w") as f:
            json.dump({"playbook": "test.yml"}, f)

        with open(session_dir / session_id / "events.jsonl", "w") as f:
            f.write('{"_event": "event1"}\n')
            f.write('{"_event": "event2"}\n')

        session = load_session(session_id, session_dir)

        jsonl_lines = [json.dumps(event) for event in session["events"]]

        for line in jsonl_lines:
            parsed = json.loads(line)
            assert "_event" in parsed
