# Community 511

> 8 nodes · cohesion 0.32

## Key Concepts

- **MonkeyPatch** (18 connections)
- **TestExplicitPathOverride** (7 connections) — `tests/unit/test_config_layer.py`
- **.test_aom_config_env_appends_to_layer_list()** (4 connections) — `tests/unit/test_config_layer.py`
- **.test_cli_config_dash_dash_config_is_picked_up()** (4 connections) — `tests/unit/test_config_layer.py`
- **.test_env_var_wins_when_both_set()** (4 connections) — `tests/unit/test_config_layer.py`
- **``AOM_CONFIG`` env var and ``--config`` CLI flag both override the list.** (1 connections) — `tests/unit/test_config_layer.py`
- **``--config /path/to/file.yaml`` on sys.argv overrides too.** (1 connections) — `tests/unit/test_config_layer.py`
- **If both ``AOM_CONFIG`` and ``--config`` are set, env wins.** (1 connections) — `tests/unit/test_config_layer.py`

## Relationships

- [Auto Version Bump Hook](Auto_Version_Bump_Hook.md) (7 shared connections)
- [Rerun CLI Entry](Rerun_CLI_Entry.md) (7 shared connections)
- [Prior Run Totals Injection](Prior_Run_Totals_Injection.md) (4 shared connections)
- [Community 604](Community_604.md) (2 shared connections)
- [Community 502](Community_502.md) (2 shared connections)

## Source Files

- `tests/unit/test_config_layer.py`

## Audit Trail

- EXTRACTED: 37 (92%)
- INFERRED: 3 (8%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*