# Community 502

> 8 nodes · cohesion 0.25

## Key Concepts

- **load_config_with_layers()** (7 connections) — `src/ansible_aom/core/config_layer.py`
- **TestMissingFilesSkipped** (6 connections) — `tests/unit/test_config_layer.py`
- **.test_missing_files_loaded_as_empty()** (5 connections) — `tests/unit/test_config_layer.py`
- **.test_missing_user_file_does_not_raise()** (5 connections) — `tests/unit/test_config_layer.py`
- **Build the layered :class:`AomSettings` and run legacy migration first.** (1 connections) — `src/ansible_aom/core/config_layer.py`
- **Files that don't exist on disk are silently skipped — not errors.** (1 connections) — `tests/unit/test_config_layer.py`
- **``load_config_with_layers`` returns defaults when no files exist.** (1 connections) — `tests/unit/test_config_layer.py`
- **If only the system file is missing, no error.** (1 connections) — `tests/unit/test_config_layer.py`

## Relationships

- [Auto Version Bump Hook](Auto_Version_Bump_Hook.md) (4 shared connections)
- [Rerun CLI Entry](Rerun_CLI_Entry.md) (3 shared connections)
- [Community 511](Community_511.md) (2 shared connections)
- [State Transition Validation](State_Transition_Validation.md) (1 shared connections)
- [Core Module Init](Core_Module_Init.md) (1 shared connections)
- [Module Init File](Module_Init_File.md) (1 shared connections)
- [Community 604](Community_604.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/config_layer.py`
- `tests/unit/test_config_layer.py`

## Audit Trail

- EXTRACTED: 20 (74%)
- INFERRED: 7 (26%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*