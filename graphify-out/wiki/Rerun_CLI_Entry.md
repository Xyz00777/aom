# Rerun CLI Entry

> 14 nodes · cohesion 0.23

## Key Concepts

- **Path** (20 connections)
- **TestLegacyMigration** (8 connections) — `tests/unit/test_config_layer.py`
- **migrate_legacy_config()** (7 connections) — `src/ansible_aom/core/config_layer.py`
- **.test_new_file_already_exists_skips_migration()** (6 connections) — `tests/unit/test_config_layer.py`
- **.test_old_config_yaml_is_migrated()** (6 connections) — `tests/unit/test_config_layer.py`
- **_read_yaml()** (5 connections) — `tests/unit/test_config_layer.py`
- **.test_migration_does_not_run_twice()** (5 connections) — `tests/unit/test_config_layer.py`
- **.test_no_old_config_means_no_migration()** (5 connections) — `tests/unit/test_config_layer.py`
- **One-shot ``config.yaml`` → ``aom_config.yaml`` migration.      Returns True if a** (1 connections) — `src/ansible_aom/core/config_layer.py`
- **Old ``config.yaml`` is auto-migrated to ``aom_config.yaml`` on first run.** (1 connections) — `tests/unit/test_config_layer.py`
- **Old ``config.yaml`` → ``aom_config.yaml``; original moved to         ``config.ya** (1 connections) — `tests/unit/test_config_layer.py`
- **``migrate_legacy_config`` returns False when there's nothing to migrate.** (1 connections) — `tests/unit/test_config_layer.py`
- **If both old and new exist, we don't clobber the new one.** (1 connections) — `tests/unit/test_config_layer.py`
- **Second call after a successful migration is a no-op.** (1 connections) — `tests/unit/test_config_layer.py`

## Relationships

- [Auto Version Bump Hook](Auto_Version_Bump_Hook.md) (10 shared connections)
- [Community 511](Community_511.md) (7 shared connections)
- [Community 502](Community_502.md) (3 shared connections)
- [Prior Run Totals Injection](Prior_Run_Totals_Injection.md) (3 shared connections)
- [Community 604](Community_604.md) (2 shared connections)
- [Core Module Init](Core_Module_Init.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/config_layer.py`
- `tests/unit/test_config_layer.py`

## Audit Trail

- EXTRACTED: 58 (85%)
- INFERRED: 10 (15%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*