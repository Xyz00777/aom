# PlayDefinition

> God node · 349 connections · `src/ansible_aom/core/models.py`

**Community:** [CLI Interface Tests](CLI_Interface_Tests.md)

## Connections by Relation

### calls
- _state() `INFERRED`
- _state_with_play() `INFERRED`
- _state_with_play() `INFERRED`
- ._many_tasks_state() `EXTRACTED`
- _two_level_state() `INFERRED`
- _two_play_state() `INFERRED`
- test_format_tree_block_renders_two_level_truncation() `INFERRED`
- _make_state_with_stale_running() `INFERRED`
- ._nested_state() `EXTRACTED`
- ._single_play_single_role_state() `EXTRACTED`
- _renderer_with_running_task() `INFERRED`
- _build_state() `EXTRACTED`
- _setup_state() `INFERRED`
- _setup() `INFERRED`
- .test_tree_projection_shows_pending_role_tasks() `INFERRED`
- _state_renderer() `EXTRACTED`
- _running_state() `INFERRED`
- _seed_sticky_gap_state() `INFERRED`
- test_completed_tasks_counts_dynamic_children() `INFERRED`
- .test_runtime_cache_reuses_preflight_entry() `INFERRED`

### contains
- models.py `EXTRACTED`

### imports
- run_state.py `EXTRACTED`
- format.py `EXTRACTED`
- parser.py `EXTRACTED`
- tree_projection.py `EXTRACTED`
- includes.py `EXTRACTED`
- preflight.py `EXTRACTED`

### indirect_call
- .test_run_state_definitions_list_contains_play_definition() `INFERRED`

### rationale_for
- Static play info from --list-tasks and --list-hosts (Definition class). `EXTRACTED`

### references
- format_preflight_summary() `EXTRACTED`
- graft_include_children() `EXTRACTED`
- count_total_tasks() `EXTRACTED`
- resolve_includes_from_playbook() `EXTRACTED`
- assemble_definitions() `EXTRACTED`
- count_total_tasks_seen() `EXTRACTED`
- _play_def() `EXTRACTED`
- _play_def() `EXTRACTED`
- _play_def() `EXTRACTED`
- collect_tags() `EXTRACTED`
- _iter_leaf_task_defs() `EXTRACTED`
- _make_play() `EXTRACTED`
- _make_play() `EXTRACTED`
- _count_tasks() `EXTRACTED`
- _play() `EXTRACTED`
- _build_name_index() `EXTRACTED`
- count_leaf_tasks() `EXTRACTED`
- _build_definitions() `EXTRACTED`
- _play_def() `EXTRACTED`
- _roles_referenced() `EXTRACTED`

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
- RendererMirrorMachine `INFERRED`
- TestListTasksParser `INFERRED`
- TestPtyStreamParserPhases `INFERRED`
- TestTaskDefinition `INFERRED`
- TestListHostsEdgeCases `INFERRED`
- TestHostRunState `INFERRED`
- TestPlayRunState `INFERRED`
- TestRunState `INFERRED`
- TestStatusEnum `INFERRED`
- TestRoleGrouping `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*