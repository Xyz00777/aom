"""Unit tests for the JSON output renderer (F6)."""

from __future__ import annotations


def test_run_summary_model_has_pinned_schema():
    """RunSummary captures every field the schema spec requires."""
    from ansible_aom.json_renderer import HostCounts, RunSummary, TaskFailure

    summary = RunSummary(
        schema_version=1,
        playbook="site.yml",
        exit_code=0,
        started_at="2026-05-12T10:30:00+00:00",
        ended_at="2026-05-12T10:30:42+00:00",
        duration_s=42.3,
        hosts={"web1": HostCounts(ok=1, changed=0, failed=0, unreachable=0)},
        tasks_failed=[TaskFailure(host="web2", task="install nginx", msg="boom")],
    )

    dumped = summary.model_dump()
    assert dumped["schema_version"] == 1
    assert dumped["playbook"] == "site.yml"
    assert dumped["exit_code"] == 0
    assert dumped["duration_s"] == 42.3
    assert dumped["hosts"] == {"web1": {"ok": 1, "changed": 0, "failed": 0, "unreachable": 0}}
    assert dumped["tasks_failed"] == [{"host": "web2", "task": "install nginx", "msg": "boom"}]


def test_run_summary_schema_version_is_literal_one():
    """schema_version refuses any value other than 1 — guards against accidental drift."""
    from pydantic import ValidationError

    from ansible_aom.json_renderer import RunSummary

    try:
        RunSummary.model_validate(
            {
                "schema_version": 2,
                "playbook": "site.yml",
                "exit_code": 0,
                "started_at": "2026-05-12T10:30:00+00:00",
                "ended_at": "2026-05-12T10:30:00+00:00",
                "duration_s": 0.0,
                "hosts": {},
                "tasks_failed": [],
            }
        )
    except ValidationError:
        return
    raise AssertionError("schema_version should be a Literal[1]")


def test_json_renderer_satisfies_renderer_protocol():
    """JsonRenderer is structurally a Renderer (runtime_checkable Protocol)."""
    from ansible_aom.json_renderer import JsonRenderer
    from ansible_aom.renderer.protocol import Renderer

    renderer = JsonRenderer()
    assert isinstance(renderer, Renderer)


def test_json_renderer_start_records_playbook_and_args():
    """start() captures the playbook path and ansible args without printing."""
    from ansible_aom.json_renderer import JsonRenderer

    renderer = JsonRenderer()
    renderer.start("site.yml", ["-i", "inv.ini"])
    assert renderer._playbook == "site.yml"
    assert renderer._args == ["-i", "inv.ini"]


def test_json_renderer_set_definitions_stores_them(capsys):
    """set_definitions stores the list and prints nothing."""
    from ansible_aom.json_renderer import JsonRenderer

    renderer = JsonRenderer()
    renderer.set_definitions([])
    assert renderer._definitions == []
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_json_renderer_noop_methods_emit_nothing(capsys):
    """add_warning, print_log, tick must not write to stdout/stderr in JSON mode."""
    from ansible_aom.json_renderer import JsonRenderer

    renderer = JsonRenderer()
    renderer.start("site.yml", [])
    renderer.add_warning("ignored", is_deprecation=False)
    renderer.add_warning("also ignored", is_deprecation=True)
    renderer.print_log("nothing to see")
    renderer.tick()
    renderer.stop()
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


# =============================================================================
# Task 3 tests: handle_completion JSON shape
# =============================================================================

import json  # noqa: E402
from datetime import datetime, timezone  # noqa: E402


