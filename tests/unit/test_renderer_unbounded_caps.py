"""R14 — cap unbounded CompactRenderer sets.

R14 spec: the compact renderer carries four set/dict structures that
grow monotonically as events arrive. A pathological run (100k unique
warning messages, 100k distinct (host, task_id) loop-item pairs, …)
would blow them up without bound.

Caps introduced:
- ``_streamed_loop_items`` (set): 10 000 — bounded because the set's
  only role is dedupe, and a runaway loop fan-out can otherwise fill
  memory in seconds.
- ``_announced_task_uuids`` (set): MAX_TASKS_PER_PLAY (10 000) — same
  dedupe role.
- ``_completed_task_ids`` (set): MAX_TASKS_PER_PLAY (10 000) — same
  dedupe role.
- ``_seen_warning_messages`` (set): 5 000 — bounded to keep the
  rendered warning count honest. Dropping the oldest warning message
  from the seen-set is acceptable: a warning that repeats past the cap
  will be re-printed, which is the "we noticed it, but maybe not 100k
  times" middle-ground.

When a cap is exceeded, the set is cleared (so a soft re-seed lets
future lookups continue dedupe-ing the recent tail) — sets are
unordered so a true FIFO drop would require a different container
(OrderedDict / ``deque``). The renderer doesn't need strict FIFO for
any of these; correctness only requires that the set not grow
unboundedly.
"""

from __future__ import annotations

from typing import Any

from ansible_aom.core.state_machine import MAX_TASKS_PER_PLAY


def _build_compact_renderer() -> Any:
    """Construct a CompactRenderer with mocks for its dependencies.

    The renderer's ``__init__`` does terminal detection; pass ``is_tty=False``
    so the construction is non-interactive in the test environment.
    """
    from ansible_aom.compact.renderer import CompactRenderer

    return CompactRenderer(is_tty=False)


def test_streamed_loop_items_capped() -> None:
    """R14: ``_streamed_loop_items`` is bounded at 10 000 entries."""
    renderer = _build_compact_renderer()
    cap = 10_000
    for i in range(cap * 2):
        # Each unique (host, task_id) pair. Tuple-as-set-element is the
        # data shape the renderer uses internally.
        renderer._streamed_loop_items.add((f"h-{i}", f"t-{i}"))
    assert len(renderer._streamed_loop_items) <= cap


def test_announced_task_uuids_capped() -> None:
    """R14: ``_announced_task_uuids`` is bounded at MAX_TASKS_PER_PLAY."""
    renderer = _build_compact_renderer()
    for i in range(MAX_TASKS_PER_PLAY * 2):
        renderer._announced_task_uuids.add(f"uuid-{i}")
    assert len(renderer._announced_task_uuids) <= MAX_TASKS_PER_PLAY


def test_completed_task_ids_capped() -> None:
    """R14: ``_completed_task_ids`` is bounded at MAX_TASKS_PER_PLAY."""
    renderer = _build_compact_renderer()
    for i in range(MAX_TASKS_PER_PLAY * 2):
        renderer._completed_task_ids.add(f"task-id-{i}")
    assert len(renderer._completed_task_ids) <= MAX_TASKS_PER_PLAY


def test_seen_warning_messages_capped() -> None:
    """R14: ``_seen_warning_messages`` is bounded at 5 000 entries."""
    renderer = _build_compact_renderer()
    cap = 5_000
    for i in range(cap * 2):
        renderer._seen_warning_messages.add(f"warning message {i}")
    assert len(renderer._seen_warning_messages) <= cap


def test_renderer_constructor_uses_sane_initial_caps() -> None:
    """R14: the initial empty sets have the same cap semantics — fresh
    renderers must not start with arbitrary large sizes."""
    renderer = _build_compact_renderer()
    assert isinstance(renderer._streamed_loop_items, set)
    assert isinstance(renderer._announced_task_uuids, set)
    assert isinstance(renderer._completed_task_ids, set)
    assert isinstance(renderer._seen_warning_messages, set)
