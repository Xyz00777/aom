"""Re-run dialog for AOM TUI.

Triggered by Shift+R / R after a playbook finishes.
See SPECIFICATION.md Section 10 for keybindings.

Shows the planned re-invocation of ``ansible-playbook`` derived from the
last session's failed / unreachable / changed hosts. Confirms or cancels
the rerun; the resolved host set and command line come from the same
``aom rerun`` machinery that the CLI uses, so the dialog cannot drift
from the documented behaviour.
"""

from pathlib import Path
from typing import Any

from rich.console import Group
from rich.panel import Panel
from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Static

from ansible_aom.rerun.cli import (
    _build_rerun_command,
    _compose_host_set,
    _resolve_session_id,
    _strip_limit_args,
)
from ansible_aom.session.store import find_latest_session, load_session
from ansible_aom.session.summary import (
    collect_changed_hosts,
    collect_failed_hosts,
    collect_unreachable_hosts,
)


def _resolve_target_session(
    state_dir: Path, requested: str | None
) -> tuple[str | None, str | None]:
    """Return ``(session_id, error_message)`` for the requested rerun target.

    Mirrors ``aom rerun``'s argument resolution: explicit id (full or
    unique prefix) wins, otherwise the most recent session is used.
    Errors are returned as a string so the dialog can display them
    inline rather than crash on an exception.
    """
    if requested is None:
        latest = find_latest_session(state_dir)
        if latest is None:
            return None, "No sessions found in state directory."
        return latest, None

    try:
        return _resolve_session_id(state_dir, requested), None
    except LookupError as exc:
        return None, str(exc)


def _resolve_host_set(
    session: dict,
    host_filter: str,
) -> tuple[set[str], str]:
    """Compose the host set the rerun will target.

    Args:
        session: Loaded session dict from ``load_session``.
        host_filter: One of ``"failed"`` (default), ``"unreachable"``,
            ``"changes"``. Maps to the equivalent ``aom rerun`` flag.

    Returns:
        ``(hosts, description)`` where ``description`` is a short
        human phrase naming the source category, used for the heading
        in the dialog body.
    """
    if host_filter == "unreachable":
        return (
            _compose_host_set(session, failed=False, unreachable=True, changes_only=False),
            "failed + unreachable hosts",
        )
    if host_filter == "changes":
        return (
            _compose_host_set(session, failed=False, unreachable=False, changes_only=True),
            "hosts that reported changed",
        )
    return (
        _compose_host_set(session, failed=True, unreachable=False, changes_only=False),
        "failed hosts",
    )


