# Prior Run Totals Injection

> 13 nodes · cohesion 0.18

## Key Concepts

- **find_config_paths()** (9 connections) — `src/ansible_aom/core/config_layer.py`
- **TestXdgPathResolution** (8 connections) — `tests/unit/test_config_layer.py`
- **.test_local_config_is_in_cwd()** (5 connections) — `tests/unit/test_config_layer.py`
- **.test_system_path_is_first_under_home()** (5 connections) — `tests/unit/test_config_layer.py`
- **.test_user_config_is_xdg_compliant()** (5 connections) — `tests/unit/test_config_layer.py`
- **.test_built_in_default_is_first()** (2 connections) — `tests/unit/test_config_layer.py`
- **Path** (1 connections)
- **Return the YAML file list in lowest → highest priority order.** (1 connections) — `src/ansible_aom/core/config_layer.py`
- **The standard 4-file layering resolves in the documented order.** (1 connections) — `tests/unit/test_config_layer.py`
- **Built-in defaults are first, then system, then user, then local.** (1 connections) — `tests/unit/test_config_layer.py`
- **User config sits under ``$XDG_CONFIG_HOME`` / ``~/.config``.** (1 connections) — `tests/unit/test_config_layer.py`
- **Repo-local override sits at ``./.aom_config.yaml``.** (1 connections) — `tests/unit/test_config_layer.py`
- **Built-in ``default_config.yaml`` from the wheel is the lowest layer.** (1 connections) — `tests/unit/test_config_layer.py`

## Relationships

- [Community 511](Community_511.md) (4 shared connections)
- [Auto Version Bump Hook](Auto_Version_Bump_Hook.md) (3 shared connections)
- [Rerun CLI Entry](Rerun_CLI_Entry.md) (3 shared connections)
- [Core Module Init](Core_Module_Init.md) (2 shared connections)
- [Community 604](Community_604.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/config_layer.py`
- `tests/unit/test_config_layer.py`

## Audit Trail

- EXTRACTED: 32 (78%)
- INFERRED: 9 (22%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*