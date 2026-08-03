# Total Task Counting

> 16 nodes · cohesion 0.21

## Key Concepts

- **test_meta_schema_version.py** (10 connections) — `tests/unit/test_meta_schema_version.py`
- **Path** (7 connections)
- **_start_and_end()** (7 connections) — `tests/unit/test_meta_schema_version.py`
- **test_load_session_exposes_schema_version_2()** (5 connections) — `tests/unit/test_meta_schema_version.py`
- **test_load_session_of_v2_session_round_trips_schema_version_2()** (5 connections) — `tests/unit/test_meta_schema_version.py`
- **test_end_session_preserves_schema_version_2()** (4 connections) — `tests/unit/test_meta_schema_version.py`
- **test_load_session_defaults_missing_schema_version_to_1()** (4 connections) — `tests/unit/test_meta_schema_version.py`
- **test_schema_version_2_coexists_with_existing_meta_fields()** (4 connections) — `tests/unit/test_meta_schema_version.py`
- **test_start_session_writes_schema_version_2()** (4 connections) — `tests/unit/test_meta_schema_version.py`
- **Phase 1 / Task 1.1: meta.json `_schema_version` bump.  Per `.sisyphus/plans/v1-v** (1 connections) — `tests/unit/test_meta_schema_version.py`
- **End-to-end: SessionManager writes v2; load_session returns v2.** (1 connections) — `tests/unit/test_meta_schema_version.py`
- **``start_session`` persists ``_schema_version: 2`` immediately.      The field is** (1 connections) — `tests/unit/test_meta_schema_version.py`
- **``end_session`` does not strip the schema field added at start.** (1 connections) — `tests/unit/test_meta_schema_version.py`
- **The bump is additive: every v1 field is still present and unchanged.      Guards** (1 connections) — `tests/unit/test_meta_schema_version.py`
- **``load_session`` surfaces the new field on the returned dict.** (1 connections) — `tests/unit/test_meta_schema_version.py`
- **A v1 legacy ``meta.json`` (no ``_schema_version`` field) loads cleanly     and r** (1 connections) — `tests/unit/test_meta_schema_version.py`

## Relationships

- [Include Role Discovery](Include_Role_Discovery.md) (3 shared connections)
- [Run Config Key Normalization](Run_Config_Key_Normalization.md) (2 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (1 shared connections)
- [StatusBarConfig Model](StatusBarConfig_Model.md) (1 shared connections)

## Source Files

- `tests/unit/test_meta_schema_version.py`

## Audit Trail

- EXTRACTED: 52 (91%)
- INFERRED: 5 (9%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*