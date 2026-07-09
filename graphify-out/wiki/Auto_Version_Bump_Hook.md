# Auto Version Bump Hook

> 22 nodes · cohesion 0.14

## Key Concepts

- **AomSettings** (21 connections) — `src/ansible_aom/core/config_layer.py`
- **test_config_layer.py** (10 connections) — `tests/unit/test_config_layer.py`
- **_write_yaml()** (9 connections) — `tests/unit/test_config_layer.py`
- **TestDeepMerge** (7 connections) — `tests/unit/test_config_layer.py`
- **.test_nested_submodel_merges_across_files()** (6 connections) — `tests/unit/test_config_layer.py`
- **.test_partial_submodel_update_preserves_siblings()** (6 connections) — `tests/unit/test_config_layer.py`
- **.test_user_field_overrides_system_field()** (6 connections) — `tests/unit/test_config_layer.py`
- **TestEnvVarOverrides** (6 connections) — `tests/unit/test_config_layer.py`
- **.test_aom_config_env_changes_path_layer()** (6 connections) — `tests/unit/test_config_layer.py`
- **.test_aom_capture_verbose_env_overrides_yaml()** (5 connections) — `tests/unit/test_config_layer.py`
- **.settings_customise_sources()** (4 connections) — `src/ansible_aom/core/config_layer.py`
- **BaseSettings** (2 connections)
- **Any** (2 connections)
- **PydanticBaseSettingsSource** (1 connections)
- **Application settings — see :data:`_BUILTIN_DEFAULT` for the schema.** (1 connections) — `src/ansible_aom/core/config_layer.py`
- **Unit tests for the multi-layer config system (Task 3.1 / 3.2).  Covers the new :** (1 connections) — `tests/unit/test_config_layer.py`
- **Nested sub-models are merged, not replaced, across files.** (1 connections) — `tests/unit/test_config_layer.py`
- **Setting ``capture.verbose`` in user file does not lose system file's         ``c** (1 connections) — `tests/unit/test_config_layer.py`
- **The later (higher-priority) file wins on key collision.** (1 connections) — `tests/unit/test_config_layer.py`
- **``nested_model_default_partial_update=True`` keeps siblings.          Without th** (1 connections) — `tests/unit/test_config_layer.py`
- **``AOM_*`` env vars override YAML values (per pydantic-settings).** (1 connections) — `tests/unit/test_config_layer.py`
- **``AOM_CONFIG`` env var causes its file to be added to the layer list.** (1 connections) — `tests/unit/test_config_layer.py`

## Relationships

- [Rerun CLI Entry](Rerun_CLI_Entry.md) (10 shared connections)
- [Community 511](Community_511.md) (7 shared connections)
- [Community 604](Community_604.md) (6 shared connections)
- [Community 502](Community_502.md) (4 shared connections)
- [Prior Run Totals Injection](Prior_Run_Totals_Injection.md) (3 shared connections)
- [Module Init File](Module_Init_File.md) (2 shared connections)
- [Core Module Init](Core_Module_Init.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/config_layer.py`
- `tests/unit/test_config_layer.py`

## Audit Trail

- EXTRACTED: 75 (76%)
- INFERRED: 24 (24%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*