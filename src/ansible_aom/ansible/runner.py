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
import sys
import time
from pathlib import Path
from typing import Any

import pexpect

from ansible_aom.ansible.preflight import run_preflight
from ansible_aom.core import diagnostics
from ansible_aom.core.models import WarningType, count_leaf_tasks
from ansible_aom.core.parser import PtyStreamParser
from ansible_aom.core.run_config import build_run_config_key
from ansible_aom.renderer.protocol import Renderer
from ansible_aom.session.history import find_previous_run
from ansible_aom.session.store import SessionManager

logger = logging.getLogger(__name__)


def _default_session_dir() -> Path:
    """Spec-standard location for live session directories.

    Mirrors the default that ``aom inspect`` falls back to so a run
    recorded here is immediately findable by ``aom inspect list`` /
    ``aom inspect show`` without any flag plumbing.
    """
    return Path.home() / ".local" / "state" / "aom" / "sessions"


def _print_session_footer(*, session_id: str | None, stderr_isatty: bool) -> None:
    """Print the end-of-run hint that points users at ``aom inspect``.

    Suppressed in two cases:
    - The runner had no session (recording disabled or failed to start).
    - stderr is not a TTY (CI, pipe, redirect) — keeps script output clean.
    """
    if not session_id or not stderr_isatty:
        return
    short = session_id[:8]
    sys.stderr.write(f"\nSession {short}   aom inspect\n")
    sys.stderr.flush()


class _NullSink:
    """No-op sink used when session recording is disabled (F3 --no-record).

    Has the same shape as ``_SessionSink`` so the runner's hot path is
    branchless once the sink is wired up. Methods accept the same args
    and silently discard them.
    """

    @property
    def session_id(self) -> str | None:
        return None

    def record_event(self, event: dict) -> None:  # noqa: ARG002
        return None

    def record_stderr(self, line: str) -> None:  # noqa: ARG002
        return None

    def end(
        self,
        status: str,  # noqa: ARG002
        *,
        preflight_task_count: int | None = None,  # noqa: ARG002
        resolved_host_count: int | None = None,  # noqa: ARG002
    ) -> None:
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
        diagnostics.set_session_recording_disabled(reason)
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

    def end(
        self,
        status: str,
        *,
        preflight_task_count: int | None = None,
        resolved_host_count: int | None = None,
    ) -> None:
        if self._disabled or self._manager is None or self._session_id is None:
            return
        try:
            self._manager.end_session(
                self._session_id,
                status,
                preflight_task_count=preflight_task_count,
                resolved_host_count=resolved_host_count,
            )
        except OSError as exc:
            logger.debug("session end failed: %s", exc)

    @property
    def session_id(self) -> str | None:
        return self._session_id


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
    # sudo pass-through: fires when a module shells out to ``sudo``
    # (e.g. a formula's post-install hooks). Order from most-specific
    # to least so pexpect's first-match-wins semantics give bracketed
    # and user-qualified forms priority over bare ``Password: ``.
    r"\[sudo\] password for [^:\n]+: ",
    r"Password for [^:\n]+: ",
    r"Password: ",
]

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

# Per-loop pexpect trace toggle. Reads through ``core.diagnostics`` so
# ``AOM_TRACE_PEXPECT=1`` (new canonical) and ``AOM_TRACE=1`` (legacy
# alias, kept for one release) flow through one decision point. Used to
# debug "AOM didn't see the prompt" reports — every TIMEOUT branch logs
# ``buffer=... before=... prior=...``.


def _trace_enabled() -> bool:
    from ansible_aom.core import diagnostics

    return diagnostics.is_trace_pexpect()


def _trace(label: str, **fields: object) -> None:
    if not _trace_enabled():
        return
    parts = " ".join(f"{k}={v!r}" for k, v in fields.items())
    sys.stderr.write(f"[aom-trace] {label} {parts}\n")
    sys.stderr.flush()


