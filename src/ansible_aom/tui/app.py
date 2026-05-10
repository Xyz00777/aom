"""Main AOM TUI Application.

This module implements the Textual-based TUI renderer.
See SPECIFICATION.md Section 4.2 for full TUI details.

AOMApp satisfies the Renderer Protocol (Section 2.3) while also being
a Textual App that provides the interactive multi-panel interface.
"""

from typing import Any

from textual.app import App
from textual.binding import Binding

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

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the AOMApp with internal state tracking."""
        super().__init__(**kwargs)
        self._playbook: str | None = None
        self._args: list[str] = []
        self._state: str = "IDLE"
        self._exit_code: int | None = None

    def start(self, playbook: str, args: list[str]) -> None:
        """Start rendering a playbook run.

        Initialize the TUI with playbook name and args, set app title,
        and prepare for event processing.

        Args:
            playbook: Path to the playbook file.
            args: Additional ansible-playbook arguments.
        """
        self._playbook = playbook
        self._args = list(args)  # Make a copy
        self._state = "STARTING"
        # Set app title to playbook name for display
        self.title = playbook

    def set_definitions(self, definitions: list) -> None:
        """Receive preflight definitions.

        TUI builds its tree from RunState today, so this is a no-op for now.
        Once the TUI consumes definitions directly, populate the task tree here.
        """
        return None

    def add_warning(self, message: str, is_deprecation: bool = False) -> None:
        """Renderer Protocol — no-op. TUI surfaces warnings via RunState today."""
        return None

    def print_log(self, message: str) -> None:
        """Renderer Protocol — no-op. TUI renders its own panels, no scrolling log."""
        return None

    def tick(self) -> None:
        """Renderer Protocol — no-op. Textual has its own clock."""
        return None

    def update_state(self, event: dict) -> None:
        """Handle a new JSONL event.

        Receive a JSONL event dict and route it to the appropriate handler
        based on event type. Updates internal RunState.

        Args:
            event: JSONL event dictionary from ansible.posix.jsonl callback.
                Includes '_event' key indicating event type.
        """
        event_type = event.get("_event", "")

        # Route events to state updates based on type
        # Full state machine implementation deferred to RunState integration
        if event_type == "v2_playbook_on_start":
            self._state = "RUNNING"
        elif event_type == "v2_playbook_on_stats":
            self._state = "COMPLETED"

    def handle_password_prompt(self, prompt_text: str) -> str:
        """Handle a password prompt and return the password.

        Show a password modal dialog (Textual ModalScreen), block until
        user responds, and return the password. Timeout after 60 seconds.

        Args:
            prompt_text: The password prompt text to display.

        Returns:
            The password entered by the user, or empty string on timeout.
        """
        import getpass

        try:
            with self.suspend():
                return getpass.getpass(prompt_text + ": ")
        except EOFError, KeyboardInterrupt:
            return ""

    def handle_completion(self, exit_code: int, state: str) -> None:
        """Handle playbook completion (success/failure/crash).

        Update state to COMPLETED/FAILED/CRASHED based on exit code,
        and show summary.

        Args:
            exit_code: The exit code from ansible-playbook subprocess.
                0 = success, 1 = failure, 2 = unreachable, etc.
            state: Final state string (e.g., "completed", "failed", "crashed").
        """
        self._exit_code = exit_code
        # Map completion state string to internal state
        if exit_code == 0:
            self._state = "COMPLETED"
        elif exit_code == 1:
            self._state = "FAILED"
        else:
            self._state = "CRASHED"

    def stop(self) -> None:
        """Stop rendering and clean up.

        Exit the Textual app gracefully, restoring terminal state.
        """
        self.exit()

    def on_mount(self) -> None:
        """Mount the main screen when the app starts.

        This is called by Textual when the app is ready to display.
        We push the MainScreen to start the UI.
        """
        # Import here to avoid circular imports at module load time
        from ansible_aom.tui.screens.main import MainScreen

        self.push_screen(MainScreen())

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
