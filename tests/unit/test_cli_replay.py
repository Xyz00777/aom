"""CLI tests for the F2 `aom replay` subcommand dispatch.

Mirrors the inspect-dispatcher tests in test_cli.py: top-level
``aom replay ...`` strips the ``replay`` token and forwards the rest
to ``ansible_aom.replay`` (or a thin CLI wrapper there).
"""

from __future__ import annotations

from unittest.mock import patch


class TestReplayDispatch:
    def test_replay_dispatches_to_replay_main(self) -> None:
        """`aom replay <id>` invokes the replay CLI entry with ['<id>']."""
        from ansible_aom.cli import main

        with (
            patch("ansible_aom.replay.cli_main", return_value=0) as mock_main,
            patch("sys.argv", ["aom", "replay", "abc123"]),
        ):
            assert main() == 0
            mock_main.assert_called_once_with(["abc123"])

    def test_replay_forwards_speed_flag(self) -> None:
        from ansible_aom.cli import main

        with (
            patch("ansible_aom.replay.cli_main", return_value=0) as mock_main,
            patch("sys.argv", ["aom", "replay", "abc123", "--speed", "5"]),
        ):
            main()
            mock_main.assert_called_once_with(["abc123", "--speed", "5"])

    def test_replay_forwards_renderer_flags(self) -> None:
        from ansible_aom.cli import main

        with (
            patch("ansible_aom.replay.cli_main", return_value=0) as mock_main,
            patch("sys.argv", ["aom", "replay", "abc123", "--tui"]),
        ):
            main()
            mock_main.assert_called_once_with(["abc123", "--tui"])

    def test_replay_propagates_exit_code(self) -> None:
        from ansible_aom.cli import main

        with (
            patch("ansible_aom.replay.cli_main", return_value=2),
            patch("sys.argv", ["aom", "replay", "missing"]),
        ):
            assert main() == 2
