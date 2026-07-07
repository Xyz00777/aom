# Main TUI Screen

> 13 nodes · cohesion 0.10

## Key Concepts

- **MainScreen** (24 connections) — `src/ansible_aom/tui/screens/main.py`
- **.update_from_state()** (5 connections) — `src/ansible_aom/tui/screens/main.py`
- **._update_elapsed_from_start()** (4 connections) — `src/ansible_aom/tui/screens/main.py`
- **.on_mount()** (3 connections) — `src/ansible_aom/tui/app.py`
- **main.py** (2 connections) — `src/ansible_aom/tui/screens/main.py`
- **.update_debug_from_summary()** (2 connections) — `src/ansible_aom/tui/screens/main.py`
- **.update_elapsed()** (2 connections) — `src/ansible_aom/tui/screens/main.py`
- **.update_hosts_progress()** (2 connections) — `src/ansible_aom/tui/screens/main.py`
- **.update_log_line()** (2 connections) — `src/ansible_aom/tui/screens/main.py`
- **.update_play_name()** (2 connections) — `src/ansible_aom/tui/screens/main.py`
- **.update_tasks_progress()** (2 connections) — `src/ansible_aom/tui/screens/main.py`
- **Main TUI screen for AOM.  See SPECIFICATION.md Section 4.2 for layout.** (1 connections) — `src/ansible_aom/tui/screens/main.py`
- **Update elapsed time on both panels from start time.** (1 connections) — `src/ansible_aom/tui/screens/main.py`

## Relationships

- [[Task Definition Live Refresh]] (6 shared connections)
- [[AOM TUI Application]] (3 shared connections)
- [[TUI Keybindings Config]] (1 shared connections)
- [[Log Panel Widget]] (1 shared connections)
- [[Play Definition Tree Population]] (1 shared connections)

## Source Files

- `src/ansible_aom/tui/app.py`
- `src/ansible_aom/tui/screens/main.py`

## Audit Trail

- EXTRACTED: 39 (75%)
- INFERRED: 13 (25%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*