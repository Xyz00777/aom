# Run History Mining

> 23 nodes · cohesion 0.13

## Key Concepts

- **datetime** (63 connections)
- **PriorRun** (16 connections) — `src/ansible_aom/session/history.py`
- **history.py** (12 connections) — `src/ansible_aom/session/history.py`
- **RunConfigKey** (7 connections) — `src/ansible_aom/core/run_config.py`
- **_iter_completed_sessions()** (7 connections) — `src/ansible_aom/session/history.py`
- **_mine_and_replace()** (7 connections) — `src/ansible_aom/session/history.py`
- **_build_prior()** (6 connections) — `src/ansible_aom/session/history.py`
- **_match_loose()** (6 connections) — `src/ansible_aom/session/history.py`
- **_match_strict()** (6 connections) — `src/ansible_aom/session/history.py`
- **_mine_task_wall()** (5 connections) — `src/ansible_aom/session/history.py`
- **_mine_loop_totals()** (4 connections) — `src/ansible_aom/session/history.py`
- **_parse_iso()** (4 connections) — `src/ansible_aom/session/history.py`
- **test_runtime_role_task_count.py** (4 connections) — `tests/unit/test_runtime_role_task_count.py`
- **Hashable normalization of an ansible-playbook invocation.      Equality semantic** (1 connections) — `src/ansible_aom/core/run_config.py`
- **Pure history lookup: find the most recent prior run matching a config + host cou** (1 connections) — `src/ansible_aom/session/history.py`
- **Yield ``(end_time, meta, session_path)`` for every valid completed session.** (1 connections) — `src/ansible_aom/session/history.py`
- **True when the stored session matches the current invocation exactly.** (1 connections) — `src/ansible_aom/session/history.py`
- **True when the stored session matches the current invocation loosely.      Loose** (1 connections) — `src/ansible_aom/session/history.py`
- **Mine per-task wall and loop totals for *prior*, returning a new PriorRun.** (1 connections) — `src/ansible_aom/session/history.py`
- **Stats from the most recent matching prior session.** (1 connections) — `src/ansible_aom/session/history.py`
- **Mine ``{task.path: {host: item_count}}`` from a session's events.      Scans ``e** (1 connections) — `src/ansible_aom/session/history.py`
- **Mine the per-task wall profile + result segmentation from a session.      Return** (1 connections) — `src/ansible_aom/session/history.py`
- **Regression tests for role_total_tasks counting runtime-only tasks.  When a role** (1 connections) — `tests/unit/test_runtime_role_task_count.py`

## Relationships

- [[Run Config Key Normalization]] (18 shared connections)
- [[Playbook Event Parsing]] (11 shared connections)
- [[Runtime Event Handlers]] (8 shared connections)
- [[Preflight Summary Rendering]] (4 shared connections)
- [[Prior Run Totals Injection]] (4 shared connections)
- [[Duration Formatting Helpers]] (3 shared connections)
- [[Role Group Task Models]] (3 shared connections)
- [[Play Definition Tree Population]] (3 shared connections)
- [[Include Role Discovery]] (2 shared connections)
- [[Inspect Data Model Builders]] (2 shared connections)
- [[Per-Task Overhead Analysis]] (2 shared connections)
- [[Replay CLI Subcommand]] (2 shared connections)

## Source Files

- `src/ansible_aom/core/run_config.py`
- `src/ansible_aom/session/history.py`
- `tests/unit/test_runtime_role_task_count.py`

## Audit Trail

- EXTRACTED: 146 (93%)
- INFERRED: 11 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*