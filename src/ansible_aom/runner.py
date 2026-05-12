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

import logging
import os
import re
import sys
from pathlib import Path
from typing import Any

import pexpect

from ansible_aom.core.models import WarningType
from ansible_aom.core.parser import _ANSI_SGR_RE, PtyStreamParser
from ansible_aom.core.preflight import run_preflight
from ansible_aom.core.session import SessionManager
from ansible_aom.renderer.protocol import Renderer

logger = logging.getLogger(__name__)


def _default_session_dir() -> Path:
    """Spec-standard location for live session directories.

    Mirrors the default that ``aom inspect`` falls back to so a run
    recorded here is immediately findable by ``aom inspect list`` /
    ``aom inspect show`` without any flag plumbing.
    """
    return Path.home() / ".local" / "state" / "aom" / "sessions"


class _NullSink:
    """No-op sink used when session recording is disabled (F3 --no-record).

    Has the same shape as ``_SessionSink`` so the runner's hot path is
    branchless once the sink is wired up. Methods accept the same args
    and silently discard them.
    """

    def record_event(self, event: dict) -> None:  # noqa: ARG002
        return None

    def record_stderr(self, line: str) -> None:  # noqa: ARG002
        return None

    def end(self, status: str) -> None:  # noqa: ARG002
        return None


class _SessionSink:
    """Best-effort wrapper around SessionManager for runtime recording.

    Disk errors at session start/write/end are swallowed and logged —
    recording is observability, not control flow. A run that can't open
    its session directory still completes normally; the inspect-side
    catches up next time.

    R3: on the *first* write OSError after a successful start (disk fills
    mid-run, NFS hiccup, quota exceeded), the sink disables itself —
    subsequent calls return immediately so a 1000-events/sec stream
    doesn't flood logs by retrying every event. The renderer gets a
    one-time warning so the user sees recording stopped even though the
    run kept going.
    """

    def __init__(
        self,
        session_dir: Path,
        playbook: str,
        ansible_args: list[str] | None = None,
        renderer: object | None = None,
    ) -> None:
        self._manager: SessionManager | None = None
        self._session_id: str | None = None
        self._renderer = renderer
        self._disabled = False
        try:
            session_dir.mkdir(parents=True, exist_ok=True)
            manager = SessionManager(session_dir=session_dir, playbook=playbook)
            self._session_id = manager.start_session(playbook, ansible_args=ansible_args or [])
            self._manager = manager
        except OSError as exc:
            logger.debug("session recording disabled (start failed): %s", exc)

    def _disable(self, reason: str) -> None:
        """Stop recording and emit a one-time warning to the renderer.

        Called from any write path that hits an OSError. After this, all
        record_* calls return early — both as a safety against repeated
        OSErrors on the same broken disk and to keep the runner's hot
        path branchless.
        """
        if self._disabled:
            return
        self._disabled = True
        if self._renderer is not None:
            add_warning = getattr(self._renderer, "add_warning", None)
            if callable(add_warning):
                add_warning(f"session recording disabled (disk write failed: {reason})", False)

    def record_event(self, event: dict) -> None:
        if self._disabled or self._manager is None or self._session_id is None:
            return
        try:
            self._manager.record_event(self._session_id, event)
        except OSError as exc:
            logger.debug("session event write failed: %s", exc)
            self._disable(str(exc))

    def record_stderr(self, line: str) -> None:
        if self._disabled or self._manager is None or self._session_id is None:
            return
        try:
            self._manager.record_stderr(self._session_id, line)
        except OSError as exc:
            logger.debug("session stderr write failed: %s", exc)
            self._disable(str(exc))

    def end(self, status: str) -> None:
        if self._disabled or self._manager is None or self._session_id is None:
            return
        try:
            self._manager.end_session(self._session_id, status)
        except OSError as exc:
            logger.debug("session end failed: %s", exc)


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

# High-confidence prompt markers. When any of these substrings appears in
# the unread buffer during a TIMEOUT branch, we're confident the child
# is blocked on stdin (`ansible.builtin.pause`, `vars_prompt`, common
# yes/no confirmations). The match is substring-based rather than a
# pexpect pattern because real prompts arrive mid-line and pexpect's
# regex match can fire before the full prompt has buffered.
_INTERACTIVE_PROMPT_MARKERS: tuple[str, ...] = (
    "[pause]",
    "Press Enter",
    "press enter",
    "(yes/no)",
    "(y/n)",
    "[y/N]",
    "[Y/n]",
    "[yes/no]",
)

