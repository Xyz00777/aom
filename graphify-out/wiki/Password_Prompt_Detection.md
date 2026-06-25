# Password Prompt Detection

> 10 nodes · cohesion 0.20

## Key Concepts

- **TestPasswordPrompts** (10 connections) — `tests/integration/test_playbook_parser.py`
- **.test_become_password_prompt_detected()** (3 connections) — `tests/integration/test_playbook_parser.py`
- **.test_clear_password_prompt()** (3 connections) — `tests/integration/test_playbook_parser.py`
- **.test_ssh_password_prompt_detected()** (3 connections) — `tests/integration/test_playbook_parser.py`
- **.test_vault_password_prompt_detected()** (3 connections) — `tests/integration/test_playbook_parser.py`
- **Test password prompt detection.** (1 connections) — `tests/integration/test_playbook_parser.py`
- **Vault password prompt is detected.** (1 connections) — `tests/integration/test_playbook_parser.py`
- **SSH password prompt is detected.** (1 connections) — `tests/integration/test_playbook_parser.py`
- **BECOME password prompt is detected.** (1 connections) — `tests/integration/test_playbook_parser.py`
- **Password prompt can be cleared.** (1 connections) — `tests/integration/test_playbook_parser.py`

## Relationships

- [[PTY Stream Parser]] (5 shared connections)
- [[Role Group Task Models]] (2 shared connections)
- [[Run State Summary Panel]] (1 shared connections)
- [[Playbook Parser Integration Tests]] (1 shared connections)

## Source Files

- `tests/integration/test_playbook_parser.py`

## Audit Trail

- EXTRACTED: 23 (85%)
- INFERRED: 4 (15%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*