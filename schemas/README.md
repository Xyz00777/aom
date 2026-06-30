# JSON Schemas (deprecated)

The JSON schema files in this directory are **deprecated**. The
`RunSummary` Pydantic model in
`src/ansible_aom/formats/json.py` is the authoritative source of
truth for the run summary shape.

The committed `.json` files are kept only for test parity
(`test_run_summary_schema.py`). When the Pydantic model changes,
run `UPDATE_SCHEMA=1 pytest tests/unit/test_run_summary_schema.py`
to regenerate them.
