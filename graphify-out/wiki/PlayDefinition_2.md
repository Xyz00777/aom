# PlayDefinition

> God node · 340 connections · `src/ansible_aom/core/models.py`

**Community:** [CLI Argument Parser](CLI_Argument_Parser.md)

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
- _setup_state() `INFERRED`
- _setup() `INFERRED`
- .test_update_from_state_drops_completed_tasks() `INFERRED`
- .test_update_from_state_keeps_running_task_visible() `INFERRED`
- .test_update_from_state_shows_ok_icon_after_completion() `INFERRED`
- .test_tree_projection_shows_pending_role_tasks() `INFERRED`
- _running_state() `INFERRED`
- _seed_sticky_gap_state() `INFERRED`
- test_completed_tasks_counts_dynamic_children() `INFERRED`

### contains
- models.py `EXTRACTED`

### indirect_call
- .test_run_state_definitions_list_contains_play_definition() `INFERRED`
- .test_run_state_definitions_list() `INFERRED`

### rationale_for
- Static play info from --list-tasks and --list-hosts (Definition class). `EXTRACTED`

### references
- format_preflight_summary() `EXTRACTED`
- graft_include_children() `EXTRACTED`
- count_total_tasks() `EXTRACTED`
- assemble_definitions() `EXTRACTED`
- resolve_includes_from_playbook() `EXTRACTED`
- count_total_tasks_seen() `EXTRACTED`
- _play_def() `EXTRACTED`
- _play_def() `EXTRACTED`
- _play_def() `EXTRACTED`
- _iter_leaf_task_defs() `EXTRACTED`
- _make_play() `EXTRACTED`
- collect_tags() `EXTRACTED`
- _make_play() `EXTRACTED`
- _count_tasks() `EXTRACTED`
- _build_name_index() `EXTRACTED`
- _play() `EXTRACTED`
- _build_definitions() `EXTRACTED`
- _play_def() `EXTRACTED`
- count_leaf_tasks() `EXTRACTED`
- _roles_referenced() `EXTRACTED`

### uses
- [RunState](RunState.md) `INFERRED`
- [PtyStreamParser](PtyStreamParser.md) `INFERRED`
- StreamPhase `INFERRED`
- JsonLineStream `INFERRED`
- [TreeProjection](TreeProjection.md) `INFERRED`
- TestPtyStreamParserStderrLineEmission `INFERRED`
- PreParseResult `INFERRED`
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

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*