"""Unit tests for verbose-panel session filtering."""

from ansible_aom.core.inspect_model import build_verbose_lines


def _session_with_verbose_events() -> dict:
    return {
        "events": [
            {"_event": "v2_playbook_on_play_start", "play": {"id": "play-1", "name": "Play One"}},
            {"_event": "v2_playbook_on_task_start", "task": {"id": "task-1", "name": "Task One"}},
            {
                "_event": "aom_connection_acquired",
                "connection_id": "conn-1",
                "task_id": "task-1",
                "host": "web1",
                "timestamp": "2026-07-01T10:00:00Z",
            },
            {
                "_event": "aom_stderr_line",
                "source": "run_level",
                "host": None,
                "level": 1,
                "line": "run line",
                "connection_id": None,
                "attribution_confidence": "unique",
            },
            {
                "_event": "aom_stderr_line",
                "source": "connection",
                "host": "web1",
                "level": 3,
                "line": "play one line",
                "connection_id": "conn-1",
                "attribution_confidence": "unique",
            },
            {
                "_event": "aom_stderr_line",
                "source": "connection",
                "host": "web1",
                "level": 3,
                "line": "ambiguous line",
                "connection_id": "conn-1",
                "attribution_confidence": "ambiguous",
            },
            {
                "_event": "v2_runner_on_ok",
                "task": {"id": "task-1", "name": "Task One"},
                "hosts": {"web1": {"changed": False}},
            },
            {
                "_event": "aom_connection_released",
                "connection_id": "conn-1",
                "task_id": "task-1",
                "host": "web1",
                "timestamp": "2026-07-01T10:00:05Z",
            },
            {"_event": "v2_playbook_on_play_start", "play": {"id": "play-2", "name": "Play Two"}},
            {"_event": "v2_playbook_on_task_start", "task": {"id": "task-2", "name": "Task Two"}},
            {
                "_event": "aom_connection_acquired",
                "connection_id": "conn-2",
                "task_id": "task-2",
                "host": "web2",
                "timestamp": "2026-07-01T10:00:06Z",
            },
            {
                "_event": "aom_stderr_line",
                "source": "connection",
                "host": "web2",
                "level": 3,
                "line": "play two line",
                "connection_id": "conn-2",
                "attribution_confidence": "unique",
            },
            {
                "_event": "v2_runner_on_ok",
                "task": {"id": "task-2", "name": "Task Two"},
                "hosts": {"web2": {"changed": False}},
            },
            {
                "_event": "aom_connection_released",
                "connection_id": "conn-2",
                "task_id": "task-2",
                "host": "web2",
                "timestamp": "2026-07-01T10:00:10Z",
            },
        ]
    }


def test_build_verbose_lines_filters_by_scope() -> None:
    session = _session_with_verbose_events()

    run_lines = build_verbose_lines(session, level="run")
    assert run_lines == ("run line",)

    play_lines = build_verbose_lines(session, level="play", play_name="Play One")
    assert play_lines == ("run line", "play one line", "? ambiguous line")
    assert "play two line" not in play_lines

    task_lines = build_verbose_lines(
        session,
        level="task",
        task_id="task-1",
        host="web1",
    )
    assert task_lines == ("run line", "play one line", "? ambiguous line")
    assert "play two line" not in task_lines


def test_build_verbose_lines_ignores_unmatched_play_task_lines() -> None:
    session = _session_with_verbose_events()

    assert build_verbose_lines(session, level="play", play_name="Play Two") == (
        "run line",
        "play two line",
    )
