#!/usr/bin/env bash
# Install AOM's git hooks. Run once after cloning.
#
# Sets this repo's core.hooksPath to .githooks/ so the hooks below are
# used regardless of any global core.hooksPath (e.g. a Nix-managed
# ~/.config/git/hooks). Installs:
#
# - post-commit: .githooks/post-commit, which dispatches to:
#     * scripts/bump_version.py         — bumps pyproject.toml's version
#       based on the conventional-commit type and amends the commit
#     * .githooks/post-commit-graphify  — regenerates the graphify-out
#       submodule graph, commits+pushes it, and amends the gitlink
# - pre-commit: .githooks/pre-commit    — delegated to the pre-commit
#       framework (ruff, mypy, verify-anchors)
# - pre-push:   .githooks/pre-push      — diff-aware pytest (testmon)
#
# Design rationale: neither prepare-commit-msg nor commit-msg actually
# lets a hook land staged changes in the commit being created. git
# snapshots the index at the start of `git commit` and builds the tree
# from that snapshot — staging from within a hook updates the live index
# but the commit is already pinned. The pre-commit framework's
# stash/restore cycle around its own pre-commit-stage hooks compounds the
# problem. post-commit + `git commit --amend` is the only timing where a
# generated artifact (version bump, graphify gitlink) reliably lands in
# the same commit (the SHA changes but the message is preserved).
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"

# Point this repo at its own committed hooks dir (portable across machines).
git config core.hooksPath .githooks

chmod +x "$REPO_ROOT/.githooks/pre-commit"
chmod +x "$REPO_ROOT/.githooks/pre-push"
chmod +x "$REPO_ROOT/.githooks/post-commit"
chmod +x "$REPO_ROOT/.githooks/post-commit-graphify"
chmod +x "$REPO_ROOT/scripts/bump_version.py"

echo "installed: core.hooksPath = .githooks (repo-local)"
echo "  post-commit -> .githooks/post-commit (version bump + graphify)"
echo "  pre-commit  -> .githooks/pre-commit (pre-commit framework)"
echo "  pre-push    -> .githooks/pre-push (diff-aware pytest)"
echo "test it with: git commit --allow-empty -m 'fix: test bump'"
