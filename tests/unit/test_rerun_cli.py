"""Unit tests for the aom rerun subcommand."""

import json
from pathlib import Path

import pytest

from ansible_aom.rerun.cli import _resolve_session_id


def _make_session(state_dir: Path, session_id: str, start_time: str) -> Path:
    """Helper: create a session directory with a minimal meta.json."""
    session_path = state_dir / session_id
    session_path.mkdir(parents=True)
    meta = {
        "playbook": "site.yml",
        "ansible_args": ["-i", "inv.ini"],
        "start_time": start_time,
        "session_id": session_id,
        "status": "failed",
        "version": "1.1",
    }
    (session_path / "meta.json").write_text(json.dumps(meta))
    return session_path


class TestResolveSessionId:
    def test_explicit_full_id_returned_as_is(self, tmp_path: Path):
        state_dir = tmp_path / "sessions"
        sid = "01971111-1111-7000-8000-000000000001"
        _make_session(state_dir, sid, "2026-05-12T10:00:00Z")
        assert _resolve_session_id(state_dir, sid) == sid

    def test_explicit_short_id_resolved_to_full(self, tmp_path: Path):
        state_dir = tmp_path / "sessions"
        sid = "01971111-1111-7000-8000-000000000001"
        _make_session(state_dir, sid, "2026-05-12T10:00:00Z")
        assert _resolve_session_id(state_dir, "01971111") == sid

    def test_omitted_returns_most_recent(self, tmp_path: Path):
        state_dir = tmp_path / "sessions"
        older = "01971111-1111-7000-8000-000000000001"
        newer = "01971112-2222-7000-8000-000000000002"
        _make_session(state_dir, older, "2026-05-10T10:00:00Z")
        _make_session(state_dir, newer, "2026-05-12T10:00:00Z")
        assert _resolve_session_id(state_dir, None) == newer

    def test_unknown_id_raises(self, tmp_path: Path):
        state_dir = tmp_path / "sessions"
        sid = "01971111-1111-7000-8000-000000000001"
        _make_session(state_dir, sid, "2026-05-12T10:00:00Z")
        with pytest.raises(LookupError, match="No session matching"):
            _resolve_session_id(state_dir, "deadbeef")

    def test_no_sessions_at_all_raises(self, tmp_path: Path):
        state_dir = tmp_path / "sessions"
        state_dir.mkdir()
        with pytest.raises(LookupError, match="No sessions"):
            _resolve_session_id(state_dir, None)

    def test_ambiguous_short_id_raises(self, tmp_path: Path):
        state_dir = tmp_path / "sessions"
        sid_a = "01971111-1111-7000-8000-000000000001"
        sid_b = "01971111-2222-7000-8000-000000000002"
        _make_session(state_dir, sid_a, "2026-05-10T10:00:00Z")
        _make_session(state_dir, sid_b, "2026-05-12T10:00:00Z")
        with pytest.raises(LookupError, match="ambiguous"):
            _resolve_session_id(state_dir, "01971111")


from ansible_aom.rerun.cli import _compose_host_set  # noqa: E402


def _session_dict(events: list[dict]) -> dict:
    return {"events": events, "playbook": "site.yml", "ansible_args": []}


class TestComposeHostSet:
    def _events(self) -> list[dict]:
        return [
            {
                "_event": "v2_runner_on_failed",
                "task": {"name": "T1"},
                "hosts": {"web2": {"failed": True}},
            },
            {
                "_event": "v2_runner_on_unreachable",
                "task": {"name": "T2"},
                "hosts": {"web1": {"unreachable": True}},
            },
            {
                "_event": "v2_runner_on_ok",
                "task": {"name": "T3"},
                "hosts": {"web3": {"ok": True, "changed": True}},
            },
        ]

    def test_default_no_flag_returns_failed_only(self):
        result = _compose_host_set(
            _session_dict(self._events()),
            failed=False,
            unreachable=False,
            changes_only=False,
        )
        assert result == {"web2"}

    def test_failed_flag_returns_failed_hosts(self):
        result = _compose_host_set(
            _session_dict(self._events()),
            failed=True,
            unreachable=False,
            changes_only=False,
        )
        assert result == {"web2"}

    def test_unreachable_flag_includes_failed_and_unreachable(self):
        """--unreachable is a strict superset of --failed (per spec)."""
        result = _compose_host_set(
            _session_dict(self._events()),
            failed=False,
            unreachable=True,
            changes_only=False,
        )
        assert result == {"web1", "web2"}

    def test_changes_only_returns_changed_hosts(self):
        result = _compose_host_set(
            _session_dict(self._events()),
            failed=False,
            unreachable=False,
            changes_only=True,
        )
        assert result == {"web3"}

    def test_combined_flags_union(self):
        result = _compose_host_set(
            _session_dict(self._events()),
            failed=True,
            unreachable=True,
            changes_only=True,
        )
        assert result == {"web1", "web2", "web3"}

    def test_no_matching_hosts_returns_empty(self):
        result = _compose_host_set(
            _session_dict([]),
            failed=True,
            unreachable=True,
            changes_only=True,
        )
        assert result == set()


