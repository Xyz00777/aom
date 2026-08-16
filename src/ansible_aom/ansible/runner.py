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
from concurrent.futures import Future, ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from os import _Environ

import pexpect

from ansible_aom.ansible.preflight import run_preflight
from ansible_aom.core import diagnostics
from ansible_aom.core.event_types import JsonlEvent
from ansible_aom.core.models import WarningType
from ansible_aom.core.parser import PreParseResult, PtyStreamParser, StreamPhase

# Re-exported under their historical underscore-prefixed names so existing
# tests that patch / import them from this module keep working unchanged.
from ansible_aom.core.prompts import (
    looks_like_interactive_prompt as _looks_like_interactive_prompt,
)
from ansible_aom.core.prompts import (
    reconstruct_pause_prompt as _reconstruct_pause_prompt,
)
from ansible_aom.core.run_config import build_run_config_key
from ansible_aom.core.run_state import RunState, count_leaf_tasks
from ansible_aom.renderer.protocol import Renderer
from ansible_aom.session.history import find_previous_run
from ansible_aom.session.store import SessionManager

logger = logging.getLogger(__name__)


class _AsyncPreflight:
    """Manages asynchronous background execution of preflight."""

    def __init__(self, future: Future[PreParseResult], preflight_t0: int) -> None:
        self.future = future
        self.preflight_t0 = preflight_t0
        self.applied = False
        self.result: PreParseResult | None = None
        self.resolved_host_count: int = 0
        self.preflight_task_count: int = 0

    def apply(
        self,
        state: RunState,
        renderer: Renderer,
        sink: _SessionSink | _NullSink,
        diag: diagnostics.RunDiagnostics | None = None,
    ) -> None:
        if self.applied:
            return
        self.applied = True
        try:
            self.result = self.future.result()
        except Exception as exc:
            logger.warning("Background preflight failed: %s", exc)
            self.result = PreParseResult(
                plays=[],
                play_hosts=[],
                definitions=[],
                errors=[f"preflight error: {exc}"],
                include_cache={},
            )

        diagnostics.lifecycle_mark("preflight_end")
        if diag is not None:
            diag.note_preflight_elapsed_ms((time.monotonic_ns() - self.preflight_t0) // 1_000_000)

        self.resolved_host_count = len(
            {host for play in self.result.definitions for host in play.resolved_hosts}
        )
        self.preflight_task_count = count_leaf_tasks(self.result.definitions)

        # Update renderer and state definitions
        renderer.set_definitions(self.result.definitions)

        for err in self.result.errors:
            renderer.add_warning(err, False)
            sink.record_stderr(err)


def _bundled_callback_dir() -> Path | None:
    """Resolve the directory holding AOM's bundled ``aom_jsonl`` callback.

    Returns the ``callback/`` package data dir when it exists and contains
    the plugin, else None so the caller can fall back to the upstream
    ``ansible.posix.jsonl`` callback rather than break the run.
    """
    callback_dir = Path(__file__).resolve().parent / "callback"
    if (callback_dir / "aom_jsonl.py").is_file():
        return callback_dir
    return None


def _bundled_connection_callback_dir() -> Path | None:
    """Resolve the directory holding AOM's bundled ``aom_connection`` callback.

    This is the notification-type callback that emits
    ``aom_connection_acquired``/``aom_connection_released`` JSONL events
    for the parser's connection-id map. It lives in a separate package
    (``ansible_aom/callbacks/``) so the connection-tracking surface can
    evolve independently of the stdout-callback (``ansible_aom/ansible/
    callback/``) surface.

    Returns the dir when it exists and contains the plugin file, else
    None. A missing connection callback is non-fatal — the run just
    loses per-host connection-id attribution, which is observability,
    not control flow. ANSIBLE's default plugin search path is used as
    the fallback in that case.
    """
    callbacks_pkg = Path(__file__).resolve().parent.parent / "callbacks"
    if (callbacks_pkg / "aom_connection.py").is_file():
        return callbacks_pkg
    return None


def _callback_env() -> dict[str, str]:
    """Return the env overrides that select AOM's stdout callback.

    Prefers the bundled ``aom_jsonl`` plugin (which streams per-item loop
    events live); falls back to ``ansible.posix.jsonl`` when the bundled
    dir can't be resolved, so a packaging glitch costs only live item
    streaming — never the whole run.

    Also includes the bundled ``aom_connection`` notification callback
    in ``ANSIBLE_CALLBACK_PLUGINS`` so the connection-tracking plugin
    loads automatically — no user-visible flag. The connection-callback
    dir is listed first in the search path so its plugin resolves
    before the upstream ones (avoids any future name collision).
    """
    stdout_dir = _bundled_callback_dir()
    conn_dir = _bundled_connection_callback_dir()

    # Build the plugin search path. Connection-callback dir is listed
    # first so it resolves before any upstream plugin with the same
    # short name (defensive; today there is no such collision).
    plugin_dirs: list[Path] = []
    if conn_dir is not None:
        plugin_dirs.append(conn_dir)
    if stdout_dir is not None:
        plugin_dirs.append(stdout_dir)

    env: dict[str, str] = {}
    if plugin_dirs:
        env["ANSIBLE_CALLBACK_PLUGINS"] = os.pathsep.join(str(d) for d in plugin_dirs)

    if stdout_dir is not None:
        env["ANSIBLE_STDOUT_CALLBACK"] = "aom_jsonl"
    else:
        env["ANSIBLE_STDOUT_CALLBACK"] = "ansible.posix.jsonl"

    return env


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

    def record_event(self, event: JsonlEvent) -> None:  # noqa: ARG002
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

    def record_event(self, event: JsonlEvent) -> None:
        if self._disabled or self._manager is None or self._session_id is None:
            return
        try:
            self._manager.record_event(self._session_id, cast(dict[str, Any], event))
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
        # The async writer can only report a disk failure after the fact
        # (record_event never blocks on the write). Surface it now so the
        # user still gets the one-time "recording disabled" warning.
        reason = self._manager.recording_failed(self._session_id)
        if reason is not None:
            self._disable(reason)

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

# R8: after ``v2_playbook_on_stats`` has been consumed, the wait for
# EOF is bounded by this many seconds. If EOF doesn't fire within the
# window we log a warning and treat it as a synthetic EOF so a child
# that forgot to close its PTY (rare, but seen with become_user nested
# forks) can't hang the run forever.
_EOF_WATCHDOG_S: float = 30.0

# R11: tighter EOF watchdog once the runner has both consumed the final
# stats event AND observed the parser's ``end_time`` to be set. 5 s is
# long enough to absorb the typical post-stats cleanup tail (stragglers
# draining buffers, become forks unwinding) without paying the full 30 s
# when the child actually went idle and forgot to close its PTY.
_EOF_WATCHDOG_S_QUIET: float = 5.0

# R9: bound pexpect's internal search window so a single multi-MB JSONL
# event can't blow up pexpect's StringIO.  pexpect retains the entire
# incoming buffer when ``searchwindowsize=None`` (``expect.py``: ``copy
# the whole buffer (really slow for large datasets)``); with the default
# a ``debug: var=huge_object`` line keeps growing the StringIO until
# the terminating ``\n`` arrives.  512 bytes covers every pattern in
# ``_drive``'s pattern list (longest is ``[sudo] password for ...``,
# well under 100 chars) while bounding pexpect's per-call buffer.
_SEARCH_WINDOW_BYTES: int = 512

# Per-loop pexpect trace toggle. Now folded into ``AOM_DEBUG`` — one
# diagnostic knob instead of three. Used to debug "AOM didn't see the
# prompt" reports — every TIMEOUT branch logs
# ``buffer=... before=... prior=...``.


def _trace_enabled() -> bool:
    from ansible_aom.core import diagnostics

    return diagnostics.is_debug()


def _trace(label: str, **fields: object) -> None:
    if not _trace_enabled():
        return
    parts = " ".join(f"{k}={v!r}" for k, v in fields.items())
    sys.stderr.write(f"[aom-trace] {label} {parts}\n")
    sys.stderr.flush()


# The pure prompt-detection heuristics live in core/prompts.py; they're
# imported (with their historical underscore aliases) at the top of this
# module so the runner can call them in the hot PTY loop.


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
    env.update(_callback_env())

    parser = PtyStreamParser()
    state = RunState(playbook=playbook)
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

    # Preflight: spawn in background thread so large playbooks don't delay
    # ansible-playbook spawn. If preflight completes within the 200ms grace
    # window, apply immediately before spawn. Otherwise, apply dynamically
    # mid-run the moment the background worker finishes.
    diagnostics.lifecycle_mark("preflight_start")
    _preflight_t0 = time.monotonic_ns()

    preflight_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="aom-preflight")
    preflight_future = preflight_executor.submit(
        run_preflight,
        playbook=playbook,
        ansible_args=ansible_args,
    )
    async_preflight = _AsyncPreflight(preflight_future, _preflight_t0)

    try:
        preflight_future.result(timeout=0.2)
        async_preflight.apply(state, renderer, sink, diag=diag)
    except FutureTimeoutError, TimeoutError:
        pass
    except Exception:
        async_preflight.apply(state, renderer, sink, diag=diag)

    # Look up a matching prior completed run (same run-config + host
    # count) so the compact renderer can surface "Last run: N tasks in T".
    key = build_run_config_key(playbook=playbook, ansible_args=ansible_args)
    prior = find_previous_run(
        resolved_session_dir, key, host_count=async_preflight.resolved_host_count
    )
    renderer.set_prior_run(prior)

    child: pexpect.spawn | None = None
    try:
        try:
            # R6: ``codec_errors="surrogateescape"`` so any invalid UTF-8 byte
            # in the PTY stream becomes a lone surrogate codepoint in ``str``,
            # and ``str.encode("utf-8", "surrogateescape")`` later round-trips
            # the byte back losslessly. The on-disk ``events.jsonl`` therefore
            # contains the original payload bytes (``aom inspect show`` can
            # dump them verbatim). The renderer, in turn, decodes those
            # surrogate codepoints back to bytes and re-encodes with
            # ``errors="replace"`` before display so the user never sees a
            # bare surrogate — only ``?`` for non-displayable bytes.
            child = pexpect.spawn(
                executable,
                args=args,
                env=cast("_Environ[str]", env),
                encoding="utf-8",
                codec_errors="surrogateescape",
                timeout=timeout,
                searchwindowsize=_SEARCH_WINDOW_BYTES,
            )
        except pexpect.exceptions.ExceptionPexpect, FileNotFoundError, OSError:
            # Command not found / not executable — surface as 127.
            sink.end(
                "crashed",
                preflight_task_count=async_preflight.preflight_task_count,
                resolved_host_count=async_preflight.resolved_host_count,
            )
            renderer.handle_completion(127, "crashed")
            return 127

        diagnostics.lifecycle_mark("spawn")

        profiler = diagnostics.get_profiler()
        if profiler is not None:
            profiler.enable()
        # Pre-declare so the KeyboardInterrupt handler below can read the
        # child's real exit code if the race window between ``_drive``
        # returning and ``run_playbook`` returning lands SIGINT here.
        exit_code: int | None = None
        try:
            exit_code = _drive(
                child,
                parser,
                state,
                renderer,
                timeout,
                sink,
                async_preflight=async_preflight,
                diag=diag,
            )
        finally:
            if profiler is not None:
                profiler.disable()
        diagnostics.lifecycle_mark("last_event")
        diagnostics.record_tracemalloc_peak()
        final_status = "completed" if exit_code == 0 else "failed"
        sink.end(
            final_status,
            preflight_task_count=async_preflight.preflight_task_count,
            resolved_host_count=async_preflight.resolved_host_count,
        )
        renderer.handle_completion(exit_code, final_status)
        diagnostics.lifecycle_mark("completion")
        return exit_code

    except KeyboardInterrupt:
        # User hit Ctrl+C. SIGINT to the child first; if it doesn't exit
        # promptly, force-close.
        if child is not None and child.isalive():
            try:
                child.sendintr()
                child.close(force=True)
            except pexpect.exceptions.ExceptionPexpect, OSError:
                logger.debug("child cleanup during Ctrl+C failed", exc_info=True)
        sink.end(
            "crashed",
            preflight_task_count=async_preflight.preflight_task_count,
            resolved_host_count=async_preflight.resolved_host_count,
        )
        # R7 race guard: if the child already exited cleanly (exitstatus
        # is set and the child is no longer alive) before SIGINT fired,
        # prefer the real exit code over the unconditional 130. The
        # narrow window where this matters is between ``_drive``
        # returning and ``run_playbook`` itself returning — small in
        # practice, but observable when the renderer does real work in
        # ``handle_completion``. A still-running child (no exitstatus
        # yet, or ``isalive`` True) is a genuine cancel: keep 130.
        if child is not None and not child.isalive() and child.exitstatus is not None:
            real_exit = int(child.exitstatus)
            renderer.handle_completion(real_exit, "completed" if real_exit == 0 else "failed")
            return real_exit
        renderer.handle_completion(130, "crashed")
        return 130
    finally:
        if async_preflight is not None and not async_preflight.applied:
            try:
                preflight_executor.shutdown(wait=False, cancel_futures=True)
                diagnostics.lifecycle_mark("preflight_end")
            except Exception:
                pass
        else:
            preflight_executor.shutdown(wait=False)
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
    state: RunState,
    renderer: Renderer,
    timeout: float,
    sink: _SessionSink | _NullSink,
    *,
    async_preflight: _AsyncPreflight | None = None,
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

    # R8: post-stats EOF watchdog. The parser flips its phase to
    # POST_RUN_RECAP exactly when it consumes a ``v2_playbook_on_stats``
    # event (see PtyStreamParser._is_jsonl_stats_event), so tracking
    # phase is the canonical way to know stats has been seen. Once
    # that fires, the per-read timeout below grows to ``_EOF_WATCHDOG_S``
    # so a child that never closes its PTY can't hang us forever, and
    # the next post-stats TIMEOUT turns into a synthetic EOF + warning.

    while True:
        if (
            async_preflight is not None
            and not async_preflight.applied
            and async_preflight.future.done()
        ):
            async_preflight.apply(state, renderer, sink, diag=diag)

        # Post-stats: a single ``expect`` call covers the whole watchdog

        # window. Pre-stats: keep the regular per-read timeout so the
        # liveness / prompt heuristics still tick on the normal cadence.
        # R11: once ``v2_playbook_on_stats`` has set the run's
        # ``end_time``, shrink the watchdog to the "quiet" window.
        if parser.phase == StreamPhase.POST_RUN_RECAP and state.end_time is not None:
            read_timeout = _EOF_WATCHDOG_S_QUIET
        else:
            read_timeout = (
                _EOF_WATCHDOG_S if parser.phase == StreamPhase.POST_RUN_RECAP else timeout
            )
        try:
            idx = child.expect(patterns, timeout=read_timeout)
        except pexpect.exceptions.EOF:
            _flush_pending(child, parser, state, renderer, sink)
            break

        if idx == newline_idx:
            before: str = cast("str", child.before or "")
            after: str = cast("str", child.after or "")
            line = before + after
            _trace("newline", line=line[:200])
            # pexpect's `before` carries the entire unread chunk since
            # the last match; when that chunk spans multiple JSONL
            # events (the common case once the child has flushed its
            # final stats event), it contains every event concatenated
            # by `\n`. ``PtyStreamParser.feed_line`` treats the payload
            # as a single JSON document, so a multi-event blob fails
            # to parse and falls through to plaintext — every event in
            # the blob is silently dropped from ``events.jsonl``. Split
            # on the actual newline boundaries so each event lands in
            # its own ``feed_line`` call.
            for sub_line in line.splitlines():
                if not sub_line:
                    continue
                _feed(sub_line, parser, state, renderer, sink, diag=diag)
            # pexpect's ``_before`` StringIO holds the per-match buffer
            # that's exposed as ``child.before`` on the next match.
            # When the post-match ``isalive`` break runs, it calls
            # ``_flush_pending`` which reads ``child.before`` again —
            # the same lines we just fed. Reset the documented per-match
            # accumulator to an empty string so the re-read sees nothing.
            # The setter is a plain attribute write (not a property);
            # some pexpect builds don't expose it as settable, hence
            # the AttributeError fallback.
            try:
                child.before = ""
            except AttributeError:
                pass
            # Reset to 0 (not max(stall_count, 0)) — a newline always
            # ends a silent window, including the "already-handled"
            # window marked by negative stall_count.
            stall_count = 0
            # R10: the child may have exited between ``expect`` returning
            # and now (the Python subprocess finished writing its
            # events and ``sys.exit(0)`` raced with pexpect's match).
            # Check liveness AFTER feeding the newline payload so the
            # trailing events from the same PTY read aren't silently
            # dropped — the previous ordering broke the loop on the
            # last batch and lost events 7/8 in the fixture.
            if not child.isalive():
                _flush_pending(child, parser, state, renderer, sink)
                break
        elif idx == eof_idx:
            _trace("eof", leftover=(child.before or "")[:200])
            _flush_pending(child, parser, state, renderer, sink)
            break
        elif idx == timeout_idx:
            # R8: post-stats timeout = EOF watchdog fired. The child
            # refused to close its PTY within ``_EOF_WATCHDOG_S`` of
            # the final stats event — bail out as if EOF had arrived
            # so the run can complete.
            if parser.phase == StreamPhase.POST_RUN_RECAP:
                warning = (
                    f"EOF watchdog fired after {_EOF_WATCHDOG_S:.0f}s — "
                    "ansible-playbook child did not close its PTY after "
                    "v2_playbook_on_stats; treating as synthetic EOF"
                )
                logger.warning(warning)
                renderer.print_log(f"[aom] {warning}")
                _flush_pending(child, parser, state, renderer, sink)
                break
            # Pre-stats timeout: same liveness / prompt heuristics as
            # before — the watchdog doesn't apply yet.
            #
            # Only consider plaintext as a prompt candidate when it is
            # genuinely the child's LATEST output. JSONL events never touch
            # ``plaintext_lines``, so a stale line ending in ``?`` early in a
            # run would otherwise stay ``plaintext_lines[-1]`` forever and
            # arm a block-forever ``input()`` trap on every later quiet
            # window (e.g. a long silent task). ``latest_output_is_plaintext``
            # is False once any JSONL event has been consumed after the line.
            if parser.plaintext_lines and parser.latest_output_is_plaintext:
                prior = parser.plaintext_lines[-1]
                # Rebuild a multi-line ``|`` pause block whose terminating
                # ``:`` landed on its own line (the bare-colon ``prior`` alone
                # carries no signal — the identifying header is lines back).
                prompt_block = _reconstruct_pause_prompt(parser.plaintext_lines)
            else:
                prior = None
                prompt_block = None
            _trace(
                "timeout",
                stall_count=stall_count,
                buffer=(getattr(child, "buffer", "") or "")[:200],
                before=(getattr(child, "before", "") or "")[:200],
                prior=(prior or "")[:120],
                block=(prompt_block or "")[:200],
            )
            stall_count = _handle_timeout_branch(
                child, renderer, sink, stall_count, prior, prompt_block
            )
            if diag is not None:
                diag.note_timeout()
                diag.note_stall(stall_count if stall_count > 0 else 0)
            timeout_count += 1
            if timeout_count >= cpu_sample_every:
                pid = child.pid
                if pid is not None:
                    renderer.note_subprocess_active(_sample_subprocess_active(pid))
                timeout_count = 0
            continue
        else:
            # Password prompt fired. Build the prompt text from the
            # pre-match content (which may contain prior plaintext we
            # haven't routed yet) and the matched prompt itself.
            prompt_before: str = cast("str", child.before or "")
            prompt_after: str = cast("str", child.after or "")
            prompt = prompt_before + prompt_after
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
        except AttributeError:
            # Defensive: some pexpect versions/spawn variants don't
            # support direct buffer assignment. Fall back to a
            # read_nonblocking drain.
            try:
                child.read_nonblocking(size=len(pending), timeout=0)
            except pexpect.exceptions.ExceptionPexpect:
                logger.debug("buffer drain via read_nonblocking failed", exc_info=True)
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
        logger.warning("interactive prompt handler crashed; sending empty line", exc_info=True)
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
    prompt_block: str | None = None,
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

    # Case 2b: a multi-line ``|`` block ``prompt:`` whose terminating
    # ``:`` landed on its own newline-terminated line. The buffer is
    # empty and the immediate prior line is a bare ``:`` (no signal), so
    # the block is reconstructed from recent plaintext at the call site
    # and the ``[Task name]`` header inside it identifies the pause.
    if not pending and prompt_block and _looks_like_interactive_prompt(prompt_block):
        _fire_prompt(child, renderer, sink, prompt_block, None)
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
    state: RunState,
    renderer: Renderer,
    sink: _SessionSink | _NullSink,
) -> None:
    """Drain any final bytes left in the buffer when the subprocess ends.

    EOF often arrives without a trailing newline — pexpect leaves the last
    fragment in `child.before`. We treat it as a terminal line so its event,
    if any, still reaches the renderer.

    When the child died mid-write, ``child.before`` may also hold multiple
    ``\\n``-separated events that arrived in the same PTY read. Feed each
    non-empty line individually; ``PtyStreamParser.feed_line`` can only
    parse one JSON object per call.

    R17: also drain ``child.buffer`` (pexpect's internal unread accumulator).
    After the newline branch resets ``child.before = ""`` and the
    ``isalive()`` check fires, ``child.buffer`` may still hold events that
    arrived in the same PTY read but after the matched ``\\n``. Without this,
    trailing events are silently dropped when the child exits between
    ``expect()`` returning and the ``isalive()`` check.
    """
    leftover = (child.before or "") + (_peek_unread(child) or "")
    if not leftover.strip():
        return
    for sub_line in leftover.splitlines():
        if sub_line:
            _feed(sub_line, parser, state, renderer, sink)