def _state_two_hosts_one_failure():
    """web1: 2 ok + 1 changed; web2: 1 ok + 1 failed (msg='boom')."""
    from ansible_aom.core.models import (
        HostRunState,
        PlayRunState,
        RunState,
        Status,
        TaskRunState,
    )

    state = RunState(playbook="site.yml")
    play = PlayRunState(play_id="1", name="web", status=Status.RUNNING)

    t1 = TaskRunState(task_id="t1", name="gather facts")
    t1.hosts["web1"] = HostRunState(hostname="web1", status=Status.OK)
    t1.hosts["web2"] = HostRunState(hostname="web2", status=Status.OK)
    play.tasks["t1"] = t1

    t2 = TaskRunState(task_id="t2", name="install nginx")
    t2.hosts["web1"] = HostRunState(hostname="web1", status=Status.CHANGED, changed=True)
    t2.hosts["web2"] = HostRunState(hostname="web2", status=Status.FAILED, message="boom")
    play.tasks["t2"] = t2

    t3 = TaskRunState(task_id="t3", name="restart")
    t3.hosts["web1"] = HostRunState(hostname="web1", status=Status.OK)
    play.tasks["t3"] = t3

    state.plays["1"] = play
    state.start_time = datetime(2026, 5, 12, 10, 30, 0, tzinfo=timezone.utc)
    state.end_time = datetime(2026, 5, 12, 10, 30, 42, 300000, tzinfo=timezone.utc)
    return state


def test_handle_completion_emits_one_json_object(capsys):
    """The renderer prints exactly one JSON object on stdout."""
    from ansible_aom.json_renderer import JsonRenderer

    renderer = JsonRenderer()
    renderer.start("site.yml", [])
    renderer._state = _state_two_hosts_one_failure()
    renderer.handle_completion(1, "failed")

    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert isinstance(parsed, dict)


def test_handle_completion_schema_version_is_one(capsys):
    from ansible_aom.json_renderer import JsonRenderer

    renderer = JsonRenderer()
    renderer.start("site.yml", [])
    renderer._state = _state_two_hosts_one_failure()
    renderer.handle_completion(1, "failed")

    parsed = json.loads(capsys.readouterr().out)
    assert parsed["schema_version"] == 1


def test_handle_completion_records_playbook_and_exit_code(capsys):
    from ansible_aom.json_renderer import JsonRenderer

    renderer = JsonRenderer()
    renderer.start("site.yml", [])
    renderer._state = _state_two_hosts_one_failure()
    renderer.handle_completion(1, "failed")

    parsed = json.loads(capsys.readouterr().out)
    assert parsed["playbook"] == "site.yml"
    assert parsed["exit_code"] == 1


def test_handle_completion_uses_state_timestamps(capsys):
    """started_at / ended_at come from RunState when present."""
    from ansible_aom.json_renderer import JsonRenderer

    renderer = JsonRenderer()
    renderer.start("site.yml", [])
    renderer._state = _state_two_hosts_one_failure()
    renderer.handle_completion(1, "failed")

    parsed = json.loads(capsys.readouterr().out)
    assert parsed["started_at"] == "2026-05-12T10:30:00+00:00"
    assert parsed["ended_at"] == "2026-05-12T10:30:42.300000+00:00"
    assert parsed["duration_s"] == 42.3


def test_handle_completion_aggregates_per_host_counts(capsys):
    """Hosts dict has one entry per host with summed counts across tasks."""
    from ansible_aom.json_renderer import JsonRenderer

    renderer = JsonRenderer()
    renderer.start("site.yml", [])
    renderer._state = _state_two_hosts_one_failure()
    renderer.handle_completion(1, "failed")

    parsed = json.loads(capsys.readouterr().out)
    assert parsed["hosts"] == {
        "web1": {"ok": 2, "changed": 1, "failed": 0, "unreachable": 0},
        "web2": {"ok": 1, "changed": 0, "failed": 1, "unreachable": 0},
    }


def test_handle_completion_lists_failed_tasks(capsys):
    """tasks_failed names host, task, and the failure message."""
    from ansible_aom.json_renderer import JsonRenderer

    renderer = JsonRenderer()
    renderer.start("site.yml", [])
    renderer._state = _state_two_hosts_one_failure()
    renderer.handle_completion(1, "failed")

    parsed = json.loads(capsys.readouterr().out)
    assert parsed["tasks_failed"] == [{"host": "web2", "task": "install nginx", "msg": "boom"}]


