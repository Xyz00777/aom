"""Warnings emitted to the log must be coloured yellow and deprecations
orange so they stand out from ordinary log lines.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from ansible_aom.compact.format import _ORANGE, _YELLOW
from ansible_aom.compact.renderer import CompactRenderer


def _renderer() -> CompactRenderer:
    r = CompactRenderer(is_tty=False)
    r.start("test.yml", [])
    # Force colorize on so the SGR wrapping is observable in non-TTY tests.
    r._colorize = True
    r._display = MagicMock()
    return r


def _printed(r: CompactRenderer) -> list[str]:
    return [c.args[0] for c in r._display.print_log.call_args_list]


def test_warning_wrapped_in_yellow() -> None:
    r = _renderer()
    r.add_warning("[WARNING]: Using run_once with the free strategy")
    (line,) = _printed(r)
    assert _YELLOW in line
    assert "[WARNING]: Using run_once" in line


def test_deprecation_wrapped_in_orange() -> None:
    r = _renderer()
    r.add_warning("[DEPRECATION WARNING]: foo bar baz", is_deprecation=True)
    (line,) = _printed(r)
    assert _ORANGE in line
    assert "[DEPRECATION WARNING]: foo bar baz" in line


def test_warning_without_color_when_colorize_off() -> None:
    r = _renderer()
    r._colorize = False
    r.add_warning("[WARNING]: plain text mode")
    (line,) = _printed(r)
    assert _YELLOW not in line
    assert _ORANGE not in line
    assert "[WARNING]: plain text mode" in line


def test_warning_with_synthesised_prefix_also_colored() -> None:
    """add_warning falls through to a `[WARNING] msg` synthesis when the
    raw text doesn't start with ``[``. That branch must wrap too."""
    r = _renderer()
    r.add_warning("missing role 'x'")
    (line,) = _printed(r)
    assert _YELLOW in line
    assert "[WARNING] missing role 'x'" in line
