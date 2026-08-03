# Keybinding Conflict Validation

> 14 nodes · cohesion 0.18

## Key Concepts

- **StderrEvent** (30 connections) — `src/ansible_aom/core/stderr_classifier.py`
- **TestStderrEvent** (8 connections) — `tests/unit/test_stderr_classifier.py`
- **TestAnsiStrippedInputs** (6 connections) — `tests/unit/test_stderr_classifier.py`
- **.test_clean_text_input()** (3 connections) — `tests/unit/test_stderr_classifier.py`
- **.test_equality()** (3 connections) — `tests/unit/test_stderr_classifier.py`
- **.test_frozen_dataclass()** (3 connections) — `tests/unit/test_stderr_classifier.py`
- **.test_required_fields()** (3 connections) — `tests/unit/test_stderr_classifier.py`
- **A classified stderr line.      Carries the full info needed to emit a synthetic** (1 connections) — `src/ansible_aom/core/stderr_classifier.py`
- **StderrEvent shape — used by emit code in store.py.** (1 connections) — `tests/unit/test_stderr_classifier.py`
- **StderrEvent is frozen so emit code can rely on it being immutable.** (1 connections) — `tests/unit/test_stderr_classifier.py`
- **Frozen dataclass equality on all four fields.** (1 connections) — `tests/unit/test_stderr_classifier.py`
- **All four fields are required (no defaults).** (1 connections) — `tests/unit/test_stderr_classifier.py`
- **Real ansible-playbook wraps stderr in SGR escape sequences. The     classifier s** (1 connections) — `tests/unit/test_stderr_classifier.py`
- **Sanity: clean text is classifiable.** (1 connections) — `tests/unit/test_stderr_classifier.py`

## Relationships

- [Skipped Task Collapsing](Skipped_Task_Collapsing.md) (11 shared connections)
- [Prompt Detection Heuristics](Prompt_Detection_Heuristics.md) (6 shared connections)
- [Profile Tracemalloc Wiring](Profile_Tracemalloc_Wiring.md) (5 shared connections)
- [TestClassifierRules](TestClassifierRules.md) (1 shared connections)
- [TestClassifyEmpty](TestClassifyEmpty.md) (1 shared connections)
- [TestClassifyError](TestClassifyError.md) (1 shared connections)
- [TestClassifyPrompt](TestClassifyPrompt.md) (1 shared connections)
- [TestClassifySshDebug](TestClassifySshDebug.md) (1 shared connections)
- [TestClassifyWarning](TestClassifyWarning.md) (1 shared connections)
- [TestFirstMatchWins](TestFirstMatchWins.md) (1 shared connections)
- [TestHostExtraction](TestHostExtraction.md) (1 shared connections)
- [TestLevelMap](TestLevelMap.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/stderr_classifier.py`
- `tests/unit/test_stderr_classifier.py`

## Audit Trail

- EXTRACTED: 26 (41%)
- INFERRED: 37 (59%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*