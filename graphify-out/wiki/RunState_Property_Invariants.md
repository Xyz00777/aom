# RunState Property Invariants

> 22 nodes · cohesion 0.26

## Key Concepts

- **format_host_rows()** (26 connections) — `src/ansible_aom/compact/format.py`
- **_strip_sgr()** (16 connections) — `src/ansible_aom/compact/format.py`
- **test_host_table.py** (15 connections) — `tests/compact/test_host_table.py`
- **_state()** (14 connections) — `tests/compact/test_host_table.py`
- **_add_results()** (13 connections) — `tests/compact/test_host_table.py`
- **test_failed_host_shows_failed_task_in_suffix()** (8 connections) — `tests/compact/test_host_table.py`
- **test_failed_host_shows_X_in_ascii_mode()** (8 connections) — `tests/compact/test_host_table.py`
- **test_running_host_shows_current_task()** (8 connections) — `tests/compact/test_host_table.py`
- **test_unreachable_host_shows_unreachable_task_in_suffix()** (8 connections) — `tests/compact/test_host_table.py`
- **test_columns_align_across_rows()** (6 connections) — `tests/compact/test_host_table.py`
- **test_header_row_present()** (6 connections) — `tests/compact/test_host_table.py`
- **test_idle_host_shows_idle_marker()** (6 connections) — `tests/compact/test_host_table.py`
- **test_skipped_column_hidden_when_no_skipped()** (6 connections) — `tests/compact/test_host_table.py`
- **test_skipped_column_visible_when_any_host_has_skipped()** (6 connections) — `tests/compact/test_host_table.py`
- **test_unreachable_column_hidden_when_no_unreachable()** (6 connections) — `tests/compact/test_host_table.py`
- **test_unreachable_column_visible_when_any_host_has_unreachable()** (6 connections) — `tests/compact/test_host_table.py`
- **_rows()** (3 connections) — `tests/compact/test_host_table.py`
- **Render the per-host overview as a column-aligned table.      Header row + one ro** (1 connections) — `src/ansible_aom/compact/format.py`
- **Strip SGR escapes so visible-length comparisons are accurate.** (1 connections) — `src/ansible_aom/compact/format.py`
- **Per-host overview renders as a column-aligned table rather than a flat row of co** (1 connections) — `tests/compact/test_host_table.py`
- **Synthesise OK/CHANGED/SKIPPED/FAILED/UNREACHABLE results for a host.** (1 connections) — `tests/compact/test_host_table.py`
- **Split rows on whitespace runs after stripping SGR — coarse but     enough to ass** (1 connections) — `tests/compact/test_host_table.py`

## Relationships

- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (15 shared connections)
- [CLI Interface Tests](CLI_Interface_Tests.md) (11 shared connections)
- [Four-Layer Redaction System](Four-Layer_Redaction_System.md) (6 shared connections)
- [Renderer Set Definitions](Renderer_Set_Definitions.md) (4 shared connections)
- [Status Bar Warning Panels](Status_Bar_Warning_Panels.md) (2 shared connections)
- [Community 642](Community_642.md) (1 shared connections)
- [Crash Recovery Notification](Crash_Recovery_Notification.md) (1 shared connections)
- [Hide State Gating Tests](Hide_State_Gating_Tests.md) (1 shared connections)
- [Community 560](Community_560.md) (1 shared connections)
- [Pause Prompt Heuristic](Pause_Prompt_Heuristic.md) (1 shared connections)
- [CLI Argument Parser](CLI_Argument_Parser.md) (1 shared connections)

## Source Files

- `src/ansible_aom/compact/format.py`
- `tests/compact/test_host_table.py`

## Audit Trail

- EXTRACTED: 96 (58%)
- INFERRED: 70 (42%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*