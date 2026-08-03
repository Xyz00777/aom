# .update

> 22 nodes · cohesion 0.13

## Key Concepts

- **.update()** (9 connections) — `src/ansible_aom/compact/display.py`
- **._write_frame()** (9 connections) — `src/ansible_aom/compact/display.py`
- **.print_log()** (7 connections) — `src/ansible_aom/compact/display.py`
- **._rewind_status()** (7 connections) — `src/ansible_aom/compact/display.py`
- **._drain_pending_logs()** (6 connections) — `src/ansible_aom/compact/display.py`
- **_terminal_width()** (5 connections) — `src/ansible_aom/compact/display.py`
- **.clear()** (4 connections) — `src/ansible_aom/compact/display.py`
- **._log_flush_due()** (4 connections) — `src/ansible_aom/compact/display.py`
- **.stop()** (4 connections) — `src/ansible_aom/compact/display.py`
- **._current_size()** (3 connections) — `src/ansible_aom/compact/display.py`
- **.flush_logs()** (3 connections) — `src/ansible_aom/compact/display.py`
- **One synchronized frame: pending logs, then the status block.** (2 connections) — `src/ansible_aom/compact/display.py`
- **Erase the status block and release the terminal.** (1 connections) — `src/ansible_aom/compact/display.py`
- **Redraw the status block with new content.          Updates within _THROTTLE_INTE** (1 connections) — `src/ansible_aom/compact/display.py`
- **Queue a log line for printing above the status block.          Leading-edge batc** (1 connections) — `src/ansible_aom/compact/display.py`
- **Drain any buffered log lines in one synchronized frame.          Called by the r** (1 connections) — `src/ansible_aom/compact/display.py`
- **True when the flush window has elapsed (or never started).** (1 connections) — `src/ansible_aom/compact/display.py`
- **Take the queued log lines (each already newline-terminated).** (1 connections) — `src/ansible_aom/compact/display.py`
- **Erase the status content (but leave the display running).** (1 connections) — `src/ansible_aom/compact/display.py`
- **Resolve (cols, rows) — the test override or the live kernel value.          ``sh** (1 connections) — `src/ansible_aom/compact/display.py`
- **Cursor sequence to move back to the start of the status block.          After wr** (1 connections) — `src/ansible_aom/compact/display.py`
- **Current terminal width in columns, with a sensible fallback.      Queried fresh** (1 connections) — `src/ansible_aom/compact/display.py`

## Relationships

- [Display](Display.md) (10 shared connections)
- [_row_count](_row_count.md) (4 shared connections)
- [IO](IO.md) (1 shared connections)

## Source Files

- `src/ansible_aom/compact/display.py`

## Audit Trail

- EXTRACTED: 73 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*