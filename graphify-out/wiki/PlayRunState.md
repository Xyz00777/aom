# PlayRunState

> God node · 278 connections · `src/ansible_aom/core/models.py`

**Community:** [[Run State Completion Recap]]

## Connections by Relation

### calls
- [[_state_with_play()]] `INFERRED`
- [[._handle_v2_playbook_on_task_start()]] `EXTRACTED`
- [[_add_results()]] `INFERRED`
- [[_two_level_state()]] `INFERRED`
- [[_spur_projection()]] `INFERRED`
- [[._handle_v2_runner_on_start()]] `EXTRACTED`
- [[_state_two_hosts_one_failure()]] `INFERRED`
- [[test_format_tree_block_renders_two_level_truncation()]] `INFERRED`
- [[_visible_projection()]] `INFERRED`
- [[_make_state_with_stale_running()]] `INFERRED`
- [[_renderer_with_running_task()]] `INFERRED`
- [[_state_first_play_running()]] `INFERRED`
- [[_state_with_failure()]] `INFERRED`
- [[_running_state()]] `INFERRED`
- [[._state_with()]] `INFERRED`
- [[_two_plays_with_running_tasks()]] `INFERRED`
- [[_seed_sticky_gap_state()]] `INFERRED`
- [[test_completed_tasks_counts_dynamic_children()]] `INFERRED`
- [[_state_with_two_hosts()]] `INFERRED`
- [[test_failed_host_shows_failed_task_in_suffix()]] `INFERRED`

### contains
- [[models.py]] `EXTRACTED`

### rationale_for
- [[Runtime state for a task execution on a host (State class).]] `EXTRACTED`
- [[Runtime state for a play execution (State class).]] `EXTRACTED`

### references
- [[._emit_runtime_play()]] `EXTRACTED`
- [[._touch_task_lease()]] `EXTRACTED`
- [[._play_runtime_identity()]] `EXTRACTED`
- [[._touch_play_leases()]] `EXTRACTED`
- [[._leased_play_id()]] `EXTRACTED`
- [[._remember_running_play()]] `EXTRACTED`
- [[._task_runtime_identity()]] `EXTRACTED`
- [[._play_sticky_identity()]] `EXTRACTED`

### uses
- [[TreeProjection]] `INFERRED`
- [[TreeLine]] `INFERRED`
- [[HostRow]] `INFERRED`
- [[TestJsonLineStreamBasics]] `INFERRED`
- [[TestHideStateFlag]] `INFERRED`
- [[TestListTasksEdgeCases]] `INFERRED`
- [[TestListTasksParser]] `INFERRED`
- [[TestPtyStreamParserPhases]] `INFERRED`
- [[TestTaskDefinition]] `INFERRED`
- [[TestTaskMatching]] `INFERRED`
- [[TestListHostsEdgeCases]] `INFERRED`
- [[TestHostRunState]] `INFERRED`
- [[TestPlayRunState]] `INFERRED`
- [[TestStatusBarFormat]] `INFERRED`
- [[TestRunState]] `INFERRED`
- [[TestStatusEnum]] `INFERRED`
- [[TestRoleGrouping]] `INFERRED`
- [[TestPlayDefinition]] `INFERRED`
- [[TestTaskRunState]] `INFERRED`
- [[TestListHostsParser]] `INFERRED`

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*