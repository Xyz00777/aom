# Auto Version Bump Hook

> 80 nodes · cohesion 0.05

## Key Concepts

- **Path** (20 connections)
- **AomSettings** (19 connections) — `src/ansible_aom/core/config_layer.py`
- **MonkeyPatch** (18 connections)
- **config_layer.py** (12 connections) — `src/ansible_aom/core/config_layer.py`
- **CaptureConfig** (10 connections) — `src/ansible_aom/core/config_layer.py`
- **test_config_layer.py** (10 connections) — `tests/unit/test_config_layer.py`
- **find_config_paths()** (9 connections) — `src/ansible_aom/core/config_layer.py`
- **_write_yaml()** (9 connections) — `tests/unit/test_config_layer.py`
- **TestLegacyMigration** (8 connections) — `tests/unit/test_config_layer.py`
- **TestXdgPathResolution** (8 connections) — `tests/unit/test_config_layer.py`
- **load_config_with_layers()** (7 connections) — `src/ansible_aom/core/config_layer.py`
- **migrate_legacy_config()** (7 connections) — `src/ansible_aom/core/config_layer.py`
- **.test_init_kwargs_beat_yaml()** (7 connections) — `tests/unit/test_config_layer.py`
- **TestDeepMerge** (7 connections) — `tests/unit/test_config_layer.py`
- **TestExplicitPathOverride** (7 connections) — `tests/unit/test_config_layer.py`
- **BaseModel** (6 connections)
- **.test_nested_submodel_merges_across_files()** (6 connections) — `tests/unit/test_config_layer.py`
- **.test_partial_submodel_update_preserves_siblings()** (6 connections) — `tests/unit/test_config_layer.py`
- **.test_user_field_overrides_system_field()** (6 connections) — `tests/unit/test_config_layer.py`
- **TestEnvVarOverrides** (6 connections) — `tests/unit/test_config_layer.py`
- **.test_aom_config_env_changes_path_layer()** (6 connections) — `tests/unit/test_config_layer.py`
- **.test_new_file_already_exists_skips_migration()** (6 connections) — `tests/unit/test_config_layer.py`
- **.test_old_config_yaml_is_migrated()** (6 connections) — `tests/unit/test_config_layer.py`
- **TestMissingFilesSkipped** (6 connections) — `tests/unit/test_config_layer.py`
- **_read_yaml()** (5 connections) — `tests/unit/test_config_layer.py`
- *... and 55 more nodes in this community*

## Relationships

- [TestConfigPathFlag](TestConfigPathFlag.md) (1 shared connections)
- [ansible_aom/cli.py](ansible_aom-cli.py.md) (1 shared connections)
- [load_session](load_session.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/config_layer.py`
- `tests/unit/test_config_layer.py`

## Audit Trail

- EXTRACTED: 268 (81%)
- INFERRED: 63 (19%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*