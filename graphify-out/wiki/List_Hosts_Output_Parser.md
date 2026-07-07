# List Hosts Output Parser

> 23 nodes · cohesion 0.05

## Key Concepts

- **parse_list_hosts_output()** (27 connections) — `src/ansible_aom/core/parser.py`
- **.test_list_hosts_no_duplicate_hosts()** (4 connections) — `tests/unit/test_parser.py`
- **.test_list_hosts_stderr_not_in_result()** (4 connections) — `tests/unit/test_parser.py`
- **.test_parallel_parse_does_not_corrupt_data()** (4 connections) — `tests/unit/test_parser.py`
- **.test_list_hosts_all_inventory()** (3 connections) — `tests/unit/test_parser.py`
- **.test_list_hosts_dynamic_inventory_timeout()** (3 connections) — `tests/unit/test_parser.py`
- **.test_list_hosts_dynamic_pattern_empty_hosts()** (3 connections) — `tests/unit/test_parser.py`
- **.test_list_hosts_dynamic_pattern_fallback()** (3 connections) — `tests/unit/test_parser.py`
- **.test_list_hosts_multiple_plays_hosts()** (3 connections) — `tests/unit/test_parser.py`
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
- **TC-101: Multiple plays with different host sets.** (2 connections) — `tests/unit/test_parser.py`
- **TC-116: Play names may contain special section designations.** (2 connections) — `tests/unit/test_parser.py`

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

- EXTRACTED: 48 (51%)
- INFERRED: 46 (49%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*