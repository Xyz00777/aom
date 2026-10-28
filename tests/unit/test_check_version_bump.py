from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from check_version_bump import (  # noqa: E402
    check_version_bump,
    evaluate_release_condition,
    is_app_or_dep_path,
    is_version_higher,
    parse_version,
    should_trigger_release,
)


def _isolated_env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
        env=_isolated_env(),
    )


class TestPathClassification:
    def test_app_and_dependency_paths_recognized(self) -> None:
        assert is_app_or_dep_path("src/ansible_aom/cli.py") is True
        assert is_app_or_dep_path("src/ansible_aom/core/models.py") is True
        assert is_app_or_dep_path("packaging/aom.spec") is True
        assert is_app_or_dep_path("pyproject.toml") is True
        assert is_app_or_dep_path("uv.lock") is True
        assert is_app_or_dep_path("flake.nix") is True
        assert is_app_or_dep_path("flake.lock") is True
        assert is_app_or_dep_path("schemas/run_summary.v1.json") is True

    def test_doc_test_and_tooling_paths_not_app_or_dep(self) -> None:
        assert is_app_or_dep_path("README.md") is False
        assert is_app_or_dep_path("ARCHITECTURE.md") is False
        assert is_app_or_dep_path("docs/brainstorms/example.md") is False
        assert is_app_or_dep_path("schemas/README.md") is False
        assert is_app_or_dep_path("LICENSE") is False
        assert is_app_or_dep_path("tests/unit/test_cli.py") is False
        assert is_app_or_dep_path("tests/fixtures/ansible/simple.yml") is False
        assert is_app_or_dep_path(".github/workflows/ci.yml") is False
        assert is_app_or_dep_path(".pre-commit-config.yaml") is False
        assert is_app_or_dep_path("scripts/bump_version.py") is False
        assert is_app_or_dep_path(".gitignore") is False

    def test_should_trigger_release(self) -> None:
        assert should_trigger_release(["README.md", "tests/unit/test_cli.py"]) is False
        assert should_trigger_release(["docs/spec.md", "LICENSE"]) is False
        assert should_trigger_release([".github/workflows/ci.yml"]) is False
        assert should_trigger_release([]) is False

        assert should_trigger_release(["src/ansible_aom/cli.py"]) is True
        assert should_trigger_release(["README.md", "src/ansible_aom/cli.py"]) is True
        assert should_trigger_release(["tests/unit/test_cli.py", "src/ansible_aom/cli.py"]) is True
        assert should_trigger_release(["pyproject.toml"]) is True
        assert should_trigger_release(["uv.lock"]) is True


class TestVersionComparison:
    def test_parse_version(self) -> None:
        assert parse_version("0.102.12") == (0, 102, 12)
        assert parse_version("v1.2.3") == (1, 2, 3)
        with pytest.raises(ValueError, match="expected X.Y.Z"):
            parse_version("invalid")

    def test_is_version_higher(self) -> None:
        assert is_version_higher("0.102.13", "0.102.12") is True
        assert is_version_higher("0.103.0", "0.102.12") is True
        assert is_version_higher("1.0.0", "0.102.12") is True

        assert is_version_higher("0.102.12", "0.102.12") is False
        assert is_version_higher("0.102.11", "0.102.12") is False


class TestCheckVersionBumpLogic:
    def test_passes_when_no_app_or_dep_changes(self) -> None:
        ok, msg = check_version_bump(
            changed_files=["README.md", "tests/unit/test_x.py"],
            base_version="0.1.0",
            head_version="0.1.0",
        )
        assert ok is True
        assert "no application or dependency changes" in msg.lower()

    def test_fails_when_app_changed_without_bump(self) -> None:
        ok, msg = check_version_bump(
            changed_files=["src/ansible_aom/cli.py", "tests/unit/test_cli.py"],
            base_version="0.1.0",
            head_version="0.1.0",
        )
        assert ok is False
        assert "not higher" in msg.lower()

    def test_passes_when_app_changed_with_bump(self) -> None:
        ok, msg = check_version_bump(
            changed_files=["src/ansible_aom/cli.py"],
            base_version="0.1.0",
            head_version="0.1.1",
        )
        assert ok is True
        assert "bumped from 0.1.0 to 0.1.1" in msg

    def test_passes_when_base_version_missing(self) -> None:
        ok, msg = check_version_bump(
            changed_files=["src/ansible_aom/cli.py"],
            base_version=None,
            head_version="0.1.0",
        )
        assert ok is True
        assert "initial" in msg.lower() or "no prior" in msg.lower()


