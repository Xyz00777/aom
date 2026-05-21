"""Main AOM TUI Application.

This module implements the Textual-based TUI renderer.
See SPECIFICATION.md Section 4.2 for full TUI details.

AOMApp satisfies the Renderer Protocol (Section 2.3) while also being
a Textual App that provides the interactive multi-panel interface. To
make the TUI work end-to-end, the app owns a worker thread that runs
the pexpect-based playbook driver; renderer callbacks dispatched from
that thread schedule UI updates onto Textual's event loop via
``call_from_thread``.
"""

from pathlib import Path
from typing import Any

from textual.app import App
from textual.binding import Binding

from ansible_aom.core.models import RunState
from ansible_aom.drivers.protocol import EventSource
from ansible_aom.tui.keybindings import KEYBINDINGS, KeyContext
from ansible_aom.tui.widgets import DebugPanel


class AOMApp(App[None]):
    """Textual-based TUI renderer satisfying the Renderer Protocol.

    See SPECIFICATION.md Section 4.2 for TUI layout and Section 2.3
    for the Renderer Protocol definition.
    """

    CSS_PATH = "../styles/app.tcss"
    TITLE = "AOM - Ansible Output Monitor"
    SUB_TITLE = "Monitoring playbook execution"

    # Build BINDINGS from keybindings module - global context only
    BINDINGS = [
        Binding(
            key=key,
            action=action_info["action"],
            description=action_info["description"],
        )
        for key, action_info in KEYBINDINGS.items()
        if action_info["context"] == KeyContext.GLOBAL
    ]

    def __init__(
        self,
        playbook: str | None = None,
        ansible_args: list[str] | None = None,
        session_dir: Path | None = None,
        record: bool = True,
        driver: EventSource | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the AOMApp with optional playbook context.

        Args:
            playbook: Path to the playbook to run when the app mounts.
                When ``None``, the app starts idle (legacy behaviour the
                Renderer-Protocol smoke tests still rely on).
            ansible_args: Extra CLI args to forward to ``ansible-playbook``.
            session_dir: Override for the session recording location.
                ``None`` lets the runner pick the spec default
                ``~/.local/state/aom/sessions/``.
            record: When False the worker uses a driver with recording
                disabled (F3 --no-record). Ignored when ``driver`` is
                supplied — the caller picks the driver's behaviour.
            driver: Optional pre-built :class:`EventSource`. When passed,
                the worker calls ``driver.drive(self)`` directly. When
                ``None`` (legacy path), a :class:`LiveDriver` is
                constructed from ``playbook`` / ``ansible_args`` /
                ``session_dir`` / ``record``.
        """
        super().__init__(**kwargs)
        self._playbook: str | None = playbook
        self._args: list[str] = list(ansible_args) if ansible_args is not None else []
        self._session_dir: Path | None = session_dir
        self._record: bool = record
        # Stored as ``_event_source`` (not ``_driver``) to avoid the
        # name collision with Textual's ``App._driver`` (the terminal
        # input/output driver). Textual swaps that out for HeadlessDriver
        # in ``run_test()`` — our event source would get clobbered.
        self._event_source: EventSource | None = driver
        self._state: str = "IDLE"
        self._exit_code: int | None = None
        self._final_state: str | None = None
        self._run_state: RunState = RunState(playbook=playbook or "")
        self._warnings_count: int = 0
        self._deprecations_count: int = 0
        self._log_lines: list[str] = []
        # Phase 12: renderer activity counters published at completion.
        self._render_calls: int = 0
        self._log_writes: int = 0
        # F1: worker→UI signalling. _dirty is incremented by every
        # renderer callback that mutates state; the periodic tick in
        # on_mount() refreshes widgets only when the value advances.
        # CPython int writes are not strictly atomic but the GIL
        # serialises bytecode and we only ever compare current vs last
        # seen — a lost increment defers, never corrupts.
        self._dirty: int = 0
        # Lines buffered by print_log() from the worker thread; the
        # UI tick drains these into LogPanel on the main thread (Rich
        # widgets are not thread-safe).
        self._pending_log_lines: list[str] = []
        # Last _dirty value the periodic tick observed; used so the
        # tick can short-circuit when nothing has changed.
        self._last_seen_dirty: int = 0

    # ----- Public read-only surface for tests + widgets -----

    @property
    def playbook(self) -> str | None:
        return self._playbook

    @property
    def ansible_args(self) -> list[str]:
        return self._args

    @property
    def record(self) -> bool:
        return self._record

    @property
    def run_state(self) -> RunState:
        return self._run_state

    @property
    def exit_code(self) -> int | None:
        return self._exit_code

    @property
    def final_state(self) -> str | None:
        return self._final_state

    @property
    def warnings_count(self) -> int:
        return self._warnings_count

    @property
    def deprecations_count(self) -> int:
        return self._deprecations_count

    @property
    def log_lines(self) -> list[str]:
        return self._log_lines

    # ----- Renderer Protocol -----

    def start(self, playbook: str, args: list[str]) -> None:
        """Renderer Protocol: enter the RUNNING state and reset state.

        Called once from the runner worker before any events flow.
        Resets the internal RunState so a re-run inside the same app
        instance (e.g. from the rerun screen) starts clean.
        """
        self._playbook = playbook
        self._args = list(args)
        self._state = "STARTING"
        self._run_state = RunState(playbook=playbook)
        self.title = playbook

    def set_definitions(self, definitions: list) -> None:
        """Renderer Protocol: store preflight definitions on the RunState."""
        self._run_state.definitions = list(definitions)
        self._dirty += 1

    def set_prior_run(self, prior_run: object) -> None:  # noqa: ARG002
        """Renderer Protocol no-op — the TUI doesn't surface the prior-run hint yet."""
        return

    def add_warning(self, message: str, is_deprecation: bool = False) -> None:
        """Renderer Protocol: bump counters; widgets can read them.

        Counter mutation itself is GIL-safe, but we marshal through
        ``call_from_thread`` so future side effects (toast notifications,
        StatusBar reactives, etc.) added to the dirty bump run on the
        UI thread by construction.
        """

        def _bump() -> None:
            if is_deprecation:
                self._deprecations_count += 1
            else:
                self._warnings_count += 1
            self._dirty += 1

        self._safe_call_from_thread(_bump)

    def print_log(self, message: str) -> None:
        """Renderer Protocol: append a line to the log buffer.

        Appends to ``_pending_log_lines`` which the periodic UI tick
        drains into ``LogPanel`` on the main thread.
        """

        def _enqueue() -> None:
            self._log_lines.append(message)
            self._pending_log_lines.append(message)
            self._dirty += 1

        self._log_writes += 1
        self._safe_call_from_thread(_enqueue)

    def _safe_call_from_thread(self, fn) -> None:
        """Invoke ``fn`` on the Textual main thread when possible.

        During unit tests (no event loop) and direct synchronous calls
        from the runner-protocol smoke tests, ``call_from_thread``
        raises ``RuntimeError``; fall back to a direct call so those
        tests keep working.
        """
        try:
            self.call_from_thread(fn)
        except RuntimeError:
            fn()

    def tick(self) -> None:
        """Renderer Protocol: no-op. Textual has its own clock."""
        return None

    def note_pty_bytes(self) -> None:
        """Renderer Protocol: no-op. TUI does not surface a heartbeat yet."""
        return None

    def note_subprocess_active(self, active: bool) -> None:  # noqa: ARG002
        """Renderer Protocol: no-op. TUI does not surface a heartbeat yet."""
        return None

    def update_state(self, event: dict) -> None:
        """Renderer Protocol: route the JSONL event through RunState.

        Called from the runner worker thread. The mutation itself is
        cheap and thread-safe on a plain dataclass; any visible widget
        refresh that depends on it should be scheduled via
        ``call_from_thread``.
        """
        self._render_calls += 1
        self._run_state.handle_event(event)
        event_type = event.get("_event", "")
        if event_type == "v2_playbook_on_start":
            self._state = "RUNNING"
        elif event_type == "v2_playbook_on_stats":
            self._state = "COMPLETED"
        self._dirty += 1

    def handle_password_prompt(self, prompt_text: str) -> str:
        """Renderer Protocol: pause the TUI, read a password, resume."""
        import getpass

        try:
            with self.suspend():
                return getpass.getpass(prompt_text + ": ")
        except EOFError, KeyboardInterrupt:
            return ""

    def handle_interactive_prompt(self, prompt_text: str) -> str:
        """Renderer Protocol: pause the TUI and read a line (with echo).

        Used for ``ansible.builtin.pause`` and plain ``vars_prompt``,
        where the user expects to see what they type. ``self.suspend()``
        hands the terminal back so a normal ``input()`` works without
        Textual fighting for keystrokes.

        Same correctness details as the compact renderer:
        - prompt goes to ``sys.stdout`` explicitly (readline would
          otherwise route ``input(prompt)``'s prompt to stderr);
        - ``KeyboardInterrupt`` propagates so Ctrl+C at the prompt
          aborts the run rather than silently sending Enter.
        """
        import sys

        try:
            with self.suspend():
                sys.stdout.write(prompt_text)
                sys.stdout.flush()
                return input()
        except EOFError:
            return ""

    def handle_completion(self, exit_code: int, state: str) -> None:
        """Renderer Protocol: stash final outcome; do not exit the app.

        Leaving the app running lets the user inspect the final state.
        ``stop()`` is intentionally a no-op for the same reason — the
        runner thread completes, but Textual's loop keeps spinning
        until the user presses ``q``.

        Marshals through the event loop so the title update and final
        refresh happen on the main thread (the runner worker calls
        this from a non-UI thread).
        """

        from ansible_aom.core import diagnostics

        diagnostics.set_last_renderer_stats(
            diagnostics.RendererStats(
                render_calls=self._render_calls,
                log_writes=self._log_writes,
            )
        )

        def _finish() -> None:
            self._exit_code = exit_code
            self._final_state = state
            if exit_code == 0:
                self._state = "COMPLETED"
                marker = "✓"
            elif exit_code == 1:
                self._state = "FAILED"
                marker = "✖"
            else:
                self._state = "CRASHED"
                marker = "✖"

            base = self._playbook or self.title
            # Strip a stale marker if handle_completion is called twice.
            for sym in ("✓", "✖"):
                if base.endswith(f" {sym}"):
                    base = base[:-2]
            self.title = f"{base} {marker}"

            # Force one final refresh independent of the tick cadence
            # so the user sees the terminal state immediately.
            self._dirty += 1
            self._refresh_widgets()

        self._safe_call_from_thread(_finish)

    def stop(self) -> None:
        """Renderer Protocol: leave the TUI up so the user can see results.

        The legacy implementation called ``self.exit()`` here, which
        tore the UI down the instant the runner returned and produced
        a blank screen. Now the app stays mounted; ``action_quit`` (q)
        is the user-facing way out.
        """
        return None

    # ----- Worker plumbing -----

    def _run_playbook_worker(self) -> None:
        """Drive the playbook to completion from a Textual worker thread.

        Lives off the main event loop so pexpect's blocking expect()
        calls don't freeze the UI. All renderer callbacks bound to this
        worker (start, update_state, …) mutate plain Python state on
        ``self``; widgets that need to redraw are kicked via
        ``call_from_thread`` from inside those callbacks.
        """
        driver = self._event_source
        if driver is None:
            if self._playbook is None:
                return
            from ansible_aom.drivers.live import LiveDriver

            driver = LiveDriver(
                self._playbook,
                self._args,
                session_dir=self._session_dir,
                record=self._record,
            )
        try:
            driver.drive(self)
        except Exception as exc:
            # Surface unexpected failures into final_state instead of
            # leaving the user with a frozen UI and no explanation.
            self._exit_code = 1
            self._final_state = "crashed"
            self._log_lines.append(f"[ERROR] runner crashed: {exc}")

    def _refresh_widgets(self) -> None:
        """Periodic tick: drain pending updates onto widgets.

        Runs on the Textual event loop (main thread). Reads the
        worker-set _dirty counter and only refreshes when it has
        advanced — avoids per-tick churn in idle phases.

        Guards against firing before the current screen has its
        widgets composed (screen swaps during quit confirmation, for
        instance). Any unexpected widget-state failure is logged and
        swallowed so the timer keeps running.
        """
        try:
            screen = self.screen
        except Exception:
            return
        if not screen.is_mounted:
            return

        current = self._dirty
        if current == self._last_seen_dirty and not self._pending_log_lines:
            return
        self._last_seen_dirty = current

        try:
            from ansible_aom.tui.screens.main import MainScreen

            if isinstance(screen, MainScreen):
                screen.update_from_state(self._run_state)

                # Drain any log lines queued by the worker thread.
                if self._pending_log_lines:
                    from ansible_aom.tui.widgets import LogPanel

                    try:
                        log = screen.query_one(LogPanel)
                    except Exception:
                        log = None
                    if log is not None:
                        # Snapshot-and-clear so a concurrent print_log
                        # call appending mid-iteration is picked up on
                        # the next tick rather than duplicated.
                        pending = self._pending_log_lines[:]
                        del self._pending_log_lines[: len(pending)]
                        for line in pending:
                            log.write_line(line)
        except Exception as exc:
            self.log.error(f"refresh tick error: {exc}")

    def on_mount(self) -> None:
        """Mount the main screen and (if configured) start the playbook."""
        from ansible_aom.tui.screens.main import MainScreen

        self.push_screen(MainScreen())

        # F1: 0.2s refresh tick. nom uses ~200ms; battery-friendly,
        # imperceptible latency. The tick reads the worker-set _dirty
        # counter and only refreshes widgets when it has advanced.
        self.set_interval(0.2, self._refresh_widgets)

        # Auto-start only when constructed with something to drive. The
        # protocol smoke tests still build a bare AOMApp() and never
        # call run() — they must not trigger a worker.
        if self._event_source is not None or self._playbook is not None:
            self.run_worker(self._run_playbook_worker, thread=True, exclusive=True)

    async def action_quit(self) -> None:
        """Quit with confirmation per SPECIFICATION.md Section 10.

        Shows confirmation if running, exits immediately if completed/failed.
        """
        if self._state in ("RUNNING", "STARTING"):
            from ansible_aom.tui.screens.quit_confirm import QuitConfirmScreen

            def on_result(result: bool | None) -> None:
                if result:
                    self.exit()

            self.push_screen(QuitConfirmScreen(), on_result)
        else:
            self.exit()

    async def action_toggle_debug(self) -> None:
        """Toggle debug panel visibility.

        Per SPECIFICATION.md Section 7.5, toggles the debug panel that shows:
        - Command and env overrides
        - Event count
        - Parsing errors
        - Subprocess PID
        - etc.
        """
        try:
            debug_panel = self.screen.query_one(DebugPanel)
            debug_panel.toggle_visibility()
        except Exception:
            pass
