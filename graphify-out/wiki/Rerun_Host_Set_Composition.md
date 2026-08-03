# Rerun Host Set Composition

> 20 nodes · cohesion 0.14

## Key Concepts

- **test_tree_pipe_continuation.py** (13 connections) — `tests/compact/test_tree_pipe_continuation.py`
- **_spur_projection()** (12 connections) — `tests/compact/test_tree_pipe_continuation.py`
- **_two_plays_with_running_tasks()** (9 connections) — `tests/compact/test_tree_pipe_continuation.py`
- **test_ascii_mode_uses_pipe_substitute()** (5 connections) — `tests/compact/test_tree_pipe_continuation.py`
- **test_last_play_children_have_plain_indent()** (5 connections) — `tests/compact/test_tree_pipe_continuation.py`
- **test_non_last_play_children_show_vertical_pipe()** (5 connections) — `tests/compact/test_tree_pipe_continuation.py`
- **test_spur_continues_spine_through_inner_footer()** (5 connections) — `tests/compact/test_tree_pipe_continuation.py`
- **test_spur_continues_spine_through_outer_footer()** (5 connections) — `tests/compact/test_tree_pipe_continuation.py`
- **test_spur_in_ascii_mode_inner_footer()** (5 connections) — `tests/compact/test_tree_pipe_continuation.py`
- **test_spur_in_ascii_mode_outer_footer()** (5 connections) — `tests/compact/test_tree_pipe_continuation.py`
- **Tree-block lines under a non-last play must show the vertical continuation pipe** (1 connections) — `tests/compact/test_tree_pipe_continuation.py`
- **A visible ``TreeProjection`` whose ``tree_lines`` is stubbed so     individual t** (1 connections) — `tests/compact/test_tree_pipe_continuation.py`
- **The line directly above the OUTER footer (``… and N more     tasks`` at depth 0)** (1 connections) — `tests/compact/test_tree_pipe_continuation.py`
- **The line directly above the INNER footer (``… and N more     tasks`` at the deep** (1 connections) — `tests/compact/test_tree_pipe_continuation.py`
- **State with two plays, each with a running task on one host.      Built directly** (1 connections) — `tests/compact/test_tree_pipe_continuation.py`
- **ASCII parity for ``test_spur_continues_spine_through_outer_footer``.      With `** (1 connections) — `tests/compact/test_tree_pipe_continuation.py`
- **r"""ASCII parity for ``test_spur_continues_spine_through_inner_footer``.      Wi** (1 connections) — `tests/compact/test_tree_pipe_continuation.py`
- **A task under a non-last play must be indented with ``│  ``.** (1 connections) — `tests/compact/test_tree_pipe_continuation.py`
- **A task under the last play must NOT carry a vertical pipe — the     parent is th** (1 connections) — `tests/compact/test_tree_pipe_continuation.py`
- **ASCII mode renders the continuation as ``|  `` (or equivalent)     rather than t** (1 connections) — `tests/compact/test_tree_pipe_continuation.py`

## Relationships

- [HostRunState](HostRunState.md) (7 shared connections)
- [format_tree_block](format_tree_block.md) (7 shared connections)
- [TreeProjection](TreeProjection.md) (5 shared connections)
- [.from_run_state](from_run_state.md) (4 shared connections)
- [RunState](RunState.md) (2 shared connections)
- [renderer.py](renderer.py.md) (1 shared connections)
- [tree.py](tree.py.md) (1 shared connections)

## Source Files

- `tests/compact/test_tree_pipe_continuation.py`

## Audit Trail

- EXTRACTED: 75 (95%)
- INFERRED: 4 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*