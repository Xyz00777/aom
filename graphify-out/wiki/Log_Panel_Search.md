# Log Panel Search

> 22 nodes · cohesion 0.09

## Key Concepts

- **TestLogPanelSearchOverlay** (20 connections) — `tests/tui/test_panels.py`
- **.test_search_case_sensitive_toggle()** (2 connections) — `tests/tui/test_panels.py`
- **.test_search_empty_result()** (2 connections) — `tests/tui/test_panels.py`
- **.test_search_f3_navigation_next()** (2 connections) — `tests/tui/test_panels.py`
- **.test_search_f3_navigation_previous()** (2 connections) — `tests/tui/test_panels.py`
- **.test_search_f3_wrap_at_last_match()** (2 connections) — `tests/tui/test_panels.py`
- **.test_search_match_highlighting()** (2 connections) — `tests/tui/test_panels.py`
- **.test_search_overlay_activation_ctrl_f()** (2 connections) — `tests/tui/test_panels.py`
- **.test_search_plain_text_mode()** (2 connections) — `tests/tui/test_panels.py`
- **.test_search_regex_invalid_pattern_handled()** (2 connections) — `tests/tui/test_panels.py`
- **.test_search_regex_mode()** (2 connections) — `tests/tui/test_panels.py`
- **Tests for search overlay functionality - TC-278 to TC-283.** (1 connections) — `tests/tui/test_panels.py`
- **TC-278: Ctrl+F opens search overlay at top of log panel.** (1 connections) — `tests/tui/test_panels.py`
- **TC-279: Plain text search finds and highlights matching lines.** (1 connections) — `tests/tui/test_panels.py`
- **TC-280: Regex search matches patterns.** (1 connections) — `tests/tui/test_panels.py`
- **TC-280 edge case: Invalid regex patterns handled gracefully.** (1 connections) — `tests/tui/test_panels.py`
- **TC-281: Case-sensitive toggle affects search matching.** (1 connections) — `tests/tui/test_panels.py`
- **TC-282: F3 jumps to next match.** (1 connections) — `tests/tui/test_panels.py`
- **TC-282: Shift+F3 jumps to previous match.** (1 connections) — `tests/tui/test_panels.py`
- **TC-282 edge case: F3 at last match wraps to first.** (1 connections) — `tests/tui/test_panels.py`
- **TC-283: Search matches are visually highlighted.** (1 connections) — `tests/tui/test_panels.py`
- **TC-279 edge case: No matches shows empty result.** (1 connections) — `tests/tui/test_panels.py`

## Relationships

- [[Status Bar Warning Panels]] (3 shared connections)
- [[Run State Completion Recap]] (3 shared connections)
- [[Role Group Task Models]] (2 shared connections)
- [[Run State Summary Panel]] (1 shared connections)

## Source Files

- `tests/tui/test_panels.py`

## Audit Trail

- EXTRACTED: 43 (84%)
- INFERRED: 8 (16%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*