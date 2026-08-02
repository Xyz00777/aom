from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_flake_version_is_derived_from_pyproject() -> None:
    flake_text = (_REPO_ROOT / "flake.nix").read_text()

    assert "fromTOML (builtins.readFile ./pyproject.toml)" in flake_text
    assert "pyproject.toml" in flake_text
    assert 'version = "0.1.0"' not in flake_text
