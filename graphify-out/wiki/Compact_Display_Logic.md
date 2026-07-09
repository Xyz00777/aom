# Compact Display Logic

> 23 nodes · cohesion 0.09

## Key Concepts

- **SummaryPanel** (20 connections) — `src/ansible_aom/tui/widgets/summary_panel.py`
- **.update_elapsed()** (4 connections) — `src/ansible_aom/tui/screens/main.py`
- **.update_tasks_progress()** (4 connections) — `src/ansible_aom/tui/screens/main.py`
- **.get_status_icon()** (3 connections) — `src/ansible_aom/tui/widgets/summary_panel.py`
- **summary_panel.py** (2 connections) — `src/ansible_aom/tui/widgets/summary_panel.py`
- **.format_host_status_line()** (2 connections) — `src/ansible_aom/tui/widgets/summary_panel.py`
- **.__init__()** (2 connections) — `src/ansible_aom/tui/widgets/summary_panel.py`
- **.set_elapsed_time()** (2 connections) — `src/ansible_aom/tui/widgets/summary_panel.py`
- **.set_hosts_progress()** (2 connections) — `src/ansible_aom/tui/widgets/summary_panel.py`
- **.set_play_name()** (2 connections) — `src/ansible_aom/tui/widgets/summary_panel.py`
- **.set_tasks_progress()** (2 connections) — `src/ansible_aom/tui/widgets/summary_panel.py`
- **Update tasks progress on SummaryPanel and StatusBar.** (1 connections) — `src/ansible_aom/tui/screens/main.py`
- **Update elapsed time on SummaryPanel and StatusBar.** (1 connections) — `src/ansible_aom/tui/screens/main.py`
- **Widget** (1 connections)
- **Summary panel widget for AOM TUI.  Play-level overview with stats. See SPECIFICA** (1 connections) — `src/ansible_aom/tui/widgets/summary_panel.py`
- **Format a host status line with icons.          Args:             hostname: The h** (1 connections) — `src/ansible_aom/tui/widgets/summary_panel.py`
- **Get the icon for a status.          Args:             status: The status to get** (1 connections) — `src/ansible_aom/tui/widgets/summary_panel.py`
- **Summary panel showing play-level stats.** (1 connections) — `src/ansible_aom/tui/widgets/summary_panel.py`
- **Initialize the summary panel widget.          Args:             name: Widget nam** (1 connections) — `src/ansible_aom/tui/widgets/summary_panel.py`
- **Set the current play name.          Args:             name: The play name** (1 connections) — `src/ansible_aom/tui/widgets/summary_panel.py`
- **Set hosts progress.          Args:             completed: Number of completed ho** (1 connections) — `src/ansible_aom/tui/widgets/summary_panel.py`
- **Set tasks progress.          Args:             completed: Number of completed ta** (1 connections) — `src/ansible_aom/tui/widgets/summary_panel.py`
- **Set elapsed time in seconds.          Args:             seconds: Elapsed time in** (1 connections) — `src/ansible_aom/tui/widgets/summary_panel.py`

## Relationships

- [Session Recording Tests](Session_Recording_Tests.md) (5 shared connections)
- [Diagnostics CLI Wiring](Diagnostics_CLI_Wiring.md) (3 shared connections)
- [Compact Renderer Integration Tests](Compact_Renderer_Integration_Tests.md) (2 shared connections)
- [Community 477](Community_477.md) (2 shared connections)
- [Community 684](Community_684.md) (1 shared connections)

## Source Files

- `src/ansible_aom/tui/screens/main.py`
- `src/ansible_aom/tui/widgets/summary_panel.py`

## Audit Trail

- EXTRACTED: 45 (79%)
- INFERRED: 12 (21%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*