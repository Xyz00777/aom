"""Renderer seeds the task denominator from a matching prior run.

Preflight ``--list-tasks`` can't see dynamic ``include_tasks``, so a
role-heavy playbook reports e.g. 4 preflight tasks but runs ~110. When a
matching prior run observed the real total, the live bar shows it up
front (``1/110``). A loose-match prior is marked as an estimate
(``1/~110``); a strict match is trusted plainly.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ansible_aom.compact.renderer import CompactRenderer
from ansible_aom.core.models import PlayDefinition
from ansible_aom.session.history import PriorRun


def _prior(*, observed: int, exact: bool) -> PriorRun:
    return PriorRun(
        session_id="prev",
        duration_seconds=50.0,
        task_count=4,  # misleading preflight count
        host_count=1,
        end_time=datetime(2026, 6, 30, 12, 0, tzinfo=timezone.utc),
        observed_task_count=observed,
        exact_match=exact,
    )


def _drive_one_task(renderer: CompactRenderer) -> None:
    renderer.update_state(
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-07-01T10:00:00Z",
            "play": {"id": "1", "name": "web"},
        }
    )
    renderer.update_state(
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-07-01T10:00:01Z",
            "task": {"id": "t1", "name": "a"},
            "play": {"id": "1"},
        }
    )
    renderer.update_state(
        {
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-07-01T10:00:02Z",
            "task": {"id": "t1"},
            "play": {"id": "1"},
            "hosts": {"w1": {"changed": False}},
        }
    )
    renderer._last_panel_compute_time = 0.0
    renderer.tick()


def _run(prior: PriorRun, monkeypatch) -> list[str]:
    captured: list[str] = []

    class FakeDisplay:
        def start(self):
            pass

        def stop(self):
            pass

        def update(self, text: str) -> None:
            captured.append(text)

        def print_log(self, message: str) -> None:
            pass

        def flush_logs(self) -> None:
            pass

    renderer = CompactRenderer(is_tty=True)
    monkeypatch.setattr(renderer, "_display", FakeDisplay())
    renderer.start("site.yml", [])
    renderer.set_prior_run(prior)
    # Preflight sees zero static tasks (all dynamic includes).
    renderer.set_definitions(
        [PlayDefinition(id="1", name="web", hosts="all", resolved_hosts=["w1"], tasks=[])]
    )
    _drive_one_task(renderer)
    return captured


def test_loose_prior_seeds_estimated_total(monkeypatch) -> None:
    frames = _run(_prior(observed=110, exact=False), monkeypatch)
    assert any("1/~110 tasks" in f for f in frames), frames


def test_strict_prior_seeds_plain_total(monkeypatch) -> None:
    frames = _run(_prior(observed=110, exact=True), monkeypatch)
    assert any("1/110 tasks" in f for f in frames), frames
    assert not any("~110" in f for f in frames), frames


def test_no_prior_falls_back_to_seen(monkeypatch) -> None:
    captured: list[str] = []

    class FakeDisplay:
        def start(self):
            pass

        def stop(self):
            pass

        def update(self, text: str) -> None:
            captured.append(text)

        def print_log(self, message: str) -> None:
            pass

        def flush_logs(self) -> None:
            pass

    renderer = CompactRenderer(is_tty=True)
    monkeypatch.setattr(renderer, "_display", FakeDisplay())
    renderer.start("site.yml", [])
    renderer.set_definitions(
        [PlayDefinition(id="1", name="web", hosts="all", resolved_hosts=["w1"], tasks=[])]
    )
    _drive_one_task(renderer)
    # Without a prior, denominator is just what's been seen (1/1), no tilde.
    assert any("1/1 tasks" in f for f in captured), captured
    assert not any("~" in f for f in captured), captured
