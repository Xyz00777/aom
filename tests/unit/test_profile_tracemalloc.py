"""Phase 7: AOM_PROFILE and AOM_TRACEMALLOC wiring.

Spec: docs/superpowers/specs/2026-05-21-diagnostics-layer-design.md §6.

These two env vars opt into cProfile / tracemalloc instrumentation
respectively. Tests stay focused on the plumbing — actual profiler
output content is left to the stdlib.
"""

from __future__ import annotations

import cProfile
import tracemalloc
from pathlib import Path

import pytest

from ansible_aom.core import diagnostics


@pytest.fixture(autouse=True)
def _reset() -> None:
    diagnostics._reset_for_testing()
    if tracemalloc.is_tracing():
        tracemalloc.stop()
    yield
    if tracemalloc.is_tracing():
        tracemalloc.stop()
    diagnostics._reset_for_testing()


def test_is_profile_default_false() -> None:
    diagnostics.install_from_env(env={})
    assert diagnostics.is_profile() is False
    assert diagnostics.get_profiler() is None


def test_aom_profile_creates_profiler_instance() -> None:
    diagnostics.install_from_env(env={"AOM_PROFILE": "1"})
    assert diagnostics.is_profile() is True
    profiler = diagnostics.get_profiler()
    assert profiler is not None
    assert isinstance(profiler, cProfile.Profile)


def test_is_tracemalloc_default_false() -> None:
    diagnostics.install_from_env(env={})
    assert diagnostics.is_tracemalloc() is False
    assert tracemalloc.is_tracing() is False


def test_aom_tracemalloc_starts_tracing() -> None:
    diagnostics.install_from_env(env={"AOM_TRACEMALLOC": "1"})
    assert diagnostics.is_tracemalloc() is True
    assert tracemalloc.is_tracing() is True


def test_record_tracemalloc_peak_reads_current_peak() -> None:
    diagnostics.install_from_env(env={"AOM_TRACEMALLOC": "1"})
    # Allocate something so the peak is non-zero.
    _ = [bytearray(1024) for _ in range(100)]

    diagnostics.record_tracemalloc_peak()
    peak = diagnostics.get_tracemalloc_peak_kb()
    assert peak is not None
    assert peak > 0


def test_record_tracemalloc_peak_noop_when_off() -> None:
    diagnostics.install_from_env(env={})
    diagnostics.record_tracemalloc_peak()
    assert diagnostics.get_tracemalloc_peak_kb() is None


def test_dump_profile_writes_pstats(tmp_path: Path) -> None:
    diagnostics.install_from_env(env={"AOM_PROFILE": "1"})
    profiler = diagnostics.get_profiler()
    assert profiler is not None
    profiler.enable()

    def _work() -> int:
        return sum(range(1000))

    _work()
    profiler.disable()

    target = tmp_path / "x.pstats"
    diagnostics.dump_profile(target)
    assert target.exists()
    assert target.stat().st_size > 0


def test_dump_profile_noop_when_off(tmp_path: Path) -> None:
    diagnostics.install_from_env(env={})
    target = tmp_path / "x.pstats"
    diagnostics.dump_profile(target)
    assert not target.exists()


def test_reset_stops_tracemalloc() -> None:
    diagnostics.install_from_env(env={"AOM_TRACEMALLOC": "1"})
    assert tracemalloc.is_tracing() is True
    diagnostics._reset_for_testing()
    assert tracemalloc.is_tracing() is False
