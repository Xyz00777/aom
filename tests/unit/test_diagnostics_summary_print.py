"""Phase 13: automatic post-run diagnostics summary on AOM_DEBUG=1.

When the user runs ``AOM_DEBUG=1 aom site.yml``, the diagnostics
summary lands on stderr at completion — no extra ``aom inspect``
step required. With ``AOM_DEBUG`` unset, the function is a silent
no-op.
"""

from __future__ import annotations

from io import StringIO

import pytest

from ansible_aom.core import diagnostics


@pytest.fixture(autouse=True)
def _reset() -> None:
    diagnostics._reset_for_testing()
    yield
    diagnostics._reset_for_testing()


def _populate() -> None:
    diag = diagnostics.RunDiagnostics()
    diag.note_event("v2_playbook_on_start")
    diag.note_event("v2_runner_on_ok")
    diag.note_event("v2_runner_on_ok")
    diag.note_event("v2_playbook_on_stats")
    diag.note_preflight_elapsed_ms(120)
    diagnostics.set_last_run_diagnostics(diag)
    diagnostics.set_last_renderer_stats(diagnostics.RendererStats(render_calls=4, log_writes=8))


def test_print_summary_if_debug_silent_without_debug() -> None:
    diagnostics.install_from_env(env={})
    _populate()
    buf = StringIO()
    diagnostics.print_summary_if_debug(file=buf)
    assert buf.getvalue() == ""


def test_print_summary_if_debug_emits_with_debug() -> None:
    diagnostics.install_from_env(env={"AOM_DEBUG": "1"})
    _populate()
    buf = StringIO()
    diagnostics.print_summary_if_debug(file=buf)
    out = buf.getvalue()
    assert "[aom-debug]" in out
    assert "events=4" in out
    assert "v2_runner_on_ok" in out


def test_print_summary_if_debug_handles_no_run_data() -> None:
    """No accumulator published yet — still safe to call."""
    diagnostics.install_from_env(env={"AOM_DEBUG": "1"})
    buf = StringIO()
    diagnostics.print_summary_if_debug(file=buf)
    # Empty or a single "no data" line; never raises.
    assert isinstance(buf.getvalue(), str)


def test_set_debug_enables_summary() -> None:
    """set_debug(True) should have same effect as AOM_DEBUG=1 env var."""
    diagnostics.set_debug(True)
    _populate()
    buf = StringIO()
    diagnostics.print_summary_if_debug(file=buf)
    out = buf.getvalue()
    assert "[aom-debug]" in out
    assert "events=4" in out


def test_set_debug_disables_summary() -> None:
    """set_debug(False) should suppress the summary."""
    diagnostics.set_debug(True)
    diagnostics.set_debug(False)
    _populate()
    buf = StringIO()
    diagnostics.print_summary_if_debug(file=buf)
    assert buf.getvalue() == ""
