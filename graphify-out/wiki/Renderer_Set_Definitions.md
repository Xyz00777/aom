# Renderer Set Definitions

> 16 nodes · cohesion 0.16

## Key Concepts

- **test_renderer_set_definitions.py** (9 connections) — `tests/compact/test_renderer_set_definitions.py`
- **_build_definitions()** (7 connections) — `tests/compact/test_renderer_set_definitions.py`
- **test_set_definitions_called_before_start_is_safe()** (4 connections) — `tests/compact/test_renderer_set_definitions.py`
- **test_set_definitions_prints_summary_above_status_panel()** (4 connections) — `tests/compact/test_renderer_set_definitions.py`
- **test_set_definitions_unions_hosts_across_plays()** (4 connections) — `tests/compact/test_renderer_set_definitions.py`
- **test_set_definitions_updates_initial_hosts_total_in_status_bar()** (4 connections) — `tests/compact/test_renderer_set_definitions.py`
- **test_set_definitions_stores_definitions_on_renderer()** (3 connections) — `tests/compact/test_renderer_set_definitions.py`
- **test_set_definitions_with_empty_list_emits_no_summary()** (3 connections) — `tests/compact/test_renderer_set_definitions.py`
- **test_set_definitions_with_empty_list_keeps_zero_hosts()** (3 connections) — `tests/compact/test_renderer_set_definitions.py`
- **Tests for CompactRenderer.set_definitions (preflight result wiring).** (1 connections) — `tests/compact/test_renderer_set_definitions.py`
- **Hosts that appear in multiple plays count once each.** (1 connections) — `tests/compact/test_renderer_set_definitions.py`
- **After preflight, the status bar should show total resolved hosts immediately.** (1 connections) — `tests/compact/test_renderer_set_definitions.py`
- **Defensive: calling set_definitions before start should not crash.** (1 connections) — `tests/compact/test_renderer_set_definitions.py`
- **Preflight failure path: empty definitions should not crash and leaves hosts at 0** (1 connections) — `tests/compact/test_renderer_set_definitions.py`
- **The startup summary lands above the status panel via print_log.** (1 connections) — `tests/compact/test_renderer_set_definitions.py`
- **Empty preflight result should not print a stray header.** (1 connections) — `tests/compact/test_renderer_set_definitions.py`

## Relationships

- [[Compact Renderer Implementation]] (7 shared connections)
- [[Play Definition Tree Population]] (2 shared connections)
- [[Task Definition Live Refresh]] (1 shared connections)

## Source Files

- `tests/compact/test_renderer_set_definitions.py`

## Audit Trail

- EXTRACTED: 40 (83%)
- INFERRED: 8 (17%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*