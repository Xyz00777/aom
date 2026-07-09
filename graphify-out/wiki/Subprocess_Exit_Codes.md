# Subprocess Exit Codes

> 23 nodes · cohesion 0.11

## Key Concepts

- **TestEventParsing** (11 connections) — `tests/integration/test_playbook_parser.py`
- **TestJsonlFixtures** (10 connections) — `tests/integration/test_playbook_parser.py`
- **Path** (9 connections)
- **.test_v2_playbook_on_stats_event()** (5 connections) — `tests/integration/test_playbook_parser.py`
- **.test_v2_runner_on_failed_event()** (5 connections) — `tests/integration/test_playbook_parser.py`
- **.test_v2_runner_on_ok_event()** (5 connections) — `tests/integration/test_playbook_parser.py`
- **.test_multi_host_mixed_fixture()** (5 connections) — `tests/integration/test_playbook_parser.py`
- **.test_playbook_failed_fixture()** (5 connections) — `tests/integration/test_playbook_parser.py`
- **.test_single_task_ok_fixture()** (5 connections) — `tests/integration/test_playbook_parser.py`
- **.test_v2_playbook_on_start_event()** (4 connections) — `tests/integration/test_playbook_parser.py`
- **.fixtures_dir()** (3 connections) — `tests/integration/test_playbook_parser.py`
- **.fixtures_dir()** (3 connections) — `tests/integration/test_playbook_parser.py`
- **Tests using pre-recorded JSONL fixtures (no ansible-playbook needed).** (1 connections) — `tests/integration/test_playbook_parser.py`
- **Return path to tests/fixtures directory.** (1 connections) — `tests/integration/test_playbook_parser.py`
- **Parse single_task_ok.jsonl fixture.** (1 connections) — `tests/integration/test_playbook_parser.py`
- **Parse playbook_failed.jsonl fixture.** (1 connections) — `tests/integration/test_playbook_parser.py`
- **Parse multi_host_mixed.jsonl fixture.** (1 connections) — `tests/integration/test_playbook_parser.py`
- **Test parsing of specific event types from JSONL.** (1 connections) — `tests/integration/test_playbook_parser.py`
- **Return path to tests/fixtures directory.** (1 connections) — `tests/integration/test_playbook_parser.py`
- **v2_playbook_on_start triggers EXECUTION phase.** (1 connections) — `tests/integration/test_playbook_parser.py`
- **v2_playbook_on_stats triggers POST_RUN_RECAP phase and sets end_time.** (1 connections) — `tests/integration/test_playbook_parser.py`
- **v2_runner_on_ok creates HostRunState with OK status.** (1 connections) — `tests/integration/test_playbook_parser.py`
- **v2_runner_on_failed creates HostRunState with FAILED status.** (1 connections) — `tests/integration/test_playbook_parser.py`

## Relationships

- [Run State Completion Recap](Run_State_Completion_Recap.md) (9 shared connections)
- [Status Bar Warning Panels](Status_Bar_Warning_Panels.md) (8 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (4 shared connections)
- [Compact Renderer Integration Tests](Compact_Renderer_Integration_Tests.md) (2 shared connections)

## Source Files

- `tests/integration/test_playbook_parser.py`

## Audit Trail

- EXTRACTED: 73 (90%)
- INFERRED: 8 (10%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*