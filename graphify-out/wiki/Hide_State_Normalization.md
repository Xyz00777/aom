# Hide State Normalization

> 36 nodes · cohesion 0.11

## Key Concepts

- **replay_session()** (30 connections) — `src/ansible_aom/drivers/replay.py`
- **_make_session()** (13 connections) — `tests/unit/test_replay.py`
- **Path** (13 connections)
- **test_replay.py** (8 connections) — `tests/unit/test_replay.py`
- **.test_replay_uses_meta_status_failed_when_recorded_failed()** (6 connections) — `tests/integration/test_replay.py`
- **TestReplayCompletionFromMeta** (6 connections) — `tests/unit/test_replay.py`
- **.test_record_then_replay_produces_same_event_sequence()** (5 connections) — `tests/integration/test_replay.py`
- **TestReplaySpeedControl** (5 connections) — `tests/unit/test_replay.py`
- **test_replay.py** (4 connections) — `tests/integration/test_replay.py`
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
- **_fake_ansible_command()** (3 connections) — `tests/integration/test_replay.py`
- **TestRecordThenReplay** (3 connections) — `tests/integration/test_replay.py`
- **.test_missing_status_defaults_to_completed()** (3 connections) — `tests/unit/test_replay.py`
- **TestReplayNegativeDelta** (3 connections) — `tests/unit/test_replay.py`
- **TestReplaySessionBasic** (3 connections) — `tests/unit/test_replay.py`
- *... and 11 more nodes in this community*

## Relationships

- [Play Boundary State Tests](Play_Boundary_State_Tests.md) (4 shared connections)
- [Include Import Role Tasks](Include_Import_Role_Tasks.md) (3 shared connections)
- [Community 504](Community_504.md) (2 shared connections)
- [Diagnostics Layer Tests](Diagnostics_Layer_Tests.md) (2 shared connections)
- [Community 602](Community_602.md) (2 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (2 shared connections)
- [Tree Block Animation](Tree_Block_Animation.md) (2 shared connections)
- [Interactive Prompt Tests](Interactive_Prompt_Tests.md) (1 shared connections)
- [Total Task Counting](Total_Task_Counting.md) (1 shared connections)

## Source Files

- `src/ansible_aom/drivers/replay.py`
- `tests/integration/test_replay.py`
- `tests/unit/test_replay.py`

## Audit Trail

- EXTRACTED: 123 (75%)
- INFERRED: 40 (25%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*