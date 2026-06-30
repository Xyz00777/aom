# Status Bar Elements

> 20 nodes · cohesion 0.10

## Key Concepts

- **TestStatusBarAvailableElements** (19 connections) — `tests/tui/test_panels.py`
- **.test_current_task_displays_correctly()** (2 connections) — `tests/tui/test_panels.py`
- **.test_elapsed_time_displays_correctly()** (2 connections) — `tests/tui/test_panels.py`
- **.test_host_count_displays_correctly()** (2 connections) — `tests/tui/test_panels.py`
- **.test_memory_usage_displays_correctly()** (2 connections) — `tests/tui/test_panels.py`
- **.test_memory_usage_not_available()** (2 connections) — `tests/tui/test_panels.py`
- **.test_playbook_name_displays_correctly()** (2 connections) — `tests/tui/test_panels.py`
- **.test_subprocess_pid_displays_correctly()** (2 connections) — `tests/tui/test_panels.py`
- **.test_subprocess_pid_not_available()** (2 connections) — `tests/tui/test_panels.py`
- **.test_task_progress_displays_correctly()** (2 connections) — `tests/tui/test_panels.py`
- **Tests for available status bar elements - TC-291.** (1 connections) — `tests/tui/test_panels.py`
- **TC-291: playbook_name element renders with correct data.** (1 connections) — `tests/tui/test_panels.py`
- **TC-291: elapsed_time element renders HH:MM:SS.** (1 connections) — `tests/tui/test_panels.py`
- **TC-291: task_progress element shows completed/total.** (1 connections) — `tests/tui/test_panels.py`
- **TC-291: current_task element shows task name.** (1 connections) — `tests/tui/test_panels.py`
- **TC-291: host_count element shows completed/total hosts.** (1 connections) — `tests/tui/test_panels.py`
- **TC-291: subprocess_pid element shows PID when available.** (1 connections) — `tests/tui/test_panels.py`
- **TC-291 edge case: PID not available shows N/A or hides.** (1 connections) — `tests/tui/test_panels.py`
- **TC-291: memory_usage element shows RSS/VSZ.** (1 connections) — `tests/tui/test_panels.py`
- **TC-291 edge case: Memory unavailable shows N/A.** (1 connections) — `tests/tui/test_panels.py`

## Relationships

- [[Status Bar Warning Panels]] (3 shared connections)
- [[Run State Completion Recap]] (3 shared connections)
- [[Role Group Task Models]] (2 shared connections)
- [[Run State Summary Panel]] (1 shared connections)

## Source Files

- `tests/tui/test_panels.py`

## Audit Trail

- EXTRACTED: 39 (83%)
- INFERRED: 8 (17%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*