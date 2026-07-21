# Worktree-safe Version Hook Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the global Git hook dispatcher and AOM's amend-based version bumper operate on the committing linked worktree.

**Architecture:** The dispatcher resolves Git's common administrative directory before its existing worktree-local and tracked-hook fallbacks. The bumper resolves its target worktree and operation-marker paths from the invoking Git context instead of the installed script path.

**Tech Stack:** POSIX shell/Bash, Git hooks, Python 3.14, pytest, uv

---

### Task 1: Pin dispatcher behavior

**Files:**
- Create: `/Users/felix/configs/tests/test_git_hook_dispatch.sh`
- Modify: `/Users/felix/configs/ansible/roles/terminal_dotfiles/files/git-hooks/dispatch`

- [ ] Write a shell regression test that creates a temporary repository plus linked worktree, configures the real dispatcher as `core.hooksPath/post-commit`, and asserts that a shared `.git/hooks/post-commit` runs from the linked worktree.
- [ ] Add a second case proving `<worktree-root>/.githooks/post-commit` remains the fallback when no shared hook exists.
- [ ] Run `bash tests/test_git_hook_dispatch.sh`; verify the shared-hook case fails before implementation.
- [ ] Change dispatcher candidate discovery to `git rev-parse --git-common-dir`, then `git rev-parse --git-dir` when distinct, then `<toplevel>/.githooks`; retain first-executable `exec` and recursion protection.
- [ ] Re-run `bash tests/test_git_hook_dispatch.sh`; verify both cases pass.
- [ ] Commit only the configs repository files as `git-hooks: dispatch shared hooks from linked worktrees`.

### Task 2: Pin AOM bumper behavior

**Files:**
- Modify: `/Users/felix/Coding/ansible-aom/tests/unit/test_bump_version.py`
- Modify: `/Users/felix/Coding/ansible-aom/scripts/bump_version.py`

- [ ] Add a pytest regression that builds a real temporary Git repository, installs an absolute shared-hook symlink to the bumper, commits from a linked worktree, and asserts only that worktree is bumped and amended.
- [ ] Add coverage that an operation marker resolved by `git rev-parse --git-path` suppresses a manual bumper run from a linked worktree.
- [ ] Run `uv run pytest tests/unit/test_bump_version.py -q`; verify the linked-worktree regression fails because the bump is absent or targets the main checkout.
- [ ] Resolve the active root with `git rev-parse --show-toplevel` from the hook's inherited working directory, and resolve each safety marker with `git rev-parse --git-path` in that root.
- [ ] Re-run `uv run pytest tests/unit/test_bump_version.py -q`; verify all hook tests pass.

### Task 3: Verify and finish

**Files:**
- Refresh generated graph files under `/Users/felix/Coding/ansible-aom/graphify-out/` using the required project command.

- [ ] Run `uv run ruff format`, `uv run ruff check --fix`, `uv run mypy src/ansible_aom`, and `uv run pytest tests/ -q` in AOM.
- [ ] Run `bash tests/test_git_hook_dispatch.sh` and `./scripts/ansible_smoketest.sh` in configs if the smoke test is safe on the local host; otherwise run syntax-level validation and report the limitation.
- [ ] Run `graphify update .` in AOM when the CLI is available; report the unavailable CLI otherwise.
- [ ] Confirm `pyproject.toml` remains `0.94.1` and no backfill was introduced.
- [ ] Commit the AOM implementation and test files as `fix(hooks): target version bumps at active worktree`.
