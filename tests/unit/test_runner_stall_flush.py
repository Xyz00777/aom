"""Tests for the stall-flush safety net (IP2).

When the child produces output without a trailing newline AND no
known prompt marker matches, the runner doesn't know whether it's a
real prompt or just a slow task. Blocking for stdin on a false
positive would lock the run, so the safety net is **visibility-only**:
after N consecutive TIMEOUTs with non-empty unread buffer, flush the
held content as a log line so the user can see what's stuck. It
never reads from stdin in this path.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from ansible_aom.runner import (
    _STALL_FLUSH_TIMEOUTS,
    _STALL_HINT_TIMEOUTS,
    _handle_timeout_branch,
    _looks_like_interactive_prompt,
)


class _FakeChild:
    """Minimal pexpect-like child for unit testing the TIMEOUT branch."""

    def __init__(self, buffer_value: str = "") -> None:
        self.buffer = buffer_value
        self.sent_lines: list[str] = []

    def sendline(self, line: str) -> None:  # pragma: no cover - not used here
        self.sent_lines.append(line)


class _FakeSink:
    def __init__(self) -> None:
        self.stderr_lines: list[str] = []

    def record_event(self, event: dict) -> None: ...
    def record_stderr(self, line: str) -> None:
        self.stderr_lines.append(line)

    def end(self, status: str) -> None: ...


class TestLooksLikePrompt:
    """The heuristic used to gate the blocking-input path."""

    def test_empty_buffer_is_not_a_prompt(self) -> None:
        assert _looks_like_interactive_prompt("") is False
        assert _looks_like_interactive_prompt("   \n") is False

    def test_known_marker_with_colon_is_prompt(self) -> None:
        assert _looks_like_interactive_prompt("[pause]\nPress Enter: ") is True
        assert _looks_like_interactive_prompt("Continue? (yes/no): ") is True

    def test_question_mark_alone_is_a_prompt(self) -> None:
        assert _looks_like_interactive_prompt("Which env? ") is True

    def test_trailing_colon_without_marker_is_NOT_a_prompt(self) -> None:
        """Pure ``something:`` is too risky — many debug tasks end in colon."""
        assert _looks_like_interactive_prompt("error:") is False
        assert _looks_like_interactive_prompt("Installing packages:") is False

    def test_no_terminator_is_not_a_prompt(self) -> None:
        """No colon, no question mark → don't treat as prompt."""
        assert _looks_like_interactive_prompt("Press Enter to continue") is False

    def test_vars_prompt_default_format_is_caught(self) -> None:
        """ansible vars_prompt without custom text uses ``[name]: ``."""
        assert _looks_like_interactive_prompt("[deploy_env]: ") is True
        assert _looks_like_interactive_prompt("[name] (default): ") is True

    def test_log_line_containing_bracketed_word_is_not_a_prompt(self) -> None:
        """Defensive: don't false-positive on log lines mentioning [INFO]."""
        # Bracketed word in the middle isn't a prompt.
        assert _looks_like_interactive_prompt("[INFO] processing: 5 items") is False
        # Bracketed word followed by colon BUT with other text after isn't a prompt.
        assert _looks_like_interactive_prompt("[INFO]: starting up") is False

    def test_real_ansible_pause_with_ansi_codes_is_caught(self) -> None:
        """Real ansible colorises pause output — buffer ends in ``\\x1b[0m``.

        Without ANSI stripping the trailing-char check sees ``m`` and
        rejects. With stripping it sees ``:`` and we match either via
        the "Press Enter" marker or the bracketed-header rule.
        """
        # SGR sequences around both the header and the prompt — what
        # `ansible-playbook` emits when stdout is a TTY (it always is
        # via pexpect).
        prompt = (
            "\x1b[1;35m[Confirm deployment]\x1b[0m\n"
            "\x1b[1;35mDeploy to web1 (example.com)?"
            " Press Enter to continue or Ctrl+C to abort:\x1b[0m"
        )
        assert _looks_like_interactive_prompt(prompt) is True

    def test_real_ansible_pause_no_press_enter_phrasing_still_caught(self) -> None:
        """A custom pause prompt without the canonical phrasing.

        The user-provided ``prompt:`` doesn't have to mention "Press
        Enter" — only the ansible-emitted ``[Task name]`` header
        identifies it. The bracketed-header rule must catch it.
        """
        prompt = "[Confirm rollback]\nReally proceed?: "
        # Both signals are present (trailing `?:` ends in `:`, plus the
        # bracketed header) — `_looks_like_interactive_prompt` should
        # accept either.
        assert _looks_like_interactive_prompt(prompt) is True

    def test_real_ansible_pause_with_plain_colon_and_header(self) -> None:
        """Header + bare colon (no markers, no question mark) is still a prompt."""
        prompt = "[Confirm deployment]\nProceed: "
        assert _looks_like_interactive_prompt(prompt) is True

    def test_prior_plaintext_header_catches_split_chunks(self) -> None:
        """When the header was consumed earlier and only the prompt tail
        sits in the buffer, the prior_plaintext signal must catch it."""
        # The buffer alone has nothing distinctive.
        assert _looks_like_interactive_prompt("Proceed: ") is False
        # Same buffer, but the prior consumed line was the header.
        assert (
            _looks_like_interactive_prompt("Proceed: ", prior_plaintext="[Confirm deployment]")
            is True
        )

    def test_prior_plaintext_non_header_does_not_catch(self) -> None:
        """An ordinary log line as the prior plaintext is not a signal."""
        assert (
            _looks_like_interactive_prompt("Proceed: ", prior_plaintext="ok: [web1] => done")
            is False
        )


