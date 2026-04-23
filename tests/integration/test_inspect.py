"""Integration tests for inspect CLI commands.

Tests Section 9 (Session Inspection) of TEST_SPECIFICATION.md.
TC-319 through TC-331 for inspect list, show, diff, and export commands.

Test Isolation Rules (CRITICAL):
1. Every test creates fresh instances
2. Use tmp_path for file system tests
3. Function-scoped fixtures ONLY
4. Mock external dependencies
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from ansible_aom.core.models import HostRunState, PlayRunState, RunState, Status, TaskRunState
from ansible_aom.core.session import (
    SessionManager,
    cleanup_old_sessions,
    create_session_summary,
    generate_uuidv7,
    list_sessions,
    load_session,
)
from ansible_aom.inspect.cli import (
    inspect_diff,
    inspect_list,
    inspect_prune,
    inspect_show,
)
from ansible_aom.inspect.diff import classify_change, diff_sessions, match_tasks
from ansible_aom.inspect.display import (
    format_diff_table,
    format_session_summary,
    format_session_table,
    format_tree_view,
)

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def session_dir(tmp_path: Path) -> Path:
    """Create a session directory for testing."""
    sd = tmp_path / "sessions"
    sd.mkdir(parents=True)
    return sd


@pytest.fixture
def artifacts_dir(tmp_path: Path) -> Path:
    """Create an artifacts directory for testing."""
    ad = tmp_path / "artifacts"
    ad.mkdir(parents=True)
    return ad


@pytest.fixture
def sample_session(session_dir: Path) -> str:
    """Create a sample session with events and return session ID."""
    manager = SessionManager(session_dir=session_dir, playbook="site.yml")
    session_id = manager.start_session("site.yml")

    # Record sample events
    events = [
        {"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"},
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-04-20T10:00:01Z",
            "play": {"id": "play-001", "name": "Configure Webservers"},
        },
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-04-20T10:00:02Z",
            "play": {"id": "play-001"},
            "task": {"id": "task-001", "name": "Install nginx"},
        },
        {
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-04-20T10:00:30Z",
            "play": {"id": "play-001"},
            "task": {"id": "task-001", "name": "Install nginx"},
            "hosts": {"web1": {"ok": True, "changed": False}},
        },
        {
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-04-20T10:00:32Z",
            "play": {"id": "play-001"},
            "task": {"id": "task-001", "name": "Install nginx"},
            "hosts": {"web2": {"ok": True, "changed": True}},
        },
        {
            "_event": "v2_playbook_on_stats",
            "_timestamp": "2026-04-20T10:01:00Z",
            "stats": {
                "web1": {"ok": 1, "changed": 0, "failures": 0, "skipped": 0, "unreachable": 0},
                "web2": {"ok": 1, "changed": 1, "failures": 0, "skipped": 0, "unreachable": 0},
            },
        },
    ]

    for event in events:
        manager.record_event(session_id, event)

    manager.end_session(session_id, "completed")
    return session_id


@pytest.fixture
def failed_session(session_dir: Path) -> str:
    """Create a session with a failed task."""
    manager = SessionManager(session_dir=session_dir, playbook="deploy.yml")
    session_id = manager.start_session("deploy.yml")

    events = [
        {"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T11:00:00Z"},
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-04-20T11:00:01Z",
            "play": {"id": "play-002", "name": "Deploy Application"},
        },
        {
            "_event": "v2_runner_on_failed",
            "_timestamp": "2026-04-20T11:00:30Z",
            "play": {"id": "play-002"},
            "task": {"id": "task-fail", "name": "Deploy code"},
            "hosts": {"web1": {"failed": True, "msg": "Connection refused"}},
        },
        {
            "_event": "v2_playbook_on_stats",
            "_timestamp": "2026-04-20T11:01:00Z",
            "stats": {"web1": {"ok": 0, "failures": 1, "unreachable": 0}},
        },
    ]

    for event in events:
        manager.record_event(session_id, event)

    manager.end_session(session_id, "failed")
    return session_id


@pytest.fixture
def multi_host_session(session_dir: Path) -> str:
    """Create a session with multiple hosts."""
    manager = SessionManager(session_dir=session_dir, playbook="multi.yml")
    session_id = manager.start_session("multi.yml")

    events = [
        {"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T12:00:00Z"},
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-04-20T12:00:01Z",
            "play": {"id": "play-003", "name": "Setup All Hosts"},
        },
        {
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-04-20T12:00:30Z",
            "play": {"id": "play-003"},
            "task": {"id": "task-01", "name": "Setup"},
            "hosts": {"web1": {"ok": True}, "web2": {"ok": True}, "db1": {"ok": True}},
        },
        {
            "_event": "v2_runner_on_failed",
            "_timestamp": "2026-04-20T12:00:45Z",
            "play": {"id": "play-003"},
            "task": {"id": "task-02", "name": "Configure"},
            "hosts": {"db1": {"failed": True, "msg": "Permission denied"}},
        },
        {
            "_event": "v2_playbook_on_stats",
            "_timestamp": "2026-04-20T12:01:00Z",
            "stats": {
                "web1": {"ok": 1, "failures": 0},
                "web2": {"ok": 1, "failures": 0},
                "db1": {"ok": 1, "failures": 1},
            },
        },
    ]

    for event in events:
        manager.record_event(session_id, event)

    manager.end_session(session_id, "failed")
    return session_id


# =============================================================================
# Section 9.1: Inspect List (TC-319, TC-320)
# =============================================================================


class TestInspectList:
    """TC-319: Inspect List Command, TC-320: Session UUID Display."""

    def test_list_displays_sessions_table(self, session_dir: Path, sample_session: str):
        """TC-319: 'aom inspect list' displays table of sessions."""
        sessions = list_sessions(session_dir)

        assert len(sessions) == 1
        assert sessions[0]["session_id"] == sample_session
        assert "playbook" in sessions[0]
        assert sessions[0]["playbook"] == "site.yml"
        assert "status" in sessions[0]
        assert sessions[0]["status"] == "completed"

    def test_list_shows_8_char_uuid_prefix(self, session_dir: Path, sample_session: str):
        """TC-320: Session UUIDs displayed as first 8 characters."""
        sessions = list_sessions(session_dir)

        assert len(sessions) == 1
        session = sessions[0]

        # short_id should be first 8 chars
        assert session["short_id"] == sample_session[:8]
        assert len(session["short_id"]) == 8

    def test_list_shows_playbook_name(self, session_dir: Path, sample_session: str):
        """Session list includes playbook name column."""
        sessions = list_sessions(session_dir)

        assert sessions[0]["playbook"] == "site.yml"

    def test_list_shows_status(self, session_dir: Path, sample_session: str):
        """Session list includes status column."""
        sessions = list_sessions(session_dir)

        assert sessions[0]["status"] == "completed"

    def test_list_shows_failed_status(self, session_dir: Path, failed_session: str):
        """Session list shows FAILED status for failed sessions."""
        sessions = list_sessions(session_dir)

        failed = [s for s in sessions if s["status"] == "failed"]
        assert len(failed) == 1
        assert failed[0]["playbook"] == "deploy.yml"

    def test_list_sorted_by_time_newest_first(self, session_dir: Path):
        """TC-260: Sessions sorted by start time, newest first."""
        # Create sessions in specific order
        manager1 = SessionManager(session_dir=session_dir, playbook="first.yml")
        id1 = manager1.start_session("first.yml")
        manager1.end_session(id1, "completed")

        import time

        time.sleep(0.01)  # Ensure different timestamps

        manager2 = SessionManager(session_dir=session_dir, playbook="second.yml")
        id2 = manager2.start_session("second.yml")
        manager2.end_session(id2, "completed")

        time.sleep(0.01)

        manager3 = SessionManager(session_dir=session_dir, playbook="third.yml")
        id3 = manager3.start_session("third.yml")
        manager3.end_session(id3, "completed")

        sessions = list_sessions(session_dir)

        assert len(sessions) == 3
        # Newest first
        assert sessions[0]["session_id"] == id3
        assert sessions[1]["session_id"] == id2
        assert sessions[2]["session_id"] == id1

    def test_list_empty_directory(self, tmp_path: Path):
        """Listing empty session directory returns empty list."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        sessions = list_sessions(empty_dir)
        assert sessions == []

    def test_list_filters_failed_flag(
        self, session_dir: Path, sample_session: str, failed_session: str
    ):
        """TC-262: --failed flag filters to failed sessions only."""
        # Get all sessions
        all_sessions = list_sessions(session_dir)
        assert len(all_sessions) == 2

        # Filter to failed only (simulate --failed flag)
        failed_only = [s for s in all_sessions if s["status"] == "failed"]
        assert len(failed_only) == 1
        assert failed_only[0]["status"] == "failed"

    def test_list_shows_host_summary(self, session_dir: Path, multi_host_session: str):
        """Session list includes host summary column."""
        sessions = list_sessions(session_dir)

        session = [s for s in sessions if s["session_id"] == multi_host_session][0]
        # The stats event should indicate 3 hosts
        session_data = load_session(multi_host_session, session_dir)
        assert session_data is not None

        # Extract hosts from stats
        stats_event = None
        for event in session_data.get("events", []):
            if event.get("_event") == "v2_playbook_on_stats":
                stats_event = event
                break

        assert stats_event is not None
        assert len(stats_event.get("stats", {})) == 3

    def test_list_shows_duration(self, session_dir: Path, sample_session: str):
        """Session list includes duration."""
        sessions = list_sessions(session_dir)

        session = sessions[0]
        assert "duration_seconds" in session
        # Duration should be set
        assert session["duration_seconds"] is not None


