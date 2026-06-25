# Password Pattern Detection

> 26 nodes · cohesion 0.08

## Key Concepts

- **TestPasswordPromptPatterns** (17 connections) — `tests/unit/test_pty_stream.py`
- **.test_all_password_patterns_in_parser()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_clear_password_prompt()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_password_pattern_become()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_password_pattern_become_default_variant()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_password_pattern_confirm_vault()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_password_pattern_new_vault()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_password_pattern_ssh()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_password_pattern_vault()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_password_pattern_vault_id_variant()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_password_prompt_cleared_after_jsonl()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_password_prompt_in_execution_phase()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_password_prompt_in_pre_run_phase()** (3 connections) — `tests/unit/test_pty_stream.py`
- **TC-133 to TC-139: Password pattern detection.** (1 connections) — `tests/unit/test_pty_stream.py`
- **TC-134: Vault password: pattern detected.** (1 connections) — `tests/unit/test_pty_stream.py`
- **TC-135: Vault password (id): pattern detected.** (1 connections) — `tests/unit/test_pty_stream.py`
- **TC-136: SSH password: pattern detected.** (1 connections) — `tests/unit/test_pty_stream.py`
- **TC-137: BECOME password: pattern detected.** (1 connections) — `tests/unit/test_pty_stream.py`
- **TC-138: BECOME password[defaults to SSH password]: pattern detected.** (1 connections) — `tests/unit/test_pty_stream.py`
- **TC-139: New Vault password: pattern detected.** (1 connections) — `tests/unit/test_pty_stream.py`
- **TC-139: Confirm New Vault password: pattern detected.** (1 connections) — `tests/unit/test_pty_stream.py`
- **TC-133: All PASSWORD_PATTERNS exist in parser.** (1 connections) — `tests/unit/test_pty_stream.py`
- **Password prompts in PRE_RUN_PROMPTS phase are captured.** (1 connections) — `tests/unit/test_pty_stream.py`
- **Password prompts in EXECUTION phase are captured.** (1 connections) — `tests/unit/test_pty_stream.py`
- **Password prompt can be cleared after handling.** (1 connections) — `tests/unit/test_pty_stream.py`
- *... and 1 more nodes in this community*

## Relationships

- [[PTY Stream Parser]] (13 shared connections)
- [[Role Group Task Models]] (2 shared connections)
- [[PTY Stream Parser Tests]] (1 shared connections)

## Source Files

- `tests/unit/test_pty_stream.py`

## Audit Trail

- EXTRACTED: 51 (77%)
- INFERRED: 15 (23%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*