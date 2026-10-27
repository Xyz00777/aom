import shlex
import tomllib
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_release_tools_are_locked_without_becoming_runtime_dependencies() -> None:
    # Given the project metadata and resolved dependency graph.
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())
    lock = tomllib.loads((ROOT / "uv.lock").read_text())
    tools = {"hatchling", "pyinstaller", "twine"}

    # When selecting the release-only dependency group.
    requirements = project.get("dependency-groups", {}).get("release", [])
    names = {requirement.split(">=")[0] for requirement in requirements}

    # Then release tools are resolved, but are not application requirements.
    assert tools <= names
    assert tools <= {package["name"] for package in lock["package"]}
    assert not tools & {
        requirement.split(">=")[0] for requirement in project["project"]["dependencies"]
    }


@pytest.mark.parametrize("workflow", ["ci.yml", "release.yml"])
def test_python_workflows_reject_lock_drift(workflow: str) -> None:
    # Given either workflow that builds Python distributions.
    config = yaml.safe_load((ROOT / ".github" / "workflows" / workflow).read_text())

    # When inspecting its uv execution policy.
    env = config.get("env", {})

    # Then every uv invocation must reject stale locks rather than resolve updates.
    assert env.get("UV_LOCKED") == "true"


def test_standalone_builder_uses_locked_tools_and_keeps_resolved_dependencies() -> None:
    # Given the release build commands, in execution order.
    config = yaml.safe_load((ROOT / ".github/workflows/release.yml").read_text())
    commands = [
        shlex.split(line)
        for step in config["jobs"]["build"]["steps"]
        for line in step.get("run", "").splitlines()
        if line.strip() and not line.startswith(" ")
    ]

    # When finding environment setup, distribution building and bundling.
    sync = next((command for command in commands if command[:2] == ["uv", "sync"]), [])
    build = next((command for command in commands if command[:2] == ["uv", "build"]), [])
    install = next((command for command in commands if command[:3] == ["uv", "pip", "install"]), [])

    # Then tools come from the lock, with no second runtime dependency resolution.
    assert "--group" in sync
    assert ["--group", "release"] == sync[sync.index("--group") : sync.index("--group") + 2]
    assert "--no-build-isolation" in build
    assert "--no-deps" in install
    assert any(command[:4] == ["uv", "run", "--no-sync", "pyinstaller"] for command in commands)
    assert not any(command[:3] == ["python", "-m", "pip"] for command in commands)


def test_nix_ci_builds_smoke_tests_and_evaluates_the_development_shell() -> None:
    # Given the independently resolved Nix package.
    config = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())

    # When inspecting its CI job.
    steps = config["jobs"].get("nix", {}).get("steps", [])
    commands = "\n".join(step.get("run", "") for step in steps)

    # Then a lock update must build and exercise AOM, not merely parse the flake.
    assert "nix build" in commands
    assert "--no-update-lock-file" in commands
    assert "./result/bin/aom --version" in commands
    assert "./result/bin/aom --help" in commands
    assert "devShells.x86_64-linux.default.drvPath" in commands


def test_dependabot_schedules_all_independent_dependency_sources() -> None:
    # Given the dependency-update configuration.
    path = ROOT / ".github/dependabot.yml"
    assert path.is_file()
    config = yaml.safe_load(path.read_text())

    # When selecting configured ecosystems.
    updates = config["updates"]

    # Then Python, Nix inputs and workflow actions all receive weekly updates.
    assert {update["package-ecosystem"] for update in updates} == {"uv", "nix", "github-actions"}
    assert all(update["directory"] == "/" for update in updates)
    assert all(update["schedule"]["interval"] == "weekly" for update in updates)
