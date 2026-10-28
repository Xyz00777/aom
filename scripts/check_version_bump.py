#!/usr/bin/env python3
"""Check software version bump on merge and pull request.

Validates that when application code or dependencies are modified (and not
only documentation or test files), the software version in pyproject.toml
is strictly greater than on the base branch (e.g. main).

Also provides `--check-release` for the release workflow to determine whether
an automatic package release should be created on push/merge to main.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tomllib
from collections.abc import Iterable
from pathlib import Path
from typing import Final

from packaging.version import Version

APPLICATION_PREFIXES: Final[tuple[str, ...]] = ("src/", "packaging/")
DEPENDENCY_FILES: Final[frozenset[str]] = frozenset(
    {"pyproject.toml", "uv.lock", "flake.nix", "flake.lock"}
)


def is_app_or_dep_path(path: str) -> bool:
    """Return True if path represents application code or dependencies."""
    normalized = path.replace("\\", "/").lstrip("./")
    if normalized.startswith(APPLICATION_PREFIXES):
        return True
    if normalized in DEPENDENCY_FILES:
        return True
    if normalized.startswith("schemas/") and not normalized.endswith(".md"):
        return True
    return False


def should_trigger_release(changed_files: Iterable[str]) -> bool:
    """Return True if any changed file belongs to application or dependencies."""
    return any(is_app_or_dep_path(p) for p in changed_files)


def is_version_higher(head_version: str, base_version: str) -> bool:
    """Return True if head_version is strictly greater than base_version."""
    return Version(head_version) > Version(base_version)


def _run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def get_pyproject_version(repo_root: Path, git_ref: str | None = None) -> str | None:
    """Extract project.version from pyproject.toml (worktree or given git ref)."""
    if git_ref is None:
        pyproject_path = repo_root / "pyproject.toml"
        if not pyproject_path.is_file():
            return None
        content = pyproject_path.read_text(encoding="utf-8")
    else:
        res = _run_git(["show", f"{git_ref}:pyproject.toml"], repo_root)
        if res.returncode != 0:
            return None
        content = res.stdout

    try:
        data = tomllib.loads(content)
        version = data.get("project", {}).get("version")
        return str(version) if isinstance(version, str) else None
    except tomllib.TOMLDecodeError, OSError:
        return None


def get_changed_files(repo_root: Path, base_ref: str, head_ref: str = "HEAD") -> list[str]:
    """Return the list of changed files between base_ref and head_ref."""
    merge_base_res = _run_git(["merge-base", base_ref, head_ref], repo_root)
    diff_base = (
        merge_base_res.stdout.strip()
        if merge_base_res.returncode == 0 and merge_base_res.stdout.strip()
        else base_ref
    )
    diff_res = _run_git(["diff", "--name-only", diff_base, head_ref], repo_root)
    if diff_res.returncode != 0:
        diff_res = _run_git(["diff", "--name-only", base_ref, head_ref], repo_root)
    return [line.strip() for line in diff_res.stdout.splitlines() if line.strip()]


def resolve_base_ref(repo_root: Path, explicit_base: str | None = None) -> str:
    """Resolve the base git ref to compare against."""
    if explicit_base:
        return explicit_base

    if "GITHUB_BASE_REF" in os.environ and os.environ["GITHUB_BASE_REF"].strip():
        base = os.environ["GITHUB_BASE_REF"].strip()
        check = _run_git(["rev-parse", "--verify", f"origin/{base}"], repo_root)
        if check.returncode == 0:
            return f"origin/{base}"
        return base

    if "GITHUB_EVENT_PATH" in os.environ:
        event_path = Path(os.environ["GITHUB_EVENT_PATH"])
        if event_path.is_file():
            try:
                event = json.loads(event_path.read_text(encoding="utf-8"))
                before = event.get("before")
                if isinstance(before, str) and before.strip() and before.strip("0") != "":
                    return before.strip()
            except json.JSONDecodeError, OSError:
                pass

    if _run_git(["rev-parse", "--verify", "origin/main"], repo_root).returncode == 0:
        return "origin/main"
    if _run_git(["rev-parse", "--verify", "main"], repo_root).returncode == 0:
        return "main"
    return "HEAD~1"


def check_version_bump(
    changed_files: Iterable[str] | None = None,
    base_version: str | None = None,
    head_version: str | None = None,
    repo_root: Path | None = None,
    base_ref: str | None = None,
    head_ref: str = "HEAD",
) -> tuple[bool, str]:
    """Check that software version was bumped if app/dep changes occurred."""
    root = repo_root or Path.cwd()
    if changed_files is None:
        resolved_base = resolve_base_ref(root, base_ref)
        files = get_changed_files(root, resolved_base, head_ref)
        b_ver = get_pyproject_version(root, resolved_base)
        h_ver = get_pyproject_version(root, head_ref)
    else:
        files = list(changed_files)
        b_ver = base_version
        h_ver = head_version

    if not should_trigger_release(files):
        return True, "No application or dependency changes detected; version bump not required."

    if b_ver is None:
        return (
            True,
            f"Initial release or no prior pyproject.toml at base; project version is {h_ver}.",
        )

    if h_ver is None:
        return False, "pyproject.toml is missing project.version at head."

    if is_version_higher(h_ver, b_ver):
        return (
            True,
            f"Version check passed: software version bumped from {b_ver} to {h_ver}.",
        )

    app_files = [f for f in files if is_app_or_dep_path(f)]
    formatted_files = ", ".join(app_files[:5]) + ("..." if len(app_files) > 5 else "")
    return (
        False,
        f"Application or dependency changes detected ({formatted_files}), but software version "
        f"in pyproject.toml ({h_ver}) is not higher than base ({b_ver}). "
        "Please bump project.version.",
    )


def evaluate_release_condition(
    changed_files: Iterable[str] | None = None,
    head_version: str | None = None,
    is_tag: bool = False,
    tag_name: str | None = None,
    output_file: Path | None = None,
    repo_root: Path | None = None,
    base_ref: str | None = None,
    head_ref: str = "HEAD",
) -> tuple[bool, str, str]:
    """Determine whether a release should be triggered and write GitHub outputs."""
    root = repo_root or Path.cwd()
    ver = head_version or get_pyproject_version(root, head_ref) or "0.0.0"

    if is_tag or os.environ.get("GITHUB_REF_TYPE") == "tag":
        should_rel = True
        tag = tag_name or os.environ.get("GITHUB_REF_NAME") or f"v{ver}"
    else:
        if changed_files is None:
            resolved_base = resolve_base_ref(root, base_ref)
            files = get_changed_files(root, resolved_base, head_ref)
        else:
            files = list(changed_files)
        should_rel = should_trigger_release(files)
        tag = f"v{ver}"

        # If the tag already exists on git, do not attempt to re-release.
        if (
            should_rel
            and _run_git(["rev-parse", "--verify", f"refs/tags/{tag}"], root).returncode == 0
        ):
            should_rel = False

    out_path = output_file
    if out_path is None and "GITHUB_OUTPUT" in os.environ:
        out_path = Path(os.environ["GITHUB_OUTPUT"])

    if out_path is not None:
        with open(out_path, "a", encoding="utf-8") as f:
            f.write(f"should_release={'true' if should_rel else 'false'}\n")
            f.write(f"version={ver}\n")
            f.write(f"tag={tag}\n")

    return should_rel, tag, ver


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Verify software version bump or evaluate release trigger."
    )
    parser.add_argument(
        "--base",
        dest="base_ref",
        help="Base git reference (default: auto-detected from PR/event or origin/main)",
    )
    parser.add_argument(
        "--head",
        dest="head_ref",
        default="HEAD",
        help="Head git reference to compare (default: HEAD)",
    )
    parser.add_argument(
        "--root",
        dest="repo_root",
        type=Path,
        default=Path.cwd(),
        help="Repository root directory",
    )
    parser.add_argument(
        "--check-release",
        action="store_true",
        help="Evaluate whether to trigger package release and export GITHUB_OUTPUT",
    )
    args = parser.parse_args(argv[1:])

    if args.check_release:
        should_rel, tag, ver = evaluate_release_condition(
            repo_root=args.repo_root,
            base_ref=args.base_ref,
            head_ref=args.head_ref,
        )
        status = "triggered" if should_rel else "skipped"
        print(f"[release-check] release {status} for {tag} (version {ver})")
        return 0

    ok, message = check_version_bump(
        repo_root=args.repo_root,
        base_ref=args.base_ref,
        head_ref=args.head_ref,
    )
    if ok:
        print(f"[version-check] {message}")
        return 0
    else:
        print(f"[version-check] ERROR: {message}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
