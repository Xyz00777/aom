# TestSignalHandling

> 10 nodes · cohesion 0.20

## Key Concepts

- **TestSignalHandling** (19 connections) — `tests/integration/test_compact_renderer.py`
- **.test_exit_code_130_for_sigint()** (2 connections) — `tests/integration/test_compact_renderer.py`
- **.test_sigint_second_press_kills_within_2s()** (2 connections) — `tests/integration/test_compact_renderer.py`
- **.test_sigpipe_is_ignored()** (2 connections) — `tests/integration/test_compact_renderer.py`
- **.test_sigquit_logs_stack_trace()** (2 connections) — `tests/integration/test_compact_renderer.py`
- **Tests for TC-046 to TC-053: Signal handling.** (1 connections) — `tests/integration/test_compact_renderer.py`
- **TC-047: Exit code 130 for SIGINT (second Ctrl+C).** (1 connections) — `tests/integration/test_compact_renderer.py`
- **TC-047: Second Ctrl+C within 2s kills everything, exits 130.** (1 connections) — `tests/integration/test_compact_renderer.py`
- **TC-048: SIGQUIT logs stack trace to file, continues execution.** (1 connections) — `tests/integration/test_compact_renderer.py`
- **TC-052: SIGPIPE is ignored — process continues without crash.** (1 connections) — `tests/integration/test_compact_renderer.py`

## Relationships

- [HostRunState](HostRunState.md) (5 shared connections)
- [Display](Display.md) (4 shared connections)
- [CompactRenderer](CompactRenderer.md) (2 shared connections)
- [TaskDefinition](TaskDefinition.md) (1 shared connections)
- [PlayDefinition](PlayDefinition.md) (1 shared connections)
- [Completion State Labels](Completion_State_Labels.md) (1 shared connections)

## Source Files

- `tests/integration/test_compact_renderer.py`

## Audit Trail

- EXTRACTED: 24 (75%)
- INFERRED: 8 (25%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*