from ansible_aom.rerun.cli import _build_rerun_command  # noqa: E402


class TestBuildRerunCommand:
    def test_appends_limit_to_original_args(self):
        playbook, args = _build_rerun_command(
            session={
                "playbook": "site.yml",
                "ansible_args": ["-i", "inv.ini", "--tags", "web"],
            },
            hosts={"web2", "web3"},
        )
        assert playbook == "site.yml"
        # Limit value is sorted for determinism.
        assert args == ["-i", "inv.ini", "--tags", "web", "--limit", "web2,web3"]

    def test_overrides_existing_limit_flag(self):
        """A pre-existing --limit in the original args is dropped in favour of ours."""
        playbook, args = _build_rerun_command(
            session={
                "playbook": "site.yml",
                "ansible_args": ["-i", "inv.ini", "--limit", "web1", "--tags", "web"],
            },
            hosts={"web2"},
        )
        assert args == ["-i", "inv.ini", "--tags", "web", "--limit", "web2"]

    def test_overrides_short_l_flag(self):
        """``-l`` is the short form of ``--limit``; treat it the same."""
        playbook, args = _build_rerun_command(
            session={
                "playbook": "site.yml",
                "ansible_args": ["-l", "web1", "-v"],
            },
            hosts={"web2"},
        )
        assert args == ["-v", "--limit", "web2"]

    def test_overrides_limit_equals_form(self):
        """``--limit=hosts`` (single arg) is also dropped."""
        playbook, args = _build_rerun_command(
            session={
                "playbook": "site.yml",
                "ansible_args": ["--limit=web1", "-v"],
            },
            hosts={"web2"},
        )
        assert args == ["-v", "--limit", "web2"]

    def test_single_host_limit(self):
        playbook, args = _build_rerun_command(
            session={"playbook": "site.yml", "ansible_args": []},
            hosts={"web2"},
        )
        assert args == ["--limit", "web2"]

    def test_empty_host_set_raises(self):
        """No hosts → no rerun. Caller is expected to surface this earlier."""
        with pytest.raises(ValueError, match="empty host set"):
            _build_rerun_command(
                session={"playbook": "site.yml", "ansible_args": []},
                hosts=set(),
            )


import io  # noqa: E402
from contextlib import redirect_stdout  # noqa: E402

from ansible_aom.rerun.cli import _confirm  # noqa: E402


class TestConfirm:
    def test_yes_flag_skips_prompt_and_returns_true(self):
        # No input function provided — would raise EOFError if called.
        out = io.StringIO()
        with redirect_stdout(out):
            assert (
                _confirm(
                    playbook="site.yml",
                    args=["-i", "inv.ini", "--limit", "web2,web3"],
                    host_count=2,
                    assume_yes=True,
                    input_fn=None,
                )
                is True
            )
        text = out.getvalue()
        assert "ansible-playbook site.yml -i inv.ini --limit web2,web3" in text
        assert "2 host" in text
        # Warning still printed even with --yes — the user should see what's
        # about to happen.
        assert "non-idempotent" in text.lower()

    def test_default_yes_on_empty_input(self):
        """Bare Enter (empty string) accepts the default Y."""
        out = io.StringIO()
        with redirect_stdout(out):
            result = _confirm(
                playbook="site.yml",
                args=["--limit", "web2"],
                host_count=1,
                assume_yes=False,
                input_fn=lambda _prompt: "",
            )
        assert result is True

    def test_y_accepted(self):
        result = _confirm(
            playbook="site.yml",
            args=["--limit", "web2"],
            host_count=1,
            assume_yes=False,
            input_fn=lambda _prompt: "y",
        )
        assert result is True

    def test_yes_accepted(self):
        result = _confirm(
            playbook="site.yml",
            args=["--limit", "web2"],
            host_count=1,
            assume_yes=False,
            input_fn=lambda _prompt: "yes",
        )
        assert result is True

    def test_n_rejected(self):
        result = _confirm(
            playbook="site.yml",
            args=["--limit", "web2"],
            host_count=1,
            assume_yes=False,
            input_fn=lambda _prompt: "n",
        )
        assert result is False

    def test_no_rejected(self):
        result = _confirm(
            playbook="site.yml",
            args=["--limit", "web2"],
            host_count=1,
            assume_yes=False,
            input_fn=lambda _prompt: "no",
        )
        assert result is False

    def test_anything_else_rejected(self):
        result = _confirm(
            playbook="site.yml",
            args=["--limit", "web2"],
            host_count=1,
            assume_yes=False,
            input_fn=lambda _prompt: "maybe",
        )
        assert result is False

    def test_warning_includes_idempotency_language(self):
        out = io.StringIO()
        with redirect_stdout(out):
            _confirm(
                playbook="site.yml",
                args=["--limit", "web2"],
                host_count=1,
                assume_yes=True,
                input_fn=None,
            )
        text = out.getvalue().lower()
        # Must mention non-idempotent risk explicitly so the user sees it.
        assert "non-idempotent" in text


