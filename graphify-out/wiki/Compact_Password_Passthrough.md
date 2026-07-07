# Compact Password Passthrough

> 6 nodes · cohesion 0.17

## Key Concepts

- **TestCompactModePasswordPassThrough** (10 connections) — `tests/unit/test_pty_stream.py`
- **.test_clear_password_prompt_allows_next_detection()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_password_prompt_exact_text_stored()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_password_prompt_multiple_types()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_password_prompt_not_json_event()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_password_prompt_sets_pending_state()** (3 connections) — `tests/unit/test_pty_stream.py`

## Relationships

- [[PTY Stream Parser]] (6 shared connections)
- [[Role Group Task Models]] (2 shared connections)
- [[PTY Stream Parser Tests]] (1 shared connections)

## Source Files

- `tests/unit/test_pty_stream.py`

## Audit Trail

- EXTRACTED: 17 (68%)
- INFERRED: 8 (32%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*