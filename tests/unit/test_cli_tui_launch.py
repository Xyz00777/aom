"""Tests for the CLI's run dispatch paths.

Compact mode uses the legacy ``run_playbook(...)`` synchronous path.
The --tui launch path was removed; only the compact path remains.
"""

from __future__ import annotations

from unittest.mock import patch


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
