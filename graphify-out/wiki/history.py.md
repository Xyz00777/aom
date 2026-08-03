# history.py

> 23 nodes · cohesion 0.16

## Key Concepts

- **history.py** (31 connections) — `src/ansible_aom/session/history.py`
- **run_config.py** (12 connections) — `src/ansible_aom/core/run_config.py`
- **RunConfigKey** (9 connections) — `src/ansible_aom/core/run_config.py`
- **_iter_completed_sessions()** (7 connections) — `src/ansible_aom/session/history.py`
- **_mine_and_replace()** (7 connections) — `src/ansible_aom/session/history.py`
- **Path** (7 connections)
- **_build_prior()** (6 connections) — `src/ansible_aom/session/history.py`
- **_match_loose()** (6 connections) — `src/ansible_aom/session/history.py`
- **_match_strict()** (6 connections) — `src/ansible_aom/session/history.py`
- **_mine_task_wall()** (5 connections) — `src/ansible_aom/session/history.py`
- **_parse_iso()** (5 connections) — `src/ansible_aom/session/history.py`
- **_mine_loop_totals()** (4 connections) — `src/ansible_aom/session/history.py`
- **Any** (4 connections)
- **datetime** (4 connections)
- **Pure normalization of an ansible-playbook invocation into a hashable key.  The :** (1 connections) — `src/ansible_aom/core/run_config.py`
- **Hashable normalization of an ansible-playbook invocation.      Equality semantic** (1 connections) — `src/ansible_aom/core/run_config.py`
- **Pure history lookup: find the most recent prior run matching a config + host cou** (1 connections) — `src/ansible_aom/session/history.py`
- **Mine the per-task wall profile + result segmentation from a session.      Return** (1 connections) — `src/ansible_aom/session/history.py`
- **Yield ``(end_time, meta, session_path)`` for every valid completed session.** (1 connections) — `src/ansible_aom/session/history.py`
- **True when the stored session matches the current invocation exactly.** (1 connections) — `src/ansible_aom/session/history.py`
- **True when the stored session matches the current invocation loosely.      Loose** (1 connections) — `src/ansible_aom/session/history.py`
- **Mine per-task wall and loop totals for *prior*, returning a new PriorRun.** (1 connections) — `src/ansible_aom/session/history.py`
- **Mine ``{task.path: {host: item_count}}`` from a session's events.      Scans ``e** (1 connections) — `src/ansible_aom/session/history.py`

## Relationships

- [find_previous_run](find_previous_run.md) (10 shared connections)
- [build_run_config_key](build_run_config_key.md) (7 shared connections)
- [PriorRun](PriorRun.md) (6 shared connections)
- [json.py](json.py.md) (5 shared connections)
- [run_playbook](run_playbook.md) (2 shared connections)
- [test_history_roundtrip.py](test_history_roundtrip.py.md) (2 shared connections)
- [test_history_loop_totals.py](test_history_loop_totals.py.md) (2 shared connections)
- [Run Diagnostics Accumulator](Run_Diagnostics_Accumulator.md) (2 shared connections)
- [Terminal Size Check](Terminal_Size_Check.md) (2 shared connections)
- [renderer.py](renderer.py.md) (2 shared connections)
- [Shift Modifier Keybindings](Shift_Modifier_Keybindings.md) (1 shared connections)
- [CompactRenderer](CompactRenderer.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/run_config.py`
- `src/ansible_aom/session/history.py`

## Audit Trail

- EXTRACTED: 120 (98%)
- INFERRED: 2 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*