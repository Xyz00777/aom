# JSON Output Renderer

> 13 nodes · cohesion 0.22

## Key Concepts

- **RunSummary** (8 connections) — `src/ansible_aom/formats/json.py`
- **HostCounts** (7 connections) — `src/ansible_aom/formats/json.py`
- **TaskFailure** (7 connections) — `src/ansible_aom/formats/json.py`
- **BaseModel** (6 connections)
- **.handle_completion()** (6 connections) — `src/ansible_aom/formats/json.py`
- **json.py** (5 connections) — `src/ansible_aom/formats/json.py`
- **test_run_summary_model_has_pinned_schema()** (4 connections) — `tests/unit/test_json_renderer.py`
- **JSON output renderer for AOM (F6).  Implements the Renderer Protocol but produce** (1 connections) — `src/ansible_aom/formats/json.py`
- **Build the RunSummary from accumulated RunState and print as JSON.          ``exi** (1 connections) — `src/ansible_aom/formats/json.py`
- **Per-host status counts aggregated across every task in every play.** (1 connections) — `src/ansible_aom/formats/json.py`
- **One (host, task) pair that ended in FAILED or UNREACHABLE.** (1 connections) — `src/ansible_aom/formats/json.py`
- **End-of-run summary emitted by ``JsonRenderer.handle_completion``.      Field rul** (1 connections) — `src/ansible_aom/formats/json.py`
- **RunSummary captures every field the schema spec requires.** (1 connections) — `tests/unit/test_json_renderer.py`

## Relationships

- [[Run State Summary Panel]] (4 shared connections)
- [[JSON Renderer]] (3 shared connections)
- [[Role Group Task Models]] (3 shared connections)
- [[RunSummary Schema Contract]] (2 shared connections)
- [[Status Bar Warning Panels]] (1 shared connections)
- [[Secret Redaction Configuration]] (1 shared connections)
- [[Warnings Display Config]] (1 shared connections)

## Source Files

- `src/ansible_aom/formats/json.py`
- `tests/unit/test_json_renderer.py`

## Audit Trail

- EXTRACTED: 36 (73%)
- INFERRED: 13 (27%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*