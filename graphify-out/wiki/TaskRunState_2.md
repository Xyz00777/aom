# TaskRunState

> God node · 266 connections · `src/ansible_aom/core/models.py`

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
- _state_first_play_running() `INFERRED`
- .test_update_from_state_drops_completed_tasks() `INFERRED`
- .test_update_from_state_keeps_running_task_visible() `INFERRED`
- .test_update_from_state_shows_ok_icon_after_completion() `INFERRED`
- _state_with_failure() `INFERRED`
- _running_state() `INFERRED`
- ._state_with() `INFERRED`
- _two_plays_with_running_tasks() `INFERRED`

### contains
- models.py `EXTRACTED`

### indirect_call
- test_runstate_never_holds_orphan_hostrunstate() `INFERRED`
- .test_runner_start_creates_task_run_state() `INFERRED`
- .test_play_run_state_tasks_dict_value_is_task_run_state() `INFERRED`

### rationale_for
- Runtime state for a task execution (State class). `EXTRACTED`

### references
- _reserve_host_run_state() `EXTRACTED`
- ._touch_task_lease() `EXTRACTED`
- ._play_running_and_pending() `EXTRACTED`
- ._task_line() `EXTRACTED`
- ._task_runtime_identity() `EXTRACTED`

### uses
- [RunState](RunState.md) `INFERRED`
- [TreeProjection](TreeProjection.md) `INFERRED`
- TestPtyStreamParserStderrLineEmission `INFERRED`
- TreeLine `INFERRED`
- TestJsonLineStreamBasics `INFERRED`
- TestHideStateFlag `INFERRED`
- TestListTasksEdgeCases `INFERRED`
- TestListTasksParser `INFERRED`
- TestPtyStreamParserPhases `INFERRED`
- TestTaskDefinition `INFERRED`
- TestTaskMatching `INFERRED`
- TestListHostsEdgeCases `INFERRED`
- TestHostRunState `INFERRED`
- TestPlayRunState `INFERRED`
- TestStatusBarFormat `INFERRED`
- TestRunState `INFERRED`
- TestStatusEnum `INFERRED`
- TestRoleGrouping `INFERRED`
- TestPlayDefinition `INFERRED`
- TestTaskRunState `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*