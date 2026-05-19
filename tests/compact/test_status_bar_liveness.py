"""Tests for the liveness segment in ``format_status_bar``.

When a ``LivenessState`` is passed in, the status bar grows one extra
segment placed immediately before the elapsed-time segment, with no
separator pipe between it and the preceding segment (it sits flush
against the deprecation count when present). See the spec at
``docs/superpowers/specs/2026-05-19-liveness-indicator-design.md``.
"""

from __future__ import annotations

from ansible_aom.compact.renderer import (
    _DIM,
    _GREEN,
    _RED,
    _RESET,
    format_status_bar,
)
from ansible_aom.core.heartbeat import LivenessState


def test_no_segment_when_liveness_is_none():
    line = format_status_bar("site.yml", 1, 1, 0, 0, 30.0)
    assert "●" not in line
    assert "○" not in line


def test_live_segment_rendered_with_dot_and_age():
    line = format_status_bar(
        "site.yml",
        1,
        1,
        0,
        0,
        30.0,
        liveness=LivenessState(level="live", age_s=3),
    )
    assert "● 3s" in line


def test_working_segment_rendered_with_open_circle():
    line = format_status_bar(
        "site.yml",
        1,
        1,
        0,
        0,
        30.0,
        liveness=LivenessState(level="working", age_s=18),
    )
    assert "○ 18s" in line


def test_stuck_segment_rendered_with_bang():
    line = format_status_bar(
        "site.yml",
        1,
        1,
        0,
        0,
        30.0,
        liveness=LivenessState(level="stuck", age_s=90),
    )
    assert "! 90s" in line


def test_ascii_mode_falls_back_to_plain_glyphs():
    live = format_status_bar(
        "site.yml",
        1,
        1,
        0,
        0,
        30.0,
        ascii_mode=True,
        liveness=LivenessState(level="live", age_s=2),
    )
    working = format_status_bar(
        "site.yml",
        1,
        1,
        0,
        0,
        30.0,
        ascii_mode=True,
        liveness=LivenessState(level="working", age_s=20),
    )
    assert "* 2s" in live
    assert "o 20s" in working


def test_segment_inserted_directly_before_elapsed_no_separator_after_predecessor():
    """The liveness segment hugs the preceding segment (no `│` before it)
    and has the normal `│` separator on its right, before elapsed."""
    line = format_status_bar(
        "site.yml",
        1,
        1,
        0,
        2,  # deprecations present so '✱ 2' is the preceding segment
        30.0,
        liveness=LivenessState(level="live", age_s=3),
    )
    # The segment sits flush against the deprecation count:
    assert "✱ 2 ● 3s" in line
    # And the elapsed segment still follows behind a separator pipe:
    assert "● 3s │ 0:00:30" in line


def test_segment_present_even_with_zero_deprecations_and_warnings():
    line = format_status_bar(
        "site.yml",
        1,
        1,
        0,
        0,
        30.0,
        tasks_completed=5,
        tasks_total=10,
        liveness=LivenessState(level="working", age_s=12),
    )
    assert "5/10 tasks ○ 12s │ 0:00:30" in line


def test_live_segment_is_green_when_colorized():
    line = format_status_bar(
        "site.yml",
        1,
        1,
        0,
        0,
        30.0,
        colorize=True,
        liveness=LivenessState(level="live", age_s=3),
    )
    assert f"{_GREEN}● 3s{_RESET}" in line


def test_working_segment_is_dim_when_colorized():
    line = format_status_bar(
        "site.yml",
        1,
        1,
        0,
        0,
        30.0,
        colorize=True,
        liveness=LivenessState(level="working", age_s=18),
    )
    assert f"{_DIM}○ 18s{_RESET}" in line


def test_stuck_segment_is_red_when_colorized():
    line = format_status_bar(
        "site.yml",
        1,
        1,
        0,
        0,
        30.0,
        colorize=True,
        liveness=LivenessState(level="stuck", age_s=90),
    )
    assert f"{_RED}! 90s{_RESET}" in line


def test_no_color_in_segment_when_colorize_off():
    line = format_status_bar(
        "site.yml",
        1,
        1,
        0,
        0,
        30.0,
        liveness=LivenessState(level="stuck", age_s=90),
    )
    assert "\x1b[" not in line
