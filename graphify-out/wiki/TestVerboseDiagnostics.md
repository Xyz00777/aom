# TestVerboseDiagnostics

> 12 nodes · cohesion 0.17

## Key Concepts

- **TestVerboseDiagnostics** (14 connections) — `tests/unit/test_cli.py`
- **.test_verbose_list_tasks_summary()** (2 connections) — `tests/unit/test_cli.py`
- **.test_verbose_prints_ansible_path()** (2 connections) — `tests/unit/test_cli.py`
- **.test_verbose_prints_env_overrides()** (2 connections) — `tests/unit/test_cli.py`
- **.test_verbose_prints_terminal_capabilities()** (2 connections) — `tests/unit/test_cli.py`
- **.test_verbose_without_playbook_shows_help()** (2 connections) — `tests/unit/test_cli.py`
- **Tests for TC-008: Verbose flag diagnostics.** (1 connections) — `tests/unit/test_cli.py`
- **TC-008: --verbose prints resolved ansible-playbook path.** (1 connections) — `tests/unit/test_cli.py`
- **TC-008: --verbose prints ANSIBLE_STDOUT_CALLBACK env override.** (1 connections) — `tests/unit/test_cli.py`
- **TC-008: --verbose prints terminal capabilities when verbose.** (1 connections) — `tests/unit/test_cli.py`
- **TC-008: --verbose without playbook still shows help, not crash.** (1 connections) — `tests/unit/test_cli.py`
- **TC-008: --verbose includes --list-tasks summary in diagnostics.** (1 connections) — `tests/unit/test_cli.py`

## Relationships

- [HostRunState](HostRunState.md) (6 shared connections)
- [CompactRenderer](CompactRenderer.md) (1 shared connections)
- [RunState](RunState.md) (1 shared connections)

## Source Files

- `tests/unit/test_cli.py`

## Audit Trail

- EXTRACTED: 23 (77%)
- INFERRED: 7 (23%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*