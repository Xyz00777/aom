# Session Replay Round Trip

> 34 nodes · cohesion 0.10

## Key Concepts

- **replay_session()** (23 connections) — `src/ansible_aom/drivers/replay.py`
- **_make_session()** (13 connections) — `tests/unit/test_replay.py`
- **test_replay.py** (7 connections) — `tests/unit/test_replay.py`
- **.test_replay_uses_meta_status_failed_when_recorded_failed()** (6 connections) — `tests/integration/test_replay.py`
- **TestReplayCompletionFromMeta** (6 connections) — `tests/unit/test_replay.py`
- **.test_record_then_replay_produces_same_event_sequence()** (5 connections) — `tests/integration/test_replay.py`
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
- **test_replay.py** (3 connections) — `tests/integration/test_replay.py`
- **_fake_ansible_command()** (3 connections) — `tests/integration/test_replay.py`
- **TestRecordThenReplay** (3 connections) — `tests/integration/test_replay.py`
- **.test_missing_status_defaults_to_completed()** (3 connections) — `tests/unit/test_replay.py`
- **TestReplayNegativeDelta** (3 connections) — `tests/unit/test_replay.py`
- **TestReplaySessionBasic** (3 connections) — `tests/unit/test_replay.py`
- **.test_returns_minus_one_when_session_missing()** (3 connections) — `tests/unit/test_replay.py`
- *... and 9 more nodes in this community*

## Relationships

- [[Run Config Key Normalization]] (16 shared connections)
- [[Replay CLI Subcommand]] (2 shared connections)
- [[Replay Determinism Tests]] (2 shared connections)
- [[Playbook Run Integration Tests]] (2 shared connections)
- [[Renderer Event Protocol]] (1 shared connections)
- [[Inspect CLI Commands]] (1 shared connections)
- [[Session Replay Driver]] (1 shared connections)

## Source Files

- `src/ansible_aom/drivers/replay.py`
- `tests/integration/test_replay.py`
- `tests/unit/test_replay.py`

## Audit Trail

- EXTRACTED: 106 (76%)
- INFERRED: 33 (24%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*