def test_handle_completion_unreachable_lands_in_tasks_failed(capsys):
    """UNREACHABLE hosts also appear in tasks_failed."""
    from ansible_aom.core.models import (
        HostRunState,
        PlayRunState,
        RunState,
        Status,
        TaskRunState,
    )
    from ansible_aom.json_renderer import JsonRenderer

    state = RunState(playbook="site.yml")
    play = PlayRunState(play_id="1", name="p", status=Status.RUNNING)
    t1 = TaskRunState(task_id="t1", name="ping")
    t1.hosts["db1"] = HostRunState(
        hostname="db1", status=Status.UNREACHABLE, message="ssh timeout"
    )
    play.tasks["t1"] = t1
    state.plays["1"] = play
    state.start_time = datetime(2026, 5, 12, 10, 30, 0, tzinfo=timezone.utc)
    state.end_time = datetime(2026, 5, 12, 10, 30, 1, tzinfo=timezone.utc)

    renderer = JsonRenderer()
    renderer.start("site.yml", [])
    renderer._state = state
    renderer.handle_completion(2, "failed")

    parsed = json.loads(capsys.readouterr().out)
    assert parsed["exit_code"] == 2
    assert parsed["tasks_failed"] == [{"host": "db1", "task": "ping", "msg": "ssh timeout"}]
    assert parsed["hosts"] == {
        "db1": {"ok": 0, "changed": 0, "failed": 0, "unreachable": 1},
    }


def test_handle_completion_empty_state_emits_zero_exit(capsys):
    """An empty RunState produces a valid JSON with exit_code=0 and empty hosts."""
    from ansible_aom.json_renderer import JsonRenderer

    renderer = JsonRenderer()
    renderer.start("empty.yml", [])
    renderer.handle_completion(0, "completed")

    parsed = json.loads(capsys.readouterr().out)
    assert parsed["schema_version"] == 1
    assert parsed["playbook"] == "empty.yml"
    assert parsed["exit_code"] == 0
    assert parsed["hosts"] == {}
    assert parsed["tasks_failed"] == []
    datetime.fromisoformat(parsed["started_at"])
    datetime.fromisoformat(parsed["ended_at"])


def test_handle_completion_falls_back_to_wall_clock_when_state_lacks_timestamps(capsys):
    """When state.start_time / end_time are None we use wall clock."""
    from ansible_aom.core.models import (
        HostRunState,
        PlayRunState,
        RunState,
        Status,
        TaskRunState,
    )
    from ansible_aom.json_renderer import JsonRenderer

    state = RunState(playbook="site.yml")
    play = PlayRunState(play_id="1", name="p", status=Status.RUNNING)
    t1 = TaskRunState(task_id="t1", name="t")
    t1.hosts["h"] = HostRunState(hostname="h", status=Status.OK)
    play.tasks["t1"] = t1
    state.plays["1"] = play
    # Deliberately leave state.start_time / end_time as None.

    renderer = JsonRenderer()
    renderer.start("site.yml", [])
    renderer._state = state
    renderer.handle_completion(0, "completed")

    parsed = json.loads(capsys.readouterr().out)
    started = datetime.fromisoformat(parsed["started_at"])
    ended = datetime.fromisoformat(parsed["ended_at"])
    assert started.tzinfo is not None
    assert ended.tzinfo is not None
    assert parsed["duration_s"] >= 0.0


# =============================================================================
# Task 4 tests: factory dispatch
# =============================================================================


def test_factory_returns_json_renderer_for_json_format():
    from ansible_aom.json_renderer import JsonRenderer
    from ansible_aom.renderer.factory import create_renderer

    renderer = create_renderer(tui_mode=False, format="json")
    assert isinstance(renderer, JsonRenderer)


def test_factory_default_format_is_compact():
    from ansible_aom.compact.renderer import CompactRenderer
    from ansible_aom.renderer.factory import create_renderer

    renderer = create_renderer(tui_mode=False)
    assert isinstance(renderer, CompactRenderer)


