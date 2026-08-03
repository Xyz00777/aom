# Diagnostics CLI Wiring

> 8 nodes · cohesion 0.36

## Key Concepts

- **.test_replay_uses_meta_status_failed_when_recorded_failed()** (6 connections) — `tests/integration/test_replay.py`
- **.test_record_then_replay_produces_same_event_sequence()** (5 connections) — `tests/integration/test_replay.py`
- **integration/test_replay.py** (4 connections) — `tests/integration/test_replay.py`
- **_fake_ansible_command()** (3 connections) — `tests/integration/test_replay.py`
- **TestRecordThenReplay** (3 connections) — `tests/integration/test_replay.py`
- **Path** (2 connections)
- **Integration test: record a fake run, then replay it.  Drives ``run_playbook`` ag** (1 connections) — `tests/integration/test_replay.py`
- **A recorded failure (exit 2) writes meta.status=failed; replay         forwards t** (1 connections) — `tests/integration/test_replay.py`

## Relationships

- [Replay Determinism Tests](Replay_Determinism_Tests.md) (2 shared connections)
- [Hide State Normalization](Hide_State_Normalization.md) (2 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (1 shared connections)

## Source Files

- `tests/integration/test_replay.py`

## Audit Trail

- EXTRACTED: 21 (84%)
- INFERRED: 4 (16%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*