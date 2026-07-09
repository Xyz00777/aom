# Event Source Adapters

> 11 nodes · cohesion 0.22

## Key Concepts

- **._load_plan()** (7 connections) — `src/ansible_aom/tui/screens/rerun.py`
- **_resolve_target_session()** (6 connections) — `src/ansible_aom/tui/screens/rerun.py`
- **rerun.py** (4 connections) — `src/ansible_aom/tui/screens/rerun.py`
- **.__init__()** (4 connections) — `src/ansible_aom/tui/screens/rerun.py`
- **_resolve_host_set()** (4 connections) — `src/ansible_aom/tui/screens/rerun.py`
- **Path** (2 connections)
- **Re-run dialog for AOM TUI.  Triggered by Shift+R / R after a playbook finishes.** (1 connections) — `src/ansible_aom/tui/screens/rerun.py`
- **Build the dialog from a recorded session on disk.          Args:             sta** (1 connections) — `src/ansible_aom/tui/screens/rerun.py`
- **Read session data and compute the planned command line.** (1 connections) — `src/ansible_aom/tui/screens/rerun.py`
- **Return ``(session_id, error_message)`` for the requested rerun target.      Mirr** (1 connections) — `src/ansible_aom/tui/screens/rerun.py`
- **Compose the host set the rerun will target.      Args:         session: Loaded s** (1 connections) — `src/ansible_aom/tui/screens/rerun.py`

## Relationships

- [Session Replay Round Trip](Session_Replay_Round_Trip.md) (3 shared connections)
- [Total Task Counting](Total_Task_Counting.md) (1 shared connections)
- [PTY Buffer Stall Handling](PTY_Buffer_Stall_Handling.md) (1 shared connections)
- [KeyAction TypedDict](KeyAction_TypedDict.md) (1 shared connections)
- [Compact Renderer Formatters](Compact_Renderer_Formatters.md) (1 shared connections)
- [Status Bar Widget](Status_Bar_Widget.md) (1 shared connections)

## Source Files

- `src/ansible_aom/tui/screens/rerun.py`

## Audit Trail

- EXTRACTED: 27 (84%)
- INFERRED: 5 (16%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*