# Status Bar Color Tests

> 22 nodes · cohesion 0.09

## Key Concepts

- **TestTaskMatching** (24 connections) — `tests/unit/test_parser.py`
- **.test_dynamic_task_ordering()** (3 connections) — `tests/unit/test_parser.py`
- **.test_dynamic_task_parent_relationship()** (3 connections) — `tests/unit/test_parser.py`
- **.test_include_tasks_dynamic_expansion()** (3 connections) — `tests/unit/test_parser.py`
- **.test_multiple_dynamic_children()** (3 connections) — `tests/unit/test_parser.py`
- **.test_path_matching_when_uuid_differs()** (3 connections) — `tests/unit/test_parser.py`
- **.test_sequential_match_requires_all_three()** (3 connections) — `tests/unit/test_parser.py`
- **.test_task_matching_by_path()** (3 connections) — `tests/unit/test_parser.py`
- **.test_task_matching_by_sequential_and_name()** (3 connections) — `tests/unit/test_parser.py`
- **.test_task_matching_by_uuid()** (3 connections) — `tests/unit/test_parser.py`
- **.test_uuid_none_means_no_uuid_match()** (3 connections) — `tests/unit/test_parser.py`
- **TC-091 to TC-096: Task matching logic and dynamic expansion.** (1 connections) — `tests/unit/test_parser.py`
- **TC-091: Primary matching uses task UUID from JSONL.** (1 connections) — `tests/unit/test_parser.py`
- **TC-091: Task with uuid=None cannot match by UUID.** (1 connections) — `tests/unit/test_parser.py`
- **TC-092: Secondary matching uses task path (file:line format).** (1 connections) — `tests/unit/test_parser.py`
- **TC-092: Path match succeeds even when UUIDs differ.** (1 connections) — `tests/unit/test_parser.py`
- **TC-093: Fallback matching uses play_order, task_order, and name.** (1 connections) — `tests/unit/test_parser.py`
- **TC-093: Sequential match requires play_id + task_order + name all match.** (1 connections) — `tests/unit/test_parser.py`
- **TC-094: Dynamic tasks created with is_dynamic=True.** (1 connections) — `tests/unit/test_parser.py`
- **TC-095: Dynamic tasks are children of the include_tasks node.** (1 connections) — `tests/unit/test_parser.py`
- **TC-096: Dynamic tasks have task_order=-1, placed after static siblings.** (1 connections) — `tests/unit/test_parser.py`
- **TC-094: Multiple dynamic children under one include_tasks.** (1 connections) — `tests/unit/test_parser.py`

## Relationships

- [Compact Renderer Implementation](Compact_Renderer_Implementation.md) (11 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (3 shared connections)
- [Secret Redaction Configuration](Secret_Redaction_Configuration.md) (2 shared connections)
- [Compact Renderer Integration Tests](Compact_Renderer_Integration_Tests.md) (1 shared connections)
- [Task Definition Live Refresh](Task_Definition_Live_Refresh.md) (1 shared connections)
- [Per-Task Overhead Analysis](Per-Task_Overhead_Analysis.md) (1 shared connections)
- [CLI Argument Parser](CLI_Argument_Parser.md) (1 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (1 shared connections)
- [Three-Pane Inspect App](Three-Pane_Inspect_App.md) (1 shared connections)
- [Run State Completion Recap](Run_State_Completion_Recap.md) (1 shared connections)

## Source Files

- `tests/unit/test_parser.py`

## Audit Trail

- EXTRACTED: 43 (66%)
- INFERRED: 22 (34%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*