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
