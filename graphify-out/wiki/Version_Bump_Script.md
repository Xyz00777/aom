# Version Bump Script

> 48 nodes · cohesion 0.08

## Key Concepts

- **_detect_bump()** (15 connections) — `scripts/bump_version.py`
- **TestDetectBump** (14 connections) — `tests/unit/test_bump_version.py`
- **Path** (11 connections)
- **_bump_pyproject()** (10 connections) — `scripts/bump_version.py`
- **TestBumpPyproject** (9 connections) — `tests/unit/test_bump_version.py`
- **main()** (8 connections) — `scripts/bump_version.py`
- **bump_version.py** (7 connections) — `scripts/bump_version.py`
- **test_bump_version.py** (7 connections) — `tests/unit/test_bump_version.py`
- **_git()** (6 connections) — `tests/unit/test_bump_version.py`
- **._make_pyproject()** (6 connections) — `tests/unit/test_bump_version.py`
- **Path** (5 connections)
- **_make_git_repo_with_linked_worktree()** (5 connections) — `tests/unit/test_bump_version.py`
- **_read_head_message()** (4 connections) — `scripts/bump_version.py`
- **_resolve_git_path()** (4 connections) — `scripts/bump_version.py`
- **_resolve_repo_root()** (4 connections) — `scripts/bump_version.py`
- **.test_major_bump_resets_minor_and_patch()** (4 connections) — `tests/unit/test_bump_version.py`
- **.test_minor_bump_resets_patch()** (4 connections) — `tests/unit/test_bump_version.py`
- **.test_other_version_strings_not_touched()** (4 connections) — `tests/unit/test_bump_version.py`
- **.test_patch_bump()** (4 connections) — `tests/unit/test_bump_version.py`
- **.test_unknown_level_is_noop()** (4 connections) — `tests/unit/test_bump_version.py`
- **TestLinkedWorktreeHook** (4 connections) — `tests/unit/test_bump_version.py`
- **.test_git_resolved_operation_marker_prevents_worktree_bump()** (4 connections) — `tests/unit/test_bump_version.py`
- **.test_post_commit_bumps_and_amends_the_committing_worktree()** (4 connections) — `tests/unit/test_bump_version.py`
- **.test_missing_version_line_is_noop()** (3 connections) — `tests/unit/test_bump_version.py`
- **.test_bang_suffix_triggers_major()** (2 connections) — `tests/unit/test_bump_version.py`
- *... and 23 more nodes in this community*

## Relationships

- No strong cross-community connections detected

## Source Files

- `scripts/bump_version.py`
- `tests/unit/test_bump_version.py`

## Audit Trail

- EXTRACTED: 150 (81%)
- INFERRED: 36 (19%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*