def _feed(
    line: str,
    parser: PtyStreamParser,
    state: RunState,
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

    ``state`` (the runner's own RunState) is fed events in parallel
    with the renderer's state so the post-stats watchdog logic in
    ``_drive`` can read ``state.end_time`` without depending on
    renderer-private attributes. The renderer's RunState is the
    source of truth for display; this one is read-only outside the
    watchdog timeout selection.

    When ``diag`` is supplied, it receives ``note_pty_bytes(len(line))``
    plus a ``note_event`` per parsed JSONL event — that's how the
    diagnostics histogram is built (also fires the ``first_event``
    lifecycle mark on the first call).
    """
    renderer.note_pty_bytes()
    if diag is not None:
        diag.note_pty_bytes(len(line))

    trace_events = diagnostics.is_debug()
    for event in parser.feed_line(line):
        # R11: feed the runner's RunState so ``state.end_time`` is set
        # when ``v2_playbook_on_stats`` is consumed. The renderer's own
        # ``update_state`` does this too for display purposes; this call
        # is what makes ``_drive``'s quiet-watchdog selection work.
        state.handle_event(event)
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


_PSUTIL_CACHE: dict[int, Any] = {}
_PSUTIL_PROBE_SENTINEL: Any = object()
_PSUTIL_MODULE: Any = _PSUTIL_PROBE_SENTINEL
_PSUTIL_DISABLED_REASON: str | None = None


def _probe_psutil() -> tuple[Any, str | None]:
    """Subprocess-probe ``import psutil``; return ``(module, None)`` on
    success or ``(None, reason)`` on failure.

    A try/except cannot catch the SIGSEGV that ``_psutil_linux.abi3.so``
    raises during its C-level module init when the shared object is
    ABI-incompatible with the running interpreter (the common case:
    uv-installed CPython loading a Nix-built ``.so``). Running the
    import inside a subprocess turns that crash into an exit code we
    can read — and the main process keeps running.
    """
    import subprocess

    try:
        result = subprocess.run(
            [sys.executable, "-c", "import psutil"],
            capture_output=True,
            timeout=10,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return None, "psutil import probe timed out"
    except OSError as e:
        return None, f"psutil import probe OSError: {e}"

    if result.returncode != 0:
        stderr_tail = (result.stderr or b"").decode("utf-8", errors="replace").strip()
        # Negative return code on POSIX = killed by signal (e.g. -11 = SIGSEGV).
        return None, f"psutil import probe exit={result.returncode} stderr={stderr_tail!r}"

    try:
        import psutil  # noqa: PLC0415
    except ImportError as e:
        return None, f"psutil ImportError after passing probe: {e}"

    return psutil, None


def _get_psutil() -> Any:
    """Return the cached psutil module, or None if probing failed.

    Lazy: the first call probes (one subprocess spawn). All subsequent
    calls return the cached result so the heartbeat loop pays at most
    one probe cost per process.
    """
    global _PSUTIL_MODULE, _PSUTIL_DISABLED_REASON
    if _PSUTIL_MODULE is _PSUTIL_PROBE_SENTINEL:
        module, reason = _probe_psutil()
        _PSUTIL_MODULE = module
        _PSUTIL_DISABLED_REASON = reason
        if reason is not None:
            diagnostics.set_psutil_disabled(reason)
    return _PSUTIL_MODULE


def _psutil_disabled_reason() -> str | None:
    return _PSUTIL_DISABLED_REASON


def _reset_psutil_probe_for_testing() -> None:
    """Test-only: undo the probe cache so each test sees a fresh state."""
    global _PSUTIL_MODULE, _PSUTIL_DISABLED_REASON
    _PSUTIL_MODULE = _PSUTIL_PROBE_SENTINEL
    _PSUTIL_DISABLED_REASON = None
    _PSUTIL_CACHE.clear()


def _sample_subprocess_active(pid: int) -> bool:
    """Return True if pid or any descendant used CPU since the last call.

    Uses ``psutil.cpu_percent(interval=None)`` — non-blocking, returns
    the delta since the previous call on the same Process. Caches by
    pid at module scope so deltas stay meaningful.

    psutil is loaded behind a one-shot subprocess probe (see
    :func:`_get_psutil`) so an ABI-broken ``_psutil_linux.abi3.so``
    can't SIGSEGV the runner. When psutil is unavailable for any
    reason — broken install, import error, missing module — this
    helper returns False; the heartbeat still works on the byte
    signal alone.
    """
    psutil = _get_psutil()
    if psutil is None:
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
    except OSError, AttributeError:
        # OSError: e.g. race where the PID disappears between
        # Process(pid) and is_running() returning True.
        # AttributeError: psutil sometimes raises this on exotic platforms.
        logger.debug("psutil CPU sampling failed", exc_info=True)
        cache.pop(pid, None)
        return False
