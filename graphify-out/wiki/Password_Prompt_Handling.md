# Password Prompt Handling

> 12 nodes · cohesion 0.17

## Key Concepts

- **TestPasswordPromptHandling** (10 connections) — `tests/unit/test_pty_stream.py`
- **.test_multiple_password_prompts_replaced()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_password_prompt_cleared_after_handling()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_password_prompt_in_recap_phase()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_password_prompt_pending_state()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_password_prompt_preserved_across_phases()** (3 connections) — `tests/unit/test_pty_stream.py`
- **TC-143 to TC-148: Password prompt handling in PTY stream.** (1 connections) — `tests/unit/test_pty_stream.py`
- **TC-143: Password prompts set _pending_password_prompt.** (1 connections) — `tests/unit/test_pty_stream.py`
- **Password prompt state cleared after handle_password_prompt.** (1 connections) — `tests/unit/test_pty_stream.py`
- **Multiple password prompts - last one wins.** (1 connections) — `tests/unit/test_pty_stream.py`
- **Password prompt persists across phase transition.** (1 connections) — `tests/unit/test_pty_stream.py`
- **Password prompts still detected in POST_RUN_RECAP (unusual edge case).** (1 connections) — `tests/unit/test_pty_stream.py`

## Relationships

- [[PTY Stream Parser]] (6 shared connections)
- [[Role Group Task Models]] (2 shared connections)
- [[PTY Stream Parser Tests]] (1 shared connections)

## Source Files

- `tests/unit/test_pty_stream.py`

## Audit Trail

- EXTRACTED: 23 (74%)
- INFERRED: 8 (26%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*