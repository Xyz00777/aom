# Property Based Tests

> 19 nodes · cohesion 0.19

## Key Concepts

- **history.py** (31 connections) — `src/ansible_aom/session/history.py`
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
- **Pure history lookup: find the most recent prior run matching a config + host cou** (1 connections) — `src/ansible_aom/session/history.py`
- **Mine the per-task wall profile + result segmentation from a session.      Return** (1 connections) — `src/ansible_aom/session/history.py`
- **Yield ``(end_time, meta, session_path)`` for every valid completed session.** (1 connections) — `src/ansible_aom/session/history.py`
- **True when the stored session matches the current invocation exactly.** (1 connections) — `src/ansible_aom/session/history.py`
- **True when the stored session matches the current invocation loosely.      Loose** (1 connections) — `src/ansible_aom/session/history.py`
- **Mine per-task wall and loop totals for *prior*, returning a new PriorRun.** (1 connections) — `src/ansible_aom/session/history.py`
- **Mine ``{task.path: {host: item_count}}`` from a session's events.      Scans ``e** (1 connections) — `src/ansible_aom/session/history.py`

## Relationships

- [JSON Renderer](JSON_Renderer.md) (14 shared connections)
- [TUI Keybindings Config](TUI_Keybindings_Config.md) (6 shared connections)
- [StatusBarConfig Model](StatusBarConfig_Model.md) (3 shared connections)
- [Tree Block Animation](Tree_Block_Animation.md) (1 shared connections)
- [Warning Classification Tests](Warning_Classification_Tests.md) (1 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (1 shared connections)
- [Interactive Prompt Tests](Interactive_Prompt_Tests.md) (1 shared connections)
- [Failed Host Collection](Failed_Host_Collection.md) (1 shared connections)
- [Run Config Key Normalization](Run_Config_Key_Normalization.md) (1 shared connections)
- [Shift Modifier Keybindings](Shift_Modifier_Keybindings.md) (1 shared connections)
- [test_history_loop_totals.py](test_history_loop_totals.py.md) (1 shared connections)
- [Run Diagnostics Accumulator](Run_Diagnostics_Accumulator.md) (1 shared connections)

## Source Files

- `src/ansible_aom/session/history.py`

## Audit Trail

- EXTRACTED: 97 (98%)
- INFERRED: 2 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*