# Golden Frame Tests

> 34 nodes · cohesion 0.08

## Key Concepts

- **TestPasswordPromptPTYIntegration** (27 connections) — `tests/compact/test_password.py`
- **is_password_prompt()** (15 connections) — `src/ansible_aom/core/prompts.py`
- **.test_is_password_prompt_become_password()** (3 connections) — `tests/compact/test_password.py`
- **.test_is_password_prompt_become_password_defaults()** (3 connections) — `tests/compact/test_password.py`
- **.test_is_password_prompt_confirm_vault_password()** (3 connections) — `tests/compact/test_password.py`
- **.test_is_password_prompt_new_vault_password()** (3 connections) — `tests/compact/test_password.py`
- **.test_is_password_prompt_rejects_empty_string()** (3 connections) — `tests/compact/test_password.py`
- **.test_is_password_prompt_rejects_non_password()** (3 connections) — `tests/compact/test_password.py`
- **.test_is_password_prompt_rejects_partial_match_only()** (3 connections) — `tests/compact/test_password.py`
- **.test_is_password_prompt_ssh_password()** (3 connections) — `tests/compact/test_password.py`
- **.test_is_password_prompt_sudo_bracketed_password()** (3 connections) — `tests/compact/test_password.py`
- **.test_is_password_prompt_sudo_password()** (3 connections) — `tests/compact/test_password.py`
- **.test_is_password_prompt_sudo_password_for_user()** (3 connections) — `tests/compact/test_password.py`
- **.test_is_password_prompt_vault_password()** (3 connections) — `tests/compact/test_password.py`
- **.test_is_password_prompt_vault_password_with_id()** (3 connections) — `tests/compact/test_password.py`
- **.test_all_password_patterns_are_valid_regex()** (2 connections) — `tests/compact/test_password.py`
- **.test_password_patterns_count()** (2 connections) — `tests/compact/test_password.py`
- **Check if ``text`` matches any known password prompt pattern.** (1 connections) — `src/ansible_aom/core/prompts.py`
- **TC-143: Empty string is not a password prompt.** (1 connections) — `tests/compact/test_password.py`
- **TC-143: Text containing but not ending with password pattern prefix still matche** (1 connections) — `tests/compact/test_password.py`
- **TC-143: All PASSWORD_PATTERNS entries compile as valid regex.** (1 connections) — `tests/compact/test_password.py`
- **TC-143: All 10 documented password patterns present.          Ansible-native (7)** (1 connections) — `tests/compact/test_password.py`
- **TC-143: Verify pexpect spawns with PTY, Ansible's getpass reads from /dev/tty.** (1 connections) — `tests/compact/test_password.py`
- **TC-143: Vault password pattern detected for PTY integration.** (1 connections) — `tests/compact/test_password.py`
- **TC-143: Vault password (vault_id variant) detected.** (1 connections) — `tests/compact/test_password.py`
- *... and 9 more nodes in this community*

## Relationships

- [Status Bar Liveness Tests](Status_Bar_Liveness_Tests.md) (8 shared connections)
- [Credential String Sanitization](Credential_String_Sanitization.md) (1 shared connections)
- [App Configuration Settings](App_Configuration_Settings.md) (1 shared connections)
- [Session Recording Tests](Session_Recording_Tests.md) (1 shared connections)
- [Pause Lingering Cleanup](Pause_Lingering_Cleanup.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/prompts.py`
- `tests/compact/test_password.py`

## Audit Trail

- EXTRACTED: 74 (73%)
- INFERRED: 28 (27%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*