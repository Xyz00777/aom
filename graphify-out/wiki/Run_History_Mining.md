# Run History Mining

> 15 nodes · cohesion 0.13

## Key Concepts

- **PriorRun** (17 connections) — `src/ansible_aom/session/history.py`
- **history.py** (11 connections) — `src/ansible_aom/session/history.py`
- **_iter_completed_sessions()** (9 connections) — `src/ansible_aom/session/history.py`
- **_build_prior()** (8 connections) — `src/ansible_aom/session/history.py`
- **_match_loose()** (8 connections) — `src/ansible_aom/session/history.py`
- **_mine_and_replace()** (8 connections) — `src/ansible_aom/session/history.py`
- **RunConfigKey** (7 connections) — `src/ansible_aom/core/run_config.py`
- **_match_strict()** (7 connections) — `src/ansible_aom/session/history.py`
- **_mine_task_wall()** (6 connections) — `src/ansible_aom/session/history.py`
- **_mine_loop_totals()** (5 connections) — `src/ansible_aom/session/history.py`
- **_parse_iso()** (5 connections) — `src/ansible_aom/session/history.py`
- **test_runtime_role_task_count.py** (3 connections) — `tests/unit/test_runtime_role_task_count.py`
- **Hashable normalization of an ansible-playbook invocation.      Equality semantic** (1 connections) — `src/ansible_aom/core/run_config.py`
- **Pure history lookup: find the most recent prior run matching a config + host cou** (1 connections) — `src/ansible_aom/session/history.py`
- **Regression tests for role_total_tasks counting runtime-only tasks.  When a role** (1 connections) — `tests/unit/test_runtime_role_task_count.py`

## Relationships

- [[Run Config Key Normalization]] (17 shared connections)
- [[Playbook Event Parsing]] (4 shared connections)
- [[Preflight Summary Rendering]] (3 shared connections)
- [[Prior Run Totals Injection]] (3 shared connections)
- [[Renderer ETA Wiring]] (2 shared connections)
- [[Play Definition Tree Population]] (2 shared connections)
- [[Compact Renderer Implementation]] (1 shared connections)
- [[Renderer Event Protocol]] (1 shared connections)

## Source Files

- `src/ansible_aom/core/run_config.py`
- `src/ansible_aom/session/history.py`
- `tests/unit/test_runtime_role_task_count.py`

## Audit Trail

- EXTRACTED: 84 (87%)
- INFERRED: 13 (13%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*