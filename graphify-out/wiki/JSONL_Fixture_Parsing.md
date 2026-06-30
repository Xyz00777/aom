# JSONL Fixture Parsing

> 8 nodes · cohesion 0.25

## Key Concepts

- **TestJsonlFixtures** (10 connections) — `tests/integration/test_playbook_parser.py`
- **.test_multi_host_mixed_fixture()** (5 connections) — `tests/integration/test_playbook_parser.py`
- **.test_playbook_failed_fixture()** (5 connections) — `tests/integration/test_playbook_parser.py`
- **.test_single_task_ok_fixture()** (5 connections) — `tests/integration/test_playbook_parser.py`
- **Tests using pre-recorded JSONL fixtures (no ansible-playbook needed).** (1 connections) — `tests/integration/test_playbook_parser.py`
- **Parse single_task_ok.jsonl fixture.** (1 connections) — `tests/integration/test_playbook_parser.py`
- **Parse playbook_failed.jsonl fixture.** (1 connections) — `tests/integration/test_playbook_parser.py`
- **Parse multi_host_mixed.jsonl fixture.** (1 connections) — `tests/integration/test_playbook_parser.py`

## Relationships

- [[Run State Summary Panel]] (4 shared connections)
- [[PTY Stream Parser]] (4 shared connections)
- [[Run Config Key Normalization]] (4 shared connections)
- [[Role Group Task Models]] (2 shared connections)
- [[Playbook Parser Integration Tests]] (1 shared connections)

## Source Files

- `tests/integration/test_playbook_parser.py`

## Audit Trail

- EXTRACTED: 25 (86%)
- INFERRED: 4 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*