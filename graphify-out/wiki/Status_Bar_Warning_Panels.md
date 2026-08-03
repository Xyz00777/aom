# Status Bar Warning Panels

> 160 nodes · cohesion 0.01

## Key Concepts

- **test_event_processing.py** (30 connections) — `tests/unit/test_event_processing.py`
- **TestHandleEventDispatcher** (17 connections) — `tests/unit/test_event_processing.py`
- **TestTaskMatchingAlgorithm** (16 connections) — `tests/unit/test_event_processing.py`
- **TestEventProcessingEdgeCases** (11 connections) — `tests/unit/test_event_processing.py`
- **TestHandleEventUnknownType** (11 connections) — `tests/unit/test_event_processing.py`
- **TestHandlerTaskStart** (11 connections) — `tests/unit/test_event_processing.py`
- **TestPlaybookOnStart** (11 connections) — `tests/unit/test_event_processing.py`
- **TestRunnerOnFailed** (11 connections) — `tests/unit/test_event_processing.py`
- **TestRunnerOnFailedIgnoreErrors** (11 connections) — `tests/unit/test_event_processing.py`
- **TestRunnerOnFailedStateTransition** (11 connections) — `tests/unit/test_event_processing.py`
- **TestRunnerOnOk** (11 connections) — `tests/unit/test_event_processing.py`
- **TestRunnerOnOkStatus** (11 connections) — `tests/unit/test_event_processing.py`
- **TestRunnerOnStartTaskCreation** (11 connections) — `tests/unit/test_event_processing.py`
- **TestTaskStart** (11 connections) — `tests/unit/test_event_processing.py`
- **TestRunnerOnSkipped** (10 connections) — `tests/unit/test_event_processing.py`
- **TestRunnerOnStartStrategy** (10 connections) — `tests/unit/test_event_processing.py`
- **TestRunnerOnUnreachable** (10 connections) — `tests/unit/test_event_processing.py`
- **TestStatsCrossValidation** (10 connections) — `tests/unit/test_event_processing.py`
- **TestTerminalEventsPreserveStartTime** (10 connections) — `tests/unit/test_event_processing.py`
- **TestRunnerOnUnreachableStateTransition** (9 connections) — `tests/unit/test_event_processing.py`
- **.test_runner_ok_creates_host_run_state()** (4 connections) — `tests/unit/test_event_processing.py`
- **.test_runner_skipped_creates_skipped_host()** (4 connections) — `tests/unit/test_event_processing.py`
- **.test_runner_start_creates_task_run_state()** (4 connections) — `tests/unit/test_event_processing.py`
- **.test_runner_unreachable_triggers_runstate_failed()** (4 connections) — `tests/unit/test_event_processing.py`
- **.test_event_with_missing_optional_fields()** (3 connections) — `tests/unit/test_event_processing.py`
- *... and 135 more nodes in this community*

## Relationships

- [CLI Interface Tests](CLI_Interface_Tests.md) (98 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (63 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (19 shared connections)
- [Task Definition Live Refresh](Task_Definition_Live_Refresh.md) (1 shared connections)
- [Status Icon Animation Tests](Status_Icon_Animation_Tests.md) (1 shared connections)
- [Run Diagnostics Tests](Run_Diagnostics_Tests.md) (1 shared connections)
- [Design Specs Plans](Design_Specs_Plans.md) (1 shared connections)
- [Limit Args Merging](Limit_Args_Merging.md) (1 shared connections)
- [Incremental Task Counters](Incremental_Task_Counters.md) (1 shared connections)

## Source Files

- `tests/unit/test_event_processing.py`

## Audit Trail

- EXTRACTED: 386 (76%)
- INFERRED: 124 (24%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*