# PlayRunState

> God node · 252 connections · `src/ansible_aom/core/models.py`

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
- .test_play_start_creates_play_run_state() `INFERRED`
- .test_run_state_plays_dict_value_is_play_run_state() `INFERRED`

### rationale_for
- Runtime state for a play execution (State class). `EXTRACTED`

### references
- ._emit_runtime_play() `EXTRACTED`
- ._touch_task_lease() `EXTRACTED`
- ._finalize_play() `EXTRACTED`
- ._play_runtime_identity() `EXTRACTED`
- ._task_runtime_identity() `EXTRACTED`
- ._touch_play_leases() `EXTRACTED`
- ._leased_play_id() `EXTRACTED`
- ._remember_running_play() `EXTRACTED`
- ._resolve_play_hosts() `EXTRACTED`
- ._play_sticky_identity() `EXTRACTED`

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