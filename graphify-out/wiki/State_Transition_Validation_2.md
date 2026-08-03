# State Transition Validation

> 13 nodes · cohesion 0.19

## Key Concepts

- **TestFuzzNoFalsePositives** (8 connections) — `tests/unit/test_aom_verbose_line_fuzz.py`
- **test_aom_verbose_line_fuzz.py** (7 connections) — `tests/unit/test_aom_verbose_line_fuzz.py`
- **_build_corpus()** (3 connections) — `tests/unit/test_aom_verbose_line_fuzz.py`
- **_generate_line()** (3 connections) — `tests/unit/test_aom_verbose_line_fuzz.py`
- **_random_text()** (2 connections) — `tests/unit/test_aom_verbose_line_fuzz.py`
- **.test_all_lines_are_unknown()** (2 connections) — `tests/unit/test_aom_verbose_line_fuzz.py`
- **.test_all_lines_have_no_host()** (2 connections) — `tests/unit/test_aom_verbose_line_fuzz.py`
- **.test_corpus_is_deterministic()** (2 connections) — `tests/unit/test_aom_verbose_line_fuzz.py`
- **.test_never_raises()** (2 connections) — `tests/unit/test_aom_verbose_line_fuzz.py`
- **_random_word()** (1 connections) — `tests/unit/test_aom_verbose_line_fuzz.py`
- **Deterministic fuzz test for the v1 stderr classifier.  Exercises ``classify()``** (1 connections) — `tests/unit/test_aom_verbose_line_fuzz.py`
- **10k stderr-like lines must not produce false positives.** (1 connections) — `tests/unit/test_aom_verbose_line_fuzz.py`
- **.test_corpus_size_is_exactly_10k()** (1 connections) — `tests/unit/test_aom_verbose_line_fuzz.py`

## Relationships

- [Prompt Detection Heuristics](Prompt_Detection_Heuristics.md) (3 shared connections)
- [Profile Tracemalloc Wiring](Profile_Tracemalloc_Wiring.md) (2 shared connections)

## Source Files

- `tests/unit/test_aom_verbose_line_fuzz.py`

## Audit Trail

- EXTRACTED: 34 (97%)
- INFERRED: 1 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*