class TestStallFlushDoesNotBlock:
    """Stall safety net must never call handle_interactive_prompt."""

    def test_below_threshold_does_nothing_to_buffer(self) -> None:
        child = _FakeChild(buffer_value="Installing packages...")
        renderer = MagicMock()
        sink = _FakeSink()

        new_count = _handle_timeout_branch(
            child, renderer, sink, stall_count=_STALL_FLUSH_TIMEOUTS - 2
        )

        # One step closer to the flush, but no flush yet.
        assert new_count == _STALL_FLUSH_TIMEOUTS - 1
        assert child.buffer == "Installing packages..."
        renderer.print_log.assert_not_called()
        renderer.handle_interactive_prompt.assert_not_called()

    def test_at_threshold_flushes_buffer_as_log(self) -> None:
        held_content = "Long compile step\nstill working..."
        child = _FakeChild(buffer_value=held_content)
        renderer = MagicMock()
        sink = _FakeSink()

        new_count = _handle_timeout_branch(
            child, renderer, sink, stall_count=_STALL_FLUSH_TIMEOUTS - 1
        )

        # Buffer drained, count reset, content surfaced to the renderer.
        assert child.buffer == ""
        assert new_count == 0
        printed = [c.args[0] for c in renderer.print_log.call_args_list]
        assert "Long compile step" in printed
        assert "still working..." in printed
        # And never blocks for input.
        renderer.handle_interactive_prompt.assert_not_called()

    def test_quiet_child_just_ticks(self) -> None:
        """No buffered output → nothing to flush; just tick the clock."""
        child = _FakeChild(buffer_value="")
        renderer = MagicMock()
        sink = _FakeSink()

        new_count = _handle_timeout_branch(child, renderer, sink, stall_count=5)

        # No buffer means no stall progress.
        assert new_count == 5
        renderer.tick.assert_called_once()
        renderer.print_log.assert_not_called()
        renderer.handle_interactive_prompt.assert_not_called()

    def test_flush_records_to_session_sink(self) -> None:
        child = _FakeChild(buffer_value="held line one\nheld line two")
        renderer = MagicMock()
        sink = _FakeSink()

        _handle_timeout_branch(child, renderer, sink, stall_count=_STALL_FLUSH_TIMEOUTS - 1)

        # Both held lines are mirrored to the session log so a later
        # `aom inspect show` can replay what was stuck.
        assert "held line one" in sink.stderr_lines
        assert "held line two" in sink.stderr_lines


class TestHighConfidencePromptPath:
    """When the heuristic fires, the blocking-input path takes over."""

    def test_known_prompt_drains_buffer_and_calls_handler(self) -> None:
        child = _FakeChild(buffer_value="[pause]\nPress Enter: ")
        renderer = MagicMock()
        renderer.handle_interactive_prompt.return_value = "yes"
        sink = _FakeSink()

        new_count = _handle_timeout_branch(child, renderer, sink, stall_count=0)

        # Sentinel negative value marks "prompt already fired in this
        # silent window — don't re-fire on subsequent timeouts until a
        # newline arrives and the caller resets to 0".
        assert new_count == -1
        assert child.buffer == ""
        renderer.handle_interactive_prompt.assert_called_once()
        # Answer sent through sendline; sink records the interaction.
        assert child.sent_lines == ["yes"]
        assert any("[user-input] yes" in line for line in sink.stderr_lines)

    def test_renderer_crash_sends_empty_line_to_avoid_hang(self) -> None:
        """A crashing renderer must not leave the child blocked forever."""
        child = _FakeChild(buffer_value="[pause]\nPress Enter: ")
        renderer = MagicMock()
        renderer.handle_interactive_prompt.side_effect = RuntimeError("boom")
        sink = _FakeSink()

        _handle_timeout_branch(child, renderer, sink, stall_count=0)

        # Empty string forwarded so pause accepts "continue".
        assert child.sent_lines == [""]


