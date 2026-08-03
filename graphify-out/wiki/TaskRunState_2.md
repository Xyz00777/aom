# TaskRunState

> God node · 260 connections · `src/ansible_aom/core/models.py`

**Community:** [Play Definition Tree Population](Play_Definition_Tree_Population.md)

## Connections by Relation

### calls
- ._handle_v2_playbook_on_task_start() `EXTRACTED`
- _state_with_play() `INFERRED`
- _state_with_play() `INFERRED`
- ._handle_v2_runner_on_start() `EXTRACTED`
- _add_results() `INFERRED`
- _two_level_state() `INFERRED`
- _spur_projection() `INFERRED`
- _state_two_hosts_one_failure() `INFERRED`
- test_format_tree_block_renders_two_level_truncation() `INFERRED`
- _visible_projection() `INFERRED`
- _make_state_with_stale_running() `INFERRED`
- _renderer_with_running_task() `INFERRED`
- _build_state() `EXTRACTED`
- _state_first_play_running() `INFERRED`
- _state_with_failure() `INFERRED`
- _running_state() `INFERRED`
- ._state_with() `INFERRED`
- _two_plays_with_running_tasks() `INFERRED`
- _seed_sticky_gap_state() `INFERRED`
- test_completed_tasks_counts_dynamic_children() `INFERRED`

### contains
- models.py `EXTRACTED`

### imports
- run_state.py `EXTRACTED`
- tree_projection.py `EXTRACTED`

### indirect_call
- test_runstate_never_holds_orphan_hostrunstate() `INFERRED`
- .test_runner_start_creates_task_run_state() `INFERRED`
- .test_play_run_state_tasks_dict_value_is_task_run_state() `INFERRED`

### rationale_for
- Runtime state for a task execution (State class). `EXTRACTED`

### references
- _reserve_host_run_state() `EXTRACTED`
- ._resolve_runner_task() `EXTRACTED`
- ._touch_task_lease() `EXTRACTED`
- ._prior_host_start_time() `EXTRACTED`
- ._play_running_and_pending() `EXTRACTED`
- ._task_line() `EXTRACTED`
- ._task_runtime_identity() `EXTRACTED`
- _pending_host_count() `EXTRACTED`

### uses
- [RunState](RunState.md) `INFERRED`
- TreeProjection `INFERRED`
- TestPtyStreamParserStderrLineEmission `INFERRED`
- TreeLine `INFERRED`
- TestJsonLineStreamBasics `INFERRED`
- TestHideStateFlag `INFERRED`
- TestListTasksEdgeCases `INFERRED`
- TestListTasksParser `INFERRED`
- TestPtyStreamParserPhases `INFERRED`
- TestTaskDefinition `INFERRED`
- TestListHostsEdgeCases `INFERRED`
- TestHostRunState `INFERRED`
- TestPlayRunState `INFERRED`
- TestRunState `INFERRED`
- TestStatusEnum `INFERRED`
- TestRoleGrouping `INFERRED`
- TestPlayDefinition `INFERRED`
- TestTaskRunState `INFERRED`
- TestJsonLineStreamCarryBuffer `INFERRED`
- TestListHostsParser `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*