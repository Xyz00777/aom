"""Tests for the auto-version-bump pre-commit hook.

The hook reads a conventional-commit message and bumps pyproject.toml
accordingly:

- ``feat:`` → minor bump
- ``fix:`` / ``refactor:`` / ``perf:`` → patch bump
- ``feat!:`` or ``BREAKING CHANGE:`` footer → major bump
- ``docs:``, ``chore:``, ``test:``, ``style:`` etc. → no bump
"""

from __future__ import annotations

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
