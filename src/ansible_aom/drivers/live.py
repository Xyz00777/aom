"""LiveDriver — :class:`EventSource` that runs a real ``ansible-playbook``.

A thin facade over :func:`ansible_aom.runner.run_playbook`. The
heavy-lifting subprocess/pexpect loop still lives there until §7.2
relocates it to ``ansible/runner.py``; the driver owns parameter
storage and the ``drive()`` boundary so ``cli.py`` only sees the
two-protocol composition root.
"""

from __future__ import annotations

from pathlib import Path

from ansible_aom.renderer.protocol import Renderer


class LiveDriver:
    """Spawns ``ansible-playbook`` and pumps its JSONL output.

    Parameters mirror :func:`ansible_aom.runner.run_playbook` so the
    driver can be constructed once at the CLI composition root and
    handed off to a renderer (or, in the TUI case, to a worker thread
    that calls :meth:`drive` from off the event loop).
    """

    def __init__(
        self,
        playbook: str,
        ansible_args: list[str] | None = None,
        *,
        session_dir: Path | None = None,
        record: bool = True,
    ) -> None:
        self._playbook = playbook
        self._ansible_args: list[str] = list(ansible_args) if ansible_args is not None else []
        self._session_dir = session_dir
        self._record = record

    @property
    def playbook(self) -> str:
        return self._playbook

    @property
    def ansible_args(self) -> list[str]:
        return list(self._ansible_args)

    def drive(self, renderer: Renderer) -> int:
        from ansible_aom.runner import run_playbook

        return run_playbook(
            self._playbook,
            self._ansible_args,
            renderer,
            session_dir=self._session_dir,
            record=self._record,
        )
