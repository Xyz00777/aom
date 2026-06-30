# Version Bump Script

> 17 nodes · cohesion 0.20

## Key Concepts

- **_bump_pyproject()** (10 connections) — `scripts/bump_version.py`
- **TestBumpPyproject** (9 connections) — `tests/unit/test_bump_version.py`
- **main()** (6 connections) — `scripts/bump_version.py`
- **._make_pyproject()** (6 connections) — `tests/unit/test_bump_version.py`
- **bump_version.py** (4 connections) — `scripts/bump_version.py`
- **_read_head_message()** (4 connections) — `scripts/bump_version.py`
- **.test_major_bump_resets_minor_and_patch()** (4 connections) — `tests/unit/test_bump_version.py`
- **.test_minor_bump_resets_patch()** (4 connections) — `tests/unit/test_bump_version.py`
- **.test_other_version_strings_not_touched()** (4 connections) — `tests/unit/test_bump_version.py`
- **.test_patch_bump()** (4 connections) — `tests/unit/test_bump_version.py`
- **.test_unknown_level_is_noop()** (4 connections) — `tests/unit/test_bump_version.py`
- **.test_missing_version_line_is_noop()** (3 connections) — `tests/unit/test_bump_version.py`
- **Get the message of the just-created commit (HEAD).** (1 connections) — `scripts/bump_version.py`
- **Hook entry point.      Called as a post-commit hook (no useful argv). Reads the** (1 connections) — `scripts/bump_version.py`
- **Bump version in `pyproject`. Returns (old, new) or None if no match.** (1 connections) — `scripts/bump_version.py`
- **A ``requires-python = ">=3.14"`` or similar must NOT be bumped.** (1 connections) — `tests/unit/test_bump_version.py`
- **The pyproject mutation itself.** (1 connections) — `tests/unit/test_bump_version.py`

## Relationships

- [[Run Config Key Normalization]] (10 shared connections)
- [[Auto Version Bump Hook]] (3 shared connections)

## Source Files

- `scripts/bump_version.py`
- `tests/unit/test_bump_version.py`

## Audit Trail

- EXTRACTED: 55 (82%)
- INFERRED: 12 (18%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*