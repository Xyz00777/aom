# TaskRunState

> God node · 244 connections · `src/ansible_aom/core/models.py`

**Community:** [HostRunState](HostRunState.md)

## Connections by Relation

### calls
- ._handle_v2_playbook_on_task_start() `EXTRACTED`
- _state_with_play() `EXTRACTED`
- _state_with_play() `EXTRACTED`
- ._handle_v2_runner_on_start() `EXTRACTED`
- _add_results() `EXTRACTED`
- _spur_projection() `EXTRACTED`
- _state_two_hosts_one_failure() `INFERRED`
- test_format_tree_block_renders_two_level_truncation() `EXTRACTED`
- _visible_projection() `EXTRACTED`
- _make_state_with_stale_running() `EXTRACTED`
- _renderer_with_running_task() `EXTRACTED`
- _build_state() `EXTRACTED`
- _state_first_play_running() `EXTRACTED`
- _state_with_failure() `EXTRACTED`
- _running_state() `EXTRACTED`
- ._state_with() `EXTRACTED`
- _two_plays_with_running_tasks() `EXTRACTED`
- _seed_sticky_gap_state() `EXTRACTED`
- test_completed_tasks_counts_dynamic_children() `EXTRACTED`
- _state_with_two_hosts() `EXTRACTED`

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
- [TreeProjection](TreeProjection.md) `INFERRED`
- TestPtyStreamParserStderrLineEmission `INFERRED`
- TreeLine `INFERRED`
- TestJsonLineStreamBasics `INFERRED`
- TestHideStateFlag `INFERRED`
- TestListTasksEdgeCases `INFERRED`
- TestListTasksParser `INFERRED`
- [TestPtyStreamParserPhases](TestPtyStreamParserPhases.md) `INFERRED`
- TestTaskDefinition `INFERRED`
- TestListHostsEdgeCases `INFERRED`
- [TestHostRunState](TestHostRunState.md) `INFERRED`
- TestPlayRunState `INFERRED`
- TestRunState `INFERRED`
- [TestStatusEnum](TestStatusEnum.md) `INFERRED`
- [TestRoleGrouping](TestRoleGrouping.md) `INFERRED`
- TestPlayDefinition `INFERRED`
- TestTaskRunState `INFERRED`
- TestJsonLineStreamCarryBuffer `INFERRED`
- TestListHostsParser `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*