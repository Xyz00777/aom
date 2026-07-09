# State Machine Happy Path

> 16 nodes · cohesion 0.25

## Key Concepts

- **cli_main()** (12 connections) — `src/ansible_aom/drivers/replay.py`
- **TestReplayCLIMain** (8 connections) — `tests/unit/test_cli_replay.py`
- **Path** (7 connections)
- **_make_session()** (6 connections) — `tests/unit/test_cli_replay.py`
- **test_cli_replay.py** (5 connections) — `tests/unit/test_cli_replay.py`
- **.test_cli_main_speed_zero_allowed()** (5 connections) — `tests/unit/test_cli_replay.py`
- **.test_cli_main_default_uses_compact_renderer()** (4 connections) — `tests/unit/test_cli_replay.py`
- **.test_cli_main_speed_forwarded()** (4 connections) — `tests/unit/test_cli_replay.py`
- **.test_cli_main_tui_flag_selects_tui_renderer()** (4 connections) — `tests/unit/test_cli_replay.py`
- **.test_compact_and_tui_are_mutually_exclusive()** (4 connections) — `tests/unit/test_cli_replay.py`
- **.test_cli_main_returns_1_when_session_missing()** (3 connections) — `tests/unit/test_cli_replay.py`
- **Entry point for ``aom replay <session-id> [...]``.      Argparse the supplied ta** (1 connections) — `src/ansible_aom/drivers/replay.py`
- **CLI tests for the F2 `aom replay` subcommand dispatch.  Mirrors the inspect-disp** (1 connections) — `tests/unit/test_cli_replay.py`
- **`--speed 0` is the documented "fast as possible" sentinel.** (1 connections) — `tests/unit/test_cli_replay.py`
- **Passing both --compact and --tui exits with usage error (argparse SystemExit).** (1 connections) — `tests/unit/test_cli_replay.py`
- **`replay.cli_main` parses argv, builds a renderer, calls replay_session.** (1 connections) — `tests/unit/test_cli_replay.py`

## Relationships

- [Community 504](Community_504.md) (2 shared connections)
- [Diagnostics Layer Tests](Diagnostics_Layer_Tests.md) (2 shared connections)
- [Preflight Summary Rendering](Preflight_Summary_Rendering.md) (1 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (1 shared connections)
- [Community 571](Community_571.md) (1 shared connections)

## Source Files

- `src/ansible_aom/drivers/replay.py`
- `tests/unit/test_cli_replay.py`

## Audit Trail

- EXTRACTED: 54 (81%)
- INFERRED: 13 (19%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*