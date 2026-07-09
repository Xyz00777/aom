# Password Prompt Handling

> 17 nodes · cohesion 0.18

## Key Concepts

- **TestPopulateFromProjectionFooters** (14 connections) — `tests/tui/test_tree_more_footers.py`
- **_two_level_state()** (13 connections) — `tests/tui/test_tree_more_footers.py`
- **_walk_all_nodes()** (7 connections) — `tests/tui/test_tree_more_footers.py`
- **.test_tui_more_node_is_not_expandable()** (6 connections) — `tests/tui/test_tree_more_footers.py`
- **.test_tui_more_node_styled_dim_italic()** (6 connections) — `tests/tui/test_tree_more_footers.py`
- **.test_tui_renders_two_level_truncation()** (6 connections) — `tests/tui/test_tree_more_footers.py`
- **.test_tui_role_label_carries_total_in_textual_tree()** (6 connections) — `tests/tui/test_tree_more_footers.py`
- **test_tree_more_footers.py** (4 connections) — `tests/tui/test_tree_more_footers.py`
- **TreeNode** (1 connections)
- **Tests for TUI parity of the two-level truncation (``populate_from_projection``).** (1 connections) — `tests/tui/test_tree_more_footers.py`
- **Depth-first walk of every TreeNode under ``tree.root``.      Used by the tests t** (1 connections) — `tests/tui/test_tree_more_footers.py`
- **``populate_from_projection`` maps ``TreeProjection.tree_lines`` to     Textual `** (1 connections) — `tests/tui/test_tree_more_footers.py`
- **A two-cut projection (budget=15, 33 podman tasks) renders         exactly two ``** (1 connections) — `tests/tui/test_tree_more_footers.py`
- **Both footers must have ``allow_expand=False`` so the user         cannot expand** (1 connections) — `tests/tui/test_tree_more_footers.py`
- **When the budget cut lands inside a role, the role's         TreeNode label must** (1 connections) — `tests/tui/test_tree_more_footers.py`
- **Both footers must carry the ``"dim italic"`` style so they         read as metad** (1 connections) — `tests/tui/test_tree_more_footers.py`
- **Build the user's sketch shape: two plays, second with a 33-task     ``podman`` r** (1 connections) — `tests/tui/test_tree_more_footers.py`

## Relationships

- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (6 shared connections)
- [Session Recording Tests](Session_Recording_Tests.md) (5 shared connections)
- [CLI Interface Tests](CLI_Interface_Tests.md) (4 shared connections)
- [Compact Renderer Implementation](Compact_Renderer_Implementation.md) (2 shared connections)
- [Per-Task Overhead Analysis](Per-Task_Overhead_Analysis.md) (2 shared connections)
- [CLI Argument Parser](CLI_Argument_Parser.md) (2 shared connections)
- [Compact Renderer Integration Tests](Compact_Renderer_Integration_Tests.md) (1 shared connections)
- [Status Bar Warning Panels](Status_Bar_Warning_Panels.md) (1 shared connections)

## Source Files

- `tests/tui/test_tree_more_footers.py`

## Audit Trail

- EXTRACTED: 53 (75%)
- INFERRED: 18 (25%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*