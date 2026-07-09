# Community 604

> 5 nodes · cohesion 0.50

## Key Concepts

- **CaptureConfig** (10 connections) — `src/ansible_aom/core/config_layer.py`
- **.test_init_kwargs_beat_yaml()** (7 connections) — `tests/unit/test_config_layer.py`
- **TestCliOverrides** (5 connections) — `tests/unit/test_config_layer.py`
- **``AomSettings(**kwargs)`` from the CLI wins over every layer.** (1 connections) — `tests/unit/test_config_layer.py`
- **Passing ``capture=CaptureConfig(verbose=True)`` wins over YAML.** (1 connections) — `tests/unit/test_config_layer.py`

## Relationships

- [Auto Version Bump Hook](Auto_Version_Bump_Hook.md) (6 shared connections)
- [Core Module Init](Core_Module_Init.md) (2 shared connections)
- [Community 511](Community_511.md) (2 shared connections)
- [Rerun CLI Entry](Rerun_CLI_Entry.md) (2 shared connections)
- [Community 502](Community_502.md) (1 shared connections)
- [Prior Run Totals Injection](Prior_Run_Totals_Injection.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/config_layer.py`
- `tests/unit/test_config_layer.py`

## Audit Trail

- EXTRACTED: 12 (50%)
- INFERRED: 12 (50%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*