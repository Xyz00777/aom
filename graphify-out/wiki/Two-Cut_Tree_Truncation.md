# Two-Cut Tree Truncation

> 14 nodes · cohesion 0.33

## Key Concepts

- **render_session()** (18 connections) — `src/ansible_aom/inspect/text.py`
- **test_inspect_text_golden.py** (13 connections) — `tests/compact/test_inspect_text_golden.py`
- **_load()** (11 connections) — `tests/compact/test_inspect_text_golden.py`
- **test_render_clean_run_has_header_and_no_failure_block()** (3 connections) — `tests/compact/test_inspect_text_golden.py`
- **test_render_failed_loop_shows_msg_and_failed_items()** (3 connections) — `tests/compact/test_inspect_text_golden.py`
- **test_render_includes_verbose_section_when_stderr_lines_exist()** (3 connections) — `tests/compact/test_inspect_text_golden.py`
- **test_render_no_verbose_section_when_no_stderr_events()** (3 connections) — `tests/compact/test_inspect_text_golden.py`
- **test_render_running_shows_running_status()** (3 connections) — `tests/compact/test_inspect_text_golden.py`
- **test_render_unreachable_shows_connection_msg()** (3 connections) — `tests/compact/test_inspect_text_golden.py`
- **test_render_verbose_not_gated_on_failed_status()** (3 connections) — `tests/compact/test_inspect_text_golden.py`
- **test_render_verbose_play_scoping()** (3 connections) — `tests/compact/test_inspect_text_golden.py`
- **test_render_verbose_task_scoping()** (3 connections) — `tests/compact/test_inspect_text_golden.py`
- **Render a session dict as plain text. ANSI-free, deterministic.      When ``play_** (1 connections) — `src/ansible_aom/inspect/text.py`
- **Golden-frame tests for the text-mode inspect renderer.** (1 connections) — `tests/compact/test_inspect_text_golden.py`

## Relationships

- [ASCII Status Icon Fallback](ASCII_Status_Icon_Fallback.md) (5 shared connections)
- [Playbook Parser Integration Tests](Playbook_Parser_Integration_Tests.md) (2 shared connections)
- [Status Bar Widget](Status_Bar_Widget.md) (2 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (1 shared connections)
- [RunSummary Schema Contract](RunSummary_Schema_Contract.md) (1 shared connections)

## Source Files

- `src/ansible_aom/inspect/text.py`
- `tests/compact/test_inspect_text_golden.py`

## Audit Trail

- EXTRACTED: 49 (69%)
- INFERRED: 22 (31%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*