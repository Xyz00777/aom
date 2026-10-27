from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from check_version_consistency import find_version_mismatches  # noqa: E402


def test_repository_versions_are_consistent() -> None:
    assert find_version_mismatches(_REPO_ROOT) == []


def test_uv_lock_version_mismatch_is_reported(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "1.2.3"\n')
    (tmp_path / "uv.lock").write_text('[[package]]\nname = "ansible-aom"\nversion = "1.2.4"\n')
    (tmp_path / "flake.nix").write_text("version = pyproject.project.version;\n")
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / ".github/workflows/release.yml").write_text("pyproject.toml\n")

    mismatches = find_version_mismatches(tmp_path)

    assert any("uv.lock" in mismatch for mismatch in mismatches)


def test_version_derivation_contracts_are_required(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "1.2.3"\n')
    (tmp_path / "uv.lock").write_text('[[package]]\nname = "ansible-aom"\nversion = "1.2.3"\n')
    (tmp_path / "flake.nix").write_text('version = "1.2.3";\n')
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / ".github/workflows/release.yml").write_text("version: 1.2.3\n")

    mismatches = find_version_mismatches(tmp_path)

    assert any("flake.nix" in mismatch for mismatch in mismatches)
    assert any("release.yml" in mismatch for mismatch in mismatches)


def test_missing_project_version_fails_cleanly(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'ansible-aom'\n")

    with pytest.raises(ValueError, match="project.version"):
        find_version_mismatches(tmp_path)
