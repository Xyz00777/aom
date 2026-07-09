"""Phase 1 / Task 1.1: meta.json `_schema_version` bump.

Per `.sisyphus/plans/v1-verbosity.md` Task 1.1 (Phase 1 of v1 work,
reversing QC-004): SessionManager now writes ``_schema_version: 2`` to
``meta.json``; readers (notably ``load_session``) default a missing
field to ``1`` so v1 (legacy) sessions stay loadable.

These tests pin the contract from the public API:

* Writer side: a freshly started + ended session has
  ``meta["_schema_version"] == 2`` and the rest of the existing v1
  fields are unchanged.
* Reader side: ``load_session`` returns the new field for a v2 session
  and returns ``1`` for a hand-built v1 legacy meta.
* Round trip: ``load_session`` of a session produced by ``SessionManager``
  exposes ``_schema_version == 2`` alongside the other meta keys.
"""

from __future__ import annotations

import json
from pathlib import Path

from ansible_aom.session.store import SessionManager, load_session


def _start_and_end(tmp_path: Path) -> str:
    mgr = SessionManager(session_dir=tmp_path, playbook="site.yml")
    sid = mgr.start_session("site.yml", ansible_args=[])
    mgr.end_session(
        sid,
        "completed",
        preflight_task_count=4,
        resolved_host_count=2,
    )
    return sid


def test_start_session_writes_schema_version_2(tmp_path: Path) -> None:
    """``start_session`` persists ``_schema_version: 2`` immediately.

    The field is written at session-start (before ``end_session`` runs)
    so a crash mid-run still leaves an unambiguous schema marker for
    recovery / replay code to branch on.
    """
    mgr = SessionManager(session_dir=tmp_path / "sessions", playbook="play.yml")
    sid = mgr.start_session("play.yml", ansible_args=[])

    meta = json.loads((tmp_path / "sessions" / sid / "meta.json").read_text())
    assert meta["_schema_version"] == 2


def test_end_session_preserves_schema_version_2(tmp_path: Path) -> None:
    """``end_session`` does not strip the schema field added at start."""
    sid = _start_and_end(tmp_path)

    meta = json.loads((tmp_path / sid / "meta.json").read_text())
    assert meta["_schema_version"] == 2


def test_schema_version_2_coexists_with_existing_meta_fields(tmp_path: Path) -> None:
    """The bump is additive: every v1 field is still present and unchanged.

    Guards against accidentally renaming or dropping ``version``,
    ``playbook``, ``session_id``, ``start_time`` while adding the new
    field.
    """
    sid = _start_and_end(tmp_path)
    meta = json.loads((tmp_path / sid / "meta.json").read_text())

    assert meta["_schema_version"] == 2
    assert meta["playbook"] == "site.yml"
    assert meta["session_id"] == sid
    assert meta["status"] == "completed"
    assert meta["version"] == "1.2"  # AOM package version, NOT schema version
    assert meta["preflight_task_count"] == 4
    assert meta["resolved_host_count"] == 2
    assert "start_time" in meta
    assert "end_time" in meta


def test_load_session_exposes_schema_version_2(tmp_path: Path) -> None:
    """``load_session`` surfaces the new field on the returned dict."""
    sid = _start_and_end(tmp_path)

    session = load_session(sid, tmp_path)
    assert session is not None
    assert session["_schema_version"] == 2


def test_load_session_defaults_missing_schema_version_to_1(tmp_path: Path) -> None:
    """A v1 legacy ``meta.json`` (no ``_schema_version`` field) loads cleanly
    and reports ``_schema_version == 1`` so downstream code can branch on
    the new key without special-casing absence.
    """
    legacy = tmp_path / "legacy-session-id"
    legacy.mkdir()
    (legacy / "meta.json").write_text(
        json.dumps(
            {
                "session_id": "legacy-session-id",
                "playbook": "old.yml",
                "status": "completed",
                "version": "1.1",
                "start_time": "2026-06-30T10:00:00Z",
            }
        )
    )
    (legacy / "events.jsonl").write_text("")

    session = load_session("legacy-session-id", tmp_path)
    assert session is not None
    assert session["_schema_version"] == 1
    # Existing v1 fields must survive the defaulting pass untouched.
    assert session["playbook"] == "old.yml"
    assert session["version"] == "1.1"
    assert session["status"] == "completed"


def test_load_session_of_v2_session_round_trips_schema_version_2(tmp_path: Path) -> None:
    """End-to-end: SessionManager writes v2; load_session returns v2."""
    sid = _start_and_end(tmp_path)
    session = load_session(sid, tmp_path)
    assert session is not None
    assert session["_schema_version"] == 2
    assert session["playbook"] == "site.yml"
    assert session["status"] == "completed"
