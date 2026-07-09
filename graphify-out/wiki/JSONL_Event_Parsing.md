# JSONL Event Parsing

> 15 nodes · cohesion 0.18

## Key Concepts

- **_build_compact_renderer()** (9 connections) — `tests/unit/test_renderer_unbounded_caps.py`
- **test_renderer_unbounded_caps.py** (7 connections) — `tests/unit/test_renderer_unbounded_caps.py`
- **test_announced_task_uuids_capped()** (3 connections) — `tests/unit/test_renderer_unbounded_caps.py`
- **test_completed_task_ids_capped()** (3 connections) — `tests/unit/test_renderer_unbounded_caps.py`
- **test_renderer_constructor_uses_sane_initial_caps()** (3 connections) — `tests/unit/test_renderer_unbounded_caps.py`
- **test_seen_warning_messages_capped()** (3 connections) — `tests/unit/test_renderer_unbounded_caps.py`
- **test_streamed_loop_items_capped()** (3 connections) — `tests/unit/test_renderer_unbounded_caps.py`
- **Any** (1 connections)
- **R14 — cap unbounded CompactRenderer sets.  R14 spec: the compact renderer carrie** (1 connections) — `tests/unit/test_renderer_unbounded_caps.py`
- **Construct a CompactRenderer with mocks for its dependencies.      The renderer's** (1 connections) — `tests/unit/test_renderer_unbounded_caps.py`
- **R14: ``_streamed_loop_items`` is bounded at 10 000 entries.** (1 connections) — `tests/unit/test_renderer_unbounded_caps.py`
- **R14: ``_announced_task_uuids`` is bounded at MAX_TASKS_PER_PLAY.** (1 connections) — `tests/unit/test_renderer_unbounded_caps.py`
- **R14: ``_completed_task_ids`` is bounded at MAX_TASKS_PER_PLAY.** (1 connections) — `tests/unit/test_renderer_unbounded_caps.py`
- **R14: ``_seen_warning_messages`` is bounded at 5 000 entries.** (1 connections) — `tests/unit/test_renderer_unbounded_caps.py`
- **R14: the initial empty sets have the same cap semantics — fresh     renderers mu** (1 connections) — `tests/unit/test_renderer_unbounded_caps.py`

## Relationships

- [App Configuration Settings](App_Configuration_Settings.md) (1 shared connections)

## Source Files

- `tests/unit/test_renderer_unbounded_caps.py`

## Audit Trail

- EXTRACTED: 38 (97%)
- INFERRED: 1 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*