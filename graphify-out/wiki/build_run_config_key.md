# build_run_config_key

> 20 nodes · cohesion 0.22

## Key Concepts

- **build_run_config_key()** (44 connections) — `src/ansible_aom/core/run_config.py`
- **test_run_config.py** (14 connections) — `tests/unit/test_run_config.py`
- **Path** (12 connections)
- **test_key_is_hashable_and_frozen()** (4 connections) — `tests/unit/test_run_config.py`
- **test_key_unknown_flag_is_ignored_safely()** (4 connections) — `tests/unit/test_run_config.py`
- **_split_csv_sorted()** (3 connections) — `src/ansible_aom/core/run_config.py`
- **test_key_check_and_diff_are_distinct()** (3 connections) — `tests/unit/test_run_config.py`
- **test_key_extra_vars_are_sorted()** (3 connections) — `tests/unit/test_run_config.py`
- **test_key_ignores_verbosity_flags()** (3 connections) — `tests/unit/test_run_config.py`
- **test_key_inventory_order_matters()** (3 connections) — `tests/unit/test_run_config.py`
- **test_key_limit_is_string()** (3 connections) — `tests/unit/test_run_config.py`
- **test_key_skip_tags_are_sorted()** (3 connections) — `tests/unit/test_run_config.py`
- **test_key_start_at_task_buckets_separately()** (3 connections) — `tests/unit/test_run_config.py`
- **test_key_step_buckets_separately()** (3 connections) — `tests/unit/test_run_config.py`
- **test_key_tags_are_sorted()** (3 connections) — `tests/unit/test_run_config.py`
- **test_key_uses_resolved_playbook_path()** (3 connections) — `tests/unit/test_run_config.py`
- **Split a comma-separated flag value, strip whitespace, drop empties, sort.** (1 connections) — `src/ansible_aom/core/run_config.py`
- **Build a :class:`RunConfigKey` from a playbook path and ansible argv tail.      `** (1 connections) — `src/ansible_aom/core/run_config.py`
- **Unit tests for core.run_config — argv normalization for the history key.** (1 connections) — `tests/unit/test_run_config.py`
- **Future ansible flags shouldn't crash us; they just don't contribute to the key.** (1 connections) — `tests/unit/test_run_config.py`

## Relationships

- [find_previous_run](find_previous_run.md) (12 shared connections)
- [history.py](history.py.md) (7 shared connections)
- [test_history_roundtrip.py](test_history_roundtrip.py.md) (5 shared connections)
- [Run Diagnostics Accumulator](Run_Diagnostics_Accumulator.md) (5 shared connections)
- [run_playbook](run_playbook.md) (2 shared connections)
- [test_history_loop_totals.py](test_history_loop_totals.py.md) (1 shared connections)
- [Terminal Size Check](Terminal_Size_Check.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/run_config.py`
- `tests/unit/test_run_config.py`

## Audit Trail

- EXTRACTED: 114 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*