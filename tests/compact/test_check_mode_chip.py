"""Tests for the ``DRY RUN`` / ``DIFF`` chip in the status bar.

Users sometimes forget they're in ``--check`` mode after switching
terminal tabs. A persistent yellow ``DRY RUN`` chip in the leftmost
status slot makes the mode unmistakable; a cyan ``DIFF`` chip
flags ``--diff`` for the same reason. Both can appear together.
"""

from __future__ import annotations

from ansible_aom.compact.renderer import (
    _CYAN,
    _GREEN,
    _YELLOW,
    _compute_mode_label,
    format_status_bar,
)


class TestComputeModeLabel:
    def test_no_flags_yields_empty_label(self):
        assert _compute_mode_label([], colorize=True) == ""
        assert _compute_mode_label(["-i", "inv.ini", "--limit", "web"], colorize=True) == ""

    def test_check_long_flag_yields_dry_run_label(self):
        label = _compute_mode_label(["--check"], colorize=True)
        assert _YELLOW in label and "DRY RUN" in label

    def test_check_short_flag_also_caught(self):
        label = _compute_mode_label(["-C"], colorize=True)
        assert "DRY RUN" in label

    def test_diff_long_flag_yields_diff_label(self):
        label = _compute_mode_label(["--diff"], colorize=True)
        assert _CYAN in label and "DIFF" in label

    def test_diff_short_flag_also_caught(self):
        label = _compute_mode_label(["-D"], colorize=True)
        assert "DIFF" in label

    def test_check_and_diff_combine(self):
        label = _compute_mode_label(["--check", "--diff"], colorize=True)
        assert "DRY RUN" in label
        assert "DIFF" in label

    def test_substring_in_other_arg_does_not_false_positive(self):
        """``--check-something`` shouldn't trip the literal ``--check`` chip."""
        label = _compute_mode_label(["--check-something", "--my-diff-thing"], colorize=True)
        assert label == ""

    def test_no_color_emits_plain_label(self):
        label = _compute_mode_label(["--check"], colorize=False)
        assert "DRY RUN" in label
        assert "\x1b[" not in label

    def test_recording_label_is_present_by_default(self):
        label = _compute_mode_label([], colorize=False, recording=True)
        assert label == "● REC"

    def test_recording_label_is_green_when_colorized(self):
        label = _compute_mode_label([], colorize=True, recording=True)
        assert _GREEN in label and "● REC" in label

    def test_verbose_capture_upgrades_recording_label(self):
        label = _compute_mode_label([], colorize=False, recording=True, capture_verbose=True)
        assert label == "● REC+VC"

    def test_recording_label_precedes_check_and_diff(self):
        label = _compute_mode_label(
            ["--check", "--diff"],
            colorize=False,
            recording=True,
            capture_verbose=True,
        )
        assert label == "● REC+VC DRY RUN DIFF"


class TestStatusBarMode:
    def test_mode_label_lands_first_when_set(self):
        line = format_status_bar(
            "site.yml",
            0,
            1,
            0,
            0,
            10.0,
            mode_label="DRY RUN",
        )
        # The chip should appear before the playbook path in the joined line.
        assert line.startswith("DRY RUN")
        assert "site.yml" in line.split("DRY RUN", 1)[1]

    def test_recording_label_lands_first_when_set(self):
        line = format_status_bar(
            "site.yml",
            0,
            1,
            0,
            0,
            10.0,
            mode_label="● REC+VC",
        )
        assert line.startswith("● REC+VC")
        assert "site.yml" in line.split("● REC+VC", 1)[1]

    def test_no_mode_label_is_unchanged(self):
        without = format_status_bar("site.yml", 0, 1, 0, 0, 10.0)
        with_empty = format_status_bar("site.yml", 0, 1, 0, 0, 10.0, mode_label="")
        assert without == with_empty
