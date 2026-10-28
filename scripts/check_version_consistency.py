#!/usr/bin/env python3

from __future__ import annotations

import sys
import tomllib
from pathlib import Path


def find_version_mismatches(root: Path) -> list[str]:
    project_path = root / "pyproject.toml"
    project = tomllib.loads(project_path.read_text())
    version = project.get("project", {}).get("version")
    if not isinstance(version, str):
        raise ValueError("pyproject.toml is missing project.version")

    mismatches: list[str] = []
    lock_path = root / "uv.lock"
    lock = tomllib.loads(lock_path.read_text())
    lock_project = next(
        (package for package in lock.get("package", []) if package.get("name") == "ansible-aom"),
        None,
    )
    if lock_project is None:
        mismatches.append("uv.lock has no ansible-aom package entry")
    elif lock_project.get("version") != version:
        mismatches.append(
            f"uv.lock ansible-aom version is {lock_project.get('version')!r}; expected {version!r}"
        )

    flake_path = root / "flake.nix"
    if "version = pyproject.project.version;" not in flake_path.read_text():
        mismatches.append("flake.nix must derive version from pyproject.project.version")

    release_path = root / ".github" / "workflows" / "release.yml"
    release_text = release_path.read_text()
    required_release_contract = (
        "RELEASE_TAG:",
        'tomllib.loads(Path("pyproject.toml").read_text())',
        "if tag[1:] != version:",
    )
    if any(marker not in release_text for marker in required_release_contract):
        mismatches.append("release.yml must validate the tag against pyproject.toml")

    return mismatches


def main() -> int:
    try:
        mismatches = find_version_mismatches(Path(__file__).resolve().parents[1])
    except (OSError, tomllib.TOMLDecodeError, ValueError) as exc:
        print(f"version consistency check failed: {exc}", file=sys.stderr)
        return 1
    if mismatches:
        for mismatch in mismatches:
            print(f"version consistency check failed: {mismatch}", file=sys.stderr)
        return 1
    print("version consistency check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
