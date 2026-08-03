# Ctrl-C Race Handling

> 14 nodes · cohesion 0.16

## Key Concepts

- **.update()** (9 connections) — `src/ansible_aom/compact/display.py`
- **._rewind_status()** (7 connections) — `src/ansible_aom/compact/display.py`
- **._drain_pending_logs()** (6 connections) — `src/ansible_aom/compact/display.py`
- **.clear()** (4 connections) — `src/ansible_aom/compact/display.py`
- **._log_flush_due()** (4 connections) — `src/ansible_aom/compact/display.py`
- **.stop()** (4 connections) — `src/ansible_aom/compact/display.py`
- **._current_size()** (3 connections) — `src/ansible_aom/compact/display.py`
- **Erase the status block and release the terminal.** (1 connections) — `src/ansible_aom/compact/display.py`
- **Redraw the status block with new content.          Updates within _THROTTLE_INTE** (1 connections) — `src/ansible_aom/compact/display.py`
- **True when the flush window has elapsed (or never started).** (1 connections) — `src/ansible_aom/compact/display.py`
- **Take the queued log lines (each already newline-terminated).** (1 connections) — `src/ansible_aom/compact/display.py`
- **Erase the status content (but leave the display running).** (1 connections) — `src/ansible_aom/compact/display.py`
- **Resolve (cols, rows) — the test override or the live kernel value.          ``sh** (1 connections) — `src/ansible_aom/compact/display.py`
- **Cursor sequence to move back to the start of the status block.          After wr** (1 connections) — `src/ansible_aom/compact/display.py`

## Relationships

- [Compact Renderer Integration Tests](Compact_Renderer_Integration_Tests.md) (7 shared connections)
- [Ansible Runner Subprocess](Ansible_Runner_Subprocess.md) (7 shared connections)

## Source Files

- `src/ansible_aom/compact/display.py`

## Audit Trail

- EXTRACTED: 44 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*