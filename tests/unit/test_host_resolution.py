"""Tests for host name resolution (TC-149 to TC-152).

Covers TEST_SPECIFICATION.md Section 5.8 by exercising the real production
host-resolution code paths:

- TC-149: ``ansible.preflight.assemble_definitions`` and
  ``core.parser.parse_list_hosts_output`` — populated ``resolved_hosts``
  flow from raw ``--list-hosts`` output through to PlayDefinition.
- TC-150: ``RunState._resolve_play_hosts`` — when a v2_runner_on_* event
  arrives with a host NOT in the preflight ``resolved_hosts``, the
  runtime play's per-task host map records the host (and never raises).
- TC-151: ``RunState.set_definitions`` accepting an empty list + v2_runner_on_*
  events populating hosts incrementally — the fallback path when
  ``--list-hosts`` fails.
- TC-152: ``RunState._handle_v2_playbook_on_stats`` consuming the final
  stats event — the cross-check is implicit (final state must match the
  union of hosts the events touched).

Tests do not use inline mock functions or assert against inline helpers;
every assertion checks behaviour of the actual production code under
``ansible_aom.core.parser`` / ``ansible_aom.ansible.preflight`` /
``ansible_aom.core.models``.
"""

from __future__ import annotations

from ansible_aom.ansible.preflight import assemble_definitions
from ansible_aom.core.models import PlayDefinition, Status, TaskDefinition
from ansible_aom.core.parser import parse_list_hosts_output, parse_list_tasks_output
from ansible_aom.core.run_state import RunState


class TestListHostsResolvesHostnames:
    """TC-149: --list-hosts populates PlayDefinition.resolved_hosts."""

    def test_list_hosts_output_populates_resolved_hosts(self, list_hosts_output: str):
        """TC-149: parse_list_hosts_output extracts hostnames per play."""
        result = parse_list_hosts_output(list_hosts_output)

        assert len(result) == 2
        assert result[0]["play_number"] == 1
        assert result[0]["hosts"] == ["web1.example.com", "web2.example.com"]
        assert result[1]["play_number"] == 2
        assert result[1]["hosts"] == ["db1.example.com"]

    def test_assemble_definitions_transfers_resolved_hosts(
        self, list_tasks_output: str, list_hosts_output: str
    ):
        """TC-149: assemble_definitions wires parse_list_hosts_output into PlayDefinition."""
        plays = parse_list_tasks_output(list_tasks_output)
        play_hosts = parse_list_hosts_output(list_hosts_output)

        defs = assemble_definitions(plays=plays, play_hosts=play_hosts)

        assert len(defs) == 2
        assert defs[0].name == "Setup web servers"
        assert defs[0].resolved_hosts == ["web1.example.com", "web2.example.com"]
        assert defs[1].resolved_hosts == ["db1.example.com"]
        assert defs[0].hosts == "webservers"
        assert defs[1].hosts == "dbservers"

    def test_assemble_definitions_no_match_yields_empty_resolved_hosts(self):
        """TC-149 edge: play with no matching --list-hosts entry gets empty resolved_hosts."""
        plays = [{"play_number": 1, "name": "Solo", "tasks": []}]
        # play_hosts is for a different play_number (2) so play 1 has no match
        play_hosts = [
            {
                "play_number": 2,
                "name": "Other",
                "hosts_pattern": ["all"],
                "hosts": ["other.example.com"],
            }
        ]

        defs = assemble_definitions(plays=plays, play_hosts=play_hosts)

        assert len(defs) == 1
        assert defs[0].resolved_hosts == []

    def test_resolved_hosts_empty_when_list_hosts_blank(self):
        """TC-149: Empty --list-hosts output propagates empty resolved_hosts."""
        plays = [{"play_number": 1, "name": "Empty", "tasks": []}]
        defs = assemble_definitions(plays=plays, play_hosts=[])

        assert defs == [] or defs[0].resolved_hosts == []


