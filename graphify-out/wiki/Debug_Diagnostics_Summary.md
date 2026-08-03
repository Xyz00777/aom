# Debug Diagnostics Summary

> 8 nodes · cohesion 0.25

## Key Concepts

- **LiveDriver** (12 connections) — `src/ansible_aom/drivers/live.py`
- **test_live_driver_satisfies_event_source()** (4 connections) — `tests/unit/test_event_source.py`
- **.drive()** (3 connections) — `src/ansible_aom/drivers/live.py`
- **.__init__()** (2 connections) — `src/ansible_aom/drivers/live.py`
- **.ansible_args()** (1 connections) — `src/ansible_aom/drivers/live.py`
- **Path** (1 connections)
- **Spawns ``ansible-playbook`` and pumps its JSONL output.      Parameters mirror :** (1 connections) — `src/ansible_aom/drivers/live.py`
- **LiveDriver is the production EventSource for ansible-playbook runs.** (1 connections) — `tests/unit/test_event_source.py`

## Relationships

- [Diagnostics Layer Tests](Diagnostics_Layer_Tests.md) (4 shared connections)
- [First Ctrl-C Cancellation](First_Ctrl-C_Cancellation.md) (2 shared connections)
- [Interactive Prompt Tests](Interactive_Prompt_Tests.md) (2 shared connections)
- [WarningType Enum](WarningType_Enum.md) (1 shared connections)
- [Session Diagnostics Writing](Session_Diagnostics_Writing.md) (1 shared connections)
- [Replay Determinism Tests](Replay_Determinism_Tests.md) (1 shared connections)

## Source Files

- `src/ansible_aom/drivers/live.py`
- `tests/unit/test_event_source.py`

## Audit Trail

- EXTRACTED: 17 (68%)
- INFERRED: 8 (32%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*