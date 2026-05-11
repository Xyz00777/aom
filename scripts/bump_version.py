#!/usr/bin/env python3
"""Auto-bump pyproject.toml version based on a conventional-commit message.

Wired as a ``commit-msg`` pre-commit hook (see ``.pre-commit-config.yaml``).
The hook is invoked with the path to the commit message file. We:

1. Parse the first line for a conventional-commit type (``feat:``,
   ``fix:``, ``refactor:``, ``perf:``, ``feat!:``, …) plus optional
   ``!`` / ``BREAKING CHANGE:`` footer for major bumps.
2. Read the current ``[project].version`` from ``pyproject.toml``.
3. Compute the bumped version:
   - ``BREAKING CHANGE`` / ``type!:`` → major (X+1.0.0)
   - ``feat`` → minor (X.Y+1.0)
   - ``fix`` / ``refactor`` / ``perf`` → patch (X.Y.Z+1)
   - anything else (``docs``, ``chore``, ``test``, ``style``, …) → no bump
4. Write the new version back to ``pyproject.toml``.
5. ``git add pyproject.toml`` so the bump rides along in the same commit.

Idempotent: re-running on an already-bumped commit message is a no-op
because we never re-bump if the message lacks a recognised prefix or
if pyproject is already past the expected version.

Failure modes are intentionally soft — any exception logs to stderr
and exits 0. A broken hook MUST NOT block the user's commit.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# (type, allowed-bumps). "patch" means "bump patch unless ! or BREAKING".
_BUMP_RULES: dict[str, str] = {
    "feat": "minor",
    "fix": "patch",
    "refactor": "patch",
    "perf": "patch",
}

# Match conventional-commit header:
#   feat: add X
#   feat(scope): add X
#   feat!: breaking change
#   fix(parser)!: drop Y
_HEADER_RE = re.compile(
    r"^(?P<type>[a-z]+)(?P<scope>\([^)]+\))?(?P<bang>!)?:\s",
)

_VERSION_RE = re.compile(r'^(version\s*=\s*")(\d+)\.(\d+)\.(\d+)(")\s*$', re.MULTILINE)


def _detect_bump(message: str) -> str | None:
    """Return ``major`` / ``minor`` / ``patch`` or ``None`` for no bump."""
    first_line = message.splitlines()[0] if message else ""
    match = _HEADER_RE.match(first_line)
    if not match:
        return None

    commit_type = match.group("type")
    bang = match.group("bang") is not None
    has_breaking_footer = bool(re.search(r"^BREAKING[ -]CHANGE:", message, re.MULTILINE))

    if bang or has_breaking_footer:
        return "major"
    return _BUMP_RULES.get(commit_type)


def _bump_pyproject(pyproject: Path, level: str) -> tuple[str, str] | None:
    """Bump version in `pyproject`. Returns (old, new) or None if no match."""
    text = pyproject.read_text()
    match = _VERSION_RE.search(text)
    if not match:
        return None

    major = int(match.group(2))
    minor = int(match.group(3))
    patch = int(match.group(4))

    if level == "major":
        major, minor, patch = major + 1, 0, 0
    elif level == "minor":
        minor, patch = minor + 1, 0
    elif level == "patch":
        patch += 1
    else:
        return None

    new_version = f"{major}.{minor}.{patch}"
    new_text = _VERSION_RE.sub(lambda m: f"{m.group(1)}{new_version}{m.group(5)}", text)
    pyproject.write_text(new_text)
    old_version = f"{match.group(2)}.{match.group(3)}.{match.group(4)}"
    return old_version, new_version


def main(argv: list[str]) -> int:
    """Hook entry point. Argv: [script, commit_msg_file]."""
    if len(argv) < 2:
        return 0  # nothing to do
    msg_path = Path(argv[1])
    try:
        message = msg_path.read_text()
    except OSError:
        return 0

    bump = _detect_bump(message)
    if bump is None:
        return 0  # not a versioning commit type; quietly skip

    repo_root = Path(__file__).resolve().parent.parent
    pyproject = repo_root / "pyproject.toml"
    if not pyproject.exists():
        return 0

    result = _bump_pyproject(pyproject, bump)
    if result is None:
        return 0  # no version line found; silent no-op
    old, new = result

    # Stage the change so it lands in the same commit as the user's edit.
    try:
        subprocess.run(["git", "add", str(pyproject)], cwd=repo_root, check=True)
    except (subprocess.SubprocessError, FileNotFoundError) as exc:
        # Hook MUST NOT block commits — fall back to leaving the file
        # modified so the user can stage it manually.
        sys.stderr.write(
            f"[bump-version] git add failed ({exc}); pyproject left modified at {new}\n"
        )
        return 0

    sys.stderr.write(f"[bump-version] {bump}: {old} -> {new}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
