# HostRunState

> God node · 285 connections · `src/ansible_aom/core/models.py`

**Community:** [HostRunState](HostRunState.md)

## Connections by Relation

### calls
- ._handle_v2_playbook_on_task_start() `EXTRACTED`
- _state_with_play() `EXTRACTED`
- _state_with_play() `EXTRACTED`
- ._handle_v2_runner_on_start() `EXTRACTED`
- _add_results() `EXTRACTED`
- ._handle_v2_runner_on_failed() `EXTRACTED`
- ._handle_v2_runner_on_ok() `EXTRACTED`
- ._handle_v2_runner_on_skipped() `EXTRACTED`
- ._handle_v2_runner_on_unreachable() `EXTRACTED`
- _spur_projection() `EXTRACTED`
- _state_two_hosts_one_failure() `INFERRED`
- test_format_tree_block_renders_two_level_truncation() `EXTRACTED`
- _visible_projection() `EXTRACTED`
- _make_state_with_stale_running() `EXTRACTED`
- _renderer_with_running_task() `EXTRACTED`
- _build_state() `EXTRACTED`
- _state_first_play_running() `EXTRACTED`
- ._handle_v2_runner_item_on() `EXTRACTED`
- _state_with_failure() `EXTRACTED`
- _running_state() `EXTRACTED`

### contains
- models.py `EXTRACTED`

### imports
- run_state.py `EXTRACTED`
- tree_projection.py `EXTRACTED`

### indirect_call
- .test_runner_ok_creates_host_run_state() `INFERRED`
- .test_task_run_state_hosts_dict_key_is_hostname_string() `INFERRED`

### rationale_for
- Runtime state for a task execution on a host (State class). `EXTRACTED`

### references
- _reserve_host_run_state() `EXTRACTED`
- _effective_status() `EXTRACTED`
- _host_leaf_label() `EXTRACTED`
- _leaf_elapsed_s() `EXTRACTED`
- _leaf_visible() `EXTRACTED`

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