# TestPtyStreamParserPhaseTransitions

> 18 nodes · cohesion 0.11

## Key Concepts

- **TestPtyStreamParserPhaseTransitions** (13 connections) — `tests/unit/test_pty_stream.py`
- **.test_initial_phase_is_pre_run_prompts()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_phase_remains_execution_without_stats_event()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_phase_remains_pre_run_without_start_event()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_post_run_recap_collects_lines()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_transition_to_execution_on_first_jsonl()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_transition_to_execution_on_start_event()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_transition_to_post_run_on_recap_line()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_transition_to_post_run_on_stats_event()** (3 connections) — `tests/unit/test_pty_stream.py`
- **Phase stays EXECUTION without v2_playbook_on_stats.** (1 connections) — `tests/unit/test_pty_stream.py`
- **Lines in POST_RUN_RECAP phase are collected.** (1 connections) — `tests/unit/test_pty_stream.py`
- **TC-128, TC-131, TC-132: Phase transition tests.** (1 connections) — `tests/unit/test_pty_stream.py`
- **TC-128: Initial phase is PRE_RUN_PROMPTS.** (1 connections) — `tests/unit/test_pty_stream.py`
- **TC-131: v2_playbook_on_start triggers PRE_RUN_PROMPTS -> EXECUTION.** (1 connections) — `tests/unit/test_pty_stream.py`
- **TC-131: First JSONL event triggers transition to EXECUTION.** (1 connections) — `tests/unit/test_pty_stream.py`
- **TC-132: v2_playbook_on_stats triggers EXECUTION -> POST_RUN_RECAP.** (1 connections) — `tests/unit/test_pty_stream.py`
- **TC-132: PLAY RECAP line triggers EXECUTION -> POST_RUN_RECAP.** (1 connections) — `tests/unit/test_pty_stream.py`
- **Phase stays PRE_RUN_PROMPTS without v2_playbook_on_start.** (1 connections) — `tests/unit/test_pty_stream.py`

## Relationships

- [PtyStreamParser](PtyStreamParser.md) (9 shared connections)
- [WarningType](WarningType.md) (1 shared connections)
- [StreamPhase](StreamPhase.md) (1 shared connections)
- [test_pty_stream.py](test_pty_stream.py.md) (1 shared connections)

## Source Files

- `tests/unit/test_pty_stream.py`

## Audit Trail

- EXTRACTED: 43 (93%)
- INFERRED: 3 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*