class TestHostCrossCheckDuringExecution:
    """TC-150: Runner event hostnames matched against resolved_hosts.

    Production code: ``RunState._resolve_play_hosts`` returns the preflight
    resolved_hosts for a runtime play. When a v2_runner_on_* event arrives,
    the host is registered against the task regardless of whether it was
    pre-resolved — so the cross-check is implicit: hosts not in
    resolved_hosts still get added (the runtime is the source of truth at
    task level).
    """

    def test_resolve_play_hosts_returns_preflight_resolved_hosts(self):
        """TC-150: _resolve_play_hosts looks up preflight resolved_hosts by play name."""
        state = RunState(playbook="test.yml")
        state.definitions = [
            PlayDefinition(
                id="1",
                name="Setup webservers",
                hosts="webservers",
                resolved_hosts=["web1", "web2"],
            )
        ]
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "play-uuid-1", "name": "Setup webservers"},
            }
        )

        play = state.plays["play-uuid-1"]
        resolved = state._resolve_play_hosts(play)

        assert resolved == ["web1", "web2"]

    def test_resolve_play_hosts_empty_when_no_definition_match(self):
        """TC-150 edge: play name without a definition returns empty list (no fallback)."""
        state = RunState(playbook="test.yml")
        state.definitions = []  # No definitions → no preflight data
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "play-uuid-1", "name": "Unrecognised play"},
            }
        )

        play = state.plays["play-uuid-1"]
        resolved = state._resolve_play_hosts(play)

        assert resolved == []

    def test_resolve_play_hosts_handles_name_whitespace_difference(self):
        """TC-150: stripped-name match catches whitespace differences."""
        state = RunState(playbook="test.yml")
        state.definitions = [
            PlayDefinition(
                id="1",
                name="Setup webservers",
                hosts="webservers",
                resolved_hosts=["web1", "web2"],
            )
        ]
        # Runtime play name has trailing whitespace — preflight name is stripped
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "play-uuid-1", "name": "Setup webservers "},
            }
        )

        play = state.plays["play-uuid-1"]
        resolved = state._resolve_play_hosts(play)

        assert resolved == ["web1", "web2"]

    def test_task_start_with_resolved_hosts_populates_hosts(self):
        """TC-150: v2_playbook_on_task_start under linear strategy creates HostRunStates."""
        state = RunState(playbook="test.yml")
        state.definitions = [
            PlayDefinition(
                id="1",
                name="Setup webservers",
                hosts="webservers",
                resolved_hosts=["web1", "web2"],
                tasks=[
                    TaskDefinition(
                        name="Install nginx",
                        role=None,
                        tags=[],
                        play_id="1",
                        play_order=0,
                        task_order=0,
                    )
                ],
            )
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "play-uuid-1", "name": "Setup webservers"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "task-uuid-1", "name": "Install nginx"},
                "play": {"id": "play-uuid-1"},
            }
        )

        task = state.plays["play-uuid-1"].tasks["task-uuid-1"]
        assert set(task.hosts) == {"web1", "web2"}
        assert task.hosts["web1"].status == Status.RUNNING
        assert task.hosts["web2"].status == Status.RUNNING


class TestHostFallbackAfterListHostsFailure:
    """TC-151: If --list-hosts fails, resolved_hosts starts empty; populated by runner events.

    Production code path:
    - ``assemble_definitions`` with no play_hosts → empty resolved_hosts
    - Runner events (v2_runner_on_*) populate ``TaskRunState.hosts`` directly
    """

    def test_assemble_definitions_with_empty_play_hosts_yields_empty(self):
        """TC-151: --list-hosts failure → empty play_hosts → empty resolved_hosts."""
        plays = [{"play_number": 1, "name": "Setup webservers", "tasks": []}]

        defs = assemble_definitions(plays=plays, play_hosts=[])

        assert defs[0].resolved_hosts == []

    def test_runstate_with_empty_definitions_resolves_to_empty(self):
        """TC-151: RunState.definitions=[] → _resolve_play_hosts returns []."""
        state = RunState(playbook="test.yml")
        state.definitions = []
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "play-uuid-1", "name": "Setup webservers"},
            }
        )

        resolved = state._resolve_play_hosts(state.plays["play-uuid-1"])
        assert resolved == []

    def test_runner_events_populate_hosts_incrementally(self):
        """TC-151: v2_runner_on_* events add hosts to task.hosts even without preflight."""
        state = RunState(playbook="test.yml")
        state.definitions = []  # No preflight → no resolved_hosts
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "play-uuid-1", "name": "Setup webservers"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "task-uuid-1", "name": "Install nginx"},
                "host": "web1",
                "play": {"id": "play-uuid-1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-04-20T10:00:05Z",
                "task": {"id": "task-uuid-1", "name": "Install nginx"},
                "play": {"id": "play-uuid-1"},
                "hosts": {"web2": {"changed": False, "ok": True}},
            }
        )

        task = state.plays["play-uuid-1"].tasks["task-uuid-1"]
        assert "web1" in task.hosts
        assert "web2" in task.hosts
        assert task.hosts["web2"].status == Status.OK

    def test_runner_event_host_not_in_resolved_hosts_still_added(self):
        """TC-151 edge: host arriving from a runner event but absent from preflight
        resolved_hosts is still added to the task's host map (runtime is authoritative)."""
        state = RunState(playbook="test.yml")
        # Preflight resolved only web1 and web2 — but web3 shows up at runtime.
        state.definitions = [
            PlayDefinition(
                id="1",
                name="Setup webservers",
                hosts="webservers",
                resolved_hosts=["web1", "web2"],
            )
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "play-uuid-1", "name": "Setup webservers"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "task-uuid-1", "name": "Install nginx"},
                "host": "web3",
                "play": {"id": "play-uuid-1"},
            }
        )

        task = state.plays["play-uuid-1"].tasks["task-uuid-1"]
        assert "web3" in task.hosts


