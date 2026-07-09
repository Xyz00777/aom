# Diagnostics and Profiler

> 46 nodes · cohesion 0.06

## Key Concepts

- **parse_list_hosts_output()** (27 connections) — `src/ansible_aom/core/parser.py`
- **TestListHostsEdgeCases** (23 connections) — `tests/unit/test_parser.py`
- **TestListHostsParser** (20 connections) — `tests/unit/test_parser.py`
- **TestListHostsFallback** (17 connections) — `tests/unit/test_parser.py`
- **.test_list_hosts_output_populates_resolved_hosts()** (3 connections) — `tests/unit/test_host_resolution.py`
- **.test_list_hosts_all_inventory()** (3 connections) — `tests/unit/test_parser.py`
- **.test_list_hosts_dynamic_inventory_timeout()** (3 connections) — `tests/unit/test_parser.py`
- **.test_list_hosts_dynamic_pattern_empty_hosts()** (3 connections) — `tests/unit/test_parser.py`
- **.test_list_hosts_dynamic_pattern_fallback()** (3 connections) — `tests/unit/test_parser.py`
- **.test_list_hosts_multiple_plays_hosts()** (3 connections) — `tests/unit/test_parser.py`
- **.test_list_hosts_no_duplicate_hosts()** (3 connections) — `tests/unit/test_parser.py`
- **.test_list_hosts_pattern_filtering()** (3 connections) — `tests/unit/test_parser.py`
- **.test_list_hosts_play_number_sequential()** (3 connections) — `tests/unit/test_parser.py`
- **.test_list_hosts_with_limit()** (3 connections) — `tests/unit/test_parser.py`
- **.test_list_hosts_empty_result_fallback()** (3 connections) — `tests/unit/test_parser.py`
- **.test_list_hosts_fallback_warning_logged()** (3 connections) — `tests/unit/test_parser.py`
- **.test_list_hosts_partial_error_output()** (3 connections) — `tests/unit/test_parser.py`
- **.test_empty_output_returns_empty_list()** (3 connections) — `tests/unit/test_parser.py`
- **.test_localhost_handling()** (3 connections) — `tests/unit/test_parser.py`
- **.test_parse_hostname_extraction()** (3 connections) — `tests/unit/test_parser.py`
- **.test_parse_play_line_pattern()** (3 connections) — `tests/unit/test_parser.py`
- **.test_playbook_header_skipped()** (3 connections) — `tests/unit/test_parser.py`
- **.test_skip_non_host_lines()** (3 connections) — `tests/unit/test_parser.py`
- **Parse --list-hosts output into structured data.      Returns list of dicts with** (1 connections) — `src/ansible_aom/core/parser.py`
- **TC-149: parse_list_hosts_output extracts hostnames per play.** (1 connections) — `tests/unit/test_host_resolution.py`
- *... and 21 more nodes in this community*

## Relationships

- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (9 shared connections)
- [Secret Redaction Configuration](Secret_Redaction_Configuration.md) (8 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (4 shared connections)
- [State Machine Module](State_Machine_Module.md) (3 shared connections)
- [Compact Renderer Integration Tests](Compact_Renderer_Integration_Tests.md) (3 shared connections)
- [Task Definition Live Refresh](Task_Definition_Live_Refresh.md) (3 shared connections)
- [Compact Renderer Implementation](Compact_Renderer_Implementation.md) (3 shared connections)
- [Per-Task Overhead Analysis](Per-Task_Overhead_Analysis.md) (3 shared connections)
- [CLI Argument Parser](CLI_Argument_Parser.md) (3 shared connections)
- [Three-Pane Inspect App](Three-Pane_Inspect_App.md) (3 shared connections)
- [Run State Completion Recap](Run_State_Completion_Recap.md) (3 shared connections)
- [List Hosts Output Parser](List_Hosts_Output_Parser.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/parser.py`
- `tests/unit/test_host_resolution.py`
- `tests/unit/test_parser.py`

## Audit Trail

- EXTRACTED: 87 (52%)
- INFERRED: 80 (48%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*