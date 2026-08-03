# TestClassifyEmpty

> 8 nodes · cohesion 0.25

## Key Concepts

- **TestClassifyEmpty** (8 connections) — `tests/unit/test_stderr_classifier.py`
- **.test_arbitrary_garbage_returns_unknown()** (3 connections) — `tests/unit/test_stderr_classifier.py`
- **.test_empty_string_returns_unknown()** (3 connections) — `tests/unit/test_stderr_classifier.py`
- **.test_whitespace_only_returns_unknown()** (3 connections) — `tests/unit/test_stderr_classifier.py`
- **classify() must never crash on empty / whitespace input.** (1 connections) — `tests/unit/test_stderr_classifier.py`
- **Empty line → UNKNOWN source, no host, no level.** (1 connections) — `tests/unit/test_stderr_classifier.py`
- **Whitespace-only line → UNKNOWN.** (1 connections) — `tests/unit/test_stderr_classifier.py`
- **A line matching no rule → UNKNOWN, original text preserved.** (1 connections) — `tests/unit/test_stderr_classifier.py`

## Relationships

- [Prompt Detection Heuristics](Prompt_Detection_Heuristics.md) (3 shared connections)
- [Skipped Task Collapsing](Skipped_Task_Collapsing.md) (2 shared connections)
- [Profile Tracemalloc Wiring](Profile_Tracemalloc_Wiring.md) (1 shared connections)
- [Keybinding Conflict Validation](Keybinding_Conflict_Validation.md) (1 shared connections)

## Source Files

- `tests/unit/test_stderr_classifier.py`

## Audit Trail

- EXTRACTED: 18 (86%)
- INFERRED: 3 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*