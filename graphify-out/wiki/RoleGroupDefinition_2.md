# RoleGroupDefinition

> God node · 152 connections · `src/ansible_aom/core/models.py`

**Community:** [TaskDefinition](TaskDefinition.md)

## Connections by Relation

### calls
- ._many_tasks_state() `EXTRACTED`
- group_roles() `EXTRACTED`
- test_format_tree_block_renders_two_level_truncation() `EXTRACTED`
- ._nested_state() `EXTRACTED`
- ._single_play_single_role_state() `EXTRACTED`
- .test_mixed_consecutive_and_nested_roles() `EXTRACTED`
- .test_nested_role_renders_as_sub_branch() `EXTRACTED`
- .test_runtime_podman_prefix_does_not_duplicate_role_header() `EXTRACTED`
- ._multi_task_role_with_completed_task() `EXTRACTED`
- .test_regression_flat_role_tasks_unchanged() `EXTRACTED`
- ._multi_play_completed_state() `EXTRACTED`
- .test_arbitrary_depth_renders_correctly() `EXTRACTED`
- .test_task_label_strips_role_prefix_and_pending_visible() `EXTRACTED`
- .test_no_double_counting_preflight_and_runtime() `EXTRACTED`
- .test_preflight_duplicate_role_header_bug() `EXTRACTED`
- .test_single_level_role_one_inner_footer() `EXTRACTED`
- .test_no_inner_footer_when_role_has_no_remaining() `EXTRACTED`
- .test_role_total_single_role_unchanged() `EXTRACTED`
- .test_inner_footer_does_not_count_upcoming_plays_tasks() `EXTRACTED`
- .test_outer_footer_appears_when_budget_overflow() `EXTRACTED`

### contains
- models.py `EXTRACTED`

### imports
- run_state.py `EXTRACTED`
- format.py `EXTRACTED`
- parser.py `EXTRACTED`
- tree_projection.py `EXTRACTED`
- includes.py `EXTRACTED`

### indirect_call
- collect_tags() `INFERRED`
- _iter_leaf_task_defs() `INFERRED`
- _count_tasks() `INFERRED`
- _roles_referenced() `INFERRED`
- .test_play_definition_can_have_mixed_tasks_and_groups() `INFERRED`
- .test_play_definition_can_have_role_group() `INFERRED`
- .test_play_definition_tasks_can_contain_task_or_role_group() `INFERRED`
- .test_five_same_role_tasks_creates_group() `INFERRED`
- .test_role_group_at_end_of_list() `INFERRED`
- _index_into() `INFERRED`
- test_assemble_definitions_invokes_role_grouping() `INFERRED`

### method
- .name() `EXTRACTED`

### rationale_for
- Grouped role tasks when 5+ consecutive tasks share same role.      ``parent`` ca `EXTRACTED`

### references
- iter_preflight_task_defs() `EXTRACTED`
- _leaves_of_role_group() `EXTRACTED`
- _count_role_group_tasks() `EXTRACTED`
- _collect_role_group_tags() `EXTRACTED`

### uses
- [RunState](RunState.md) `INFERRED`
- [PtyStreamParser](PtyStreamParser.md) `INFERRED`
- [StreamPhase](StreamPhase.md) `INFERRED`
- [JsonLineStream](JsonLineStream.md) `INFERRED`
- [TreeProjection](TreeProjection.md) `INFERRED`
- TestPtyStreamParserStderrLineEmission `INFERRED`
- TreeLine `INFERRED`
- PreParseResult `INFERRED`
- TestJsonLineStreamBasics `INFERRED`
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

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*