import shlex
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_release_runs_only_daily_or_manually_on_main() -> None:
    config = yaml.safe_load((ROOT / ".github/workflows/release.yml").read_text())
    triggers = config.get("on", config.get(True, {}))
    assert triggers == {"schedule": [{"cron": "17 4 * * *"}], "workflow_dispatch": None}
    assert config["jobs"]["check"]["if"] == "github.ref == 'refs/heads/main'"
    assert config["concurrency"]["cancel-in-progress"] is False
    assert config["jobs"]["build"]["if"] == "needs.check.outputs.should_release == 'true'"
    assert config["jobs"]["build"]["steps"][0]["with"]["ref"] == "${{ needs.check.outputs.sha }}"
    assert "pypi" in config["jobs"]["github-release"]["needs"]


def test_release_evaluates_since_last_tag_after_a_docs_only_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = yaml.safe_load((ROOT / ".github/workflows/release.yml").read_text())
    evaluate = next(
        step for step in config["jobs"]["check"]["steps"] if step.get("id") == "evaluate"
    )

    def git(*args: str) -> None:
        subprocess.run(
            ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", *args],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )

    for name in ("GITHUB_REF_TYPE", "GITHUB_BASE_REF", "GITHUB_EVENT_PATH"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("GITHUB_OUTPUT", str(tmp_path / "outputs"))
    git("init", "-b", "main")
    manifest = tmp_path / "pyproject.toml"
    for version in ("1.0.0", "1.0.1"):
        manifest.write_text(f'[project]\nversion = "{version}"\n')
        git("add", "pyproject.toml")
        git("commit", "-m", version)
        if version == "1.0.0":
            git("tag", "v1.0.0")
    (tmp_path / "README.md").write_text("A later docs-only change.\n")
    git("add", "README.md")
    git("commit", "-m", "docs")
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts/check_version_bump.py").write_text(
        (ROOT / "scripts/check_version_bump.py").read_text()
    )

    outputs = tmp_path / "outputs"
    for expected in ("true", "false"):
        outputs.write_text("")
        command = evaluate["run"].replace(
            "python scripts/", f"{shlex.quote(sys.executable)} scripts/"
        )
        subprocess.run(["bash", "-eo", "pipefail", "-c", command], cwd=tmp_path, check=True)
        assert f"should_release={expected}" in outputs.read_text().splitlines()
        if expected == "true":
            git("tag", "v1.0.1")


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
