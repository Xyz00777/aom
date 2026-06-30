# Replay CLI Subcommand

> 22 nodes · cohesion 0.13

## Key Concepts

- **cli_main()** (12 connections) — `src/ansible_aom/drivers/replay.py`
- **TestReplayCLIMain** (8 connections) — `tests/unit/test_cli_replay.py`
- **replay.py** (7 connections) — `src/ansible_aom/drivers/replay.py`
- **_make_session()** (6 connections) — `tests/unit/test_cli_replay.py`
- **ArgumentParser** (5 connections)
- **.test_cli_main_speed_zero_allowed()** (5 connections) — `tests/unit/test_cli_replay.py`
- **_build_parser()** (4 connections) — `src/ansible_aom/drivers/replay.py`
- **_parse_timestamp()** (4 connections) — `src/ansible_aom/drivers/replay.py`
- **test_cli_replay.py** (4 connections) — `tests/unit/test_cli_replay.py`
- **.test_cli_main_default_uses_compact_renderer()** (4 connections) — `tests/unit/test_cli_replay.py`
- **.test_cli_main_speed_forwarded()** (4 connections) — `tests/unit/test_cli_replay.py`
- **.test_cli_main_tui_flag_selects_tui_renderer()** (4 connections) — `tests/unit/test_cli_replay.py`
- **.test_compact_and_tui_are_mutually_exclusive()** (4 connections) — `tests/unit/test_cli_replay.py`
- **.test_cli_main_returns_1_when_session_missing()** (3 connections) — `tests/unit/test_cli_replay.py`
- **Replay a recorded AOM session through a Renderer (F2).  Both halves of the repla** (1 connections) — `src/ansible_aom/drivers/replay.py`
- **Build the ``aom replay`` argument parser.      Factored out of :func:`cli_main`** (1 connections) — `src/ansible_aom/drivers/replay.py`
- **Entry point for ``aom replay <session-id> [...]``.      Argparse the supplied ta** (1 connections) — `src/ansible_aom/drivers/replay.py`
- **Parse an ISO 8601 ``_timestamp`` field; return None when unparseable.** (1 connections) — `src/ansible_aom/drivers/replay.py`
- **CLI tests for the F2 `aom replay` subcommand dispatch.  Mirrors the inspect-disp** (1 connections) — `tests/unit/test_cli_replay.py`
- **`--speed 0` is the documented "fast as possible" sentinel.** (1 connections) — `tests/unit/test_cli_replay.py`
- **Passing both --compact and --tui exits with usage error (argparse SystemExit).** (1 connections) — `tests/unit/test_cli_replay.py`
- **`replay.cli_main` parses argv, builds a renderer, calls replay_session.** (1 connections) — `tests/unit/test_cli_replay.py`

## Relationships

- [[Run Config Key Normalization]] (7 shared connections)
- [[Session Replay Driver]] (3 shared connections)
- [[Run History Mining]] (2 shared connections)
- [[Session Replay Round Trip]] (2 shared connections)
- [[CLI Main Entry Point]] (1 shared connections)
- [[CLI Argument Parser]] (1 shared connections)
- [[Inspect CLI Commands]] (1 shared connections)
- [[Rerun CLI Parser]] (1 shared connections)
- [[Renderer Factory Function]] (1 shared connections)
- [[Replay Command Dispatch]] (1 shared connections)

## Source Files

- `src/ansible_aom/drivers/replay.py`
- `tests/unit/test_cli_replay.py`

## Audit Trail

- EXTRACTED: 69 (84%)
- INFERRED: 13 (16%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*