class TestGitRepositoryIntegration:
    @pytest.fixture
    def git_repo(self, tmp_path: Path) -> Path:
        repo = tmp_path / "repo"
        repo.mkdir()
        _git(repo, "init", "-q")
        _git(repo, "config", "user.name", "Test User")
        _git(repo, "config", "user.email", "test@example.com")
        _git(repo, "config", "commit.gpgSign", "false")

        (repo / "pyproject.toml").write_text('[project]\nname = "x"\nversion = "0.1.0"\n')
        (repo / "src").mkdir()
        (repo / "src" / "app.py").write_text("print('hello')\n")
        (repo / "tests").mkdir()
        (repo / "tests" / "test_app.py").write_text("def test(): pass\n")
        (repo / "README.md").write_text("# Readme\n")

        _git(repo, "add", ".")
        _git(repo, "commit", "-q", "-m", "chore: initial")
        return repo

    def test_git_repo_check_doc_only_passes(self, git_repo: Path) -> None:
        (git_repo / "README.md").write_text("# Updated Readme\n")
        _git(git_repo, "commit", "-am", "docs: update readme")

        ok, msg = check_version_bump(repo_root=git_repo, base_ref="HEAD~1", head_ref="HEAD")
        assert ok is True
        assert "no application or dependency changes" in msg.lower()

    def test_git_repo_check_app_change_without_bump_fails(self, git_repo: Path) -> None:
        (git_repo / "src" / "app.py").write_text("print('updated')\n")
        _git(git_repo, "commit", "-am", "fix: update app")

        ok, msg = check_version_bump(repo_root=git_repo, base_ref="HEAD~1", head_ref="HEAD")
        assert ok is False
        assert "not higher" in msg.lower()

    def test_git_repo_check_app_change_with_bump_passes(self, git_repo: Path) -> None:
        (git_repo / "src" / "app.py").write_text("print('updated')\n")
        (git_repo / "pyproject.toml").write_text('[project]\nname = "x"\nversion = "0.1.1"\n')
        _git(git_repo, "commit", "-am", "fix: update app with bump")

        ok, msg = check_version_bump(repo_root=git_repo, base_ref="HEAD~1", head_ref="HEAD")
        assert ok is True
        assert "bumped from 0.1.0 to 0.1.1" in msg


