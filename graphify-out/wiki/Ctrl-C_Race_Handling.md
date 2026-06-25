# Ctrl-C Race Handling

> 13 nodes · cohesion 0.19

## Key Concepts

- **test_ctrl_c_race.py** (4 connections) — `tests/integration/test_ctrl_c_race.py`
- **_fake_ansible_command()** (4 connections) — `tests/integration/test_ctrl_c_race.py`
- **TestCtrlCAfterCompletionDocumentsCurrentBehavior** (4 connections) — `tests/integration/test_ctrl_c_race.py`
- **.test_signal_after_drive_returns_run_result_when_handler_already_ran()** (4 connections) — `tests/integration/test_ctrl_c_race.py`
- **.test_signal_after_drive_still_maps_to_130()** (4 connections) — `tests/integration/test_ctrl_c_race.py`
- **.test_keyboard_interrupt_during_drive_returns_130()** (4 connections) — `tests/integration/test_ctrl_c_race.py`
- **TestCtrlCDuringRun** (3 connections) — `tests/integration/test_ctrl_c_race.py`
- **Batch E item #10b — R7 Ctrl-C race with completion.  SIGINT can arrive at any of** (1 connections) — `tests/integration/test_ctrl_c_race.py`
- **If SIGINT arrives *after* ``handle_completion`` has fully run         (i.e. insi** (1 connections) — `tests/integration/test_ctrl_c_race.py`
- **SIGINT before ``playbook_on_stats`` — runner returns 130.** (1 connections) — `tests/integration/test_ctrl_c_race.py`
- **Variant A: signal arrives mid-stream, completion never happens.** (1 connections) — `tests/integration/test_ctrl_c_race.py`
- **Variant B: completion arrives first, then SIGINT.      Currently the runner's ou** (1 connections) — `tests/integration/test_ctrl_c_race.py`
- **The run completed cleanly (exit 0). SIGINT arrives during the         ``renderer** (1 connections) — `tests/integration/test_ctrl_c_race.py`

## Relationships

- [[Playbook Run Integration Tests]] (3 shared connections)

## Source Files

- `tests/integration/test_ctrl_c_race.py`

## Audit Trail

- EXTRACTED: 30 (91%)
- INFERRED: 3 (9%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*