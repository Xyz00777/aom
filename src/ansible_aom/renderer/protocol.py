"""Renderer Protocol — the display-side port of the architecture.

See ``ARCHITECTURE.md §4.1``. Every concrete renderer
(``CompactRenderer``, ``AOMApp``, ``JsonRenderer``, future replay-only
fixtures, …) sits behind this Protocol so the rest of the system —
drivers, the CLI, the parity oracle — never sees a concrete
implementation.

This module is also the source of truth for the protocol surface.
SPECIFICATION.md §2.3 lists the same methods at a higher level; if
the two disagree, this file wins.

Mandatory vs optional
---------------------

The Protocol has no Python-level way to mark a method optional, so
each docstring states explicitly whether the method is mandatory or
no-op-able. The summary:

============================== ============================== ==================
Method                         Mandatory for                  May no-op for
============================== ============================== ==================
``start``                      every renderer                 (none)
``stop``                       every renderer                 (none)
``set_definitions``            every renderer                 (none — empty list
                                                              still permitted)
``set_prior_run``              compact                        tui, json, replay
``update_state``               every renderer                 (none)
``handle_completion``          every renderer                 (none)
``add_warning``                live (compact + tui)           json, replay-only
``print_log``                  compact, tui                   json
``tick``                       compact                        tui (own clock),
                                                              json, replay
``note_pty_bytes``             compact (heartbeat)            tui, json, replay
``note_subprocess_active``     compact (heartbeat)            tui, json, replay
``handle_password_prompt``     live driver only               replay, json
                                                              (no human present;
                                                              fail fast)
``handle_interactive_prompt``  live driver only               replay, json
============================== ============================== ==================

Replay drivers never call the password / interactive-prompt methods —
recorded sessions don't replay prompts (see ``drivers/replay.py``'s
"What replay does NOT reproduce" note). Renderers used in
replay-or-JSON contexts may raise ``NotImplementedError`` from these
methods so a misuse is loud rather than silent.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from ansible_aom.core.event_types import JsonlEvent
    from ansible_aom.session.history import PriorRun


@runtime_checkable
class Renderer(Protocol):
    """The display sink for a run.

    Concrete implementations: :class:`CompactRenderer` (compact ANSI),
    :class:`AOMApp` (Textual TUI), :class:`JsonRenderer` (end-of-run
    JSON to stdout). Driven by an :class:`EventSource` from
    ``drivers/``.
    """

    # -----------------------------------------------------------------
    # Lifecycle
    # -----------------------------------------------------------------

    def start(self, playbook: str, args: list[str]) -> None:
        """Begin a run. **Mandatory.**

        Called once before any other method on this instance. Renderers
        use this to initialise their state, start any UI lifecycle
        (Rich Live, Textual app, …), and stash the playbook name + arg
        list for later display.
        """
        ...

    def stop(self) -> None:
        """End a run. **Mandatory.**

        Always called in a ``finally`` block by the driver — even when
        the run was cancelled, crashed, or never got past ``start``.
        Renderers must tear down any UI lifecycle and release the
        terminal here. Safe to call when ``start`` was the only
        previous interaction.
        """
        ...

    # -----------------------------------------------------------------
    # Definitions (preflight)
    # -----------------------------------------------------------------

    def set_definitions(self, definitions: list) -> None:
        """Receive pre-flight playbook definitions (plays/tasks/hosts).

        **Mandatory.** Called once between :meth:`start` and the first
        :meth:`update_state`. Renderers use this to seed the task tree
        and total host count before any JSONL events arrive.

        May receive an empty list when preflight failed (no
        ``--list-tasks`` data); renderers must tolerate that and rebuild
        their tree from the runtime ``v2_playbook_on_play_start`` /
        ``v2_playbook_on_task_start`` events. The replay driver
        deliberately does NOT call this method — recorded sessions
        don't carry the preflight summary.
        """
        ...

    def set_prior_run(self, prior_run: "PriorRun | None") -> None:
        """Optional. Provide stats from the most-recent matching prior run.

        **Mandatory for compact** (drives the "Last run: N tasks in T"
        hint line above the preflight summary). **TUI, JSON, and replay
        renderers may no-op** — they don't display the hint.

        **Must be called before** :meth:`set_definitions` for the
        compact renderer to include the hint in its one-shot startup
        summary. The runner calls them in that order.

        ``None`` means either no matching history exists or the caller
        chose not to look one up — the hint is silently omitted.
        """
        ...

    # -----------------------------------------------------------------
    # Event stream
    # -----------------------------------------------------------------

    def update_state(self, event: "JsonlEvent") -> None:
        """Handle a new JSONL event from ansible.

        **Mandatory.** Called once per event in document order. The
        event dict is the raw output of the ``ansible.posix.jsonl``
        callback, possibly with ``_timestamp`` injected by the parser.
        """
        ...

    # -----------------------------------------------------------------
    # Diagnostics & telemetry pushed by the driver
    # -----------------------------------------------------------------

    def add_warning(self, message: str, is_deprecation: bool = False) -> None:
        """Surface a warning or deprecation to the user.

        **Mandatory for live renderers.** Implementations are expected
        to make the message visible (above the panel, in a dedicated
        panel, …) and bump any visible counter.

        Headless renderers (``JsonRenderer``, replay-only sinks) may
        implement this as a no-op — warnings are still represented in
        the JSON summary's counts, just not surfaced as a printed line.
        """
        ...

    def print_log(self, message: str) -> None:
        """Print a log line above the live panel.

        **Mandatory for compact and TUI renderers** — the runner uses
        this to surface stall hints, password prompt notices, and
        preflight errors that need to be seen verbatim.

        ``JsonRenderer`` no-ops — the JSON consumer parses the final
        summary, not interleaved log lines.
        """
        ...

    def tick(self) -> None:
        """Refresh time-based UI elements during quiet periods.

        Called by the runner when no output has been received for a
        timeout window. Renderers that show elapsed time use this to
        keep the clock moving.

        TUI (Textual has its own clock), JSON (no live UI) and replay
        (no live runtime) may implement as a no-op.
        """
        ...

    def note_pty_bytes(self) -> None:
        """Signal that PTY bytes were just received from the subprocess.

        Drives the compact renderer's per-task liveness indicator.
        TUI, JSON, and replay renderers may no-op.
        """
        ...

    def note_subprocess_active(self, active: bool) -> None:
        """Report a periodic CPU-activity sample for the subprocess tree.

        ``active`` is True when the ansible subprocess or any of its
        descendants used CPU since the previous sample. Used by the
        liveness indicator to distinguish "quiet but working" from
        "no output AND no CPU".

        Only compact's heartbeat reads this; others may no-op.
        """
        ...

    # -----------------------------------------------------------------
    # Interactive prompts (live driver only)
    # -----------------------------------------------------------------

    def handle_password_prompt(self, prompt_text: str) -> str:
        """Capture a password from the user. **Live-driver only.**

        The :class:`LiveDriver` calls this when pexpect matches one of
        the known password-prompt patterns (vault, ssh, become, sudo).
        Implementations must:

        1. Stop / suspend any live UI so getpass can read from the
           real terminal.
        2. Read a password without echoing.
        3. Restart the UI.
        4. Return the password (empty string on EOF / cancel).

        Never called by :class:`ReplayDriver` (recorded sessions skip
        prompts) or by ``JsonRenderer`` consumers (no human present).
        Headless implementations may raise ``NotImplementedError`` so
        misuse is loud rather than silent.
        """
        ...

    def handle_interactive_prompt(self, prompt_text: str) -> str:
        """Capture a non-password line from the user. **Live-driver only.**

        Same lifecycle dance as :meth:`handle_password_prompt`, but the
        user's input is echoed — pause / vars_prompt are not secrets.
        Implementations must:

        1. Stop / suspend any live panel so ``prompt_text`` is visible.
        2. Read one line from stdin.
        3. Restart the panel.
        4. Return the line (empty string on EOF or KeyboardInterrupt).

        Replay / JSON contexts treat this as not-applicable; see
        :meth:`handle_password_prompt`.
        """
        ...

    # -----------------------------------------------------------------
    # Completion
    # -----------------------------------------------------------------

    def handle_completion(self, exit_code: int, state: str) -> None:
        """Final-state callback. **Mandatory.**

        Called exactly once after the last :meth:`update_state` and
        before :meth:`stop`. ``state`` is one of ``"completed"``,
        ``"failed"``, or ``"crashed"`` (the latter covers Ctrl+C exit
        130, missing binary exit 127, and unexpected pexpect failures).
        """
        ...