# Number of consecutive TIMEOUTs (each `timeout` seconds) before stall
# detection flushes the unread buffer to the log so the user can at
# least see what was being held. Never blocks for input — see
# `.sisyphus/notepads/plans/interactive-prompts.md` for the rationale.
_STALL_FLUSH_TIMEOUTS: int = 6  # ~3s at the default 0.5s timeout

# Earlier hint: when the child has been silent with a non-empty buffer
# for this many consecutive timeouts, surface a one-time "[aom] waiting
# on output…" breadcrumb so the user knows AOM is alive and watching.
# Set strictly less than _STALL_FLUSH_TIMEOUTS so the hint always
# precedes the flush.
_STALL_HINT_TIMEOUTS: int = 4  # ~2s at the default 0.5s timeout

_DEFAULT_TIMEOUT_S = 0.5

# When set to a truthy value, write a per-loop trace of the runner's
# pexpect activity to stderr. Used to debug "AOM didn't see the
# prompt" reports — every TIMEOUT branch logs ``buffer=...
# before=... prior=...`` so we can tell whether pexpect is buffering
# the data, returning empty, or something else.
_TRACE_ENV_VAR = "AOM_TRACE"


def _trace_enabled() -> bool:
    return bool(os.environ.get(_TRACE_ENV_VAR))


def _trace(label: str, **fields: object) -> None:
    if not _trace_enabled():
        return
    parts = " ".join(f"{k}={v!r}" for k, v in fields.items())
    sys.stderr.write(f"[aom-trace] {label} {parts}\n")
    sys.stderr.flush()


_VARS_PROMPT_RE = re.compile(r"^\s*\[[^\]\n]+\]\s*(\([^)]*\))?\s*:\s*$", re.MULTILINE)

# Real ansible decorates the pause prompt with a bracketed task-name
# header on its own line, e.g. ``[Confirm deployment]\n<prompt>:``.
# Detect that as a strong "this is a pause prompt" signal regardless
# of the prompt text the user typed in their playbook.
_BRACKETED_HEADER_RE = re.compile(r"^\s*\[[^\]\n]+\]\s*$", re.MULTILINE)


def _strip_ansi(text: str) -> str:
    """Remove SGR escape sequences from `text`. Reuses the parser's regex."""
    return _ANSI_SGR_RE.sub("", text)


