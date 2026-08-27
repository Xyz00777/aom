"""Terminal runner events must update host state even when ids mismatch.

Real-world trigger (2026-07-14): a long-running multi-host task showed
every host as RUNNING with identical elapsed in the tree while the log
above already streamed ``ok: [host]`` lines for several of them. The
per-host terminal events were being dropped silently because the
``(play_id, task_id)`` lookup in the ``v2_runner_on_*`` handlers found
nothing — the exact failure class the ``v2_playbook_on_stats`` docstring
admits to ("terminal events are silently dropped because play_id or
task_id doesn't match"). Stats-time cleanup fixes the *end* of the run;
these tests pin the *mid-run* behaviour:

- A terminal event whose ``task.id`` is unknown but whose ``task.path``
  (or, failing that, ``task.name``) matches a task in the resolved play
  is attributed to that task instead of being dropped.
- A terminal event carrying a stale/unknown ``play.id`` still lands on
  the task that owns its ``task.id``.
- A terminal event that matches nothing is counted in
  ``RunState.unmatched_events`` so the drop is observable.
- ``v2_playbook_on_task_start`` synthesises per-host RUNNING entries
  from hosts seen on earlier tasks of the same play when preflight
  ``resolved_hosts`` is unavailable (linear strategy only).
"""

from __future__ import annotations

from datetime import datetime, timezone

from ansible_aom.core.models import (
    HostRunState,
    PlayDefinition,
    RunState,
    Status,
    TaskDefinition,
)
from ansible_aom.core.tree_projection import TreeProjection

T0 = "2026-07-14T12:00:00Z"
T1 = "2026-07-14T12:00:01Z"
T2 = "2026-07-14T12:00:02Z"
T3 = "2026-07-14T12:00:03Z"


def _play_start(state: RunState, play_id: str = "play-uuid", name: str = "deploy") -> None:
    state.handle_event(
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": T0,
            "play": {"id": play_id, "name": name},
        }
    )


def _task_start(
    state: RunState,
    task_id: str = "t1",
    name: str = "Update AIDE database (if exists)",
    path: str | None = "playbooks/aide/update_db.yml:10",
) -> None:
    task: dict = {"id": task_id, "name": name}
    if path is not None:
        task["path"] = path
    state.handle_event(
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": T1,
            "task": task,
        }
    )


class TestTerminalEventFallbackAttribution:
    def test_ok_with_unknown_task_id_matches_by_path(self):
        """An ok whose task.id is unknown but whose task.path matches the
        running task must update that task's host state."""
        state = RunState(playbook="update_db.yml")
        _play_start(state)
        _task_start(state, task_id="t1")

        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": T2,
                "task": {
                    "id": "DIFFERENT-UUID",
                    "name": "Update AIDE database (if exists)",
                    "path": "playbooks/aide/update_db.yml:10",
                },
                "hosts": {"ipa1": {"changed": False}},
            }
        )

        task = state.plays["play-uuid"].tasks["t1"]
        assert task.hosts["ipa1"].status == Status.OK

    def test_ok_with_unknown_task_id_matches_by_name(self):
        """Without a usable path, the task name is the fallback key."""
        state = RunState(playbook="update_db.yml")
        _play_start(state)
        _task_start(state, task_id="t1", path=None)

        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": T2,
                "task": {"id": "DIFFERENT-UUID", "name": "Update AIDE database (if exists)"},
                "hosts": {"ipa1": {"changed": True}},
            }
        )

        task = state.plays["play-uuid"].tasks["t1"]
        assert task.hosts["ipa1"].status == Status.CHANGED

    def test_failed_with_unknown_task_id_matches_by_name(self):
        """The fallback must cover every terminal handler, not just ok."""
        state = RunState(playbook="update_db.yml")
        _play_start(state)
        _task_start(state, task_id="t1", path=None)

        state.handle_event(
            {
                "_event": "v2_runner_on_failed",
                "_timestamp": T2,
                "task": {"id": "DIFFERENT-UUID", "name": "Update AIDE database (if exists)"},
                "hosts": {"ipa1": {"msg": "boom"}},
            }
        )

        task = state.plays["play-uuid"].tasks["t1"]
        assert task.hosts["ipa1"].status == Status.FAILED

    def test_ok_with_stale_play_id_lands_via_task_ownership(self):
        """An ok carrying a play.id we never saw must still land on the
        task that owns its task.id (today the stale play id short-circuits
        the handler and the event is dropped)."""
        state = RunState(playbook="update_db.yml")
        _play_start(state, play_id="play-uuid")
        _task_start(state, task_id="t1")

        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": T2,
                "play": {"id": "STALE-PLAY-UUID"},
                "task": {"id": "t1", "name": "Update AIDE database (if exists)"},
                "hosts": {"ipa1": {"changed": False}},
            }
        )

        task = state.plays["play-uuid"].tasks["t1"]
        assert task.hosts["ipa1"].status == Status.OK

    def test_name_fallback_prefers_running_task(self):
        """Two same-named tasks in one play: the fallback must pick the
        one still running, not the completed earlier instance."""
        state = RunState(playbook="update_db.yml")
        _play_start(state)
        _task_start(state, task_id="t1", path=None)
        # Complete t1 for its only host, then start a same-named t2.
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": T2,
                "task": {"id": "t1", "name": "Update AIDE database (if exists)"},
                "hosts": {"ipa1": {"changed": False}},
            }
        )
        _task_start(state, task_id="t2", path=None)

        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": T3,
                "task": {"id": "DIFFERENT-UUID", "name": "Update AIDE database (if exists)"},
                "hosts": {"ipa2": {"changed": False}},
            }
        )

        assert "ipa2" in state.plays["play-uuid"].tasks["t2"].hosts
        assert "ipa2" not in state.plays["play-uuid"].tasks["t1"].hosts


