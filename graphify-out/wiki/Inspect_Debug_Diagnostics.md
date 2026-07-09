# Inspect Debug Diagnostics

> 21 nodes · cohesion 0.11

## Key Concepts

- **_BoundedSet** (16 connections) — `src/ansible_aom/compact/renderer.py`
- **.__init__()** (10 connections) — `src/ansible_aom/compact/renderer.py`
- **TestColorEnabled** (10 connections) — `tests/compact/test_status_bar_colors.py`
- **.start()** (9 connections) — `src/ansible_aom/compact/renderer.py`
- **_color_enabled()** (6 connections) — `src/ansible_aom/compact/format.py`
- **.stop()** (6 connections) — `src/ansible_aom/compact/renderer.py`
- **.handle_interactive_prompt()** (4 connections) — `src/ansible_aom/compact/renderer.py`
- **.handle_password_prompt()** (4 connections) — `src/ansible_aom/compact/renderer.py`
- **.__init__()** (2 connections) — `src/ansible_aom/compact/renderer.py`
- **.test_off_when_no_color_set_even_for_tty()** (2 connections) — `tests/compact/test_status_bar_colors.py`
- **.test_off_when_not_a_tty()** (2 connections) — `tests/compact/test_status_bar_colors.py`
- **.test_on_when_tty_and_no_color_unset()** (2 connections) — `tests/compact/test_status_bar_colors.py`
- **True if we should emit SGR codes — TTY only, NO_COLOR honored.** (1 connections) — `src/ansible_aom/compact/format.py`
- **set** (1 connections)
- **Stop rendering and clean up resources.          Restores terminal state, flushes** (1 connections) — `src/ansible_aom/compact/renderer.py`
- **Initialize the compact renderer.          Args:             is_tty: Whether stdo** (1 connections) — `src/ansible_aom/compact/renderer.py`
- **Start rendering a playbook run.          Initializes the RunState, starts the Ri** (1 connections) — `src/ansible_aom/compact/renderer.py`
- **Surface a pause / vars_prompt-style prompt and capture one line.          Mirror** (1 connections) — `src/ansible_aom/compact/renderer.py`
- **Handle a password prompt.          Stops the Rich Live display, delegates to the** (1 connections) — `src/ansible_aom/compact/renderer.py`
- **A ``set`` that drops itself when it exceeds a cap on insert.      R14: the compa** (1 connections) — `src/ansible_aom/compact/renderer.py`
- **The gating predicate honours both the TTY flag and ``NO_COLOR``.** (1 connections) — `tests/compact/test_status_bar_colors.py`

## Relationships

- [App Configuration Settings](App_Configuration_Settings.md) (6 shared connections)
- [Compact Renderer Integration Tests](Compact_Renderer_Integration_Tests.md) (4 shared connections)
- [Warning Classification Tests](Warning_Classification_Tests.md) (4 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (3 shared connections)
- [Renderer Set Definitions](Renderer_Set_Definitions.md) (2 shared connections)
- [Heartbeat Liveness Tracker](Heartbeat_Liveness_Tracker.md) (2 shared connections)
- [Status Icon Animation Tests](Status_Icon_Animation_Tests.md) (2 shared connections)
- [Status Icon Unicode Mapping](Status_Icon_Unicode_Mapping.md) (2 shared connections)
- [Renderer Event Protocol](Renderer_Event_Protocol.md) (1 shared connections)
- [JSON Renderer](JSON_Renderer.md) (1 shared connections)
- [Session List View](Session_List_View.md) (1 shared connections)
- [Main TUI Screen](Main_TUI_Screen.md) (1 shared connections)

## Source Files

- `src/ansible_aom/compact/format.py`
- `src/ansible_aom/compact/renderer.py`
- `tests/compact/test_status_bar_colors.py`

## Audit Trail

- EXTRACTED: 51 (62%)
- INFERRED: 31 (38%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*