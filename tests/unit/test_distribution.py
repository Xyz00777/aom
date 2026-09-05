from __future__ import annotations

import subprocess
import sys
import tarfile
import tomllib
import zipfile
from collections.abc import Iterator
from pathlib import Path

import pytest

from ansible_aom.ansible import runner

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_VERSION = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())["project"]["version"]
WHEEL_RESOURCES = {
    "ansible_aom/ansible/callback/aom_jsonl.py",
    "ansible_aom/callbacks/aom_connection.py",
    "ansible_aom/core/default_config.yaml",
}
SDIST_RESOURCES = {
    f"ansible_aom-{PACKAGE_VERSION}/src/ansible_aom/ansible/callback/aom_jsonl.py",
    f"ansible_aom-{PACKAGE_VERSION}/src/ansible_aom/callbacks/aom_connection.py",
    f"ansible_aom-{PACKAGE_VERSION}/src/ansible_aom/core/default_config.yaml",
}


@pytest.fixture
def built_distributions(tmp_path: Path) -> Iterator[tuple[Path, Path]]:
    result = subprocess.run(
        [
            "uv",
            "build",
            "--wheel",
            "--sdist",
            "--offline",
            "--out-dir",
            str(tmp_path),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, (
        f"uv build failed:\nstdout={result.stdout}\nstderr={result.stderr}"
    )

    wheel = tmp_path / f"ansible_aom-{PACKAGE_VERSION}-py3-none-any.whl"
    sdist = tmp_path / f"ansible_aom-{PACKAGE_VERSION}.tar.gz"
    assert wheel.is_file()
    assert sdist.is_file()
    yield wheel, sdist


def test_wheel_contains_runtime_resources_and_current_metadata(
    built_distributions: tuple[Path, Path],
) -> None:
    wheel, _ = built_distributions

    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        assert WHEEL_RESOURCES <= names
        metadata = archive.read(f"ansible_aom-{PACKAGE_VERSION}.dist-info/METADATA").decode()

    assert f"Version: {PACKAGE_VERSION}" in metadata


def test_sdist_contains_runtime_sources_and_current_metadata(
    built_distributions: tuple[Path, Path],
) -> None:
    _, sdist = built_distributions

    with tarfile.open(sdist, "r:gz") as archive:
        names = set(archive.getnames())
        assert SDIST_RESOURCES <= names
        metadata = archive.extractfile(f"ansible_aom-{PACKAGE_VERSION}/PKG-INFO")
        assert metadata is not None
        metadata_text = metadata.read().decode()

    assert f"Version: {PACKAGE_VERSION}" in metadata_text


def _run_module_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "ansible_aom", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )


def test_clean_module_cli_version_reports_current_version() -> None:
    result = _run_module_cli("--version")

    assert result.returncode == 0
    assert result.stdout.startswith(f"aom {PACKAGE_VERSION} (")
    assert result.stderr == ""


def test_clean_module_cli_help_reports_usage_without_ansible() -> None:
    result = _run_module_cli("--help")

    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()
    assert "ansible-playbook" in result.stdout
    assert result.stderr == ""


def test_runtime_resources_are_inside_the_package() -> None:
    package_dir = Path(runner.__file__).resolve().parent.parent

    assert (package_dir / "ansible" / "callback" / "aom_jsonl.py").is_file()
    assert (package_dir / "callbacks" / "aom_connection.py").is_file()
    assert (package_dir / "core" / "default_config.yaml").is_file()


def test_frozen_child_environment_restores_original_library_path(monkeypatch) -> None:
    monkeypatch.setattr(runner.sys, "frozen", True, raising=False)
    monkeypatch.setenv("LD_LIBRARY_PATH", "/tmp/pyinstaller-libs")
    monkeypatch.setenv("LD_LIBRARY_PATH_ORIG", "/usr/lib:/lib")

    child_env = runner._child_environment()

    assert child_env["LD_LIBRARY_PATH"] == "/usr/lib:/lib"
    assert child_env["LD_LIBRARY_PATH_ORIG"] == "/usr/lib:/lib"


def test_normal_child_environment_preserves_library_path(monkeypatch) -> None:
    monkeypatch.delattr(runner.sys, "frozen", raising=False)
    monkeypatch.setenv("LD_LIBRARY_PATH", "/usr/lib:/lib")

    child_env = runner._child_environment()

    assert child_env["LD_LIBRARY_PATH"] == "/usr/lib:/lib"
