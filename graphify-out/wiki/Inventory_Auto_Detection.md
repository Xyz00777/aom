# Inventory Auto Detection

> 25 nodes · cohesion 0.13

## Key Concepts

- **MonkeyPatch** (27 connections)
- **ensure_inventory_arg()** (9 connections) — `src/ansible_aom/cli.py`
- **detect_default_inventory()** (7 connections) — `src/ansible_aom/cli.py`
- **.test_add_warning_from_worker_lands_on_status_bar()** (7 connections) — `tests/tui/test_live_refresh.py`
- **.test_completion_nonzero_marks_title_with_cross()** (7 connections) — `tests/tui/test_live_refresh.py`
- **.test_completion_zero_marks_title_with_check()** (7 connections) — `tests/tui/test_live_refresh.py`
- **.test_three_task_starts_appear_in_tree()** (7 connections) — `tests/tui/test_live_refresh.py`
- **.test_tick_drains_pending_log_lines()** (7 connections) — `tests/tui/test_live_refresh.py`
- **.test_tick_refreshes_widgets_after_event()** (7 connections) — `tests/tui/test_live_refresh.py`
- **TestEnsureInventoryArg** (6 connections) — `tests/unit/test_cli_inventory_autodetect.py`
- **TestDetectDefaultInventory** (5 connections) — `tests/unit/test_cli_inventory_autodetect.py`
- **.test_handles_inventory_file_long_form()** (5 connections) — `tests/unit/test_cli_inventory_autodetect.py`
- **test_cli_inventory_autodetect.py** (4 connections) — `tests/unit/test_cli_inventory_autodetect.py`
- **.test_finds_inventory_ini_in_cwd()** (4 connections) — `tests/unit/test_cli_inventory_autodetect.py`
- **.test_finds_yaml_inventory_when_only_one_present()** (4 connections) — `tests/unit/test_cli_inventory_autodetect.py`
- **.test_prefers_inventory_ini_over_hosts()** (4 connections) — `tests/unit/test_cli_inventory_autodetect.py`
- **.test_returns_none_when_no_known_file_present()** (4 connections) — `tests/unit/test_cli_inventory_autodetect.py`
- **.test_leaves_args_unchanged_when_dash_i_present()** (4 connections) — `tests/unit/test_cli_inventory_autodetect.py`
- **.test_leaves_args_unchanged_when_long_inventory_flag_present()** (4 connections) — `tests/unit/test_cli_inventory_autodetect.py`
- **.test_leaves_args_unchanged_when_no_default_present()** (4 connections) — `tests/unit/test_cli_inventory_autodetect.py`
- **.test_prepends_default_inventory_when_none_given()** (4 connections) — `tests/unit/test_cli_inventory_autodetect.py`
- **If no -i/--inventory flag is set, prepend one pointing at the default file.** (1 connections) — `src/ansible_aom/cli.py`
- **Return the first conventional inventory file found in CWD, or None.** (1 connections) — `src/ansible_aom/cli.py`
- **Tests for inventory auto-detection.  When the user doesn't pass `-i` / `--invent** (1 connections) — `tests/unit/test_cli_inventory_autodetect.py`
- **ansible-playbook also accepts --inventory-file as a synonym.** (1 connections) — `tests/unit/test_cli_inventory_autodetect.py`

## Relationships

- [[Run Config Key Normalization]] (15 shared connections)
- [[AOM TUI Application]] (8 shared connections)
- [[Task Definition Live Refresh]] (6 shared connections)
- [[CLI Main Entry Point]] (4 shared connections)
- [[Golden Frame Tests]] (2 shared connections)
- [[Diagnostics CLI Wiring]] (2 shared connections)
- [[Playbook Run Integration Tests]] (1 shared connections)
- [[RunState Persistence Shape]] (1 shared connections)
- [[Shell Completion Helpers]] (1 shared connections)
- [[Session ID Completion]] (1 shared connections)
- [[Session Replay Driver]] (1 shared connections)
- [[Session Diagnostics Writing]] (1 shared connections)

## Source Files

- `src/ansible_aom/cli.py`
- `tests/tui/test_live_refresh.py`
- `tests/unit/test_cli_inventory_autodetect.py`

## Audit Trail

- EXTRACTED: 129 (91%)
- INFERRED: 12 (9%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*