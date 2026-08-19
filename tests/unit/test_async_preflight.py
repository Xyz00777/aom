"""Unit tests for async background preflight execution.

When preflight takes longer than the initial grace window, ansible-playbook
must spawn immediately, and the preflight results must be delivered mid-run
when the background worker finishes.
"""

from __future__ import annotations

import time
from concurrent.futures import Future
from unittest.mock import MagicMock

from ansible_aom.ansible.runner import _AsyncPreflight
from ansible_aom.core.models import PlayDefinition, RunState, TaskDefinition
from ansible_aom.core.parser import PreParseResult


def test_async_preflight_applies_definitions_mid_run() -> None:
    """A slow preflight that finishes mid-run updates the renderer and state."""
    state = RunState("site.yml")
    renderer = MagicMock()
    sink = MagicMock()

    fut: Future[PreParseResult] = Future()
    async_pf = _AsyncPreflight(fut, time.monotonic_ns())

    assert not async_pf.applied

    # Deliver result into future
    definitions = [
        PlayDefinition(
            id="p1",
            name="Deploy",
            hosts="all",
            resolved_hosts=["web1", "web2"],
            tasks=[
                TaskDefinition(
                    name="T1", role=None, tags=[], play_id="p1", play_order=0, task_order=0
                ),
                TaskDefinition(
                    name="T2", role=None, tags=[], play_id="p1", play_order=0, task_order=1
                ),
            ],
        )
    ]
    fut.set_result(
        PreParseResult(
            plays=[],
            play_hosts=[],
            definitions=definitions,
            errors=["mock warning"],
            include_cache={},
        )
    )

    async_pf.apply(state, renderer, sink)

    assert async_pf.applied
    assert async_pf.resolved_host_count == 2
    assert async_pf.preflight_task_count == 2
    renderer.set_definitions.assert_called_once_with(definitions)
    renderer.add_warning.assert_called_once_with("mock warning", False)
    sink.record_stderr.assert_called_once_with("mock warning")
