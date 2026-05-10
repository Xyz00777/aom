"""Ansible-playbook runner — pumps PTY output into a Renderer.

This is the infrastructure adapter that wires `core/parser.PtyStreamParser`
to a `Renderer` (compact or TUI) over a real `ansible-playbook` subprocess.
The runner owns the subprocess lifecycle: spawn → loop reading the PTY
stream → password prompts get round-tripped through the renderer →
final exit code routed to handle_completion.

It deliberately handles password prompts at the pexpect layer rather than
through `PtyStreamParser`'s own detection: live PTY prompts have no
trailing newline (`Vault password: ` followed by a wait for input), so
they never reach the parser's line-oriented `feed_line`. We let pexpect
match the prompt patterns directly and call `renderer.handle_password_prompt`
the moment one fires.
"""

from __future__ import annotations

import os
from typing import Any

import pexpect

from ansible_aom.core.parser import PtyStreamParser
from ansible_aom.renderer.protocol import Renderer

# Same patterns the parser uses for replay-time detection. They appear
# here because we need pexpect to recognise them mid-line in the PTY
# stream, not after a newline (the parser's domain).
_PASSWORD_PATTERNS: list[str] = [
    r"Vault password \([^)]+\): ",  # named-vault must come before the bare form
    r"Vault password: ",
    r"SSH password: ",
    r"BECOME password\[defaults to SSH password\]: ",
    r"BECOME password: ",
    r"New Vault password: ",
    r"Confirm New Vault password: ",
]

_DEFAULT_TIMEOUT_S = 0.5


def _build_command(playbook: str, ansible_args: list[str]) -> tuple[str, list[str]]:
    """Return the (executable, args) pair to spawn.

    Split out so tests can patch in a fake executable that emits canned
    JSONL — the rest of the runner exercises the real spawn/expect loop.
    """
    return "ansible-playbook", [playbook, *ansible_args]


def run_playbook(
    playbook: str,
    ansible_args: list[str],
    renderer: Renderer,
    timeout: float = _DEFAULT_TIMEOUT_S,
) -> int:
    """Run a playbook through the renderer; return the subprocess exit code.

    The renderer's lifecycle is fully owned here: `start` is called before
    the spawn, `handle_completion` after the subprocess exits (or fails to
    start), and `stop` always runs in a finally block.
    """
    executable, args = _build_command(playbook, ansible_args)
    env = os.environ.copy()
    env["ANSIBLE_STDOUT_CALLBACK"] = "ansible.posix.jsonl"

    parser = PtyStreamParser()
    renderer.start(playbook, ansible_args)

    child: pexpect.spawn | None = None
    try:
        try:
            child = pexpect.spawn(
                executable,
                args=args,
                env=env,
                encoding="utf-8",
                codec_errors="replace",
                timeout=timeout,
            )
        except pexpect.exceptions.ExceptionPexpect, FileNotFoundError, OSError:
            # Command not found / not executable — surface as 127.
            renderer.handle_completion(127, "crashed")
            return 127

        exit_code = _drive(child, parser, renderer, timeout)
        state = "completed" if exit_code == 0 else "failed"
        renderer.handle_completion(exit_code, state)
        return exit_code

    except KeyboardInterrupt:
        # User hit Ctrl+C. SIGINT to the child first; if it doesn't exit
        # promptly, force-close.
        if child is not None and child.isalive():
            try:
                child.sendintr()
                child.close(force=True)
            except Exception:
                pass
        renderer.handle_completion(130, "crashed")
        return 130
    finally:
        renderer.stop()


def _drive(
    child: pexpect.spawn,
    parser: PtyStreamParser,
    renderer: Renderer,
    timeout: float,
) -> int:
    """Read the PTY until EOF, feeding lines to the parser/renderer."""
    # We expect either a newline (terminating a complete line), EOF
    # (subprocess exited), TIMEOUT (no output for `timeout` seconds —
    # fine, just keep going), or one of the password-prompt patterns
    # (mid-line, no newline). The order matters only insofar as the
    # named-vault pattern must come before the bare vault pattern; both
    # are higher-specificity matches than the generic newline so pexpect
    # picks them when applicable.
    patterns: list[Any] = [r"\r?\n", pexpect.EOF, pexpect.TIMEOUT, *_PASSWORD_PATTERNS]
    newline_idx = 0
    eof_idx = 1
    timeout_idx = 2

    while True:
        try:
            idx = child.expect(patterns, timeout=timeout)
        except pexpect.exceptions.EOF:
            _flush_pending(child, parser, renderer)
            break

        if idx == newline_idx:
            line = (child.before or "") + (child.after or "")
            _feed(line, parser, renderer)
        elif idx == eof_idx:
            _flush_pending(child, parser, renderer)
            break
        elif idx == timeout_idx:
            # No output yet — perfectly normal during long-running tasks.
            # A future slice can wake the renderer here for elapsed-time
            # ticks; for now we just keep waiting.
            continue
        else:
            # Password prompt fired. Build the prompt text from the
            # pre-match content (which may contain prior plaintext we
            # haven't routed yet) and the matched prompt itself.
            prompt = (child.before or "") + (child.after or "")
            password = renderer.handle_password_prompt(prompt)
            child.sendline(password)

    child.close()
    return child.exitstatus if child.exitstatus is not None else (child.signalstatus or 1)


def _flush_pending(child: pexpect.spawn, parser: PtyStreamParser, renderer: Renderer) -> None:
    """Drain any final bytes left in the buffer when the subprocess ends.

    EOF often arrives without a trailing newline — pexpect leaves the last
    fragment in `child.before`. We treat it as a terminal line so its event,
    if any, still reaches the renderer.
    """
    leftover = child.before or ""
    if leftover.strip():
        _feed(leftover, parser, renderer)


def _feed(line: str, parser: PtyStreamParser, renderer: Renderer) -> None:
    """Feed one line to the parser and forward emitted events."""
    for event in parser.feed_line(line):
        renderer.update_state(event)
