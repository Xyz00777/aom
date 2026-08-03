# Status

> God node · 291 connections · `src/ansible_aom/core/models.py`

**Community:** [Role Group Task Models](Role_Group_Task_Models.md)

## Connections by Relation

### contains
- models.py `EXTRACTED`

### imports
- renderer.py `EXTRACTED`
- json.py `EXTRACTED`
- run_state.py `EXTRACTED`
- format.py `EXTRACTED`
- [tree.py](tree.py.md) `EXTRACTED`
- tree_projection.py `EXTRACTED`
- icons.py `EXTRACTED`
- parity.py `EXTRACTED`
- core/exit_code.py `EXTRACTED`

### indirect_call
- test_host_terminal_states_are_disjoint() `INFERRED`
- .test_status_enum_has_eight_values() `INFERRED`
- .test_status_enum_values() `INFERRED`

### inherits
- Enum `EXTRACTED`

### rationale_for
- Task/host execution status. `EXTRACTED`

### references
- get_status_icon() `EXTRACTED`
- _state_with_play() `EXTRACTED`
- get_status_color() `EXTRACTED`
- get_status_icon_ascii() `EXTRACTED`
- _effective_status() `EXTRACTED`
- ._state_with() `EXTRACTED`
- _shape() `EXTRACTED`
- _bump() `EXTRACTED`
- ._worst_status_of() `EXTRACTED`

### uses
- [RunState](RunState.md) `INFERRED`
- [CompactRenderer](CompactRenderer.md) `INFERRED`
- JsonRenderer `INFERRED`
- TreeProjection `INFERRED`
- TestPtyStreamParserStderrLineEmission `INFERRED`
- TreeLine `INFERRED`
- TestJsonLineStreamBasics `INFERRED`
- TestHideStateFlag `INFERRED`
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
- TestPlayDefinition `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*