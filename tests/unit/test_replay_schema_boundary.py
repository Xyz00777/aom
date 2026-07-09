"""Schema-boundary regression test (Phase 8 / Task 8.3).

What this test pins
-------------------

The session record on disk gained a ``_schema_version`` field in
Phase 1 (Task 1.1). Two shape regimes exist in the wild:

* **AOM v1 sessions** (legacy): ``meta.json`` predates the schema-bump
  and has no ``_schema_version`` key at all. These still have to load
  cleanly and replay without a code change at the read site.
* **AOM v2 sessions** (current): ``meta.json`` was written by
  ``SessionManager.start_session`` and contains an explicit
  ``"_schema_version": 2`` marker. The reader must respect that
  marker verbatim and not rewrite it to ``1``.

The branch we are pinning lives in :func:`ansible_aom.session.store.load_session`:

    if "_schema_version" not in result:
        result["_schema_version"] = 1

That one line is the entire version-boundary contract for replay. If
someone later "tidies" the field (renames it, drops the default, or
unconditionally overwrites it with ``2``), legacy sessions either lose
their v1 marker or get an explicit v2 marker they did not earn. Both
failures are silent — there is no error, just incorrect metadata
propagated to ``aom inspect`` and ``aom replay``.

The test exercises the boundary through three lenses:

* ``TestLoadSessionSchemaBranch`` — calls ``load_session`` directly
  and asserts the branched value, plus a "round trip" of a real
  ``SessionManager``-produced session so the writer side is covered
  too.
* ``TestReplayHonorsSchemaBoundary`` — drives ``replay_session``
  against both v1 and v2 sessions and asserts the renderer still
  receives every event and ``handle_completion`` fires. The point is
  not that the renderer sees different events (it doesn't, on
  purpose — the boundary is invisible at the renderer level); the
  point is that the branch does not cause replay to short-circuit.
* ``TestSchemaBoundarySideBySide`` — same fixture under both regimes
  in the same ``tmp_path`` so a regression that conflates the two
  (e.g. accidentally reading ``_schema_version`` from a sibling
  session) would show up as one of the two assertions failing.

Why this is test-only
---------------------

A reading of :mod:`ansible_aom.session.store` confirms the branching
is already correct: legacy sessions get the ``1`` default, v2
sessions keep their ``2`` marker, and ``replay_session`` reads the
same dict either way. So no production change is needed; the value
of this test is locking the boundary so a future refactor (e.g. a
single ``MIGRATIONS`` map) does not blur the distinction.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Minimal but real-looking event stream. Same shape for both regimes
# so the renderer is held constant; only meta.json differs.
_BOUNDARY_EVENTS: list[dict] = [
    {
        "_event": "v2_playbook_on_start",
        "_timestamp": "2026-07-01T12:00:00Z",
    },
    {
        "_event": "v2_playbook_on_play_start",
        "_timestamp": "2026-07-01T12:00:00.1Z",
        "play": {"id": "p1", "name": "Boundary play"},
    },
    {
        "_event": "v2_playbook_on_task_start",
        "_timestamp": "2026-07-01T12:00:00.2Z",
        "task": {"id": "t1", "name": "Boundary task"},
    },
    {
        "_event": "v2_runner_on_ok",
        "_timestamp": "2026-07-01T12:00:01Z",
        "task": {"id": "t1", "name": "Boundary task"},
        "hosts": {"web1": {"changed": False}},
    },
    {
        "_event": "v2_playbook_on_stats",
        "_timestamp": "2026-07-01T12:00:02Z",
    },
]


def _make_v1_session(base: Path, session_id: str = "v1-legacy") -> Path:
    """Build a legacy AOM v1 session: meta.json with no ``_schema_version``.

    The on-disk shape is the same ``events.jsonl`` + ``meta.json`` that
    a pre-Phase-1 ``SessionManager`` would have written: ``playbook``,
    ``status``, ``start_time``, ``version`` (AOM package), and no
    ``_schema_version``. The reader is expected to default the missing
    field to ``1`` and to leave the rest of the v1 metadata untouched.
    """
    session_path = base / session_id
    session_path.mkdir(parents=True)
    (session_path / "events.jsonl").write_text(
        "\n".join(json.dumps(e) for e in _BOUNDARY_EVENTS) + "\n"
    )
    (session_path / "meta.json").write_text(
        json.dumps(
            {
                "session_id": session_id,
                "playbook": "legacy.yml",
                "status": "completed",
                "version": "1.1",
                "start_time": "2026-06-30T10:00:00Z",
            }
        )
    )
    return session_path


def _make_v2_session(base: Path, session_id: str = "v2-current") -> Path:
    """Build a current AOM v2 session: meta.json carries ``_schema_version: 2``.

    The on-disk shape matches what ``SessionManager.start_session``
    writes today: the explicit schema marker plus the usual playbook,
    status, and version fields. The reader must surface ``2`` verbatim
    — it must NOT be re-defaulted to ``1`` or replaced with another
    integer.
    """
    session_path = base / session_id
    session_path.mkdir(parents=True)
    (session_path / "events.jsonl").write_text(
        "\n".join(json.dumps(e) for e in _BOUNDARY_EVENTS) + "\n"
    )
    (session_path / "meta.json").write_text(
        json.dumps(
            {
                "session_id": session_id,
                "playbook": "current.yml",
                "status": "completed",
                "version": "1.2",
                "start_time": "2026-07-01T12:00:00Z",
                "_schema_version": 2,
            }
        )
    )
    return session_path


def _make_v1_and_v2_sessions(base: Path) -> tuple[Path, Path]:
    """Build both regimes side-by-side in the same ``base`` directory.

    Returning the two paths lets each test name them in the failure
    message, so a future reader who hits a failure knows immediately
    which side of the boundary regressed.
    """
    return _make_v1_session(base, "v1-legacy"), _make_v2_session(base, "v2-current")


class TestLoadSessionSchemaBranch:
    """``load_session`` is the branch site. Pin both sides here."""

    def test_v1_session_loads_with_defaulted_schema_version_1(self, tmp_path: Path) -> None:
        """Legacy v1 meta.json → ``_schema_version`` defaults to ``1``."""
        from ansible_aom.session.store import load_session

        _make_v1_session(tmp_path, "v1-legacy")

        session = load_session("v1-legacy", tmp_path)
        assert session is not None, (
            "load_session returned None for a v1 session; legacy reads must not fail"
        )
        assert session["_schema_version"] == 1, (
            f"v1 legacy session should default _schema_version to 1, "
            f"got {session.get('_schema_version')!r}; the load_session defaulting "
            f"branch regressed (see store.py:782-783)"
        )
        assert session["playbook"] == "legacy.yml"
        assert session["version"] == "1.1"
        assert session["status"] == "completed"

    def test_v2_session_loads_with_schema_version_2_verbatim(self, tmp_path: Path) -> None:
        """v2 meta.json → ``_schema_version`` stays at ``2``, not rewritten to ``1``."""
        from ansible_aom.session.store import load_session

        _make_v2_session(tmp_path, "v2-current")

        session = load_session("v2-current", tmp_path)
        assert session is not None
        assert session["_schema_version"] == 2, (
            f"v2 session should expose _schema_version == 2, got "
            f"{session.get('_schema_version')!r}; a future reader that "
            f"unconditionally writes 1 (or coerces absent/zero) would "
            f"regress this assertion"
        )
        assert session["playbook"] == "current.yml"
        assert session["version"] == "1.2"
        assert session["status"] == "completed"

    def test_v2_session_written_by_session_manager_round_trips_as_v2(self, tmp_path: Path) -> None:
        """End-to-end: ``SessionManager`` writes ``2``; ``load_session`` returns ``2``."""
        from ansible_aom.session.store import SessionManager, load_session

        mgr = SessionManager(session_dir=tmp_path, playbook="rt.yml")
        sid = mgr.start_session("rt.yml", ansible_args=[])
        mgr.end_session(sid, "completed", preflight_task_count=1, resolved_host_count=1)

        session = load_session(sid, tmp_path)
        assert session is not None
        assert session["_schema_version"] == 2, (
            f"SessionManager round-trip should yield _schema_version == 2, "
            f"got {session.get('_schema_version')!r}; the writer's marker "
            f"(store.py:327) and the reader's defaulting branch are out of sync"
        )
        assert session["playbook"] == "rt.yml"
        assert session["status"] == "completed"


class TestReplayHonorsSchemaBoundary:
    """The schema boundary must be invisible to ``replay_session`` and the renderer.

    The schema version is metadata, not a render hint. The renderer's
    job is to play back ``events.jsonl``; it doesn't care whether the
    meta file is v1-shaped or v2-shaped. These tests pin that
    invariant: the boundary does not affect what the renderer sees or
    how ``aom replay`` exits.
    """

    def test_replay_v1_session_drives_renderer_to_completion(self, tmp_path: Path) -> None:
        """v1 session: exit 0, every event reaches the renderer, completion fires."""
        from ansible_aom.drivers.replay import replay_session

        _make_v1_session(tmp_path, "v1-replay")

        renderer = MagicMock()
        exit_code = replay_session(
            session_dir=tmp_path,
            session_id="v1-replay",
            renderer=renderer,
            speed=0,
        )

        assert exit_code == 0, (
            f"replay_session returned {exit_code} on a v1 session; "
            f"v1 sessions must replay with exit 0 (same as v2)"
        )
        assert renderer.update_state.call_count == len(_BOUNDARY_EVENTS), (
            f"v1 session should replay all {len(_BOUNDARY_EVENTS)} events, "
            f"renderer saw {renderer.update_state.call_count}"
        )
        seen = [c.args[0]["_event"] for c in renderer.update_state.call_args_list]
        assert seen == [e["_event"] for e in _BOUNDARY_EVENTS], (
            f"v1 event order broken: {seen!r} != {[e['_event'] for e in _BOUNDARY_EVENTS]!r}"
        )
        renderer.handle_completion.assert_called_once_with(0, "completed")

    def test_replay_v2_session_drives_renderer_to_completion(self, tmp_path: Path) -> None:
        """v2 session: same shape, same exit code, same completion."""
        from ansible_aom.drivers.replay import replay_session

        _make_v2_session(tmp_path, "v2-replay")

        renderer = MagicMock()
        exit_code = replay_session(
            session_dir=tmp_path,
            session_id="v2-replay",
            renderer=renderer,
            speed=0,
        )

        assert exit_code == 0
        assert renderer.update_state.call_count == len(_BOUNDARY_EVENTS)
        seen = [c.args[0]["_event"] for c in renderer.update_state.call_args_list]
        assert seen == [e["_event"] for e in _BOUNDARY_EVENTS]
        renderer.handle_completion.assert_called_once_with(0, "completed")

    def test_replay_both_regimes_with_identical_event_stream(self, tmp_path: Path) -> None:
        """Renderer call sequence is identical for v1 and v2 (symmetry).

        If a future refactor makes the replay path *behave* differently
        for the two regimes (e.g. skip a v1-only event, or add a v2-only
        warning), this test will catch it. Today the contract is: the
        boundary is invisible to the renderer.
        """
        from ansible_aom.drivers.replay import replay_session

        v1_path = _make_v1_session(tmp_path, "v1-sym")
        v2_path = _make_v2_session(tmp_path, "v2-sym")
        assert v1_path != v2_path

        v1_renderer = MagicMock(name="v1")
        replay_session(session_dir=tmp_path, session_id="v1-sym", renderer=v1_renderer, speed=0)

        v2_renderer = MagicMock(name="v2")
        replay_session(session_dir=tmp_path, session_id="v2-sym", renderer=v2_renderer, speed=0)

        v1_events = [c.args[0] for c in v1_renderer.update_state.call_args_list]
        v2_events = [c.args[0] for c in v2_renderer.update_state.call_args_list]
        assert v1_events == v2_events, (
            "renderer received different event dicts for v1 vs v2 sessions; "
            "the schema boundary must be invisible to the renderer"
        )
        assert v1_renderer.handle_completion.call_args_list == (
            v2_renderer.handle_completion.call_args_list
        ), (
            "handle_completion calls differ between v1 and v2 replay; "
            "the schema boundary must not affect completion semantics"
        )


class TestSchemaBoundarySideBySide:
    """Both regimes in the same directory; the load path picks the right one.

    Putting v1 and v2 sessions in the same parent ``tmp_path`` exercises
    a regression mode that single-session tests cannot: a future "load
    the most-recent schema version" optimization that reads a sibling's
    ``_schema_version`` and applies it to every session in the
    directory. Both reads must be correct, and must each be correct
    independently of the other's presence.
    """

    def test_v1_and_v2_loaded_from_same_dir_branch_independently(self, tmp_path: Path) -> None:
        """Both reads correct when the two regimes coexist in one state dir."""
        from ansible_aom.session.store import load_session

        _make_v1_and_v2_sessions(tmp_path)

        v1 = load_session("v1-legacy", tmp_path)
        v2 = load_session("v2-current", tmp_path)

        assert v1 is not None and v2 is not None
        assert v1["_schema_version"] == 1, (
            f"v1 session in mixed dir should still default to 1, got "
            f"{v1.get('_schema_version')!r}; a sibling-aware reader could "
            f"accidentally promote it to 2"
        )
        assert v2["_schema_version"] == 2, (
            f"v2 session in mixed dir should still report 2, got {v2.get('_schema_version')!r}"
        )
        assert v1["playbook"] == "legacy.yml"
        assert v2["playbook"] == "current.yml"
        assert v1["version"] == "1.1"
        assert v2["version"] == "1.2"

    def test_replay_v1_and_v2_in_same_dir_both_complete(self, tmp_path: Path) -> None:
        """Both regimes replay cleanly when both directories coexist.

        Mirrors the integration scenario: a real user's state directory
        has a v1 session from last month and a v2 session from today.
        ``aom replay`` is invoked once against each; both must succeed
        independently.
        """
        from ansible_aom.drivers.replay import replay_session

        _make_v1_and_v2_sessions(tmp_path)

        v1_renderer = MagicMock(name="v1")
        v1_exit = replay_session(
            session_dir=tmp_path, session_id="v1-legacy", renderer=v1_renderer, speed=0
        )
        v2_renderer = MagicMock(name="v2")
        v2_exit = replay_session(
            session_dir=tmp_path, session_id="v2-current", renderer=v2_renderer, speed=0
        )

        assert v1_exit == 0, f"v1 replay returned {v1_exit}, expected 0"
        assert v2_exit == 0, f"v2 replay returned {v2_exit}, expected 0"
        assert v1_renderer.update_state.call_count == len(_BOUNDARY_EVENTS)
        assert v2_renderer.update_state.call_count == len(_BOUNDARY_EVENTS)
        v1_renderer.handle_completion.assert_called_once_with(0, "completed")
        v2_renderer.handle_completion.assert_called_once_with(0, "completed")


@pytest.mark.parametrize(
    ("session_id", "expected_schema_version", "expected_playbook"),
    [
        pytest.param("v1-legacy", 1, "legacy.yml", id="v1-defaults-to-1"),
        pytest.param("v2-current", 2, "current.yml", id="v2-keeps-2"),
    ],
)
def test_load_session_branches_at_schema_boundary(
    tmp_path: Path,
    session_id: str,
    expected_schema_version: int,
    expected_playbook: str,
) -> None:
    """Parametrised table-form: the two regimes and their expected branched values.

    The two regimes are checked by a single parametrised test so the
    test ID is the failure message. A future maintainer running
    ``pytest -k v1`` or ``-k v2`` can target either side of the
    boundary in isolation, which is the use case this table exists to
    support: when the schema bumps again (v3, v4, …), adding one more
    row to this parametrise — and one more ``_make_vN_session``
    helper — is the smallest possible diff.
    """
    from ansible_aom.session.store import load_session

    _make_v1_and_v2_sessions(tmp_path)

    session = load_session(session_id, tmp_path)
    assert session is not None, f"load_session returned None for {session_id!r}"
    assert session["_schema_version"] == expected_schema_version, (
        f"boundary branch wrong for {session_id!r}: "
        f"expected _schema_version == {expected_schema_version}, "
        f"got {session.get('_schema_version')!r}"
    )
    assert session["playbook"] == expected_playbook
