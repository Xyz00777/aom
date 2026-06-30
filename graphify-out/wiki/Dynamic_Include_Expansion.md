# Dynamic Include Expansion

> 30 nodes · cohesion 0.11

## Key Concepts

- **TestDynamicExpansion** (14 connections) — `tests/unit/test_dynamic_expansion.py`
- **_play_start()** (11 connections) — `tests/unit/test_dynamic_expansion.py`
- **.test_runtime_cache_reuses_preflight_entry()** (10 connections) — `tests/unit/test_dynamic_expansion.py`
- **.test_task_path_populates_include_cache()** (9 connections) — `tests/unit/test_dynamic_expansion.py`
- **_task_start()** (8 connections) — `tests/unit/test_dynamic_expansion.py`
- **.test_repeated_task_uuid_does_not_re_graft()** (8 connections) — `tests/unit/test_dynamic_expansion.py`
- **TestRuntimeIncludeDiscovery** (8 connections) — `tests/unit/test_dynamic_expansion.py`
- **test_dynamic_expansion.py** (7 connections) — `tests/unit/test_dynamic_expansion.py`
- **.test_dynamic_task_inherits_parent_play_fields()** (7 connections) — `tests/unit/test_dynamic_expansion.py`
- **.test_grafting_works_under_v2_runner_on_start()** (7 connections) — `tests/unit/test_dynamic_expansion.py`
- **.test_multiple_unknown_tasks_accumulate_under_same_parent()** (7 connections) — `tests/unit/test_dynamic_expansion.py`
- **.test_orphan_dynamic_task_when_no_parent_seen_yet()** (7 connections) — `tests/unit/test_dynamic_expansion.py`
- **.test_static_task_following_dynamic_resets_parent()** (7 connections) — `tests/unit/test_dynamic_expansion.py`
- **.test_unknown_task_grafted_as_child_of_last_matched_task()** (7 connections) — `tests/unit/test_dynamic_expansion.py`
- **.test_no_grafting_without_definitions()** (5 connections) — `tests/unit/test_dynamic_expansion.py`
- **_runner_start()** (3 connections) — `tests/unit/test_dynamic_expansion.py`
- **_task_start_with_path()** (3 connections) — `tests/unit/test_dynamic_expansion.py`
- **Unit tests for include_tasks dynamic expansion.  TC-094 / TC-095 from TEST_SPECI** (1 connections) — `tests/unit/test_dynamic_expansion.py`
- **Dynamic TaskDefinition copies play_id and play_order from the parent.** (1 connections) — `tests/unit/test_dynamic_expansion.py`
- **TC-094: Several dynamic tasks under the same include_tasks parent.** (1 connections) — `tests/unit/test_dynamic_expansion.py`
- **A second v2_runner_on_start for the same UUID must not graft twice.** (1 connections) — `tests/unit/test_dynamic_expansion.py`
- **A subsequent matched preflight task replaces the parent cursor.** (1 connections) — `tests/unit/test_dynamic_expansion.py`
- **Unknown task before any preflight match is left orphan (no graft, no crash).** (1 connections) — `tests/unit/test_dynamic_expansion.py`
- **Free-strategy plays emit v2_runner_on_start instead of task_start.          The** (1 connections) — `tests/unit/test_dynamic_expansion.py`
- **With no preflight definitions there's no parent to graft under.** (1 connections) — `tests/unit/test_dynamic_expansion.py`
- *... and 5 more nodes in this community*

## Relationships

- [[Run State Summary Panel]] (12 shared connections)
- [[Task Definition Live Refresh]] (11 shared connections)
- [[Play Definition Tree Population]] (11 shared connections)
- [[Include Role Discovery]] (3 shared connections)
- [[Run Config Key Normalization]] (2 shared connections)

## Source Files

- `tests/unit/test_dynamic_expansion.py`

## Audit Trail

- EXTRACTED: 104 (74%)
- INFERRED: 37 (26%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*