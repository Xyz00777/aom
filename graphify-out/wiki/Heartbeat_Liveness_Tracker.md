# Heartbeat Liveness Tracker

> 41 nodes · cohesion 0.07

## Key Concepts

- **._emit_event_log()** (22 connections) — `src/ansible_aom/compact/renderer.py`
- **.print_log()** (10 connections) — `src/ansible_aom/compact/renderer.py`
- **._announce_task()** (9 connections) — `src/ansible_aom/compact/renderer.py`
- **._emit_previous_task_summary()** (8 connections) — `src/ansible_aom/compact/renderer.py`
- **._flush_pending_skips()** (7 connections) — `src/ansible_aom/compact/renderer.py`
- **._format_loop_item_line()** (7 connections) — `src/ansible_aom/compact/renderer.py`
- **._inline_duration_suffix()** (6 connections) — `src/ansible_aom/compact/renderer.py`
- **renderer.py** (5 connections) — `src/ansible_aom/compact/renderer.py`
- **.add()** (5 connections) — `src/ansible_aom/compact/renderer.py`
- **.add_warning()** (5 connections) — `src/ansible_aom/compact/renderer.py`
- **._enter_terminal_event()** (5 connections) — `src/ansible_aom/compact/renderer.py`
- **._format_duration()** (5 connections) — `src/ansible_aom/compact/renderer.py`
- **._maybe_emit_pause_seconds_hint()** (5 connections) — `src/ansible_aom/compact/renderer.py`
- **.set_definitions()** (5 connections) — `src/ansible_aom/compact/renderer.py`
- **_extract_error_msg()** (5 connections) — `src/ansible_aom/compact/renderer.py`
- **is_async_poll_payload()** (5 connections) — `src/ansible_aom/core/_async_poll.py`
- **._hosts_dict()** (4 connections) — `src/ansible_aom/compact/renderer.py`
- **._loop_item_lines()** (4 connections) — `src/ansible_aom/compact/renderer.py`
- **_first_line()** (3 connections) — `src/ansible_aom/compact/renderer.py`
- **format_duration_decimal()** (3 connections) — `src/ansible_aom/core/duration.py`
- **_async_poll.py** (2 connections) — `src/ansible_aom/core/_async_poll.py`
- **Compact renderer — Rich Live lifecycle and per-event log emission.  Pure formatt** (1 connections) — `src/ansible_aom/compact/renderer.py`
- **Surface a one-line hint when a pause-with-seconds task starts.          ``ansibl** (1 connections) — `src/ansible_aom/compact/renderer.py`
- **Compact human duration: ``0.4s`` / ``12.3s`` / ``1m23s`` / ``1h02m``.          T** (1 connections) — `src/ansible_aom/compact/renderer.py`
- **Print a one-line summary of the task that just finished.          Triggered righ** (1 connections) — `src/ansible_aom/compact/renderer.py`
- *... and 16 more nodes in this community*

## Relationships

- [App Configuration Settings](App_Configuration_Settings.md) (15 shared connections)
- [Renderer Set Definitions](Renderer_Set_Definitions.md) (6 shared connections)
- [Status Icon Animation Tests](Status_Icon_Animation_Tests.md) (5 shared connections)
- [Crash Recovery Panels](Crash_Recovery_Panels.md) (4 shared connections)
- [Inspect Debug Diagnostics](Inspect_Debug_Diagnostics.md) (2 shared connections)
- [Host Result Hide Filter](Host_Result_Hide_Filter.md) (2 shared connections)
- [Community 560](Community_560.md) (2 shared connections)
- [StatusBarConfig Model](StatusBarConfig_Model.md) (1 shared connections)
- [Parser Edge Cases](Parser_Edge_Cases.md) (1 shared connections)
- [TUI Keybindings Config](TUI_Keybindings_Config.md) (1 shared connections)
- [Host Overview Table](Host_Overview_Table.md) (1 shared connections)
- [Community 503](Community_503.md) (1 shared connections)

## Source Files

- `src/ansible_aom/compact/renderer.py`
- `src/ansible_aom/core/_async_poll.py`
- `src/ansible_aom/core/duration.py`

## Audit Trail

- EXTRACTED: 133 (89%)
- INFERRED: 17 (11%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*