# RunSummary Schema Contract

> 22 nodes · cohesion 0.11

## Key Concepts

- **test_run_summary_schema.py** (7 connections) — `tests/unit/test_run_summary_schema.py`
- **TestSchemaVersionPin** (6 connections) — `tests/unit/test_run_summary_schema.py`
- **_load_committed_schema()** (5 connections) — `tests/unit/test_run_summary_schema.py`
- **TestSchemaParity** (4 connections) — `tests/unit/test_run_summary_schema.py`
- **_canonical_schema_text()** (3 connections) — `tests/unit/test_run_summary_schema.py`
- **test_golden_payload_validates_against_committed_schema()** (3 connections) — `tests/unit/test_run_summary_schema.py`
- **test_pydantic_roundtrip_also_validates()** (3 connections) — `tests/unit/test_run_summary_schema.py`
- **.test_committed_schema_matches_current_model()** (3 connections) — `tests/unit/test_run_summary_schema.py`
- **.test_committed_schema_pins_schema_version_to_one()** (3 connections) — `tests/unit/test_run_summary_schema.py`
- **.test_construction_with_wrong_version_rejected()** (2 connections) — `tests/unit/test_run_summary_schema.py`
- **.test_live_model_instance_has_schema_version_one()** (2 connections) — `tests/unit/test_run_summary_schema.py`
- **Contract test for the committed ``RunSummary`` v1 JSON schema (Item #7).  Downst** (1 connections) — `tests/unit/test_run_summary_schema.py`
- **Load the on-disk schema. Skipped if missing (handled in Layer 1).** (1 connections) — `tests/unit/test_run_summary_schema.py`
- **Each canonical shape must validate. Catches accidental tightening.** (1 connections) — `tests/unit/test_run_summary_schema.py`
- **Bonus: a payload produced through the Pydantic model must validate.      Prevent** (1 connections) — `tests/unit/test_run_summary_schema.py`
- **``schema_version`` is the only stable contract callers can pin to.** (1 connections) — `tests/unit/test_run_summary_schema.py`
- **JSON Schema's ``const`` keyword fixes the value to literally 1.** (1 connections) — `tests/unit/test_run_summary_schema.py`
- **The model itself emits 1, matching what the schema requires.** (1 connections) — `tests/unit/test_run_summary_schema.py`
- **``Literal[1]`` rejects any other integer at construction time.** (1 connections) — `tests/unit/test_run_summary_schema.py`
- **Pretty-print the current ``RunSummary`` schema for comparison.      Format pinne** (1 connections) — `tests/unit/test_run_summary_schema.py`
- **The committed schema must match the model verbatim.** (1 connections) — `tests/unit/test_run_summary_schema.py`
- **Re-generate and compare. Failure means the model drifted.          The escape ha** (1 connections) — `tests/unit/test_run_summary_schema.py`

## Relationships

- [[JSON Output Renderer]] (2 shared connections)

## Source Files

- `tests/unit/test_run_summary_schema.py`

## Audit Trail

- EXTRACTED: 50 (96%)
- INFERRED: 2 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*