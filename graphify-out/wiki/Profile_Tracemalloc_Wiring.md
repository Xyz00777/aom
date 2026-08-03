# Profile Tracemalloc Wiring

> 17 nodes · cohesion 0.14

## Key Concepts

- **StderrSource** (31 connections) — `src/ansible_aom/core/stderr_classifier.py`
- **stderr_classifier.py** (10 connections) — `src/ansible_aom/core/stderr_classifier.py`
- **TestStderrSource** (8 connections) — `tests/unit/test_stderr_classifier.py`
- **TestRealWorldSamples** (6 connections) — `tests/unit/test_stderr_classifier.py`
- **.test_sample()** (3 connections) — `tests/unit/test_stderr_classifier.py`
- **.test_member_count_is_13()** (3 connections) — `tests/unit/test_stderr_classifier.py`
- **Enum** (2 connections)
- **.test_all_required_members_present()** (2 connections) — `tests/unit/test_stderr_classifier.py`
- **.test_values_are_lowercase_strings()** (2 connections) — `tests/unit/test_stderr_classifier.py`
- **V1 stderr classifier — maps raw ansible-playbook stderr lines to typed events.** (1 connections) — `src/ansible_aom/core/stderr_classifier.py`
- **Stable enum of stderr line sources (v1 contract — 12 named values).      Plus an** (1 connections) — `src/ansible_aom/core/stderr_classifier.py`
- **str** (1 connections)
- **The StderrSource enum is the public contract — 12 named values + UNKNOWN.** (1 connections) — `tests/unit/test_stderr_classifier.py`
- **The enum has 12 named values (per the v1 design) plus an         UNKNOWN catch-a** (1 connections) — `tests/unit/test_stderr_classifier.py`
- **Every source named in the v1 plan exists in the enum.** (1 connections) — `tests/unit/test_stderr_classifier.py`
- **Values match the canonical strings used in events.jsonl.** (1 connections) — `tests/unit/test_stderr_classifier.py`
- **Sample lines observed during real ansible-playbook runs.** (1 connections) — `tests/unit/test_stderr_classifier.py`

## Relationships

- [Skipped Task Collapsing](Skipped_Task_Collapsing.md) (12 shared connections)
- [Prompt Detection Heuristics](Prompt_Detection_Heuristics.md) (6 shared connections)
- [Keybinding Conflict Validation](Keybinding_Conflict_Validation.md) (5 shared connections)
- [State Transition Validation](State_Transition_Validation.md) (2 shared connections)
- [TestClassifierRules](TestClassifierRules.md) (2 shared connections)
- [StreamPhase](StreamPhase.md) (1 shared connections)
- [load_session](load_session.md) (1 shared connections)
- [TestClassifyEmpty](TestClassifyEmpty.md) (1 shared connections)
- [TestClassifyError](TestClassifyError.md) (1 shared connections)
- [TestClassifyPrompt](TestClassifyPrompt.md) (1 shared connections)
- [TestClassifySshDebug](TestClassifySshDebug.md) (1 shared connections)
- [TestClassifyWarning](TestClassifyWarning.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/stderr_classifier.py`
- `tests/unit/test_stderr_classifier.py`

## Audit Trail

- EXTRACTED: 42 (56%)
- INFERRED: 33 (44%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*