# The pure prompt-detection heuristic lives in core/prompts.py. Re-exported
# under its historical underscore-prefixed name so existing tests that
# patch / import from this module keep working unchanged.
from ansible_aom.core.prompts import looks_like_interactive_prompt as _looks_like_interactive_prompt


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
    diag = diagnostics.RunDiagnostics()
    diagnostics.set_last_run_diagnostics(diag)

    executable, args = _build_command(playbook, ansible_args)
    env = os.environ.copy()
    env["ANSIBLE_STDOUT_CALLBACK"] = "ansible.posix.jsonl"

    parser = PtyStreamParser()
    renderer.start(playbook, ansible_args)

    # Resolve once so the sink and the history lookup can never see
    # different directories — and so a future env-var-driven default
    # would land consistently in both places.
    resolved_session_dir = session_dir or _default_session_dir()

    sink: _SessionSink | _NullSink
    if record:
        sink = _SessionSink(
            resolved_session_dir,
            playbook,
            ansible_args=ansible_args,
            renderer=renderer,
        )
    else:
        sink = _NullSink()

    # Preflight: --list-tasks + --list-hosts in parallel before spawning
    # the JSONL run so the renderer can show plays/tasks/host count from
    # the very first frame. Failures are non-fatal — surfaced as warnings.
    diagnostics.lifecycle_mark("preflight_start")
    _preflight_t0 = time.monotonic_ns()
    pre_result = run_preflight(playbook=playbook, ansible_args=ansible_args)
    diag.note_preflight_elapsed_ms((time.monotonic_ns() - _preflight_t0) // 1_000_000)
    diagnostics.lifecycle_mark("preflight_end")

    # Union of resolved hosts across plays — preflight is best-effort,
    # so a play with no resolved_hosts simply contributes nothing.
    resolved_host_count = len(
        {host for play in pre_result.definitions for host in play.resolved_hosts}
    )
    preflight_task_count = count_leaf_tasks(pre_result.definitions)

    # Look up a matching prior completed run (same run-config + host
    # count) so the compact renderer can surface "Last run: N tasks in T".
    # Must be pushed BEFORE ``set_definitions`` so the hint is part of
    # the one-shot startup summary the compact renderer prints there.
    key = build_run_config_key(playbook=playbook, ansible_args=ansible_args)
    prior = find_previous_run(resolved_session_dir, key, host_count=resolved_host_count)
    renderer.set_prior_run(prior)
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
            sink.end(
                "crashed",
                preflight_task_count=preflight_task_count,
                resolved_host_count=resolved_host_count,
            )
            renderer.handle_completion(127, "crashed")
            return 127
        diagnostics.lifecycle_mark("spawn")

        profiler = diagnostics.get_profiler()
        if profiler is not None:
            profiler.enable()
        try:
            exit_code = _drive(child, parser, renderer, timeout, sink, diag=diag)
        finally:
            if profiler is not None:
                profiler.disable()
        diagnostics.lifecycle_mark("last_event")
        diagnostics.record_tracemalloc_peak()
        state = "completed" if exit_code == 0 else "failed"
        sink.end(
            state,
            preflight_task_count=preflight_task_count,
            resolved_host_count=resolved_host_count,
        )
        renderer.handle_completion(exit_code, state)
        diagnostics.lifecycle_mark("completion")
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
        sink.end(
            "crashed",
            preflight_task_count=preflight_task_count,
            resolved_host_count=resolved_host_count,
        )
        renderer.handle_completion(130, "crashed")
        return 130
    finally:
        renderer.stop()
        try:
            stderr_tty = sys.stderr.isatty()
        except AttributeError, ValueError:
            stderr_tty = False
        _print_session_footer(
            session_id=getattr(sink, "session_id", None),
            stderr_isatty=stderr_tty,
        )


def _drive(
    child: pexpect.spawn,
    parser: PtyStreamParser,
    renderer: Renderer,
    timeout: float,
    sink: _SessionSink | _NullSink,
    *,
    diag: diagnostics.RunDiagnostics | None = None,
) -> int:
    """Read the PTY until EOF, feeding lines to the parser/renderer.

    ``diag`` is the optional run-scoped diagnostics accumulator. When
    supplied (which ``run_playbook`` always does in production), it
    receives per-event histogram bumps from ``_feed`` and TIMEOUT /
    stall counters from this loop. Passing ``None`` is a no-op path
    kept for legacy callers and unit tests that don't care about
    instrumentation.
    """
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

    # CPU sampler cadence: every Nth consecutive TIMEOUT we poll psutil
    # and feed the renderer's heartbeat so it can distinguish "quiet
    # but the brew install is still working" from "actually stuck".
    # Cadence chosen so a 0.5s expect-timeout polls roughly every 2s.
    cpu_sample_every = max(1, int(2.0 / max(timeout, 0.05)))
    timeout_count = 0

    while True:
        try:
            idx = child.expect(patterns, timeout=timeout)
        except pexpect.exceptions.EOF:
            _flush_pending(child, parser, renderer, sink)
            break

        if idx == newline_idx:
            line = (child.before or "") + (child.after or "")
            _trace("newline", line=line[:200])
            _feed(line, parser, renderer, sink, diag=diag)
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
            if diag is not None:
                diag.note_timeout()
                diag.note_stall(stall_count if stall_count > 0 else 0)
            timeout_count += 1
            if timeout_count >= cpu_sample_every:
                renderer.note_subprocess_active(_sample_subprocess_active(child.pid))
                timeout_count = 0
            continue
        else:
            # Password prompt fired. Build the prompt text from the
            # pre-match content (which may contain prior plaintext we
            # haven't routed yet) and the matched prompt itself.
            prompt = (child.before or "") + (child.after or "")
            _trace("password-pattern", prompt=prompt[:200])
            renderer.note_pty_bytes()
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
    line: str,
    parser: PtyStreamParser,
    renderer: Renderer,
    sink: _SessionSink | _NullSink,
    *,
    diag: diagnostics.RunDiagnostics | None = None,
) -> None:
    """Feed one line to the parser and forward emitted events + warnings.

    Warnings (`[WARNING]:` / `[DEPRECATION WARNING]:` lines from ansible)
    are detected by the parser's plaintext path but never reach the
    renderer through the JSONL event flow — drain them and forward via
    `add_warning` (renderers without a visible warning surface implement
    it as a no-op).

    Each parsed event is mirrored to the session sink so a later
    ``aom inspect show`` can replay the exact JSONL the run saw.

    The line itself counts as a liveness signal — ``note_pty_bytes``
    runs unconditionally so any task (including a silent long-running
    one like ``community.general.homebrew`` looping over many
    formulae) keeps the heartbeat tracker in a defined state from
    its very first ``task_start`` event onwards.

    When ``diag`` is supplied, it receives ``note_pty_bytes(len(line))``
    plus a ``note_event`` per parsed JSONL event — that's how the
    diagnostics histogram is built (also fires the ``first_event``
    lifecycle mark on the first call).
    """
    renderer.note_pty_bytes()
    if diag is not None:
        diag.note_pty_bytes(len(line))

    trace_events = diagnostics.is_trace_events()
    for event in parser.feed_line(line):
        sink.record_event(event)
        renderer.update_state(event)
        if diag is not None:
            event_type = event.get("_event", "<unknown>")
            diag.note_event(event_type)
            if trace_events and diag.events_received % 100 == 0:
                sys.stderr.write(
                    f"[aom-trace-events] count={diag.events_received} type={event_type}\n"
                )
                sys.stderr.flush()

    for warning in parser.drain_warnings():
        sink.record_stderr(warning.message)
        renderer.add_warning(warning.message, warning.type == WarningType.DEPRECATION)


