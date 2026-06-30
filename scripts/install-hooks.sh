#!/usr/bin/env bash
# Install AOM's git hooks. Run once after cloning.
#
# - post-commit: scripts/bump_version.py, which bumps pyproject.toml's
#   [project].version based on the conventional-commit type
#   (feat → minor, fix/refactor/perf → patch, ! / BREAKING → major)
#   and amends the just-created commit to include the bump.
#
# Design rationale: neither prepare-commit-msg nor commit-msg actually
# lets the hook land staged changes in the commit being created.
# git snapshots the index at the start of `git commit` and builds the
# tree from that snapshot — staging from within a hook updates the
# live index but the commit is already pinned. The pre-commit
# framework's stash/restore cycle around its own pre-commit-stage
# hooks compounds the problem. post-commit + `git commit --amend`
# is the only timing where the bump reliably lands in the same
# commit (the SHA changes but the message is preserved).

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOK_DIR="$REPO_ROOT/.git/hooks"
SCRIPT="$REPO_ROOT/scripts/bump_version.py"

if [[ ! -x "$SCRIPT" ]]; then
    chmod +x "$SCRIPT"
fi

# Symlink rather than copy so updates to the script are picked up
# without re-running this installer.
ln -sf "$SCRIPT" "$HOOK_DIR/post-commit"

# Clean up stale symlinks left over from earlier (broken) installs.
for stale in commit-msg prepare-commit-msg; do
    if [[ -L "$HOOK_DIR/$stale" ]] && [[ "$(readlink "$HOOK_DIR/$stale")" == "$SCRIPT" ]]; then
        rm "$HOOK_DIR/$stale"
        echo "removed stale: $HOOK_DIR/$stale"
    fi
done

echo "installed: $HOOK_DIR/post-commit -> $SCRIPT"
echo "test it with: git commit --allow-empty -m 'fix: test bump'"
