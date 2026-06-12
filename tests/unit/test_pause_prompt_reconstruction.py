"""Tests for reconstruct_pause_prompt (multi-line ``|`` pause prompts).

A YAML ``|`` block-scalar ``prompt:`` keeps a trailing newline, so
ansible's ``"[%s]\\n%s:"`` pause format puts the terminating ``:`` on
its OWN line. Every line of the block ends ``\\r\\n``, so pexpect's
newline matcher consumes the whole block and the unread buffer is empty
when the PTY read TIMEOUTs — the lone ``:`` last line carries no signal
and the identifying ``[Task name]`` header is several lines back.

``reconstruct_pause_prompt`` rebuilds the block from the recent
plaintext tail so the existing detector can recognise it.
"""

from __future__ import annotations

from ansible_aom.core.prompts import (
    looks_like_interactive_prompt,
    reconstruct_pause_prompt,
)

# The exact plaintext lines captured from a real ``ansible-playbook``
# run of a ``pause:`` task whose ``prompt:`` is a YAML ``|`` block.
_REAL_BLOCK = [
    "[Confirm deployment]",
    "Deploy to localhost (example.com)?",
    "",
    "Press Enter to continue or Ctrl+C to abort",
    ":",
]


class TestReconstructPausePrompt:
    def test_lone_colon_after_header_rebuilds_block(self) -> None:
        block = reconstruct_pause_prompt(_REAL_BLOCK)
        assert block is not None
        # The reconstructed block starts at the header and ends at the colon.
        assert block.startswith("[Confirm deployment]")
        assert block.rstrip().endswith(":")
        # And the existing detector recognises it.
        assert looks_like_interactive_prompt(block) is True

    def test_empty_list_is_none(self) -> None:
        assert reconstruct_pause_prompt([]) is None

    def test_no_header_in_window_is_none(self) -> None:
        # Tail ends in ``:`` but there's no ``[Task name]`` header at all.
        lines = ["Installing things", "downloading", ":"]
        assert reconstruct_pause_prompt(lines) is None

    def test_tail_not_a_terminator_is_none(self) -> None:
        # Last line doesn't end in ``:`` or ``?`` — not a blocked prompt.
        lines = ["[Confirm deployment]", "Deploy?", "ok: [localhost]"]
        assert reconstruct_pause_prompt(lines) is None

    def test_trailing_blank_line_is_none(self) -> None:
        """After the prompt is answered the PTY echoes a newline.

        The echoed blank line becomes the new tail; reconstruct must
        NOT walk back past it and re-surface the just-answered block
        (which would re-fire the prompt and send a spurious newline).
        """
        answered = [*_REAL_BLOCK, ""]
        assert reconstruct_pause_prompt(answered) is None

    def test_header_beyond_lookback_is_none(self) -> None:
        """A stale header far above an unrelated trailing colon must not match."""
        lines = ["[Old pause]", *[f"line {i}" for i in range(30)], "something:"]
        assert reconstruct_pause_prompt(lines, max_lookback=20) is None

    def test_nearest_header_wins_for_second_pause(self) -> None:
        """Two pause blocks back-to-back: rebuild only the latest one."""
        lines = [
            "[First pause]",
            "Proceed?",
            ":",
            "[Second pause]",
            "Really proceed?",
            ":",
        ]
        block = reconstruct_pause_prompt(lines)
        assert block is not None
        assert block.startswith("[Second pause]")
        assert "First pause" not in block

    def test_long_preview_anchors_on_marker_when_header_out_of_window(self) -> None:
        """A long preview block pushes the ``[header]`` beyond the lookback
        window. The ``Press Enter`` marker line just above the colon must
        still anchor the block so the prompt fires."""
        lines = [
            "[Confirm deployment]",
            "Deploy to epistree (epistree.com)?",
            *[f"  service-{i}: v1.{i}.0 (no change)" for i in range(60)],
            "Press Enter to continue or Ctrl+C to abort",
            ":",
        ]
        # Force the header out of the window so the marker fallback is exercised.
        block = reconstruct_pause_prompt(lines, max_lookback=40)
        assert block is not None
        assert looks_like_interactive_prompt(block) is True
        # Marker-anchored, so the marker + colon are present even though the
        # header is too far back to include.
        assert "Press Enter to continue or Ctrl+C to abort" in block
        assert "[Confirm deployment]" not in block

    def test_moderate_preview_includes_full_context_via_header(self) -> None:
        """A typical preview fits in the generous default window, so the
        whole block (header + preview) is returned for display."""
        lines = [
            "[Confirm deployment]",
            "Deploy to epistree (epistree.com)?",
            *[f"  service-{i}: v1.{i}.0 (no change)" for i in range(20)],
            "Press Enter to continue or Ctrl+C to abort",
            ":",
        ]
        block = reconstruct_pause_prompt(lines)
        assert block is not None
        assert block.startswith("[Confirm deployment]")
        assert "service-0" in block

    def test_marker_only_block_without_header_is_rebuilt(self) -> None:
        """A custom prompt with a ``(yes/no)`` marker but no bracketed header."""
        lines = ["Some output", "Continue with rollout? (yes/no)", ":"]
        block = reconstruct_pause_prompt(lines)
        assert block is not None
        assert looks_like_interactive_prompt(block) is True

    def test_header_preferred_over_marker_for_full_context(self) -> None:
        """When a header is within the window it wins (fuller context)
        even if a marker line sits closer to the colon."""
        lines = [
            "[Confirm deployment]",
            "Deploy now?",
            "Press Enter to continue",
            ":",
        ]
        block = reconstruct_pause_prompt(lines)
        assert block is not None
        assert block.startswith("[Confirm deployment]")

    def test_folded_scalar_single_body_line_is_rebuilt(self) -> None:
        """YAML ``>`` folds the body to one line but keeps the trailing
        newline, so the colon still lands on its own line."""
        lines = [
            "[Confirm deployment]",
            "Deploy to epistree (epistree.com)? Press Enter to continue or Ctrl+C to abort",
            ":",
        ]
        block = reconstruct_pause_prompt(lines)
        assert block is not None
        assert looks_like_interactive_prompt(block) is True

    def test_no_anchor_within_window_is_none(self) -> None:
        """Tail ends in ``:`` but neither a header nor a marker is nearby."""
        lines = ["plain output", "more output", "Result:"]
        assert reconstruct_pause_prompt(lines) is None

    def test_ansi_colorized_block_is_rebuilt(self) -> None:
        """Real ansible colorises pause output with SGR escape sequences."""
        lines = [
            "\x1b[1;35m[Confirm deployment]\x1b[0m",
            "\x1b[1;35mDeploy to web1 (example.com)?\x1b[0m",
            "",
            "\x1b[1;35mPress Enter to continue or Ctrl+C to abort\x1b[0m",
            "\x1b[1;35m:\x1b[0m",
        ]
        block = reconstruct_pause_prompt(lines)
        assert block is not None
        assert looks_like_interactive_prompt(block) is True
