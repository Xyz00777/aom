# Golden Frame Tests

> 26 nodes · cohesion 0.08

## Key Concepts

- **is_password_prompt()** (16 connections) — `src/ansible_aom/core/prompts.py`
- **.test_is_password_prompt_become_password()** (3 connections) — `tests/compact/test_password.py`
- **.test_is_password_prompt_become_password_defaults()** (3 connections) — `tests/compact/test_password.py`
- **.test_is_password_prompt_confirm_vault_password()** (3 connections) — `tests/compact/test_password.py`
- **.test_is_password_prompt_new_vault_password()** (3 connections) — `tests/compact/test_password.py`
- **.test_is_password_prompt_rejects_empty_string()** (3 connections) — `tests/compact/test_password.py`
- **.test_is_password_prompt_rejects_non_password()** (3 connections) — `tests/compact/test_password.py`
- **.test_is_password_prompt_ssh_password()** (3 connections) — `tests/compact/test_password.py`
- **.test_is_password_prompt_sudo_bracketed_password()** (3 connections) — `tests/compact/test_password.py`
- **.test_is_password_prompt_sudo_password()** (3 connections) — `tests/compact/test_password.py`
- **.test_is_password_prompt_sudo_password_for_user()** (3 connections) — `tests/compact/test_password.py`
- **.test_is_password_prompt_vault_password()** (3 connections) — `tests/compact/test_password.py`
- **.test_is_password_prompt_vault_password_with_id()** (3 connections) — `tests/compact/test_password.py`
- **Check if ``text`` matches any known password prompt pattern.** (1 connections) — `src/ansible_aom/core/prompts.py`
- **TC-143: Empty string is not a password prompt.** (1 connections) — `tests/compact/test_password.py`
- **TC-143: Vault password pattern detected for PTY integration.** (1 connections) — `tests/compact/test_password.py`
- **TC-143: Vault password (vault_id variant) detected.** (1 connections) — `tests/compact/test_password.py`
- **TC-143: SSH password pattern detected for PTY integration.** (1 connections) — `tests/compact/test_password.py`
- **TC-143: BECOME password pattern detected.** (1 connections) — `tests/compact/test_password.py`
- **TC-143: BECOME password[defaults to SSH password] pattern detected.** (1 connections) — `tests/compact/test_password.py`
- **TC-143: New Vault password pattern detected.** (1 connections) — `tests/compact/test_password.py`
- **TC-143: Confirm New Vault password pattern detected.** (1 connections) — `tests/compact/test_password.py`
- **TC-143: macOS / Linux sudo prompt 'Password: ' is recognised.          This matt** (1 connections) — `tests/compact/test_password.py`
- **TC-143: sudo's ``Password for <user>: `` variant is recognised.** (1 connections) — `tests/compact/test_password.py`
- **TC-143: sudo's ``[sudo] password for <user>: `` variant is recognised.** (1 connections) — `tests/compact/test_password.py`
- *... and 1 more nodes in this community*

## Relationships

- [List Hosts Output Parser](List_Hosts_Output_Parser.md) (13 shared connections)
- [test_password.py](test_password.py.md) (1 shared connections)
- [Credential String Sanitization](Credential_String_Sanitization.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/prompts.py`
- `tests/compact/test_password.py`

## Audit Trail

- EXTRACTED: 40 (62%)
- INFERRED: 25 (38%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*