# CLI Interface Tests

> 169 nodes · cohesion 0.02

## Key Concepts

- **.from_run_state()** (199 connections) — `src/ansible_aom/core/tree_projection.py`
- **test_tree_projection.py** (26 connections) — `tests/unit/test_tree_projection.py`
- **TestTemplateVariableNameMismatch** (19 connections) — `tests/unit/test_template_variable_names.py`
- **TestHostRows** (19 connections) — `tests/unit/test_tree_projection.py`
- **TestTwoLevelTruncation** (17 connections) — `tests/unit/test_tree_projection.py`
- **TestTaskCompletionLifecycle** (15 connections) — `tests/unit/test_tree_projection.py`
- **TestMultiPlayTruncationWithRoleFooters** (14 connections) — `tests/unit/test_tree_projection.py`
- **._many_tasks_state()** (14 connections) — `tests/unit/test_tree_projection.py`
- **TestRoleLabelsAfterTruncation** (12 connections) — `tests/unit/test_tree_projection.py`
- **TestTreeLinesBasic** (12 connections) — `tests/unit/test_tree_projection.py`
- **_play_def()** (11 connections) — `tests/unit/test_template_variable_names.py`
- **_td()** (11 connections) — `tests/unit/test_template_variable_names.py`
- **TestTreeLinesPruning** (11 connections) — `tests/unit/test_tree_projection.py`
- **TestTreeLinesRolesAndFanOut** (11 connections) — `tests/unit/test_tree_projection.py`
- **._single_play_single_role_state()** (11 connections) — `tests/unit/test_tree_projection.py`
- **._multi_host_state()** (10 connections) — `tests/unit/test_tree_projection.py`
- **TestVisibility** (10 connections) — `tests/unit/test_tree_projection.py`
- **_running_state()** (9 connections) — `tests/compact/test_spinner_animation.py`
- **._multi_play_completed_state()** (9 connections) — `tests/unit/test_tree_projection.py`
- **TestTreeLineIdentity** (9 connections) — `tests/unit/test_tree_projection.py`
- **TestTreeLinesTaskIdentity** (8 connections) — `tests/unit/test_tree_projection.py`
- **_running_loop_state()** (7 connections) — `tests/unit/test_loop_item_count.py`
- **.test_no_inner_footer_when_role_has_no_remaining()** (7 connections) — `tests/unit/test_tree_projection.py`
- **.test_inner_footer_does_not_count_upcoming_plays_tasks()** (7 connections) — `tests/unit/test_tree_projection.py`
- **.test_outer_footer_appears_when_budget_overflow()** (7 connections) — `tests/unit/test_tree_projection.py`
- *... and 144 more nodes in this community*

## Relationships

- [Compact Renderer Implementation](Compact_Renderer_Implementation.md) (53 shared connections)
- [Status Bar Warning Panels](Status_Bar_Warning_Panels.md) (46 shared connections)
- [Per-Task Overhead Analysis](Per-Task_Overhead_Analysis.md) (44 shared connections)
- [CLI Argument Parser](CLI_Argument_Parser.md) (34 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (30 shared connections)
- [Runner Session Recording](Runner_Session_Recording.md) (15 shared connections)
- [Compact Renderer Integration Tests](Compact_Renderer_Integration_Tests.md) (14 shared connections)
- [Pause Prompt Heuristic](Pause_Prompt_Heuristic.md) (13 shared connections)
- [Four-Layer Redaction System](Four-Layer_Redaction_System.md) (11 shared connections)
- [RunState Property Invariants](RunState_Property_Invariants.md) (11 shared connections)
- [Run Diagnostics Tests](Run_Diagnostics_Tests.md) (11 shared connections)
- [Rerun Host Set Composition](Rerun_Host_Set_Composition.md) (4 shared connections)

## Source Files

- `src/ansible_aom/core/tree_projection.py`
- `tests/compact/test_spinner_animation.py`
- `tests/unit/test_loop_item_count.py`
- `tests/unit/test_template_variable_names.py`
- `tests/unit/test_tree_meta_hostless.py`
- `tests/unit/test_tree_projection.py`

## Audit Trail

- EXTRACTED: 812 (90%)
- INFERRED: 95 (10%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*