def _sample_subprocess_active(pid: int) -> bool:
    """Return True if pid or any descendant used CPU since the last call.

    Uses psutil.cpu_percent with ``interval=None`` — non-blocking, returns
    the delta since the previous call on the same Process. The runner
    is expected to cache a single Process object across calls so the
    delta is meaningful; here we keep it self-contained by caching by
    pid at module scope.

    Any psutil error (process exited, permission denied, missing
    descendant) degrades to False rather than propagating — the
    heartbeat still works on byte signal alone.
    """
    try:
        import psutil
    except ImportError:
        return False

    cache = _PSUTIL_CACHE
    try:
        proc = cache.get(pid)
        if proc is None or not proc.is_running():
            proc = psutil.Process(pid)
            cache[pid] = proc
            # Seed cpu_percent so the next call has a delta baseline.
            proc.cpu_percent(interval=None)
            return False

        any_active = bool(proc.cpu_percent(interval=None) > 0.0)
        if not any_active:
            for child in proc.children(recursive=True):
                try:
                    if child.cpu_percent(interval=None) > 0.0:
                        any_active = True
                        break
                except psutil.Error:
                    continue
        return any_active
    except psutil.Error:
        cache.pop(pid, None)
        return False
    except Exception:
        return False


_PSUTIL_CACHE: dict[int, Any] = {}
