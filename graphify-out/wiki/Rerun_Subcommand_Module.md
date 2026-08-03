# Rerun Subcommand Module

> 21 nodes · cohesion 0.13

## Key Concepts

- **rerun/cli.py** (22 connections) — `src/ansible_aom/rerun/cli.py`
- **main()** (12 connections) — `src/ansible_aom/rerun/cli.py`
- **_build_rerun_command()** (10 connections) — `src/ansible_aom/rerun/cli.py`
- **TestBuildRerunCommand** (7 connections) — `tests/unit/test_rerun_cli.py`
- **_default_runner()** (4 connections) — `src/ansible_aom/rerun/cli.py`
- **_strip_limit_args()** (3 connections) — `src/ansible_aom/rerun/cli.py`
- **.test_empty_host_set_raises()** (3 connections) — `tests/unit/test_rerun_cli.py`
- **.test_overrides_existing_limit_flag()** (3 connections) — `tests/unit/test_rerun_cli.py`
- **.test_overrides_limit_equals_form()** (3 connections) — `tests/unit/test_rerun_cli.py`
- **.test_overrides_short_l_flag()** (3 connections) — `tests/unit/test_rerun_cli.py`
- **.test_appends_limit_to_original_args()** (2 connections) — `tests/unit/test_rerun_cli.py`
- **.test_single_host_limit()** (2 connections) — `tests/unit/test_rerun_cli.py`
- **CLI entry point for ``aom rerun``.  Reads a recorded session, derives a host lis** (1 connections) — `src/ansible_aom/rerun/cli.py`
- **Drop any pre-existing ``--limit`` / ``-l`` from the args list.      Handles thre** (1 connections) — `src/ansible_aom/rerun/cli.py`
- **Construct the (playbook, ansible_args) pair to spawn for the rerun.      The ses** (1 connections) — `src/ansible_aom/rerun/cli.py`
- **Real-world runner: spawn the renderer + run_playbook.      Lazy-imported so unit** (1 connections) — `src/ansible_aom/rerun/cli.py`
- **CLI entry point for ``aom rerun``.      Args:         argv: Argument list. If No** (1 connections) — `src/ansible_aom/rerun/cli.py`
- **A pre-existing --limit in the original args is dropped in favour of ours.** (1 connections) — `tests/unit/test_rerun_cli.py`
- **``-l`` is the short form of ``--limit``; treat it the same.** (1 connections) — `tests/unit/test_rerun_cli.py`
- **``--limit=hosts`` (single arg) is also dropped.** (1 connections) — `tests/unit/test_rerun_cli.py`
- **No hosts → no rerun. Caller is expected to surface this earlier.** (1 connections) — `tests/unit/test_rerun_cli.py`

## Relationships

- [KeyAction TypedDict](KeyAction_TypedDict.md) (4 shared connections)
- [Dynamic Include Expansion](Dynamic_Include_Expansion.md) (4 shared connections)
- [Replay Determinism Tests](Replay_Determinism_Tests.md) (2 shared connections)
- [Loop Item Stream Tests](Loop_Item_Stream_Tests.md) (2 shared connections)
- [Preflight Summary Rendering](Preflight_Summary_Rendering.md) (2 shared connections)
- [Exit Code Constants](Exit_Code_Constants.md) (2 shared connections)
- [Shell Completion Helpers](Shell_Completion_Helpers.md) (2 shared connections)
- [TUI Widgets Module](TUI_Widgets_Module.md) (2 shared connections)
- [Compact Renderer Formatters](Compact_Renderer_Formatters.md) (2 shared connections)
- [Include Role Discovery](Include_Role_Discovery.md) (2 shared connections)
- [First Ctrl-C Cancellation](First_Ctrl-C_Cancellation.md) (2 shared connections)
- [Ansible Posix Availability](Ansible_Posix_Availability.md) (1 shared connections)

## Source Files

- `src/ansible_aom/rerun/cli.py`
- `tests/unit/test_rerun_cli.py`

## Audit Trail

- EXTRACTED: 80 (96%)
- INFERRED: 3 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*