# Inspect Text Golden Tests

> 18 nodes · cohesion 0.17

## Key Concepts

- **render_session()** (20 connections) — `src/ansible_aom/inspect/text.py`
- **text.py** (12 connections) — `src/ansible_aom/inspect/text.py`
- **test_inspect_text_golden.py** (11 connections) — `tests/compact/test_inspect_text_golden.py`
- **_load()** (10 connections) — `tests/compact/test_inspect_text_golden.py`
- **_render_failures()** (6 connections) — `src/ansible_aom/inspect/text.py`
- **_render_header()** (5 connections) — `src/ansible_aom/inspect/text.py`
- **_fmt_duration()** (4 connections) — `src/ansible_aom/inspect/text.py`
- **_iter_failed_tasks()** (4 connections) — `src/ansible_aom/inspect/text.py`
- **_render_detail()** (4 connections) — `src/ansible_aom/inspect/text.py`
- **render_session_list()** (4 connections) — `src/ansible_aom/inspect/text.py`
- **test_render_clean_run_has_header_and_no_failure_block()** (3 connections) — `tests/compact/test_inspect_text_golden.py`
- **test_render_failed_loop_shows_msg_and_failed_items()** (3 connections) — `tests/compact/test_inspect_text_golden.py`
- **test_render_running_shows_running_status()** (3 connections) — `tests/compact/test_inspect_text_golden.py`
- **test_render_unreachable_shows_connection_msg()** (3 connections) — `tests/compact/test_inspect_text_golden.py`
- **_host_counts_line()** (3 connections) — `src/ansible_aom/inspect/text.py`
- **Golden-frame tests for the text-mode inspect renderer.** (1 connections) — `tests/compact/test_inspect_text_golden.py`
- **Plain-text rendering of an inspect session.  Used by ``aom inspect --text`` (and** (1 connections) — `src/ansible_aom/inspect/text.py`
- **Render the verbose/stderr section from ``aom_stderr_line`` events.      Uses ``b** (1 connections) — `src/ansible_aom/inspect/text.py`

## Relationships

- [[Inspect Data Model Builders]] (5 shared connections)
- [[Task Tree Navigation]] (2 shared connections)
- [[Design Specs Plans]] (2 shared connections)
- [[Inspect TUI Widget Data]] (1 shared connections)
- [[Inspect CLI Commands]] (1 shared connections)

## Source Files

- `src/ansible_aom/inspect/text.py`
- `tests/compact/test_inspect_text_golden.py`

## Audit Trail

- EXTRACTED: 83 (85%)
- INFERRED: 15 (15%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*