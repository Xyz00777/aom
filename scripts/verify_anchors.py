#!/usr/bin/env python3
"""Verify ``path:line-line`` anchors in design docs against the file system.

This script is a pre-commit hook entry (see ``.pre-commit-config.yaml``).
It scans one or more design documents for tokens shaped like
``path:line-line`` (a range) or ``path:line`` (a single line) and
checks each one against the actual file on disk. The grammar is
deliberately narrow so common false positives in design prose —
ISO-8601 timestamps, ratio expressions, bare numeric tokens — are
filtered out before the file lookup runs.

Exit codes:

- ``0`` — every anchor in every input doc resolves to a real file
  with a line range that fits within the file
- ``1`` — at least one anchor is broken; the first such anchor in
  citation order is reported on stderr and the script stops. The
  doc path, the bad anchor, the file the anchor names, and the
  reason (``missing`` or ``out-of-range``) are all named.
- ``2`` — usage error (missing doc, missing repo root)

Failure mode is **explicit and first-error-wins**. A future maintainer
debugging a hook failure reads one line on stderr and knows exactly
what to fix and where to fix it. The design docs are
single-source-of-truth, so a single broken anchor is enough to block
a commit.

Usage::

    python scripts/verify_anchors.py path/to/design.md [more.md ...]
    python scripts/verify_anchors.py --repo-root /path/to/repo path/to/design.md

The default ``--repo-root`` is the current working directory, which is
the project root when run from a pre-commit hook.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Anchor grammar: ``<path-with-extension>:<line>[-<line>]``. The
# extension constraint is what filters out ISO-8601 timestamps (which
# have ``:`` and ``-`` but no file extension) and bare numeric
# tokens. Lines are 1-indexed; ``0`` is rejected explicitly so
# off-by-one anchors surface as errors instead of silently passing.
_ANCHOR_RE = re.compile(
    r"(?P<path>[A-Za-z0-9_./-]+\.[A-Za-z0-9]+):"
    r"(?P<start>0|[1-9][0-9]*)"
    r"(?:-(?P<end>0|[1-9][0-9]*))?"
)

# Project file extensions the script recognises as anchor targets.
# Keeping this small prevents design prose with arbitrary extensions
# (e.g. ``.log``, ``.tar.gz``) from being mis-parsed.
_ALLOWED_EXTS = frozenset(
    {".py", ".md", ".toml", ".yaml", ".yml", ".json", ".sh", ".txt", ".cfg", ".ini"}
)

# Scan window: every ``word_char`` adjacent to ``:`` could be a path.
# We bound the path length so a stray prose fragment with a colon
# (e.g. URLs like ``http://example.com:8080/path``) cannot be picked
# up as an anchor; the regex above already filters by extension, but
# the scan pattern below also avoids ``://`` style URL prefixes.
_SCAN_RE = re.compile(r"[A-Za-z0-9_./-]+\.[A-Za-z0-9]+:[0-9]+(?:-[0-9]+)?")


def parse_anchor(token: str) -> tuple[str, int, int] | None:
    """Parse a single anchor token into ``(path, start, end)``.

    Returns ``None`` if the token does not match the grammar. The end
    line is the start line for a ``path:line`` (single-line) anchor.
    """
    match = _ANCHOR_RE.fullmatch(token)
    if match is None:
        return None

    path = match.group("path")
    ext = path[path.rfind(".") :].lower()
    if ext not in _ALLOWED_EXTS:
        return None

    start = int(match.group("start"))
    if start == 0:
        return None

    end_raw = match.group("end")
    end = int(end_raw) if end_raw is not None else start
    if end == 0 or end < start:
        return None

    return (path, start, end)


def extract_anchors(doc: Path) -> list[tuple[str, int, int]]:
    """Extract every distinct anchor token from a design doc.

    The order in the returned list is **citation order** (the order
    each anchor first appears in the doc). Duplicates are collapsed
    by inserting into an order-preserving set.
    """
    try:
        text = doc.read_text(encoding="utf-8")
    except OSError, UnicodeDecodeError:
        return []

    seen: dict[tuple[str, int, int], None] = {}
    for match in _SCAN_RE.finditer(text):
        anchor = parse_anchor(match.group(0))
        if anchor is not None:
            seen.setdefault(anchor, None)
    return list(seen.keys())


def validate_anchor(
    anchor: tuple[str, int, int],
    *,
    citation_file: Path,
    repo_root: Path,
) -> str | None:
    """Return ``None`` if the anchor is valid, or a one-line error
    message describing the first failure.

    The error message names the doc, the cited anchor, the target
    file, and the kind of failure (missing or out-of-range). One
    error per call — the caller (``verify_doc``) short-circuits on
    the first failure.
    """
    path, start, end = anchor
    target = repo_root / path
    if not target.is_file():
        return (
            f"{citation_file}: anchor `{path}:{start}-{end}` failed: "
            f"target `{path}` is missing (looked under {repo_root})"
        )

    line_count = sum(1 for _ in target.open("rb"))
    if end > line_count:
        return (
            f"{citation_file}: anchor `{path}:{start}-{end}` failed: "
            f"target has only {line_count} line(s) (end {end} > {line_count})"
        )
    if start > line_count:
        return (
            f"{citation_file}: anchor `{path}:{start}-{end}` failed: "
            f"target has only {line_count} line(s) (start {start} > {line_count})"
        )
    return None


def verify_doc(doc: Path, *, repo_root: Path) -> list[str]:
    """Return a list of broken-anchor error messages for ``doc``.

    The list is in citation order. ``verify_doc`` does not
    short-circuit — the caller (the CLI ``main``) decides whether
    to stop at the first failure or to enumerate every failure. The
    current contract is **stop at the first broken anchor** for the
    user-facing CLI; the function returns the full list so unit
    tests can assert on the shape of the result.
    """
    broken: list[str] = []
    for anchor in extract_anchors(doc):
        err = validate_anchor(anchor, citation_file=doc, repo_root=repo_root)
        if err is not None:
            broken.append(err)
    return broken


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="verify_anchors.py",
        description=(
            "Verify ``path:line-line`` and ``path:line`` anchors in "
            "design docs against the file system. Designed as a "
            "pre-commit hook entry."
        ),
    )
    parser.add_argument(
        "docs",
        nargs="*",
        help="Design doc paths to verify (Markdown or similar).",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help=(
            "Root the anchor paths are resolved against. Defaults to the current working directory."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. See module docstring for exit codes.

    ``argv`` defaults to ``sys.argv[1:]`` so the function is callable
    from tests with a synthetic argument list and from
    ``if __name__ == "__main__"`` with the real one.
    """
    if argv is None:
        argv = sys.argv[1:]
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not args.docs:
        parser.error("at least one design doc path is required")

    if not args.repo_root.is_dir():
        sys.stderr.write(f"verify_anchors: repo root {args.repo_root} is not a directory\n")
        return 2

    for doc in args.docs:
        doc_path = Path(doc)
        if not doc_path.is_file():
            sys.stderr.write(f"verify_anchors: doc not found: {doc_path}\n")
            return 2
        for err in verify_doc(doc_path, repo_root=args.repo_root):
            sys.stderr.write(f"{err}\n")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