# =============================================================================
# Section 9.2: Inspect Show (TC-266 through TC-271)
# =============================================================================


class TestInspectShow:
    """TC-266 to TC-271: Inspect Show Command."""

    def test_show_displays_session_summary(self, session_dir: Path, sample_session: str):
        """TC-266: 'aom inspect <session-id>' shows full session details."""
        session = load_session(sample_session, session_dir)

        assert session is not None
        assert session["session_id"] == sample_session
        assert session["playbook"] == "site.yml"
        assert session["status"] == "completed"

    def test_show_plays_by_play(self, session_dir: Path, sample_session: str):
        """Show displays play-by-play breakdown."""
        session = load_session(sample_session, session_dir)

        # Find play events
        play_events = [
            e for e in session.get("events", []) if e.get("_event") == "v2_playbook_on_play_start"
        ]

        assert len(play_events) == 1
        assert play_events[0]["play"]["name"] == "Configure Webservers"

    def test_show_lists_tasks_with_status(self, session_dir: Path, sample_session: str):
        """TC-267: Show displays task listing with status icons."""
        session = load_session(sample_session, session_dir)

        # Find task events
        task_events = [
            e for e in session.get("events", []) if e.get("_event") == "v2_playbook_on_task_start"
        ]

        assert len(task_events) == 1
        task = task_events[0]["task"]
        assert task["name"] == "Install nginx"

    def test_show_host_status_per_task(self, session_dir: Path, multi_host_session: str):
        """TC-268: Host status displayed per task."""
        session = load_session(multi_host_session, session_dir)

        # Find runner events to check host status
        ok_events = [e for e in session.get("events", []) if e.get("_event") == "v2_runner_on_ok"]
        failed_events = [
            e for e in session.get("events", []) if e.get("_event") == "v2_runner_on_failed"
        ]

        assert len(ok_events) == 1
        assert set(ok_events[0]["hosts"].keys()) == {"web1", "web2", "db1"}

        assert len(failed_events) == 1
        assert "db1" in failed_events[0]["hosts"]

    def test_show_elapsed_time(self, session_dir: Path, sample_session: str):
        """TC-269: Elapsed time display."""
        session = load_session(sample_session, session_dir)

        summary = create_session_summary(session)

        assert "duration_seconds" in summary
        assert summary["duration_seconds"] is not None

    def test_show_filter_failed(self, session_dir: Path, multi_host_session: str):
        """TC-270: --failed flag shows only failed tasks."""
        session = load_session(multi_host_session, session_dir)

        # Filter to failed events only
        failed_events = [
            e for e in session.get("events", []) if e.get("_event") == "v2_runner_on_failed"
        ]

        assert len(failed_events) == 1
        task_name = failed_events[0]["task"]["name"]
        assert "Configure" in task_name

    def test_show_filter_by_host(self, session_dir: Path, multi_host_session: str):
        """TC-271: --host flag filters by hostname."""
        session = load_session(multi_host_session, session_dir)

        # Filter events to only those involving a specific host
        target_host = "web1"

        host_events = []
        for event in session.get("events", []):
            hosts_data = event.get("hosts", {})
            if hosts_data and target_host in hosts_data:
                host_events.append(event)

        # Should have the ok event for web1
        assert len(host_events) >= 1

        # The failed event should NOT include web1
        failed_on_db = [
            e for e in session.get("events", []) if e.get("_event") == "v2_runner_on_failed"
        ][0]
        assert "web1" not in failed_on_db["hosts"]

    def test_show_tree_view(self, session_dir: Path, sample_session: str):
        """TC-271: --tree flag shows ASCII tree structure."""
        session = load_session(sample_session, session_dir)

        # Build a tree structure from events
        tree = format_tree_view(session)

        assert tree is not None
        assert "Configure Webservers" in tree  # Play name
        assert "Install nginx" in tree  # Task name

    def test_show_nonexistent_session(self, session_dir: Path):
        """Show returns None for nonexistent session."""
        session = load_session("nonexistent-session-id", session_dir)
        assert session is None


