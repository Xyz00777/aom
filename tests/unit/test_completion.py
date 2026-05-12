"""Unit tests for shell-completion helpers (F5).

Covers:
- ``session_id_completer`` returns the IDs of session directories
  under the given state dir, filtered by the ``prefix`` arg.
- Empty / missing state dirs return ``[]`` (never raise).
- ``completion_snippet`` returns a shell-appropriate snippet for
  bash, zsh, and fish, and raises ``ValueError`` for anything else.
"""

from pathlib import Path

import pytest


class TestSessionIdCompleter:
    def test_returns_session_dir_names(self, tmp_path: Path):
        from ansible_aom.completion import session_id_completer

        (tmp_path / "0193abcd-1111-7000-8000-000000000001").mkdir()
        (tmp_path / "0193abcd-2222-7000-8000-000000000002").mkdir()

        result = session_id_completer(prefix="", parsed_args=None, state_dir=tmp_path)

        assert sorted(result) == [
            "0193abcd-1111-7000-8000-000000000001",
            "0193abcd-2222-7000-8000-000000000002",
        ]

    def test_filters_by_prefix(self, tmp_path: Path):
        from ansible_aom.completion import session_id_completer

        (tmp_path / "aaa-1").mkdir()
        (tmp_path / "aaa-2").mkdir()
        (tmp_path / "bbb-1").mkdir()

        result = session_id_completer(prefix="aaa", parsed_args=None, state_dir=tmp_path)

        assert sorted(result) == ["aaa-1", "aaa-2"]

    def test_ignores_files(self, tmp_path: Path):
        from ansible_aom.completion import session_id_completer

        (tmp_path / "real-session").mkdir()
        (tmp_path / "stray-file.txt").write_text("not a session")

        result = session_id_completer(prefix="", parsed_args=None, state_dir=tmp_path)

        assert result == ["real-session"]

    def test_missing_state_dir_returns_empty(self, tmp_path: Path):
        from ansible_aom.completion import session_id_completer

        missing = tmp_path / "does-not-exist"
        result = session_id_completer(prefix="", parsed_args=None, state_dir=missing)

        assert result == []

    def test_empty_state_dir_returns_empty(self, tmp_path: Path):
        from ansible_aom.completion import session_id_completer

        result = session_id_completer(prefix="", parsed_args=None, state_dir=tmp_path)

        assert result == []

    def test_default_state_dir_is_local_state_aom_sessions(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """When state_dir is not supplied the completer derives it from $HOME."""
        from ansible_aom.completion import session_id_completer

        fake_home = tmp_path / "home"
        sessions = fake_home / ".local" / "state" / "aom" / "sessions"
        sessions.mkdir(parents=True)
        (sessions / "from-home-default").mkdir()

        monkeypatch.setenv("HOME", str(fake_home))

        result = session_id_completer(prefix="", parsed_args=None)

        assert "from-home-default" in result


class TestCompletionSnippet:
    def test_bash_snippet_contains_argcomplete_register(self):
        from ansible_aom.completion import completion_snippet

        snippet = completion_snippet("bash")

        assert "register-python-argcomplete" in snippet
        assert "aom" in snippet

    def test_zsh_snippet_contains_argcomplete_register(self):
        from ansible_aom.completion import completion_snippet

        snippet = completion_snippet("zsh")

        assert "register-python-argcomplete" in snippet
        assert "aom" in snippet

    def test_fish_snippet_contains_argcomplete_register(self):
        from ansible_aom.completion import completion_snippet

        snippet = completion_snippet("fish")

        assert "register-python-argcomplete" in snippet
        assert "aom" in snippet

    def test_unknown_shell_raises_value_error(self):
        from ansible_aom.completion import completion_snippet

        with pytest.raises(ValueError, match="unsupported shell"):
            completion_snippet("powershell")

    def test_supported_shells_constant(self):
        from ansible_aom.completion import SUPPORTED_SHELLS

        assert SUPPORTED_SHELLS == ("bash", "zsh", "fish")


class TestInspectCLICompleterWiring:
    """F5: session-id positionals on inspect parsers carry the completer."""

    def _completer_of(self, parser, dest):
        action = next(a for a in parser._actions if a.dest == dest)
        return getattr(action, "completer", None)

    def _subparser(self, parser, name):
        sub = next(a for a in parser._actions if a.__class__.__name__ == "_SubParsersAction")
        return sub.choices[name]

    def test_show_session_id_has_completer(self):
        from ansible_aom.completion import session_id_completer
        from ansible_aom.inspect.cli import _build_parser

        parser = _build_parser()
        show_parser = self._subparser(parser, "show")
        assert self._completer_of(show_parser, "session_id") is session_id_completer

    def test_diff_session_ids_have_completer(self):
        from ansible_aom.completion import session_id_completer
        from ansible_aom.inspect.cli import _build_parser

        parser = _build_parser()
        diff_parser = self._subparser(parser, "diff")
        assert self._completer_of(diff_parser, "session_id_1") is session_id_completer
        assert self._completer_of(diff_parser, "session_id_2") is session_id_completer


class TestReplayCLICompleterWiring:
    """F5: session-id positional on the replay parser carries the completer."""

    def test_replay_session_id_has_completer(self):
        from ansible_aom.completion import session_id_completer
        from ansible_aom.replay import _build_parser

        parser = _build_parser()
        action = next(a for a in parser._actions if a.dest == "session_id")
        assert getattr(action, "completer", None) is session_id_completer


class TestRerunCLICompleterWiring:
    """F5: session-id positional on the rerun parser carries the completer."""

    def test_rerun_session_id_has_completer(self):
        from ansible_aom.completion import session_id_completer
        from ansible_aom.rerun.cli import _create_parser

        parser = _create_parser()
        action = next(a for a in parser._actions if a.dest == "session_id")
        assert getattr(action, "completer", None) is session_id_completer
