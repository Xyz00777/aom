"""EventSource Protocol — the source-side port of the architecture.

See ``ARCHITECTURE.md §4.2``. Every concrete driver lives behind this
interface so ``cli.py`` can compose a run with one call:

    driver.drive(renderer)

The protocol is intentionally minimal — a single method that owns
the entire run lifecycle: setup, event pumping, completion, teardown.
That keeps the renderer side decoupled from *how* events were
produced (live subprocess, recorded session, network stream, …).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ansible_aom.renderer.protocol import Renderer


@runtime_checkable
class EventSource(Protocol):
    """A producer of run events for a :class:`Renderer`.

    Implementations own the full lifecycle around their event source:
    starting the renderer, pumping events into it, signalling
    completion, and stopping the renderer in a ``finally`` clause.
    """

    def drive(self, renderer: Renderer) -> int:
        """Drive ``renderer`` to completion and return the run's exit code.

        Contract:
            * ``renderer.start(playbook, args)`` is called once before
              any events flow.
            * Each event is forwarded via ``renderer.update_state``
              (with definitions, warnings, log lines flowing through
              their dedicated methods).
            * ``renderer.handle_completion(exit_code, state)`` is
              called exactly once before ``renderer.stop()``.
            * The returned int is the same exit code passed to
              ``handle_completion`` — useful for the CLI's exit path.
        """
        ...
