# Frame Parameter Handling

> 20 nodes · cohesion 0.10

## Key Concepts

- **IO** (14 connections)
- **test_small_terminal.py** (7 connections) — `tests/compact/test_small_terminal.py`
- **TestDegradedModeFallthrough** (7 connections) — `tests/compact/test_small_terminal.py`
- **TestForceSizePassthrough** (5 connections) — `tests/compact/test_small_terminal.py`
- **TestThresholdConstant** (4 connections) — `tests/compact/test_small_terminal.py`
- **print_summary_if_debug()** (3 connections) — `src/ansible_aom/core/diagnostics.py`
- **.test_stop_in_degraded_mode_is_a_noop()** (2 connections) — `tests/compact/test_small_terminal.py`
- **.test_start_without_force_size_works_as_before()** (2 connections) — `tests/compact/test_small_terminal.py`
- **Emit a single-line ``[aom-debug] …`` post-run digest to ``file``.      Silent un** (1 connections) — `src/ansible_aom/core/diagnostics.py`
- **Tests for R4 — graceful degradation on terminals smaller than 80×24.  Today the** (1 connections) — `tests/compact/test_small_terminal.py`
- **In degraded mode update() drops the status content (we don't     flood stdout wi** (1 connections) — `tests/compact/test_small_terminal.py`
- **No panel was ever shown, so stop() must not emit clear/show         sequences th** (1 connections) — `tests/compact/test_small_terminal.py`
- **The (cols, rows) threshold lives as a module constant so tests     can reference** (1 connections) — `tests/compact/test_small_terminal.py`
- **`force_size` is the test injection seam for the size detection     that Task 2 w** (1 connections) — `tests/compact/test_small_terminal.py`
- **Backwards-compatible: existing callers don't pass force_size.** (1 connections) — `tests/compact/test_small_terminal.py`
- **.test_clear_in_degraded_mode_is_a_noop()** (1 connections) — `tests/compact/test_small_terminal.py`
- **.test_print_log_in_degraded_mode_emits_plain_text()** (1 connections) — `tests/compact/test_small_terminal.py`
- **.test_update_in_degraded_mode_emits_no_dec_frame()** (1 connections) — `tests/compact/test_small_terminal.py`
- **.test_start_accepts_force_size_kwarg_without_error()** (1 connections) — `tests/compact/test_small_terminal.py`
- **.test_minimum_size_is_80_cols_24_rows()** (1 connections) — `tests/compact/test_small_terminal.py`

## Relationships

- [Compact Renderer Integration Tests](Compact_Renderer_Integration_Tests.md) (4 shared connections)
- [Inspect CLI Module](Inspect_CLI_Module.md) (1 shared connections)
- [Config Loading Screen](Config_Loading_Screen.md) (1 shared connections)
- [RunSummary Schema Contract](RunSummary_Schema_Contract.md) (1 shared connections)
- [UUIDv7 Session Generation](UUIDv7_Session_Generation.md) (1 shared connections)
- [Inventory Auto Detection](Inventory_Auto_Detection.md) (1 shared connections)
- [Session Replay Round Trip](Session_Replay_Round_Trip.md) (1 shared connections)
- [Renderer Protocol Tests](Renderer_Protocol_Tests.md) (1 shared connections)
- [Secret Redaction Layers](Secret_Redaction_Layers.md) (1 shared connections)
- [Rerun CLI Parser](Rerun_CLI_Parser.md) (1 shared connections)
- [Community 486](Community_486.md) (1 shared connections)
- [KeyAction TypedDict](KeyAction_TypedDict.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/diagnostics.py`
- `tests/compact/test_small_terminal.py`

## Audit Trail

- EXTRACTED: 53 (95%)
- INFERRED: 3 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*