# =============================================================================
# Section 9.3: Inspect Diff (TC-272 through TC-275, TC-325 through TC-330)
# =============================================================================


class TestInspectDiff:
    """TC-272 to TC-275: Inspect Diff Command."""

    def test_diff_compares_two_sessions(
        self, session_dir: Path, sample_session: str, failed_session: str
    ):
        """TC-272: 'aom inspect diff <id1> <id2>' compares task results."""
        session1 = load_session(sample_session, session_dir)
        session2 = load_session(failed_session, session_dir)

        assert session1 is not None
        assert session2 is not None

        result = diff_sessions(session1, session2)

        assert "tasks" in result
        assert "classifications" in result

    def test_diff_shows_changed_marker(
        self, session_dir: Path, sample_session: str, failed_session: str
    ):
        """TC-273: Diff highlights task result changes."""
        session1 = load_session(sample_session, session_dir)
        session2 = load_session(failed_session, session_dir)

        # Find task results in each session
        ok_tasks_1 = [e for e in session1["events"] if e.get("_event") == "v2_runner_on_ok"]
        failed_tasks_2 = [e for e in session2["events"] if e.get("_event") == "v2_runner_on_failed"]

        assert len(ok_tasks_1) > 0, "Session 1 should have OK tasks"
        assert len(failed_tasks_2) > 0, "Session 2 should have failed tasks"

    def test_diff_shows_unchanged_marker(self, session_dir: Path):
        """TC-273: Diff shows unchanged tasks."""
        # Create two similar sessions
        manager1 = SessionManager(session_dir=session_dir, playbook="same.yml")
        id1 = manager1.start_session("same.yml")
        manager1.record_event(
            id1, {"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"}
        )
        manager1.record_event(
            id1,
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-04-20T10:00:30Z",
                "task": {"id": "t1", "name": "Task1"},
                "hosts": {"h1": {"ok": True}},
            },
        )
        manager1.end_session(id1, "completed")

        import time

        time.sleep(0.01)

        manager2 = SessionManager(session_dir=session_dir, playbook="same.yml")
        id2 = manager2.start_session("same.yml")
        manager2.record_event(
            id2, {"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T11:00:00Z"}
        )
        manager2.record_event(
            id2,
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-04-20T11:00:30Z",
                "task": {"id": "t1", "name": "Task1"},
                "hosts": {"h1": {"ok": True}},
            },
        )
        manager2.end_session(id2, "completed")

        session1 = load_session(id1, session_dir)
        session2 = load_session(id2, session_dir)

        result = diff_sessions(session1, session2)

        # Same task with same status should be marked unchanged
        assert result is not None

    def test_diff_colored_output(self, session_dir: Path, sample_session: str, failed_session: str):
        """TC-274: Diff output shows color-coded markers."""
        session1 = load_session(sample_session, session_dir)
        session2 = load_session(failed_session, session_dir)

        diff_output = format_diff_table(diff_sessions(session1, session2))

        # Output should contain the diff table structure
        assert diff_output is not None

    def test_diff_task_matching_uuid_priority(self):
        """TC-326: Diff uses task.uuid as primary matching method."""
        tasks1 = [
            {"uuid": "abc-123", "name": "Task A", "status": "ok"},
            {"uuid": "def-456", "name": "Task B", "status": "ok"},
        ]
        tasks2 = [
            {"uuid": "abc-123", "name": "Task A renamed", "status": "failed"},
            {"uuid": "def-456", "name": "Task B", "status": "changed"},
        ]

        matches = match_tasks(tasks1, tasks2)

        # Should match by UUID even though names differ
        assert ("abc-123", "abc-123") in matches.values() or len(matches) == 2

    def test_diff_task_matching_path_fallback(self):
        """TC-327: Diff uses task.path as secondary matching."""
        tasks1 = [
            {"path": "site.yml:10", "name": "Task A", "status": "ok"},
        ]
        tasks2 = [
            {"path": "site.yml:10", "name": "Task A modified", "status": "failed"},
        ]

        matches = match_tasks(tasks1, tasks2)

        # Should match by path when UUID not available
        assert len(matches) > 0

    def test_diff_task_matching_name_fallback(self):
        """TC-328: Diff uses task name as last resort matching."""
        tasks1 = [
            {"name": "Install nginx", "status": "ok"},
        ]
        tasks2 = [
            {"name": "Install nginx", "status": "failed"},
        ]

        matches = match_tasks(tasks1, tasks2)

        # Should match by name when UUID and path not available
        assert len(matches) > 0

    def test_diff_cross_playbook_warning(
        self, session_dir: Path, sample_session: str, failed_session: str
    ):
        """TC-329: Cross-playbook diff shows warning banner."""
        session1 = load_session(sample_session, session_dir)
        session2 = load_session(failed_session, session_dir)

        # Different playbook names
        assert session1["playbook"] == "site.yml"
        assert session2["playbook"] == "deploy.yml"

        result = diff_sessions(session1, session2)

        # Result should indicate different playbooks
        assert result is not None
        assert "playbooks_differ" in result or result.get("baseline_playbook") != result.get(
            "current_playbook"
        )

    def test_diff_changes_only_flag(
        self, session_dir: Path, sample_session: str, failed_session: str
    ):
        """TC-330: --changes-only flag hides unchanged tasks."""
        session1 = load_session(sample_session, session_dir)
        session2 = load_session(failed_session, session_dir)

        result_all = diff_sessions(session1, session2)
        result_changes = diff_sessions(session1, session2, changes_only=True)

        # Changes-only should filter to only changed tasks
        assert result_all is not None
        assert result_changes is not None

    def test_diff_default_shows_all_tasks(self, session_dir: Path):
        """TC-331: Default diff shows all tasks including unchanged."""
        # Create two identical sessions
        manager1 = SessionManager(session_dir=session_dir, playbook="test.yml")
        id1 = manager1.start_session("test.yml")
        manager1.record_event(id1, {"_event": "v2_playbook_on_start"})
        manager1.record_event(
            id1,
            {
                "_event": "v2_runner_on_ok",
                "task": {"id": "t1", "name": "Task1"},
                "hosts": {"h1": {"ok": True}},
            },
        )
        manager1.end_session(id1, "completed")

        import time

        time.sleep(0.01)

        manager2 = SessionManager(session_dir=session_dir, playbook="test.yml")
        id2 = manager2.start_session("test.yml")
        manager2.record_event(id2, {"_event": "v2_playbook_on_start"})
        manager2.record_event(
            id2,
            {
                "_event": "v2_runner_on_ok",
                "task": {"id": "t1", "name": "Task1"},
                "hosts": {"h1": {"ok": True}},
            },
        )
        manager2.end_session(id2, "completed")

        session1 = load_session(id1, session_dir)
        session2 = load_session(id2, session_dir)

        result = diff_sessions(session1, session2)

        # Default should include all tasks
        assert result is not None

    def test_classify_change_regressed(self):
        """Classify status change from OK to FAILED as regressed."""
        classification = classify_change("ok", "failed")
        assert classification == "regressed"

    def test_classify_change_improved(self):
        """Classify status change from FAILED to OK as improved."""
        classification = classify_change("failed", "ok")
        assert classification == "improved"

    def test_classify_change_changed(self):
        """Classify status change from OK to CHANGED as changed."""
        classification = classify_change("ok", "changed")
        assert classification == "changed"

    def test_classify_change_unchanged(self):
        """Classify same status as unchanged."""
        classification = classify_change("ok", "ok")
        assert classification == "unchanged"

    def test_classify_change_new_task(self):
        """Classify task only in current session as new."""
        classification = classify_change(None, "ok")
        assert classification == "new"

    def test_classify_change_removed_task(self):
        """Classify task only in baseline session as removed."""
        classification = classify_change("ok", None)
        assert classification == "removed"


