"""End-to-end round-trip for ``aom rerun`` (Item #4).

Exercises the full pipeline:

1. **Record a live session.** Drive ``run_playbook`` against a fake
   ansible-playbook shim that emits JSONL events flagging ``web1,web4``
   as ok and ``web2,web3`` as failed (one of the OK hosts also
   ``changed=true``). This produces a real session directory under
   ``tmp_path`` with ``meta.json`` (populated ``ansible_args``) plus
   ``events.jsonl``.

2. **Rerun and capture argv.** Invoke ``rerun.cli.main`` with the
   recorded session ID, patching ``runner._build_command`` to a second
   fake shim that records its argv to a file and exits 0. The shim
   never executes anything real — it just observes the argv that
   ``rerun`` composed.

3. **Assert the spawn line.** Verify ``--limit`` carries exactly the
   expected hosts (set comparison), the original ``ansible_args`` are
   preserved verbatim, and any pre-existing ``--limit`` is replaced
   (not duplicated).

Also covers the refusal path: a session whose ``ansible_args`` is
``None`` (old schema) prints a clear error, exits 2, and never spawns
the capture shim.

Decision points:

- We patch ``ansible_aom.runner._build_command`` at the module level
  rather than relying on PATH manipulation; that's the same trick the
  existing ``test_runner_session_recording.py`` uses, and it avoids
  the "shutil.which sees a real ansible-playbook on the developer
  machine" gotcha.
- ``--changes-only`` is exercised on a separate recorded session
  because the spec requires ``v2_runner_on_ok`` events with
  ``changed=true`` (see ``core/session.py::collect_changed_hosts``).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch


def _fake_ansible_command(events: list[dict], exit_code: int = 0) -> tuple[str, list[str]]:
    """(command, args) pair emitting `events` then exiting with `exit_code`.

    Mirrors the helper in test_runner_session_recording.py — kept local
    so this test file is self-contained.
    """
    payload = json.dumps(events)
    code = (
        "import json, sys; "
        f"events = json.loads({payload!r}); "
        "[sys.stdout.write(json.dumps(e) + '\\n') for e in events]; "
        "sys.stdout.flush(); "
        f"sys.exit({exit_code})"
    )
    return sys.executable, ["-c", code]


def _make_capture_build_command(argv_log: Path, exit_code: int = 0):
    """Factory: a fake ``_build_command`` that records its inputs.

    Returns a callable suitable for ``patch(..., side_effect=...)`` that
    wraps the rerun's (playbook, ansible_args) into a python shim
    invocation. The shim writes ``playbook`` + ``ansible_args`` to
    ``argv_log`` (one entry per line) and exits with ``exit_code``.

    Why ``side_effect`` instead of ``return_value``: ``_build_command``
    is called with the rerun's *actual* (playbook, ansible_args) and
    must propagate them into the spawned shim's argv. A static
    ``return_value`` would drop them on the floor and leave the shim
    unaware of what rerun composed.
    """

    def _fake(playbook: str, ansible_args: list[str]) -> tuple[str, list[str]]:
        code = (
            "import sys, pathlib; "
            f"pathlib.Path({str(argv_log)!r}).write_text('\\n'.join(sys.argv[1:])); "
            f"sys.exit({exit_code})"
        )
        return sys.executable, ["-c", code, playbook, *ansible_args]

    return _fake


def _record_live_session(
    tmp_path: Path,
    *,
    ansible_args: list[str],
    events: list[dict],
) -> str:
    """Drive ``run_playbook`` against a fake shim and return the session ID."""
    from ansible_aom.runner import run_playbook

    renderer = MagicMock()
    cmd, args = _fake_ansible_command(events, exit_code=0)

    with patch("ansible_aom.runner._build_command", return_value=(cmd, args)):
        # run_preflight tries to talk to ansible-playbook; mock it out
        # so the test doesn't shell out for --list-tasks/--list-hosts.
        with patch(
            "ansible_aom.runner.run_preflight",
            return_value=MagicMock(definitions=[], errors=[]),
        ):
            run_playbook(
                "site.yml",
                ansible_args,
                renderer,
                session_dir=tmp_path,
            )

    sessions = [p for p in tmp_path.iterdir() if p.is_dir()]
    assert len(sessions) == 1, f"expected one session dir, got {sessions}"
    return sessions[0].name


def _read_argv(argv_log: Path) -> list[str]:
    """Read the captured argv lines emitted by the capture-shim.

    When CPython is invoked as ``python -c CODE arg1 arg2``,
    ``sys.argv`` is ``["-c", "arg1", "arg2", ...]`` (the source string
    is consumed and replaced with ``-c``). So ``sys.argv[1:]`` is
    ``["arg1", "arg2", ...]`` — i.e. exactly the rerun's argv tail:
    ``[playbook, *ansible_args]``.
    """
    return argv_log.read_text().splitlines()


# ---------------------------------------------------------------------------
# Building blocks for the multi-host fixture
# ---------------------------------------------------------------------------


def _mixed_outcome_events() -> list[dict]:
    """Events flagging web2/web3 as failed, web1 as changed, web4 as ok."""
    return [
        {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-13T10:00:00Z"},
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-05-13T10:00:00Z",
            "play": {"id": "p1", "name": "Deploy"},
        },
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-05-13T10:00:00Z",
            "task": {"id": "t1", "name": "Install nginx"},
        },
        {
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-05-13T10:00:01Z",
            "task": {"id": "t1", "name": "Install nginx"},
            "hosts": {"web1": {"ok": True, "changed": True}},
        },
        {
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-05-13T10:00:01Z",
            "task": {"id": "t1", "name": "Install nginx"},
            "hosts": {"web4": {"ok": True, "changed": False}},
        },
        {
            "_event": "v2_runner_on_failed",
            "_timestamp": "2026-05-13T10:00:01Z",
            "task": {"id": "t1", "name": "Install nginx"},
            "hosts": {"web2": {"failed": True, "msg": "boom"}},
        },
        {
            "_event": "v2_runner_on_failed",
            "_timestamp": "2026-05-13T10:00:01Z",
            "task": {"id": "t1", "name": "Install nginx"},
            "hosts": {"web3": {"failed": True, "msg": "boom"}},
        },
        {"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-13T10:00:02Z"},
    ]


def _unreachable_events() -> list[dict]:
    """Events flagging web5 as unreachable plus web2/web3 as failed."""
    return [
        {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-13T10:00:00Z"},
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-05-13T10:00:00Z",
            "play": {"id": "p1", "name": "Deploy"},
        },
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-05-13T10:00:00Z",
            "task": {"id": "t1", "name": "Probe"},
        },
        {
            "_event": "v2_runner_on_unreachable",
            "_timestamp": "2026-05-13T10:00:01Z",
            "task": {"id": "t1", "name": "Probe"},
            "hosts": {"web5": {"unreachable": True, "msg": "timeout"}},
        },
        {
            "_event": "v2_runner_on_failed",
            "_timestamp": "2026-05-13T10:00:01Z",
            "task": {"id": "t1", "name": "Probe"},
            "hosts": {"web2": {"failed": True, "msg": "boom"}},
        },
        {"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-13T10:00:02Z"},
    ]


# ---------------------------------------------------------------------------
# Round-trip tests
# ---------------------------------------------------------------------------


class TestRerunRoundtripFailed:
    """Record → rerun --failed → assert spawn argv."""

    def test_failed_limit_contains_only_failed_hosts(self, tmp_path: Path) -> None:
        sessions_dir = tmp_path / "sessions"
        original_args = ["-i", "hosts.ini", "--limit", "web1,web2,web3,web4"]
        session_id = _record_live_session(
            sessions_dir,
            ansible_args=original_args,
            events=_mixed_outcome_events(),
        )

        argv_log = tmp_path / "argv.txt"
        fake_build = _make_capture_build_command(argv_log)

        from ansible_aom.rerun.cli import main as rerun_main

        with patch(
            "ansible_aom.runner._build_command",
            side_effect=fake_build,
        ):
            with patch(
                "ansible_aom.runner.run_preflight",
                return_value=MagicMock(definitions=[], errors=[]),
            ):
                rc = rerun_main(
                    argv=[
                        "--state-dir",
                        str(sessions_dir),
                        session_id,
                        "--failed",
                        "--yes",
                    ],
                )

        assert rc == 0, "rerun should exit cleanly when failed hosts exist"
        spawned = _read_argv(argv_log)
        # First arg is the playbook (passed verbatim through run_playbook).
        assert spawned[0] == "site.yml"

        # The original --limit must be entirely gone.
        # We re-add the new --limit ourselves and assert it once.
        assert spawned.count("--limit") == 1
        limit_idx = spawned.index("--limit")
        limit_value = spawned[limit_idx + 1]
        # Set comparison: order is internal to _build_rerun_command.
        assert set(limit_value.split(",")) == {"web2", "web3"}

        # The original web1/web4 hosts (which weren't failed) must NOT
        # appear in the new --limit, and the inventory flag survives.
        assert "web1" not in limit_value.split(",")
        assert "web4" not in limit_value.split(",")
        assert "-i" in spawned
        assert "hosts.ini" in spawned
        assert spawned[spawned.index("-i") + 1] == "hosts.ini"


class TestRerunRoundtripUnreachable:
    """``--unreachable`` returns failed ∪ unreachable hosts."""

    def test_unreachable_limit_includes_failed_and_unreachable(self, tmp_path: Path) -> None:
        sessions_dir = tmp_path / "sessions"
        original_args = ["-i", "hosts.ini"]
        session_id = _record_live_session(
            sessions_dir,
            ansible_args=original_args,
            events=_unreachable_events(),
        )

        argv_log = tmp_path / "argv.txt"
        fake_build = _make_capture_build_command(argv_log)

        from ansible_aom.rerun.cli import main as rerun_main

        with patch(
            "ansible_aom.runner._build_command",
            side_effect=fake_build,
        ):
            with patch(
                "ansible_aom.runner.run_preflight",
                return_value=MagicMock(definitions=[], errors=[]),
            ):
                rc = rerun_main(
                    argv=[
                        "--state-dir",
                        str(sessions_dir),
                        session_id,
                        "--unreachable",
                        "--yes",
                    ],
                )

        assert rc == 0
        spawned = _read_argv(argv_log)
        assert spawned[0] == "site.yml"
        limit_idx = spawned.index("--limit")
        assert set(spawned[limit_idx + 1].split(",")) == {"web2", "web5"}
        # Inventory still preserved.
        assert "-i" in spawned and "hosts.ini" in spawned


class TestRerunRoundtripChangesOnly:
    """``--changes-only`` requires runner_on_ok events with changed=true."""

    def test_changes_only_limit_is_just_changed_hosts(self, tmp_path: Path) -> None:
        sessions_dir = tmp_path / "sessions"
        original_args = ["-i", "hosts.ini"]
        session_id = _record_live_session(
            sessions_dir,
            ansible_args=original_args,
            events=_mixed_outcome_events(),
        )

        argv_log = tmp_path / "argv.txt"
        fake_build = _make_capture_build_command(argv_log)

        from ansible_aom.rerun.cli import main as rerun_main

        with patch(
            "ansible_aom.runner._build_command",
            side_effect=fake_build,
        ):
            with patch(
                "ansible_aom.runner.run_preflight",
                return_value=MagicMock(definitions=[], errors=[]),
            ):
                rc = rerun_main(
                    argv=[
                        "--state-dir",
                        str(sessions_dir),
                        session_id,
                        "--changes-only",
                        "--yes",
                    ],
                )

        assert rc == 0
        spawned = _read_argv(argv_log)
        limit_idx = spawned.index("--limit")
        # Only web1 had ok+changed=true in the fixture.
        assert set(spawned[limit_idx + 1].split(",")) == {"web1"}


class TestRerunRoundtripRefusal:
    """Old-format session (no ansible_args) → exit 2, no spawn."""

    def test_missing_ansible_args_refuses_without_spawning(self, tmp_path: Path, capsys) -> None:
        sessions_dir = tmp_path / "sessions"
        sid = "01971111-1111-7000-8000-000000000099"
        session_path = sessions_dir / sid
        session_path.mkdir(parents=True)
        # Schema 1.0 meta: no ansible_args field at all.
        meta = {
            "playbook": "site.yml",
            "start_time": "2026-05-13T10:00:00Z",
            "session_id": sid,
            "status": "failed",
            "version": "1.0",
        }
        (session_path / "meta.json").write_text(json.dumps(meta))
        events = [
            {
                "_event": "v2_runner_on_failed",
                "task": {"name": "Install"},
                "hosts": {"web2": {"failed": True, "msg": "boom"}},
            }
        ]
        (session_path / "events.jsonl").write_text("\n".join(json.dumps(e) for e in events) + "\n")
        (session_path / "stderr.log").write_text("")

        argv_log = tmp_path / "argv.txt"
        fake_build = _make_capture_build_command(argv_log)

        from ansible_aom.rerun.cli import main as rerun_main

        with patch(
            "ansible_aom.runner._build_command",
            side_effect=fake_build,
        ):
            with patch(
                "ansible_aom.runner.run_preflight",
                return_value=MagicMock(definitions=[], errors=[]),
            ):
                rc = rerun_main(
                    argv=[
                        "--state-dir",
                        str(sessions_dir),
                        sid,
                        "--failed",
                        "--yes",
                    ],
                )

        assert rc == 2, "missing ansible_args must exit 2"
        # Capture shim never ran.
        assert not argv_log.exists(), "capture shim must NOT spawn on refusal"
        err = capsys.readouterr().err
        assert "ansible_args" in err
        assert sid in err

    def test_null_ansible_args_also_refused(self, tmp_path: Path) -> None:
        """``ansible_args: null`` (hand-edited) is treated the same as missing."""
        sessions_dir = tmp_path / "sessions"
        sid = "01971111-1111-7000-8000-000000000098"
        session_path = sessions_dir / sid
        session_path.mkdir(parents=True)
        meta = {
            "playbook": "site.yml",
            "ansible_args": None,  # explicit null
            "start_time": "2026-05-13T10:00:00Z",
            "session_id": sid,
            "status": "failed",
            "version": "1.1",
        }
        (session_path / "meta.json").write_text(json.dumps(meta))
        (session_path / "events.jsonl").write_text(
            json.dumps(
                {
                    "_event": "v2_runner_on_failed",
                    "task": {"name": "x"},
                    "hosts": {"web2": {"failed": True}},
                }
            )
            + "\n"
        )
        (session_path / "stderr.log").write_text("")

        argv_log = tmp_path / "argv.txt"
        fake_build = _make_capture_build_command(argv_log)

        from ansible_aom.rerun.cli import main as rerun_main

        with patch(
            "ansible_aom.runner._build_command",
            side_effect=fake_build,
        ):
            rc = rerun_main(
                argv=[
                    "--state-dir",
                    str(sessions_dir),
                    sid,
                    "--failed",
                    "--yes",
                ],
            )

        assert rc == 2
        assert not argv_log.exists()
