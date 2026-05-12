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
