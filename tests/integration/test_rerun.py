"""End-to-end integration test for `aom rerun`.

Wires the real ``run_playbook`` against a fake ansible-playbook shim
that records its argv and exits cleanly. Verifies the full pipeline:
``aom rerun`` -> load session -> compose hosts -> build command ->
spawn -> exit code.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch


def test_aom_rerun_failed_spawns_with_correct_limit(tmp_path: Path) -> None:
    """`aom rerun --failed --yes` spawns ansible-playbook with --limit web2,web3."""
    sessions_dir = tmp_path / "sessions"
    session_id = "01971111-1111-7000-8000-000000000001"
    session_path = sessions_dir / session_id
    session_path.mkdir(parents=True)

    meta = {
        "playbook": "site.yml",
        "ansible_args": ["-i", "inv.ini"],
        "start_time": "2026-05-12T10:00:00Z",
        "session_id": session_id,
        "status": "failed",
        "version": "1.1",
    }
    (session_path / "meta.json").write_text(json.dumps(meta))
    events = [
        {
            "_event": "v2_runner_on_failed",
            "task": {"name": "Install nginx"},
            "hosts": {"web2": {"failed": True, "msg": "boom"}},
        },
        {
            "_event": "v2_runner_on_failed",
            "task": {"name": "Install nginx"},
            "hosts": {"web3": {"failed": True, "msg": "boom"}},
        },
    ]
    (session_path / "events.jsonl").write_text("\n".join(json.dumps(e) for e in events) + "\n")
    (session_path / "stderr.log").write_text("")

    # Fake ansible-playbook: a Python one-liner that records its argv to
    # a file and exits 0. This mirrors the trick used by
    # tests/integration/test_runner_session_recording.py.
    argv_log = tmp_path / "argv.txt"
    code = (
        "import sys, pathlib; "
        f"pathlib.Path({str(argv_log)!r}).write_text('\\n'.join(sys.argv[1:])); "
        "sys.exit(0)"
    )
    fake_cmd = sys.executable
    fake_args_prefix = ["-c", code]

    # Patch the runner's command builder so it spawns our shim. We have
    # to swap in (cmd, args) where args includes the playbook + the
    # rerun's ansible_args, because run_playbook will pass those
    # through unchanged.
    def fake_build_command(playbook: str, ansible_args: list[str]) -> tuple[str, list[str]]:
        return fake_cmd, [*fake_args_prefix, playbook, *ansible_args]

    from ansible_aom.rerun.cli import main as rerun_main

    with patch("ansible_aom.ansible.runner._build_command", side_effect=fake_build_command):
        rc = rerun_main(
            argv=[
                "--state-dir",
                str(sessions_dir),
                session_id,
                "--failed",
                "--yes",
            ],
        )
    assert rc == 0

    spawned_argv = argv_log.read_text().splitlines()
    # First arg is the playbook path.
    assert spawned_argv[0] == "site.yml"
    # Original args preserved.
    assert "-i" in spawned_argv
    assert "inv.ini" in spawned_argv
    # --limit appended with sorted hosts.
    assert "--limit" in spawned_argv
    limit_idx = spawned_argv.index("--limit")
    assert spawned_argv[limit_idx + 1] == "web2,web3"


def test_aom_rerun_no_failures_exits_1_without_spawning(tmp_path: Path) -> None:
    """When the session has no failures, `--failed` exits 1 and never spawns."""
    sessions_dir = tmp_path / "sessions"
    session_id = "01971111-1111-7000-8000-000000000001"
    session_path = sessions_dir / session_id
    session_path.mkdir(parents=True)

    meta = {
        "playbook": "site.yml",
        "ansible_args": [],
        "start_time": "2026-05-12T10:00:00Z",
        "session_id": session_id,
        "status": "completed",
        "version": "1.1",
    }
    (session_path / "meta.json").write_text(json.dumps(meta))
    (session_path / "events.jsonl").write_text("")
    (session_path / "stderr.log").write_text("")

    spawned: list = []

    def fake_build_command(playbook: str, ansible_args: list[str]) -> tuple[str, list[str]]:
        spawned.append((playbook, ansible_args))
        return "/bin/false", []

    from ansible_aom.rerun.cli import main as rerun_main

    with patch("ansible_aom.ansible.runner._build_command", side_effect=fake_build_command):
        rc = rerun_main(
            argv=[
                "--state-dir",
                str(sessions_dir),
                session_id,
                "--failed",
                "--yes",
            ],
        )
    assert rc == 1
    assert spawned == []
