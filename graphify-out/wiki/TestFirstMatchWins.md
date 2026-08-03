# TestFirstMatchWins

> 6 nodes · cohesion 0.33

## Key Concepts

- **TestFirstMatchWins** (7 connections) — `tests/unit/test_stderr_classifier.py`
- **.test_failed_to_connect_takes_precedence_over_ssh_retry()** (3 connections) — `tests/unit/test_stderr_classifier.py`
- **.test_ssh_agent_takes_precedence_over_generic_ssh()** (3 connections) — `tests/unit/test_stderr_classifier.py`
- **When two rules could match, the first one in CLASSIFIER_RULES wins.** (1 connections) — `tests/unit/test_stderr_classifier.py`
- **``<web1> SSH: SSH_AGENT ...`` should hit the SSH_AGENT rule,         not the gen** (1 connections) — `tests/unit/test_stderr_classifier.py`
- **``Failed to connect to the host via ssh:`` could potentially         collide wit** (1 connections) — `tests/unit/test_stderr_classifier.py`

## Relationships

- [Skipped Task Collapsing](Skipped_Task_Collapsing.md) (2 shared connections)
- [Prompt Detection Heuristics](Prompt_Detection_Heuristics.md) (2 shared connections)
- [Profile Tracemalloc Wiring](Profile_Tracemalloc_Wiring.md) (1 shared connections)
- [Keybinding Conflict Validation](Keybinding_Conflict_Validation.md) (1 shared connections)

## Source Files

- `tests/unit/test_stderr_classifier.py`

## Audit Trail

- EXTRACTED: 11 (69%)
- INFERRED: 5 (31%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*