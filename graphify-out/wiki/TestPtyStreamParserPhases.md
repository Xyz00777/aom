# TestPtyStreamParserPhases

> 22 nodes · cohesion 0.09

## Key Concepts

- **TestPtyStreamParserPhases** (25 connections) — `tests/unit/test_parser.py`
- **.test_clear_password_prompt()** (3 connections) — `tests/unit/test_parser.py`
- **.test_deprecation_warning_pattern()** (3 connections) — `tests/unit/test_parser.py`
- **.test_initial_phase_pre_run_prompts()** (3 connections) — `tests/unit/test_parser.py`
- **.test_password_pattern_become()** (3 connections) — `tests/unit/test_parser.py`
- **.test_password_pattern_ssh()** (3 connections) — `tests/unit/test_parser.py`
- **.test_password_pattern_vault()** (3 connections) — `tests/unit/test_parser.py`
- **.test_play_recap_detection()** (3 connections) — `tests/unit/test_parser.py`
- **.test_transition_to_execution_on_start_event()** (3 connections) — `tests/unit/test_parser.py`
- **.test_transition_to_post_run_on_stats_event()** (3 connections) — `tests/unit/test_parser.py`
- **.test_warning_pattern_detection()** (3 connections) — `tests/unit/test_parser.py`
- **TC-128 to TC-142: PTY stream phase transitions.** (1 connections) — `tests/unit/test_parser.py`
- **TC-128: Initial phase is PRE_RUN_PROMPTS.** (1 connections) — `tests/unit/test_parser.py`
- **TC-131: Start event triggers PRE_RUN_PROMPTS -> EXECUTION.** (1 connections) — `tests/unit/test_parser.py`
- **TC-132: Stats event triggers EXECUTION -> POST_RUN_RECAP.** (1 connections) — `tests/unit/test_parser.py`
- **TC-134: Vault password prompt pattern detected.** (1 connections) — `tests/unit/test_parser.py`
- **TC-136: SSH password prompt pattern detected.** (1 connections) — `tests/unit/test_parser.py`
- **TC-137: BECOME password prompt pattern detected.** (1 connections) — `tests/unit/test_parser.py`
- **TC-141: [WARNING]: pattern detected.** (1 connections) — `tests/unit/test_parser.py`
- **TC-141: [DEPRECATION WARNING]: pattern detected.** (1 connections) — `tests/unit/test_parser.py`
- **TC-140: PLAY RECAP pattern detected.** (1 connections) — `tests/unit/test_parser.py`
- **Password prompt can be cleared after handling.** (1 connections) — `tests/unit/test_parser.py`

## Relationships

- [PtyStreamParser](PtyStreamParser.md) (11 shared connections)
- [HostRunState](HostRunState.md) (4 shared connections)
- [WarningType](WarningType.md) (4 shared connections)
- [TaskDefinition](TaskDefinition.md) (2 shared connections)
- [PlayDefinition](PlayDefinition.md) (1 shared connections)
- [StreamPhase](StreamPhase.md) (1 shared connections)
- [JsonLineStream](JsonLineStream.md) (1 shared connections)

## Source Files

- `tests/unit/test_parser.py`

## Audit Trail

- EXTRACTED: 54 (82%)
- INFERRED: 12 (18%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*