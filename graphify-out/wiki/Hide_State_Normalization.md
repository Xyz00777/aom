# Hide State Normalization

> 28 nodes · cohesion 0.16

## Key Concepts

- **replay_session()** (30 connections) — `src/ansible_aom/drivers/replay.py`
- **_make_session()** (13 connections) — `tests/unit/test_replay.py`
- **Path** (13 connections)
- **unit/test_replay.py** (8 connections) — `tests/unit/test_replay.py`
- **TestReplayCompletionFromMeta** (6 connections) — `tests/unit/test_replay.py`
- **TestReplaySpeedControl** (5 connections) — `tests/unit/test_replay.py`
- **.test_status_completed()** (4 connections) — `tests/unit/test_replay.py`
- **.test_status_crashed()** (4 connections) — `tests/unit/test_replay.py`
- **.test_status_failed()** (4 connections) — `tests/unit/test_replay.py`
- **TestReplayKeyboardInterrupt** (4 connections) — `tests/unit/test_replay.py`
- **.test_keyboard_interrupt_during_sleep()** (4 connections) — `tests/unit/test_replay.py`
- **.test_keyboard_interrupt_during_update_state()** (4 connections) — `tests/unit/test_replay.py`
- **.test_out_of_order_timestamps_do_not_sleep_negative()** (4 connections) — `tests/unit/test_replay.py`
- **.test_renderer_receives_each_event_in_order()** (4 connections) — `tests/unit/test_replay.py`
- **.test_speed_one_sleeps_real_delta_seconds()** (4 connections) — `tests/unit/test_replay.py`
- **.test_speed_two_halves_sleeps()** (4 connections) — `tests/unit/test_replay.py`
- **.test_speed_zero_makes_no_sleep_calls()** (4 connections) — `tests/unit/test_replay.py`
- **.test_missing_status_defaults_to_completed()** (3 connections) — `tests/unit/test_replay.py`
- **TestReplayNegativeDelta** (3 connections) — `tests/unit/test_replay.py`
- **TestReplaySessionBasic** (3 connections) — `tests/unit/test_replay.py`
- **.test_returns_minus_one_when_session_missing()** (3 connections) — `tests/unit/test_replay.py`
- **Replay ``session_id`` from ``session_dir`` through ``renderer``.      Args:** (1 connections) — `src/ansible_aom/drivers/replay.py`
- **Unit tests for F2 replay_session.  Replay reads `events.jsonl` + `meta.json` fro** (1 connections) — `tests/unit/test_replay.py`
- **Real ansible JSONL is not strictly monotonic across threads.      A delta of -0.** (1 connections) — `tests/unit/test_replay.py`
- **`handle_completion` is called with the meta.json status.** (1 connections) — `tests/unit/test_replay.py`
- *... and 3 more nodes in this community*

## Relationships

- [Play Boundary State Tests](Play_Boundary_State_Tests.md) (4 shared connections)
- [Include Import Role Tasks](Include_Import_Role_Tasks.md) (3 shared connections)
- [StatusBarConfig Model](StatusBarConfig_Model.md) (2 shared connections)
- [Diagnostics Layer Tests](Diagnostics_Layer_Tests.md) (2 shared connections)
- [test_replay_determinism.py](test_replay_determinism.py.md) (2 shared connections)
- [Diagnostics CLI Wiring](Diagnostics_CLI_Wiring.md) (2 shared connections)
- [Interactive Prompt Tests](Interactive_Prompt_Tests.md) (1 shared connections)
- [Include Role Discovery](Include_Role_Discovery.md) (1 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (1 shared connections)

## Source Files

- `src/ansible_aom/drivers/replay.py`
- `tests/unit/test_replay.py`

## Audit Trail

- EXTRACTED: 102 (74%)
- INFERRED: 36 (26%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*