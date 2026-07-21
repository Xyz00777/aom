"""Tests for the auto-version-bump pre-commit hook.

The hook reads a conventional-commit message and bumps pyproject.toml
accordingly:

- ``feat:`` → minor bump
- ``fix:`` / ``refactor:`` / ``perf:`` → patch bump
- ``feat!:`` or ``BREAKING CHANGE:`` footer → major bump
- ``docs:``, ``chore:``, ``test:``, ``style:`` etc. → no bump
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

# The script lives outside of `src/` so make it importable without
# installing — adjust sys.path the same way pytest does for src layouts.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from bump_version import (  # noqa: E402  — sys.path manipulation above
    _bump_pyproject,
    _detect_bump,
)


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def _make_git_repo_with_linked_worktree(tmp_path: Path) -> tuple[Path, Path, Path]:
    main = tmp_path / "main"
    linked = tmp_path / "linked"
    main.mkdir()
    _git(main, "init", "-q")
    _git(main, "config", "user.name", "Version Hook Test")
    _git(main, "config", "user.email", "version-hook@example.invalid")
    _git(main, "config", "commit.gpgSign", "false")
    _git(main, "config", "core.hooksPath", str(main / ".git" / "hooks"))

    (main / "pyproject.toml").write_text('[project]\nname = "x"\nversion = "0.1.0"\n')
    (main / "tracked.txt").write_text("base\n")
    script = main / "scripts" / "bump_version.py"
    script.parent.mkdir()
    shutil.copy2(_REPO_ROOT / "scripts" / "bump_version.py", script)
    _git(main, "add", ".")
    _git(main, "commit", "-q", "-m", "chore: initial")
    _git(main, "worktree", "add", "-q", "-b", "linked", str(linked))
    return main, linked, script


class TestDetectBump:
    """Mapping from commit message to bump level."""

    def test_feat_triggers_minor(self):
        assert _detect_bump("feat: add the thing") == "minor"

    def test_feat_with_scope_triggers_minor(self):
        assert _detect_bump("feat(parser): add the thing") == "minor"

    def test_fix_triggers_patch(self):
        assert _detect_bump("fix: stop crashing on X") == "patch"

    def test_refactor_triggers_patch(self):
        assert _detect_bump("refactor: rename Y") == "patch"

    def test_perf_triggers_patch(self):
        assert _detect_bump("perf: faster grafting") == "patch"

    def test_bang_suffix_triggers_major(self):
        assert _detect_bump("feat!: remove old API") == "major"

    def test_bang_with_scope_triggers_major(self):
        assert _detect_bump("fix(core)!: drop method") == "major"

    def test_breaking_change_footer_triggers_major(self):
        msg = "feat: add new format\n\nBREAKING CHANGE: old format gone"
        assert _detect_bump(msg) == "major"

    def test_breaking_dash_form_also_triggers_major(self):
        msg = "feat: new\n\nBREAKING-CHANGE: gone"
        assert _detect_bump(msg) == "major"

    def test_docs_chore_test_style_do_not_bump(self):
        assert _detect_bump("docs: tweak readme") is None
        assert _detect_bump("chore: deps update") is None
        assert _detect_bump("test: more coverage") is None
        assert _detect_bump("style: format") is None

    def test_non_conventional_message_no_bump(self):
        assert _detect_bump("just words") is None
        assert _detect_bump("WIP something") is None

    def test_empty_message_no_bump(self):
        assert _detect_bump("") is None


class TestBumpPyproject:
    """The pyproject mutation itself."""

    def _make_pyproject(self, tmp_path: Path, version: str) -> Path:
        path = tmp_path / "pyproject.toml"
        path.write_text(f'[project]\nname = "x"\nversion = "{version}"\ndescription = "y"\n')
        return path

    def test_patch_bump(self, tmp_path: Path):
        path = self._make_pyproject(tmp_path, "0.2.0")
        old, new = _bump_pyproject(path, "patch")
        assert (old, new) == ("0.2.0", "0.2.1")
        assert 'version = "0.2.1"' in path.read_text()

    def test_minor_bump_resets_patch(self, tmp_path: Path):
        path = self._make_pyproject(tmp_path, "0.2.7")
        old, new = _bump_pyproject(path, "minor")
        assert (old, new) == ("0.2.7", "0.3.0")
        assert 'version = "0.3.0"' in path.read_text()

    def test_major_bump_resets_minor_and_patch(self, tmp_path: Path):
        path = self._make_pyproject(tmp_path, "1.4.9")
        old, new = _bump_pyproject(path, "major")
        assert (old, new) == ("1.4.9", "2.0.0")
        assert 'version = "2.0.0"' in path.read_text()

    def test_missing_version_line_is_noop(self, tmp_path: Path):
        path = tmp_path / "pyproject.toml"
        path.write_text('[project]\nname = "x"\n')
        assert _bump_pyproject(path, "patch") is None

    def test_unknown_level_is_noop(self, tmp_path: Path):
        path = self._make_pyproject(tmp_path, "0.2.0")
        assert _bump_pyproject(path, "weird") is None
        # Version unchanged.
        assert 'version = "0.2.0"' in path.read_text()

    def test_other_version_strings_not_touched(self, tmp_path: Path):
        """A ``requires-python = ">=3.14"`` or similar must NOT be bumped."""
        path = tmp_path / "pyproject.toml"
        path.write_text(
            "[project]\n"
            'name = "x"\n'
            'version = "0.2.0"\n'
            'requires-python = ">=3.14"\n'
            "\n[tool.ruff]\n"
            'target-version = "py314"\n'
        )
        _bump_pyproject(path, "patch")
        text = path.read_text()
        assert 'version = "0.2.1"' in text
        assert 'requires-python = ">=3.14"' in text
        assert 'target-version = "py314"' in text


class TestLinkedWorktreeHook:
    """Regression coverage for hooks installed in a shared Git directory."""

    def test_post_commit_bumps_and_amends_the_committing_worktree(self, tmp_path: Path):
        main, linked, script = _make_git_repo_with_linked_worktree(tmp_path)
        (main / ".git" / "hooks" / "post-commit").symlink_to(script)

        (linked / "tracked.txt").write_text("changed in linked worktree\n")
        _git(linked, "add", "tracked.txt")
        _git(linked, "commit", "-q", "-m", "fix: linked worktree change")

        assert 'version = "0.1.0"' in (main / "pyproject.toml").read_text()
        assert 'version = "0.1.1"' in (linked / "pyproject.toml").read_text()
        committed = _git(linked, "show", "HEAD:pyproject.toml").stdout
        assert 'version = "0.1.1"' in committed

    def test_git_resolved_operation_marker_prevents_worktree_bump(self, tmp_path: Path):
        main, linked, script = _make_git_repo_with_linked_worktree(tmp_path)

        (main / "tracked.txt").write_text("changed in main worktree\n")
        _git(main, "add", "tracked.txt")
        _git(main, "-c", "core.hooksPath=/dev/null", "commit", "-q", "-m", "fix: main change")
        (linked / "tracked.txt").write_text("changed in linked worktree\n")
        _git(linked, "add", "tracked.txt")
        _git(
            linked,
            "-c",
            "core.hooksPath=/dev/null",
            "commit",
            "-q",
            "-m",
            "fix: linked change",
        )

        marker = Path(_git(linked, "rev-parse", "--git-path", "CHERRY_PICK_HEAD").stdout.strip())
        marker.write_text(_git(linked, "rev-parse", "HEAD").stdout.strip())
        result = subprocess.run(
            [sys.executable, str(script)],
            cwd=linked,
            check=True,
            capture_output=True,
            text=True,
        )

        assert "skipped" in result.stderr
        assert 'version = "0.1.0"' in (main / "pyproject.toml").read_text()
        assert 'version = "0.1.0"' in (linked / "pyproject.toml").read_text()
