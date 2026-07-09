# Community 465

> 10 nodes · cohesion 0.20

## Key Concepts

- **TestClassifierRules** (9 connections) — `tests/unit/test_stderr_classifier.py`
- **.test_every_rule_has_three_fields()** (3 connections) — `tests/unit/test_stderr_classifier.py`
- **.test_at_least_30_rules()** (2 connections) — `tests/unit/test_stderr_classifier.py`
- **.test_no_duplicate_first_words()** (2 connections) — `tests/unit/test_stderr_classifier.py`
- **.test_regexes_are_compiled()** (2 connections) — `tests/unit/test_stderr_classifier.py`
- **No two rules share the same first matching token (first-match-wins         would** (1 connections) — `tests/unit/test_stderr_classifier.py`
- **CLASSIFIER_RULES shape and ordering — the engine of the classifier.** (1 connections) — `tests/unit/test_stderr_classifier.py`
- **The plan calls for 30 rules; we accept more but not fewer.** (1 connections) — `tests/unit/test_stderr_classifier.py`
- **Each rule is ``(source, regex, has_host)``.** (1 connections) — `tests/unit/test_stderr_classifier.py`
- **Each rule's regex is a pre-compiled ``re.Pattern`` (hot path).** (1 connections) — `tests/unit/test_stderr_classifier.py`

## Relationships

- [Profile Tracemalloc Wiring](Profile_Tracemalloc_Wiring.md) (2 shared connections)
- [Skipped Task Collapsing](Skipped_Task_Collapsing.md) (2 shared connections)
- [Keybinding Conflict Validation](Keybinding_Conflict_Validation.md) (1 shared connections)

## Source Files

- `tests/unit/test_stderr_classifier.py`

## Audit Trail

- EXTRACTED: 19 (83%)
- INFERRED: 4 (17%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*