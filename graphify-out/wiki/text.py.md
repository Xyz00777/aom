# text.py

> 43 nodes · cohesion 0.10

## Key Concepts

- **text.py** (36 connections) — `src/ansible_aom/inspect/text.py`
- **DetailBlock** (18 connections) — `src/ansible_aom/core/inspect_model.py`
- **render_session()** (18 connections) — `src/ansible_aom/inspect/text.py`
- **render_session_from_index()** (14 connections) — `src/ansible_aom/inspect/text.py`
- **test_inspect_text_golden.py** (13 connections) — `tests/compact/test_inspect_text_golden.py`
- **_render_verbose()** (11 connections) — `src/ansible_aom/inspect/text.py`
- **_load()** (11 connections) — `tests/compact/test_inspect_text_golden.py`
- **_render_failures_from_index()** (8 connections) — `src/ansible_aom/inspect/text.py`
- **_resolve_verbose_scope()** (7 connections) — `src/ansible_aom/inspect/text.py`
- **_hydrate_node()** (6 connections) — `src/ansible_aom/inspect/text.py`
- **_iter_tree()** (6 connections) — `src/ansible_aom/inspect/text.py`
- **_play_name_for_task()** (6 connections) — `src/ansible_aom/inspect/text.py`
- **_render_failures()** (6 connections) — `src/ansible_aom/inspect/text.py`
- **_render_header()** (6 connections) — `src/ansible_aom/inspect/text.py`
- **_iter_failed_tasks()** (5 connections) — `src/ansible_aom/inspect/text.py`
- **_render_detail()** (5 connections) — `src/ansible_aom/inspect/text.py`
- **_fmt_duration()** (4 connections) — `src/ansible_aom/inspect/text.py`
- **render_session_list()** (4 connections) — `src/ansible_aom/inspect/text.py`
- **_host_counts_line()** (3 connections) — `src/ansible_aom/inspect/text.py`
- **Path** (3 connections)
- **_verbose_section()** (3 connections) — `src/ansible_aom/inspect/text.py`
- **test_render_clean_run_has_header_and_no_failure_block()** (3 connections) — `tests/compact/test_inspect_text_golden.py`
- **test_render_failed_loop_shows_msg_and_failed_items()** (3 connections) — `tests/compact/test_inspect_text_golden.py`
- **test_render_includes_verbose_section_when_stderr_lines_exist()** (3 connections) — `tests/compact/test_inspect_text_golden.py`
- **test_render_no_verbose_section_when_no_stderr_events()** (3 connections) — `tests/compact/test_inspect_text_golden.py`
- *... and 18 more nodes in this community*

## Relationships

- [StatusCounts](StatusCounts.md) (12 shared connections)
- [TaskTreeNode](TaskTreeNode.md) (11 shared connections)
- [inspect_model.py](inspect_model.py.md) (8 shared connections)
- [inspect.py](inspect.py.md) (8 shared connections)
- [index.py](index.py.md) (7 shared connections)
- [build_verbose_lines](build_verbose_lines.md) (6 shared connections)
- [load_session](load_session.md) (5 shared connections)
- [InspectApp](InspectApp.md) (1 shared connections)
- [json.py](json.py.md) (1 shared connections)
- [RunSummary Schema Contract](RunSummary_Schema_Contract.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/inspect_model.py`
- `src/ansible_aom/inspect/text.py`
- `tests/compact/test_inspect_text_golden.py`

## Audit Trail

- EXTRACTED: 222 (95%)
- INFERRED: 12 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*