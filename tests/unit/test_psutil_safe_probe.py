"""Tests for the psutil-safe probe in the runner.

Background: ``_sample_subprocess_active`` imports ``psutil`` to read
per-process CPU. On some installs (e.g. uv-installed Python loading a
Nix-built ``_psutil_linux.abi3.so``) the C extension SIGSEGVs during
its module init — which a ``try: import psutil`` cannot catch because
the crash is at the dlopen/PyInit level. To survive this, the runner
probes psutil in a subprocess once; if the probe crashes or exits
non-zero, psutil is marked disabled for the rest of the process and
``_sample_subprocess_active`` returns False without ever importing it.
"""

from __future__ import annotations

import sys
import types
from unittest.mock import patch

import pytest

from ansible_aom.ansible import runner
from ansible_aom.core import diagnostics


@pytest.fixture(autouse=True)
def _reset() -> None:
    diagnostics._reset_for_testing()
    runner._reset_psutil_probe_for_testing()
    yield
    diagnostics._reset_for_testing()
    runner._reset_psutil_probe_for_testing()


def test_probe_failure_returns_false_without_importing_psutil() -> None:
    """If the subprocess probe exits non-zero (e.g. SIGSEGV at import),
    ``_sample_subprocess_active`` returns False without attempting an
    in-process import of psutil."""
    with patch.object(runner, "_probe_psutil", return_value=(None, "exit=-11 (SIGSEGV)")):
        active = runner._sample_subprocess_active(123456)
    assert active is False
    assert runner._psutil_disabled_reason() == "exit=-11 (SIGSEGV)"


def test_probe_failure_disables_psutil_in_diagnostics() -> None:
    """The disable reason is surfaced via the diagnostics module so it
    lands in diagnostics.json and the post-run summary."""
    with patch.object(runner, "_probe_psutil", return_value=(None, "exit=-11 (SIGSEGV)")):
        runner._sample_subprocess_active(123456)
    assert diagnostics.psutil_disabled_reason() == "exit=-11 (SIGSEGV)"


def test_probe_runs_once_per_process() -> None:
    """The probe is expensive (subprocess spawn). It must be cached so
    repeated heartbeat ticks don't re-probe."""
    with patch.object(runner, "_probe_psutil", return_value=(None, "exit=-11")) as mock_probe:
        for _ in range(5):
            runner._sample_subprocess_active(123456)
    assert mock_probe.call_count == 1


def test_probe_success_path_uses_returned_module() -> None:
    """A successful probe yields a usable psutil module; subsequent
    sample calls go through it normally."""
    fake = types.ModuleType("psutil")

    class _FakeError(Exception):
        pass

    class _FakeProc:
        def __init__(self, pid: int) -> None:
            self.pid = pid

        def is_running(self) -> bool:
            return True

        def cpu_percent(self, interval: float | None = None) -> float:
            return 5.0

        def children(self, recursive: bool = False) -> list[object]:
            return []

    fake.Process = _FakeProc  # type: ignore[attr-defined]
    fake.Error = _FakeError  # type: ignore[attr-defined]

    with patch.object(runner, "_probe_psutil", return_value=(fake, None)):
        # First call seeds, second call yields the delta.
        runner._sample_subprocess_active(99999)
        active = runner._sample_subprocess_active(99999)
    assert active is True
    assert runner._psutil_disabled_reason() is None


def test_real_probe_in_current_process_does_not_crash() -> None:
    """Sanity: the real subprocess probe runs to completion in the test
    environment. (If psutil happens to be broken in the test env, the
    probe returns a reason — both outcomes are valid; we only assert
    the call returns and the result is a 2-tuple.)"""
    mod, reason = runner._probe_psutil()
    assert (mod is not None and reason is None) or (mod is None and reason is not None)


def test_sample_short_circuits_when_subprocess_check_unavailable() -> None:
    """If subprocess itself blows up (highly unlikely but defensive), the
    helper still returns False instead of propagating."""
    with patch("subprocess.run", side_effect=OSError("no exec for you")):
        # Reset since the autouse fixture already cleared the cache.
        active = runner._sample_subprocess_active(123456)
    assert active is False
    reason = runner._psutil_disabled_reason()
    assert reason is not None
    assert "OSError" in reason or "no exec" in reason
