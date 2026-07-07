# Playbook Parser Integration Tests

> 29 nodes · cohesion 0.05

## Key Concepts

- **parse_jsonl_output()** (37 connections) — `tests/integration/test_playbook_parser.py`
- **test_playbook_parser.py** (35 connections) — `tests/integration/test_playbook_parser.py`
- **run_ansible_playbook()** (35 connections) — `tests/integration/test_playbook_parser.py`
- **TestEmptyPlaybook** (9 connections) — `tests/integration/test_playbook_parser.py`
- **TestMultiHostMixed** (9 connections) — `tests/integration/test_playbook_parser.py`
- **TestMultiplePlays** (9 connections) — `tests/integration/test_playbook_parser.py`
- **TestPlayRecap** (9 connections) — `tests/integration/test_playbook_parser.py`
- **TestSingleTaskSuccess** (9 connections) — `tests/integration/test_playbook_parser.py`
- **TestSyntaxError** (9 connections) — `tests/integration/test_playbook_parser.py`
- **TestWarnings** (9 connections) — `tests/integration/test_playbook_parser.py`
- **TestIgnoreErrors** (8 connections) — `tests/integration/test_playbook_parser.py`
- **TestTaskFailure** (7 connections) — `tests/integration/test_playbook_parser.py`
- **.test_deprecation_warnings_captured()** (6 connections) — `tests/integration/test_playbook_parser.py`
- **.test_empty_playbook_no_plays()** (6 connections) — `tests/integration/test_playbook_parser.py`
- **.test_multi_host_mixed_results()** (6 connections) — `tests/integration/test_playbook_parser.py`
- **.test_recap_lines_captured()** (6 connections) — `tests/integration/test_playbook_parser.py`
- **.test_syntax_error_fails_before_jsonl()** (6 connections) — `tests/integration/test_playbook_parser.py`
- **.test_warnings_captured()** (6 connections) — `tests/integration/test_playbook_parser.py`
- **test_skipped_tasks()** (5 connections) — `tests/integration/test_playbook_parser.py`
- **.test_parser_handles_ignore_errors()** (5 connections) — `tests/integration/test_playbook_parser.py`
- **.test_parser_tracks_multiple_plays()** (5 connections) — `tests/integration/test_playbook_parser.py`
- **.test_play_names_extracted()** (5 connections) — `tests/integration/test_playbook_parser.py`
- **.test_parser_detects_changed_status()** (4 connections) — `tests/integration/test_playbook_parser.py`
- **.test_host_status_ok()** (4 connections) — `tests/integration/test_playbook_parser.py`
- **.test_parser_phases_correct()** (4 connections) — `tests/integration/test_playbook_parser.py`
- *... and 4 more nodes in this community*

## Relationships

- [[Role Group Task Models]] (28 shared connections)
- [[PTY Stream Parser]] (10 shared connections)
- [[Become Password Prompt]] (1 shared connections)
- [[JSONL Event Parsing]] (1 shared connections)
- [[JSONL Fixture Parsing]] (1 shared connections)
- [[Large Playbook Performance]] (1 shared connections)
- [[Password Prompt Detection]] (1 shared connections)
- [[Parser Phase Transitions]] (1 shared connections)
- [[Warning Pattern Detection]] (1 shared connections)

## Source Files

- `tests/integration/test_playbook_parser.py`

## Audit Trail

- EXTRACTED: 230 (86%)
- INFERRED: 36 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*