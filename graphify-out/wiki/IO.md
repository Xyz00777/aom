# IO

> 24 nodes · cohesion 0.09

## Key Concepts

- **IO** (13 connections)
- **display.py** (11 connections) — `src/ansible_aom/compact/display.py`
- **test_small_terminal.py** (8 connections) — `tests/compact/test_small_terminal.py`
- **test_display_ansi.py** (5 connections) — `tests/compact/test_display_ansi.py`
- **TestSynchronizedOutput** (5 connections) — `tests/compact/test_display_ansi.py`
- **TestForceSizePassthrough** (5 connections) — `tests/compact/test_small_terminal.py`
- **print_summary_if_debug()** (4 connections) — `src/ansible_aom/core/diagnostics.py`
- **TestThresholdConstant** (4 connections) — `tests/compact/test_small_terminal.py`
- **.test_non_tty_update_emits_no_ansi()** (3 connections) — `tests/compact/test_display_ansi.py`
- **.test_start_without_force_size_works_as_before()** (3 connections) — `tests/compact/test_small_terminal.py`
- **check_terminal_size()** (2 connections) — `src/ansible_aom/compact/display.py`
- **.test_update_wraps_content_in_dec_2026_sync()** (2 connections) — `tests/compact/test_display_ansi.py`
- **.test_start_accepts_force_size_kwarg_without_error()** (2 connections) — `tests/compact/test_small_terminal.py`
- **Display logic for compact mode — nom-style fixed-bottom status panel.  Renders d** (1 connections) — `src/ansible_aom/compact/display.py`
- **Check if terminal meets minimum size requirements.      Args:         lines: Num** (1 connections) — `src/ansible_aom/compact/display.py`
- **Emit a single-line ``[aom-debug] …`` post-run digest to ``file``.      Silent un** (1 connections) — `src/ansible_aom/core/diagnostics.py`
- **Tests for nom-style ANSI rendering in compact mode.  These tests pin the new-spe** (1 connections) — `tests/compact/test_display_ansi.py`
- **Each Display.update() in TTY mode emits a single DEC 2026 frame.** (1 connections) — `tests/compact/test_display_ansi.py`
- **is_tty=False is the pipe/CI fallback (PQ6): never emit positioning.** (1 connections) — `tests/compact/test_display_ansi.py`
- **Tests for R4 — graceful degradation on terminals smaller than 80×24.  Today the** (1 connections) — `tests/compact/test_small_terminal.py`
- **The (cols, rows) threshold lives as a module constant so tests     can reference** (1 connections) — `tests/compact/test_small_terminal.py`
- **`force_size` is the test injection seam for the size detection     that Task 2 w** (1 connections) — `tests/compact/test_small_terminal.py`
- **Backwards-compatible: existing callers don't pass force_size.** (1 connections) — `tests/compact/test_small_terminal.py`
- **.test_minimum_size_is_80_cols_24_rows()** (1 connections) — `tests/compact/test_small_terminal.py`

## Relationships

- [Display](Display.md) (10 shared connections)
- [Per-Task Timing Tests](Per-Task_Timing_Tests.md) (2 shared connections)
- [renderer.py](renderer.py.md) (2 shared connections)
- [diagnostics.py](diagnostics.py.md) (2 shared connections)
- [_row_count](_row_count.md) (2 shared connections)
- [Inspect CLI Module](Inspect_CLI_Module.md) (1 shared connections)
- [RunSummary Schema Contract](RunSummary_Schema_Contract.md) (1 shared connections)
- [HostRunState](HostRunState.md) (1 shared connections)
- [Secret Redaction Layers](Secret_Redaction_Layers.md) (1 shared connections)
- [Color ASCII Fallback](Color_ASCII_Fallback.md) (1 shared connections)
- [core/__init__.py](core-__init__.py.md) (1 shared connections)
- [KeyAction TypedDict](KeyAction_TypedDict.md) (1 shared connections)

## Source Files

- `src/ansible_aom/compact/display.py`
- `src/ansible_aom/core/diagnostics.py`
- `tests/compact/test_display_ansi.py`
- `tests/compact/test_small_terminal.py`

## Audit Trail

- EXTRACTED: 75 (96%)
- INFERRED: 3 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*