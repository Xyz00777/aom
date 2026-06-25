"""Tests for TUI parity of the two-level truncation (``populate_from_projection``).

See ``.sisyphus/plans/two-level-truncation.md`` T6. The TUI uses
Textual's ``Tree`` widget which manages its own indentation/expansion,
so it cannot reuse ``compact.format_tree_block``. Instead it consumes
``TreeProjection.tree_lines(budget)`` directly via a new
``TaskTree.populate_from_projection`` method that maps each ``TreeLine``
to a ``TreeNode``.

Tests:

- ``test_tui_renders_two_level_truncation`` — both inner + outer
  "more" footers render as Textual TreeNodes with the right data key.
- ``test_tui_more_node_is_not_expandable`` — footers carry
  ``allow_expand=False`` so the user can't expand a footer.
- ``test_tui_role_label_remaining_in_textual_tree`` — the role
  label says ``(M remaining)`` when the cut lands inside the role
  (T3 contract).
- ``test_tui_more_node_styled_dim_italic`` — the footer's label
  carries ``"dim italic"`` style so it reads as metadata, not a
  real task.

All tests build a state directly via ``RunState`` /
``PlayRunState`` / ``TaskRunState`` / ``HostRunState`` (mirrors the
integration test in ``tests/compact/test_tree_render.py``), then call
``populate_from_projection(projection, budget=N)`` and inspect the
resulting ``Tree`` widget's node structure.
"""

from textual.widgets.tree import TreeNode

from ansible_aom.core.models import (
    HostRunState,
    PlayDefinition,
    PlayRunState,
    RoleGroupDefinition,
    RunState,
    Status,
    TaskDefinition,
    TaskRunState,
)
from ansible_aom.core.tree import TreeLine, TreeProjection

# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _two_level_state() -> RunState:
    """Build the user's sketch shape: two plays, second with a 33-task
    ``podman`` role. Same shape as
    ``tests/compact/test_tree_render.py::test_format_tree_block_renders_two_level_truncation``
    so the TUI test mirrors the compact integration test.
    """
    state = RunState(playbook="smfc-and-scrutiny.yml")
    state.definitions = [
        PlayDefinition(
            id="p1",
            name="Supermicro Fan Control (smfc) Install and Config",
            hosts="localhost",
            resolved_hosts=["host1"],
            tasks=[
                RoleGroupDefinition(
                    role="smfc",
                    tasks=[
                        TaskDefinition(
                            name=f"smfc : step {i}",
                            role="smfc",
                            tags=[],
                            play_id="p1",
                            play_order=0,
                            task_order=i,
                        )
                        for i in range(3)
                    ],
                )
            ],
        ),
        PlayDefinition(
            id="p2",
            name="Setup rootless Podman for Scrutiny web server",
            hosts="localhost",
            resolved_hosts=["host1"],
            tasks=[
                RoleGroupDefinition(
                    role="podman",
                    tasks=[
                        TaskDefinition(
                            name=f"podman : Podman task {i}",
                            role="podman",
                            tags=[],
                            play_id="p2",
                            play_order=1,
                            task_order=i,
                        )
                        for i in range(33)
                    ],
                )
            ],
        ),
    ]

    # Runtime: one task per play running so both plays stay visible to
    # the active-play filter in ``_tree_lines_unbounded``.
    p1 = PlayRunState(play_id="p1", name="Supermicro Fan Control (smfc) Install and Config")
    t_p1 = TaskRunState(task_id="smfc_t0", name="smfc : step 0", status=Status.RUNNING)
    t_p1.hosts["host1"] = HostRunState(hostname="host1", status=Status.RUNNING)
    p1.tasks["smfc_t0"] = t_p1
    state.plays["p1"] = p1

    p2 = PlayRunState(play_id="p2", name="Setup rootless Podman for Scrutiny web server")
    t_p2 = TaskRunState(task_id="podman_t0", name="podman : Podman task 0", status=Status.RUNNING)
    t_p2.hosts["host1"] = HostRunState(hostname="host1", status=Status.RUNNING)
    p2.tasks["podman_t0"] = t_p2
    state.plays["p2"] = p2

    return state


