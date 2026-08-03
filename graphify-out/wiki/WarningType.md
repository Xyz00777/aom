# WarningType

> 109 nodes · cohesion 0.03

## Key Concepts

- **WarningType** (95 connections) — `src/ansible_aom/core/models.py`
- **PreParseResult** (35 connections) — `src/ansible_aom/core/parser.py`
- **parse_list_hosts_output()** (28 connections) — `src/ansible_aom/core/parser.py`
- **test_parser.py** (24 connections) — `tests/unit/test_parser.py`
- **TestListHostsEdgeCases** (23 connections) — `tests/unit/test_parser.py`
- **TestListHostsParser** (20 connections) — `tests/unit/test_parser.py`
- **TestMultiLineWarningContinuation** (18 connections) — `tests/unit/test_parser.py`
- **TestPtyStreamParserJsonlEvents** (18 connections) — `tests/unit/test_parser.py`
- **TestWarningDetectionThroughAnsiPrefix** (18 connections) — `tests/unit/test_parser.py`
- **TestListHostsFallback** (17 connections) — `tests/unit/test_parser.py`
- **TestListTasksListHostsIntegration** (16 connections) — `tests/unit/test_parser.py`
- **TestParallelPreParse** (16 connections) — `tests/unit/test_parser.py`
- **TestPtyStreamParserPlaintextCap** (16 connections) — `tests/unit/test_parser.py`
- **TestStatusEnum** (16 connections) — `tests/unit/test_parser.py`
- **.test_preparse_result_assembly()** (5 connections) — `tests/unit/test_parser.py`
- **.test_list_hosts_all_inventory()** (4 connections) — `tests/unit/test_parser.py`
- **.test_parse_play_line_pattern()** (4 connections) — `tests/unit/test_parser.py`
- **.test_skip_non_host_lines()** (4 connections) — `tests/unit/test_parser.py`
- **._feed_wrapped_warning()** (4 connections) — `tests/unit/test_parser.py`
- **.test_concurrent_parse_combine_results()** (4 connections) — `tests/unit/test_parser.py`
- **.test_parallel_parse_does_not_corrupt_data()** (4 connections) — `tests/unit/test_parser.py`
- **.test_process_task_start_linear_strategy()** (4 connections) — `tests/unit/test_parser.py`
- **.test_list_hosts_output_populates_resolved_hosts()** (3 connections) — `tests/unit/test_host_resolution.py`
- **.test_warning_type_enum_has_two_values()** (3 connections) — `tests/unit/test_models.py`
- **.test_list_hosts_dynamic_inventory_timeout()** (3 connections) — `tests/unit/test_parser.py`
- *... and 84 more nodes in this community*

## Relationships

- [HostRunState](HostRunState.md) (44 shared connections)
- [PtyStreamParser](PtyStreamParser.md) (39 shared connections)
- [TaskDefinition](TaskDefinition.md) (29 shared connections)
- [WarningEntry](WarningEntry.md) (25 shared connections)
- [JsonLineStream](JsonLineStream.md) (20 shared connections)
- [StreamPhase](StreamPhase.md) (16 shared connections)
- [PlayDefinition](PlayDefinition.md) (11 shared connections)
- [parse_list_tasks_output](parse_list_tasks_output.md) (10 shared connections)
- [test_pty_stream.py](test_pty_stream.py.md) (5 shared connections)
- [TestWarningPatternsEdgeCases](TestWarningPatternsEdgeCases.md) (5 shared connections)
- [RunState](RunState.md) (4 shared connections)
- [TestPtyStreamParserPhases](TestPtyStreamParserPhases.md) (4 shared connections)

## Source Files

- `src/ansible_aom/core/models.py`
- `src/ansible_aom/core/parser.py`
- `tests/unit/test_host_resolution.py`
- `tests/unit/test_models.py`
- `tests/unit/test_parser.py`

## Audit Trail

- EXTRACTED: 317 (58%)
- INFERRED: 234 (42%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*