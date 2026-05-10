"""Tests for CompactRenderer.set_definitions (preflight result wiring)."""

from __future__ import annotations

from ansible_aom.compact.renderer import CompactRenderer
from ansible_aom.core.models import PlayDefinition, TaskDefinition


def _build_definitions() -> list[PlayDefinition]:
    return [
        PlayDefinition(
            id="1",
            name="Web setup",
            hosts="webservers",
            resolved_hosts=["web1", "web2"],
            tasks=[
                TaskDefinition(
                    name="install nginx",
                    role=None,
                    tags=[],
                    play_id="1",
                    play_order=1,
                    task_order=0,
                ),
            ],
        ),
        PlayDefinition(
            id="2",
            name="DB setup",
            hosts="dbservers",
            resolved_hosts=["db1"],
            tasks=[],
        ),
    ]


def test_set_definitions_stores_definitions_on_renderer():
    renderer = CompactRenderer(is_tty=False)
    renderer.start("site.yml", [])

    defs = _build_definitions()
    renderer.set_definitions(defs)

    assert renderer._definitions == defs


def test_set_definitions_updates_initial_hosts_total_in_status_bar(capsys):
    """After preflight, the status bar should show total resolved hosts immediately."""
    renderer = CompactRenderer(is_tty=False)
    renderer.start("site.yml", [])

    renderer.set_definitions(_build_definitions())
    renderer.handle_completion(0, "completed")

    captured = capsys.readouterr()
    # 2 hosts in play 1 + 1 in play 2 = 3 unique
    assert "0/3 hosts" in captured.out or "3/3 hosts" in captured.out


def test_set_definitions_called_before_start_is_safe():
    """Defensive: calling set_definitions before start should not crash."""
    renderer = CompactRenderer(is_tty=False)
    renderer.set_definitions(_build_definitions())
    assert renderer._definitions == _build_definitions()


def test_set_definitions_with_empty_list_keeps_zero_hosts(capsys):
    """Preflight failure path: empty definitions should not crash and leaves hosts at 0."""
    renderer = CompactRenderer(is_tty=False)
    renderer.start("site.yml", [])

    renderer.set_definitions([])
    renderer.handle_completion(0, "completed")

    captured = capsys.readouterr()
    assert "0/0 hosts" in captured.out


def test_set_definitions_prints_summary_above_status_panel(capsys):
    """The startup summary lands above the status panel via print_log."""
    renderer = CompactRenderer(is_tty=False)
    renderer.start("site.yml", [])

    renderer.set_definitions(_build_definitions())

    captured = capsys.readouterr()
    # Summary lines appear in stdout (non-TTY path prints them as plain text)
    assert "PLAY [Web setup]" in captured.out
    assert "PLAY [DB setup]" in captured.out


def test_set_definitions_with_empty_list_emits_no_summary(capsys):
    """Empty preflight result should not print a stray header."""
    renderer = CompactRenderer(is_tty=False)
    renderer.start("site.yml", [])

    renderer.set_definitions([])

    captured = capsys.readouterr()
    assert "PLAY [" not in captured.out


def test_set_definitions_unions_hosts_across_plays(capsys):
    """Hosts that appear in multiple plays count once each."""
    renderer = CompactRenderer(is_tty=False)
    renderer.start("site.yml", [])

    defs = [
        PlayDefinition(id="1", name="p1", hosts="all", resolved_hosts=["a", "b"]),
        PlayDefinition(id="2", name="p2", hosts="all", resolved_hosts=["b", "c"]),
    ]
    renderer.set_definitions(defs)
    renderer.handle_completion(0, "completed")

    captured = capsys.readouterr()
    assert "0/3 hosts" in captured.out
