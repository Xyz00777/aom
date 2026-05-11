#!/usr/bin/env bash
# Install AOM's git hooks. Run once after cloning.
#
# - commit-msg: scripts/bump_version.py, which bumps pyproject.toml's
#   [project].version based on the conventional-commit type
#   (feat → minor, fix/refactor/perf → patch, ! / BREAKING → major).
#
# Direct git-hook installation rather than pre-commit framework because
# pre-commit stashes unstaged files around hook execution, undoing any
# `git add` the bumper performs (the bump would land in the NEXT commit
# instead of the one being written).

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOK_DIR="$REPO_ROOT/.git/hooks"
SCRIPT="$REPO_ROOT/scripts/bump_version.py"

if [[ ! -x "$SCRIPT" ]]; then
    chmod +x "$SCRIPT"
fi

# Symlink rather than copy so updates to the script are picked up
# without re-running this installer.
ln -sf "$SCRIPT" "$HOOK_DIR/commit-msg"

echo "installed: $HOOK_DIR/commit-msg -> $SCRIPT"
echo "test it with: git commit --allow-empty -m 'fix: test bump'"
