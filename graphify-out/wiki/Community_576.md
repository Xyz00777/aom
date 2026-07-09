# Community 576

> 6 nodes · cohesion 0.33

## Key Concepts

- **TestClassifySshDebug** (8 connections) — `tests/unit/test_stderr_classifier.py`
- **.test_without_host()** (3 connections) — `tests/unit/test_stderr_classifier.py`
- **.test_with_fqdn_host()** (2 connections) — `tests/unit/test_stderr_classifier.py`
- **.test_with_host()** (2 connections) — `tests/unit/test_stderr_classifier.py`
- **``<host> SSH:`` lines from ssh.py (caplevel 4+).** (1 connections) — `tests/unit/test_stderr_classifier.py`
- **SSH: without a host prefix still classifies as ssh_debug with no host.** (1 connections) — `tests/unit/test_stderr_classifier.py`

## Relationships

- [Prompt Detection Heuristics](Prompt_Detection_Heuristics.md) (3 shared connections)
- [Skipped Task Collapsing](Skipped_Task_Collapsing.md) (2 shared connections)
- [Profile Tracemalloc Wiring](Profile_Tracemalloc_Wiring.md) (1 shared connections)
- [Keybinding Conflict Validation](Keybinding_Conflict_Validation.md) (1 shared connections)

## Source Files

- `tests/unit/test_stderr_classifier.py`

## Audit Trail

- EXTRACTED: 11 (65%)
- INFERRED: 6 (35%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*