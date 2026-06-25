# JSONL Event Parsing

> 10 nodes · cohesion 0.20

## Key Concepts

- **TestEventParsing** (11 connections) — `tests/integration/test_playbook_parser.py`
- **.test_v2_playbook_on_stats_event()** (5 connections) — `tests/integration/test_playbook_parser.py`
- **.test_v2_runner_on_failed_event()** (5 connections) — `tests/integration/test_playbook_parser.py`
- **.test_v2_runner_on_ok_event()** (5 connections) — `tests/integration/test_playbook_parser.py`
- **.test_v2_playbook_on_start_event()** (4 connections) — `tests/integration/test_playbook_parser.py`
- **Test parsing of specific event types from JSONL.** (1 connections) — `tests/integration/test_playbook_parser.py`
- **v2_playbook_on_start triggers EXECUTION phase.** (1 connections) — `tests/integration/test_playbook_parser.py`
- **v2_playbook_on_stats triggers POST_RUN_RECAP phase and sets end_time.** (1 connections) — `tests/integration/test_playbook_parser.py`
- **v2_runner_on_ok creates HostRunState with OK status.** (1 connections) — `tests/integration/test_playbook_parser.py`
- **v2_runner_on_failed creates HostRunState with FAILED status.** (1 connections) — `tests/integration/test_playbook_parser.py`

## Relationships

- [[PTY Stream Parser]] (5 shared connections)
- [[Run Config Key Normalization]] (5 shared connections)
- [[Run State Summary Panel]] (4 shared connections)
- [[Role Group Task Models]] (2 shared connections)
- [[Playbook Parser Integration Tests]] (1 shared connections)

## Source Files

- `tests/integration/test_playbook_parser.py`

## Audit Trail

- EXTRACTED: 31 (89%)
- INFERRED: 4 (11%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*