def _looks_like_interactive_prompt(pending: str, prior_plaintext: str | None = None) -> bool:
    """True if `pending` (unread PTY buffer) looks like a child waiting on stdin.

    High-confidence signals only:
    - non-empty
    - last non-whitespace char is ``:`` or ``?`` (the universal "prompt
      waiting" terminator)
    - AND one of:
        * contains a known marker (``[pause]``, ``Press Enter``,
          ``(yes/no)``, …)
        * ends in ``?`` (any question — strong signal)
        * matches the ``vars_prompt`` default ``[name]: `` /
          ``[name] (default): `` format
        * has a bracketed header on its own line above the prompt
          inside ``pending``
        * ``prior_plaintext`` (the most recently consumed plaintext
          line, ANSI-stripped) is a bracketed header on its own —
          real ansible pause emits the header and the prompt on
          separate lines, and the header is consumed by the
          newline-matcher before the prompt's TIMEOUT fires.

    ANSI SGR escape sequences are stripped before any of these checks.
    ansible colorises the pause prompt by default, so the raw buffer
    often ends in ``\\x1b[0m`` (a reset code) rather than the
    visible ``:``.

    False positives still possible (e.g. a debug task ending in
    ``Installing packages:``) but rare; the cost is one spurious
    newline sent to the child, which is harmless when no module is
    reading from stdin. Pure trailing-``:`` without any other signal
    is intentionally rejected — it's too common in regular log lines.
    """
    clean = _strip_ansi(pending)
    text = clean.rstrip()
    if not text:
        return False
    last_char = text[-1]
    if last_char not in (":", "?"):
        return False
    if last_char == "?":
        return True
    if any(marker in clean for marker in _INTERACTIVE_PROMPT_MARKERS):
        return True
    # vars_prompt default: the last line is ``[varname]: `` or
    # ``[varname] (default): ``. Anchor to MULTILINE start so log
    # lines that happen to contain ``[FOO]`` later don't trip it.
    last_line = clean.splitlines()[-1] if "\n" in clean else clean
    if _VARS_PROMPT_RE.match(last_line):
        return True
    # Real ansible pause output: a ``[Task name]`` header line.
    # Either above the prompt inside the same buffer, OR consumed
    # earlier as a separate plaintext line (newline-terminated, so
    # pexpect routed it through ``_feed`` before TIMEOUT fired).
    if _BRACKETED_HEADER_RE.search(clean):
        return True
    if prior_plaintext is not None:
        prior_clean = _strip_ansi(prior_plaintext).strip()
        if _BRACKETED_HEADER_RE.fullmatch(prior_clean):
            return True
    return False


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
    session_dir: Path | None = None,
    record: bool = True,
) -> int:
    """Run a playbook through the renderer; return the subprocess exit code.

    The renderer's lifecycle is fully owned here: `start` is called before
    the spawn, `handle_completion` after the subprocess exits (or fails to
    start), and `stop` always runs in a finally block.

    Session recording writes a new directory under ``session_dir`` (or
    the spec default ``~/.local/state/aom/sessions/`` when None) so
    ``aom inspect`` can replay the run. Recording is best-effort —
    disk errors are logged but never abort the run. Pass ``record=False``
    to disable session recording entirely (F3 --no-record).
    """
    executable, args = _build_command(playbook, ansible_args)
    env = os.environ.copy()
    env["ANSIBLE_STDOUT_CALLBACK"] = "ansible.posix.jsonl"

    parser = PtyStreamParser()
    renderer.start(playbook, ansible_args)

    sink: _SessionSink | _NullSink
    if record:
        sink = _SessionSink(
            session_dir or _default_session_dir(),
            playbook,
            ansible_args=ansible_args,
            renderer=renderer,
        )
    else:
        sink = _NullSink()

    # Preflight: --list-tasks + --list-hosts in parallel before spawning
    # the JSONL run so the renderer can show plays/tasks/host count from
    # the very first frame. Failures are non-fatal — surfaced as warnings.
    pre_result = run_preflight(playbook=playbook, ansible_args=ansible_args)
    renderer.set_definitions(pre_result.definitions)
    # add_warning prints the message above the panel AND bumps the counter.
    # The renderer's own dedupe handles repeats so it's safe to forward
    # every error here without extra filtering.
    for err in pre_result.errors:
        renderer.add_warning(err, False)
        sink.record_stderr(err)

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
            sink.end("crashed")
            renderer.handle_completion(127, "crashed")
            return 127

        exit_code = _drive(child, parser, renderer, timeout, sink)
        state = "completed" if exit_code == 0 else "failed"
        sink.end(state)
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
        sink.end("crashed")
        renderer.handle_completion(130, "crashed")
        return 130
    finally:
        renderer.stop()


