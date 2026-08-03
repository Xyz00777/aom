# KeyAction TypedDict

> 14 nodes · cohesion 0.32

## Key Concepts

- **test_rerun_cli.py** (14 connections) — `tests/unit/test_rerun_cli.py`
- **_compose_host_set()** (12 connections) — `src/ansible_aom/rerun/cli.py`
- **TestComposeHostSet** (8 connections) — `tests/unit/test_rerun_cli.py`
- **_session_dict()** (7 connections) — `tests/unit/test_rerun_cli.py`
- **._events()** (6 connections) — `tests/unit/test_rerun_cli.py`
- **.test_unreachable_flag_includes_failed_and_unreachable()** (5 connections) — `tests/unit/test_rerun_cli.py`
- **.test_changes_only_returns_changed_hosts()** (4 connections) — `tests/unit/test_rerun_cli.py`
- **.test_combined_flags_union()** (4 connections) — `tests/unit/test_rerun_cli.py`
- **.test_default_no_flag_returns_failed_only()** (4 connections) — `tests/unit/test_rerun_cli.py`
- **.test_failed_flag_returns_failed_hosts()** (4 connections) — `tests/unit/test_rerun_cli.py`
- **.test_no_matching_hosts_returns_empty()** (3 connections) — `tests/unit/test_rerun_cli.py`
- **Combine the requested host categories into a single set.      Semantics (from th** (1 connections) — `src/ansible_aom/rerun/cli.py`
- **Unit tests for the aom rerun subcommand.** (1 connections) — `tests/unit/test_rerun_cli.py`
- **--unreachable is a strict superset of --failed (per spec).** (1 connections) — `tests/unit/test_rerun_cli.py`

## Relationships

- [Compact Renderer Formatters](Compact_Renderer_Formatters.md) (4 shared connections)
- [load_session](load_session.md) (3 shared connections)
- [_session](_session.md) (2 shared connections)
- [collect_failed_hosts](collect_failed_hosts.md) (1 shared connections)
- [IO](IO.md) (1 shared connections)
- [json.py](json.py.md) (1 shared connections)
- [_build_rerun_command](_build_rerun_command.md) (1 shared connections)
- [Exit Code Constants](Exit_Code_Constants.md) (1 shared connections)
- [Shell Completion Helpers](Shell_Completion_Helpers.md) (1 shared connections)
- [TUI Widgets Module](TUI_Widgets_Module.md) (1 shared connections)

## Source Files

- `src/ansible_aom/rerun/cli.py`
- `tests/unit/test_rerun_cli.py`

## Audit Trail

- EXTRACTED: 74 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*