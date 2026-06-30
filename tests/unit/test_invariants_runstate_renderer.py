"""Stateful invariants over RunState and the CompactRenderer mirror.

The HS-2..HS-6 perf commits replaced "recompute from scratch on every
render" with caches and incremental counters kept on ``CompactRenderer``.
That trade is fast but introduces a class of bug where the mirror drifts
from the authoritative ``RunState``: an event handler that forgets to
bump a counter, an invalidation that misses an event type, an index
that goes stale across reassignment of ``definitions``.

These tests drive renderer + state with random event sequences using a
Hypothesis ``RuleBasedStateMachine`` and assert wider-reaching
invariants after every step. The oracles are the "slow" full-walk
functions in ``compact.format`` and the documented relationships in
``core.models`` — they are intentionally unchanged by the perf commits
so they make safe ground truth.

Scope of invariants checked here (one per ``@invariant``):

* ``_tasks_completed`` (incremental, HS-2) == ``count_completed_tasks``
  oracle from ``compact.format`` over the live ``RunState``.
* ``_tasks_seen`` (incremental, HS-2) == ``count_total_tasks_seen``
  oracle.
* ``_completed_task_ids`` only ever names task ids that exist in
  ``state.plays`` and are in fact terminal (no host still RUNNING).
* ``_projection`` (cached TreeProjection, HS-3), if non-None, references
  the renderer's current ``_state`` — never a stale state object.
* ``_task_def_index`` and ``_play_def_by_name`` (HS-5/HS-6) match a
  freshly-rebuilt index from ``state.definitions``.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from hypothesis import HealthCheck, settings
from hypothesis import strategies as st
from hypothesis.stateful import (
    Bundle,
    RuleBasedStateMachine,
    invariant,
    rule,
)

from ansible_aom.compact.format import (
    count_completed_tasks,
    count_total_tasks_seen,
)
from ansible_aom.compact.renderer import CompactRenderer
from ansible_aom.core.models import (
    PlayDefinition,
    Status,
    TaskDefinition,
    _iter_leaf_task_defs,
)


def _ts(i: int) -> str:
    """Monotone fake timestamps so end_time >= start_time holds trivially."""
    return f"2026-05-22T10:00:{i:02d}Z"


def _renderer() -> CompactRenderer:
    """Build a renderer with stdout muted so the test stays quiet.

    ``is_tty=False`` makes ``Display.update`` a no-op but ``print_log``
    still falls through to ``print()`` — we swap ``_display`` for a mock
    so the stateful run doesn't dump thousands of log lines into the
    pytest output buffer.
    """
    r = CompactRenderer(is_tty=False)
    r.start("invariants.yml", [])
    r._display = MagicMock()
    return r


_HOST_POOL = ("web1", "web2", "web3", "db1")
_host_strategy = st.sampled_from(_HOST_POOL)


class RendererMirrorMachine(RuleBasedStateMachine):
    """Random event walk + invariants over (RunState, CompactRenderer)."""

    plays = Bundle("plays")  # play_id strings
    tasks = Bundle("tasks")  # (play_id, task_id) tuples

    def __init__(self) -> None:
        super().__init__()
        self.renderer = _renderer()
        self._event_seq = 0

    def _next_ts(self) -> str:
        self._event_seq += 1
        return _ts(self._event_seq)

    # ── rules: shrink the state surface to events that actually mutate
    # the mirror we care about. ``v2_playbook_on_start`` is deliberately
    # omitted because it only sets ``start_time`` and doesn't touch any
    # of the renderer caches. Hosts are drawn from a small fixed pool
    # rather than a Bundle — Bundles are for objects whose identity
    # matters across rules, hosts are plain strings.

    @rule(target=plays, name=st.text(min_size=1, max_size=4))
    def play_start(self, name: str) -> str:
        play_id = f"pl-{self._event_seq}"
        ev = {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": self._next_ts(),
            "play": {"id": play_id, "name": name},
        }
        self.renderer.update_state(ev)
        return play_id

    @rule(target=tasks, play=plays, name=st.text(min_size=1, max_size=8))
    def task_start(self, play: str, name: str) -> tuple[str, str]:
        task_id = f"t-{play}-{self._event_seq}"
        ev = {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": self._next_ts(),
            "play": {"id": play},
            "task": {"id": task_id, "name": name},
        }
        self.renderer.update_state(ev)
        return (play, task_id)

    @rule(target=tasks, play=plays, host=_host_strategy, name=st.text(min_size=1, max_size=8))
    def runner_on_start(self, play: str, host: str, name: str) -> tuple[str, str]:
        """Free-strategy entry point — task_id appears via runner_on_start."""
        task_id = f"t-{play}-{self._event_seq}"
        ev = {
            "_event": "v2_runner_on_start",
            "_timestamp": self._next_ts(),
            "play": {"id": play},
            "task": {"id": task_id, "name": name},
            "host": host,
        }
        self.renderer.update_state(ev)
        return (play, task_id)

    @rule(task=tasks, host=_host_strategy, changed=st.booleans())
    def runner_on_ok(self, task: tuple[str, str], host: str, changed: bool) -> None:
        play_id, task_id = task
        ev = {
            "_event": "v2_runner_on_ok",
            "_timestamp": self._next_ts(),
            "play": {"id": play_id},
            "task": {"id": task_id},
            "hosts": {host: {"changed": changed}},
        }
        self.renderer.update_state(ev)

    @rule(task=tasks, host=_host_strategy)
    def runner_on_failed(self, task: tuple[str, str], host: str) -> None:
        play_id, task_id = task
        ev = {
            "_event": "v2_runner_on_failed",
            "_timestamp": self._next_ts(),
            "play": {"id": play_id},
            "task": {"id": task_id},
            "hosts": {host: {"msg": "boom"}},
        }
        self.renderer.update_state(ev)

    @rule(task=tasks, host=_host_strategy)
    def runner_on_skipped(self, task: tuple[str, str], host: str) -> None:
        play_id, task_id = task
        ev = {
            "_event": "v2_runner_on_skipped",
            "_timestamp": self._next_ts(),
            "play": {"id": play_id},
            "task": {"id": task_id},
            "hosts": {host: {"skipped": True}},
        }
        self.renderer.update_state(ev)

    @rule(task=tasks, host=_host_strategy)
    def runner_on_unreachable(self, task: tuple[str, str], host: str) -> None:
        play_id, task_id = task
        ev = {
            "_event": "v2_runner_on_unreachable",
            "_timestamp": self._next_ts(),
            "play": {"id": play_id},
            "task": {"id": task_id},
            "hosts": {host: {"msg": "no ssh"}},
        }
        self.renderer.update_state(ev)

    @rule()
    def tick(self) -> None:
        """Quiet-period refresh; must not perturb any counter or index."""
        self.renderer.tick()

    @rule(
        play_count=st.integers(min_value=0, max_value=3),
        task_count=st.integers(min_value=0, max_value=3),
    )
    def reload_definitions(self, play_count: int, task_count: int) -> None:
        """Reassign ``state.definitions`` mid-run.

        Exercises the __setattr__ hook that rebuilds the lookup indexes.
        After this rule fires the indexes must reflect the *new*
        definitions, not the old ones — that's the regression we'd see
        if a future refactor moved indexing out of ``__setattr__``.
        """
        defs: list[PlayDefinition] = []
        for p in range(play_count):
            tasks: list = []
            for t in range(task_count):
                tasks.append(
                    TaskDefinition(
                        name=f"def-task-{p}-{t}",
                        role=None,
                        tags=[],
                        play_id=str(p),
                        play_order=p,
                        task_order=t,
                    )
                )
            defs.append(
                PlayDefinition(
                    id=str(p),
                    name=f"def-play-{p}",
                    hosts="all",
                    resolved_hosts=[],
                    tasks=tasks,
                )
            )
        self.renderer.set_definitions(defs)

    # ── invariants ────────────────────────────────────────────────────

    @invariant()
    def tasks_completed_matches_oracle(self) -> None:
        """HS-2: incremental counter == authoritative full-state walk."""
        if self.renderer._state is None:
            return
        oracle = count_completed_tasks(self.renderer._state)
        assert self.renderer._tasks_completed == oracle, (
            f"_tasks_completed drifted from oracle: "
            f"{self.renderer._tasks_completed} != {oracle} "
            f"(plays={len(self.renderer._state.plays)})"
        )

    @invariant()
    def tasks_seen_matches_oracle(self) -> None:
        """HS-2: ``_tasks_seen`` is the renderer-side denominator floor.

        The status bar takes ``max(_tasks_seen, count_total_tasks(defs))``,
        so we only require the renderer counter to never exceed the
        oracle — under-counting is acceptable while a task_start is
        still in flight, but over-counting would break the ratio
        invariant ``completed / total <= 1``.
        """
        if self.renderer._state is None:
            return
        oracle = count_total_tasks_seen(self.renderer._definitions, self.renderer._state)
        # The renderer's ``_tasks_seen`` only bumps on task_start; under
        # the free strategy where runner_on_start is the first signal,
        # the oracle (which counts ``state.plays[…].tasks``) can exceed
        # _tasks_seen until a matching task_start arrives. The hard
        # invariant is the other direction.
        assert self.renderer._tasks_seen <= oracle, (
            f"_tasks_seen overshot oracle: {self.renderer._tasks_seen} > {oracle}"
        )

    @invariant()
    def completed_ids_subset_of_known_tasks(self) -> None:
        """Every id we counted as completed must still exist in state."""
        if self.renderer._state is None:
            return
        known: set[str] = set()
        for play in self.renderer._state.plays.values():
            known.update(play.tasks.keys())
        leaked = self.renderer._completed_task_ids - known
        assert not leaked, f"_completed_task_ids names tasks not in state.plays: {leaked}"

    @invariant()
    def completed_ids_are_actually_terminal(self) -> None:
        """A task id in ``_completed_task_ids`` must have no RUNNING hosts.

        Counter-positive of the bump rule in ``_bump_task_counters``: we
        only set an id when ``all(hs.status != RUNNING for hs in hosts)``,
        and once added it stays. If a *later* event resurrects a host
        to RUNNING for that task, the counter still claims "complete" —
        that would be a real bug worth catching.
        """
        if self.renderer._state is None:
            return
        for play in self.renderer._state.plays.values():
            for task_id, task in play.tasks.items():
                if task_id not in self.renderer._completed_task_ids:
                    continue
                still_running = [h for h, hs in task.hosts.items() if hs.status == Status.RUNNING]
                assert not still_running, (
                    f"task {task_id} is in _completed_task_ids but hosts "
                    f"{still_running} are RUNNING"
                )

    @invariant()
    def projection_cache_references_current_state(self) -> None:
        """HS-3: cached ``TreeProjection``, if any, points at the live state."""
        proj = self.renderer._projection
        if proj is None:
            return
        # ``TreeProjection.from_run_state`` stashes the source state on
        # ``_state``; if the cache survived a definitions swap or a
        # ``start()`` reset, this identity check catches it.
        assert proj._state is self.renderer._state, (
            "cached TreeProjection references a stale RunState — invalidation missed an event type"
        )

    @invariant()
    def task_def_index_matches_definitions(self) -> None:
        """HS-5: ``_task_def_index`` is a coherent view of ``definitions``.

        First-write-wins on duplicates matches the linear scan it
        replaced, so we rebuild the same way and compare keys + identity.
        """
        state = self.renderer._state
        if state is None:
            return
        idx = state._task_def_index
        assert idx is not None, (
            "_task_def_index is None after __setattr__ — index rebuild "
            "did not run on definitions assignment"
        )
        expected: dict[str, TaskDefinition] = {}
        for leaf in _iter_leaf_task_defs(state.definitions):
            expected.setdefault(leaf.name, leaf)
        assert set(idx.keys()) == set(expected.keys()), (
            f"_task_def_index key set drifted: {set(idx.keys()) ^ set(expected.keys())}"
        )
        for name, leaf in expected.items():
            assert idx[name] is leaf, (
                f"_task_def_index[{name!r}] is not the same object as the "
                f"first leaf in definitions — first-write-wins broke"
            )

    @invariant()
    def play_def_by_name_matches_definitions(self) -> None:
        """HS-6: ``_play_def_by_name`` matches a rebuilt-from-scratch index."""
        state = self.renderer._state
        if state is None:
            return
        idx = state._play_def_by_name
        assert idx is not None
        expected: dict[str, PlayDefinition] = {}
        for play_def in state.definitions:
            expected.setdefault(play_def.name, play_def)
        assert set(idx.keys()) == set(expected.keys())
        for name, play_def in expected.items():
            assert idx[name] is play_def


# Wrap the state machine for pytest. ``stateful_step_count`` controls
# how many rules fire per Hypothesis example; 30 is enough to surface
# multi-step ordering bugs while keeping the suite under a few seconds.
TestRendererMirror = RendererMirrorMachine.TestCase
TestRendererMirror.settings = settings(
    max_examples=50,
    stateful_step_count=30,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
)
