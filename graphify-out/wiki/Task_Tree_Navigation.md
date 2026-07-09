# Task Tree Navigation

> 15 nodes · cohesion 0.17

## Key Concepts

- **test_ctrl_c_race.py** (5 connections) — `tests/integration/test_ctrl_c_race.py`
- **_fake_ansible_command()** (5 connections) — `tests/integration/test_ctrl_c_race.py`
- **TestCtrlCAfterCompletion** (5 connections) — `tests/integration/test_ctrl_c_race.py`
- **.test_signal_after_drive_returns_non_zero_exit_code()** (4 connections) — `tests/integration/test_ctrl_c_race.py`
- **.test_signal_after_drive_returns_real_exit_code()** (4 connections) — `tests/integration/test_ctrl_c_race.py`
- **.test_signal_after_drive_returns_run_result_when_handler_already_ran()** (4 connections) — `tests/integration/test_ctrl_c_race.py`
- **.test_keyboard_interrupt_during_drive_returns_130()** (4 connections) — `tests/integration/test_ctrl_c_race.py`
- **TestCtrlCDuringRun** (3 connections) — `tests/integration/test_ctrl_c_race.py`
- **Batch E item #10b — R7 Ctrl-C race with completion.  SIGINT can arrive at any of** (1 connections) — `tests/integration/test_ctrl_c_race.py`
- **Same as above but the child failed (exit 2). The real exit         code still wi** (1 connections) — `tests/integration/test_ctrl_c_race.py`
- **If SIGINT arrives *after* ``handle_completion`` has fully run         (i.e. insi** (1 connections) — `tests/integration/test_ctrl_c_race.py`
- **SIGINT before ``playbook_on_stats`` — runner returns 130.** (1 connections) — `tests/integration/test_ctrl_c_race.py`
- **Variant A: signal arrives mid-stream, completion never happens.** (1 connections) — `tests/integration/test_ctrl_c_race.py`
- **Variant B: completion arrives first, then SIGINT.      R7 spec: completion wins.** (1 connections) — `tests/integration/test_ctrl_c_race.py`
- **The run completed cleanly (exit 0). SIGINT arrives during the         ``renderer** (1 connections) — `tests/integration/test_ctrl_c_race.py`

## Relationships

- [Tree Block Animation](Tree_Block_Animation.md) (4 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (1 shared connections)

## Source Files

- `tests/integration/test_ctrl_c_race.py`

## Audit Trail

- EXTRACTED: 37 (90%)
- INFERRED: 4 (10%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*