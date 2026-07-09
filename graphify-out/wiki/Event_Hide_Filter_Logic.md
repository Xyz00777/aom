# Event Hide Filter Logic

> 45 nodes · cohesion 0.05

## Key Concepts

- **TestJsonlEnvironmentVariable** (7 connections) — `tests/unit/test_posix_callback.py`
- **test_posix_callback.py** (6 connections) — `tests/unit/test_posix_callback.py`
- **TestAnsibleCoreVersionCheck** (5 connections) — `tests/unit/test_posix_callback.py`
- **TestAnsiblePosixAvailability** (5 connections) — `tests/unit/test_posix_callback.py`
- **TestAnsiblePosixVersionCheck** (5 connections) — `tests/unit/test_posix_callback.py`
- **TestAnsiblePosixInstallPrompt** (4 connections) — `tests/unit/test_posix_callback.py`
- **.test_callback_env_callable_for_any_ansible_core_state()** (3 connections) — `tests/unit/test_posix_callback.py`
- **.test_callback_env_does_not_mutate_os_environ()** (3 connections) — `tests/unit/test_posix_callback.py`
- **MonkeyPatch** (2 connections)
- **.test_callback_env_does_not_pin_ansible_core_version()** (2 connections) — `tests/unit/test_posix_callback.py`
- **.test_callback_env_returns_dict_with_required_key()** (2 connections) — `tests/unit/test_posix_callback.py`
- **.test_bundled_callback_dir_none_when_file_missing()** (2 connections) — `tests/unit/test_posix_callback.py`
- **.test_bundled_callback_dir_resolves_when_present()** (2 connections) — `tests/unit/test_posix_callback.py`
- **.test_bundled_callback_plugin_file_exists()** (2 connections) — `tests/unit/test_posix_callback.py`
- **.test_bundled_preferred_over_posix_fallback()** (2 connections) — `tests/unit/test_posix_callback.py`
- **.test_fallback_selects_ansible_posix_jsonl()** (2 connections) — `tests/unit/test_posix_callback.py`
- **.test_bundled_plugin_does_not_require_ansible_posix_collection()** (2 connections) — `tests/unit/test_posix_callback.py`
- **.test_fallback_callback_name_is_ansible_posix_jsonl()** (2 connections) — `tests/unit/test_posix_callback.py`
- **.test_fallback_callback_name_split_correctly()** (2 connections) — `tests/unit/test_posix_callback.py`
- **.test_callback_env_bundled_sets_callback_plugins()** (2 connections) — `tests/unit/test_posix_callback.py`
- **.test_callback_env_fallback_omits_callback_plugins()** (2 connections) — `tests/unit/test_posix_callback.py`
- **.test_callback_env_preserves_user_override()** (2 connections) — `tests/unit/test_posix_callback.py`
- **.test_callback_env_sets_ansible_stdout_callback()** (2 connections) — `tests/unit/test_posix_callback.py`
- **Tests for JSONL callback plugin configuration (TC-067 to TC-071).  Test cases co** (1 connections) — `tests/unit/test_posix_callback.py`
- **TC-068: When bundled dir resolves, aom_jsonl wins over ansible.posix.jsonl.** (1 connections) — `tests/unit/test_posix_callback.py`
- *... and 20 more nodes in this community*

## Relationships

- No strong cross-community connections detected

## Source Files

- `tests/unit/test_posix_callback.py`

## Audit Trail

- EXTRACTED: 90 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*