"""Tests for the CLI's --tui launch path (roadmap #9 wiring).

For ``--tui`` mode, cli.main constructs an AOMApp(playbook, ansible_args)
and calls ``app.run()`` so Textual owns the event loop. The runner
fires inside an AOMApp worker; cli.main never calls run_playbook
directly in TUI mode.

Compact mode still uses the legacy ``run_playbook(...)`` synchronous
path — we don't want to regress that.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestTuiLaunchPath:
    """--tui uses app.run() and skips the legacy run_playbook call."""

    def test_tui_mode_calls_app_run_not_run_playbook_directly(self) -> None:
        from ansible_aom.cli import main

        fake_app = MagicMock()
        fake_app.run.return_value = None
        fake_app.exit_code = 0

        with (
            patch("ansible_aom.tui.app.AOMApp", return_value=fake_app) as ctor,
            patch("ansible_aom.ansible.runner.run_playbook") as legacy_runner,
            patch("sys.argv", ["aom", "--tui", "site.yml"]),
        ):
            exit_code = main()

        fake_app.run.assert_called_once()
        legacy_runner.assert_not_called()
        # AOMApp must be constructed with the playbook + forwarded args.
        construction = ctor.call_args
        # playbook is the positional or kwarg "playbook"
        playbook_arg = construction.kwargs.get("playbook") or (
            construction.args[0] if construction.args else None
        )
        assert playbook_arg == "site.yml"
        assert exit_code == 0

    def test_tui_mode_propagates_app_exit_code(self) -> None:
        """app.exit_code → main()'s return value."""
        from ansible_aom.cli import main

        fake_app = MagicMock()
        fake_app.run.return_value = None
        fake_app.exit_code = 2

        with (
            patch("ansible_aom.tui.app.AOMApp", return_value=fake_app),
            patch("sys.argv", ["aom", "--tui", "site.yml"]),
        ):
            assert main() == 2

    def test_tui_mode_returns_1_when_exit_code_missing(self) -> None:
        """A quit-before-completion run has exit_code=None; cli surfaces 1."""
        from ansible_aom.cli import main

        fake_app = MagicMock()
        fake_app.run.return_value = None
        fake_app.exit_code = None

        with (
            patch("ansible_aom.tui.app.AOMApp", return_value=fake_app),
            patch("sys.argv", ["aom", "--tui", "site.yml"]),
        ):
            assert main() == 1


class TestCompactModePathUnchanged:
    """The compact path must keep calling run_playbook directly."""

    def test_compact_mode_still_calls_run_playbook(self) -> None:
        from ansible_aom.cli import main

        with (
            patch("ansible_aom.ansible.runner.run_playbook", return_value=0) as legacy_runner,
            patch("ansible_aom.renderer.factory.create_renderer") as renderer_factory,
            patch("sys.argv", ["aom", "site.yml"]),
        ):
            main()

        legacy_runner.assert_called_once()
        renderer_factory.assert_called_once()
