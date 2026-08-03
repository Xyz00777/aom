# .test_record_false_does_not_touch_default_state_dir

> 8 nodes · cohesion 0.36

## Key Concepts

- **.test_record_false_does_not_touch_default_state_dir()** (5 connections) — `tests/integration/test_no_record.py`
- **integration/test_no_record.py** (4 connections) — `tests/integration/test_no_record.py`
- **.test_record_false_writes_no_session_dir()** (4 connections) — `tests/integration/test_no_record.py`
- **_fake_ansible_command()** (3 connections) — `tests/integration/test_no_record.py`
- **TestNoRecordIntegration** (3 connections) — `tests/integration/test_no_record.py`
- **Path** (2 connections)
- **Integration test for F3 --no-record at the runner level.  The unit tests cover a** (1 connections) — `tests/integration/test_no_record.py`
- **Even if session_dir is None, record=False must not create the default.** (1 connections) — `tests/integration/test_no_record.py`

## Relationships

- [Replay Determinism Tests](Replay_Determinism_Tests.md) (2 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (1 shared connections)

## Source Files

- `tests/integration/test_no_record.py`

## Audit Trail

- EXTRACTED: 21 (91%)
- INFERRED: 2 (9%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*