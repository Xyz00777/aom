# Ctrl-C Race Handling

> 5 nodes · cohesion 0.19

## Key Concepts

- **_fake_ansible_command()** (5 connections) — `tests/integration/test_ctrl_c_race.py`
- **test_ctrl_c_race.py** (4 connections) — `tests/integration/test_ctrl_c_race.py`
- **.test_keyboard_interrupt_during_drive_returns_130()** (4 connections) — `tests/integration/test_ctrl_c_race.py`
- **TestCtrlCDuringRun** (3 connections) — `tests/integration/test_ctrl_c_race.py`
- **Batch E item #10b — R7 Ctrl-C race with completion.  SIGINT can arrive at any of** (1 connections) — `tests/integration/test_ctrl_c_race.py`

## Relationships

- [[Playbook Run Integration Tests]] (1 shared connections)

## Source Files

- `tests/integration/test_ctrl_c_race.py`

## Audit Trail

- EXTRACTED: 16 (94%)
- INFERRED: 1 (6%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*