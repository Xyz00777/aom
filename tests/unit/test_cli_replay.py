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


import json
from pathlib import Path


def _make_session(base: Path, session_id: str, events: list[dict]) -> Path:
    p = base / session_id
    p.mkdir(parents=True)
    with open(p / "events.jsonl", "w") as f:
        for e in events:
            f.write(json.dumps(e) + "\n")
    with open(p / "meta.json", "w") as f:
        json.dump({"playbook": "x.yml", "status": "completed"}, f)
    (p / "stderr.log").touch()
    return p


class TestReplayCLIMain:
    """`replay.cli_main` parses argv, builds a renderer, calls replay_session."""

    def test_cli_main_default_uses_compact_renderer(self, tmp_path: Path) -> None:
        from ansible_aom.replay import cli_main

        _make_session(
            tmp_path,
            "abc",
            [{"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:00Z"}],
        )

        captured: dict[str, object] = {}

        def fake_replay(**kwargs: object) -> int:
            captured.update(kwargs)
            return 0

        with (
            patch("ansible_aom.replay.replay_session", side_effect=fake_replay),
            patch("ansible_aom.replay.create_renderer") as mock_factory,
        ):
            mock_factory.return_value = object()
            exit_code = cli_main(["abc", "--state-dir", str(tmp_path)])

        assert exit_code == 0
        # Default = compact renderer (tui_mode=False).
        kw = mock_factory.call_args.kwargs
        assert kw.get("tui_mode") is False

    def test_cli_main_tui_flag_selects_tui_renderer(self, tmp_path: Path) -> None:
        from ansible_aom.replay import cli_main

        _make_session(
            tmp_path,
            "abc",
            [{"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:00Z"}],
        )

        with (
            patch("ansible_aom.replay.replay_session", return_value=0),
            patch("ansible_aom.replay.create_renderer") as mock_factory,
        ):
            mock_factory.return_value = object()
            cli_main(["abc", "--state-dir", str(tmp_path), "--tui"])

        assert mock_factory.call_args.kwargs.get("tui_mode") is True

    def test_cli_main_speed_forwarded(self, tmp_path: Path) -> None:
        from ansible_aom.replay import cli_main

        _make_session(
            tmp_path,
            "abc",
            [{"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:00Z"}],
        )

        captured: dict[str, object] = {}

        def fake_replay(**kwargs: object) -> int:
            captured.update(kwargs)
            return 0

        with (
            patch("ansible_aom.replay.replay_session", side_effect=fake_replay),
            patch("ansible_aom.replay.create_renderer", return_value=object()),
        ):
            cli_main(["abc", "--state-dir", str(tmp_path), "--speed", "10"])

        assert captured.get("speed") == 10.0

    def test_cli_main_speed_zero_allowed(self, tmp_path: Path) -> None:
        """`--speed 0` is the documented "fast as possible" sentinel."""
        from ansible_aom.replay import cli_main

        _make_session(
            tmp_path,
            "abc",
            [{"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:00Z"}],
        )

        captured: dict[str, object] = {}

        def fake_replay(**kwargs: object) -> int:
            captured.update(kwargs)
            return 0

        with (
            patch("ansible_aom.replay.replay_session", side_effect=fake_replay),
            patch("ansible_aom.replay.create_renderer", return_value=object()),
        ):
            cli_main(["abc", "--state-dir", str(tmp_path), "--speed", "0"])

        assert captured.get("speed") == 0.0

    def test_cli_main_returns_1_when_session_missing(self, tmp_path: Path) -> None:
        from ansible_aom.replay import cli_main

        # No session created — replay_session returns 1 (real behaviour).
        with patch("ansible_aom.replay.create_renderer", return_value=object()):
            exit_code = cli_main(["nope", "--state-dir", str(tmp_path)])

        assert exit_code == 1

    def test_compact_and_tui_are_mutually_exclusive(self, tmp_path: Path) -> None:
        """Passing both --compact and --tui exits with usage error (argparse SystemExit)."""
        import pytest

        from ansible_aom.replay import cli_main

        with (
            patch("ansible_aom.replay.replay_session", return_value=0),
            patch("ansible_aom.replay.create_renderer", return_value=object()),
            pytest.raises(SystemExit),
        ):
            cli_main(["abc", "--state-dir", str(tmp_path), "--compact", "--tui"])
