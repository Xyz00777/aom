# Status Bar Rerender

> 16 nodes · cohesion 0.12

## Key Concepts

- **.format_status_bar()** (9 connections) — `tests/integration/test_compact_renderer.py`
- **.test_sigwinch_triggers_rerender()** (4 connections) — `tests/integration/test_compact_renderer.py`
- **.test_elapsed_time_format_over_one_hour()** (3 connections) — `tests/integration/test_compact_renderer.py`
- **.test_elapsed_time_format_under_one_minute()** (3 connections) — `tests/integration/test_compact_renderer.py`
- **.test_status_bar_format_basic()** (3 connections) — `tests/integration/test_compact_renderer.py`
- **.test_status_bar_with_both_warnings_and_deprecations()** (3 connections) — `tests/integration/test_compact_renderer.py`
- **.test_status_bar_with_deprecations()** (3 connections) — `tests/integration/test_compact_renderer.py`
- **.test_status_bar_with_warnings()** (3 connections) — `tests/integration/test_compact_renderer.py`
- **TC-051: SIGWINCH triggers re-render of the status panel.** (1 connections) — `tests/integration/test_compact_renderer.py`
- **Format status bar: playbook | X/Y hosts | ⚠ N ✱ N | elapsed.** (1 connections) — `tests/integration/test_compact_renderer.py`
- **TC-031: Status bar shows playbook, hosts, time.** (1 connections) — `tests/integration/test_compact_renderer.py`
- **TC-031: Status bar shows warning count.** (1 connections) — `tests/integration/test_compact_renderer.py`
- **TC-031: Status bar shows deprecation count.** (1 connections) — `tests/integration/test_compact_renderer.py`
- **TC-031: Status bar shows both warnings and deprecations.** (1 connections) — `tests/integration/test_compact_renderer.py`
- **TC-031: Elapsed time formats correctly under 1 minute.** (1 connections) — `tests/integration/test_compact_renderer.py`
- **TC-031: Elapsed time formats correctly over 1 hour.** (1 connections) — `tests/integration/test_compact_renderer.py`

## Relationships

- [[Compact Renderer Integration Tests]] (8 shared connections)
- [[Compact Renderer Implementation]] (1 shared connections)

## Source Files

- `tests/integration/test_compact_renderer.py`

## Audit Trail

- EXTRACTED: 38 (97%)
- INFERRED: 1 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*