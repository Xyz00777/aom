"""Renderer wiring for the live run-duration estimate.

The renderer builds a :class:`RunEstimate` from the matching prior run,
accumulates covered prior wall on each task completion (keyed by
``task.path``), and feeds ``project_remaining`` into the status bar. Below
the warmup gate the bar is unchanged; once the gate opens it grows a
``~<dur> left`` annotation.
"""

from __future__ import annotations

from ansible_aom.compact.renderer import CompactRenderer
from ansible_aom.core.models import PlayDefinition, TaskDefinition
from ansible_aom.session.history import PriorRun


def _prior(task_wall: dict[str, float]) -> PriorRun:
    from datetime import datetime, timezone

    return PriorRun(
        session_id="prev",
        duration_seconds=sum(task_wall.values()),
        task_count=len(task_wall),
        host_count=1,
        end_time=datetime(2026, 6, 1, tzinfo=timezone.utc),
        task_wall_s=dict(task_wall),
        prior_wall_total_s=sum(task_wall.values()),
    )


class _FakeDisplay:
    def __init__(self) -> None:
        self.frames: list[str] = []

    def start(self) -> None: ...
    def stop(self) -> None: ...
    def print_log(self, message: str) -> None: ...
    def update(self, text: str) -> None:
        self.frames.append(text)


def _task(name: str, order: int) -> TaskDefinition:
    return TaskDefinition(
        name=name, role=None, tags=[], play_id="1", play_order=0, task_order=order
    )


def _complete_task(renderer: CompactRenderer, *, tid: str, name: str, path: str, ts: str) -> None:
    renderer.update_state(
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": ts,
            "task": {"id": tid, "name": name, "path": path},
            "play": {"id": "1"},
        }
    )
    renderer.update_state(
        {
            "_event": "v2_runner_on_ok",
            "_timestamp": ts,
            "task": {"id": tid, "name": name, "path": path},
            "play": {"id": "1"},
            "hosts": {"w1": {"changed": False}},
        }
    )


def _setup(monkeypatch, task_wall: dict[str, float]) -> tuple[CompactRenderer, _FakeDisplay]:
    renderer = CompactRenderer(is_tty=True)
    display = _FakeDisplay()
    monkeypatch.setattr(renderer, "_display", display)
    renderer.start("site.yml", [])
    renderer.set_prior_run(_prior(task_wall))
    play = PlayDefinition(
        id="1",
        name="web",
        hosts="webservers",
        resolved_hosts=["w1"],
        tasks=[_task("a", 0), _task("b", 1), _task("c", 2), _task("d", 3), _task("e", 4)],
    )
    renderer.set_definitions([play])
    renderer.update_state(
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "t",
            "play": {"id": "1", "name": "web"},
        }
    )
    return renderer, display


def test_no_eta_below_warmup_gate(monkeypatch) -> None:
    # 5 tasks × 10s = 50s prior. One completion = 1 matched task < min 2.
    renderer, display = _setup(monkeypatch, {f"site.yml:{i}": 10.0 for i in range(1, 6)})
    _complete_task(renderer, tid="t1", name="a", path="site.yml:1", ts="2026-06-02T10:00:00Z")
    renderer._last_panel_compute_time = 0.0
    renderer.tick()
    assert renderer._matched_tasks == 1
    assert all("left" not in f for f in display.frames), display.frames


def test_eta_appears_once_gate_opens(monkeypatch) -> None:
    renderer, display = _setup(monkeypatch, {f"site.yml:{i}": 10.0 for i in range(1, 6)})
    # Two completions → matched 2, covered 20s (40% of 50) → gate open.
    _complete_task(renderer, tid="t1", name="a", path="site.yml:1", ts="2026-06-02T10:00:00Z")
    _complete_task(renderer, tid="t2", name="b", path="site.yml:2", ts="2026-06-02T10:00:00Z")
    renderer._last_panel_compute_time = 0.0
    renderer.tick()
    assert renderer._matched_tasks == 2
    assert renderer._done_prior_s == 20.0
    assert any("left" in f for f in display.frames), display.frames


