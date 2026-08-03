# cli_main

> 18 nodes · cohesion 0.18

## Key Concepts

- **cli_main()** (13 connections) — `src/ansible_aom/drivers/replay.py`
- **TestReplayCLIMain** (6 connections) — `tests/unit/test_cli_replay.py`
- **test_cli_replay.py** (5 connections) — `tests/unit/test_cli_replay.py`
- **_make_session()** (5 connections) — `tests/unit/test_cli_replay.py`
- **Path** (5 connections)
- **.test_cli_main_speed_zero_allowed()** (5 connections) — `tests/unit/test_cli_replay.py`
- **.test_cli_main_default_uses_compact_renderer()** (4 connections) — `tests/unit/test_cli_replay.py`
- **.test_cli_main_speed_forwarded()** (4 connections) — `tests/unit/test_cli_replay.py`
- **TestReplayDispatch** (4 connections) — `tests/unit/test_cli_replay.py`
- **.test_cli_main_returns_1_when_session_missing()** (3 connections) — `tests/unit/test_cli_replay.py`
- **.test_replay_dispatches_to_replay_main()** (2 connections) — `tests/unit/test_cli_replay.py`
- **Entry point for ``aom replay <session-id> [...]``.      Argparse the supplied ta** (1 connections) — `src/ansible_aom/drivers/replay.py`
- **CLI tests for the F2 `aom replay` subcommand dispatch.  Mirrors the inspect-disp** (1 connections) — `tests/unit/test_cli_replay.py`
- **`--speed 0` is the documented "fast as possible" sentinel.** (1 connections) — `tests/unit/test_cli_replay.py`
- **`aom replay <id>` invokes the replay CLI entry with ['<id>'].** (1 connections) — `tests/unit/test_cli_replay.py`
- **`replay.cli_main` parses argv, builds a renderer, calls replay_session.** (1 connections) — `tests/unit/test_cli_replay.py`
- **.test_replay_forwards_speed_flag()** (1 connections) — `tests/unit/test_cli_replay.py`
- **.test_replay_propagates_exit_code()** (1 connections) — `tests/unit/test_cli_replay.py`

## Relationships

- [load_session](load_session.md) (2 shared connections)
- [json.py](json.py.md) (2 shared connections)
- [ReplayDriver](ReplayDriver.md) (2 shared connections)
- [ansible_aom/cli.py](ansible_aom-cli.py.md) (1 shared connections)
- [Ansible Posix Availability](Ansible_Posix_Availability.md) (1 shared connections)
- [create_renderer](create_renderer.md) (1 shared connections)

## Source Files

- `src/ansible_aom/drivers/replay.py`
- `tests/unit/test_cli_replay.py`

## Audit Trail

- EXTRACTED: 55 (87%)
- INFERRED: 8 (13%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*