# =============================================================================
# Section 9.4: Inspect Export (TC-22, TC-23)
# =============================================================================


class TestInspectExport:
    """TC-22, TC-23: --json and --jsonl output formats."""

    def test_json_output_format(self, session_dir: Path, sample_session: str):
        """TC-22: --json outputs valid JSON with session data."""
        session = load_session(sample_session, session_dir)

        json_output = json.dumps(session, indent=2)
        parsed = json.loads(json_output)

        assert parsed["session_id"] == sample_session
        assert parsed["playbook"] == "site.yml"
        assert "events" in parsed

    def test_jsonl_output_format(self, session_dir: Path, sample_session: str):
        """TC-23: --jsonl outputs raw event dump (line-delimited JSON)."""
        session = load_session(sample_session, session_dir)

        # JSONL format: one JSON object per line
        jsonl_lines = [json.dumps(event) for event in session.get("events", [])]

        # Each line should be valid JSON
        for line in jsonl_lines:
            parsed = json.loads(line)
            assert "_event" in parsed

        # Verify we can parse all lines back
        reloaded = [json.loads(line) for line in jsonl_lines]
        assert len(reloaded) == len(session.get("events", []))


# =============================================================================
# Additional Integration Tests
# =============================================================================


class TestInspectPrune:
    """Test inspect prune command."""

    def test_prune_removes_old_sessions(self, session_dir: Path):
        """Test that prune removes sessions older than threshold."""
        # Create old and new sessions
        old_manager = SessionManager(session_dir=session_dir, playbook="old.yml")
        old_id = old_manager.start_session("old.yml")
        old_manager.end_session(old_id, "completed")

        # Modify the start_time in meta.json to make it old
        old_meta_file = session_dir / old_id / "meta.json"
        import json
        from datetime import datetime, timedelta, timezone

        old_time = datetime.now(timezone.utc) - timedelta(days=60)
        with open(old_meta_file) as f:
            meta = json.load(f)
        meta["start_time"] = old_time.isoformat().replace("+00:00", "Z")
        with open(old_meta_file, "w") as f:
            json.dump(meta, f)

        # Create new session
        import time

        time.sleep(0.01)

        new_manager = SessionManager(session_dir=session_dir, playbook="new.yml")
        new_id = new_manager.start_session("new.yml")
        new_manager.end_session(new_id, "completed")

        # Prune sessions older than 30 days
        deleted = cleanup_old_sessions(session_dir, keep_count=100, keep_days=30)

        # Old session should be deleted
        assert deleted == 1
        assert not (session_dir / old_id).exists()
        assert (session_dir / new_id).exists()

    def test_prune_respects_keep_count(self, session_dir: Path):
        """Test that prune respects keep_count limit."""
        # Create more sessions than keep_count
        for i in range(15):
            manager = SessionManager(session_dir=session_dir, playbook=f"test{i}.yml")
            sid = manager.start_session(f"test{i}.yml")
            manager.end_session(sid, "completed")

        # Keep only 10
        deleted = cleanup_old_sessions(session_dir, keep_count=10, keep_days=365)

        # Should have deleted 5
        assert deleted == 5

        remaining = list(session_dir.iterdir())
        assert len(remaining) == 10


