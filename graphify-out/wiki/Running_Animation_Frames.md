# Running Animation Frames

> 16 nodes · cohesion 0.16

## Key Concepts

- **_make_state_with_stale_running()** (11 connections) — `tests/unit/test_stale_running_cleanup.py`
- **TestStaleRunningCleanup** (11 connections) — `tests/unit/test_stale_running_cleanup.py`
- **TestHostRowsCurrentTask** (9 connections) — `tests/unit/test_stale_running_cleanup.py`
- **test_stale_running_cleanup.py** (6 connections) — `tests/unit/test_stale_running_cleanup.py`
- **.test_host_rows_no_stale_running_after_stats()** (4 connections) — `tests/unit/test_stale_running_cleanup.py`
- **.test_completed_hosts_preserved_after_stats_cleanup()** (3 connections) — `tests/unit/test_stale_running_cleanup.py`
- **.test_task_status_cleared_after_stats_cleanup()** (3 connections) — `tests/unit/test_stale_running_cleanup.py`
- **.test_v2_playbook_on_stats_clears_stale_running_hosts()** (3 connections) — `tests/unit/test_stale_running_cleanup.py`
- **Regression tests for stale RUNNING hosts in the state model.  When terminal even** (1 connections) — `tests/unit/test_stale_running_cleanup.py`
- **host_rows() should not show any host as still running after         the playbook** (1 connections) — `tests/unit/test_stale_running_cleanup.py`
- **Cleaning up stale RUNNING hosts must not alter hosts that already         have t** (1 connections) — `tests/unit/test_stale_running_cleanup.py`
- **TaskRunState.status should be cleared from RUNNING after         playbook comple** (1 connections) — `tests/unit/test_stale_running_cleanup.py`
- **Test that host_rows() correctly tracks current_task per host.** (1 connections) — `tests/unit/test_stale_running_cleanup.py`
- **Build a RunState where ipa1 completed task A but is stuck as RUNNING     on task** (1 connections) — `tests/unit/test_stale_running_cleanup.py`
- **When playbook ends, stale RUNNING hosts must be cleaned up.** (1 connections) — `tests/unit/test_stale_running_cleanup.py`
- **After v2_playbook_on_stats, hosts stuck as RUNNING must be         transitioned** (1 connections) — `tests/unit/test_stale_running_cleanup.py`

## Relationships

- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (9 shared connections)
- [CLI Interface Tests](CLI_Interface_Tests.md) (7 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (2 shared connections)
- [Task Definition Live Refresh](Task_Definition_Live_Refresh.md) (1 shared connections)
- [tree.py](tree.py.md) (1 shared connections)

## Source Files

- `tests/unit/test_stale_running_cleanup.py`

## Audit Trail

- EXTRACTED: 44 (76%)
- INFERRED: 14 (24%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*