from ansible_aom.rerun.cli import _require_ansible_args  # noqa: E402


class TestRequireAnsibleArgs:
    def test_session_with_args_returns_them(self):
        session = {"playbook": "site.yml", "ansible_args": ["-i", "inv.ini"]}
        assert _require_ansible_args(session, "01971111") == ["-i", "inv.ini"]

    def test_session_with_empty_args_returns_empty_list(self):
        """An explicit [] is valid — the user originally ran `aom site.yml`."""
        session = {"playbook": "site.yml", "ansible_args": []}
        assert _require_ansible_args(session, "01971111") == []

    def test_missing_field_raises_with_clear_error(self):
        session = {"playbook": "site.yml"}  # no ansible_args key at all
        with pytest.raises(SystemExit) as excinfo:
            _require_ansible_args(session, "01971111-old-session")
        # SystemExit with non-zero exit code.
        assert excinfo.value.code == 2

    def test_missing_field_error_message_explains_schema(self, capsys):
        session = {"playbook": "site.yml"}
        with pytest.raises(SystemExit):
            _require_ansible_args(session, "01971111-old-session")
        err = capsys.readouterr().err
        assert "01971111-old-session" in err
        # Mentions the schema bump so the user understands.
        assert "schema" in err.lower() or "older" in err.lower() or "missing" in err.lower()
        # Mentions ansible_args so the user can grep their meta.json.
        assert "ansible_args" in err

    def test_none_value_treated_as_missing(self):
        """A null value (rare, but possible if hand-edited) is also missing."""
        session = {"playbook": "site.yml", "ansible_args": None}
        with pytest.raises(SystemExit):
            _require_ansible_args(session, "01971111")


from ansible_aom.rerun.cli import _create_parser  # noqa: E402


class TestCreateParser:
    def test_no_args(self):
        ns = _create_parser().parse_args([])
        assert ns.session_id is None
        assert ns.failed is False
        assert ns.unreachable is False
        assert ns.changes_only is False
        assert ns.yes is False

    def test_session_id_positional(self):
        ns = _create_parser().parse_args(["abc12345"])
        assert ns.session_id == "abc12345"

    def test_failed_flag(self):
        ns = _create_parser().parse_args(["--failed"])
        assert ns.failed is True

    def test_unreachable_flag(self):
        ns = _create_parser().parse_args(["--unreachable"])
        assert ns.unreachable is True

    def test_changes_only_flag(self):
        ns = _create_parser().parse_args(["--changes-only"])
        assert ns.changes_only is True

    def test_yes_short_form(self):
        ns = _create_parser().parse_args(["-y"])
        assert ns.yes is True

    def test_yes_long_form(self):
        ns = _create_parser().parse_args(["--yes"])
        assert ns.yes is True

    def test_state_dir_override(self, tmp_path: Path):
        ns = _create_parser().parse_args(["--state-dir", str(tmp_path)])
        assert ns.state_dir == tmp_path

    def test_combined(self):
        ns = _create_parser().parse_args(
            ["abc12345", "--failed", "--unreachable", "--yes"]
        )
        assert ns.session_id == "abc12345"
        assert ns.failed is True
        assert ns.unreachable is True
        assert ns.yes is True