class TestPriorPlaintextPromptPath:
    """When the prompt itself arrived newline-terminated.

    Real ansible.builtin.pause output (from live trace):
        TASK [Confirm deployment] ********
        [Confirm deployment]\\r\\n
        Deploy to host (env)? Press Enter to continue or Ctrl+C to abort:\\r\\n

    Each line ends with ``\\r\\n``, so pexpect's newline matcher
    consumes them cleanly and ``child.buffer`` is empty when TIMEOUT
    fires. The signal is in ``prior_plaintext`` — the most recently
    consumed line — which contains the prompt text.
    """

    def test_prior_prompt_with_empty_buffer_fires(self) -> None:
        child = _FakeChild(buffer_value="")
        renderer = MagicMock()
        renderer.handle_interactive_prompt.return_value = "yes"
        sink = _FakeSink()

        new_count = _handle_timeout_branch(
            child,
            renderer,
            sink,
            stall_count=0,
            prior_plaintext="Deploy to web1? Press Enter to continue: ",
        )

        renderer.handle_interactive_prompt.assert_called_once()
        # Answer forwarded to child stdin.
        assert child.sent_lines == ["yes"]
        # Sentinel marks the window as handled.
        assert new_count == -1

    def test_prior_non_prompt_does_not_fire(self) -> None:
        """An ordinary log line shouldn't trigger the prompt path."""
        child = _FakeChild(buffer_value="")
        renderer = MagicMock()
        sink = _FakeSink()

        new_count = _handle_timeout_branch(
            child,
            renderer,
            sink,
            stall_count=0,
            prior_plaintext="Monday 11 May 2026  13:59:14 +0200 (0:00:01.740)",
        )

        renderer.handle_interactive_prompt.assert_not_called()
        # No state change in a quiet-with-no-prompt window.
        assert new_count == 0


class TestSentinelPreventsRefiring:
    """Once a prompt has fired, subsequent timeouts in the same window
    must not re-trigger until a newline resets the stall counter."""

    def test_negative_stall_count_skips_prompt_path(self) -> None:
        child = _FakeChild(buffer_value="[pause]\nPress Enter: ")
        renderer = MagicMock()
        sink = _FakeSink()

        new_count = _handle_timeout_branch(
            child, renderer, sink, stall_count=-1, prior_plaintext=None
        )

        # No prompt fired, stall_count preserved.
        renderer.handle_interactive_prompt.assert_not_called()
        assert new_count == -1
        # Renderer's clock still ticks so the elapsed-time UI keeps moving.
        renderer.tick.assert_called_once()

    def test_negative_stall_count_with_prior_prompt_still_skips(self) -> None:
        """Even if the prior line is a prompt, sentinel blocks re-firing."""
        child = _FakeChild(buffer_value="")
        renderer = MagicMock()
        sink = _FakeSink()

        _handle_timeout_branch(
            child,
            renderer,
            sink,
            stall_count=-1,
            prior_plaintext="Press Enter to continue: ",
        )

        renderer.handle_interactive_prompt.assert_not_called()

    def test_prompt_path_emits_visible_breadcrumb(self) -> None:
        """A detected prompt prints a [aom] hint so the user sees what's happening."""
        child = _FakeChild(buffer_value="[pause]\nPress Enter: ")
        renderer = MagicMock()
        renderer.handle_interactive_prompt.return_value = ""
        sink = _FakeSink()

        _handle_timeout_branch(child, renderer, sink, stall_count=0)

        printed = [c.args[0] for c in renderer.print_log.call_args_list]
        assert any("[aom]" in line and "prompt" in line for line in printed), printed


class TestStallHintBeforeFlush:
    """Earlier visible hint before the flush threshold."""

    def test_hint_fires_at_hint_threshold(self) -> None:
        child = _FakeChild(buffer_value="some slow output still happening")
        renderer = MagicMock()
        sink = _FakeSink()

        # Going IN at one-less-than-hint so the increment lands on it.
        _handle_timeout_branch(child, renderer, sink, stall_count=_STALL_HINT_TIMEOUTS - 1)

        printed = [c.args[0] for c in renderer.print_log.call_args_list]
        assert any("[aom]" in line and "waiting" in line for line in printed)
        # Buffer untouched — flush comes later.
        assert child.buffer == "some slow output still happening"
        renderer.handle_interactive_prompt.assert_not_called()

    def test_hint_only_fires_once(self) -> None:
        """Subsequent timeouts past the hint threshold don't repeat it."""
        child = _FakeChild(buffer_value="slow")
        renderer = MagicMock()
        sink = _FakeSink()

        # Already past the hint threshold; increment goes further past.
        _handle_timeout_branch(child, renderer, sink, stall_count=_STALL_HINT_TIMEOUTS + 1)

        printed = [c.args[0] for c in renderer.print_log.call_args_list]
        assert not any("waiting" in line for line in printed), printed
