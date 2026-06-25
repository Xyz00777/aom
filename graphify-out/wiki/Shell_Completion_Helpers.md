# Shell Completion Helpers

> 18 nodes · cohesion 0.14

## Key Concepts

- **completion_snippet()** (7 connections) — `src/ansible_aom/completion.py`
- **test_completion.py** (6 connections) — `tests/unit/test_completion.py`
- **TestCompletionSnippet** (6 connections) — `tests/unit/test_completion.py`
- **TestRerunCLICompleterWiring** (4 connections) — `tests/unit/test_completion.py`
- **TestArgcompleteEnvHandoff** (3 connections) — `tests/unit/test_completion.py`
- **.test_top_level_parser_short_circuits_on_argcomplete_env()** (3 connections) — `tests/unit/test_completion.py`
- **TestReplayCLICompleterWiring** (3 connections) — `tests/unit/test_completion.py`
- **F5: session-id positional on the replay parser carries the completer.** (2 connections) — `tests/unit/test_completion.py`
- **.test_bash_snippet_contains_argcomplete_register()** (2 connections) — `tests/unit/test_completion.py`
- **.test_fish_snippet_contains_argcomplete_register()** (2 connections) — `tests/unit/test_completion.py`
- **.test_unknown_shell_raises_value_error()** (2 connections) — `tests/unit/test_completion.py`
- **.test_zsh_snippet_contains_argcomplete_register()** (2 connections) — `tests/unit/test_completion.py`
- **.test_rerun_session_id_has_completer()** (2 connections) — `tests/unit/test_completion.py`
- **Return the rc-file snippet to enable AOM tab-completion in ``shell``.      The s** (1 connections) — `src/ansible_aom/completion.py`
- **Unit tests for shell-completion helpers (F5).  Covers: - ``session_id_completer`** (1 connections) — `tests/unit/test_completion.py`
- **Smoke test: setting _ARGCOMPLETE causes the parser to short-circuit.      argcom** (1 connections) — `tests/unit/test_completion.py`
- **.test_supported_shells_constant()** (1 connections) — `tests/unit/test_completion.py`
- **.test_replay_session_id_has_completer()** (1 connections) — `tests/unit/test_completion.py`

## Relationships

- [[Session ID Completion]] (2 shared connections)
- [[CLI Main Entry Point]] (1 shared connections)
- [[CLI Argument Parser]] (1 shared connections)
- [[Inventory Auto Detection]] (1 shared connections)
- [[Rerun CLI Parser]] (1 shared connections)

## Source Files

- `src/ansible_aom/completion.py`
- `tests/unit/test_completion.py`

## Audit Trail

- EXTRACTED: 38 (78%)
- INFERRED: 11 (22%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*