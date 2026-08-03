#!/usr/bin/env bash
# graphify-refresh: AST-only refresh of the knowledge graph artifacts.
#
# The graph is generated from the MAIN aom repo's source, so
# `graphify update .` / cluster-only / tree / export wiki run at the repo
# root. graphify writes its artifacts into graphify-out/, which is a git
# submodule owning its own repository — so the regenerated files live in
# that submodule repo and never pollute aom's PR diff.
#
# Flow:
#   1. Ensure the graphify-out submodule is checked out.
#   2. Regenerate artifacts from the main repo root (they land inside the
#      submodule worktree).
#   3. Commit + push inside the submodule (best-effort).
#   4. Stage the updated submodule pointer (gitlink) in the superproject,
#      so aom's diff stays a single line per regeneration.
# Skips gracefully if graphify-out/ is not initialized or the CLI is missing.
set -e

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo ".")"
cd "$REPO_ROOT"

if [ ! -d graphify-out ] || [ ! -f graphify-out/graph.json ]; then
  echo "graphify-out/ not initialized, skipping graph refresh"
  exit 0
fi

if ! command -v graphify >/dev/null 2>&1; then
  echo "graphify CLI not found, skipping graph refresh"
  exit 0
fi

# Ensure the submodule is populated so graphify-out is a real git repo.
git submodule update --init graphify-out 2>/dev/null || true

# Raise HTML viz node limit. Default (5000) is too small for this repo's
# ~12k-node graph. Override locally with `GRAPHIFY_VIZ_NODE_LIMIT=... git commit`.
export GRAPHIFY_VIZ_NODE_LIMIT="${GRAPHIFY_VIZ_NODE_LIMIT:-20000}"

# NixOS: graphify needs numpy which needs libstdc++.so.6.
# If it's not on the default LD_LIBRARY_PATH, try to add it.
if ! python3 -c "import numpy" 2>/dev/null; then
  _LIBSTDCXX="$(gcc -print-file-name=libstdc++.so.6 2>/dev/null || true)"
  if [ -n "$_LIBSTDCXX" ] && [ -f "$_LIBSTDCXX" ]; then
    _LIBDIR="$(dirname "$_LIBSTDCXX")"
    export LD_LIBRARY_PATH="${_LIBDIR}${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
  fi
fi

# Generate against the main repo source. Artifacts land in graphify-out/
# (the submodule worktree).
graphify install 2>/dev/null || true
graphify update . || exit 1
graphify cluster-only . 2>/dev/null || true
graphify tree 2>/dev/null || true

if [ -f graphify-out/graph.json ]; then
  graphify export wiki 2>/dev/null || true
fi

# Commit + push the refreshed artifacts inside the submodule.
if git -C graphify-out rev-parse --git-dir >/dev/null 2>&1 \
  && git -C graphify-out remote >/dev/null 2>&1; then
  if ! git -C graphify-out diff --quiet; then
    git -C graphify-out add -u \
      graph.json \
      .graphify_labels.json \
      .graphify_analysis.json \
      .graphify_semantic_marker \
      GRAPH_TREE.html \
      GRAPH_REPORT.md \
      graph.html \
      wiki/ 2>/dev/null || true
    git -C graphify-out commit -m "chore: regenerate graph artifacts" >/dev/null 2>&1 || true
    # Push is best-effort; a missing/denied remote must not fail the commit.
    git -C graphify-out push 2>/dev/null \
      || echo "graphify: submodule push skipped (no reachable remote)"
  fi
else
  echo "graphify: submodule repo/remote not present, artifacts left uncommitted"
fi

# Stage the updated submodule pointer (gitlink) in the superproject.
git add graphify-out 2>/dev/null || true
