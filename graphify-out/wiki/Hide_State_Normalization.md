# Hide State Normalization

> 28 nodes · cohesion 0.10

## Key Concepts

- **normalize_hide_states()** (14 connections) — `src/ansible_aom/core/log_filter.py`
- **TestNormalizeHideStates** (13 connections) — `tests/unit/test_log_filter.py`
- **test_log_filter.py** (4 connections) — `tests/unit/test_log_filter.py`
- **.test_all_valid_states_accepted()** (3 connections) — `tests/unit/test_log_filter.py`
- **.test_case_insensitive()** (3 connections) — `tests/unit/test_log_filter.py`
- **.test_deduplicates()** (3 connections) — `tests/unit/test_log_filter.py`
- **.test_empty_input()** (3 connections) — `tests/unit/test_log_filter.py`
- **.test_frozenset_return_type()** (3 connections) — `tests/unit/test_log_filter.py`
- **.test_iterable_not_just_list()** (3 connections) — `tests/unit/test_log_filter.py`
- **.test_mixed_known_and_unknown()** (3 connections) — `tests/unit/test_log_filter.py`
- **.test_single_value()** (3 connections) — `tests/unit/test_log_filter.py`
- **.test_unknown_list_preserves_order()** (3 connections) — `tests/unit/test_log_filter.py`
- **.test_unknown_state_returns_in_unknown_list()** (3 connections) — `tests/unit/test_log_filter.py`
- **.test_whitespace_around_tokens_not_stripped()** (3 connections) — `tests/unit/test_log_filter.py`
- **Lowercase, deduplicate, validate, and separate unknown inputs.      Args:** (1 connections) — `src/ansible_aom/core/log_filter.py`
- **Unit tests for core/log_filter.py --hide-state helper functions.** (1 connections) — `tests/unit/test_log_filter.py`
- **Tests for normalize_hide_states — input validation and normalisation.** (1 connections) — `tests/unit/test_log_filter.py`
- **Empty iterable returns empty frozenset and empty unknown list.** (1 connections) — `tests/unit/test_log_filter.py`
- **Single known value returns frozenset with that value.** (1 connections) — `tests/unit/test_log_filter.py`
- **Mixed-case input is lowercased and matched against VALID_STATES.** (1 connections) — `tests/unit/test_log_filter.py`
- **Duplicate values produce a single entry in the frozenset.** (1 connections) — `tests/unit/test_log_filter.py`
- **Every entry in VALID_STATES is accepted individually.** (1 connections) — `tests/unit/test_log_filter.py`
- **A value not in VALID_STATES appears in the unknown list.** (1 connections) — `tests/unit/test_log_filter.py`
- **Known values go to the frozenset; unknown values go to the list.** (1 connections) — `tests/unit/test_log_filter.py`
- **The first return value is a frozenset, not a plain set.** (1 connections) — `tests/unit/test_log_filter.py`
- *... and 3 more nodes in this community*

## Relationships

- [[Color ASCII Fallback]] (1 shared connections)
- [[Log Filter Helpers]] (1 shared connections)
- [[Event Hide Filter Logic]] (1 shared connections)
- [[Host Result Hide Filter]] (1 shared connections)

## Source Files

- `src/ansible_aom/core/log_filter.py`
- `tests/unit/test_log_filter.py`

## Audit Trail

- EXTRACTED: 55 (71%)
- INFERRED: 23 (29%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*