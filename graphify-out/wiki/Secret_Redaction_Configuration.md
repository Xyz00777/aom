# Secret Redaction Configuration

> 110 nodes · cohesion 0.02

## Key Concepts

- **PreParseResult** (40 connections) — `src/ansible_aom/core/parser.py`
- **test_parser.py** (28 connections) — `tests/unit/test_parser.py`
- **TestRoleGrouping** (21 connections) — `tests/unit/test_parser.py`
- **TestTaskDefinition** (20 connections) — `tests/unit/test_parser.py`
- **TestRunStateUnknownEvent** (19 connections) — `tests/unit/test_parser.py`
- **TestPlayDefinition** (18 connections) — `tests/unit/test_parser.py`
- **TestPtyStreamParserJsonlEvents** (18 connections) — `tests/unit/test_parser.py`
- **TestPlayRunState** (17 connections) — `tests/unit/test_parser.py`
- **TestHostRunState** (16 connections) — `tests/unit/test_parser.py`
- **TestListTasksListHostsIntegration** (16 connections) — `tests/unit/test_parser.py`
- **TestParallelPreParse** (16 connections) — `tests/unit/test_parser.py`
- **TestPtyStreamParserPlaintextCap** (16 connections) — `tests/unit/test_parser.py`
- **TestRoleGroupDefinition** (16 connections) — `tests/unit/test_parser.py`
- **TestStatusEnum** (16 connections) — `tests/unit/test_parser.py`
- **TestTaskRunState** (16 connections) — `tests/unit/test_parser.py`
- **group_roles()** (10 connections) — `src/ansible_aom/core/parser.py`
- **.test_preparse_result_assembly()** (5 connections) — `tests/unit/test_parser.py`
- **.test_five_same_role_tasks_creates_group()** (5 connections) — `tests/unit/test_parser.py`
- **.test_role_group_at_end_of_list()** (5 connections) — `tests/unit/test_parser.py`
- **.test_parallel_parse_does_not_corrupt_data()** (4 connections) — `tests/unit/test_parser.py`
- **.test_role_group_definition_creation()** (4 connections) — `tests/unit/test_parser.py`
- **.test_role_group_name_property()** (4 connections) — `tests/unit/test_parser.py`
- **.test_four_same_role_tasks_no_grouping()** (4 connections) — `tests/unit/test_parser.py`
- **.test_mixed_roles_no_grouping()** (4 connections) — `tests/unit/test_parser.py`
- **.test_multiple_role_groups()** (4 connections) — `tests/unit/test_parser.py`
- *... and 85 more nodes in this community*

## Relationships

- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (46 shared connections)
- [Compact Renderer Implementation](Compact_Renderer_Implementation.md) (28 shared connections)
- [Run State Completion Recap](Run_State_Completion_Recap.md) (25 shared connections)
- [Per-Task Overhead Analysis](Per-Task_Overhead_Analysis.md) (20 shared connections)
- [Three-Pane Inspect App](Three-Pane_Inspect_App.md) (19 shared connections)
- [CLI Argument Parser](CLI_Argument_Parser.md) (18 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (15 shared connections)
- [Task Definition Live Refresh](Task_Definition_Live_Refresh.md) (14 shared connections)
- [Compact Renderer Integration Tests](Compact_Renderer_Integration_Tests.md) (13 shared connections)
- [Diagnostics and Profiler](Diagnostics_and_Profiler.md) (8 shared connections)
- [List Hosts Output Parser](List_Hosts_Output_Parser.md) (7 shared connections)
- [Status Bar Warning Panels](Status_Bar_Warning_Panels.md) (5 shared connections)

## Source Files

- `src/ansible_aom/core/parser.py`
- `tests/unit/test_parser.py`

## Audit Trail

- EXTRACTED: 233 (48%)
- INFERRED: 254 (52%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*