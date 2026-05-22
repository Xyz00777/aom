"""On Ctrl-C / failure exit, the compact panel's tree + host overview
must persist as static text in the user's scrollback so the user can
inspect what was running at the moment of failure. Previously
``handle_completion`` called ``display.stop()`` which wiped the panel
unconditionally, leaving only the final status bar.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from ansible_aom.compact.renderer import CompactRenderer
from ansible_aom.core.models import (
    HostRunState,
    PlayDefinition,
    PlayRunState,
    Status,
    TaskDefinition,
    TaskRunState,
)


def _renderer_with_running_task() -> CompactRenderer:
    r = CompactRenderer(is_tty=False)
    r.start("site.yml", [])
    r._colorize = False
    r._display = MagicMock()
    # Real preflight + runtime so the tree has content.
    r._definitions = [
        PlayDefinition(
            id="1",
            name="deploy",
            hosts="all",
            resolved_hosts=["web1", "web2"],
            tasks=[
                TaskDefinition(
                    name="Install nginx",
                    role=None,
                    tags=[],
                    play_id="1",
                    play_order=0,
                    task_order=0,
                ),
                TaskDefinition(
                    name="Configure firewall",
                    role=None,
                    tags=[],
                    play_id="1",
                    play_order=0,
                    task_order=1,
                ),
            ],
        )
    ]
    assert r._state is not None
    r._state.definitions = r._definitions
    play = PlayRunState(play_id="p1", name="deploy", status=Status.RUNNING)
    task = TaskRunState(task_id="t1", name="Install nginx", status=Status.RUNNING)
    task.hosts["web1"] = HostRunState(hostname="web1", status=Status.RUNNING)
    task.hosts["web2"] = HostRunState(hostname="web2", status=Status.RUNNING)
    play.tasks["t1"] = task
    r._state.plays["p1"] = play
    return r


def test_tree_printed_after_cancel(capsys) -> None:
    """Exit 130 (Ctrl-C) → tree + host snapshot lands in scrollback."""
    r = _renderer_with_running_task()
    r.handle_completion(exit_code=130, state="crashed")
    out = capsys.readouterr().out
    # The currently-running task and the upcoming pending task must
    # both be present as static text.
    assert "Install nginx" in out, out
    assert "Configure firewall" in out, out


def test_tree_printed_after_failure(capsys) -> None:
    """Non-zero exit on a "failed" state preserves the panel too."""
    r = _renderer_with_running_task()
    r.handle_completion(exit_code=2, state="failed")
    out = capsys.readouterr().out
    assert "Install nginx" in out, out


def test_tree_not_duplicated_on_clean_exit(capsys) -> None:
    """A clean exit doesn't need the snapshot — the live panel was empty
    by that point anyway (run completed before this call) and the final
    summary plus per-host breakdown already tells the success story.
    Avoid printing a stale running-task snapshot in that case."""
    r = _renderer_with_running_task()
    r.handle_completion(exit_code=0, state="completed")
    out = capsys.readouterr().out
    # The currently-running task should NOT be re-printed for a clean
    # exit — by the time exit_code is 0 the run is fully finished and
    # the tree snapshot would be misleading (claiming a task is still
    # running when it isn't).
    # We expect the final status bar but not the snapshot lines.
    lines_with_task = [ln for ln in out.splitlines() if "Install nginx" in ln]
    assert lines_with_task == [], lines_with_task
