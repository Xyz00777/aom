# Compact Display Logic

> 18 nodes · cohesion 0.12

## Key Concepts

- **._rewind_status()** (6 connections) — `src/ansible_aom/compact/display.py`
- **.update()** (6 connections) — `src/ansible_aom/compact/display.py`
- **display.py** (5 connections) — `src/ansible_aom/compact/display.py`
- **.print_log()** (5 connections) — `src/ansible_aom/compact/display.py`
- **_terminal_width()** (4 connections) — `src/ansible_aom/compact/display.py`
- **.clear()** (3 connections) — `src/ansible_aom/compact/display.py`
- **._current_size()** (3 connections) — `src/ansible_aom/compact/display.py`
- **.stop()** (3 connections) — `src/ansible_aom/compact/display.py`
- **check_terminal_size()** (2 connections) — `src/ansible_aom/compact/display.py`
- **Display logic for compact mode — nom-style fixed-bottom status panel.  Renders d** (1 connections) — `src/ansible_aom/compact/display.py`
- **Erase the status block and release the terminal.** (1 connections) — `src/ansible_aom/compact/display.py`
- **Redraw the status block with new content.          Updates within _THROTTLE_INTE** (1 connections) — `src/ansible_aom/compact/display.py`
- **Print a log line above the status block.          Wipes the status, writes the l** (1 connections) — `src/ansible_aom/compact/display.py`
- **Erase the status content (but leave the display running).** (1 connections) — `src/ansible_aom/compact/display.py`
- **Resolve (cols, rows) — the test override or the live kernel value.          ``sh** (1 connections) — `src/ansible_aom/compact/display.py`
- **Cursor sequence to move back to the start of the status block.          After wr** (1 connections) — `src/ansible_aom/compact/display.py`
- **Current terminal width in columns, with a sensible fallback.      Queried fresh** (1 connections) — `src/ansible_aom/compact/display.py`
- **Check if terminal meets minimum size requirements.      Args:         lines: Num** (1 connections) — `src/ansible_aom/compact/display.py`

## Relationships

- [[Terminal Display Manager]] (7 shared connections)
- [[Terminal Row Counting]] (3 shared connections)

## Source Files

- `src/ansible_aom/compact/display.py`

## Audit Trail

- EXTRACTED: 46 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*