class TestEvaluateReleaseCondition:
    def test_release_skipped_for_doc_only_changes(self, tmp_path: Path) -> None:
        out_file = tmp_path / "github_output.txt"
        should_release, tag, ver = evaluate_release_condition(
            changed_files=["README.md", "tests/unit/test_app.py"],
            head_version="0.1.0",
            output_file=out_file,
        )
        assert should_release is False
        assert tag == "v0.1.0"
        assert ver == "0.1.0"
        assert "should_release=false" in out_file.read_text()

    def test_release_triggered_for_app_changes(self, tmp_path: Path) -> None:
        out_file = tmp_path / "github_output.txt"
        should_release, tag, ver = evaluate_release_condition(
            changed_files=["src/ansible_aom/cli.py"],
            head_version="0.1.1",
            output_file=out_file,
            repo_root=tmp_path,
        )
        assert should_release is True
        assert tag == "v0.1.1"
        assert ver == "0.1.1"
        assert "should_release=true" in out_file.read_text()
        assert "tag=v0.1.1" in out_file.read_text()
        assert "version=0.1.1" in out_file.read_text()

    def test_release_skipped_if_tag_already_exists(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        _git(repo, "init", "-q")
        _git(repo, "config", "user.name", "Test User")
        _git(repo, "config", "user.email", "test@example.com")
        _git(repo, "config", "commit.gpgSign", "false")
        (repo / "pyproject.toml").write_text('[project]\nname = "x"\nversion = "0.1.0"\n')
        _git(repo, "add", ".")
        _git(repo, "commit", "-q", "-m", "chore: init")
        _git(repo, "tag", "v0.1.0")

        out_file = tmp_path / "github_output.txt"
        should_release, tag, ver = evaluate_release_condition(
            changed_files=["src/app.py"],
            head_version="0.1.0",
            output_file=out_file,
            repo_root=repo,
        )
        assert should_release is False
        assert "should_release=false" in out_file.read_text()

    def test_release_skipped_if_version_not_higher_than_base(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        _git(repo, "init", "-q")
        _git(repo, "config", "user.name", "Test User")
        _git(repo, "config", "user.email", "test@example.com")
        _git(repo, "config", "commit.gpgSign", "false")
        (repo / "pyproject.toml").write_text('[project]\nname = "x"\nversion = "0.1.0"\n')
        (repo / "src").mkdir()
        (repo / "src" / "app.py").write_text("v1\n")
        _git(repo, "add", ".")
        _git(repo, "commit", "-q", "-m", "chore: init")

        (repo / "src" / "app.py").write_text("v2\n")
        _git(repo, "commit", "-am", "fix: update without bump")

        out_file = tmp_path / "github_output.txt"
        should_release, tag, ver = evaluate_release_condition(
            repo_root=repo,
            base_ref="HEAD~1",
            head_ref="HEAD",
            output_file=out_file,
        )
        assert should_release is False
        assert "should_release=false" in out_file.read_text()

    def test_release_triggered_for_tag_ref(self, tmp_path: Path) -> None:
        out_file = tmp_path / "github_output.txt"
        should_release, tag, ver = evaluate_release_condition(
            changed_files=[],
            head_version="0.1.2",
            is_tag=True,
            tag_name="v0.1.2",
            output_file=out_file,
        )
        assert should_release is True
        assert tag == "v0.1.2"
        assert ver == "0.1.2"
        assert "should_release=true" in out_file.read_text()


class TestCliMain:
    def test_main_check_release_exit_zero(self, tmp_path: Path, monkeypatch) -> None:
        from check_version_bump import main

        out_file = tmp_path / "gh_out"
        monkeypatch.setenv("GITHUB_OUTPUT", str(out_file))
        rc = main(["check_version_bump.py", "--check-release", "--root", str(_REPO_ROOT)])
        assert rc == 0
        assert out_file.exists()

    def test_main_version_check_fails_on_unbumped_app_change(self, tmp_path: Path, capsys) -> None:
        from check_version_bump import main

        repo = tmp_path / "repo"
        repo.mkdir()
        _git(repo, "init", "-q")
        _git(repo, "config", "user.name", "Test User")
        _git(repo, "config", "user.email", "test@example.com")
        _git(repo, "config", "commit.gpgSign", "false")
        (repo / "pyproject.toml").write_text('[project]\nname = "x"\nversion = "0.1.0"\n')
        (repo / "src").mkdir()
        (repo / "src" / "app.py").write_text("v1\n")
        _git(repo, "add", ".")
        _git(repo, "commit", "-q", "-m", "chore: init")

        (repo / "src" / "app.py").write_text("v2\n")
        _git(repo, "commit", "-am", "fix: update")

        rc = main(["check_version_bump.py", "--root", str(repo), "--base", "HEAD~1"])
        assert rc == 1
        captured = capsys.readouterr()
        assert "ERROR:" in captured.err
        assert "not higher than base" in captured.err

    def test_script_runs_with_stdlib_only_no_site_packages(self, tmp_path: Path) -> None:
        out_file = tmp_path / "gh_out"
        env = _isolated_env()
        env["GITHUB_OUTPUT"] = str(out_file)
        result = subprocess.run(
            [
                sys.executable,
                "-I",
                "-S",
                str(_REPO_ROOT / "scripts" / "check_version_bump.py"),
                "--check-release",
                "--root",
                str(_REPO_ROOT),
            ],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert out_file.exists()
