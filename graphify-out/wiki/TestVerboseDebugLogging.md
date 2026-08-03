# TestVerboseDebugLogging

> 10 nodes · cohesion 0.20

## Key Concepts

- **TestVerboseDebugLogging** (13 connections) — `tests/unit/test_cli.py`
- **.test_non_verbose_does_not_set_debug_level()** (2 connections) — `tests/unit/test_cli.py`
- **.test_verbose_creates_log_file_with_debug_entries()** (2 connections) — `tests/unit/test_cli.py`
- **.test_verbose_sets_debug_log_level()** (2 connections) — `tests/unit/test_cli.py`
- **.test_verbose_sets_diagnostics_debug_flag()** (2 connections) — `tests/unit/test_cli.py`
- **Tests for TC-009: Verbose enables DEBUG logging.** (1 connections) — `tests/unit/test_cli.py`
- **TC-009: --verbose sets logging level to DEBUG.** (1 connections) — `tests/unit/test_cli.py`
- **TC-009: --verbose causes DEBUG entries in log output.** (1 connections) — `tests/unit/test_cli.py`
- **TC-009: Without --verbose, logging level is not DEBUG.** (1 connections) — `tests/unit/test_cli.py`
- **--verbose should set diagnostics._debug to True.** (1 connections) — `tests/unit/test_cli.py`

## Relationships

- [HostRunState](HostRunState.md) (6 shared connections)
- [CompactRenderer](CompactRenderer.md) (1 shared connections)
- [RunState](RunState.md) (1 shared connections)

## Source Files

- `tests/unit/test_cli.py`

## Audit Trail

- EXTRACTED: 19 (73%)
- INFERRED: 7 (27%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*