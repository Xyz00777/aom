# State Machine Invariants

> 21 nodes · cohesion 0.13

## Key Concepts

- **KeyContext** (26 connections) — `src/ansible_aom/tui/keybindings.py`
- **KeyAction** (23 connections) — `src/ansible_aom/tui/keybindings.py`
- **keybindings.py** (9 connections) — `src/ansible_aom/tui/keybindings.py`
- **get_keybindings_by_context()** (8 connections) — `src/ansible_aom/tui/keybindings.py`
- **TestGetKeybindingsByContext** (8 connections) — `tests/tui/test_keybindings.py`
- **.test_get_global_keybindings()** (3 connections) — `tests/tui/test_keybindings.py`
- **.test_get_log_keybindings()** (3 connections) — `tests/tui/test_keybindings.py`
- **.test_get_post_run_keybindings()** (3 connections) — `tests/tui/test_keybindings.py`
- **.test_get_tree_keybindings()** (3 connections) — `tests/tui/test_keybindings.py`
- **Enum** (2 connections)
- **str** (1 connections)
- **TypedDict** (1 connections)
- **Keybindings configuration for AOM TUI.  This module defines all keyboard shortcu** (1 connections) — `src/ansible_aom/tui/keybindings.py`
- **Context where a keybinding is active.** (1 connections) — `src/ansible_aom/tui/keybindings.py`
- **Definition of a keybinding action.** (1 connections) — `src/ansible_aom/tui/keybindings.py`
- **Get all keybindings for a specific context.      Args:         context: The cont** (1 connections) — `src/ansible_aom/tui/keybindings.py`
- **Tests for get_keybindings_by_context function.** (1 connections) — `tests/tui/test_keybindings.py`
- **get_keybindings_by_context filters by GLOBAL context.** (1 connections) — `tests/tui/test_keybindings.py`
- **get_keybindings_by_context filters by TREE context.** (1 connections) — `tests/tui/test_keybindings.py`
- **get_keybindings_by_context filters by LOG context.** (1 connections) — `tests/tui/test_keybindings.py`
- **get_keybindings_by_context filters by POST_RUN context.** (1 connections) — `tests/tui/test_keybindings.py`

## Relationships

- [Warning Color Formatting](Warning_Color_Formatting.md) (5 shared connections)
- [Runner Event Batching](Runner_Event_Batching.md) (4 shared connections)
- [Status Icon Mapping](Status_Icon_Mapping.md) (3 shared connections)
- [Process Liveness Monitoring](Process_Liveness_Monitoring.md) (3 shared connections)
- [Module Init File](Module_Init_File.md) (3 shared connections)
- [Help Overlay TUI](Help_Overlay_TUI.md) (2 shared connections)
- [Community 569](Community_569.md) (2 shared connections)
- [Community 458](Community_458.md) (2 shared connections)
- [Community 459](Community_459.md) (2 shared connections)
- [Rerun Command Integration](Rerun_Command_Integration.md) (2 shared connections)
- [Community 568](Community_568.md) (2 shared connections)
- [Include Tasks Dynamic Grafting](Include_Tasks_Dynamic_Grafting.md) (2 shared connections)

## Source Files

- `src/ansible_aom/tui/keybindings.py`
- `tests/tui/test_keybindings.py`

## Audit Trail

- EXTRACTED: 50 (51%)
- INFERRED: 49 (49%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*