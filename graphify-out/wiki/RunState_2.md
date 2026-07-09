# RunState

> God node · 559 connections · `src/ansible_aom/core/run_state.py`

**Community:** [Status Bar Warning Panels](Status_Bar_Warning_Panels.md)

## Connections by Relation

### calls
- run_playbook() `EXTRACTED`
- _spur_projection() `EXTRACTED`
- _state_two_hosts_one_failure() `INFERRED`
- test_format_tree_block_renders_two_level_truncation() `EXTRACTED`
- _visible_projection() `EXTRACTED`
- iter_tree_frames() `INFERRED`
- .test_tree_projection_shows_pending_role_tasks() `INFERRED`
- .test_mixed_consecutive_and_nested_roles() `EXTRACTED`
- .test_nested_role_renders_as_sub_branch() `EXTRACTED`
- .test_runtime_podman_prefix_does_not_duplicate_role_header() `EXTRACTED`
- .start() `INFERRED`
- test_completed_tasks_counts_dynamic_children() `INFERRED`
- .test_runtime_cache_reuses_preflight_entry() `INFERRED`
- .test_watchdog_emits_warning_and_returns_when_no_eof() `INFERRED`
- .test_watchdog_emits_warning_via_logger() `INFERRED`
- .test_watchdog_path_calls_expect() `INFERRED`
- .test_regression_flat_role_tasks_unchanged() `EXTRACTED`
- test_count_total_tasks_grows_with_runtime_announced_tasks() `INFERRED`
- test_host_leaves_dropped_when_budget_tight() `EXTRACTED`
- test_no_preflight_no_upcoming_plays() `EXTRACTED`

### contains
- run_state.py `EXTRACTED`

### indirect_call
- .test_app_has_runstate_after_start() `INFERRED`

### method
- ._handle_v2_playbook_on_task_start() `EXTRACTED`
- ._handle_v2_runner_on_start() `EXTRACTED`
- ._graft_or_match_task() `EXTRACTED`
- ._resolve_play_id() `EXTRACTED`
- ._task_dict() `EXTRACTED`
- ._handle_v2_runner_item_on() `EXTRACTED`
- ._handle_v2_runner_on_failed() `EXTRACTED`
- ._handle_v2_runner_on_ok() `EXTRACTED`
- ._handle_v2_runner_on_skipped() `EXTRACTED`
- ._handle_v2_runner_on_unreachable() `EXTRACTED`
- ._hosts_dict() `EXTRACTED`
- ._graft_role_pending_siblings() `EXTRACTED`
- ._finalize_play() `EXTRACTED`
- ._handle_v2_playbook_on_play_start() `EXTRACTED`
- ._bump_tree_revision() `EXTRACTED`
- ._handle_v2_playbook_on_handler_task_start() `EXTRACTED`
- ._handle_v2_playbook_on_stats() `EXTRACTED`
- ._parent_role_from_cache() `EXTRACTED`
- .handle_event() `EXTRACTED`
- ._handle_v2_playbook_on_start() `EXTRACTED`

### rationale_for
- Complete execution state (State class). `EXTRACTED`

### references
- .from_run_state() `EXTRACTED`
- parse_jsonl_output() `EXTRACTED`
- _feed() `EXTRACTED`
- determine_exit_code() `EXTRACTED`
- _drive() `EXTRACTED`
- _drive() `EXTRACTED`
- format_failure_recap() `EXTRACTED`
- _state() `EXTRACTED`
- _state_with_play() `EXTRACTED`
- _state_with_play() `EXTRACTED`
- ._many_tasks_state() `EXTRACTED`
- _discover_role() `EXTRACTED`
- _add_results() `EXTRACTED`
- _state() `EXTRACTED`
- _two_level_state() `EXTRACTED`
- _two_play_state() `EXTRACTED`
- _flush_pending() `EXTRACTED`
- count_total_tasks_seen() `EXTRACTED`
- count_completed_tasks() `EXTRACTED`
- _discover_include() `EXTRACTED`

### uses
- [TaskDefinition](TaskDefinition.md) `INFERRED`
- [PlayDefinition](PlayDefinition.md) `INFERRED`
- [HostRunState](HostRunState.md) `INFERRED`
- [Status](Status.md) `INFERRED`
- [PlayRunState](PlayRunState.md) `INFERRED`
- [TaskRunState](TaskRunState.md) `INFERRED`
- [AOMApp](AOMApp.md) `INFERRED`
- [RoleGroupDefinition](RoleGroupDefinition.md) `INFERRED`
- [JsonRenderer](JsonRenderer.md) `INFERRED`
- JsonlEvent `INFERRED`
- [TreeProjection](TreeProjection.md) `INFERRED`
- [TaskTree](TaskTree.md) `INFERRED`
- IncludeCacheEntry `INFERRED`
- TreeLine `INFERRED`
- [MainScreen](MainScreen.md) `INFERRED`
- TestHideStateFlag `INFERRED`
- [_SessionSink](_SessionSink.md) `INFERRED`
- TestRendererProtocol `INFERRED`
- _NullSink `INFERRED`
- TestHideStateCompactPlumbing `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*