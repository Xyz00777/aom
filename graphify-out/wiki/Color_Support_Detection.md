# Color Support Detection

> 21 nodes · cohesion 0.10

## Key Concepts

- **TestCallbackEnv** (8 connections) — `tests/unit/test_callback_env.py`
- **test_callback_env.py** (4 connections) — `tests/unit/test_callback_env.py`
- **TestBundledConnectionCallbackDir** (4 connections) — `tests/unit/test_callback_env.py`
- **TestBundledCallbackDir** (2 connections) — `tests/unit/test_callback_env.py`
- **.test_callback_env_does_not_include_empty_separator_entries()** (2 connections) — `tests/unit/test_callback_env.py`
- **.test_connection_callback_path_uses_posix_separator()** (2 connections) — `tests/unit/test_callback_env.py`
- **.test_includes_connection_callback_dir_in_fallback_path()** (2 connections) — `tests/unit/test_callback_env.py`
- **.test_includes_connection_callback_dir_when_bundled_available()** (2 connections) — `tests/unit/test_callback_env.py`
- **.test_omits_connection_callback_dir_when_unavailable()** (2 connections) — `tests/unit/test_callback_env.py`
- **Unit tests for the runner's stdout-callback selection.  AOM prefers its bundled** (1 connections) — `tests/unit/test_callback_env.py`
- **Task 5.3: even on the ansible.posix.jsonl fallback the connection         callba** (1 connections) — `tests/unit/test_callback_env.py`
- **Task 5.3: if the connection-callback dir can't be resolved the         runner om** (1 connections) — `tests/unit/test_callback_env.py`
- **Task 5.3: when both dirs are present, ANSIBLE_CALLBACK_PLUGINS uses         the** (1 connections) — `tests/unit/test_callback_env.py`
- **Defensive: never inject an empty ``:`` into ANSIBLE_CALLBACK_PLUGINS         eve** (1 connections) — `tests/unit/test_callback_env.py`
- **Task 5.3: the new connection-tracking callback ships in     ``src/ansible_aom/ca** (1 connections) — `tests/unit/test_callback_env.py`
- **Task 5.3: ANSIBLE_CALLBACK_PLUGINS includes the connection-callback dir.** (1 connections) — `tests/unit/test_callback_env.py`
- **.test_resolves_to_existing_dir_with_plugin()** (1 connections) — `tests/unit/test_callback_env.py`
- **.test_resolves_to_existing_dir_with_plugin()** (1 connections) — `tests/unit/test_callback_env.py`
- **.test_returns_none_when_plugin_file_missing()** (1 connections) — `tests/unit/test_callback_env.py`
- **.test_falls_back_to_posix_jsonl_when_dir_missing()** (1 connections) — `tests/unit/test_callback_env.py`
- **.test_selects_aom_jsonl_when_bundled_dir_present()** (1 connections) — `tests/unit/test_callback_env.py`

## Relationships

- No strong cross-community connections detected

## Source Files

- `tests/unit/test_callback_env.py`

## Audit Trail

- EXTRACTED: 40 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*