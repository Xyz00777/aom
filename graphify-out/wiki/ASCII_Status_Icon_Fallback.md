# ASCII Status Icon Fallback

> 32 nodes · cohesion 0.12

## Key Concepts

- **render_session()** (17 connections) — `src/ansible_aom/inspect/text.py`
- **text.py** (12 connections) — `src/ansible_aom/inspect/text.py`
- **test_inspect_text_golden.py** (12 connections) — `tests/compact/test_inspect_text_golden.py`
- **_load()** (11 connections) — `tests/compact/test_inspect_text_golden.py`
- **_render_verbose()** (7 connections) — `src/ansible_aom/inspect/text.py`
- **_render_failures()** (6 connections) — `src/ansible_aom/inspect/text.py`
- **_iter_tree()** (5 connections) — `src/ansible_aom/inspect/text.py`
- **_play_name_for_task()** (5 connections) — `src/ansible_aom/inspect/text.py`
- **_render_header()** (5 connections) — `src/ansible_aom/inspect/text.py`
- **_fmt_duration()** (4 connections) — `src/ansible_aom/inspect/text.py`
- **_iter_failed_tasks()** (4 connections) — `src/ansible_aom/inspect/text.py`
- **_render_detail()** (4 connections) — `src/ansible_aom/inspect/text.py`
- **render_session_list()** (4 connections) — `src/ansible_aom/inspect/text.py`
- **_host_counts_line()** (3 connections) — `src/ansible_aom/inspect/text.py`
- **test_render_clean_run_has_header_and_no_failure_block()** (3 connections) — `tests/compact/test_inspect_text_golden.py`
- **test_render_failed_loop_shows_msg_and_failed_items()** (3 connections) — `tests/compact/test_inspect_text_golden.py`
- **test_render_includes_verbose_section_when_stderr_lines_exist()** (3 connections) — `tests/compact/test_inspect_text_golden.py`
- **test_render_no_verbose_section_when_no_stderr_events()** (3 connections) — `tests/compact/test_inspect_text_golden.py`
- **test_render_running_shows_running_status()** (3 connections) — `tests/compact/test_inspect_text_golden.py`
- **test_render_unreachable_shows_connection_msg()** (3 connections) — `tests/compact/test_inspect_text_golden.py`
- **test_render_verbose_not_gated_on_failed_status()** (3 connections) — `tests/compact/test_inspect_text_golden.py`
- **test_render_verbose_play_scoping()** (3 connections) — `tests/compact/test_inspect_text_golden.py`
- **test_render_verbose_task_scoping()** (3 connections) — `tests/compact/test_inspect_text_golden.py`
- **RunSummary** (2 connections)
- **Plain-text rendering of an inspect session.  Used by ``aom inspect --text`` (and** (1 connections) — `src/ansible_aom/inspect/text.py`
- *... and 7 more nodes in this community*

## Relationships

- [Playbook Parser Integration Tests](Playbook_Parser_Integration_Tests.md) (5 shared connections)
- [PTY Buffer Stall Handling](PTY_Buffer_Stall_Handling.md) (4 shared connections)
- [Data Model Unit Tests](Data_Model_Unit_Tests.md) (1 shared connections)
- [Status Bar Widget](Status_Bar_Widget.md) (1 shared connections)
- [Log Filter Helpers](Log_Filter_Helpers.md) (1 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (1 shared connections)
- [RunSummary Schema Contract](RunSummary_Schema_Contract.md) (1 shared connections)

## Source Files

- `src/ansible_aom/inspect/text.py`
- `tests/compact/test_inspect_text_golden.py`

## Audit Trail

- EXTRACTED: 111 (82%)
- INFERRED: 25 (18%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*