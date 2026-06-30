# Plan: --hide-state flag for compact mode

## Goal
Add a CLI flag to suppress per-host result lines of specific states (`ok`, `changed`,
`skipped`, `failed`, `unreachable`) from the scrollable log in compact mode, while
leaving the bottom status panel, events.jsonl recording, inspect, replay, rerun,
and TUI mode completely unaffected.

## Approach
Gate the relevant branches of `CompactRenderer._emit_event_log()` behind a
`frozenset[str]` (e.g. `self._hide_states`), threaded from a new CLI flag.

## TODOs
- [x] Task 1: Implement `core/log_filter.py` + `tests/unit/test_log_filter.py`
- [x] Task 2: Add `--hide-state` flag to CLI + `tests/unit/test_cli.py` extensions
- [x] Task 3: Wire flag through `renderer/factory.py` → `CompactRenderer.__init__` →
        `_emit_event_log` gates + `tests/compact/test_hide_state.py`
- [x] Task 4: Update `SPECIFICATION.md` (Section 3.2 table, new Section 4.1.5) +
        `TEST_SPECIFICATION.md` (TC-650+)
- [x] F1: Run full verification gate (all tests, lint, typecheck, manual smoke)

## Final Verification Wave
- [x] F2: Verify all tasks are `[x]` and full test suite passes
- [x] F3: Manual smoke: `aom --help` shows `--hide-state` flag
- [x] F4: 2789 tests passed, mypy clean, ruff clean on all changed files
