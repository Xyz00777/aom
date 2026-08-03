# Event Hide Filter Logic

> 18 nodes · cohesion 0.11

## Key Concepts

- **test_posix_callback.py** (7 connections) — `tests/unit/test_posix_callback.py`
- **TestAnsiblePosixAvailability** (5 connections) — `tests/unit/test_posix_callback.py`
- **ansible/__init__.py** (4 connections) — `src/ansible_aom/ansible/__init__.py`
- **TestAnsiblePosixInstallPrompt** (4 connections) — `tests/unit/test_posix_callback.py`
- **.test_bundled_callback_dir_none_when_file_missing()** (2 connections) — `tests/unit/test_posix_callback.py`
- **.test_bundled_callback_dir_resolves_when_present()** (2 connections) — `tests/unit/test_posix_callback.py`
- **.test_bundled_callback_plugin_file_exists()** (2 connections) — `tests/unit/test_posix_callback.py`
- **.test_bundled_preferred_over_posix_fallback()** (2 connections) — `tests/unit/test_posix_callback.py`
- **.test_fallback_selects_ansible_posix_jsonl()** (2 connections) — `tests/unit/test_posix_callback.py`
- **Ansible infrastructure: subprocess, pexpect, JSONL callback wiring.  Contains th** (1 connections) — `src/ansible_aom/ansible/__init__.py`
- **Tests for JSONL callback plugin configuration (TC-067 to TC-071).  Test cases co** (1 connections) — `tests/unit/test_posix_callback.py`
- **TC-068: When bundled dir resolves, aom_jsonl wins over ansible.posix.jsonl.** (1 connections) — `tests/unit/test_posix_callback.py`
- **Tests for TC-067: ansible.posix Availability Check (bundled fallback).** (1 connections) — `tests/unit/test_posix_callback.py`
- **TC-067: The bundled aom_jsonl plugin resolves to a real path on disk.          T** (1 connections) — `tests/unit/test_posix_callback.py`
- **TC-067: When bundled plugin file is missing, return None (force fallback).** (1 connections) — `tests/unit/test_posix_callback.py`
- **TC-067: The bundled aom_jsonl.py file exists in the callback directory.** (1 connections) — `tests/unit/test_posix_callback.py`
- **Tests for TC-068: ansible.posix Install Prompt (implicit fallback path).      AO** (1 connections) — `tests/unit/test_posix_callback.py`
- **TC-068: When bundled stdout dir unavailable, env selects ansible.posix.jsonl.** (1 connections) — `tests/unit/test_posix_callback.py`

## Relationships

- [Task Wall Duration Mining](Task_Wall_Duration_Mining.md) (1 shared connections)
- [Cancellation Timer](Cancellation_Timer.md) (1 shared connections)
- [Subprocess Exit Codes](Subprocess_Exit_Codes.md) (1 shared connections)
- [Tree Projection Utilities](Tree_Projection_Utilities.md) (1 shared connections)
- [Terminal Capability Detection](Terminal_Capability_Detection.md) (1 shared connections)

## Source Files

- `src/ansible_aom/ansible/__init__.py`
- `tests/unit/test_posix_callback.py`

## Audit Trail

- EXTRACTED: 39 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*