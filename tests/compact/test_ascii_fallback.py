"""Tests for ASCII fallback in the compact renderer (TC-060 / TC-377).

The status bar and per-host summary use Unicode glyphs (│, ⚠, ✱, ●, ◆,
✖) by default. On terminals without UTF-8 (LANG=C, stripped-down
serial consoles, dumb pipes) those characters render as `?` or
mojibake, leaving the user to guess what the indicator means. When
``sys.stdout.encoding`` doesn't promise UTF-8, fall back to ASCII
glyphs that survive any encoding.
"""

from __future__ import annotations

from unittest.mock import patch

from ansible_aom.compact.renderer import format_host_summary, format_status_bar
from ansible_aom.core.icons import is_unicode_terminal

# -- detection ------------------------------------------------------


def test_is_unicode_terminal_true_for_utf8():
    with patch("sys.stdout") as mock_stdout:
        mock_stdout.encoding = "utf-8"
        assert is_unicode_terminal() is True


def test_is_unicode_terminal_true_for_uppercase_utf8():
    with patch("sys.stdout") as mock_stdout:
        mock_stdout.encoding = "UTF-8"
        assert is_unicode_terminal() is True


def test_is_unicode_terminal_false_for_ascii():
    with patch("sys.stdout") as mock_stdout:
        mock_stdout.encoding = "ascii"
        assert is_unicode_terminal() is False


def test_is_unicode_terminal_false_for_none_encoding():
    """Some pipe wrappers expose `encoding = None` — be defensive."""
    with patch("sys.stdout") as mock_stdout:
        mock_stdout.encoding = None
        assert is_unicode_terminal() is False


# -- format_status_bar ----------------------------------------------


def test_format_status_bar_ascii_mode_uses_pipe_separator():
    result = format_status_bar(
        playbook="site.yml",
        hosts_completed=1,
        hosts_total=5,
        warnings=2,
        deprecations=1,
        elapsed_seconds=10,
        ascii_mode=True,
    )
    assert "│" not in result
    assert " | " in result


def test_format_status_bar_ascii_mode_uses_ascii_warning_glyph():
    result = format_status_bar(
        playbook="site.yml",
        hosts_completed=1,
        hosts_total=5,
        warnings=2,
        deprecations=1,
        elapsed_seconds=10,
        ascii_mode=True,
    )
    assert "⚠" not in result
    assert "✱" not in result
    assert "! 2" in result
    assert "* 1" in result


def test_format_status_bar_unicode_mode_keeps_unicode_glyphs():
    result = format_status_bar(
        playbook="site.yml",
        hosts_completed=1,
        hosts_total=5,
        warnings=1,
        deprecations=0,
        elapsed_seconds=10,
    )
    assert "│" in result
    assert "⚠ 1" in result


# -- format_host_summary --------------------------------------------


def test_format_host_summary_ascii_mode_uses_ascii_icons():
    result = format_host_summary(
        hostname="web1", ok=3, changed=1, failed=0, unreachable=0, ascii_mode=True
    )
    assert "●" not in result
    assert "◆" not in result
    # STATUS_ICONS_ASCII: OK=*, CHANGED=+
    assert "* 3 ok" in result
    assert "+ 1 changed" in result


def test_format_host_summary_unicode_mode_default():
    result = format_host_summary(hostname="web1", ok=3, changed=1, failed=0, unreachable=0)
    assert "● 3 ok" in result
    assert "◆ 1 changed" in result
