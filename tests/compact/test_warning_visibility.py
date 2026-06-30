"""Tests that warnings are not just counted but also surfaced as text.

Counter-only display ("⚠ 1") is unhelpful — the user has no idea what
the warning was about. CompactRenderer.add_warning should print the
message above the panel as well as bump the counter, deduped so a
warning that fires once per host doesn't flood the log.
"""

from __future__ import annotations

from unittest.mock import patch

from ansible_aom.compact.renderer import CompactRenderer


def test_add_warning_prints_message_above_panel():
    renderer = CompactRenderer(is_tty=False)
    renderer.start("site.yml", [])

    with patch.object(renderer._display, "print_log") as mock_print:
        renderer.add_warning("Module foo is deprecated", is_deprecation=True)

    mock_print.assert_called_once()
    msg = mock_print.call_args.args[0]
    assert "Module foo is deprecated" in msg


def test_add_warning_message_is_prefixed_for_classification():
    """A glance at the printed line should distinguish warning vs deprecation."""
    renderer = CompactRenderer(is_tty=False)
    renderer.start("site.yml", [])

    with patch.object(renderer._display, "print_log") as mock_print:
        renderer.add_warning("plain warning", is_deprecation=False)
        renderer.add_warning("dep warning", is_deprecation=True)

    msgs = [call.args[0] for call in mock_print.call_args_list]
    assert any("warning" in m.lower() and "plain warning" in m for m in msgs)
    assert any("deprec" in m.lower() and "dep warning" in m for m in msgs)


def test_add_warning_counter_still_bumps():
    """Making warnings visible must not regress the counter behaviour."""
    renderer = CompactRenderer(is_tty=False)
    renderer.start("site.yml", [])

    renderer.add_warning("w1", is_deprecation=False)
    renderer.add_warning("w2", is_deprecation=False)
    renderer.add_warning("d1", is_deprecation=True)

    assert renderer._warnings_count == 2
    assert renderer._deprecations_count == 1


def test_add_warning_dedupes_repeated_messages():
    """Same warning text fired N times → still printed once. Counter still bumps."""
    renderer = CompactRenderer(is_tty=False)
    renderer.start("site.yml", [])

    with patch.object(renderer._display, "print_log") as mock_print:
        renderer.add_warning("repeat me", is_deprecation=False)
        renderer.add_warning("repeat me", is_deprecation=False)
        renderer.add_warning("repeat me", is_deprecation=False)

    assert mock_print.call_count == 1
    assert renderer._warnings_count == 3


def test_add_warning_distinct_messages_each_print():
    renderer = CompactRenderer(is_tty=False)
    renderer.start("site.yml", [])

    with patch.object(renderer._display, "print_log") as mock_print:
        renderer.add_warning("one", is_deprecation=False)
        renderer.add_warning("two", is_deprecation=False)
        renderer.add_warning("three", is_deprecation=False)

    assert mock_print.call_count == 3
