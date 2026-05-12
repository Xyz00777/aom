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
from ansible_aom.runner import run_playbook
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
        """
        super().__init__(**kwargs)
        self._playbook: str | None = playbook
        self._args: list[str] = list(ansible_args) if ansible_args is not None else []
        self._session_dir: Path | None = session_dir
        self._state: str = "IDLE"
        self._exit_code: int | None = None
        self._final_state: str | None = None
        self._run_state: RunState = RunState(playbook=playbook or "")
        self._warnings_count: int = 0
        self._deprecations_count: int = 0
        self._log_lines: list[str] = []
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

    # ----- Public read-only surface for tests + widgets -----

    @property
    def playbook(self) -> str | None:
        return self._playbook

    @property
    def ansible_args(self) -> list[str]:
        return self._args

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

    def add_warning(self, message: str, is_deprecation: bool = False) -> None:
        """Renderer Protocol: bump counters; widgets can read them."""
        if is_deprecation:
            self._deprecations_count += 1
        else:
            self._warnings_count += 1
        self._dirty += 1

    def print_log(self, message: str) -> None:
        """Renderer Protocol: append a line to the log buffer.

        The line is also queued in ``_pending_log_lines`` so the periodic
        UI tick can write it into ``LogPanel`` on the main thread.
        """
        self._log_lines.append(message)
        self._pending_log_lines.append(message)
        self._dirty += 1

    def tick(self) -> None:
        """Renderer Protocol: no-op. Textual has its own clock."""
        return None

    def update_state(self, event: dict) -> None:
        """Renderer Protocol: route the JSONL event through RunState.

        Called from the runner worker thread. The mutation itself is
        cheap and thread-safe on a plain dataclass; any visible widget
        refresh that depends on it should be scheduled via
        ``call_from_thread``.
        """
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
        """
        self._exit_code = exit_code
        self._final_state = state
        if exit_code == 0:
            self._state = "COMPLETED"
        elif exit_code == 1:
            self._state = "FAILED"
        else:
            self._state = "CRASHED"

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
        if self._playbook is None:
            return
        try:
            run_playbook(
                self._playbook,
                self._args,
                self,
                session_dir=self._session_dir,
            )
        except Exception as exc:
            # Surface unexpected failures into final_state instead of
            # leaving the user with a frozen UI and no explanation.
            self._exit_code = 1
            self._final_state = "crashed"
            self._log_lines.append(f"[ERROR] runner crashed: {exc}")

    def on_mount(self) -> None:
        """Mount the main screen and (if configured) start the playbook."""
        from ansible_aom.tui.screens.main import MainScreen

        self.push_screen(MainScreen())

        # Auto-start only when constructed with a playbook target. The
        # protocol smoke tests still build a bare AOMApp() and never
        # call run() — they must not trigger a worker.
        if self._playbook is not None:
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
