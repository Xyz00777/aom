# TestHostExtraction

> 9 nodes · cohesion 0.22

## Key Concepts

- **TestHostExtraction** (10 connections) — `tests/unit/test_stderr_classifier.py`
- **.test_no_host_prefix_means_no_host()** (3 connections) — `tests/unit/test_stderr_classifier.py`
- **.test_run_level_lines_never_have_host()** (3 connections) — `tests/unit/test_stderr_classifier.py`
- **.test_host_extracted_fqdn()** (2 connections) — `tests/unit/test_stderr_classifier.py`
- **.test_host_extracted_ip_address()** (2 connections) — `tests/unit/test_stderr_classifier.py`
- **.test_host_extracted_simple()** (2 connections) — `tests/unit/test_stderr_classifier.py`
- **Host is extracted from ``<hostname>`` prefix when present.** (1 connections) — `tests/unit/test_stderr_classifier.py`
- **A line without ``<...>`` prefix has no host even if rule says has_host.** (1 connections) — `tests/unit/test_stderr_classifier.py`
- **Even with a stale ``<...>`` in the regex, run-level sources         don't extrac** (1 connections) — `tests/unit/test_stderr_classifier.py`

## Relationships

- [Prompt Detection Heuristics](Prompt_Detection_Heuristics.md) (5 shared connections)
- [Skipped Task Collapsing](Skipped_Task_Collapsing.md) (2 shared connections)
- [Profile Tracemalloc Wiring](Profile_Tracemalloc_Wiring.md) (1 shared connections)
- [Keybinding Conflict Validation](Keybinding_Conflict_Validation.md) (1 shared connections)

## Source Files

- `tests/unit/test_stderr_classifier.py`

## Audit Trail

- EXTRACTED: 22 (88%)
- INFERRED: 3 (12%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*