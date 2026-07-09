"""Tests for ``scripts/verify_anchors.py``.

The anchor checker is a pre-commit hook entry that scans design docs
for tokens of the form ``path:line-line`` (or ``path:line``) and
verifies each one against the file on disk. This test file pins the
narrow contract the task asked for:

- the grammar is **narrow** — only files with project extensions
  (``.py``, ``.md``, ``.toml``, ``.yaml``, ``.yml``, ``.json``, ``.sh``,
  ``.txt``) and a digit-only line / line-range match the regex, so
  false positives (timestamps, ratio expressions, etc.) are not
  extracted
- validation is **deterministic** — the first broken anchor wins, the
  script reports a single clear error and exits non-zero
- the script is **smoke-runnable from the CLI** with a clear exit code

The tests deliberately avoid relying on a particular repo layout by
constructing a tiny scratch repo under ``tmp_path`` and pointing the
checker at it. That makes the test self-contained and fast.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

# The script lives in ``scripts/`` outside the src layout, so we adjust
# ``sys.path`` (mirrors what ``tests/unit/test_bump_version.py`` does
# for the sibling script).
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
sys.path.insert(0, str(_SCRIPTS_DIR))

# Import the script as a module. We deliberately avoid importing the
# ``main`` function via ``import`` because the script also runs as
# ``__main__`` for the pre-commit hook; loading by file path keeps
# behaviour identical to a fresh interpreter.
_spec = importlib.util.spec_from_file_location("verify_anchors", _SCRIPTS_DIR / "verify_anchors.py")
assert _spec is not None and _spec.loader is not None
verify_anchors = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(verify_anchors)


# --- Test scratch repo helpers -------------------------------------------------


def _write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


# --- TestParseAnchor: the regex grammar ----------------------------------------


class TestParseAnchor:
    """The anchor grammar is narrow: ``path:line`` or ``path:line-line``."""

    def test_parses_path_with_single_line(self) -> None:
        anchor = verify_anchors.parse_anchor("src/ansible_aom/cli.py:200")
        assert anchor == ("src/ansible_aom/cli.py", 200, 200)

    def test_parses_path_with_line_range(self) -> None:
        anchor = verify_anchors.parse_anchor("src/ansible_aom/cli.py:200-203")
        assert anchor == ("src/ansible_aom/cli.py", 200, 203)

    def test_parses_dotted_filename_with_md_extension(self) -> None:
        anchor = verify_anchors.parse_anchor("docs/spec.md:12")
        assert anchor == ("docs/spec.md", 12, 12)

    def test_parses_toml_extension(self) -> None:
        anchor = verify_anchors.parse_anchor("pyproject.toml:5-10")
        assert anchor == ("pyproject.toml", 5, 10)

    def test_rejects_plain_text_with_no_colon(self) -> None:
        assert verify_anchors.parse_anchor("hello world") is None

    def test_rejects_iso_timestamp_with_dash(self) -> None:
        # Common false positive: ISO-8601 timestamps have `:` and `-`
        # but no file extension. The regex requires a file extension,
        # so this is filtered out.
        assert verify_anchors.parse_anchor("2026-06-30T12:34:56-08:00") is None

    def test_rejects_numeric_only_token(self) -> None:
        assert verify_anchors.parse_anchor("12345") is None

    def test_rejects_line_range_with_non_digit_endpoint(self) -> None:
        assert verify_anchors.parse_anchor("file.py:10-abc") is None

    def test_rejects_path_with_non_project_extension(self) -> None:
        # ``.exe`` is not in the project extension allowlist, so the
        # extractor returns None even though the syntax is well-formed.
        assert verify_anchors.parse_anchor("binary.exe:1") is None

    def test_rejects_zero_line(self) -> None:
        # Lines are 1-indexed; ``0`` is not a valid line.
        assert verify_anchors.parse_anchor("file.py:0") is None

    def test_rejects_inverted_range(self) -> None:
        # ``10-5`` is malformed: end < start.
        assert verify_anchors.parse_anchor("file.py:10-5") is None

    def test_parses_deeply_nested_path(self) -> None:
        anchor = verify_anchors.parse_anchor("a/b/c/d/e/f.py:42-100")
        assert anchor == ("a/b/c/d/e/f.py", 42, 100)


# --- TestExtractAnchors: scanning a design doc ----------------------------------


class TestExtractAnchors:
    """The extractor pulls every anchor token from a doc, including
    backtick-wrapped and bare forms. The grammar filters out non-anchor
    ``:``-bearing tokens (timestamps, URLs, ratios)."""

    def test_extracts_backtick_wrapped_anchors(self, tmp_path: Path) -> None:
        doc = tmp_path / "design.md"
        _write(doc, "See `src/foo.py:10-20` and `src/bar.py:5`.\n")
        anchors = verify_anchors.extract_anchors(doc)
        assert ("src/foo.py", 10, 20) in anchors
        assert ("src/bar.py", 5, 5) in anchors

    def test_extracts_bare_anchors(self, tmp_path: Path) -> None:
        doc = tmp_path / "design.md"
        _write(doc, "References: src/foo.py:10-20 and src/bar.py:5.\n")
        anchors = verify_anchors.extract_anchors(doc)
        assert ("src/foo.py", 10, 20) in anchors
        assert ("src/bar.py", 5, 5) in anchors

    def test_extracts_mixed_paths_in_single_line(self, tmp_path: Path) -> None:
        doc = tmp_path / "design.md"
        _write(
            doc,
            "Range anchors: `core/redaction.py:280-283`, `core/run_state.py:1208-1212`.\n",
        )
        anchors = verify_anchors.extract_anchors(doc)
        assert ("core/redaction.py", 280, 283) in anchors
        assert ("core/run_state.py", 1208, 1212) in anchors

    def test_ignores_iso_timestamps(self, tmp_path: Path) -> None:
        doc = tmp_path / "design.md"
        _write(doc, "Timestamp: 2026-06-30T12:34:56-08:00 and 2026-06-30T12:34:56Z.\n")
        anchors = verify_anchors.extract_anchors(doc)
        assert anchors == []

    def test_ignores_ratio_expressions(self, tmp_path: Path) -> None:
        # A ratio like ``1-10`` without a path is not an anchor; with
        # a path it could be an anchor (handled above). Verify the
        # bare case is filtered.
        doc = tmp_path / "design.md"
        _write(doc, "Ratio: 1-10 of events.\n")
        anchors = verify_anchors.extract_anchors(doc)
        assert anchors == []

    def test_returns_sorted_unique_anchors(self, tmp_path: Path) -> None:
        doc = tmp_path / "design.md"
        _write(
            doc,
            "`a.py:1-3` and `a.py:1-3` and `b.py:5-7` and `a.py:10`.\n",
        )
        anchors = verify_anchors.extract_anchors(doc)
        # The ``a.py:1-3`` duplicate is collapsed; the others are
        # distinct. The function returns the de-duplicated set as a
        # list, so we sort for the comparison.
        assert sorted(anchors) == sorted(
            [
                ("a.py", 1, 3),
                ("b.py", 5, 7),
                ("a.py", 10, 10),
            ]
        )

    def test_handles_empty_file(self, tmp_path: Path) -> None:
        doc = tmp_path / "empty.md"
        _write(doc, "")
        assert verify_anchors.extract_anchors(doc) == []


# --- TestValidateAnchor: the file / line-range check --------------------------


class TestValidateAnchor:
    """Validation must report the *first* broken anchor with a clear
    message and the location of the citation in the design doc."""

    def test_returns_none_when_path_and_range_valid(self, tmp_path: Path) -> None:
        # The repo root is parent of the script dir; we use a
        # scratch file inside tmp_path so the test does not depend
        # on any particular project file.
        target = tmp_path / "src" / "foo.py"
        _write(target, "\n".join(f"line {i}" for i in range(1, 21)))
        citation_file = tmp_path / "design.md"
        _write(citation_file, "`src/foo.py:5-7` is fine.\n")
        result = verify_anchors.validate_anchor(
            ("src/foo.py", 5, 7),
            citation_file=citation_file,
            repo_root=tmp_path,
        )
        assert result is None

    def test_reports_missing_file(self, tmp_path: Path) -> None:
        citation_file = tmp_path / "design.md"
        _write(citation_file, "`src/missing.py:1-3` is fine.\n")
        result = verify_anchors.validate_anchor(
            ("src/missing.py", 1, 3),
            citation_file=citation_file,
            repo_root=tmp_path,
        )
        assert result is not None
        assert "missing" in result.lower() or "not found" in result.lower()
        assert "src/missing.py" in result

    def test_reports_line_beyond_file_length(self, tmp_path: Path) -> None:
        target = tmp_path / "foo.py"
        _write(target, "\n".join(f"line {i}" for i in range(1, 6)))  # 5 lines
        citation_file = tmp_path / "design.md"
        _write(citation_file, "`foo.py:1-99` overshoots.\n")
        result = verify_anchors.validate_anchor(
            ("foo.py", 1, 99),
            citation_file=citation_file,
            repo_root=tmp_path,
        )
        assert result is not None
        assert "foo.py" in result
        # The error message names the bad line range.
        assert "1-99" in result or "1..99" in result or "99" in result

    def test_reports_single_line_anchor_beyond_file(self, tmp_path: Path) -> None:
        target = tmp_path / "short.py"
        _write(target, "only one line\n")  # 1 line
        citation_file = tmp_path / "design.md"
        _write(citation_file, "`short.py:50` is wrong.\n")
        result = verify_anchors.validate_anchor(
            ("short.py", 50, 50),
            citation_file=citation_file,
            repo_root=tmp_path,
        )
        assert result is not None
        assert "short.py" in result


# --- TestVerifyDoc: end-to-end single-doc driver ------------------------------


class TestVerifyDoc:
    """``verify_doc`` returns a list of broken-anchor messages and
    should short-circuit to a single failure (deterministic first
    broken anchor)."""

    def test_returns_empty_list_when_all_anchors_valid(self, tmp_path: Path) -> None:
        target = tmp_path / "src" / "ok.py"
        _write(target, "\n".join(f"line {i}" for i in range(1, 11)))
        doc = tmp_path / "design.md"
        _write(doc, "`src/ok.py:1-5` and `src/ok.py:7-9` are both fine.\n")
        broken = verify_anchors.verify_doc(doc, repo_root=tmp_path)
        assert broken == []

    def test_returns_one_error_per_broken_anchor(self, tmp_path: Path) -> None:
        target = tmp_path / "ok.py"
        _write(target, "\n".join(f"line {i}" for i in range(1, 11)))
        doc = tmp_path / "design.md"
        # First anchor is valid, second is bad (line out of range).
        _write(
            doc,
            "`ok.py:1-3` is valid, `ok.py:50-60` is wrong.\n",
        )
        broken = verify_anchors.verify_doc(doc, repo_root=tmp_path)
        assert len(broken) == 1
        assert "ok.py" in broken[0]
        assert "50" in broken[0]

    def test_handles_duplicate_anchors(self, tmp_path: Path) -> None:
        # Same anchor cited multiple times is reported once (de-duped
        # upstream by extract_anchors).
        target = tmp_path / "ok.py"
        _write(target, "\n".join(f"line {i}" for i in range(1, 11)))
        doc = tmp_path / "design.md"
        _write(
            doc,
            "`ok.py:50-60` here, and `ok.py:50-60` again.\n",
        )
        broken = verify_anchors.verify_doc(doc, repo_root=tmp_path)
        assert len(broken) == 1

    def test_handles_missing_target_file(self, tmp_path: Path) -> None:
        doc = tmp_path / "design.md"
        _write(doc, "`no/such/file.py:1-3` is cited.\n")
        broken = verify_anchors.verify_doc(doc, repo_root=tmp_path)
        assert len(broken) == 1
        assert "no/such/file.py" in broken[0]


# --- TestMain: the CLI entry point --------------------------------------------


class TestMain:
    """``main`` exits 0 on a clean doc and 1 on a broken anchor, with
    a clear stderr message naming the first failure."""

    def test_exits_zero_when_doc_has_no_anchors(self, tmp_path: Path, capsys) -> None:
        doc = tmp_path / "design.md"
        _write(doc, "No anchors here, just prose.\n")
        rc = verify_anchors.main([str(doc), "--repo-root", str(tmp_path)])
        assert rc == 0

    def test_exits_zero_when_all_anchors_valid(self, tmp_path: Path, capsys) -> None:
        target = tmp_path / "ok.py"
        _write(target, "\n".join(f"line {i}" for i in range(1, 11)))
        doc = tmp_path / "design.md"
        _write(doc, "`ok.py:1-3` is fine.\n")
        rc = verify_anchors.main([str(doc), "--repo-root", str(tmp_path)])
        assert rc == 0

    def test_exits_one_with_clear_stderr_on_broken_anchor(self, tmp_path: Path, capsys) -> None:
        doc = tmp_path / "design.md"
        _write(doc, "`missing.py:1-3` does not exist.\n")
        rc = verify_anchors.main([str(doc), "--repo-root", str(tmp_path)])
        assert rc == 1
        captured = capsys.readouterr()
        assert "missing.py" in captured.err
        # Error names the doc so the user knows where to fix.
        assert "design.md" in captured.err

    def test_first_broken_anchor_wins(self, tmp_path: Path, capsys) -> None:
        target = tmp_path / "ok.py"
        _write(target, "\n".join(f"line {i}" for i in range(1, 11)))
        doc = tmp_path / "design.md"
        # First anchor valid, second is missing-file, third is
        # out-of-range. The script should report the SECOND one
        # (the first broken anchor in citation order) and stop.
        _write(
            doc,
            "`ok.py:1-3` valid; `gone.py:1-3` missing; `ok.py:99-100` past end.\n",
        )
        rc = verify_anchors.main([str(doc), "--repo-root", str(tmp_path)])
        assert rc == 1
        captured = capsys.readouterr()
        assert "gone.py" in captured.err
        # The later broken anchor should NOT be in the stderr —
        # the script short-circuits on the first.
        assert "ok.py:99" not in captured.err

    def test_exits_two_when_doc_missing(self, tmp_path: Path, capsys) -> None:
        doc = tmp_path / "does_not_exist.md"
        rc = verify_anchors.main([str(doc), "--repo-root", str(tmp_path)])
        assert rc == 2
        captured = capsys.readouterr()
        assert "does_not_exist.md" in captured.err

    def test_exits_two_when_repo_root_missing(self, tmp_path: Path, capsys) -> None:
        doc = tmp_path / "design.md"
        _write(doc, "anything\n")
        rc = verify_anchors.main([str(doc), "--repo-root", str(tmp_path / "no_such_repo")])
        assert rc == 2
        captured = capsys.readouterr()
        assert "no_such_repo" in captured.err

    def test_exits_zero_with_help_flag(self, capsys) -> None:
        # ``--help`` triggers argparse's built-in ``SystemExit(0)``;
        # the script does not wrap it. We assert on the exit code
        # through pytest's ``raises`` and on the help text on stdout.
        with pytest.raises(SystemExit) as exc_info:
            verify_anchors.main(["--help"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        # Help text mentions the script's purpose.
        assert "anchor" in captured.out.lower() or "verify" in captured.out.lower()

    def test_uses_cwd_as_default_repo_root(self, tmp_path: Path, monkeypatch, capsys) -> None:
        target = tmp_path / "ok.py"
        _write(target, "\n".join(f"line {i}" for i in range(1, 11)))
        doc = tmp_path / "design.md"
        _write(doc, "`ok.py:1-3` is fine.\n")
        monkeypatch.chdir(tmp_path)
        rc = verify_anchors.main([str(doc)])
        assert rc == 0


# --- TestSmokeFromCommandLine: run the actual script as a subprocess ----------


class TestSmokeFromCommandLine:
    """The script must be smoke-runnable from the command line so the
    pre-commit hook can invoke it. This is the contract the pre-commit
    entry depends on."""

    def test_exits_zero_on_valid_design_doc(self, tmp_path: Path) -> None:
        target = tmp_path / "ok.py"
        _write(target, "\n".join(f"line {i}" for i in range(1, 11)))
        doc = tmp_path / "design.md"
        _write(doc, "`ok.py:1-3` is fine.\n")
        result = subprocess.run(
            [sys.executable, str(_SCRIPTS_DIR / "verify_anchors.py"), str(doc)],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert result.stderr == ""

    def test_exits_one_with_stderr_on_broken_anchor(self, tmp_path: Path) -> None:
        doc = tmp_path / "design.md"
        _write(doc, "`nope.py:1-3` is gone.\n")
        result = subprocess.run(
            [sys.executable, str(_SCRIPTS_DIR / "verify_anchors.py"), str(doc)],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 1
        assert "nope.py" in result.stderr
