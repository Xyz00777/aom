# Install Completion Flag

> 12 nodes · cohesion 0.17

## Key Concepts

- **TestExitCodes** (15 connections) — `tests/unit/test_cli.py`
- **.test_exit_code_0_for_help()** (2 connections) — `tests/unit/test_cli.py`
- **.test_exit_code_0_for_version()** (2 connections) — `tests/unit/test_cli.py`
- **.test_exit_code_127_for_missing_ansible()** (2 connections) — `tests/unit/test_cli.py`
- **.test_exit_code_130_for_sigint()** (2 connections) — `tests/unit/test_cli.py`
- **.test_main_returns_int()** (2 connections) — `tests/unit/test_cli.py`
- **Tests for TC-024, TC-025, TC-027, TC-028: Exit Codes.** (1 connections) — `tests/unit/test_cli.py`
- **TC-024: Exit code 0 for --help.** (1 connections) — `tests/unit/test_cli.py`
- **TC-024: Exit code 0 for --version.** (1 connections) — `tests/unit/test_cli.py`
- **TC-027: Exit code 127 when ansible-playbook not found.          The runner is re** (1 connections) — `tests/unit/test_cli.py`
- **TC-028: Exit code 130 for user cancelled (Ctrl+C).** (1 connections) — `tests/unit/test_cli.py`
- **TC-024: main() returns integer exit code.** (1 connections) — `tests/unit/test_cli.py`

## Relationships

- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (4 shared connections)
- [App Configuration Settings](App_Configuration_Settings.md) (1 shared connections)
- [Compact Renderer Integration Tests](Compact_Renderer_Integration_Tests.md) (1 shared connections)
- [Status Bar Warning Panels](Status_Bar_Warning_Panels.md) (1 shared connections)
- [Inspect Data Model Builders](Inspect_Data_Model_Builders.md) (1 shared connections)
- [Session Recording Tests](Session_Recording_Tests.md) (1 shared connections)

## Source Files

- `tests/unit/test_cli.py`

## Audit Trail

- EXTRACTED: 23 (74%)
- INFERRED: 8 (26%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*