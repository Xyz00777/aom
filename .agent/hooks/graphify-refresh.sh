#!/usr/bin/env bash
# graphify-refresh: AST-only refresh of the knowledge graph artifacts.
# Runs:
#   - graphify update .         (AST-only, no LLM cost)
#   - graphify tree              (writes GRAPH_TREE.html)
#   - graphify export wiki       (writes wiki/ for AGENTS.md nav hint)
# Then re-stages the tracked artifacts so the commit includes the refresh.
# Skips gracefully if graphify-out/ is not yet initialized or the CLI is missing.
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

# NixOS: graphify needs numpy which needs libstdc++.so.6.
# If it's not on the default LD_LIBRARY_PATH, try to add it.
if ! python3 -c "import numpy" 2>/dev/null; then
  _LIBSTDCXX="$(gcc -print-file-name=libstdc++.so.6 2>/dev/null || true)"
  if [ -n "$_LIBSTDCXX" ] && [ -f "$_LIBSTDCXX" ]; then
    _LIBDIR="$(dirname "$_LIBSTDCXX")"
    export LD_LIBRARY_PATH="${_LIBDIR}${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
  fi
fi

graphify update . || exit 1
graphify tree 2>/dev/null || true

if [ -f graphify-out/graph.json ]; then
  graphify export wiki 2>/dev/null || true
fi

git add -u \
  graphify-out/graph.json \
  graphify-out/.graphify_labels.json \
  graphify-out/.graphify_analysis.json \
  graphify-out/.graphify_semantic_marker \
  graphify-out/GRAPH_TREE.html \
  graphify-out/wiki/ 2>/dev/null || true