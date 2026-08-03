# Role Chain Extraction

> 8 nodes · cohesion 0.25

## Key Concepts

- **TestInvocationModuleArgs** (6 connections) — `tests/unit/test_redaction.py`
- **.test_deeply_nested_args()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_module_args_list_values()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_module_args_recursive_redaction()** (4 connections) — `tests/unit/test_redaction.py`
- **Tests for TC-163: invocation.module_args redaction at -vvv.** (1 connections) — `tests/unit/test_redaction.py`
- **TC-163: Nested module args with exact-match secret keys are redacted.          Q** (1 connections) — `tests/unit/test_redaction.py`
- **TC-163 edge case: Deeply nested module args.          QC-002: ``secret_key`` is** (1 connections) — `tests/unit/test_redaction.py`
- **TC-163: Module args with list values containing secrets.** (1 connections) — `tests/unit/test_redaction.py`

## Relationships

- [TUI Tree View Tests](TUI_Tree_View_Tests.md) (3 shared connections)
- [Warnings Display Config](Warnings_Display_Config.md) (3 shared connections)
- [Timestamp Timezone Formatting](Timestamp_Timezone_Formatting.md) (2 shared connections)

## Source Files

- `tests/unit/test_redaction.py`

## Audit Trail

- EXTRACTED: 18 (82%)
- INFERRED: 4 (18%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*