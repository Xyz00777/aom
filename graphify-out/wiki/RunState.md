# RunState

> 266 nodes · cohesion 0.01

## Key Concepts

- **RunState** (581 connections) — `src/ansible_aom/core/run_state.py`
- **test_event_processing.py** (30 connections) — `tests/unit/test_event_processing.py`
- **TestRunState** (21 connections) — `tests/unit/test_models.py`
- **TestRunStateUnknownEvent** (19 connections) — `tests/unit/test_parser.py`
- **TestHandleEventDispatcher** (17 connections) — `tests/unit/test_event_processing.py`
- **datetime** (15 connections)
- **TestElapsedTimeFormat** (15 connections) — `tests/unit/test_event_processing.py`
- **TestHandleEventMalformedPayloads** (15 connections) — `tests/unit/test_event_processing.py`
- **._handle_v2_playbook_on_task_start()** (14 connections) — `src/ansible_aom/core/run_state.py`
- **TestTimestampLocalTimezone** (14 connections) — `tests/unit/test_event_processing.py`
- **._handle_v2_runner_on_start()** (13 connections) — `src/ansible_aom/core/run_state.py`
- **._task_dict()** (13 connections) — `src/ansible_aom/core/run_state.py`
- **TestPlaybookOnStats** (13 connections) — `tests/unit/test_event_processing.py`
- **._handle_v2_runner_on_failed()** (12 connections) — `src/ansible_aom/core/run_state.py`
- **._handle_v2_runner_on_ok()** (12 connections) — `src/ansible_aom/core/run_state.py`
- **._handle_v2_runner_on_skipped()** (12 connections) — `src/ansible_aom/core/run_state.py`
- **._handle_v2_runner_on_unreachable()** (12 connections) — `src/ansible_aom/core/run_state.py`
- **._resolve_play_id()** (12 connections) — `src/ansible_aom/core/run_state.py`
- **_reserve_host_run_state()** (11 connections) — `src/ansible_aom/core/run_state.py`
- **._resolve_runner_task()** (11 connections) — `src/ansible_aom/core/run_state.py`
- **TestEventProcessingEdgeCases** (11 connections) — `tests/unit/test_event_processing.py`
- **TestHandleEventTimestampParsing** (11 connections) — `tests/unit/test_event_processing.py`
- **TestHandleEventUnknownType** (11 connections) — `tests/unit/test_event_processing.py`
- **TestHandlerTaskStart** (11 connections) — `tests/unit/test_event_processing.py`
- **TestPlaybookOnStart** (11 connections) — `tests/unit/test_event_processing.py`
- *... and 241 more nodes in this community*

## Relationships

- [HostRunState](HostRunState.md) (208 shared connections)
- [TaskDefinition](TaskDefinition.md) (65 shared connections)
- [json.py](json.py.md) (42 shared connections)
- [PlayDefinition](PlayDefinition.md) (42 shared connections)
- [.from_run_state](from_run_state.md) (40 shared connections)
- [StreamPhase](StreamPhase.md) (28 shared connections)
- [_drive](_drive.md) (17 shared connections)
- [Inspect CLI Commands](Inspect_CLI_Commands.md) (16 shared connections)
- [AOM TUI Application](AOM_TUI_Application.md) (15 shared connections)
- [TestCrossPlayLookupIsolation](TestCrossPlayLookupIsolation.md) (12 shared connections)
- [TestV2PlaybookOnStatsCrossCheck](TestV2PlaybookOnStatsCrossCheck.md) (11 shared connections)
- [Run Diagnostics Tests](Run_Diagnostics_Tests.md) (9 shared connections)

## Source Files

- `src/ansible_aom/core/run_state.py`
- `src/ansible_aom/formats/json.py`
- `tests/unit/test_event_processing.py`
- `tests/unit/test_loop_item_count.py`
- `tests/unit/test_models.py`
- `tests/unit/test_parser.py`

## Audit Trail

- EXTRACTED: 1099 (71%)
- INFERRED: 446 (29%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*