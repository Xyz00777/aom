# RunState

> God node · 633 connections · `src/ansible_aom/core/models.py`

**Community:** [[Run State Summary Panel]]

## Connections by Relation

### calls
- [[_spur_projection()]] `EXTRACTED`
- [[_state_two_hosts_one_failure()]] `INFERRED`
- [[test_format_tree_block_renders_two_level_truncation()]] `EXTRACTED`
- [[_visible_projection()]] `EXTRACTED`
- [[iter_tree_frames()]] `INFERRED`
- [[.test_runtime_cache_reuses_preflight_entry()]] `INFERRED`
- [[.test_mixed_consecutive_and_nested_roles()]] `EXTRACTED`
- [[.test_nested_role_renders_as_sub_branch()]] `EXTRACTED`
- [[.test_runtime_podman_prefix_does_not_duplicate_role_header()]] `EXTRACTED`
- [[test_completed_tasks_counts_dynamic_children()]] `INFERRED`
- [[.test_task_path_populates_include_cache()]] `INFERRED`
- [[.test_regression_flat_role_tasks_unchanged()]] `EXTRACTED`
- [[test_count_total_tasks_grows_with_runtime_announced_tasks()]] `INFERRED`
- [[test_host_leaves_dropped_when_budget_tight()]] `EXTRACTED`
- [[test_no_preflight_no_upcoming_plays()]] `EXTRACTED`
- [[test_tree_lines_respects_budget_with_many_pending_tasks()]] `EXTRACTED`
- [[test_tree_lines_respects_budget_with_upcoming_plays()]] `EXTRACTED`
- [[test_no_preflight_falls_back_to_running_only()]] `EXTRACTED`
- [[.test_apply_state_icons_updates_host_icon()]] `INFERRED`
- [[.test_apply_state_icons_updates_task_icon()]] `INFERRED`

### contains
- [[models.py]] `EXTRACTED`

### method
- [[._handle_v2_playbook_on_task_start()]] `EXTRACTED`
- [[._handle_v2_runner_on_start()]] `EXTRACTED`
- [[._resolve_play_id()]] `EXTRACTED`
- [[._task_dict()]] `EXTRACTED`
- [[._graft_or_match_task()]] `EXTRACTED`
- [[._handle_v2_playbook_on_play_start()]] `EXTRACTED`
- [[._handle_v2_runner_item_on()]] `EXTRACTED`
- [[._handle_v2_runner_on_failed()]] `EXTRACTED`
- [[._handle_v2_runner_on_ok()]] `EXTRACTED`
- [[._handle_v2_runner_on_skipped()]] `EXTRACTED`
- [[._handle_v2_runner_on_unreachable()]] `EXTRACTED`
- [[._hosts_dict()]] `EXTRACTED`
- [[._finalize_play()]] `EXTRACTED`
- [[._handle_v2_playbook_on_handler_task_start()]] `EXTRACTED`
- [[._handle_v2_playbook_on_stats()]] `EXTRACTED`
- [[._parent_role_from_cache()]] `EXTRACTED`
- [[._bump_tree_revision()]] `EXTRACTED`
- [[.handle_event()]] `EXTRACTED`
- [[._handle_v2_playbook_on_start()]] `EXTRACTED`
- [[._rebuild_definition_indexes()]] `EXTRACTED`

### rationale_for
- [[Complete execution state (State class).]] `EXTRACTED`

### references
- [[.from_run_state()]] `EXTRACTED`
- [[parse_jsonl_output()]] `EXTRACTED`
- [[format_failure_recap()]] `EXTRACTED`
- [[_state()]] `EXTRACTED`
- [[_state_with_play()]] `EXTRACTED`
- [[._many_tasks_state()]] `EXTRACTED`
- [[count_total_tasks_seen()]] `EXTRACTED`
- [[count_completed_tasks()]] `EXTRACTED`
- [[_discover_role()]] `EXTRACTED`
- [[_add_results()]] `EXTRACTED`
- [[_state()]] `EXTRACTED`
- [[_two_level_state()]] `EXTRACTED`
- [[_two_play_state()]] `EXTRACTED`
- [[._single_play_single_role_state()]] `EXTRACTED`
- [[_discover_include()]] `EXTRACTED`
- [[discover_include_with_runtime_path()]] `EXTRACTED`
- [[_start_play()]] `EXTRACTED`
- [[_start_task()]] `EXTRACTED`
- [[_make_state_with_stale_running()]] `EXTRACTED`
- [[._nested_state()]] `EXTRACTED`

### uses
- [[CompactRenderer]] `INFERRED`
- [[AOMApp]] `INFERRED`
- [[TreeProjection]] `INFERRED`
- [[TreeLine]] `INFERRED`
- [[JsonRenderer]] `INFERRED`
- [[TaskTree]] `INFERRED`
- [[HostRow]] `INFERRED`
- [[TestJsonLineStreamBasics]] `INFERRED`
- [[TestHideStateFlag]] `INFERRED`
- [[TestListTasksEdgeCases]] `INFERRED`
- [[MainScreen]] `INFERRED`
- [[TestListTasksParser]] `INFERRED`
- [[TestPtyStreamParserPhases]] `INFERRED`
- [[TestTaskDefinition]] `INFERRED`
- [[TestTaskMatching]] `INFERRED`
- [[TestListHostsEdgeCases]] `INFERRED`
- [[TestHostRunState]] `INFERRED`
- [[TestPlayRunState]] `INFERRED`
- [[TestHostRows]] `INFERRED`
- [[TestStatusBarFormat]] `INFERRED`

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*