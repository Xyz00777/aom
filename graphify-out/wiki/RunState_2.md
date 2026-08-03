# RunState

> God node · 581 connections · `src/ansible_aom/core/run_state.py`

**Community:** [RunState](RunState.md)

## Connections by Relation

### calls
- run_playbook() `EXTRACTED`
- _spur_projection() `EXTRACTED`
- _state_two_hosts_one_failure() `INFERRED`
- test_format_tree_block_renders_two_level_truncation() `EXTRACTED`
- _visible_projection() `EXTRACTED`
- iter_tree_frames() `EXTRACTED`
- .test_tree_projection_shows_pending_role_tasks() `INFERRED`
- .test_watchdog_emits_warning_and_returns_when_no_eof() `EXTRACTED`
- .test_watchdog_emits_warning_via_logger() `EXTRACTED`
- .test_watchdog_path_calls_expect() `EXTRACTED`
- .test_mixed_consecutive_and_nested_roles() `EXTRACTED`
- .test_nested_role_renders_as_sub_branch() `EXTRACTED`
- .test_runtime_podman_prefix_does_not_duplicate_role_header() `EXTRACTED`
- .start() `INFERRED`
- test_completed_tasks_counts_dynamic_children() `INFERRED`
- .test_runtime_cache_reuses_preflight_entry() `INFERRED`
- .test_clean_eof_after_stats_no_warning() `EXTRACTED`
- .test_regression_flat_role_tasks_unchanged() `EXTRACTED`
- test_count_total_tasks_grows_with_runtime_announced_tasks() `INFERRED`
- test_host_leaves_dropped_when_budget_tight() `EXTRACTED`

### contains
- run_state.py `EXTRACTED`

### imports
- [json.py](json.py.md) `EXTRACTED`
- format.py `EXTRACTED`
- [runner.py](runner.py.md) `EXTRACTED`
- tree_projection.py `EXTRACTED`
- includes.py `EXTRACTED`
- core/replay.py `EXTRACTED`
- parity.py `EXTRACTED`
- core/exit_code.py `EXTRACTED`

### method
- ._handle_v2_playbook_on_task_start() `EXTRACTED`
- ._handle_v2_runner_on_start() `EXTRACTED`
- ._task_dict() `EXTRACTED`
- ._handle_v2_runner_on_failed() `EXTRACTED`
- ._handle_v2_runner_on_ok() `EXTRACTED`
- ._handle_v2_runner_on_skipped() `EXTRACTED`
- ._handle_v2_runner_on_unreachable() `EXTRACTED`
- ._resolve_play_id() `EXTRACTED`
- ._graft_or_match_task() `EXTRACTED`
- ._resolve_runner_task() `EXTRACTED`
- ._handle_v2_runner_item_on() `EXTRACTED`
- ._hosts_dict() `EXTRACTED`
- ._graft_role_pending_siblings() `EXTRACTED`
- ._note_unmatched() `EXTRACTED`
- ._prior_host_start_time() `EXTRACTED`
- ._finalize_play() `EXTRACTED`
- ._handle_v2_playbook_on_play_start() `EXTRACTED`
- ._bump_tree_revision() `EXTRACTED`
- ._handle_v2_playbook_on_handler_task_start() `EXTRACTED`
- ._handle_v2_playbook_on_stats() `EXTRACTED`

### rationale_for
- Complete execution state (State class). `EXTRACTED`

### references
- .from_run_state() `EXTRACTED`
- parse_jsonl_output() `EXTRACTED`
- _drive() `EXTRACTED`
- _feed() `EXTRACTED`
- determine_exit_code() `EXTRACTED`
- format_failure_recap() `EXTRACTED`
- _drive() `EXTRACTED`
- _play_start() `EXTRACTED`
- _task_start() `EXTRACTED`
- _discover_role() `EXTRACTED`
- _state() `EXTRACTED`
- _state_with_play() `EXTRACTED`
- _state_with_play() `EXTRACTED`
- ._many_tasks_state() `EXTRACTED`
- _add_results() `EXTRACTED`
- _state() `EXTRACTED`
- _two_play_state() `EXTRACTED`
- count_total_tasks_seen() `EXTRACTED`
- count_completed_tasks() `EXTRACTED`
- _flush_pending() `EXTRACTED`

### uses
- [TaskDefinition](TaskDefinition.md) `INFERRED`
- [PlayDefinition](PlayDefinition.md) `INFERRED`
- [HostRunState](HostRunState.md) `INFERRED`
- [Status](Status.md) `INFERRED`
- [PlayRunState](PlayRunState.md) `INFERRED`
- [TaskRunState](TaskRunState.md) `INFERRED`
- [RoleGroupDefinition](RoleGroupDefinition.md) `INFERRED`
- JsonRenderer `INFERRED`
- JsonlEvent `INFERRED`
- [TreeProjection](TreeProjection.md) `INFERRED`
- [IncludeCacheEntry](IncludeCacheEntry.md) `INFERRED`
- TreeLine `INFERRED`
- TestHideStateFlag `INFERRED`
- _SessionSink `INFERRED`
- RoleCacheEntry `INFERRED`
- _NullSink `INFERRED`
- [TestHideStateCompactPlumbing](TestHideStateCompactPlumbing.md) `INFERRED`
- [TestNoRedactFlag](TestNoRedactFlag.md) `INFERRED`
- TestRendererProtocol `INFERRED`
- TestHandleEventDispatcher `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*