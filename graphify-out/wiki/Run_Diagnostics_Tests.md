# Run Diagnostics Tests

> 16 nodes · cohesion 0.12

## Key Concepts

- **_seed_run_state()** (10 connections) — `tests/unit/test_event_processing.py`
- **.test_recovery_after_malformed_event()** (3 connections) — `tests/unit/test_event_processing.py`
- **.test_runner_failed_with_hosts_as_list_does_not_raise()** (3 connections) — `tests/unit/test_event_processing.py`
- **.test_runner_failed_with_task_as_none_does_not_raise()** (3 connections) — `tests/unit/test_event_processing.py`
- **.test_runner_ok_with_hosts_as_list_does_not_raise()** (3 connections) — `tests/unit/test_event_processing.py`
- **.test_runner_skipped_with_hosts_as_list_does_not_raise()** (3 connections) — `tests/unit/test_event_processing.py`
- **.test_runner_unreachable_with_hosts_as_list_does_not_raise()** (3 connections) — `tests/unit/test_event_processing.py`
- **.test_runner_unreachable_with_task_as_string_does_not_raise()** (3 connections) — `tests/unit/test_event_processing.py`
- **Build a RunState with one play, one task, and one host already RUNNING.      The** (1 connections) — `tests/unit/test_event_processing.py`
- **TC-MITOGEN-1: ``task`` as a bare UUID string must be tolerated.          ansible** (1 connections) — `tests/unit/test_event_processing.py`
- **TC-MITOGEN-2: ``task: None`` must be tolerated.          Mitogen-shimmed actions** (1 connections) — `tests/unit/test_event_processing.py`
- **TC-MITOGEN-3: ``hosts`` as a list must be tolerated.          Mitogen aggregates** (1 connections) — `tests/unit/test_event_processing.py`
- **TC-MITOGEN-4: ``hosts: list`` on unreachable must also be tolerated.** (1 connections) — `tests/unit/test_event_processing.py`
- **TC-MITOGEN-5: ``hosts: list`` on failed must also be tolerated.** (1 connections) — `tests/unit/test_event_processing.py`
- **TC-MITOGEN-6: ``hosts: list`` on skipped must also be tolerated.** (1 connections) — `tests/unit/test_event_processing.py`
- **TC-MITOGEN-7: A malformed event does not poison subsequent events.          Afte** (1 connections) — `tests/unit/test_event_processing.py`

## Relationships

- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (7 shared connections)
- [CLI Interface Tests](CLI_Interface_Tests.md) (1 shared connections)
- [Status Bar Warning Panels](Status_Bar_Warning_Panels.md) (1 shared connections)

## Source Files

- `tests/unit/test_event_processing.py`

## Audit Trail

- EXTRACTED: 39 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*