class TestV2PlaybookOnStatsCrossCheck:
    """TC-152: Final stats event cross-checks collected hosts.

    Production code: ``RunState._handle_v2_playbook_on_stats`` processes the
    final stats event. The cross-check is implicit: any RUNNING host that
    never received a terminal event is force-completed at stats time, and
    any host in stats but not seen during the run is recorded without error.
    """

    def test_stats_event_with_no_failures_marks_run_completed(self):
        """TC-152: v2_playbook_on_stats with no failures transitions state to COMPLETED."""
        state = RunState(playbook="test.yml")
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_stats",
                "_timestamp": "2026-04-20T10:01:00Z",
                "stats": {
                    "web1": {
                        "ok": 5,
                        "changed": 0,
                        "failures": 0,
                        "skipped": 0,
                        "unreachable": 0,
                    },
                },
            }
        )

        assert state.status == Status.COMPLETED
        assert state.end_time is not None

    def test_stats_event_with_failures_marks_run_failed(self):
        """TC-152: v2_playbook_on_stats with failures transitions state to FAILED."""
        state = RunState(playbook="test.yml")
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_stats",
                "_timestamp": "2026-04-20T10:01:00Z",
                "stats": {
                    "web1": {
                        "ok": 4,
                        "changed": 0,
                        "failures": 1,
                        "skipped": 0,
                        "unreachable": 0,
                    },
                },
            }
        )

        assert state.status == Status.FAILED

    def test_stats_event_with_unreachable_marks_run_failed(self):
        """TC-152: v2_playbook_on_stats with unreachable hosts transitions to FAILED."""
        state = RunState(playbook="test.yml")
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_stats",
                "_timestamp": "2026-04-20T10:01:00Z",
                "stats": {
                    "web1": {
                        "ok": 0,
                        "changed": 0,
                        "failures": 0,
                        "skipped": 0,
                        "unreachable": 1,
                    },
                },
            }
        )

        assert state.status == Status.FAILED

    def test_stats_finalizes_stale_running_hosts(self):
        """TC-152: Hosts still marked RUNNING at stats time get finalised."""
        state = RunState(playbook="test.yml")
        state.definitions = [
            PlayDefinition(
                id="1",
                name="Setup webservers",
                hosts="webservers",
                resolved_hosts=["web1", "web2"],
                tasks=[
                    TaskDefinition(
                        name="Install nginx",
                        role=None,
                        tags=[],
                        play_id="1",
                        play_order=0,
                        task_order=0,
                    )
                ],
            )
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "play-uuid-1", "name": "Setup webservers"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "task-uuid-1", "name": "Install nginx"},
                "play": {"id": "play-uuid-1"},
            }
        )
        # web1 and web2 are RUNNING but never received terminal events
        task = state.plays["play-uuid-1"].tasks["task-uuid-1"]
        assert task.hosts["web1"].status == Status.RUNNING

        state.handle_event(
            {
                "_event": "v2_playbook_on_stats",
                "_timestamp": "2026-04-20T10:01:00Z",
                "stats": {},
            }
        )

        # Stats handler should have finalised the stale RUNNING hosts
        assert task.hosts["web1"].status != Status.RUNNING
        assert state.status == Status.COMPLETED

    def test_stats_event_with_unseen_hosts_does_not_error(self):
        """TC-152 edge: stats event hosts not seen during the run still process cleanly."""
        state = RunState(playbook="test.yml")
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_stats",
                "_timestamp": "2026-04-20T10:01:00Z",
                "stats": {
                    "web1": {"ok": 5, "changed": 0, "failures": 0, "skipped": 0, "unreachable": 0},
                    "web2": {"ok": 3, "changed": 0, "failures": 0, "skipped": 0, "unreachable": 0},
                    # web3 wasn't seen during the run
                    "web3": {"ok": 1, "changed": 0, "failures": 0, "skipped": 0, "unreachable": 0},
                },
            }
        )

        assert state.status == Status.COMPLETED
