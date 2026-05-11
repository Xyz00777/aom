#!/usr/bin/env bash
# Install AOM's git hooks. Run once after cloning.
#
# - prepare-commit-msg: scripts/bump_version.py, which bumps
#   pyproject.toml's [project].version based on the conventional-commit
#   type (feat → minor, fix/refactor/perf → patch, ! / BREAKING → major).
#
# Two design choices worth noting:
#
# 1. Direct git-hook installation rather than pre-commit framework
#    because pre-commit stashes unstaged files around hook execution,
#    undoing any `git add` the bumper performs.
# 2. prepare-commit-msg rather than commit-msg because commit-msg
#    runs after git has built the tree object for the in-flight
#    commit — `git add` at that point updates the index but the
#    commit is already snapshotted, so the bump lands in the NEXT
#    commit instead of the one being written. prepare-commit-msg
#    runs early enough that the staged change is included.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOK_DIR="$REPO_ROOT/.git/hooks"
SCRIPT="$REPO_ROOT/scripts/bump_version.py"

if [[ ! -x "$SCRIPT" ]]; then
    chmod +x "$SCRIPT"
fi

# Symlink rather than copy so updates to the script are picked up
# without re-running this installer.
ln -sf "$SCRIPT" "$HOOK_DIR/prepare-commit-msg"

# Clean up any stale commit-msg symlink left over from an earlier
# (broken) install.
if [[ -L "$HOOK_DIR/commit-msg" ]] && [[ "$(readlink "$HOOK_DIR/commit-msg")" == "$SCRIPT" ]]; then
    rm "$HOOK_DIR/commit-msg"
fi

echo "installed: $HOOK_DIR/prepare-commit-msg -> $SCRIPT"
echo "test it with: git commit --allow-empty -m 'fix: test bump'"
