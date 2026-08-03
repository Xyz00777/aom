# TestHideStateCompactPlumbing

> 12 nodes · cohesion 0.17

## Key Concepts

- **TestHideStateCompactPlumbing** (17 connections) — `tests/unit/test_cli.py`
- **.test_capture_verbose_propagates_to_renderer()** (2 connections) — `tests/unit/test_cli.py`
- **.test_hide_state_default_propagates_empty_list()** (2 connections) — `tests/unit/test_cli.py`
- **.test_hide_state_propagates_multiple_values()** (2 connections) — `tests/unit/test_cli.py`
- **.test_hide_state_propagates_to_renderer()** (2 connections) — `tests/unit/test_cli.py`
- **.test_no_failed_hint_propagates_to_renderer()** (2 connections) — `tests/unit/test_cli.py`
- **--hide-state propagates from CLI to create_renderer/run_playbook.** (1 connections) — `tests/unit/test_cli.py`
- **aom --hide-state ok playbook.yml → create_renderer gets hide_states=["ok"].** (1 connections) — `tests/unit/test_cli.py`
- **--hide-state ok --hide-state skipped → hide_states=["ok", "skipped"].** (1 connections) — `tests/unit/test_cli.py`
- **No --hide-state flag → create_renderer gets hide_states=[].** (1 connections) — `tests/unit/test_cli.py`
- **--capture-verbose should reach compact renderer creation.** (1 connections) — `tests/unit/test_cli.py`
- **--no-failed-hint should disable failed hints in compact mode only.** (1 connections) — `tests/unit/test_cli.py`

## Relationships

- [HostRunState](HostRunState.md) (6 shared connections)
- [TestWarningVisibilityCompactPlumbing](TestWarningVisibilityCompactPlumbing.md) (3 shared connections)
- [CompactRenderer](CompactRenderer.md) (1 shared connections)
- [RunState](RunState.md) (1 shared connections)

## Source Files

- `tests/unit/test_cli.py`

## Audit Trail

- EXTRACTED: 26 (79%)
- INFERRED: 7 (21%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*