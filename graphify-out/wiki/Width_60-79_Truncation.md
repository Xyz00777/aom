# Width 60-79 Truncation

> 16 nodes · cohesion 0.17

## Key Concepts

- **test_diagnostics_wiring.py** (9 connections) — `tests/unit/test_diagnostics_wiring.py`
- **_assert_installed()** (5 connections) — `tests/unit/test_diagnostics_wiring.py`
- **test_cli_main_installs_diagnostics()** (4 connections) — `tests/unit/test_diagnostics_wiring.py`
- **test_inspect_main_installs_diagnostics()** (4 connections) — `tests/unit/test_diagnostics_wiring.py`
- **test_replay_main_installs_diagnostics()** (3 connections) — `tests/unit/test_diagnostics_wiring.py`
- **test_rerun_main_installs_diagnostics()** (3 connections) — `tests/unit/test_diagnostics_wiring.py`
- **test_runner_trace_enabled_follows_aom_debug()** (3 connections) — `tests/unit/test_diagnostics_wiring.py`
- **MonkeyPatch** (2 connections)
- **Path** (1 connections)
- **Verify every CLI entry point installs the diagnostics layer.  Phase 2 of docs/su** (1 connections) — `tests/unit/test_diagnostics_wiring.py`
- **``aom`` with no args prints help and exits cleanly.** (1 connections) — `tests/unit/test_diagnostics_wiring.py`
- **``aom inspect --text`` with empty state-dir prints "no sessions".** (1 connections) — `tests/unit/test_diagnostics_wiring.py`
- **``aom rerun --help`` exits via argparse before any rerun logic runs.** (1 connections) — `tests/unit/test_diagnostics_wiring.py`
- **``aom replay --help`` exits via argparse before any replay runs.** (1 connections) — `tests/unit/test_diagnostics_wiring.py`
- **The runner's per-loop pexpect trace is now folded into AOM_DEBUG.** (1 connections) — `tests/unit/test_diagnostics_wiring.py`
- **_reset()** (1 connections) — `tests/unit/test_diagnostics_wiring.py`

## Relationships

- [core/__init__.py](core-__init__.py.md) (1 shared connections)

## Source Files

- `tests/unit/test_diagnostics_wiring.py`

## Audit Trail

- EXTRACTED: 41 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*