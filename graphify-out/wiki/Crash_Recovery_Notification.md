# Crash Recovery Notification

> 12 nodes · cohesion 0.17

## Key Concepts

- **icons.py** (7 connections) — `src/ansible_aom/core/icons.py`
- **get_running_frame()** (7 connections) — `src/ansible_aom/core/icons.py`
- **get_status_icon()** (3 connections) — `src/ansible_aom/core/icons.py`
- **.test_four_frames_per_second_timing()** (3 connections) — `tests/unit/test_icons.py`
- **.test_get_running_frame_cycles_correctly()** (3 connections) — `tests/unit/test_icons.py`
- **.test_get_running_frame_large_counter()** (3 connections) — `tests/unit/test_icons.py`
- **Status icon mapping for AOM display.  This module provides Unicode status icons** (1 connections) — `src/ansible_aom/core/icons.py`
- **Get the current animation frame for RUNNING status.      Cycles through the 4 qu** (1 connections) — `src/ansible_aom/core/icons.py`
- **Get the icon for a given status.      For RUNNING status, use the frame paramete** (1 connections) — `src/ansible_aom/core/icons.py`
- **TC-372: get_running_frame cycles through 4 frames correctly.** (1 connections) — `tests/unit/test_icons.py`
- **TC-372: Large counter values still cycle correctly.** (1 connections) — `tests/unit/test_icons.py`
- **TC-372: Animation completes full cycle in 1 second (4 frames @ 4 FPS).** (1 connections) — `tests/unit/test_icons.py`

## Relationships

- [Error Handling Tests](Error_Handling_Tests.md) (3 shared connections)
- [Dirty Flag Throttle](Dirty_Flag_Throttle.md) (1 shared connections)
- [Pydantic Model Basics](Pydantic_Model_Basics.md) (1 shared connections)
- [Ansible Args Validation](Ansible_Args_Validation.md) (1 shared connections)
- [Session List View](Session_List_View.md) (1 shared connections)
- [RunState Property Invariants](RunState_Property_Invariants.md) (1 shared connections)
- [Pause Prompt Heuristic](Pause_Prompt_Heuristic.md) (1 shared connections)
- [Compact Renderer Integration Tests](Compact_Renderer_Integration_Tests.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/icons.py`
- `tests/unit/test_icons.py`

## Audit Trail

- EXTRACTED: 24 (75%)
- INFERRED: 8 (25%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*