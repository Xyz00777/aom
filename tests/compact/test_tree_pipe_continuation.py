"""Tree-block lines under a non-last play must show the vertical
continuation pipe (``│``) so the user can see at a glance which parent
they belong to. Previously the pruner emitted plain spaces, breaking
the spine between siblings.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ansible_aom.compact.format import format_tree_block
from ansible_aom.core.models import (
    HostRunState,
    PlayRunState,
    RunState,
    Status,
    TaskRunState,
)
from ansible_aom.core.tree import TreeLine, TreeProjection


def _two_plays_with_running_tasks() -> RunState:
    """State with two plays, each with a running task on one host.

    Built directly rather than via sequential ``v2_playbook_on_play_start``
    events: a second play starting now finalises the first (ansible runs
    plays sequentially, so a prior play is definitively done), which is
    correct for real runs but collapses the first play out of the tree.
    These tests exercise the renderer's multi-play pipe-continuation glyph,
    so they need the (otherwise transient) two-rendered-plays state held
    stable — constructing it directly does exactly that.
    """
    state = RunState(playbook="site.yml")
    t0 = datetime(2026, 4, 20, 10, 0, 0, tzinfo=timezone.utc)
    for pid, pname, tid, tname in (
        ("p1", "first play", "t1", "task one"),
        ("p2", "second play", "t2", "task two"),
    ):
        play = PlayRunState(play_id=pid, name=pname, status=Status.RUNNING)
        task = TaskRunState(task_id=tid, name=tname, status=Status.RUNNING, start_time=t0)
        task.hosts["web1"] = HostRunState(hostname="web1", status=Status.RUNNING, start_time=t0)
        play.tasks[tid] = task
        state.plays[pid] = play
    return state


def test_non_last_play_children_show_vertical_pipe() -> None:
    """A task under a non-last play must be indented with ``│  ``."""
    state = _two_plays_with_running_tasks()
    p = TreeProjection.from_run_state(state)
    block = format_tree_block(p, budget=40, width=120, ascii_mode=False, colorize=False)

    # The task under "first play" (not the last) must show the spine.
    first_task_line = next(ln for ln in block if "task one" in ln)
    assert first_task_line.startswith("│  "), (
        f"expected vertical pipe before task-one under non-last play; got {first_task_line!r}"
    )


def test_last_play_children_have_plain_indent() -> None:
    """A task under the last play must NOT carry a vertical pipe — the
    parent is the last child so no continuation is needed."""
    state = _two_plays_with_running_tasks()
    p = TreeProjection.from_run_state(state)
    block = format_tree_block(p, budget=40, width=120, ascii_mode=False, colorize=False)

    last_task_line = next(ln for ln in block if "task two" in ln)
    assert not last_task_line.startswith("│"), (
        f"expected plain indent before task-two under last play; got {last_task_line!r}"
    )
    assert last_task_line.startswith("   "), (
        f"expected 3-space indent before branch glyph; got {last_task_line!r}"
    )


def test_ascii_mode_uses_pipe_substitute() -> None:
    """ASCII mode renders the continuation as ``|  `` (or equivalent)
    rather than the Unicode box-drawing pipe — no Unicode in ASCII mode.
    """
    state = _two_plays_with_running_tasks()
    p = TreeProjection.from_run_state(state)
    block = format_tree_block(p, budget=40, width=120, ascii_mode=True, colorize=False)
    joined = "\n".join(block)
    assert "│" not in joined, "ASCII mode should not contain Unicode pipe"

    first_task_line = next(ln for ln in block if "task one" in ln)
    assert first_task_line.startswith("|  "), (
        f"expected ASCII pipe before task-one under non-last play; got {first_task_line!r}"
    )


# =============================================================================
# Task 4 (two-level truncation renderer): the spur marker (T1's
# `has_tail_after` field, T2's two-cut truncation) must keep the parent
# spine running through BOTH footers so the user can trace a vertical
# line from the top of the window down to the outer "… and N more
# tasks" indicator. The renderer does this by demoting the last line
# before the cut from `└─` to `├─`, which makes the
# `_ancestor_chain_indent` helper pick up `│  ` instead of `   ` for
# every ancestor above. Both of these tests pin that contract.
#
# We hand-build the TreeLine[] list (and stub `tree_lines` via
# monkeypatch) so the renderer test is independent of T2's truncation
# algorithm — T2 produces the data, T4 renders it correctly, and T5's
# ASCII parity will verify the same shape in `+-` / `|  ` mode.
# =============================================================================


def _spur_projection(monkeypatch) -> TreeProjection:
    """A visible ``TreeProjection`` whose ``tree_lines`` is stubbed so
    individual tests can supply their own ``TreeLine[]``. Same pattern
    as ``_visible_projection`` in ``test_tree_render.py``.
    """
    state = RunState(playbook="site.yml")
    play = PlayRunState(play_id="p1", name="deploy")
    task = TaskRunState(task_id="t1", name="Install nginx")
    task.hosts["web1"] = HostRunState(hostname="web1", status=Status.RUNNING)
    play.tasks["t1"] = task
    state.plays["p1"] = play
    projection = TreeProjection.from_run_state(state)

    holder: list[TreeLine] = []
    monkeypatch.setattr(projection, "tree_lines", lambda budget: holder)
    projection._spur_lines = holder  # type: ignore[attr-defined]
    return projection


def test_spur_continues_spine_through_outer_footer(monkeypatch) -> None:
    """The line directly above the OUTER footer (``… and N more
    tasks`` at depth 0) renders with ``├─`` instead of ``└─``.

    Tree shape (hand-built): playbook → play1 → task(has_tail=True)
    → outer footer @ depth 0. With T4's ``is_last`` override, the
    task's branch flips from ``└─`` to ``├─``. The play above the
    task contributes its own indent segment; this test pins the
    spur on the line just above the footer, which is the contract
    Edit 2 actually owns.
    """
    projection = _spur_projection(monkeypatch)
    projection._spur_lines.extend(  # type: ignore[attr-defined]
        [
            TreeLine(
                depth=0,
                kind="playbook",
                label="site.yml",
                glyph=None,
                status=None,
                elapsed_s=None,
            ),
            TreeLine(
                depth=1,
                kind="play",
                label="play: deploy",
                glyph=None,
                status=Status.RUNNING,
                elapsed_s=None,
            ),
            TreeLine(
                depth=2,
                kind="task",
                label="Last visible task",
                glyph=None,
                status=Status.PENDING,
                elapsed_s=None,
                has_tail_after=True,
            ),
            TreeLine(
                depth=0,
                kind="more",
                label="… and 2832 more tasks",
                glyph=None,
                status=Status.PENDING,
                elapsed_s=None,
            ),
        ]
    )
    block = format_tree_block(projection, budget=10, width=80, ascii_mode=False, colorize=False)

    task_line = next(ln for ln in block if "Last visible task" in ln)
    outer_footer = next(ln for ln in block if "2832 more tasks" in ln)

    # The task is has_tail_after=True → its branch flips from └─ to
    # ├─ (T4 Edit 2). The parent's indent segment is `   ` because
    # the play is the only depth-1 line (no following play), so
    # is_last=True → descendants see `_TREE_GAP` (3 spaces).
    assert task_line.endswith("├─ □ Last visible task"), (
        f"task above outer footer must have ├─ spur; got {task_line!r}"
    )
    assert "└─" not in task_line, (
        f"└─ would mean the renderer ignored has_tail_after; got {task_line!r}"
    )

    # The outer footer hangs off depth 0 with no branch glyph (T4 Edit 1).
    assert "├─" not in outer_footer and "└─" not in outer_footer, (
        f"outer footer must have no branch glyph; got {outer_footer!r}"
    )
    # Edit 3: the outer footer carries the PENDING icon □.
    assert "□" in outer_footer, f"outer footer must carry PENDING icon; got {outer_footer!r}"


def test_spur_continues_spine_through_inner_footer(monkeypatch) -> None:
    """The line directly above the INNER footer (``… and N more
    tasks`` at the deepest visible depth) renders with ``├─``, and
    the inner footer hangs off the spine with no branch glyph.

    Tree shape: playbook → play1 → play2 (cut starts here) → role
    (has_tail_after=True) → task (has_tail_after=True) → inner
    footer @ depth 3 → outer footer @ depth 0.

    The cut lands inside a role's task list. Two plays are
    included so play1 is non-last (a sibling follows) and its
    descendants pick up `│  ` indent from
    ``_ancestor_chain_indent`` — proving the spine extends through
    the play boundary. The role and task lines each carry
    ``has_tail_after=True`` so their branches flip from └─ to ├─.
    """
    projection = _spur_projection(monkeypatch)
    projection._spur_lines.extend(  # type: ignore[attr-defined]
        [
            TreeLine(
                depth=0,
                kind="playbook",
                label="site.yml",
                glyph=None,
                status=None,
                elapsed_s=None,
            ),
            TreeLine(
                depth=1,
                kind="play",
                label="play: first",
                glyph=None,
                status=Status.RUNNING,
                elapsed_s=None,
            ),
            TreeLine(
                depth=1,
                kind="play",
                label="play: second",
                glyph=None,
                status=Status.RUNNING,
                elapsed_s=None,
                has_tail_after=True,
            ),
            TreeLine(
                depth=2,
                kind="role",
                label="role: podman (32 tasks)",
                glyph=None,
                status=None,
                elapsed_s=None,
                identity="podman",
                has_tail_after=True,
            ),
            TreeLine(
                depth=3,
                kind="task",
                label="Last visible podman task",
                glyph=None,
                status=Status.PENDING,
                elapsed_s=None,
                has_tail_after=True,
            ),
            TreeLine(
                depth=3,
                kind="more",
                label="… and 22 more tasks",
                glyph=None,
                status=Status.PENDING,
                elapsed_s=None,
            ),
            TreeLine(
                depth=0,
                kind="more",
                label="… and 2832 more tasks",
                glyph=None,
                status=Status.PENDING,
                elapsed_s=None,
            ),
        ]
    )
    block = format_tree_block(projection, budget=10, width=80, ascii_mode=False, colorize=False)

    play1_line = next(ln for ln in block if "play: first" in ln)
    play2_line = next(ln for ln in block if "play: second" in ln)
    role_line = next(ln for ln in block if "role: podman" in ln)
    task_line = next(ln for ln in block if "Last visible podman task" in ln)
    inner_footer = next(ln for ln in block if "22 more tasks" in ln)
    outer_footer = next(ln for ln in block if "2832 more tasks" in ln)

    # play1 has a sibling (play2) at depth 1, so the existing
    # look-ahead marks it non-last → ├─ and its descendants get
    # `│  ` indent (already covered by
    # test_non_last_play_children_show_vertical_pipe).
    assert play1_line.startswith("├─"), f"play1 must be ├─ (non-last); got {play1_line!r}"

    # play2 is the LAST play at depth 1 — but T4's Edit 2 reads
    # ``has_tail_after=True`` (the marker that T2 sets on the line
    # just before the cut) and short-circuits the look-ahead to
    # is_last=False. So play2's branch flips to ├─ instead of the
    # natural └─ closing glyph, and the spine continues down to
    # the role.
    assert play2_line.startswith("├─"), (
        f"play2 with has_tail_after=True must be ├─ (Edit 2 spur); got {play2_line!r}"
    )
    assert "└─" not in play2_line, (
        f"play2 with has_tail_after=True must not be └─; got {play2_line!r}"
    )

    # The role line at depth 2 has has_tail_after=True → its branch
    # is ├─ (Edit 2). Its indent under play2 (the most recent
    # depth-1 ancestor) is `│  ` because play2 is non-last (via
    # has_tail_after=True).
    assert role_line.startswith("│  ├─"), (
        f"role above inner footer must have ├─ spur under `│  ` ancestor; got {role_line!r}"
    )

    # The task line at depth 3 has has_tail_after=True → ├─. Its
    # indent chain: depth-1 = `│  ` (play1 non-last), depth-2 = `│  `
    # (role has_tail_after=True → non-last).
    assert task_line.startswith("│  │  ├─"), (
        f"task above inner footer must have `│  │  ├─` indent chain; got {task_line!r}"
    )

    # The inner footer hangs off depth 3 with no branch glyph (Edit 1).
    assert "├─" not in inner_footer and "└─" not in inner_footer, (
        f"inner footer must have no branch glyph; got {inner_footer!r}"
    )
    # Edit 3: inner footer carries the PENDING icon.
    assert "□" in inner_footer, f"inner footer must carry PENDING icon; got {inner_footer!r}"
    # The outer footer hangs off depth 0 with no branch glyph (Edit 1).
    assert "├─" not in outer_footer and "└─" not in outer_footer, (
        f"outer footer must have no branch glyph; got {outer_footer!r}"
    )
    assert "□" in outer_footer, f"outer footer must carry PENDING icon; got {outer_footer!r}"


# =============================================================================
# Task 5 (ASCII parity for the two-level truncation spur): the T4 spur
# contract — "a ``has_tail_after`` line flips its branch from └ to ├, and
# its ancestors render with `│  ` instead of `   `" — must hold in ASCII
# mode too. The renderer's `last_glyph` / `mid_glyph` / `pipe_glyph`
# selection at ``format_tree_block`` lines 607-609 already maps the
# Unicode constants (``├─``, ``└─``, ``│  ``) to their ASCII equivalents
# (``+-``, ``\-``, ``|  ``). These two tests pin that mapping for the
# truncation case so a future regression that drops the ASCII glyph
# selection would be caught.
#
# Mirror image of the T4 Unicode tests above; the only differences are
# ``ascii_mode=True`` and the glyph assertions swapping to ASCII
# (``+-``, ``\-``, ``|  ``) plus an extra "no Unicode in ASCII output"
# guard. PENDING icon also flips to the ASCII fallback ``.``.
# =============================================================================


def test_spur_in_ascii_mode_outer_footer(monkeypatch) -> None:
    """ASCII parity for ``test_spur_continues_spine_through_outer_footer``.

    With ``ascii_mode=True``:
    - The line just above the outer footer renders with ``+-``
      (ASCII mid) instead of ``├─``, pinning Edit 2's spur behavior
      in the ASCII glyph set.
    - The outer footer hangs off the spine with no branch glyph at
      all and carries the ASCII PENDING icon ``.`` (Edit 1 + Edit 3).
    - No Unicode box-drawing characters (``├``, ``└``, ``│``) leak
      into the rendered block.
    """
    projection = _spur_projection(monkeypatch)
    projection._spur_lines.extend(  # type: ignore[attr-defined]
        [
            TreeLine(
                depth=0,
                kind="playbook",
                label="site.yml",
                glyph=None,
                status=None,
                elapsed_s=None,
            ),
            TreeLine(
                depth=1,
                kind="play",
                label="play: deploy",
                glyph=None,
                status=Status.RUNNING,
                elapsed_s=None,
            ),
            TreeLine(
                depth=2,
                kind="task",
                label="Last visible task",
                glyph=None,
                status=Status.PENDING,
                elapsed_s=None,
                has_tail_after=True,
            ),
            TreeLine(
                depth=0,
                kind="more",
                label="… and 2832 more tasks",
                glyph=None,
                status=Status.PENDING,
                elapsed_s=None,
            ),
        ]
    )
    block = format_tree_block(projection, budget=10, width=80, ascii_mode=True, colorize=False)

    task_line = next(ln for ln in block if "Last visible task" in ln)
    outer_footer = next(ln for ln in block if "2832 more tasks" in ln)

    # The task is has_tail_after=True → branch flips from \- to +-.
    # The play above is the only depth-1 line so is_last=True → its
    # indent segment in the chain is `_TREE_GAP` (3 spaces).
    assert task_line.endswith("+- . Last visible task"), (
        f"task above outer footer must have ASCII +- spur; got {task_line!r}"
    )
    assert "\\-" not in task_line, (
        f"\\- would mean the renderer ignored has_tail_after in ASCII mode; got {task_line!r}"
    )

    # Outer footer hangs off depth 0 with no branch glyph (Edit 1).
    assert "+-" not in outer_footer and "\\-" not in outer_footer, (
        f"outer footer must have no branch glyph in ASCII mode; got {outer_footer!r}"
    )
    # Edit 3 in ASCII: PENDING icon is the ASCII fallback `.`.
    assert "." in outer_footer, f"outer footer must carry ASCII PENDING icon; got {outer_footer!r}"

    # No Unicode box-drawing characters leak into ASCII output.
    joined = "\n".join(block)
    for uni_glyph in ("├", "└", "│"):
        assert uni_glyph not in joined, (
            f"ASCII mode must not contain Unicode glyph {uni_glyph!r}; block was:\n{joined}"
        )


def test_spur_in_ascii_mode_inner_footer(monkeypatch) -> None:
    r"""ASCII parity for ``test_spur_continues_spine_through_inner_footer``.

    With ``ascii_mode=True``:
    - play1 (non-last play) starts with ``+-`` (ASCII mid).
    - play2 (has_tail_after=True) starts with ``+-`` (ASCII mid
      spur, was ``\-`` before T4 Edit 2).
    - The role line starts with ``|  +-`` (ASCII pipe + ASCII mid).
    - The task line starts with ``|  |  +-`` (two ASCII pipes +
      ASCII mid).
    - Both footers hang off the spine with no branch glyph and
      carry the ASCII PENDING icon ``.``.
    - No Unicode box-drawing characters leak into the rendered block.
    """
    projection = _spur_projection(monkeypatch)
    projection._spur_lines.extend(  # type: ignore[attr-defined]
        [
            TreeLine(
                depth=0,
                kind="playbook",
                label="site.yml",
                glyph=None,
                status=None,
                elapsed_s=None,
            ),
            TreeLine(
                depth=1,
                kind="play",
                label="play: first",
                glyph=None,
                status=Status.RUNNING,
                elapsed_s=None,
            ),
            TreeLine(
                depth=1,
                kind="play",
                label="play: second",
                glyph=None,
                status=Status.RUNNING,
                elapsed_s=None,
                has_tail_after=True,
            ),
            TreeLine(
                depth=2,
                kind="role",
                label="role: podman (32 tasks)",
                glyph=None,
                status=None,
                elapsed_s=None,
                identity="podman",
                has_tail_after=True,
            ),
            TreeLine(
                depth=3,
                kind="task",
                label="Last visible podman task",
                glyph=None,
                status=Status.PENDING,
                elapsed_s=None,
                has_tail_after=True,
            ),
            TreeLine(
                depth=3,
                kind="more",
                label="… and 22 more tasks",
                glyph=None,
                status=Status.PENDING,
                elapsed_s=None,
            ),
            TreeLine(
                depth=0,
                kind="more",
                label="… and 2832 more tasks",
                glyph=None,
                status=Status.PENDING,
                elapsed_s=None,
            ),
        ]
    )
    block = format_tree_block(projection, budget=10, width=80, ascii_mode=True, colorize=False)

    play1_line = next(ln for ln in block if "play: first" in ln)
    play2_line = next(ln for ln in block if "play: second" in ln)
    role_line = next(ln for ln in block if "role: podman" in ln)
    task_line = next(ln for ln in block if "Last visible podman task" in ln)
    inner_footer = next(ln for ln in block if "22 more tasks" in ln)
    outer_footer = next(ln for ln in block if "2832 more tasks" in ln)

    # play1 has a sibling (play2) at depth 1 → non-last → +-.
    assert play1_line.startswith("+-"), (
        f"play1 must be +- (non-last) in ASCII mode; got {play1_line!r}"
    )

    # play2 is the LAST play at depth 1, but has_tail_after=True
    # short-circuits the look-ahead → branch flips to +-.
    assert play2_line.startswith("+-"), (
        f"play2 with has_tail_after=True must be +- (Edit 2 spur) in ASCII mode; got {play2_line!r}"
    )
    assert "\\-" not in play2_line, (
        f"play2 with has_tail_after=True must not be \\- in ASCII mode; got {play2_line!r}"
    )

    # Role line at depth 2 has has_tail_after=True → +- (Edit 2).
    # Indent under play2 (non-last ancestor) is `|  `.
    assert role_line.startswith("|  +-"), (
        f"role above inner footer must have ASCII `|  +-` indent chain; got {role_line!r}"
    )

    # Task line at depth 3 has has_tail_after=True → +-.
    # Indent chain: depth-1 = `|  ` (play1 non-last),
    # depth-2 = `|  ` (role has_tail_after=True → non-last).
    assert task_line.startswith("|  |  +-"), (
        f"task above inner footer must have ASCII `|  |  +-` indent chain; got {task_line!r}"
    )

    # Inner footer hangs off depth 3 with no branch glyph (Edit 1).
    assert "+-" not in inner_footer and "\\-" not in inner_footer, (
        f"inner footer must have no branch glyph in ASCII mode; got {inner_footer!r}"
    )
    # Edit 3 in ASCII: PENDING icon is `.`.
    assert "." in inner_footer, f"inner footer must carry ASCII PENDING icon; got {inner_footer!r}"
    # Outer footer hangs off depth 0 with no branch glyph (Edit 1).
    assert "+-" not in outer_footer and "\\-" not in outer_footer, (
        f"outer footer must have no branch glyph in ASCII mode; got {outer_footer!r}"
    )
    assert "." in outer_footer, f"outer footer must carry ASCII PENDING icon; got {outer_footer!r}"

    # No Unicode box-drawing characters leak into ASCII output.
    joined = "\n".join(block)
    for uni_glyph in ("├", "└", "│"):
        assert uni_glyph not in joined, (
            f"ASCII mode must not contain Unicode glyph {uni_glyph!r}; block was:\n{joined}"
        )
