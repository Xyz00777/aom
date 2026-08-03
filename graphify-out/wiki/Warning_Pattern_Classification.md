# Warning Pattern Classification

> 36 nodes · cohesion 0.07

## Key Concepts

- **get_status_icon()** (19 connections) — `src/ansible_aom/core/icons.py`
- **TestFrameParameterIgnoedForNonRunning** (9 connections) — `tests/unit/test_icons.py`
- **.test_frame_ignored_for_changed()** (3 connections) — `tests/unit/test_icons.py`
- **.test_frame_ignored_for_completed()** (3 connections) — `tests/unit/test_icons.py`
- **.test_frame_ignored_for_failed()** (3 connections) — `tests/unit/test_icons.py`
- **.test_frame_ignored_for_ok()** (3 connections) — `tests/unit/test_icons.py`
- **.test_frame_ignored_for_pending()** (3 connections) — `tests/unit/test_icons.py`
- **.test_frame_ignored_for_skipped()** (3 connections) — `tests/unit/test_icons.py`
- **.test_frame_ignored_for_unreachable()** (3 connections) — `tests/unit/test_icons.py`
- **.test_get_status_icon_returns_changed_icon()** (3 connections) — `tests/unit/test_icons.py`
- **.test_get_status_icon_returns_failed_icon()** (3 connections) — `tests/unit/test_icons.py`
- **.test_get_status_icon_returns_ok_icon()** (3 connections) — `tests/unit/test_icons.py`
- **.test_get_status_icon_returns_pending_icon()** (3 connections) — `tests/unit/test_icons.py`
- **.test_get_status_icon_returns_skipped_icon()** (3 connections) — `tests/unit/test_icons.py`
- **.test_get_status_icon_returns_unreachable_icon()** (3 connections) — `tests/unit/test_icons.py`
- **.test_get_status_icon_running_default_frame()** (3 connections) — `tests/unit/test_icons.py`
- **.test_get_status_icon_running_frame_wraps()** (3 connections) — `tests/unit/test_icons.py`
- **.test_get_status_icon_running_with_frame()** (3 connections) — `tests/unit/test_icons.py`
- **Get the icon for a given status.      For RUNNING status, use the frame paramete** (1 connections) — `src/ansible_aom/core/icons.py`
- **TC-367: get_status_icon returns correct icon for FAILED.** (1 connections) — `tests/unit/test_icons.py`
- **TC-368: get_status_icon returns correct icon for UNREACHABLE.** (1 connections) — `tests/unit/test_icons.py`
- **TC-369: get_status_icon returns first frame for RUNNING by default.** (1 connections) — `tests/unit/test_icons.py`
- **TC-369: get_status_icon returns correct frame for RUNNING.** (1 connections) — `tests/unit/test_icons.py`
- **TC-369: Frame index wraps around for RUNNING animation.** (1 connections) — `tests/unit/test_icons.py`
- **TC-370: get_status_icon returns correct icon for PENDING.** (1 connections) — `tests/unit/test_icons.py`
- *... and 11 more nodes in this community*

## Relationships

- [Error Handling Tests](Error_Handling_Tests.md) (9 shared connections)
- [icons.py](icons.py.md) (1 shared connections)
- [HostRunState](HostRunState.md) (1 shared connections)
- [test_icons.py](test_icons.py.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/icons.py`
- `tests/unit/test_icons.py`

## Audit Trail

- EXTRACTED: 94 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*