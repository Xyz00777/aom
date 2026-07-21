#!/usr/bin/env python3
"""Auto-bump pyproject.toml version on conventional-commit messages.

Installed as a ``post-commit`` git hook by ``scripts/install-hooks.sh``.

Why post-commit and not commit-msg / prepare-commit-msg: git takes an
index snapshot at the start of ``git commit`` and builds the commit
tree from that snapshot, even after hooks modify the live index. Plus
the pre-commit framework's stash/restore cycle around its own
pre-commit-stage hooks can also undo staged changes from a custom
commit-msg hook. The only reliable way to land a bump in the *same*
commit that triggered it is to:

1. Let the commit complete with whatever the user staged.
2. In post-commit: detect the conventional-commit type from the
   freshly-written HEAD message, bump pyproject + uv.lock, stage
   them, and ``git commit --amend --no-edit`` to fold them into the
   same commit. The SHA changes but the message is preserved.

Recursion is prevented by the ``AOM_BUMP_HOOK_RUNNING`` env var the
amend call sets — when the post-commit hook re-fires for the amend
commit, it sees the var and exits immediately.

Bump rules (conventional-commit type → semver level):
- ``BREAKING CHANGE`` footer / ``type!:`` → major (X+1.0.0)
- ``feat`` → minor (X.Y+1.0)
- ``fix`` / ``refactor`` / ``perf`` → patch (X.Y.Z+1)
- anything else (``docs``, ``chore``, ``test``, ``style``, …) → no bump

Failure modes are intentionally soft — any exception logs to stderr
and exits 0. A broken hook MUST NOT abort the user's workflow.
"""

from __future__ import annotations

import os
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


def _read_head_message(repo_root: Path) -> str:
    """Get the message of the just-created commit (HEAD)."""
    result = subprocess.run(
        ["git", "log", "-1", "--format=%B"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def _resolve_repo_root() -> Path:
    """Return the worktree whose Git invocation triggered this hook."""
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=True,
    )
    return Path(result.stdout.strip())


def _resolve_git_path(repo_root: Path, name: str) -> Path:
    """Resolve a Git administrative path for the active worktree."""
    result = subprocess.run(
        ["git", "rev-parse", "--git-path", name],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    path = Path(result.stdout.strip())
    return path if path.is_absolute() else repo_root / path


_HELP = """\
Usage: bump_version.py

Post-commit hook. Reads HEAD's commit message, detects the conventional-
commit type, and (if feat/fix/refactor/perf or ! / BREAKING) bumps the
version in pyproject.toml + uv.lock and `git commit --amend`s the bump
into HEAD.

Takes no arguments. Running this manually will mutate HEAD (amend the
current tip) — only do that if you actually want a bump folded in.
"""


def main(argv: list[str]) -> int:
    """Hook entry point.

    Called as a post-commit hook (no useful argv). Reads the message
    from ``HEAD``, bumps if appropriate, amends.
    """
    if any(a in {"-h", "--help"} for a in argv[1:]):
        sys.stdout.write(_HELP)
        return 0

    # Recursion guard: the `git commit --amend` below re-fires the
    # post-commit hook. Without this, we'd infinitely re-bump.
    if os.environ.get("AOM_BUMP_HOOK_RUNNING"):
        return 0

    try:
        repo_root = _resolve_repo_root()
    except subprocess.SubprocessError, FileNotFoundError:
        return 0
    pyproject = repo_root / "pyproject.toml"
    if not pyproject.exists():
        return 0

    try:
        message = _read_head_message(repo_root)
    except subprocess.SubprocessError, FileNotFoundError:
        return 0

    bump = _detect_bump(message)
    if bump is None:
        return 0  # not a versioning commit type; quietly skip

    # Bail out if we're mid-rebase / mid-merge / mid-cherry-pick — an
    # amend during those would scramble the in-flight sequencing.
    for marker in ("REBASE_HEAD", "MERGE_HEAD", "CHERRY_PICK_HEAD", "BISECT_LOG"):
        try:
            marker_path = _resolve_git_path(repo_root, marker)
        except subprocess.SubprocessError, FileNotFoundError:
            return 0
        if marker_path.exists():
            sys.stderr.write(
                f"[bump-version] skipped: {marker} present — bumping "
                "during rebase/merge/cherry-pick/bisect is unsafe\n"
            )
            return 0

    result = _bump_pyproject(pyproject, bump)
    if result is None:
        return 0  # no version line found; silent no-op
    old, new = result

    # Refresh uv.lock so its embedded version matches the bumped
    # pyproject. `uv lock` is fast for a pure version bump — uv only
    # rewrites the project's own [package] entry, not the entire
    # dependency graph. Best-effort: if uv isn't on PATH or the
    # command fails, fall through and stage just pyproject.
    uv_lock = repo_root / "uv.lock"
    files_to_stage = [pyproject]
    if uv_lock.exists():
        try:
            subprocess.run(
                ["uv", "lock", "--quiet"],
                cwd=repo_root,
                check=True,
                timeout=30,
            )
            files_to_stage.append(uv_lock)
        except (subprocess.SubprocessError, FileNotFoundError, OSError) as exc:
            sys.stderr.write(
                f"[bump-version] `uv lock` failed ({exc}); uv.lock not "
                "refreshed (run `uv lock` manually)\n"
            )

    # Stage and amend. AOM_BUMP_HOOK_RUNNING blocks the recursive
    # post-commit fire from the amend itself.
    try:
        subprocess.run(
            ["git", "add", "--", *(str(p) for p in files_to_stage)],
            cwd=repo_root,
            check=True,
        )
        env = os.environ.copy()
        env["AOM_BUMP_HOOK_RUNNING"] = "1"
        subprocess.run(
            ["git", "commit", "--amend", "--no-edit", "--no-verify"],
            cwd=repo_root,
            env=env,
            check=True,
            capture_output=True,
        )
    except (subprocess.SubprocessError, FileNotFoundError) as exc:
        sys.stderr.write(
            f"[bump-version] amend failed ({exc}); pyproject left at {new}, "
            "stage and amend manually with `git commit --amend --no-edit`\n"
        )
        return 0

    sys.stderr.write(f"[bump-version] {bump}: {old} -> {new} (folded into HEAD)\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
