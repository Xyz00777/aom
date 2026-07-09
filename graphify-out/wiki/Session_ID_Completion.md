# Session ID Completion

> 20 nodes · cohesion 0.23

## Key Concepts

- **ensure_inventory_arg()** (9 connections) — `src/ansible_aom/cli.py`
- **MonkeyPatch** (9 connections)
- **Path** (9 connections)
- **detect_default_inventory()** (7 connections) — `src/ansible_aom/cli.py`
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

- [State Transition Validation](State_Transition_Validation.md) (4 shared connections)

## Source Files

- `src/ansible_aom/cli.py`
- `tests/unit/test_cli_inventory_autodetect.py`

## Audit Trail

- EXTRACTED: 72 (80%)
- INFERRED: 18 (20%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*