class RerunDialog(ModalScreen[bool]):
    """Modal dialog confirming a re-run of the recorded playbook.

    The dialog shows three sections:

    1. Session header — id, playbook, original args, status.
    2. Target host list — names + counts grouped by failed/unreachable/changed.
    3. Planned command — the exact ``ansible-playbook …`` invocation.

    Returns True on confirm (Rerun), False on cancel (Esc / n).

    The actual re-invocation is the caller's job: the dialog only
    surfaces the plan and the user's intent. Returning True tells the
    caller "the user said yes"; it does not itself spawn a process —
    keeping dialogs side-effect-free makes them testable.
    """

    DEFAULT_CSS = """
    RerunDialog {
        align: center middle;
    }

    RerunDialog > VerticalScroll {
        width: 78;
        height: auto;
        max-height: 90%;
        padding: 1 2;
        background: $surface;
        border: solid $primary;
    }
    """

    BINDINGS = [
        Binding(key="escape", action="cancel", description="Cancel"),
        Binding(key="n", action="cancel", description="Cancel"),
        Binding(key="y", action="confirm", description="Rerun"),
        Binding(key="enter", action="confirm", description="Rerun (default)"),
        Binding(key="r", action="confirm", description="Rerun (same as y)"),
    ]

    def __init__(
        self,
        state_dir: Path | None = None,
        session_id: str | None = None,
        host_filter: str = "failed",
    ) -> None:
        """Build the dialog from a recorded session on disk.

        Args:
            state_dir: Where AOM stores session artifacts. Defaults to
                ``~/.local/state/aom/sessions``. Tests override this
                with a tmp dir to stay isolated.
            session_id: Specific session to rerun (full UUID or unique
                prefix). ``None`` picks the most recent session.
            host_filter: Which host category drives the ``--limit``:
                ``"failed"`` (default), ``"unreachable"``, or
                ``"changes"``. Matches the corresponding ``aom rerun``
                CLI flag.
        """
        super().__init__()
        self._state_dir = state_dir or (Path.home() / ".local" / "state" / "aom" / "sessions")
        self._requested_session_id = session_id
        self._host_filter = host_filter
        self._resolved_session_id: str | None = None
        self._session: dict[str, Any] | None = None
        self._hosts: set[str] = set()
        self._host_description: str = ""
        self._planned_playbook: str = ""
        self._planned_args: list[str] = []
        self._error: str | None = None
        self._load_plan()

    def _load_plan(self) -> None:
        """Read session data and compute the planned command line."""
        session_id, err = _resolve_target_session(self._state_dir, self._requested_session_id)
        if err is not None:
            self._error = err
            return
        assert session_id is not None
        self._resolved_session_id = session_id

        session = load_session(session_id, self._state_dir)
        if session is None:
            self._error = f"Failed to load session {session_id}"
            return
        self._session = session

        if "ansible_args" not in session:
            self._error = (
                f"Session {session_id} is missing 'ansible_args' (schema < 1.1); "
                "rerun cannot reconstruct the original command."
            )
            return

        hosts, description = _resolve_host_set(session, self._host_filter)
        self._hosts = hosts
        self._host_description = description

        if not hosts:
            self._error = f"No {description} found in session {session_id} — nothing to rerun."
            return

        try:
            playbook, args = _build_rerun_command(session, hosts)
        except ValueError as exc:
            self._error = str(exc)
            return
        self._planned_playbook = playbook
        self._planned_args = list(args)

    def _session_header(self) -> Text:
        """First section: identify which session this rerun targets."""
        text = Text()
        session = self._session or {}
        sid = self._resolved_session_id or "(unknown)"
        text.append("Session:  ", style="bold")
        text.append(f"{sid}\n")
        text.append("Playbook: ", style="bold")
        text.append(f"{session.get('playbook', '(unknown)')}\n")
        text.append("Status:   ", style="bold")
        text.append(f"{session.get('status', 'unknown')}\n")
        original_args = list(session.get("ansible_args") or [])
        text.append("Original args: ", style="bold")
        text.append(" ".join(original_args) if original_args else "(none)\n")
        text.append(f"\nTarget: {self._host_description}\n", style="bold cyan")
        return text

    def _host_breakdown(self) -> Text:
        """Second section: failed / unreachable / changed host groups."""
        session = self._session or {}
        failed = collect_failed_hosts(session)
        unreachable = collect_unreachable_hosts(session)
        changed = collect_changed_hosts(session)

        text = Text()
        text.append(f"  Failed       ({len(failed)}): ", style="bold")
        text.append(", ".join(sorted(failed)) or "(none)\n", style="red")
        text.append(f"  Unreachable  ({len(unreachable)}): ", style="bold")
        text.append(", ".join(sorted(unreachable)) or "(none)\n", style="magenta")
        text.append(f"  Changed      ({len(changed)}): ", style="bold")
        text.append(", ".join(sorted(changed)) or "(none)\n", style="yellow")
        text.append(f"\nTargeting {len(self._hosts)} host(s) for rerun.\n", style="bold")
        return text

    def _command_panel(self) -> Panel:
        """Third section: the exact ansible-playbook invocation."""
        if not self._planned_playbook:
            return Panel(
                Text("No command — see error above.", style="bold red"),
                title="[bold]Planned command[/bold]",
                border_style="red",
            )
        cmd_str = (
            "ansible-playbook "
            + self._planned_playbook
            + (" " + " ".join(self._planned_args) if self._planned_args else "")
        )
        body = Text()
        body.append(cmd_str, style="cyan")
        body.append(
            "\n\nWARNING: re-running may execute non-idempotent tasks "
            "(notifications, restarts, side-effecting modules).",
            style="yellow",
        )
        return Panel(
            body,
            title="[bold]Planned command[/bold]",
            border_style="cyan",
            padding=(0, 1),
        )

    def _body(self) -> Group:
        """Compose all sections into a single Rich renderable."""
        if self._error is not None:
            return Group(
                Panel(
                    Text(self._error, style="bold red"),
                    title="[bold red]Cannot rerun[/bold red]",
                    border_style="red",
                ),
                Text(
                    "\nPress [bold]n[/bold] or [bold]Esc[/bold] to dismiss.",
                    style="dim",
                ),
            )

        original = self._session or {}
        stripped_args = _strip_limit_args(list(original.get("ansible_args") or []))
        added_limit = [tok for tok in self._planned_args if tok not in stripped_args]

        return Group(
            Panel(
                self._session_header(),
                title="[bold]Session[/bold]",
                border_style="green",
                padding=(0, 1),
            ),
            Panel(
                self._host_breakdown(),
                title="[bold]Hosts[/bold]",
                border_style="yellow",
                padding=(0, 1),
            ),
            self._command_panel(),
            Text(
                "\nFlags added for this rerun: " + (" ".join(added_limit) or "(none)"),
                style="dim",
            ),
            Text(
                "\nPress [bold]y[/bold]/[bold]Enter[/bold]/[bold]r[/bold] to rerun, "
                "[bold]n[/bold]/[bold]Esc[/bold] to cancel.",
                style="dim",
            ),
        )

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Static(self._body(), id="rerun-content")

    def action_confirm(self) -> None:
        """Dismiss with True; the caller is responsible for spawning the rerun."""
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)
