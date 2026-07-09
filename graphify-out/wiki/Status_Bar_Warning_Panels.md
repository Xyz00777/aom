# Status Bar Warning Panels

> 258 nodes · cohesion 0.01

## Key Concepts

- **RunState** (559 connections) — `src/ansible_aom/core/run_state.py`
- **test_event_processing.py** (27 connections) — `tests/unit/test_event_processing.py`
- **TestRunState** (21 connections) — `tests/unit/test_models.py`
- **TestHandleEventDispatcher** (17 connections) — `tests/unit/test_event_processing.py`
- **TestElapsedTimeFormat** (15 connections) — `tests/unit/test_event_processing.py`
- **TestHandleEventMalformedPayloads** (15 connections) — `tests/unit/test_event_processing.py`
- **TestPlaybookOnStats** (13 connections) — `tests/unit/test_event_processing.py`
- **count_completed_tasks()** (11 connections) — `src/ansible_aom/compact/format.py`
- **._graft_or_match_task()** (11 connections) — `src/ansible_aom/core/run_state.py`
- **TestEventProcessingEdgeCases** (11 connections) — `tests/unit/test_event_processing.py`
- **TestHandleEventTimestampParsing** (11 connections) — `tests/unit/test_event_processing.py`
- **TestHandleEventUnknownType** (11 connections) — `tests/unit/test_event_processing.py`
- **TestHandlerTaskStart** (11 connections) — `tests/unit/test_event_processing.py`
- **TestPlaybookOnStart** (11 connections) — `tests/unit/test_event_processing.py`
- **TestPlayStart** (11 connections) — `tests/unit/test_event_processing.py`
- **TestRunnerOnFailedStateTransition** (11 connections) — `tests/unit/test_event_processing.py`
- **TestRunnerOnOk** (11 connections) — `tests/unit/test_event_processing.py`
- **TestRunnerOnOkStatus** (11 connections) — `tests/unit/test_event_processing.py`
- **TestRunnerOnStartTaskCreation** (11 connections) — `tests/unit/test_event_processing.py`
- **TestTaskStart** (11 connections) — `tests/unit/test_event_processing.py`
- **TestV2PlaybookOnStatsCrossCheck** (11 connections) — `tests/unit/test_host_resolution.py`
- **_seed_run_state()** (10 connections) — `tests/unit/test_event_processing.py`
- **TestRunnerOnFailed** (10 connections) — `tests/unit/test_event_processing.py`
- **TestRunnerOnFailedIgnoreErrors** (10 connections) — `tests/unit/test_event_processing.py`
- **TestRunnerOnSkipped** (10 connections) — `tests/unit/test_event_processing.py`
- *... and 233 more nodes in this community*

## Relationships

- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (158 shared connections)
- [Compact Renderer Implementation](Compact_Renderer_Implementation.md) (60 shared connections)
- [CLI Interface Tests](CLI_Interface_Tests.md) (46 shared connections)
- [CLI Argument Parser](CLI_Argument_Parser.md) (45 shared connections)
- [Status Icon Animation Tests](Status_Icon_Animation_Tests.md) (34 shared connections)
- [Compact Renderer Integration Tests](Compact_Renderer_Integration_Tests.md) (30 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (27 shared connections)
- [Per-Task Overhead Analysis](Per-Task_Overhead_Analysis.md) (20 shared connections)
- [Inspect CLI Commands](Inspect_CLI_Commands.md) (16 shared connections)
- [Session Recording Tests](Session_Recording_Tests.md) (12 shared connections)
- [Runner Session Recording](Runner_Session_Recording.md) (12 shared connections)
- [Run History Mining](Run_History_Mining.md) (11 shared connections)

## Source Files

- `src/ansible_aom/compact/format.py`
- `src/ansible_aom/core/run_state.py`
- `src/ansible_aom/tui/app.py`
- `tests/compact/test_task_progress.py`
- `tests/unit/test_dynamic_counters.py`
- `tests/unit/test_event_processing.py`
- `tests/unit/test_host_resolution.py`
- `tests/unit/test_models.py`

## Audit Trail

- EXTRACTED: 861 (62%)
- INFERRED: 528 (38%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*