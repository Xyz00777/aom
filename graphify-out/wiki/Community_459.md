# Community 459

> 10 nodes · cohesion 0.20

## Key Concepts

- **TestKeybindingContextsComplete** (8 connections) — `tests/tui/test_keybindings.py`
- **.test_global_context_keys_work_everywhere()** (3 connections) — `tests/tui/test_keybindings.py`
- **.test_log_context_keys_only_for_log()** (3 connections) — `tests/tui/test_keybindings.py`
- **.test_post_run_keys_only_after_completion()** (3 connections) — `tests/tui/test_keybindings.py`
- **.test_tree_context_keys_dont_work_globally()** (3 connections) — `tests/tui/test_keybindings.py`
- **Complete coverage of keybinding contexts - TC-361 through TC-364.** (1 connections) — `tests/tui/test_keybindings.py`
- **TC-361: Keys like j/k/arrow only work when tree focused.** (1 connections) — `tests/tui/test_keybindings.py`
- **TC-362: Search keys only work when log focused.** (1 connections) — `tests/tui/test_keybindings.py`
- **TC-363: Rerun keys only work after playbook completion.** (1 connections) — `tests/tui/test_keybindings.py`
- **TC-364: Global keys work from any panel.** (1 connections) — `tests/tui/test_keybindings.py`

## Relationships

- [Runner Event Batching](Runner_Event_Batching.md) (4 shared connections)
- [State Machine Invariants](State_Machine_Invariants.md) (2 shared connections)
- [Warning Color Formatting](Warning_Color_Formatting.md) (1 shared connections)

## Source Files

- `tests/tui/test_keybindings.py`

## Audit Trail

- EXTRACTED: 19 (76%)
- INFERRED: 6 (24%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*