# Running Animation Frames

> 14 nodes · cohesion 0.19

## Key Concepts

- **_make_state_with_stale_running()** (11 connections) — `tests/unit/test_stale_running_cleanup.py`
- **TestStaleRunningCleanup** (11 connections) — `tests/unit/test_stale_running_cleanup.py`
- **test_stale_running_cleanup.py** (4 connections) — `tests/unit/test_stale_running_cleanup.py`
- **.test_host_rows_no_stale_running_after_stats()** (4 connections) — `tests/unit/test_stale_running_cleanup.py`
- **.test_completed_hosts_preserved_after_stats_cleanup()** (3 connections) — `tests/unit/test_stale_running_cleanup.py`
- **.test_task_status_cleared_after_stats_cleanup()** (3 connections) — `tests/unit/test_stale_running_cleanup.py`
- **.test_v2_playbook_on_stats_clears_stale_running_hosts()** (3 connections) — `tests/unit/test_stale_running_cleanup.py`
- **Regression tests for stale RUNNING hosts in the state model.  When terminal even** (1 connections) — `tests/unit/test_stale_running_cleanup.py`
- **host_rows() should not show any host as still running after         the playbook** (1 connections) — `tests/unit/test_stale_running_cleanup.py`
- **Cleaning up stale RUNNING hosts must not alter hosts that already         have t** (1 connections) — `tests/unit/test_stale_running_cleanup.py`
- **TaskRunState.status should be cleared from RUNNING after         playbook comple** (1 connections) — `tests/unit/test_stale_running_cleanup.py`
- **Build a RunState where ipa1 completed task A but is stuck as RUNNING     on task** (1 connections) — `tests/unit/test_stale_running_cleanup.py`
- **When playbook ends, stale RUNNING hosts must be cleaned up.** (1 connections) — `tests/unit/test_stale_running_cleanup.py`
- **After v2_playbook_on_stats, hosts stuck as RUNNING must be         transitioned** (1 connections) — `tests/unit/test_stale_running_cleanup.py`

## Relationships

- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (7 shared connections)
- [CLI Argument Parser](CLI_Argument_Parser.md) (2 shared connections)
- [Status Bar Warning Panels](Status_Bar_Warning_Panels.md) (1 shared connections)
- [Compact Renderer Integration Tests](Compact_Renderer_Integration_Tests.md) (1 shared connections)
- [CLI Interface Tests](CLI_Interface_Tests.md) (1 shared connections)

## Source Files

- `tests/unit/test_stale_running_cleanup.py`

## Audit Trail

- EXTRACTED: 37 (80%)
- INFERRED: 9 (20%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*