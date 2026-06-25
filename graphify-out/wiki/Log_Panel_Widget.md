# Log Panel Widget

> 19 nodes · cohesion 0.11

## Key Concepts

- **LogPanel** (9 connections) — `src/ansible_aom/tui/widgets/log_panel.py`
- **.compose()** (7 connections) — `src/ansible_aom/tui/screens/main.py`
- **.test_is_vertical_scroll_end_detection()** (3 connections) — `tests/tui/test_panels.py`
- **log_panel.py** (3 connections) — `src/ansible_aom/tui/widgets/log_panel.py`
- **is_vertical_scroll_end()** (3 connections) — `src/ansible_aom/tui/widgets/log_panel.py`
- **.__init__()** (2 connections) — `src/ansible_aom/tui/widgets/log_panel.py`
- **._on_mount()** (2 connections) — `src/ansible_aom/tui/widgets/log_panel.py`
- **.on_scroll()** (2 connections) — `src/ansible_aom/tui/widgets/log_panel.py`
- **.scroll_to_end()** (2 connections) — `src/ansible_aom/tui/widgets/log_panel.py`
- **.write_line()** (2 connections) — `src/ansible_aom/tui/widgets/log_panel.py`
- **TC-284: is_vertical_scroll_end() correctly detects bottom.** (1 connections) — `tests/tui/test_panels.py`
- **Log panel widget for AOM TUI.  RichLog with search functionality. See SPECIFICAT** (1 connections) — `src/ansible_aom/tui/widgets/log_panel.py`
- **Determine if scrolled to the end (bottom).      Args:         scroll_offset: Ind** (1 connections) — `src/ansible_aom/tui/widgets/log_panel.py`
- **Log panel with search support.** (1 connections) — `src/ansible_aom/tui/widgets/log_panel.py`
- **Initialize the log panel widget.          Args:             name: Widget name** (1 connections) — `src/ansible_aom/tui/widgets/log_panel.py`
- **Handle widget mount event.** (1 connections) — `src/ansible_aom/tui/widgets/log_panel.py`
- **Write a line to the log, auto-scrolling if enabled.          Args:             l** (1 connections) — `src/ansible_aom/tui/widgets/log_panel.py`
- **Scroll to bottom and re-enable auto-scroll.** (1 connections) — `src/ansible_aom/tui/widgets/log_panel.py`
- **Handle scroll events to manage auto-scroll state.** (1 connections) — `src/ansible_aom/tui/widgets/log_panel.py`

## Relationships

- [[Inspect TUI Widget Data]] (2 shared connections)
- [[Main TUI Screen]] (1 shared connections)
- [[Status Bar Widget]] (1 shared connections)
- [[Summary Panel Widget]] (1 shared connections)
- [[Task Definition Live Refresh]] (1 shared connections)
- [[Status Bar Warning Panels]] (1 shared connections)

## Source Files

- `src/ansible_aom/tui/screens/main.py`
- `src/ansible_aom/tui/widgets/log_panel.py`
- `tests/tui/test_panels.py`

## Audit Trail

- EXTRACTED: 37 (84%)
- INFERRED: 7 (16%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*