class TestUnmatchedEventCounter:
    def test_fully_unmatched_terminal_event_is_counted(self):
        state = RunState(playbook="update_db.yml")
        _play_start(state)
        _task_start(state, task_id="t1")

        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": T2,
                "task": {"id": "NOPE", "name": "some other task", "path": "other.yml:1"},
                "hosts": {"ipa1": {"changed": False}},
            }
        )

        assert state.unmatched_events == {"v2_runner_on_ok": 1}
        # The unrelated running task must be untouched.
        assert state.plays["play-uuid"].tasks["t1"].hosts == {}

    def test_matched_events_do_not_count_as_unmatched(self):
        state = RunState(playbook="update_db.yml")
        _play_start(state)
        _task_start(state, task_id="t1")

        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": T2,
                "task": {"id": "t1", "name": "Update AIDE database (if exists)"},
                "hosts": {"ipa1": {"changed": False}},
            }
        )

        assert state.unmatched_events == {}


class TestTaskStartHostSynthesisFallback:
    def test_second_task_synthesises_hosts_from_prior_task(self):
        """No preflight definitions (or no name match): the second
        task_start under linear strategy must synthesise RUNNING host
        entries from the hosts seen on earlier tasks of the same play."""
        state = RunState(playbook="update_db.yml")
        _play_start(state)
        _task_start(state, task_id="t1", name="Gathering Facts", path=None)
        for host in ("ipa1", "ipa2"):
            state.handle_event(
                {
                    "_event": "v2_runner_on_ok",
                    "_timestamp": T2,
                    "task": {"id": "t1", "name": "Gathering Facts"},
                    "hosts": {host: {"changed": False}},
                }
            )

        _task_start(state, task_id="t2", name="Update AIDE database (if exists)", path=None)

        t2 = state.plays["play-uuid"].tasks["t2"]
        assert sorted(t2.hosts) == ["ipa1", "ipa2"]
        assert all(hs.status == Status.RUNNING for hs in t2.hosts.values())

    def test_no_synthesis_under_free_strategy(self):
        """Under strategy free, per-host runner_on_start is the start
        signal; synthesising from prior tasks would mark hosts RUNNING
        for tasks they haven't started."""
        state = RunState(playbook="update_db.yml")
        _play_start(state)
        # runner_on_start flips detected_strategy to "free".
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": T1,
                "host": "ipa1",
                "task": {"id": "t1", "name": "Gathering Facts"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": T2,
                "task": {"id": "t1", "name": "Gathering Facts"},
                "hosts": {"ipa1": {"changed": False}},
            }
        )

        _task_start(state, task_id="t2", name="Update AIDE database (if exists)", path=None)

        t2 = state.plays["play-uuid"].tasks["t2"]
        assert t2.hosts == {}

    def test_removed_hosts_excluded_from_synthesis(self):
        """A host whose latest result is UNREACHABLE or FAILED is removed
        from the play by ansible — later tasks never run on it, so it
        must not be synthesised as RUNNING."""
        state = RunState(playbook="update_db.yml")
        _play_start(state)
        _task_start(state, task_id="t1", name="Gathering Facts", path=None)
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": T2,
                "task": {"id": "t1", "name": "Gathering Facts"},
                "hosts": {"ipa1": {"changed": False}},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_unreachable",
                "_timestamp": T2,
                "task": {"id": "t1", "name": "Gathering Facts"},
                "hosts": {"ipa2": {"msg": "unreachable"}},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_failed",
                "_timestamp": T2,
                "task": {"id": "t1", "name": "Gathering Facts"},
                "hosts": {"ipa3": {"msg": "boom"}},
            }
        )

        _task_start(state, task_id="t2", name="Update AIDE database (if exists)", path=None)

        t2 = state.plays["play-uuid"].tasks["t2"]
        assert sorted(t2.hosts) == ["ipa1"]

    def test_synthesised_hosts_purged_when_strategy_flips_to_free(self):
        """A play believed linear at task_start can reveal itself as free
        when the first per-host v2_runner_on_start arrives. Synthesised
        still-RUNNING guesses must be purged then — the per-host start
        events are the authoritative signal. Hosts with real terminal
        results keep them."""
        state = RunState(playbook="update_db.yml")
        _play_start(state)
        _task_start(state, task_id="t1", name="Gathering Facts", path=None)
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": T2,
                "task": {"id": "t1", "name": "Gathering Facts"},
                "hosts": {"ipa1": {"changed": False}},
            }
        )
        # t2 starts; ipa1 is synthesised as RUNNING (linear assumption).
        _task_start(state, task_id="t2", name="Update AIDE database (if exists)", path=None)
        assert "ipa1" in state.plays["play-uuid"].tasks["t2"].hosts

        # First per-host start event → the play is actually free.
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": T3,
                "host": "ipa2",
                "task": {"id": "t2", "name": "Update AIDE database (if exists)"},
            }
        )

        t2 = state.plays["play-uuid"].tasks["t2"]
        assert sorted(t2.hosts) == ["ipa2"]

    def test_preflight_resolved_hosts_still_win(self):
        """When preflight resolved_hosts is available it stays the
        synthesis source — the prior-task union is only the fallback."""
        state = RunState(playbook="update_db.yml")
        state.definitions = [
            PlayDefinition(
                id="1",
                name="deploy",
                hosts="aide_hosts",
                resolved_hosts=["ipa1", "ipa2", "ipa3"],
                tasks=[],
            )
        ]
        _play_start(state)
        _task_start(state, task_id="t1")

        t1 = state.plays["play-uuid"].tasks["t1"]
        assert sorted(t1.hosts) == ["ipa1", "ipa2", "ipa3"]


