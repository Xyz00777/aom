# Status Icon Animation Tests

> 92 nodes · cohesion 0.04

## Key Concepts

- **JsonlEvent** (57 connections) — `src/ansible_aom/core/event_types.py`
- **_BoundedDict** (18 connections) — `src/ansible_aom/core/run_state.py`
- **_BoundedSet** (18 connections) — `src/ansible_aom/core/run_state.py`
- **datetime** (14 connections)
- **._handle_v2_playbook_on_task_start()** (14 connections) — `src/ansible_aom/core/run_state.py`
- **._handle_v2_runner_on_start()** (13 connections) — `src/ansible_aom/core/run_state.py`
- **JsonlTask** (12 connections) — `src/ansible_aom/core/event_types.py`
- **run_state.py** (12 connections) — `src/ansible_aom/core/run_state.py`
- **_reserve_host_run_state()** (11 connections) — `src/ansible_aom/core/run_state.py`
- **._resolve_play_id()** (11 connections) — `src/ansible_aom/core/run_state.py`
- **._task_dict()** (11 connections) — `src/ansible_aom/core/run_state.py`
- **_iter_leaf_task_defs()** (10 connections) — `src/ansible_aom/core/run_state.py`
- **._handle_v2_runner_item_on()** (9 connections) — `src/ansible_aom/core/run_state.py`
- **._handle_v2_runner_on_failed()** (9 connections) — `src/ansible_aom/core/run_state.py`
- **._handle_v2_runner_on_ok()** (9 connections) — `src/ansible_aom/core/run_state.py`
- **._handle_v2_runner_on_skipped()** (9 connections) — `src/ansible_aom/core/run_state.py`
- **._handle_v2_runner_on_unreachable()** (9 connections) — `src/ansible_aom/core/run_state.py`
- **._hosts_dict()** (9 connections) — `src/ansible_aom/core/run_state.py`
- **RunSummary** (9 connections) — `src/ansible_aom/formats/json.py`
- **HostCounts** (8 connections) — `src/ansible_aom/formats/json.py`
- **TaskFailure** (8 connections) — `src/ansible_aom/formats/json.py`
- **JsonlHostResult** (7 connections) — `src/ansible_aom/core/event_types.py`
- **JsonlPlay** (7 connections) — `src/ansible_aom/core/event_types.py`
- **._finalize_play()** (7 connections) — `src/ansible_aom/core/run_state.py`
- **._handle_v2_playbook_on_play_start()** (7 connections) — `src/ansible_aom/core/run_state.py`
- *... and 67 more nodes in this community*

## Relationships

- [Status Bar Warning Panels](Status_Bar_Warning_Panels.md) (34 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (24 shared connections)
- [Compact Renderer Integration Tests](Compact_Renderer_Integration_Tests.md) (6 shared connections)
- [Tree Block Animation](Tree_Block_Animation.md) (5 shared connections)
- [Crash Recovery Panels](Crash_Recovery_Panels.md) (5 shared connections)
- [Heartbeat Liveness Tracker](Heartbeat_Liveness_Tracker.md) (5 shared connections)
- [16-Color Fallback](16-Color_Fallback.md) (5 shared connections)
- [Compact Renderer Implementation](Compact_Renderer_Implementation.md) (5 shared connections)
- [Per-Task Overhead Analysis](Per-Task_Overhead_Analysis.md) (5 shared connections)
- [Inspect Data Model Builders](Inspect_Data_Model_Builders.md) (4 shared connections)
- [CLI Argument Parser](CLI_Argument_Parser.md) (4 shared connections)
- [Rerun Confirmation Prompt](Rerun_Confirmation_Prompt.md) (4 shared connections)

## Source Files

- `src/ansible_aom/core/event_types.py`
- `src/ansible_aom/core/models.py`
- `src/ansible_aom/core/run_state.py`
- `src/ansible_aom/formats/json.py`
- `src/ansible_aom/tui/app.py`
- `tests/unit/test_json_renderer.py`

## Audit Trail

- EXTRACTED: 364 (81%)
- INFERRED: 84 (19%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*