def _walk_all_nodes(tree) -> list[TreeNode[str]]:
    """Depth-first walk of every TreeNode under ``tree.root``.

    Used by the tests to find nodes by their ``data`` key without
    depending on the visual indentation that Textual manages
    internally.
    """
    nodes: list[TreeNode[str]] = []

    def _walk(node: TreeNode[str]) -> None:
        nodes.append(node)
        for child in node.children:
            _walk(child)

    for child in tree.root.children:
        _walk(child)
    return nodes


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestPopulateFromProjectionFooters:
    """``populate_from_projection`` maps ``TreeProjection.tree_lines`` to
    Textual ``TreeNode`` objects, including the ``kind="more"`` footers
    emitted by T2's two-cut truncation."""

    def test_tui_renders_two_level_truncation(self) -> None:
        """A two-cut projection (budget=15, 33 podman tasks) renders
        exactly two ``"more:"`` data keys (inner + outer footer)."""
        from ansible_aom.tui.widgets.task_tree import TaskTree

        state = _two_level_state()
        projection = TreeProjection.from_run_state(state)
        # Sanity: the projection actually produces two footers for this
        # state + budget. If T2's algorithm changes and stops emitting
        # the inner footer, this test should fail at the data layer.
        lines = projection.tree_lines(budget=15)
        more_lines = [ln for ln in lines if ln.kind == "more"]
        assert len(more_lines) == 2, (
            f"fixture must produce 2 'more' footers for budget=15; got {len(more_lines)} "
            f"in:\n{[ln.label for ln in lines]}"
        )

        tree = TaskTree("Playbook")
        tree.populate_from_projection(projection, budget=15)

        nodes = _walk_all_nodes(tree)
        more_nodes = [n for n in nodes if isinstance(n.data, str) and n.data.startswith("more:")]
        assert len(more_nodes) == 2, (
            f"expected exactly 2 'more:' TreeNodes (inner + outer footer); "
            f"got {len(more_nodes)} with data={[n.data for n in more_nodes]}"
        )

    def test_tui_more_node_is_not_expandable(self) -> None:
        """Both footers must have ``allow_expand=False`` so the user
        cannot expand a "… and N more tasks" line."""
        from ansible_aom.tui.widgets.task_tree import TaskTree

        state = _two_level_state()
        projection = TreeProjection.from_run_state(state)
        tree = TaskTree("Playbook")
        tree.populate_from_projection(projection, budget=15)

        nodes = _walk_all_nodes(tree)
        more_nodes = [n for n in nodes if isinstance(n.data, str) and n.data.startswith("more:")]
        assert len(more_nodes) == 2, "fixture must produce 2 'more:' footers"
        for n in more_nodes:
            assert n.allow_expand is False, (
                f"footer node must have allow_expand=False; got {n.allow_expand!r} "
                f"for data={n.data!r}"
            )
            # ``TreeNode.children`` is an ``ImmutableSequenceView`` (a custom
            # list-like wrapper that does NOT implement ``__eq__``) — direct
            # equality ``n.children == []`` is identity-based and always
            # False. Use ``list(...) == []`` to compare values.
            assert list(n.children) == [], (
                f"footer node must have no children; got {[c.data for c in n.children]!r} "
                f"for data={n.data!r}"
            )

    def test_tui_role_label_remaining_in_textual_tree(self) -> None:
        """When the budget cut lands inside a role, the role's
        TreeNode label must contain ``"remaining"`` (T3 contract)."""
        from ansible_aom.tui.widgets.task_tree import TaskTree

        state = _two_level_state()
        projection = TreeProjection.from_run_state(state)
        # budget=12 forces the cut inside the podman role: the head
        # (playbook + smfc play + smfc role + 3 smfc tasks + smfc host
        # leaves + Podman play + podman role) consumes most of the
        # budget, and the visible tasks under podman (1-2 of 33) leave
        # the rest to the inner footer. The role label must switch to
        # ``(M remaining)`` because visible < total.
        tree = TaskTree("Playbook")
        tree.populate_from_projection(projection, budget=12)

        # Sanity: this fixture + budget must actually produce a podman
        # role node. If the projection's bookkeeping changes and the
        # podman role drops out of the visible window, this test fails
        # at the data layer — not the TUI layer — which is the right
        # place to detect it.
        lines = projection.tree_lines(budget=12)
        podman_role_lines = [ln for ln in lines if ln.kind == "role" and ln.identity == "podman"]
        assert podman_role_lines, (
            f"fixture must produce a podman role TreeLine at budget=12; "
            f"got kinds={[ln.kind for ln in lines]}"
        )
        assert "remaining" in podman_role_lines[0].label, (
            f"data-layer role label must already say '(M remaining)'; "
            f"got {podman_role_lines[0].label!r}"
        )

        nodes = _walk_all_nodes(tree)
        role_nodes = [n for n in nodes if isinstance(n.data, str) and n.data.startswith("role:")]
        assert role_nodes, "fixture must produce at least one 'role:' TreeNode"
        # Find the podman role specifically.
        podman_nodes = [n for n in role_nodes if "podman" in str(n.label)]
        assert podman_nodes, f"expected a podman role node; got {[n.data for n in role_nodes]}"
        # The label must contain "remaining" — Rich's Text ``__contains__``
        # checks the plain text, so the assertion reads naturally.
        label_str = str(podman_nodes[0].label)
        assert "remaining" in label_str, (
            f"role label must say '(M remaining)' inside the cut; got {label_str!r}"
        )
        assert "(" in label_str and ")" in label_str, (
            f"role label must carry the count parens; got {label_str!r}"
        )

    def test_tui_more_node_styled_dim_italic(self) -> None:
        """Both footers must carry the ``"dim italic"`` style so they
        read as metadata, not as a real task/role/host."""
        from ansible_aom.tui.widgets.task_tree import TaskTree

        state = _two_level_state()
        projection = TreeProjection.from_run_state(state)
        tree = TaskTree("Playbook")
        tree.populate_from_projection(projection, budget=15)

        nodes = _walk_all_nodes(tree)
        more_nodes = [n for n in nodes if isinstance(n.data, str) and n.data.startswith("more:")]
        assert len(more_nodes) == 2, "fixture must produce 2 'more:' footers"
        for n in more_nodes:
            label = n.label
            # ``label`` is a Rich ``Text`` (because ``process_label`` always
            # coerces). The ``.style`` attribute is the string passed to
            # ``Text(..., style="dim italic")`` and reads back exactly.
            style_str = str(getattr(label, "style", ""))
            assert "dim" in style_str, (
                f"footer label must carry 'dim' style; got {style_str!r} for data={n.data!r}"
            )
            assert "italic" in style_str, (
                f"footer label must carry 'italic' style; got {style_str!r} for data={n.data!r}"
            )
