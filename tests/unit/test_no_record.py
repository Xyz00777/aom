"""Unit tests for F3 --no-record plumbing."""

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


class TestRunPlaybookRecordParameter:
    """run_playbook accepts a record=bool kwarg; default is True."""

    def test_record_false_skips_session_directory(self, tmp_path: Path) -> None:
        from ansible_aom.runner import run_playbook

        renderer = MagicMock()
        cmd, args = _fake_ansible_command(
            [{"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:01Z"}],
            exit_code=0,
        )

        with patch("ansible_aom.runner._build_command", return_value=(cmd, args)):
            exit_code = run_playbook(
                "playbook.yml", [], renderer, session_dir=tmp_path, record=False
            )

        assert exit_code == 0
        # No session directory should have been created.
        assert list(tmp_path.iterdir()) == []

    def test_record_true_default_still_writes(self, tmp_path: Path) -> None:
        from ansible_aom.runner import run_playbook

        renderer = MagicMock()
        cmd, args = _fake_ansible_command(
            [{"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:01Z"}],
            exit_code=0,
        )

        with patch("ansible_aom.runner._build_command", return_value=(cmd, args)):
            run_playbook("playbook.yml", [], renderer, session_dir=tmp_path)

        sessions = list(tmp_path.iterdir())
        assert len(sessions) == 1


class TestNoRecordParserFlag:
    """`--no-record` is a top-level flag that defaults to False."""

    def test_no_record_flag_parses(self) -> None:
        from ansible_aom.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["--no-record", "playbook.yml"])
        assert args.no_record is True

    def test_no_record_default_false(self) -> None:
        from ansible_aom.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["playbook.yml"])
        assert args.no_record is False


class TestNoRecordCompactPlumbing:
    """`aom --no-record playbook.yml` calls run_playbook(..., record=False)."""

    def test_no_record_propagates_to_runner(self) -> None:
        from ansible_aom.cli import main

        with (
            patch("ansible_aom.runner.run_playbook", return_value=0) as mock_run,
            patch("ansible_aom.renderer.factory.create_renderer"),
            patch("sys.argv", ["aom", "--no-record", "playbook.yml"]),
        ):
            assert main() == 0

        # record=False must be in the kwargs.
        _args, kwargs = mock_run.call_args
        assert kwargs.get("record") is False

    def test_default_propagates_record_true(self) -> None:
        from ansible_aom.cli import main

        with (
            patch("ansible_aom.runner.run_playbook", return_value=0) as mock_run,
            patch("ansible_aom.renderer.factory.create_renderer"),
            patch("sys.argv", ["aom", "playbook.yml"]),
        ):
            main()

        _args, kwargs = mock_run.call_args
        # Either explicit True, or absent (default True). Accept both
        # so the source can choose either style.
        assert kwargs.get("record", True) is True


class TestNoRecordTUIPlumbing:
    """--no-record reaches the TUI worker as record=False."""

    def test_aomapp_accepts_record_kwarg(self) -> None:
        from ansible_aom.tui.app import AOMApp

        app = AOMApp(playbook="x.yml", ansible_args=[], record=False)
        assert app.record is False

    def test_aomapp_default_record_true(self) -> None:
        from ansible_aom.tui.app import AOMApp

        app = AOMApp(playbook="x.yml", ansible_args=[])
        assert app.record is True

    def test_tui_main_propagates_no_record_to_app(self) -> None:
        """``--no-record --tui`` builds a LiveDriver with recording off."""
        from ansible_aom.cli import main

        captured: dict[str, object] = {}

        class FakeApp:
            def __init__(self, **kwargs: object) -> None:
                captured.update(kwargs)
                self.exit_code = 0

            def run(self) -> None:
                return None

        with (
            patch("ansible_aom.tui.app.AOMApp", FakeApp),
            patch("sys.argv", ["aom", "--tui", "--no-record", "playbook.yml"]),
        ):
            assert main() == 0

        driver = captured.get("driver")
        assert driver is not None, f"AOMApp was not built with a driver; got {captured!r}"
        # LiveDriver stores the record flag privately; assert it flowed
        # through from --no-record at the CLI all the way to the driver.
        assert getattr(driver, "_record") is False