def _drive(
    child: pexpect.spawn,
    parser: PtyStreamParser,
    renderer: Renderer,
    timeout: float,
    sink: _SessionSink | _NullSink,
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

    # Stall tracking: count consecutive TIMEOUTs where the child has
    # produced no newline-terminated output. Used both for the
    # high-confidence prompt path (input forwarded) and the low-confidence
    # safety-net (flush-only, never blocks).
    stall_count = 0

    while True:
        try:
            idx = child.expect(patterns, timeout=timeout)
        except pexpect.exceptions.EOF:
            _flush_pending(child, parser, renderer, sink)
            break

        if idx == newline_idx:
            line = (child.before or "") + (child.after or "")
            _trace("newline", line=line[:200])
            _feed(line, parser, renderer, sink)
            # Reset to 0 (not max(stall_count, 0)) — a newline always
            # ends a silent window, including the "already-handled"
            # window marked by negative stall_count.
            stall_count = 0
        elif idx == eof_idx:
            _trace("eof", leftover=(child.before or "")[:200])
            _flush_pending(child, parser, renderer, sink)
            break
        elif idx == timeout_idx:
            # The parser's plaintext_lines accumulates every non-JSONL,
            # non-warning line that's gone through `_feed`. The last
            # entry is our window into "what did the child say right
            # before going quiet?" — which lets us catch the case
            # where ansible emits ``[Task name]\n<prompt>:`` and the
            # header line was already consumed before the prompt's
            # TIMEOUT fired.
            prior = parser.plaintext_lines[-1] if parser.plaintext_lines else None
            _trace(
                "timeout",
                stall_count=stall_count,
                buffer=(getattr(child, "buffer", "") or "")[:200],
                before=(getattr(child, "before", "") or "")[:200],
                prior=(prior or "")[:120],
            )
            stall_count = _handle_timeout_branch(child, renderer, sink, stall_count, prior)
            continue
        else:
            # Password prompt fired. Build the prompt text from the
            # pre-match content (which may contain prior plaintext we
            # haven't routed yet) and the matched prompt itself.
            prompt = (child.before or "") + (child.after or "")
            _trace("password-pattern", prompt=prompt[:200])
            password = renderer.handle_password_prompt(prompt)
            child.sendline(password)
            stall_count = 0

    child.close()
    return child.exitstatus if child.exitstatus is not None else (child.signalstatus or 1)


def _peek_unread(child: pexpect.spawn) -> str:
    """Return the unread PTY buffer without consuming it.

    pexpect's ``buffer`` property holds whatever was read but didn't
    match any pattern in the most recent ``expect()`` call. For a
    newline-terminated stream the buffer is empty between events; for
    a stalled child waiting on stdin the buffer holds the prompt text.
    """
    return getattr(child, "buffer", "") or ""


def _consume_unread(child: pexpect.spawn) -> str:
    """Read and clear the unread buffer; return whatever was there."""
    pending = _peek_unread(child)
    if pending:
        # Setting buffer through the property clears it (pexpect uses a
        # StringIO internally; the setter replaces it with a fresh one).
        try:
            child.buffer = ""
        except Exception:
            # Defensive: some pexpect versions/spawn variants don't
            # support direct buffer assignment. Fall back to a
            # read_nonblocking drain.
            try:
                child.read_nonblocking(size=len(pending), timeout=0)
            except Exception:
                pass
    return pending


def _fire_prompt(
    child: pexpect.spawn,
    renderer: Renderer,
    sink: _SessionSink | _NullSink,
    prompt_text: str,
    prior_plaintext: str | None,
) -> None:
    """Route a captured prompt through the renderer and forward the answer.

    Shared between the two detection paths (buffer-pending vs
    prior-line). The renderer's ``handle_interactive_prompt`` is the
    user-facing suspend/input/restart dance; we just pump the result
    into the child via ``sendline`` and mirror both prompt and answer
    into the session sink so ``aom inspect show`` can replay it.

    A renderer crash here is fatal to the child's progress (it stays
    blocked on stdin) — best-effort: send an empty line so pause
    accepts "continue" rather than leaving the run wedged.
    """
    renderer.print_log("[aom] detected interactive prompt — respond below:")
    logger.debug(
        "interactive prompt detected (len=%d, prior=%r)",
        len(prompt_text),
        (prior_plaintext or "")[:80],
    )
    try:
        answer = renderer.handle_interactive_prompt(prompt_text)
    except Exception:
        answer = ""
    child.sendline(answer)
    sink.record_stderr(prompt_text.rstrip())
    sink.record_stderr(f"[user-input] {answer}")


def _handle_timeout_branch(
    child: pexpect.spawn,
    renderer: Renderer,
    sink: _SessionSink | _NullSink,
    stall_count: int,
    prior_plaintext: str | None = None,
) -> int:
    """Handle a TIMEOUT in `_drive`. Return the new ``stall_count``.

    Three cases, in priority order:

    1. **High-confidence prompt.** Unread buffer looks like the child
       is blocked on stdin (ends in ``:`` or ``?``, contains a known
       marker, or the immediately-prior plaintext line was a
       ``[Task name]`` header). Drain the buffer, route through
       ``renderer.handle_interactive_prompt``, forward the answer via
       ``child.sendline``. Reset stall count.
    2. **Stall safety net.** Unread buffer has been pending for
       ``_STALL_FLUSH_TIMEOUTS`` consecutive timeouts. We *don't* know
       it's a prompt, so we never block — instead flush the content as
       a log line so the user can at least see what's stuck. Reset stall
       count so we don't keep re-flushing the same text.
    3. **Quiet.** No unread buffer — the child is just slow. Tick the
       renderer's clock and keep waiting.

    The split exists because blocking input on a false-positive (a
    genuine slow task) would lock up the run while the user wonders
    what happened. Flushing alone is recoverable: if output eventually
    arrives it just appears underneath.
    """
    # Sentinel: stall_count<0 means "this silent window already had a
    # prompt fired; don't re-fire". Resets to 0 in the caller when a
    # newline arrives (the child responded to our sendline).
    if stall_count < 0:
        renderer.tick()
        return stall_count

    # `child.buffer` is the documented unread accumulator. In some
    # pexpect builds or weird timing windows the data lands in
    # `child.before` instead (it's the "what was read before this
    # match" field), so fall back when buffer is empty.
    pending = _peek_unread(child) or (getattr(child, "before", "") or "")

    # Case 1: pending content directly looks like a prompt (no trailing
    # newline so pexpect couldn't consume it via the newline matcher).
    if pending and _looks_like_interactive_prompt(pending, prior_plaintext):
        prompt_text = _consume_unread(child) or pending
        _fire_prompt(child, renderer, sink, prompt_text, prior_plaintext)
        return -1

    # Case 2: the prompt itself was newline-terminated and consumed by
    # the newline matcher, so the unread buffer is empty even though
    # the child is now blocked on stdin. Real ansible.builtin.pause
    # does this — observed live: each prompt line ends in ``:\r\n``.
    # When the most recently consumed plaintext line looks like a
    # prompt and the child has gone silent, treat that line as the
    # captured prompt.
    if not pending and prior_plaintext and _looks_like_interactive_prompt(prior_plaintext):
        _fire_prompt(child, renderer, sink, prior_plaintext, prior_plaintext)
        return -1

    if pending:
        stall_count += 1
        # One-time "waiting" hint before the actual flush so the user
        # knows AOM is alive, not just silently spinning.
        if stall_count == _STALL_HINT_TIMEOUTS:
            renderer.print_log(
                f"[aom] waiting on ansible-playbook output ({len(pending)} bytes held)…"
            )
        if stall_count >= _STALL_FLUSH_TIMEOUTS:
            # Flush-only: surface the held content so the user sees
            # *something*. Never block.
            flushed = _consume_unread(child) or pending
            renderer.print_log("[aom] flushing held output (heuristic didn't recognise as prompt):")
            for line in flushed.splitlines():
                if line.strip():
                    renderer.print_log(line)
                    sink.record_stderr(line)
            stall_count = 0

    renderer.tick()
    return stall_count


def _flush_pending(
    child: pexpect.spawn,
    parser: PtyStreamParser,
    renderer: Renderer,
    sink: _SessionSink | _NullSink,
) -> None:
    """Drain any final bytes left in the buffer when the subprocess ends.

    EOF often arrives without a trailing newline — pexpect leaves the last
    fragment in `child.before`. We treat it as a terminal line so its event,
    if any, still reaches the renderer.
    """
    leftover = child.before or ""
    if leftover.strip():
        _feed(leftover, parser, renderer, sink)


def _feed(
    line: str, parser: PtyStreamParser, renderer: Renderer, sink: _SessionSink | _NullSink
) -> None:
    """Feed one line to the parser and forward emitted events + warnings.

    Warnings (`[WARNING]:` / `[DEPRECATION WARNING]:` lines from ansible)
    are detected by the parser's plaintext path but never reach the
    renderer through the JSONL event flow — drain them and forward via
    `add_warning` (renderers without a visible warning surface implement
    it as a no-op).

    Each parsed event is mirrored to the session sink so a later
    ``aom inspect show`` can replay the exact JSONL the run saw.
    """
    for event in parser.feed_line(line):
        sink.record_event(event)
        renderer.update_state(event)

    for warning in parser.drain_warnings():
        sink.record_stderr(warning.message)
        renderer.add_warning(warning.message, warning.type == WarningType.DEPRECATION)