def test_factory_compact_format_explicit_returns_compact_renderer():
    from ansible_aom.compact.renderer import CompactRenderer
    from ansible_aom.renderer.factory import create_renderer

    renderer = create_renderer(tui_mode=False, format="compact")
    assert isinstance(renderer, CompactRenderer)


def test_factory_tui_mode_still_wins_over_format():
    """tui_mode=True returns AOMApp regardless of format (CLI prevents this combo)."""
    from ansible_aom.renderer.factory import create_renderer
    from ansible_aom.tui.app import AOMApp

    renderer = create_renderer(tui_mode=True, format="json")
    assert isinstance(renderer, AOMApp)


# =============================================================================
# Task 6 tests: end-to-end smoke through Renderer lifecycle
# =============================================================================


def test_json_renderer_through_full_lifecycle(capsys):
    """Drive JsonRenderer through the same call sequence run_playbook uses."""
    from ansible_aom.json_renderer import JsonRenderer

    renderer = JsonRenderer()
    renderer.start("site.yml", ["-i", "inv.ini"])
    renderer.set_definitions([])

    # A minimal play_start → task_start → ok → stats sequence.
    renderer.update_state(
        {
            "_event": "v2_playbook_on_start",
            "_timestamp": "2026-05-12T10:30:00Z",
        }
    )
    renderer.update_state(
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-05-12T10:30:00Z",
            "play": {"id": "p1", "name": "web"},
        }
    )
    renderer.update_state(
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-05-12T10:30:01Z",
            "play": {"id": "p1", "name": "web"},
            "task": {"id": "t1", "name": "ping"},
        }
    )
    renderer.update_state(
        {
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-05-12T10:30:02Z",
            "play": {"id": "p1", "name": "web"},
            "task": {"id": "t1", "name": "ping"},
            "hosts": {"web1": {"changed": False}},
        }
    )
    renderer.update_state(
        {
            "_event": "v2_playbook_on_stats",
            "_timestamp": "2026-05-12T10:30:03Z",
            "stats": {"web1": {"ok": 1, "failures": 0, "unreachable": 0, "changed": 0}},
        }
    )

    renderer.handle_completion(0, "completed")
    renderer.stop()

    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert parsed["schema_version"] == 1
    assert parsed["playbook"] == "site.yml"
    assert parsed["exit_code"] == 0
    assert parsed["hosts"] == {
        "web1": {"ok": 1, "changed": 0, "failed": 0, "unreachable": 0},
    }
    assert parsed["tasks_failed"] == []
    assert parsed["started_at"].startswith("2026-05-12T10:30:00")
    assert parsed["ended_at"].startswith("2026-05-12T10:30:03")
    assert parsed["duration_s"] == 3.0


# =============================================================================
# Task 7 tests: interactive-prompt refusal behaviour
# =============================================================================


def test_password_prompt_refuses_to_stderr(capsys):
    """Password prompts under --format json are refused with empty string + stderr message."""
    from ansible_aom.json_renderer import JsonRenderer

    renderer = JsonRenderer()
    result = renderer.handle_password_prompt("BECOME password: ")

    assert result == ""
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "refusing" in captured.err.lower()
    assert "interactive prompt" in captured.err.lower()


def test_interactive_prompt_refuses_to_stderr(capsys):
    """Pause/vars_prompt prompts under --format json are also refused."""
    from ansible_aom.json_renderer import JsonRenderer

    renderer = JsonRenderer()
    result = renderer.handle_interactive_prompt("Press Enter to continue: ")

    assert result == ""
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "refusing" in captured.err.lower()


def test_prompt_refusal_does_not_corrupt_completion_json(capsys):
    """Even after a prompt refusal, handle_completion still emits valid JSON on stdout."""
    from ansible_aom.json_renderer import JsonRenderer

    renderer = JsonRenderer()
    renderer.start("site.yml", [])
    renderer.handle_password_prompt("BECOME password: ")
    renderer.handle_completion(2, "failed")

    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert parsed["schema_version"] == 1
    assert "refusing" in captured.err.lower()
