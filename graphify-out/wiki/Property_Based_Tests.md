# Property Based Tests

> 42 nodes · cohesion 0.05

## Key Concepts

- **DebugPanel** (21 connections) — `src/ansible_aom/tui/widgets/debug_panel.py`
- **.action_toggle_debug()** (3 connections) — `src/ansible_aom/tui/app.py`
- **.update_debug_from_summary()** (3 connections) — `src/ansible_aom/tui/screens/main.py`
- **.render()** (3 connections) — `src/ansible_aom/tui/widgets/debug_panel.py`
- **debug_panel.py** (2 connections) — `src/ansible_aom/tui/widgets/debug_panel.py`
- **.get_debug_summary()** (2 connections) — `src/ansible_aom/tui/widgets/debug_panel.py`
- **.__init__()** (2 connections) — `src/ansible_aom/tui/widgets/debug_panel.py`
- **.set_callback_status()** (2 connections) — `src/ansible_aom/tui/widgets/debug_panel.py`
- **.set_command()** (2 connections) — `src/ansible_aom/tui/widgets/debug_panel.py`
- **.set_env_overrides()** (2 connections) — `src/ansible_aom/tui/widgets/debug_panel.py`
- **.set_event_count()** (2 connections) — `src/ansible_aom/tui/widgets/debug_panel.py`
- **.set_event_latency()** (2 connections) — `src/ansible_aom/tui/widgets/debug_panel.py`
- **.set_memory_usage()** (2 connections) — `src/ansible_aom/tui/widgets/debug_panel.py`
- **.set_parsing_errors()** (2 connections) — `src/ansible_aom/tui/widgets/debug_panel.py`
- **.set_pending_events()** (2 connections) — `src/ansible_aom/tui/widgets/debug_panel.py`
- **.set_renderer_fps()** (2 connections) — `src/ansible_aom/tui/widgets/debug_panel.py`
- **.set_state_tree()** (2 connections) — `src/ansible_aom/tui/widgets/debug_panel.py`
- **.set_subprocess_pid()** (2 connections) — `src/ansible_aom/tui/widgets/debug_panel.py`
- **.set_timing_stats()** (2 connections) — `src/ansible_aom/tui/widgets/debug_panel.py`
- **.toggle_visibility()** (2 connections) — `src/ansible_aom/tui/widgets/debug_panel.py`
- **Toggle debug panel visibility.          Per SPECIFICATION.md Section 7.5, toggle** (1 connections) — `src/ansible_aom/tui/app.py`
- **Update DebugPanel from debug summary dict.** (1 connections) — `src/ansible_aom/tui/screens/main.py`
- **Text** (1 connections)
- **Widget** (1 connections)
- **Debug panel widget for AOM TUI.  Shows internal state for debugging. See SPECIFI** (1 connections) — `src/ansible_aom/tui/widgets/debug_panel.py`
- *... and 17 more nodes in this community*

## Relationships

- [Session Recording Tests](Session_Recording_Tests.md) (2 shared connections)

## Source Files

- `src/ansible_aom/tui/app.py`
- `src/ansible_aom/tui/screens/main.py`
- `src/ansible_aom/tui/widgets/debug_panel.py`

## Audit Trail

- EXTRACTED: 80 (95%)
- INFERRED: 4 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*