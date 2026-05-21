"""Verify every CLI entry point installs the diagnostics layer.

Phase 2 of docs/superpowers/specs/2026-05-21-diagnostics-layer-design.md.
The contract: regardless of which subcommand the user invokes, ``aom``
must call :func:`diagnostics.install_from_env` before doing any other
work, so ``faulthandler`` is armed before the first risky operation.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ansible_aom.core import diagnostics


@pytest.fixture(autouse=True)
def _reset() -> None:
    diagnostics._reset_for_testing()
    yield
    diagnostics._reset_for_testing()


def _assert_installed() -> None:
    assert diagnostics._installed is True


def test_cli_main_installs_diagnostics(monkeypatch: pytest.MonkeyPatch) -> None:
    """``aom`` with no args prints help and exits cleanly."""
    import sys

    from ansible_aom import cli

    monkeypatch.setattr(sys, "argv", ["aom"])
    assert diagnostics._installed is False
    cli.main()
    _assert_installed()


def test_inspect_main_installs_diagnostics(tmp_path: Path) -> None:
    """``aom inspect --text`` with empty state-dir prints "no sessions"."""
    from ansible_aom.inspect.cli import main as inspect_main

    assert diagnostics._installed is False
    inspect_main(["--text", "--state-dir", str(tmp_path)])
    _assert_installed()


def test_rerun_main_installs_diagnostics() -> None:
    """``aom rerun --help`` exits via argparse before any rerun logic runs."""
    from ansible_aom.rerun.cli import main as rerun_main

    assert diagnostics._installed is False
    with pytest.raises(SystemExit):
        rerun_main(["--help"])
    _assert_installed()


def test_replay_main_installs_diagnostics() -> None:
    """``aom replay --help`` exits via argparse before any replay runs."""
    from ansible_aom.drivers.replay import cli_main as replay_main

    assert diagnostics._installed is False
    with pytest.raises(SystemExit):
        replay_main(["--help"])
    _assert_installed()


def test_runner_trace_pexpect_consults_diagnostics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The runner's per-loop trace check delegates to diagnostics.

    Phase 2 routes the legacy ``AOM_TRACE`` and the new ``AOM_TRACE_PEXPECT``
    through one helper, so the alias works without runner re-reading env.
    """
    from ansible_aom.ansible import runner

    diagnostics.install_from_env(env={"AOM_TRACE_PEXPECT": "1"})
    assert runner._trace_enabled() is True

    diagnostics._reset_for_testing()
    diagnostics.install_from_env(env={"AOM_TRACE": "1"})
    assert runner._trace_enabled() is True

    diagnostics._reset_for_testing()
    diagnostics.install_from_env(env={})
    assert runner._trace_enabled() is False
