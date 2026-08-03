# Redaction Config Model

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

- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (4 shared connections)
- [App Configuration Settings](App_Configuration_Settings.md) (1 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (1 shared connections)
- [CLI Interface Tests](CLI_Interface_Tests.md) (1 shared connections)
- [Inspect Data Model Builders](Inspect_Data_Model_Builders.md) (1 shared connections)

## Source Files

- `tests/unit/test_cli.py`

## Audit Trail

- EXTRACTED: 19 (73%)
- INFERRED: 7 (27%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*