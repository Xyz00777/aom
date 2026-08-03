# RoleGroupDefinition

> God node · 156 connections · `src/ansible_aom/core/models.py`

**Community:** [CLI Interface Tests](CLI_Interface_Tests.md)

## Connections by Relation

### calls
- ._many_tasks_state() `INFERRED`
- _two_level_state() `INFERRED`
- test_format_tree_block_renders_two_level_truncation() `INFERRED`
- ._nested_state() `INFERRED`
- ._single_play_single_role_state() `INFERRED`
- .test_mixed_consecutive_and_nested_roles() `INFERRED`
- .test_nested_role_renders_as_sub_branch() `INFERRED`
- .test_runtime_podman_prefix_does_not_duplicate_role_header() `INFERRED`
- ._multi_task_role_with_completed_task() `INFERRED`
- .test_regression_flat_role_tasks_unchanged() `INFERRED`
- ._multi_play_completed_state() `INFERRED`
- .test_arbitrary_depth_renders_correctly() `INFERRED`
- .test_task_label_strips_role_prefix_and_pending_visible() `INFERRED`
- .test_no_double_counting_preflight_and_runtime() `INFERRED`
- .test_preflight_duplicate_role_header_bug() `INFERRED`
- .test_tui_widget_walks_recursively() `INFERRED`
- .test_single_level_role_one_inner_footer() `INFERRED`
- .test_no_inner_footer_when_role_has_no_remaining() `INFERRED`
- .test_role_total_single_role_unchanged() `INFERRED`
- .test_inner_footer_does_not_count_upcoming_plays_tasks() `INFERRED`

### contains
- models.py `EXTRACTED`

### imports
- run_state.py `EXTRACTED`
- format.py `EXTRACTED`
- parser.py `EXTRACTED`
- tree_projection.py `EXTRACTED`
- includes.py `EXTRACTED`

### indirect_call
- group_roles() `INFERRED`
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
- StreamPhase `INFERRED`
- JsonLineStream `INFERRED`
- TreeProjection `INFERRED`
- TestPtyStreamParserStderrLineEmission `INFERRED`
- TreeLine `INFERRED`
- PreParseResult `INFERRED`
- TestJsonLineStreamBasics `INFERRED`
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

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*