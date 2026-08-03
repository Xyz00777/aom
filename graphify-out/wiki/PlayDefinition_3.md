# PlayDefinition

> God node · 323 connections · `src/ansible_aom/core/models.py`

**Community:** [PlayDefinition](PlayDefinition.md)

## Connections by Relation

### calls
- _state() `EXTRACTED`
- _state_with_play() `EXTRACTED`
- _state_with_play() `EXTRACTED`
- ._many_tasks_state() `EXTRACTED`
- _two_play_state() `EXTRACTED`
- test_format_tree_block_renders_two_level_truncation() `EXTRACTED`
- _make_state_with_stale_running() `EXTRACTED`
- ._nested_state() `EXTRACTED`
- ._single_play_single_role_state() `EXTRACTED`
- _renderer_with_running_task() `EXTRACTED`
- _build_state() `EXTRACTED`
- _setup_state() `EXTRACTED`
- _setup() `EXTRACTED`
- .test_tree_projection_shows_pending_role_tasks() `EXTRACTED`
- _state_renderer() `EXTRACTED`
- _running_state() `EXTRACTED`
- _seed_sticky_gap_state() `EXTRACTED`
- test_completed_tasks_counts_dynamic_children() `EXTRACTED`
- .test_runtime_cache_reuses_preflight_entry() `EXTRACTED`
- ._multi_task_role_with_completed_task() `EXTRACTED`

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
- collect_tags() `EXTRACTED`
- _iter_leaf_task_defs() `EXTRACTED`
- _make_play() `EXTRACTED`
- _play_def() `EXTRACTED`
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
- [StreamPhase](StreamPhase.md) `INFERRED`
- [JsonLineStream](JsonLineStream.md) `INFERRED`
- [TreeProjection](TreeProjection.md) `INFERRED`
- TestPtyStreamParserStderrLineEmission `INFERRED`
- TreeLine `INFERRED`
- PreParseResult `INFERRED`
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

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*