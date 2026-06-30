# Parser Phase Transitions

> 10 nodes · cohesion 0.20

## Key Concepts

- **TestPhaseTransitions** (10 connections) — `tests/integration/test_playbook_parser.py`
- **.test_execution_to_post_run_on_stats_event()** (3 connections) — `tests/integration/test_playbook_parser.py`
- **.test_initial_phase_is_pre_run_prompts()** (3 connections) — `tests/integration/test_playbook_parser.py`
- **.test_non_json_lines_handled_during_execution()** (3 connections) — `tests/integration/test_playbook_parser.py`
- **.test_pre_run_to_execution_on_start_event()** (3 connections) — `tests/integration/test_playbook_parser.py`
- **Test PtyStreamParser phase transitions.** (1 connections) — `tests/integration/test_playbook_parser.py`
- **Parser starts in PRE_RUN_PROMPTS phase.** (1 connections) — `tests/integration/test_playbook_parser.py`
- **PRE_RUN_PROMPTS -> EXECUTION on v2_playbook_on_start.** (1 connections) — `tests/integration/test_playbook_parser.py`
- **EXECUTION -> POST_RUN_RECAP on v2_playbook_on_stats.** (1 connections) — `tests/integration/test_playbook_parser.py`
- **Non-JSON lines during EXECUTION are added to plaintext_lines.** (1 connections) — `tests/integration/test_playbook_parser.py`

## Relationships

- [[PTY Stream Parser]] (5 shared connections)
- [[Role Group Task Models]] (2 shared connections)
- [[Run State Summary Panel]] (1 shared connections)
- [[Playbook Parser Integration Tests]] (1 shared connections)

## Source Files

- `tests/integration/test_playbook_parser.py`

## Audit Trail

- EXTRACTED: 23 (85%)
- INFERRED: 4 (15%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*