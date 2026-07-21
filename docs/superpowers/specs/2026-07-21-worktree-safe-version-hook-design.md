# Worktree-safe version hook design

## Problem

AOM installs its version bumper as a `post-commit` hook in the repository's shared
`.git/hooks` directory. The machine-wide hook dispatcher currently looks in the active Git
administrative directory instead. In a linked worktree that directory is
`.git/worktrees/<name>`, so the dispatcher misses the shared hook and version bumps do not run.

Simply making the dispatcher find the shared hook is unsafe with the current bumper. The hook
is an absolute symlink into the main checkout, and the bumper derives the repository root from
its own file path. A hook triggered in a linked worktree could therefore modify and amend the
main checkout instead of the committing worktree.

## Design

The global dispatcher will probe executable repo-local hooks in this order:

1. `<git-common-dir>/hooks/<hook>`, Git's normal shared hook location.
2. `<git-dir>/hooks/<hook>` when the worktree-specific Git directory differs, preserving the
   dispatcher's existing non-standard fallback.
3. `<worktree-root>/.githooks/<hook>`, preserving tracked in-tree hooks as a final fallback.

Duplicate directories will be skipped. The first executable hook still wins and is invoked
with `exec`, so a hook cannot run twice. The existing same-file recursion guard remains.

The AOM bumper will resolve the active repository root from the hook invocation's Git context
with `git rev-parse --show-toplevel`, not from `__file__`. It will resolve in-progress operation
markers with `git rev-parse --git-path <marker>`, which works whether `.git` is a directory or a
linked-worktree pointer file. All reads, writes, staging, lock refresh, and amend operations will
therefore target the worktree whose commit triggered the hook.

`post-commit` remains the correct phase: the triggering commit is created first, then the hook
bumps `pyproject.toml` and `uv.lock` and immediately amends those changes into that same commit.

## Testing

- Add dispatcher coverage using temporary repositories to prove shared `.git/hooks` delegation
  works from both the main checkout and a linked worktree, while retaining `.githooks` fallback.
- Add bumper coverage proving repository-root and Git-marker resolution use the active worktree.
- Run the AOM focused hook tests and full AOM suite.
- Run the configs repository's available smoke validation for the modified dispatcher. The
  configs repository currently has no general automated test suite, so the dispatcher regression
  test may live with the dispatcher implementation if a minimal isolated shell test is needed.

## Scope

There is no version backfill. `0.94.1` remains unchanged until a future bump-eligible AOM commit
runs through the repaired hook. No release workflow, version policy, or unrelated hook behavior
changes in this work.
