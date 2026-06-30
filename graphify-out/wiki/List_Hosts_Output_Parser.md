# List Hosts Output Parser

> 42 nodes · cohesion 0.05

## Key Concepts

- **parse_list_hosts_output()** (25 connections) — `src/ansible_aom/core/parser.py`
- **.test_parallel_parse_does_not_corrupt_data()** (4 connections) — `tests/unit/test_parser.py`
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
- **.test_list_hosts_stderr_not_in_result()** (3 connections) — `tests/unit/test_parser.py`
- **Parse --list-hosts output into structured data.      Returns list of dicts with** (2 connections) — `src/ansible_aom/core/parser.py`
- **TC-087: Parallel parsing produces same results as sequential.** (1 connections) — `tests/unit/test_parser.py`
- **TC-089: When --list-hosts returns empty, hosts will come from         runner eve** (1 connections) — `tests/unit/test_parser.py`
- **TC-089: Partial/corrupted output still returns any parseable plays.** (1 connections) — `tests/unit/test_parser.py`
- *... and 17 more nodes in this community*

## Relationships

- [[Role Group Task Models]] (21 shared connections)
- [[List Tasks Output Parser]] (2 shared connections)
- [[Parallel Pre-flight Runner]] (1 shared connections)
- [[PreParseResult Assembly]] (1 shared connections)
- [[Preflight Definition Assembly]] (1 shared connections)

## Source Files

- `src/ansible_aom/core/parser.py`
- `tests/unit/test_parser.py`

## Audit Trail

- EXTRACTED: 64 (59%)
- INFERRED: 44 (41%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*