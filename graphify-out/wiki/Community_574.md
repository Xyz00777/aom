# Community 574

> 6 nodes · cohesion 0.40

## Key Concepts

- **test_session_meta_persistence.py** (4 connections) — `tests/unit/test_session_meta_persistence.py`
- **test_end_session_without_counts_writes_nulls()** (4 connections) — `tests/unit/test_session_meta_persistence.py`
- **test_end_session_persists_task_and_host_counts()** (3 connections) — `tests/unit/test_session_meta_persistence.py`
- **Path** (2 connections)
- **Tests that end_session persists task_count / host_count for the history feature.** (1 connections) — `tests/unit/test_session_meta_persistence.py`
- **Backwards-compatible — callers that don't pass counts still produce valid meta.** (1 connections) — `tests/unit/test_session_meta_persistence.py`

## Relationships

- [Run Config Key Normalization](Run_Config_Key_Normalization.md) (2 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (1 shared connections)

## Source Files

- `tests/unit/test_session_meta_persistence.py`

## Audit Trail

- EXTRACTED: 13 (87%)
- INFERRED: 2 (13%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*