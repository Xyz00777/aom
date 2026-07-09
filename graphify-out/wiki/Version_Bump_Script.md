# Version Bump Script

> 37 nodes · cohesion 0.10

## Key Concepts

- **_detect_bump()** (15 connections) — `scripts/bump_version.py`
- **TestDetectBump** (14 connections) — `tests/unit/test_bump_version.py`
- **_bump_pyproject()** (10 connections) — `scripts/bump_version.py`
- **TestBumpPyproject** (9 connections) — `tests/unit/test_bump_version.py`
- **Path** (7 connections)
- **main()** (6 connections) — `scripts/bump_version.py`
- **._make_pyproject()** (6 connections) — `tests/unit/test_bump_version.py`
- **bump_version.py** (5 connections) — `scripts/bump_version.py`
- **_read_head_message()** (4 connections) — `scripts/bump_version.py`
- **test_bump_version.py** (4 connections) — `tests/unit/test_bump_version.py`
- **.test_major_bump_resets_minor_and_patch()** (4 connections) — `tests/unit/test_bump_version.py`
- **.test_minor_bump_resets_patch()** (4 connections) — `tests/unit/test_bump_version.py`
- **.test_other_version_strings_not_touched()** (4 connections) — `tests/unit/test_bump_version.py`
- **.test_patch_bump()** (4 connections) — `tests/unit/test_bump_version.py`
- **.test_unknown_level_is_noop()** (4 connections) — `tests/unit/test_bump_version.py`
- **Path** (3 connections)
- **.test_missing_version_line_is_noop()** (3 connections) — `tests/unit/test_bump_version.py`
- **.test_bang_suffix_triggers_major()** (2 connections) — `tests/unit/test_bump_version.py`
- **.test_bang_with_scope_triggers_major()** (2 connections) — `tests/unit/test_bump_version.py`
- **.test_breaking_change_footer_triggers_major()** (2 connections) — `tests/unit/test_bump_version.py`
- **.test_breaking_dash_form_also_triggers_major()** (2 connections) — `tests/unit/test_bump_version.py`
- **.test_docs_chore_test_style_do_not_bump()** (2 connections) — `tests/unit/test_bump_version.py`
- **.test_empty_message_no_bump()** (2 connections) — `tests/unit/test_bump_version.py`
- **.test_feat_triggers_minor()** (2 connections) — `tests/unit/test_bump_version.py`
- **.test_feat_with_scope_triggers_minor()** (2 connections) — `tests/unit/test_bump_version.py`
- *... and 12 more nodes in this community*

## Relationships

- No strong cross-community connections detected

## Source Files

- `scripts/bump_version.py`
- `tests/unit/test_bump_version.py`

## Audit Trail

- EXTRACTED: 102 (74%)
- INFERRED: 36 (26%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*