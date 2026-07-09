# Diagnostics CLI Wiring

> 19 nodes · cohesion 0.11

## Key Concepts

- **StatusBar** (25 connections) — `src/ansible_aom/tui/widgets/status_bar.py`
- **.update_play_name()** (4 connections) — `src/ansible_aom/tui/screens/main.py`
- **.__init__()** (3 connections) — `src/ansible_aom/tui/widgets/status_bar.py`
- **.set_current_task()** (2 connections) — `src/ansible_aom/tui/widgets/status_bar.py`
- **.set_host_count()** (2 connections) — `src/ansible_aom/tui/widgets/status_bar.py`
- **.set_memory_usage()** (2 connections) — `src/ansible_aom/tui/widgets/status_bar.py`
- **.set_playbook_name()** (2 connections) — `src/ansible_aom/tui/widgets/status_bar.py`
- **.set_subprocess_pid()** (2 connections) — `src/ansible_aom/tui/widgets/status_bar.py`
- **.set_task_progress()** (2 connections) — `src/ansible_aom/tui/widgets/status_bar.py`
- **Update play name on SummaryPanel and playbook name on StatusBar.** (1 connections) — `src/ansible_aom/tui/screens/main.py`
- **Widget** (1 connections)
- **Set memory usage.          Args:             rss_mb: Resident set size in MB** (1 connections) — `src/ansible_aom/tui/widgets/status_bar.py`
- **Set the subprocess PID.          Args:             pid: The subprocess PID (or N** (1 connections) — `src/ansible_aom/tui/widgets/status_bar.py`
- **Configurable status bar showing playbook name, time, progress.** (1 connections) — `src/ansible_aom/tui/widgets/status_bar.py`
- **Initialize the status bar widget.          Args:             config: Status bar** (1 connections) — `src/ansible_aom/tui/widgets/status_bar.py`
- **Set the playbook name.          Args:             name: The playbook file name** (1 connections) — `src/ansible_aom/tui/widgets/status_bar.py`
- **Set task progress.          Args:             completed: Number of completed tas** (1 connections) — `src/ansible_aom/tui/widgets/status_bar.py`
- **Set the current task name.          Args:             task: The current task nam** (1 connections) — `src/ansible_aom/tui/widgets/status_bar.py`
- **Set host progress count.          Args:             completed: Number of complet** (1 connections) — `src/ansible_aom/tui/widgets/status_bar.py`

## Relationships

- [Non-Interactive Renderers](Non-Interactive_Renderers.md) (5 shared connections)
- [Session Recording Tests](Session_Recording_Tests.md) (4 shared connections)
- [Compact Display Logic](Compact_Display_Logic.md) (3 shared connections)
- [Run State Summary Panel](Run_State_Summary_Panel.md) (2 shared connections)
- [Community 605](Community_605.md) (2 shared connections)
- [Community 684](Community_684.md) (1 shared connections)
- [Community 477](Community_477.md) (1 shared connections)

## Source Files

- `src/ansible_aom/tui/screens/main.py`
- `src/ansible_aom/tui/widgets/status_bar.py`

## Audit Trail

- EXTRACTED: 44 (81%)
- INFERRED: 10 (19%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*