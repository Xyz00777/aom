# Shell Completion Helpers

> 23 nodes · cohesion 0.13

## Key Concepts

- **_create_parser()** (15 connections) — `src/ansible_aom/rerun/cli.py`
- **cli.py** (10 connections) — `src/ansible_aom/rerun/cli.py`
- **TestCreateParser** (10 connections) — `tests/unit/test_rerun_cli.py`
- **main()** (9 connections) — `src/ansible_aom/rerun/cli.py`
- **_build_rerun_command()** (4 connections) — `src/ansible_aom/rerun/cli.py`
- **_default_runner()** (4 connections) — `src/ansible_aom/rerun/cli.py`
- **_strip_limit_args()** (4 connections) — `src/ansible_aom/rerun/cli.py`
- **.test_state_dir_override()** (3 connections) — `tests/unit/test_rerun_cli.py`
- **.test_changes_only_flag()** (2 connections) — `tests/unit/test_rerun_cli.py`
- **.test_combined()** (2 connections) — `tests/unit/test_rerun_cli.py`
- **.test_failed_flag()** (2 connections) — `tests/unit/test_rerun_cli.py`
- **.test_no_args()** (2 connections) — `tests/unit/test_rerun_cli.py`
- **.test_session_id_positional()** (2 connections) — `tests/unit/test_rerun_cli.py`
- **.test_unreachable_flag()** (2 connections) — `tests/unit/test_rerun_cli.py`
- **.test_yes_long_form()** (2 connections) — `tests/unit/test_rerun_cli.py`
- **.test_yes_short_form()** (2 connections) — `tests/unit/test_rerun_cli.py`
- **ArgumentParser** (1 connections)
- **CLI entry point for ``aom rerun``.  Reads a recorded session, derives a host lis** (1 connections) — `src/ansible_aom/rerun/cli.py`
- **Drop any pre-existing ``--limit`` / ``-l`` from the args list.      Handles thre** (1 connections) — `src/ansible_aom/rerun/cli.py`
- **Construct the (playbook, ansible_args) pair to spawn for the rerun.      The ses** (1 connections) — `src/ansible_aom/rerun/cli.py`
- **Build the argparse parser for ``aom rerun``.      Split out from ``main`` so tes** (1 connections) — `src/ansible_aom/rerun/cli.py`
- **Real-world runner: spawn the renderer + run_playbook.      Lazy-imported so unit** (1 connections) — `src/ansible_aom/rerun/cli.py`
- **CLI entry point for ``aom rerun``.      Args:         argv: Argument list. If No** (1 connections) — `src/ansible_aom/rerun/cli.py`

## Relationships

- [KeyAction TypedDict](KeyAction_TypedDict.md) (3 shared connections)
- [Compact Renderer Formatters](Compact_Renderer_Formatters.md) (3 shared connections)
- [Exit Code Constants](Exit_Code_Constants.md) (2 shared connections)
- [TUI Widgets Module](TUI_Widgets_Module.md) (2 shared connections)
- [Ansible Posix Availability](Ansible_Posix_Availability.md) (1 shared connections)
- [Version String Parsing](Version_String_Parsing.md) (1 shared connections)
- [Tree Block Animation](Tree_Block_Animation.md) (1 shared connections)
- [Preflight Summary Rendering](Preflight_Summary_Rendering.md) (1 shared connections)
- [Total Task Counting](Total_Task_Counting.md) (1 shared connections)
- [Crash Recovery Auto-Save](Crash_Recovery_Auto-Save.md) (1 shared connections)

## Source Files

- `src/ansible_aom/rerun/cli.py`
- `tests/unit/test_rerun_cli.py`

## Audit Trail

- EXTRACTED: 58 (71%)
- INFERRED: 24 (29%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*