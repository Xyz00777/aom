# TaskDefinition

> God node · 357 connections · `src/ansible_aom/core/models.py`

**Community:** [TaskDefinition](TaskDefinition.md)

## Connections by Relation

### calls
- assemble_definitions() `EXTRACTED`
- ._many_tasks_state() `EXTRACTED`
- ._graft_or_match_task() `EXTRACTED`
- test_format_tree_block_renders_two_level_truncation() `EXTRACTED`
- _td() `EXTRACTED`
- ._nested_state() `EXTRACTED`
- ._single_play_single_role_state() `EXTRACTED`
- _renderer_with_running_task() `EXTRACTED`
- _setup_state() `EXTRACTED`
- .test_tree_projection_shows_pending_role_tasks() `EXTRACTED`
- .test_mixed_consecutive_and_nested_roles() `EXTRACTED`
- .test_nested_role_renders_as_sub_branch() `EXTRACTED`
- .test_runtime_podman_prefix_does_not_duplicate_role_header() `EXTRACTED`
- _running_state() `EXTRACTED`
- _seed_sticky_gap_state() `EXTRACTED`
- test_completed_tasks_counts_dynamic_children() `EXTRACTED`
- .test_runtime_cache_reuses_preflight_entry() `EXTRACTED`
- .test_graft_preserves_existing_children() `EXTRACTED`
- ._multi_task_role_with_completed_task() `EXTRACTED`
- .test_regression_flat_role_tasks_unchanged() `EXTRACTED`

### contains
- models.py `EXTRACTED`

### imports
- run_state.py `EXTRACTED`
- format.py `EXTRACTED`
- tree_projection.py `EXTRACTED`
- includes.py `EXTRACTED`
- preflight.py `EXTRACTED`

### indirect_call
- _count_tasks() `INFERRED`
- _count_role_group_tasks() `INFERRED`
- _roles_referenced() `INFERRED`
- test_run_preflight_grafts_include_children_into_definitions() `INFERRED`
- .test_play_definition_can_have_mixed_tasks_and_groups() `INFERRED`
- .test_role_group_at_end_of_list() `INFERRED`
- .test_role_group_definition_tasks_list() `INFERRED`
- .test_four_same_role_tasks_no_grouping() `INFERRED`
- .test_mixed_roles_no_grouping() `INFERRED`
- .test_role_group_with_mixed_none_role() `INFERRED`

### rationale_for
- Static task info from --list-tasks (Definition class). `EXTRACTED`

### references
- iter_preflight_task_defs() `EXTRACTED`
- _graft_section_dfs() `EXTRACTED`
- _iter_leaf_task_defs() `EXTRACTED`
- _make_play() `EXTRACTED`
- _make_play() `EXTRACTED`
- ._graft_role_pending_siblings() `EXTRACTED`
- _include_stub() `EXTRACTED`
- _build_name_index() `EXTRACTED`
- _td() `EXTRACTED`
- _td_tagged() `EXTRACTED`
- _task() `EXTRACTED`
- ._active_state() `EXTRACTED`
- _iter_task_def_tree() `EXTRACTED`
- _leaves_of_role_group() `EXTRACTED`
- _task() `EXTRACTED`
- _make_task() `EXTRACTED`
- _graft_children() `EXTRACTED`
- _td() `EXTRACTED`
- _index_into() `EXTRACTED`
- _find_stub_by_role() `EXTRACTED`

### uses
- [RunState](RunState.md) `INFERRED`
- [TreeProjection](TreeProjection.md) `INFERRED`
- TestPtyStreamParserStderrLineEmission `INFERRED`
- TreeLine `INFERRED`
- TestJsonLineStreamBasics `INFERRED`
- TestListTasksEdgeCases `INFERRED`
- [RendererMirrorMachine](RendererMirrorMachine.md) `INFERRED`
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