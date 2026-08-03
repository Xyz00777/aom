# HostRunState

> 341 nodes · cohesion 0.01

## Key Concepts

- **HostRunState** (285 connections) — `src/ansible_aom/core/models.py`
- **Status** (273 connections) — `src/ansible_aom/core/models.py`
- **PlayRunState** (252 connections) — `src/ansible_aom/core/models.py`
- **TaskRunState** (244 connections) — `src/ansible_aom/core/models.py`
- **models.py** (86 connections) — `src/ansible_aom/core/models.py`
- **JsonRenderer** (76 connections) — `src/ansible_aom/formats/json.py`
- **test_cli.py** (34 connections) — `tests/unit/test_cli.py`
- **TestHideStateFlag** (28 connections) — `tests/unit/test_cli.py`
- **test_compact_renderer.py** (22 connections) — `tests/integration/test_compact_renderer.py`
- **TestPlayRunState** (22 connections) — `tests/unit/test_models.py`
- **TestTaskRunState** (20 connections) — `tests/unit/test_models.py`
- **determine_exit_code()** (19 connections) — `src/ansible_aom/core/exit_code.py`
- **TestRendererProtocol** (17 connections) — `tests/unit/test_cli.py`
- **format_failure_recap()** (16 connections) — `src/ansible_aom/compact/format.py`
- **TestDisplayClass** (16 connections) — `tests/integration/test_compact_renderer.py`
- **TestNonTTYBehavior** (16 connections) — `tests/integration/test_compact_renderer.py`
- **TestRefreshStrategy** (16 connections) — `tests/integration/test_compact_renderer.py`
- **TestTerminalSizeCheck** (16 connections) — `tests/integration/test_compact_renderer.py`
- **TestPackageIdentity** (16 connections) — `tests/unit/test_cli.py`
- **TestRendererFactory** (16 connections) — `tests/unit/test_cli.py`
- **test_tree_upcoming_plays.py** (15 connections) — `tests/compact/test_tree_upcoming_plays.py`
- **TestCompactRendererHandleCompletion** (15 connections) — `tests/integration/test_compact_renderer.py`
- **TestCompactRendererProtocol** (15 connections) — `tests/integration/test_compact_renderer.py`
- **TestExitCodes** (15 connections) — `tests/integration/test_compact_renderer.py`
- **TestYesFlag** (15 connections) — `tests/unit/test_cli.py`
- *... and 316 more nodes in this community*

## Relationships

- [RunState](RunState.md) (208 shared connections)
- [TaskDefinition](TaskDefinition.md) (105 shared connections)
- [WarningEntry](WarningEntry.md) (105 shared connections)
- [CompactRenderer](CompactRenderer.md) (69 shared connections)
- [PlayDefinition](PlayDefinition.md) (62 shared connections)
- [.from_run_state](from_run_state.md) (59 shared connections)
- [WarningType](WarningType.md) (44 shared connections)
- [create_parser](create_parser.md) (34 shared connections)
- [StreamPhase](StreamPhase.md) (28 shared connections)
- [json.py](json.py.md) (27 shared connections)
- [TreeProjection](TreeProjection.md) (26 shared connections)
- [Display](Display.md) (26 shared connections)

## Source Files

- `src/ansible_aom/compact/exit_code.py`
- `src/ansible_aom/compact/format.py`
- `src/ansible_aom/core/exit_code.py`
- `src/ansible_aom/core/models.py`
- `src/ansible_aom/core/parity.py`
- `src/ansible_aom/core/tree_projection.py`
- `src/ansible_aom/formats/json.py`
- `tests/compact/test_completion_recap.py`
- `tests/compact/test_spinner_animation.py`
- `tests/compact/test_status_bar_colors.py`
- `tests/compact/test_task_progress.py`
- `tests/compact/test_tree_projection_lifecycle.py`
- `tests/compact/test_tree_render.py`
- `tests/compact/test_tree_upcoming_plays.py`
- `tests/compact/test_tree_upcoming_tasks.py`
- `tests/integration/test_compact_renderer.py`
- `tests/integration/test_invariants_session_roundtrip.py`
- `tests/tui/test_panels.py`
- `tests/unit/test_cli.py`
- `tests/unit/test_json_renderer.py`

## Audit Trail

- EXTRACTED: 1383 (52%)
- INFERRED: 1284 (48%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*