def test_unmatched_path_does_not_count(monkeypatch) -> None:
    renderer, _ = _setup(monkeypatch, {f"site.yml:{i}": 10.0 for i in range(1, 6)})
    _complete_task(renderer, tid="t1", name="a", path="site.yml:1", ts="2026-06-02T10:00:00Z")
    # A path absent from the prior profile (edited playbook) contributes 0.
    _complete_task(renderer, tid="t9", name="new", path="new.yml:99", ts="2026-06-02T10:00:00Z")
    assert renderer._matched_tasks == 1
    assert renderer._done_prior_s == 10.0


def test_long_running_task_burns_estimate_down(monkeypatch) -> None:
    # Regression: a long in-flight task used to *inflate* the ETA because
    # its known prior duration wasn't credited until completion. It must
    # now burn down. Profile: 3 short (5s) + 1 long (85s) = 100s.
    import ansible_aom.compact.renderer as rmod

    holder = {"t": 1000.0}
    monkeypatch.setattr(rmod.time, "time", lambda: holder["t"])

    renderer = CompactRenderer(is_tty=True)
    display = _FakeDisplay()
    monkeypatch.setattr(renderer, "_display", display)
    renderer.start("site.yml", [])  # _start_time captured at t=1000
    renderer.set_prior_run(_prior({"s1": 5.0, "s2": 5.0, "s3": 5.0, "long": 85.0}))
    play = PlayDefinition(
        id="1",
        name="web",
        hosts="all",
        resolved_hosts=["w1"],
        tasks=[_task("a", 0), _task("b", 1), _task("c", 2), _task("d", 3)],
    )
    renderer.set_definitions([play])
    renderer.update_state(
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "t",
            "play": {"id": "1", "name": "web"},
        }
    )

    # Three short tasks complete on pace → done_prior 15 (gate open).
    for i, (tid, path) in enumerate([("t1", "s1"), ("t2", "s2"), ("t3", "s3")]):
        holder["t"] = 1000.0 + (i + 1) * 5.0
        _complete_task(renderer, tid=tid, name=path, path=path, ts="2026-06-02T10:00:00Z")
    assert renderer._done_prior_s == 15.0

    # Long task starts (no completion yet) and runs for 40s.
    holder["t"] = 1015.0
    renderer.update_state(
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-06-02T10:00:15Z",
            "task": {"id": "tL", "name": "long", "path": "long"},
            "play": {"id": "1"},
        }
    )
    assert "tL" in renderer._running_task_starts
    holder["t"] = 1055.0  # 40s into the long task; elapsed 55s
    renderer._last_panel_compute_time = 0.0
    renderer.tick()
    # covered = 15 + min(40, 85) = 55; pace = 55/55 = 1; remaining = 100-55 = 45.
    assert any("~45s left" in f for f in display.frames), display.frames

    # Completing the long task pops it from the in-flight set.
    holder["t"] = 1100.0
    _complete_task(renderer, tid="tL", name="long", path="long", ts="2026-06-02T10:00:55Z")
    assert "tL" not in renderer._running_task_starts


def test_no_estimate_without_prior(monkeypatch) -> None:
    renderer = CompactRenderer(is_tty=True)
    display = _FakeDisplay()
    monkeypatch.setattr(renderer, "_display", display)
    renderer.start("site.yml", [])
    # No set_prior_run call at all.
    play = PlayDefinition(
        id="1", name="web", hosts="all", resolved_hosts=["w1"], tasks=[_task("a", 0)]
    )
    renderer.set_definitions([play])
    renderer.update_state(
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "t",
            "play": {"id": "1", "name": "web"},
        }
    )
    _complete_task(renderer, tid="t1", name="a", path="site.yml:1", ts="2026-06-02T10:00:00Z")
    renderer._last_panel_compute_time = 0.0
    renderer.tick()
    assert all("left" not in f for f in display.frames), display.frames
