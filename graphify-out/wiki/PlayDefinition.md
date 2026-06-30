# PlayDefinition

> God node · 333 connections · `src/ansible_aom/core/models.py`

**Community:** [[Play Definition Tree Population]]

## Connections by Relation

### calls
- [[_state()]] `INFERRED`
- [[_state_with_play()]] `INFERRED`
- [[._many_tasks_state()]] `EXTRACTED`
- [[_two_level_state()]] `INFERRED`
- [[_two_play_state()]] `INFERRED`
- [[._single_play_single_role_state()]] `EXTRACTED`
- [[test_format_tree_block_renders_two_level_truncation()]] `INFERRED`
- [[_make_state_with_stale_running()]] `INFERRED`
- [[._nested_state()]] `EXTRACTED`
- [[_renderer_with_running_task()]] `INFERRED`
- [[_setup()]] `INFERRED`
- [[.test_runtime_cache_reuses_preflight_entry()]] `INFERRED`
- [[_running_state()]] `INFERRED`
- [[_seed_sticky_gap_state()]] `INFERRED`
- [[test_completed_tasks_counts_dynamic_children()]] `INFERRED`
- [[.test_task_path_populates_include_cache()]] `INFERRED`
- [[._multi_play_completed_state()]] `EXTRACTED`
- [[test_count_total_tasks_grows_with_runtime_announced_tasks()]] `INFERRED`
- [[test_handle_completion_keeps_runtime_grown_denominator()]] `INFERRED`
- [[test_fixed_floor_not_scaled_by_fast_variable_task()]] `INFERRED`

### contains
- [[models.py]] `EXTRACTED`

### rationale_for
- [[Static play info from --list-tasks and --list-hosts (Definition class).]] `EXTRACTED`

### references
- [[format_preflight_summary()]] `EXTRACTED`
- [[graft_include_children()]] `EXTRACTED`
- [[count_total_tasks()]] `EXTRACTED`
- [[resolve_includes_from_playbook()]] `EXTRACTED`
- [[count_total_tasks_seen()]] `EXTRACTED`
- [[_play_def()]] `EXTRACTED`
- [[_play_def()]] `EXTRACTED`
- [[assemble_definitions()]] `EXTRACTED`
- [[_make_play()]] `EXTRACTED`
- [[_make_play()]] `EXTRACTED`
- [[collect_tags()]] `EXTRACTED`
- [[_count_tasks()]] `EXTRACTED`
- [[_build_name_index()]] `EXTRACTED`
- [[_play()]] `EXTRACTED`
- [[_build_definitions()]] `EXTRACTED`
- [[_play_def()]] `EXTRACTED`
- [[_play_def()]] `EXTRACTED`
- [[._role_aware_definitions()]] `EXTRACTED`
- [[_roles_referenced()]] `EXTRACTED`

### uses
- [[PtyStreamParser]] `INFERRED`
- [[TreeProjection]] `INFERRED`
- [[StreamPhase]] `INFERRED`
- [[JsonLineStream]] `INFERRED`
- [[TreeLine]] `INFERRED`
- [[PreParseResult]] `INFERRED`
- [[HostRow]] `INFERRED`
- [[TestJsonLineStreamBasics]] `INFERRED`
- [[TestListTasksEdgeCases]] `INFERRED`
- [[TestListTasksParser]] `INFERRED`
- [[TestPtyStreamParserPhases]] `INFERRED`
- [[RendererMirrorMachine]] `INFERRED`
- [[TestTaskDefinition]] `INFERRED`
- [[TestTaskMatching]] `INFERRED`
- [[TestListHostsEdgeCases]] `INFERRED`
- [[TestHostRunState]] `INFERRED`
- [[TestPlayRunState]] `INFERRED`
- [[TestHostRows]] `INFERRED`
- [[TestStatusBarFormat]] `INFERRED`
- [[TestRunState]] `INFERRED`

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*