# TaskDefinition

> God node · 393 connections · `src/ansible_aom/core/models.py`

**Community:** [Compact Renderer Implementation](Compact_Renderer_Implementation.md)

## Connections by Relation

### calls
- assemble_definitions() `INFERRED`
- ._many_tasks_state() `EXTRACTED`
- _two_level_state() `INFERRED`
- ._graft_or_match_task() `EXTRACTED`
- test_format_tree_block_renders_two_level_truncation() `INFERRED`
- _td() `INFERRED`
- ._nested_state() `EXTRACTED`
- ._single_play_single_role_state() `EXTRACTED`
- _renderer_with_running_task() `INFERRED`
- _setup_state() `INFERRED`
- .test_update_from_state_drops_completed_tasks() `INFERRED`
- .test_update_from_state_keeps_running_task_visible() `INFERRED`
- .test_update_from_state_shows_ok_icon_after_completion() `INFERRED`
- .test_tree_projection_shows_pending_role_tasks() `INFERRED`
- .test_mixed_consecutive_and_nested_roles() `INFERRED`
- .test_nested_role_renders_as_sub_branch() `INFERRED`
- .test_runtime_podman_prefix_does_not_duplicate_role_header() `INFERRED`
- _running_state() `INFERRED`
- _seed_sticky_gap_state() `INFERRED`
- test_completed_tasks_counts_dynamic_children() `INFERRED`

### contains
- models.py `EXTRACTED`

### indirect_call
- _count_tasks() `INFERRED`
- _count_role_group_tasks() `INFERRED`
- _roles_referenced() `INFERRED`
- .populate_from_definitions() `INFERRED`
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
- _graft_section_dfs() `EXTRACTED`
- _iter_leaf_task_defs() `EXTRACTED`
- _make_play() `EXTRACTED`
- iter_preflight_task_defs() `EXTRACTED`
- _make_play() `EXTRACTED`
- ._graft_role_pending_siblings() `EXTRACTED`
- _include_stub() `EXTRACTED`
- _build_name_index() `EXTRACTED`
- _td() `EXTRACTED`
- _td_tagged() `EXTRACTED`
- _task() `EXTRACTED`
- ._active_state() `EXTRACTED`
- _leaves_of_role_group() `EXTRACTED`
- _task() `EXTRACTED`
- _make_task() `EXTRACTED`
- _graft_children() `EXTRACTED`
- _iter_task_def_tree() `EXTRACTED`
- _td() `EXTRACTED`
- _index_into() `EXTRACTED`
- _find_stub_by_role() `EXTRACTED`

### uses
- [RunState](RunState.md) `INFERRED`
- [TreeProjection](TreeProjection.md) `INFERRED`
- [TaskTree](TaskTree.md) `INFERRED`
- TestPtyStreamParserStderrLineEmission `INFERRED`
- TreeLine `INFERRED`
- TestJsonLineStreamBasics `INFERRED`
- TestListTasksEdgeCases `INFERRED`
- RendererMirrorMachine `INFERRED`
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

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*