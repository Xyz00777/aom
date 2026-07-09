# Pydantic Model Basics

> 24 nodes · cohesion 0.11

## Key Concepts

- **TestAsciiFallback** (12 connections) — `tests/unit/test_icons.py`
- **get_status_icon_ascii()** (10 connections) — `src/ansible_aom/core/icons.py`
- **.test_changed_ascii_fallback_is_plus()** (3 connections) — `tests/unit/test_icons.py`
- **.test_failed_ascii_fallback_is_x()** (3 connections) — `tests/unit/test_icons.py`
- **.test_ok_ascii_fallback_is_asterisk()** (3 connections) — `tests/unit/test_icons.py`
- **.test_pending_ascii_fallback_is_dot()** (3 connections) — `tests/unit/test_icons.py`
- **.test_running_ascii_fallback_is_at_sign()** (3 connections) — `tests/unit/test_icons.py`
- **.test_skipped_ascii_fallback_is_lowercase_o()** (3 connections) — `tests/unit/test_icons.py`
- **.test_unreachable_ascii_fallback_is_uppercase_o()** (3 connections) — `tests/unit/test_icons.py`
- **.test_all_ascii_fallbacks_are_single_char()** (2 connections) — `tests/unit/test_icons.py`
- **.test_all_status_values_have_ascii_fallback()** (2 connections) — `tests/unit/test_icons.py`
- **.test_completed_ascii_fallback_same_as_ok()** (2 connections) — `tests/unit/test_icons.py`
- **Get ASCII fallback icon for terminals without Unicode support.      Args:** (1 connections) — `src/ansible_aom/core/icons.py`
- **Tests for TC-377: Unicode fallback to ASCII.** (1 connections) — `tests/unit/test_icons.py`
- **TC-377: OK falls back to * in ASCII mode.** (1 connections) — `tests/unit/test_icons.py`
- **TC-377: CHANGED falls back to + in ASCII mode.** (1 connections) — `tests/unit/test_icons.py`
- **TC-377: FAILED falls back to X in ASCII mode.** (1 connections) — `tests/unit/test_icons.py`
- **TC-377: RUNNING falls back to @ in ASCII mode.** (1 connections) — `tests/unit/test_icons.py`
- **TC-377: PENDING falls back to . in ASCII mode.** (1 connections) — `tests/unit/test_icons.py`
- **TC-377: SKIPPED falls back to o in ASCII mode.** (1 connections) — `tests/unit/test_icons.py`
- **TC-377: UNREACHABLE falls back to O in ASCII mode.** (1 connections) — `tests/unit/test_icons.py`
- **COMPLETED uses same ASCII fallback as OK.** (1 connections) — `tests/unit/test_icons.py`
- **Every Status enum value has an ASCII fallback.** (1 connections) — `tests/unit/test_icons.py`
- **All ASCII fallbacks are single ASCII characters.** (1 connections) — `tests/unit/test_icons.py`

## Relationships

- [Crash Recovery Notification](Crash_Recovery_Notification.md) (1 shared connections)
- [Compact Renderer Integration Tests](Compact_Renderer_Integration_Tests.md) (1 shared connections)
- [Community 461](Community_461.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/icons.py`
- `tests/unit/test_icons.py`

## Audit Trail

- EXTRACTED: 47 (77%)
- INFERRED: 14 (23%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*