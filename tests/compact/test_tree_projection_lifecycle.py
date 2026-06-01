# pyright: reportMissingImports=false

"""TC-PERF-020..021 — persistent TreeProjection on CompactRenderer.

``TreeProjection.from_run_state`` was called per render, which threw
away the per-instance ``_role_index`` memo on every cycle. The durable
projection now stays alive on the renderer and refreshes its own
revision-aware caches when state-shape mutating events arrive.
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
from ansible_aom.core.tree import TreeProjection


def _task_start(
    uuid: str = "u1", ts: str = "2026-05-11T10:00:00Z", name: str = "T", play_id: str = "p1"
) -> dict:
    return {
        "_event": "v2_playbook_on_task_start",
        "_timestamp": ts,
        "task": {"id": uuid, "name": name},
        "play": {"id": play_id},
    }


def _runner_ok(uuid: str = "u1", ts: str = "2026-05-11T10:00:01Z") -> dict:
    return {
        "_event": "v2_runner_on_ok",
        "_timestamp": ts,
        "task": {"id": uuid, "name": "T"},
        "play": {"id": "p1"},
        "host": "web1",
        "hosts": {"web1": {"changed": False}},
    }


def _seed_sticky_gap_state(r: CompactRenderer) -> None:
    """Build a tiny two-play state that exposes sticky row selection.

    ``active`` is currently running, while ``later`` is already completed but
    still has runtime tasks. If the projection survives the next frame, the
    tree stays anchored on ``active``. If the renderer discards the projection,
    the next frame loses ``_last_running_play_id`` and the tree can jump to
    ``later`` instead.
    """
    r._definitions = [
        PlayDefinition(
            id="1",
            name="active",
            hosts="all",
            resolved_hosts=["web1"],
            tasks=[
                TaskDefinition(
                    name="T",
                    role=None,
                    tags=[],
                    play_id="1",
                    play_order=0,
                    task_order=0,
                )
            ],
        ),
        PlayDefinition(
            id="2",
            name="later",
            hosts="all",
            resolved_hosts=["web1"],
            tasks=[
                TaskDefinition(
                    name="U",
                    role=None,
                    tags=[],
                    play_id="2",
                    play_order=1,
                    task_order=0,
                )
            ],
        ),
    ]
    assert r._state is not None
    r._state.definitions = list(r._definitions)

    active = PlayRunState(play_id="p1", name="active", status=Status.RUNNING)
    active_task = TaskRunState(task_id="u1", name="T", status=Status.RUNNING)
    active_task.hosts["web1"] = HostRunState(hostname="web1", status=Status.RUNNING)
    active.tasks["u1"] = active_task

    later = PlayRunState(play_id="p2", name="later", status=Status.COMPLETED)
    later.tasks["u2"] = TaskRunState(task_id="u2", name="U", status=Status.COMPLETED)

    r._state.plays = {"p1": active, "p2": later}


def _renderer() -> CompactRenderer:
    r = CompactRenderer(is_tty=False)
    r.start("test.yml", [])
    r._colorize = False
    r._display = MagicMock()
    return r


class TestProjectionLifecycle:
    def test_perf_020_event_keeps_projection_alive_and_refreshes_cache(self) -> None:
        """A state-shape change must refresh, not replace, the cached projection.

        The renderer should keep one durable ``TreeProjection`` instance
        alive so row continuity survives successive events. When
        ``RunState`` grafts a dynamic child, the projection must refresh
        its cached role map in place rather than being discarded.
        """
        r = _renderer()
        r._definitions = [
            PlayDefinition(
                id="p1",
                name="deploy",
                hosts="all",
                resolved_hosts=["web1"],
                tasks=[
                    TaskDefinition(
                        name="Install nginx",
                        role="webserver",
                        tags=[],
                        play_id="p1",
                        play_order=0,
                        task_order=0,
                    )
                ],
            )
        ]
        assert r._state is not None
        r._state.definitions = list(r._definitions)

        # Force a render so the projection cache populates, then seed a
        # known parent task so the next unknown task grafts as its child.
        r._last_panel_compute_time = 0.0
        r.update_state(_task_start(uuid="u1", name="Install nginx"))
        first = r._projection
        assert isinstance(first, TreeProjection)
        assert first._task_role("Install nginx") == "webserver"

        # The unknown task is grafted dynamically under the matched
        # parent. The same projection instance must survive, and its
        # role cache must refresh to recognise the new child.
        r._last_panel_compute_time = 0.0
        r.update_state(_task_start(uuid="u2", name="Poll async status"))

        post_event = r._projection
        assert post_event is first
        assert post_event._task_role("Poll async status") == "webserver"

    def test_perf_021_consecutive_ticks_reuse_projection(self) -> None:
        """Two ticks with no intervening state mutation reuse the same instance."""
        r = _renderer()
        r.tick()
        first = r._projection
        assert isinstance(first, TreeProjection)

        # The HS-1/HS-8 throttle would skip a second compute within
        # 1 s, so reset the timestamp to force a real render — that's
        # what makes the cache-reuse question observable.
        r._last_panel_compute_time = 0.0
        r.tick()
        second = r._projection

        # No state mutation between the ticks → the cached projection
        # is reused (object identity), keeping ``_role_index`` warm.
        assert second is first

    def test_perf_022_update_state_keeps_sticky_active_play_on_gap_frame(self) -> None:
        """A non-structural update must keep the active play visible only
        while it still has running/pending surface.

        The active task now completes, leaving a quiet frame. The renderer must
        keep the same projection instance alive, but the completed play itself
        must stop rendering as the sticky fallback row.
        """
        r = _renderer()
        _seed_sticky_gap_state(r)

        # Prime the projection with an active frame so the sticky play id is
        # stored on the cached ``TreeProjection`` instance.
        r._last_panel_compute_time = 0.0
        r._render_status_panel()
        assert isinstance(r._projection, TreeProjection)
        active_rows = [
            ln.label
            for ln in r._projection.tree_lines(20)
            if ln.kind == "play" and ln.depth == 1
        ]
        assert active_rows == ["play: active"]

        # The active task now completes, leaving a quiet frame. The completed
        # play must vanish instead of lingering as the sticky fallback row.
        r._last_panel_compute_time = 0.0
        r.update_state(_runner_ok())

        play_rows = [
            ln.label
            for ln in r._projection.tree_lines(20)
            if ln.kind == "play" and ln.depth == 1
        ]
        assert play_rows == []
