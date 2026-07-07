# PTY Stream Parser

> 41 nodes · cohesion 0.03

## Key Concepts

- **PtyStreamParser** (333 connections) — `src/ansible_aom/core/parser.py`
- **.feed_line()** (9 connections) — `src/ansible_aom/core/parser.py`
- **._handle_plaintext()** (7 connections) — `src/ansible_aom/core/parser.py`
- **._parse_and_return()** (5 connections) — `src/ansible_aom/core/parser.py`
- **._is_json()** (4 connections) — `src/ansible_aom/core/parser.py`
- **._is_jsonl_start_event()** (4 connections) — `src/ansible_aom/core/parser.py`
- **._is_jsonl_stats_event()** (4 connections) — `src/ansible_aom/core/parser.py`
- **.test_password_prompt_detected_patterns()** (4 connections) — `tests/integration/test_error_handling.py`
- **.test_process_runner_start_free_strategy()** (4 connections) — `tests/unit/test_parser.py`
- **.test_password_pattern_vault()** (4 connections) — `tests/unit/test_parser.py`
- **.drain_warnings()** (3 connections) — `src/ansible_aom/core/parser.py`
- **._parse_json()** (3 connections) — `src/ansible_aom/core/parser.py`
- **.test_password_patterns_defined()** (3 connections) — `tests/integration/test_error_handling.py`
- **.test_process_play_start_creates_play_state()** (3 connections) — `tests/unit/test_parser.py`
- **.test_process_playbook_start_sets_start_time()** (3 connections) — `tests/unit/test_parser.py`
- **.test_process_task_start_linear_strategy()** (3 connections) — `tests/unit/test_parser.py`
- **.test_clear_password_prompt()** (3 connections) — `tests/unit/test_parser.py`
- **.test_deprecated_removed_pattern()** (3 connections) — `tests/unit/test_parser.py`
- **.test_deprecation_warning_pattern()** (3 connections) — `tests/unit/test_parser.py`
- **.test_initial_phase_pre_run_prompts()** (3 connections) — `tests/unit/test_parser.py`
- **.test_password_pattern_become()** (3 connections) — `tests/unit/test_parser.py`
- **.test_password_pattern_ssh()** (3 connections) — `tests/unit/test_parser.py`
- **.test_play_recap_detection()** (3 connections) — `tests/unit/test_parser.py`
- **.test_transition_to_execution_on_start_event()** (3 connections) — `tests/unit/test_parser.py`
- **.test_transition_to_post_run_on_stats_event()** (3 connections) — `tests/unit/test_parser.py`
- *... and 16 more nodes in this community*

## Relationships

- [[Role Group Task Models]] (55 shared connections)
- [[Parser Phase Transitions]] (14 shared connections)
- [[Warning Pattern Detection]] (13 shared connections)
- [[Password Pattern Detection]] (13 shared connections)
- [[Warning Classification Tests]] (12 shared connections)
- [[Parser Edge Cases]] (11 shared connections)
- [[Playbook Parser Integration Tests]] (10 shared connections)
- [[PTY Stream Parser Tests]] (10 shared connections)
- [[Conftest Fixture Validation]] (9 shared connections)
- [[Error Handling Tests]] (7 shared connections)
- [[Play Recap Detection]] (7 shared connections)
- [[Compact Password Passthrough]] (6 shared connections)

## Source Files

- `src/ansible_aom/core/parser.py`
- `tests/integration/test_error_handling.py`
- `tests/unit/test_parser.py`

## Audit Trail

- EXTRACTED: 149 (33%)
- INFERRED: 305 (67%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*