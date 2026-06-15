"""Tests for the remaining-time (ETA) segment in ``format_status_bar``.

When ``remaining_seconds`` is passed, the status bar appends a dimmed
``~<dur> left`` annotation flush against the elapsed segment (a space, no
separator pipe) — an annotation on elapsed, not a peer counter. ``None``
leaves the bar exactly as it is today. See the spec at
``docs/superpowers/specs/2026-06-16-run-duration-estimate-design.md``.
"""

from __future__ import annotations

from ansible_aom.compact.renderer import _DIM, _RESET, format_status_bar


def test_no_segment_when_remaining_is_none():
    line = format_status_bar("site.yml", 1, 1, 0, 0, 30.0)
    assert "left" not in line
    assert "~" not in line


def test_remaining_segment_rendered_after_elapsed():
    line = format_status_bar("site.yml", 1, 1, 0, 0, 323.0, remaining_seconds=100.0)
    # 100s → "1m40s"; sits after the elapsed clock.
    assert "0:05:23  ~1m40s left" in line


def test_remaining_segment_is_dimmed_when_colorized():
    line = format_status_bar("site.yml", 1, 1, 0, 0, 30.0, remaining_seconds=42.0, colorize=True)
    assert f"{_DIM}~42s left{_RESET}" in line


def test_remaining_segment_has_no_separator_pipe_before_it():
    line = format_status_bar("site.yml", 1, 1, 0, 0, 30.0, remaining_seconds=42.0)
    # Flush against elapsed with a single space, not " │ ~42s left".
    assert "0:00:30  ~42s left" in line
    assert "│ ~42s left" not in line


def test_remaining_zero_still_renders():
    line = format_status_bar("site.yml", 1, 1, 0, 0, 30.0, remaining_seconds=0.0)
    assert "~0s left" in line
