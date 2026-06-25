# Replay Command Dispatch

> 6 nodes · cohesion 0.33

## Key Concepts

- **TestReplayDispatch** (5 connections) — `tests/unit/test_cli_replay.py`
- **.test_replay_dispatches_to_replay_main()** (2 connections) — `tests/unit/test_cli_replay.py`
- **`aom replay <id>` invokes the replay CLI entry with ['<id>'].** (1 connections) — `tests/unit/test_cli_replay.py`
- **.test_replay_forwards_renderer_flags()** (1 connections) — `tests/unit/test_cli_replay.py`
- **.test_replay_forwards_speed_flag()** (1 connections) — `tests/unit/test_cli_replay.py`
- **.test_replay_propagates_exit_code()** (1 connections) — `tests/unit/test_cli_replay.py`

## Relationships

- [[Replay CLI Subcommand]] (1 shared connections)

## Source Files

- `tests/unit/test_cli_replay.py`

## Audit Trail

- EXTRACTED: 11 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*