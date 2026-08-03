# TestExitCodes

> 12 nodes · cohesion 0.17

## Key Concepts

- **TestExitCodes** (14 connections) — `tests/unit/test_cli.py`
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

- [HostRunState](HostRunState.md) (6 shared connections)
- [CompactRenderer](CompactRenderer.md) (1 shared connections)
- [RunState](RunState.md) (1 shared connections)

## Source Files

- `tests/unit/test_cli.py`

## Audit Trail

- EXTRACTED: 23 (77%)
- INFERRED: 7 (23%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*