# Secret Redaction Configuration

> 186 nodes · cohesion 0.02

## Key Concepts

- **PreParseResult** (35 connections) — `src/ansible_aom/core/parser.py`
- **parse_list_tasks_output()** (31 connections) — `src/ansible_aom/core/parser.py`
- **parse_list_hosts_output()** (28 connections) — `src/ansible_aom/core/parser.py`
- **TestListTasksEdgeCases** (26 connections) — `tests/unit/test_parser.py`
- **TestListTasksParser** (25 connections) — `tests/unit/test_parser.py`
- **test_parser.py** (24 connections) — `tests/unit/test_parser.py`
- **TestListHostsEdgeCases** (23 connections) — `tests/unit/test_parser.py`
- **preflight.py** (22 connections) — `src/ansible_aom/ansible/preflight.py`
- **TestRoleGrouping** (21 connections) — `tests/unit/test_parser.py`
- **TestListHostsParser** (20 connections) — `tests/unit/test_parser.py`
- **TestRunStateUnknownEvent** (19 connections) — `tests/unit/test_parser.py`
- **TestMultiLineWarningContinuation** (18 connections) — `tests/unit/test_parser.py`
- **TestPtyStreamParserJsonlEvents** (18 connections) — `tests/unit/test_parser.py`
- **TestListHostsFallback** (17 connections) — `tests/unit/test_parser.py`
- **TestListTasksListHostsIntegration** (16 connections) — `tests/unit/test_parser.py`
- **TestParallelPreParse** (16 connections) — `tests/unit/test_parser.py`
- **TestPtyStreamParserPlaintextCap** (16 connections) — `tests/unit/test_parser.py`
- **assemble_definitions()** (14 connections) — `src/ansible_aom/ansible/preflight.py`
- **group_roles()** (11 connections) — `src/ansible_aom/core/parser.py`
- **TestListHostsResolvesHostnames** (10 connections) — `tests/unit/test_host_resolution.py`
- **test_host_resolution.py** (9 connections) — `tests/unit/test_host_resolution.py`
- **.test_assemble_definitions_transfers_resolved_hosts()** (5 connections) — `tests/unit/test_host_resolution.py`
- **.test_preparse_result_assembly()** (5 connections) — `tests/unit/test_parser.py`
- **test_assemble_definitions_combines_tasks_and_hosts()** (5 connections) — `tests/unit/test_preflight.py`
- **.test_list_hosts_all_inventory()** (4 connections) — `tests/unit/test_parser.py`
- *... and 161 more nodes in this community*

## Relationships

- [CLI Interface Tests](CLI_Interface_Tests.md) (64 shared connections)
- [Run State Completion Recap](Run_State_Completion_Recap.md) (36 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (34 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (33 shared connections)
- [Three-Pane Inspect App](Three-Pane_Inspect_App.md) (18 shared connections)
- [Task Definition Live Refresh](Task_Definition_Live_Refresh.md) (17 shared connections)
- [State Machine Module](State_Machine_Module.md) (14 shared connections)
- [Ungrouped Role Tree Tests](Ungrouped_Role_Tree_Tests.md) (6 shared connections)
- [test_replay_determinism.py](test_replay_determinism.py.md) (2 shared connections)
- [Tree Block Animation](Tree_Block_Animation.md) (1 shared connections)
- [Heartbeat Liveness Tracker](Heartbeat_Liveness_Tracker.md) (1 shared connections)
- [Status Icon Animation Tests](Status_Icon_Animation_Tests.md) (1 shared connections)

## Source Files

- `src/ansible_aom/ansible/preflight.py`
- `src/ansible_aom/core/parser.py`
- `tests/unit/test_host_resolution.py`
- `tests/unit/test_parser.py`
- `tests/unit/test_preflight.py`

## Audit Trail

- EXTRACTED: 429 (57%)
- INFERRED: 325 (43%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*