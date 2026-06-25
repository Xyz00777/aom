# Event Log Emission

> 46 nodes · cohesion 0.06

## Key Concepts

- **._emit_event_log()** (18 connections) — `src/ansible_aom/compact/renderer.py`
- **.print_log()** (10 connections) — `src/ansible_aom/compact/renderer.py`
- **._emit_previous_task_summary()** (8 connections) — `src/ansible_aom/compact/renderer.py`
- **._announce_task()** (7 connections) — `src/ansible_aom/compact/renderer.py`
- **._bump_task_counters()** (7 connections) — `src/ansible_aom/compact/renderer.py`
- **._flush_pending_skips()** (7 connections) — `src/ansible_aom/compact/renderer.py`
- **._format_loop_item_line()** (6 connections) — `src/ansible_aom/compact/renderer.py`
- **._task_dict()** (6 connections) — `src/ansible_aom/compact/renderer.py`
- **._count_completed_task()** (5 connections) — `src/ansible_aom/compact/renderer.py`
- **._enter_terminal_event()** (5 connections) — `src/ansible_aom/compact/renderer.py`
- **._inline_duration_suffix()** (5 connections) — `src/ansible_aom/compact/renderer.py`
- **.set_definitions()** (5 connections) — `src/ansible_aom/compact/renderer.py`
- **.update_state()** (5 connections) — `src/ansible_aom/compact/renderer.py`
- **_truncate_msg()** (4 connections) — `src/ansible_aom/compact/format.py`
- **.add_warning()** (4 connections) — `src/ansible_aom/compact/renderer.py`
- **._build_status_suffix()** (4 connections) — `src/ansible_aom/compact/renderer.py`
- **._format_duration()** (4 connections) — `src/ansible_aom/compact/renderer.py`
- **._loop_item_lines()** (4 connections) — `src/ansible_aom/compact/renderer.py`
- **._maybe_emit_pause_seconds_hint()** (4 connections) — `src/ansible_aom/compact/renderer.py`
- **._reconcile_completed_tasks()** (4 connections) — `src/ansible_aom/compact/renderer.py`
- **._record_running_start()** (4 connections) — `src/ansible_aom/compact/renderer.py`
- **._event_time()** (3 connections) — `src/ansible_aom/compact/renderer.py`
- **._hosts_dict()** (3 connections) — `src/ansible_aom/compact/renderer.py`
- **Cap a JSONL ``msg`` field for live display.      The suffix includes the origina** (1 connections) — `src/ansible_aom/compact/format.py`
- **Parse ``_timestamp`` from a JSONL event into a Unix float.          Returns ``No** (1 connections) — `src/ansible_aom/compact/renderer.py`
- *... and 21 more nodes in this community*

## Relationships

- [[Compact Renderer Implementation]] (22 shared connections)
- [[Compact Renderer Formatters]] (7 shared connections)
- [[Panel Refresh Snapshot]] (3 shared connections)
- [[Event Hide Filter Logic]] (2 shared connections)
- [[Color ASCII Fallback]] (1 shared connections)
- [[Host Result Hide Filter]] (1 shared connections)
- [[Preflight Summary Rendering]] (1 shared connections)

## Source Files

- `src/ansible_aom/compact/format.py`
- `src/ansible_aom/compact/renderer.py`

## Audit Trail

- EXTRACTED: 140 (90%)
- INFERRED: 15 (10%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*