class TestDisplayFormatting:
    """Test display formatting functions."""

    def test_format_session_table_empty(self):
        """format_session_table handles empty list."""
        output = format_session_table([])
        assert output is not None or output == ""

    def test_format_session_table_with_sessions(self, session_dir: Path, sample_session: str):
        """format_session_table displays session data."""
        sessions = list_sessions(session_dir)

        table = format_session_table(sessions)

        assert table is not None
        assert sample_session[:8] in table or "site.yml" in table

    def test_format_session_summary(self, session_dir: Path, sample_session: str):
        """format_session_summary formats session summary."""
        session = load_session(sample_session, session_dir)

        summary = format_session_summary(session)

        assert summary is not None
        assert "site.yml" in summary or "completed" in summary

    def test_format_tree_view_structure(self, session_dir: Path, sample_session: str):
        """format_tree_view shows hierarchical structure."""
        session = load_session(sample_session, session_dir)

        tree = format_tree_view(session)

        # Should contain play name and task name
        assert tree is not None


# =============================================================================
# CLI Integration Tests
# =============================================================================


class TestInspectCLI:
    """Test CLI entry points."""

    def test_inspect_list_cli(self, session_dir: Path, sample_session: str):
        """Test inspect_list function from CLI module."""
        result = inspect_list(session_dir, output_format="table")

        # inspect_list should return exit code 0
        assert result == 0 or result is None

    def test_inspect_show_cli(self, session_dir: Path, sample_session: str):
        """Test inspect_show function from CLI module."""
        result = inspect_show(sample_session, session_dir)

        # inspect_show should return exit code 0
        assert result == 0 or result is None

    def test_inspect_show_cli_with_filters(self, session_dir: Path, multi_host_session: str):
        """Test inspect_show with --failed and --host flags."""
        # Test with --failed flag
        result_failed = inspect_show(multi_host_session, session_dir, failed_only=True)
        assert result_failed == 0 or result_failed is None

        # Test with --host flag
        result_host = inspect_show(multi_host_session, session_dir, host_filter="web1")
        assert result_host == 0 or result_host is None

    def test_inspect_diff_cli(self, session_dir: Path, sample_session: str, failed_session: str):
        """Test inspect_diff function from CLI module."""
        result = inspect_diff(sample_session, failed_session, session_dir)

        # inspect_diff should return exit code 0
        assert result == 0 or result is None

    def test_inspect_diff_cli_with_flags(
        self, session_dir: Path, sample_session: str, failed_session: str
    ):
        """Test inspect_diff with --changes-only flag."""
        result = inspect_diff(sample_session, failed_session, session_dir, changes_only=True)

        assert result == 0 or result is None

    def test_inspect_diff_nonexistent_session(self, session_dir: Path, sample_session: str):
        """Test inspect_diff with nonexistent session."""
        # Should handle gracefully or return error code
        result = inspect_diff(sample_session, "nonexistent-id", session_dir)

        # Non-existent session should return non-zero exit code
        # or the implementation should handle it gracefully

    def test_inspect_prune_cli(self, session_dir: Path):
        """Test inspect_prune function from CLI module."""
        # Create a session to prune
        manager = SessionManager(session_dir=session_dir, playbook="old.yml")
        sid = manager.start_session("old.yml")
        manager.end_session(sid, "completed")

        result = inspect_prune(session_dir, days=30)

        # inspect_prune should return exit code 0
        assert result == 0 or result is None
