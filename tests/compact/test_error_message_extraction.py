"""Tests for error message extraction from multiple result fields.

When a task fails with ``v2_runner_on_failed``, the error message may live
in ``msg``, ``module_stderr``, ``stderr``, ``module_stdout``, or ``stdout``
depending on the module.  The compact renderer should try these fields in
priority order and only show ``=>`` when there is actual content.

See SPECIFICATION.md §4.1 for the compact log format.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from ansible_aom.compact.renderer import CompactRenderer


def _renderer() -> CompactRenderer:
    r = CompactRenderer(is_tty=False)
    r.start("test.yml", [])
    r._display = MagicMock()
    return r


def _logged(r: CompactRenderer) -> list[str]:
    return [c.args[0] for c in r._display.print_log.call_args_list]


# =============================================================================
# v2_runner_on_failed — message field extraction
# =============================================================================


def test_failed_msg_field_shown():
    """Primary ``msg`` field is displayed when present."""
    r = _renderer()
    r._emit_event_log(
        {
            "_event": "v2_runner_on_failed",
            "hosts": {"web1": {"msg": "Permission denied", "failed": True}},
        }
    )
    lines = _logged(r)
    assert any("FAILED! => Permission denied" in line for line in lines)


def test_failed_module_stderr_fallback():
    """Fall back to ``module_stderr`` when ``msg`` is empty."""
    r = _renderer()
    r._emit_event_log(
        {
            "_event": "v2_runner_on_failed",
            "hosts": {
                "web1": {"msg": "", "module_stderr": "credential store error", "failed": True}
            },
        }
    )
    lines = _logged(r)
    assert any("FAILED! => credential store error" in line for line in lines)


def test_failed_stderr_fallback():
    """Fall back to ``stderr`` when ``msg`` and ``module_stderr`` are empty."""
    r = _renderer()
    r._emit_event_log(
        {
            "_event": "v2_runner_on_failed",
            "hosts": {
                "web1": {"msg": "", "module_stderr": "", "stderr": "command failed", "failed": True}
            },
        }
    )
    lines = _logged(r)
    assert any("FAILED! => command failed" in line for line in lines)


def test_failed_module_stdout_fallback():
    """Fall back to ``module_stdout`` when ``msg``/``stderr``/``module_stderr`` are empty."""
    r = _renderer()
    r._emit_event_log(
        {
            "_event": "v2_runner_on_failed",
            "hosts": {
                "web1": {
                    "msg": "",
                    "module_stderr": "",
                    "stderr": "",
                    "module_stdout": "stdout output",
                    "failed": True,
                }
            },
        }
    )
    lines = _logged(r)
    assert any("FAILED! => stdout output" in line for line in lines)


def test_failed_stdout_fallback():
    """Fall back to ``stdout`` when all higher-priority fields are empty."""
    r = _renderer()
    r._emit_event_log(
        {
            "_event": "v2_runner_on_failed",
            "hosts": {
                "web1": {
                    "msg": "",
                    "module_stderr": "",
                    "stderr": "",
                    "module_stdout": "",
                    "stdout": "raw stdout",
                    "failed": True,
                }
            },
        }
    )
    lines = _logged(r)
    assert any("FAILED! => raw stdout" in line for line in lines)


def test_failed_msg_takes_precedence_over_module_stderr():
    """When both ``msg`` and ``module_stderr`` are present, ``msg`` wins."""
    r = _renderer()
    r._emit_event_log(
        {
            "_event": "v2_runner_on_failed",
            "hosts": {
                "web1": {
                    "msg": "primary error",
                    "module_stderr": "secondary stderr",
                    "failed": True,
                }
            },
        }
    )
    lines = _logged(r)
    fatal_lines = [l for l in lines if "FAILED!" in l]
    assert all("FAILED! => primary error" in l for l in fatal_lines)
    assert all("secondary stderr" not in l for l in fatal_lines)


def test_failed_no_msg_key():
    """Missing ``msg`` key entirely — falls back to ``module_stderr``."""
    r = _renderer()
    r._emit_event_log(
        {
            "_event": "v2_runner_on_failed",
            "hosts": {"web1": {"module_stderr": "module error", "failed": True}},
        }
    )
    lines = _logged(r)
    assert any("FAILED! => module error" in line for line in lines)


def test_failed_all_error_fields_empty():
    """All error fields empty — ``FAILED!`` without ``=>`` tail."""
    r = _renderer()
    r._emit_event_log(
        {
            "_event": "v2_runner_on_failed",
            "hosts": {"web1": {"msg": "", "failed": True}},
        }
    )
    lines = _logged(r)
    fatal_lines = [l for l in lines if "FAILED!" in l]
    assert fatal_lines, "expected at least one FAILED! line"
    for line in fatal_lines:
        assert " => " not in line, f"unexpected '=>' in empty-msg line: {line!r}"


def test_failed_module_stderr_truncated():
    """Long ``module_stderr`` is subject to ``_MSG_DISPLAY_CAP`` truncation."""
    from ansible_aom.compact.renderer import _MSG_DISPLAY_CAP

    r = _renderer()
    huge = "x" * (_MSG_DISPLAY_CAP * 2)
    r._emit_event_log(
        {
            "_event": "v2_runner_on_failed",
            "hosts": {"web1": {"msg": "", "module_stderr": huge, "failed": True}},
        }
    )
    out = _logged(r)
    fatal = [l for l in out if "FAILED!" in l]
    assert any("…(truncated" in l for l in fatal)
    assert not any(huge in l for l in fatal)


# =============================================================================
# v2_runner_on_unreachable — message field extraction
# =============================================================================


def test_unreachable_msg_field_shown():
    """Primary ``msg`` field shown for unreachable."""
    r = _renderer()
    r._emit_event_log(
        {
            "_event": "v2_runner_on_unreachable",
            "hosts": {"web1": {"msg": "host unreachable"}},
        }
    )
    lines = _logged(r)
    assert any("UNREACHABLE! => host unreachable" in line for line in lines)


def test_unreachable_module_stderr_fallback():
    """Fall back to ``module_stderr`` for unreachable when ``msg`` empty."""
    r = _renderer()
    r._emit_event_log(
        {
            "_event": "v2_runner_on_unreachable",
            "hosts": {"web1": {"msg": "", "module_stderr": "connection refused"}},
        }
    )
    lines = _logged(r)
    assert any("UNREACHABLE! => connection refused" in line for line in lines)


def test_unreachable_all_error_fields_empty():
    """All error fields empty — ``UNREACHABLE!`` without ``=>``."""
    r = _renderer()
    r._emit_event_log(
        {
            "_event": "v2_runner_on_unreachable",
            "hosts": {"web1": {"msg": ""}},
        }
    )
    lines = _logged(r)
    unreachable_lines = [l for l in lines if "UNREACHABLE!" in l]
    assert unreachable_lines, "expected at least one UNREACHABLE! line"
    for line in unreachable_lines:
        assert " => " not in line, f"unexpected '=>' in empty-msg line: {line!r}"


# =============================================================================
# no_log / censored field handling
# =============================================================================


def test_failed_no_log_shows_censored_marker():
    """``_ansible_no_log`` with no other error fields shows ``(no_log)``."""
    r = _renderer()
    r._emit_event_log(
        {
            "_event": "v2_runner_on_failed",
            "hosts": {
                "web1": {
                    "_ansible_no_log": True,
                    "censored": "the output has been hidden due to no_log",
                    "failed": True,
                }
            },
        }
    )
    lines = _logged(r)
    assert any("FAILED! => (no_log)" in line for line in lines)


def test_failed_no_log_msg_still_wins():
    """``_ansible_no_log`` with a ``msg`` field — ``msg`` still takes priority."""
    r = _renderer()
    r._emit_event_log(
        {
            "_event": "v2_runner_on_failed",
            "hosts": {
                "web1": {
                    "_ansible_no_log": True,
                    "msg": "real error message",
                    "censored": "the output has been hidden due to no_log",
                    "failed": True,
                }
            },
        }
    )
    lines = _logged(r)
    assert any("FAILED! => real error message" in line for line in lines)


def test_failed_censored_fallback_when_no_other_fields():
    """``censored`` field used when no standard error fields have content."""
    r = _renderer()
    r._emit_event_log(
        {
            "_event": "v2_runner_on_failed",
            "hosts": {
                "web1": {
                    "_ansible_no_log": False,
                    "msg": "",
                    "module_stderr": "",
                    "stderr": "",
                    "module_stdout": "",
                    "stdout": "",
                    "censored": "the output has been hidden",
                    "failed": True,
                }
            },
        }
    )
    lines = _logged(r)
    assert any("FAILED! => the output has been hidden" in line for line in lines)


def test_unreachable_no_log_shows_censored_marker():
    """``_ansible_no_log`` on unreachable shows ``(no_log)``."""
    r = _renderer()
    r._emit_event_log(
        {
            "_event": "v2_runner_on_unreachable",
            "hosts": {
                "web1": {
                    "_ansible_no_log": True,
                    "censored": "the output has been hidden due to no_log",
                }
            },
        }
    )
    lines = _logged(r)
    assert any("UNREACHABLE! => (no_log)" in line for line in lines)


def test_failed_loop_item_no_log_shows_censored_marker():
    """Loop item with ``_ansible_no_log`` shows ``(no_log)`` after item label."""
    r = _renderer()
    r._emit_event_log(
        {
            "_event": "v2_runner_on_failed",
            "hosts": {
                "web1": {
                    "results": [
                        {
                            "_ansible_no_log": True,
                            "censored": "the output has been hidden due to no_log",
                            "failed": True,
                            "_ansible_item_label": "item_1",
                        }
                    ],
                    "failed": True,
                }
            },
        }
    )
    lines = _logged(r)
    assert any("failed: [web1] => (item=item_1) => (no_log)" in line for line in lines)
