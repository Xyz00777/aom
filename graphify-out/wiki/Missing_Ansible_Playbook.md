# Missing Ansible Playbook

> 10 nodes · cohesion 0.20

## Key Concepts

- **TestMissingAnsiblePlaybook** (9 connections) — `tests/integration/test_error_handling.py`
- **.test_ansible_playbook_not_found_detection()** (2 connections) — `tests/integration/test_error_handling.py`
- **.test_ansible_playbook_not_found_error_message()** (2 connections) — `tests/integration/test_error_handling.py`
- **.test_ansible_playbook_not_found_exit_code_127()** (2 connections) — `tests/integration/test_error_handling.py`
- **.test_ansible_posix_missing_error_message()** (2 connections) — `tests/integration/test_error_handling.py`
- **TC-465 to TC-468: Missing ansible-playbook detection.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-465: ansible-playbook not found detected at startup.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-466: ansible-playbook not found results in exit code 127.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-467: Error message includes installation suggestions.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-468: ansible.posix missing shows install command.** (1 connections) — `tests/integration/test_error_handling.py`

## Relationships

- [[PTY Stream Parser]] (1 shared connections)
- [[State Machine Module]] (1 shared connections)
- [[Execution State Transitions]] (1 shared connections)
- [[Error Handling Tests]] (1 shared connections)

## Source Files

- `tests/integration/test_error_handling.py`

## Audit Trail

- EXTRACTED: 19 (86%)
- INFERRED: 3 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*