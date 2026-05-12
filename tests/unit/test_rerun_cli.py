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
