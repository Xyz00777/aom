"""Tests for width-aware row counting (roadmap #12).

`_row_count` decides how many lines the rewind step has to cursor-up
after writing the status panel. The newline-only counter undercounts
when the status bar overflows the terminal and wraps — leaving stale
content un-cleared on the next redraw. Counting wrap-rows fixes the
narrow-terminal case and is the prerequisite for proper SIGWINCH
handling.
"""

from __future__ import annotations

from ansible_aom.compact.display import _row_count


def test_row_count_empty_string_zero_rows():
    assert _row_count("", width=80) == 0


def test_row_count_short_line_one_row():
    assert _row_count("hello", width=80) == 1


def test_row_count_trailing_newline_does_not_add_row():
    """After 'abc\\n' the cursor sits on the next row but nothing is rendered there."""
    assert _row_count("abc\n", width=80) == 1


def test_row_count_two_lines_two_rows():
    assert _row_count("abc\ndef", width=80) == 2


def test_row_count_two_lines_with_trailing_newline():
    assert _row_count("abc\ndef\n", width=80) == 2


def test_row_count_exact_width_one_row():
    """A line exactly `width` chars long fits on one row (no wrap)."""
    assert _row_count("x" * 80, width=80) == 1


def test_row_count_one_over_width_wraps_to_two_rows():
    assert _row_count("x" * 81, width=80) == 2


def test_row_count_double_width_wraps_to_two_rows():
    assert _row_count("x" * 160, width=80) == 2


def test_row_count_just_over_double_width_three_rows():
    assert _row_count("x" * 161, width=80) == 3


def test_row_count_multiline_with_one_wrapping_line():
    """First line wraps to 2 rows, second line takes 1 row → 3 total."""
    text = ("x" * 81) + "\n" + "abc"
    assert _row_count(text, width=80) == 3


def test_row_count_narrow_terminal_short_text_wraps():
    """A 50-char line in a 24-col terminal wraps to ceil(50/24) = 3 rows."""
    assert _row_count("x" * 50, width=24) == 3


def test_row_count_blank_lines_count_as_one_row_each():
    """Empty strings between newlines are still rows the cursor crosses."""
    assert _row_count("a\n\nb", width=80) == 3


def test_row_count_ignores_ansi_escape_sequences():
    """ANSI escape bytes are zero-width on screen — they must not push
    a status line over the wrap threshold.

    Before this guard, a colorised status bar (many SGR escapes around
    every segment) wrapped to a phantom second row in ``_row_count``.
    The rewind step then sent the cursor one row higher than the visible
    status, and the subsequent clear-to-EOS wiped a log line above.
    """
    # The exact status bar the user's compact renderer emits for a
    # mid-run colourised view. Visible width is ~64 chars (fits in 120
    # easily); total byte length is 156 because of the SGR overhead.
    from ansible_aom.compact.renderer import format_status_bar
    from ansible_aom.core.heartbeat import LivenessState

    bar = format_status_bar(
        "general.yml",
        1,
        1,
        3,
        1,
        14,
        tasks_completed=21,
        tasks_total=89,
        colorize=True,
        liveness=LivenessState(level="live", age_s=3),
    )
    assert _row_count(bar, width=120) == 1


def test_row_count_ansi_long_line_still_wraps_correctly():
    """ANSI codes are excluded from the wrap calculation; visible chars
    are what counts. 90 visible chars at width=80 wraps to 2 rows even
    with ANSI overhead pushing the byte length past 160."""
    text = "\x1b[32m" + ("x" * 90) + "\x1b[0m"
    assert _row_count(text, width=80) == 2


def test_display_update_records_wrapped_row_count(monkeypatch):
    """After update() in a narrow terminal, _status_rows reflects wrapped rows.

    SIGWINCH self-heal: ``Display._terminal_width`` reads the kernel size
    on each render, so a narrow window makes the rewind step skip past
    every wrapped row of the previous status frame.
    """
    import io
    from contextlib import redirect_stdout

    from ansible_aom.compact import display as display_module
    from ansible_aom.compact.display import Display

    monkeypatch.setattr(display_module, "_terminal_width", lambda: 20)

    buf = io.StringIO()
    with redirect_stdout(buf):
        d = Display(is_tty=True)
        d.start()
        # 50 chars at width=20 → ceil(50/20) = 3 wrapped rows.
        d.update("x" * 50)
        # Capture the row count from this render before stop() resets it.
        rows_after_update = d._status_rows

    assert rows_after_update == 3
