# Frame Parameter Handling

> 13 nodes · cohesion 0.15

## Key Concepts

- **IO** (15 connections)
- **test_small_terminal.py** (8 connections) — `tests/compact/test_small_terminal.py`
- **TestForceSizePassthrough** (5 connections) — `tests/compact/test_small_terminal.py`
- **print_summary_if_debug()** (4 connections) — `src/ansible_aom/core/diagnostics.py`
- **TestThresholdConstant** (4 connections) — `tests/compact/test_small_terminal.py`
- **.test_start_without_force_size_works_as_before()** (3 connections) — `tests/compact/test_small_terminal.py`
- **.test_start_accepts_force_size_kwarg_without_error()** (2 connections) — `tests/compact/test_small_terminal.py`
- **Emit a single-line ``[aom-debug] …`` post-run digest to ``file``.      Silent un** (1 connections) — `src/ansible_aom/core/diagnostics.py`
- **Tests for R4 — graceful degradation on terminals smaller than 80×24.  Today the** (1 connections) — `tests/compact/test_small_terminal.py`
- **The (cols, rows) threshold lives as a module constant so tests     can reference** (1 connections) — `tests/compact/test_small_terminal.py`
- **`force_size` is the test injection seam for the size detection     that Task 2 w** (1 connections) — `tests/compact/test_small_terminal.py`
- **Backwards-compatible: existing callers don't pass force_size.** (1 connections) — `tests/compact/test_small_terminal.py`
- **.test_minimum_size_is_80_cols_24_rows()** (1 connections) — `tests/compact/test_small_terminal.py`

## Relationships

- [Compact Renderer Integration Tests](Compact_Renderer_Integration_Tests.md) (7 shared connections)
- [Inspect CLI Module](Inspect_CLI_Module.md) (1 shared connections)
- [Config Loading Screen](Config_Loading_Screen.md) (1 shared connections)
- [RunSummary Schema Contract](RunSummary_Schema_Contract.md) (1 shared connections)
- [Per-Task Timing Tests](Per-Task_Timing_Tests.md) (1 shared connections)
- [UUIDv7 Session Generation](UUIDv7_Session_Generation.md) (1 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (1 shared connections)
- [Inventory Auto Detection](Inventory_Auto_Detection.md) (1 shared connections)
- [Session Replay Round Trip](Session_Replay_Round_Trip.md) (1 shared connections)
- [Renderer Protocol Tests](Renderer_Protocol_Tests.md) (1 shared connections)
- [Secret Redaction Layers](Secret_Redaction_Layers.md) (1 shared connections)
- [Color ASCII Fallback](Color_ASCII_Fallback.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/diagnostics.py`
- `tests/compact/test_small_terminal.py`

## Audit Trail

- EXTRACTED: 45 (96%)
- INFERRED: 2 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*