class TestTreeReflectsPartialCompletion:
    """Regression pin for the 2026-07-14 report: subset of hosts done —
    completed hosts leave the tree (their result lines already streamed
    to the log) while the rest keep their own timers."""

    def test_tree_shows_per_host_status_when_subset_completed(self):
        play_name = "Update AIDE database (manual run after changes)"
        task_names = [
            "Update AIDE database (if exists)",
            "Reinitialize AIDE database (missing or corrupted)",
            "Overwrite AIDE database",
            "Remove temporary database",
        ]
        hosts = [f"h{i:02d}" for i in range(6)]
        state = RunState(playbook="update_db.yml")
        state.definitions = [
            PlayDefinition(
                id="1",
                name=play_name,
                hosts="aide_hosts",
                resolved_hosts=list(hosts),
                tasks=[
                    TaskDefinition(
                        name=name,
                        role=None,
                        tags=[],
                        play_id="1",
                        play_order=0,
                        task_order=i,
                    )
                    for i, name in enumerate(task_names)
                ],
            )
        ]
        _play_start(state, name=play_name)
        _task_start(state, task_id="t1", name=task_names[0], path=None)
        for host in hosts[:2]:
            state.handle_event(
                {
                    "_event": "v2_runner_on_ok",
                    "_timestamp": T2,
                    "task": {"id": "t1", "name": task_names[0]},
                    "hosts": {host: {"changed": False}},
                }
            )

        projection = TreeProjection.from_run_state(state)
        now = datetime(2026, 7, 14, 12, 2, 10, tzinfo=timezone.utc)
        lines = projection.tree_lines(budget=30, now=now)

        by_label = {ln.label: ln for ln in lines if ln.kind == "host"}
        # Completed hosts drop off the leaf list; the task-line summary
        # below still accounts for them.
        assert "h00" not in by_label
        assert "h01" not in by_label
        for host in hosts[2:]:
            assert by_label[host].status == Status.RUNNING
            assert by_label[host].elapsed_s is not None
            assert by_label[host].elapsed_s > 100

        task_line = next(
            ln for ln in lines if ln.kind == "task" and "AIDE database (if" in ln.label
        )
        assert "(2 ok, 4 running)" in task_line.label


