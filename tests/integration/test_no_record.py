"""Integration test for F3 --no-record at the runner level.

The unit tests cover argparse and CLI plumbing. This test goes one
level lower and calls ``run_playbook(..., record=False)`` directly
against a fake ansible executable to confirm no directory is written
even when ``session_dir`` is provided.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch


def _fake_ansible_command(events: list[dict], exit_code: int = 0) -> tuple[str, list[str]]:
    payload = json.dumps(events)
    code = (
        "import json, sys; "
        f"events = json.loads({payload!r}); "
        "[sys.stdout.write(json.dumps(e) + '\\n') for e in events]; "
        "sys.stdout.flush(); "
        f"sys.exit({exit_code})"
    )
    return sys.executable, ["-c", code]


class TestNoRecordIntegration:
    def test_record_false_writes_no_session_dir(self, tmp_path: Path) -> None:
        from ansible_aom.runner import run_playbook

        renderer = MagicMock()
        cmd, args = _fake_ansible_command(
            [
                {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-08T10:00:00Z"},
                {"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:01Z"},
            ],
            exit_code=0,
        )

        with patch("ansible_aom.runner._build_command", return_value=(cmd, args)):
            exit_code = run_playbook(
                "playbook.yml", [], renderer, session_dir=tmp_path, record=False
            )

        assert exit_code == 0
        assert list(tmp_path.iterdir()) == []
        renderer.handle_completion.assert_called_once_with(0, "completed")

    def test_record_false_does_not_touch_default_state_dir(self, tmp_path: Path) -> None:
        """Even if session_dir is None, record=False must not create the default."""
        from ansible_aom.runner import run_playbook

        renderer = MagicMock()
        cmd, args = _fake_ansible_command(
            [{"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:01Z"}],
            exit_code=0,
        )

        with (
            patch("ansible_aom.runner._build_command", return_value=(cmd, args)),
            patch("ansible_aom.runner.Path.home", return_value=tmp_path),
        ):
            run_playbook("playbook.yml", [], renderer, record=False)

        default_dir = tmp_path / ".local" / "state" / "aom" / "sessions"
        # The default dir must not have been created — record=False
        # bypasses the sink entirely, including the directory creation.
        assert not default_dir.exists()
