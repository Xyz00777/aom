# View Mode Selection

> 16 nodes · cohesion 0.17

## Key Concepts

- **TestViewModeSelection** (9 connections) — `tests/unit/test_view_modes.py`
- **.select_view_mode()** (8 connections) — `tests/unit/test_view_modes.py`
- **.test_default_is_compact()** (3 connections) — `tests/unit/test_view_modes.py`
- **.test_non_tty_uses_streaming()** (3 connections) — `tests/unit/test_view_modes.py`
- **.test_tui_flag_enables_full_tui()** (3 connections) — `tests/unit/test_view_modes.py`
- **.test_tui_flag_ignored_without_tty()** (3 connections) — `tests/unit/test_view_modes.py`
- **.test_verbose_enables_logging_in_compact()** (3 connections) — `tests/unit/test_view_modes.py`
- **.test_verbose_non_tty_uses_streaming()** (3 connections) — `tests/unit/test_view_modes.py`
- **Tests for view mode selection logic.** (1 connections) — `tests/unit/test_view_modes.py`
- **Select renderer mode based on flags and terminal.          Args:             tui** (1 connections) — `tests/unit/test_view_modes.py`
- **Default mode is compact.** (1 connections) — `tests/unit/test_view_modes.py`
- **--tui flag enables full TUI when TTY available.** (1 connections) — `tests/unit/test_view_modes.py`
- **--tui flag ignored without TTY, uses streaming instead.** (1 connections) — `tests/unit/test_view_modes.py`
- **--verbose enables logging with Rich Live in compact mode.** (1 connections) — `tests/unit/test_view_modes.py`
- **Non-TTY uses streaming output.** (1 connections) — `tests/unit/test_view_modes.py`
- **--verbose with non-TTY still uses streaming.** (1 connections) — `tests/unit/test_view_modes.py`

## Relationships

- [[View Mode Selection]] (1 shared connections)

## Source Files

- `tests/unit/test_view_modes.py`

## Audit Trail

- EXTRACTED: 43 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*