class TestRunOnceHostSynthesis:
    """run_once + delegate_to tasks emit a terminal event for only the one
    delegated host. Under linear strategy the task_start synthesis would
    otherwise mark every preflight resolved_host as phantom-RUNNING. These
    tests pin the run_once-aware synthesis skip and the sweep flip."""

    def _run_once_state(self, run_once: bool = True) -> RunState:
        state = RunState(playbook="update_db.yml")
        state.definitions = [
            PlayDefinition(
                id="1",
                name="deploy",
                hosts="ipa_hosts",
                resolved_hosts=["ipa1", "ipa2", "ipa3"],
                tasks=[
                    TaskDefinition(
                        name="Create external service DNS records (dynamic)",
                        role=None,
                        tags=[],
                        play_id="1",
                        play_order=0,
                        task_order=0,
                        path="dns_tasks.yml:2",
                        run_once=run_once,
                    )
                ],
            )
        ]
        return state

    def test_run_once_task_no_synthesis(self):
        """run_once preflight def: task_start must not synthesise the 3
        resolved hosts; the single delegated host's terminal event is the
        only host entry."""
        state = self._run_once_state(run_once=True)
        _play_start(state)
        _task_start(
            state,
            task_id="t1",
            name="Create external service DNS records (dynamic)",
            path="dns_tasks.yml:2",
        )

        t1 = state.plays["play-uuid"].tasks["t1"]
        assert t1.hosts == {}

        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": T2,
                "task": {
                    "id": "t1",
                    "name": "Create external service DNS records (dynamic)",
                    "path": "dns_tasks.yml:2",
                },
                "hosts": {"ipa1": {"changed": True}},
            }
        )
        assert sorted(t1.hosts) == ["ipa1"]
        assert t1.hosts["ipa1"].status == Status.CHANGED
        assert t1.status == Status.COMPLETED

    def test_non_run_once_control_synthesises(self):
        """Regression guard: with run_once=False the 3 resolved hosts are
        synthesised as RUNNING exactly as before."""
        state = self._run_once_state(run_once=False)
        _play_start(state)
        _task_start(
            state,
            task_id="t1",
            name="Create external service DNS records (dynamic)",
            path="dns_tasks.yml:2",
        )

        t1 = state.plays["play-uuid"].tasks["t1"]
        assert sorted(t1.hosts) == ["ipa1", "ipa2", "ipa3"]
        assert all(hs.status == Status.RUNNING for hs in t1.hosts.values())

    def test_runtime_graft_stamps_run_once_from_cache(self, tmp_path):
        """A dynamically included run_once task (no preflight leaf) is
        grafted at runtime; the graft must stamp run_once from the include
        cache so synthesis is skipped."""
        playbook = tmp_path / "playbook.yml"
        playbook.write_text(
            "- hosts: all\n"
            "  tasks:\n"
            "    - name: Gathering Facts\n"
            "      ansible.builtin.setup:\n"
            "    - name: include dns\n"
            "      ansible.builtin.include_tasks: dns_tasks.yml\n"
        )
        (tmp_path / "dns_tasks.yml").write_text(
            "- name: Create external service DNS records (dynamic)\n"
            "  run_once: true\n"
            "  delegate_to: localhost\n"
            "  ansible.builtin.debug:\n"
            "    msg: hi\n"
        )

        state = RunState(playbook=str(playbook))
        state.definitions = [
            PlayDefinition(
                id="1",
                name="deploy",
                hosts="ipa_hosts",
                resolved_hosts=["ipa1", "ipa2", "ipa3"],
                tasks=[
                    TaskDefinition(
                        name="Gathering Facts",
                        role=None,
                        tags=[],
                        play_id="1",
                        play_order=0,
                        task_order=0,
                    )
                ],
            )
        ]
        _play_start(state)
        # First task matches the preflight leaf → sets the graft parent.
        _task_start(state, task_id="t1", name="Gathering Facts", path=None)
        # The run_once include task is unknown to preflight → grafted.
        _task_start(
            state,
            task_id="t2",
            name="Create external service DNS records (dynamic)",
            path="dns_tasks.yml:2",
        )

        t2 = state.plays["play-uuid"].tasks["t2"]
        assert t2.hosts == {}

    def test_sweep_flips_synthesised_run_once_hosts_to_skipped(self):
        """Detection miss: a run_once task that already has synthesised
        RUNNING hosts must have them flipped to SKIPPED (not OK) when the
        next task starts."""
        state = self._run_once_state(run_once=True)
        _play_start(state)
        _task_start(
            state,
            task_id="t1",
            name="Create external service DNS records (dynamic)",
            path="dns_tasks.yml:2",
        )
        t1 = state.plays["play-uuid"].tasks["t1"]
        # Simulate a detection miss: synthesised RUNNING hosts present.
        for host in ("ipa1", "ipa2", "ipa3"):
            t1.hosts[host] = HostRunState(
                hostname=host,
                status=Status.RUNNING,
                start_time=datetime(2026, 7, 14, 12, 0, 1, tzinfo=timezone.utc),
                synthesised=True,
            )

        _task_start(state, task_id="t2", name="Next task", path=None)

        assert all(hs.status == Status.SKIPPED for hs in t1.hosts.values())
        assert t1.status == Status.COMPLETED

    def test_sweep_control_non_run_once_flips_to_ok(self):
        """Regression guard: non-run_once synthesised hosts keep the OK
        flip when the next task starts."""
        state = self._run_once_state(run_once=False)
        _play_start(state)
        _task_start(
            state,
            task_id="t1",
            name="Create external service DNS records (dynamic)",
            path="dns_tasks.yml:2",
        )
        t1 = state.plays["play-uuid"].tasks["t1"]
        # t1 already synthesised 3 RUNNING hosts; add a real loop-item host.
        t1.hosts["loop-host"] = HostRunState(
            hostname="loop-host",
            status=Status.RUNNING,
            start_time=datetime(2026, 7, 14, 12, 0, 1, tzinfo=timezone.utc),
            synthesised=False,
        )

        _task_start(state, task_id="t2", name="Next task", path=None)

        assert all(hs.status == Status.OK for hs in t1.hosts.values())
        assert t1.status == Status.COMPLETED

    def test_tree_shows_only_delegated_host_after_run_once(self):
        """After a run_once task completes with only the delegated host,
        the tree's host lines contain only that host — the phantom
        non-target hosts never appear."""
        state = self._run_once_state(run_once=True)
        _play_start(state)
        _task_start(
            state,
            task_id="t1",
            name="Create external service DNS records (dynamic)",
            path="dns_tasks.yml:2",
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": T2,
                "task": {
                    "id": "t1",
                    "name": "Create external service DNS records (dynamic)",
                    "path": "dns_tasks.yml:2",
                },
                "hosts": {"ipa1": {"changed": True}},
            }
        )

        projection = TreeProjection.from_run_state(state)
        lines = projection.tree_lines(budget=25)
        host_labels = {ln.label for ln in lines if ln.kind == "host"}
        # The task is COMPLETED so its host lines drop off the leaf list;
        # the invariant is that the phantom non-target hosts never appear.
        assert "ipa2" not in host_labels
        assert "ipa3" not in host_labels
