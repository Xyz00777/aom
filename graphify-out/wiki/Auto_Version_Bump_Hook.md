# Auto Version Bump Hook

> 18 nodes · cohesion 0.18

## Key Concepts

- **_detect_bump()** (15 connections) — `scripts/bump_version.py`
- **TestDetectBump** (14 connections) — `tests/unit/test_bump_version.py`
- **test_bump_version.py** (3 connections) — `tests/unit/test_bump_version.py`
- **.test_bang_suffix_triggers_major()** (2 connections) — `tests/unit/test_bump_version.py`
- **.test_bang_with_scope_triggers_major()** (2 connections) — `tests/unit/test_bump_version.py`
- **.test_breaking_change_footer_triggers_major()** (2 connections) — `tests/unit/test_bump_version.py`
- **.test_breaking_dash_form_also_triggers_major()** (2 connections) — `tests/unit/test_bump_version.py`
- **.test_docs_chore_test_style_do_not_bump()** (2 connections) — `tests/unit/test_bump_version.py`
- **.test_empty_message_no_bump()** (2 connections) — `tests/unit/test_bump_version.py`
- **.test_feat_triggers_minor()** (2 connections) — `tests/unit/test_bump_version.py`
- **.test_feat_with_scope_triggers_minor()** (2 connections) — `tests/unit/test_bump_version.py`
- **.test_fix_triggers_patch()** (2 connections) — `tests/unit/test_bump_version.py`
- **.test_non_conventional_message_no_bump()** (2 connections) — `tests/unit/test_bump_version.py`
- **.test_perf_triggers_patch()** (2 connections) — `tests/unit/test_bump_version.py`
- **.test_refactor_triggers_patch()** (2 connections) — `tests/unit/test_bump_version.py`
- **Return ``major`` / ``minor`` / ``patch`` or ``None`` for no bump.** (1 connections) — `scripts/bump_version.py`
- **Tests for the auto-version-bump pre-commit hook.  The hook reads a conventional-** (1 connections) — `tests/unit/test_bump_version.py`
- **Mapping from commit message to bump level.** (1 connections) — `tests/unit/test_bump_version.py`

## Relationships

- [[Version Bump Script]] (3 shared connections)

## Source Files

- `scripts/bump_version.py`
- `tests/unit/test_bump_version.py`

## Audit Trail

- EXTRACTED: 35 (59%)
- INFERRED: 24 (41%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*