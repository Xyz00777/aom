"""Pure-helper tests for collect_failed_hosts / collect_unreachable_hosts.

Operates on the dict shape returned by ``core.session.load_session``:
``{"events": [...], "playbook": "...", ...}``. No filesystem, no
fixtures from disk — sessions are constructed inline.
"""

from ansible_aom.session.summary import collect_failed_hosts


def _session(events: list[dict]) -> dict:
    return {"events": events, "playbook": "site.yml", "ansible_args": []}


class TestCollectFailedHosts:
    def test_empty_session_returns_empty_set(self):
        assert collect_failed_hosts(_session([])) == set()

    def test_single_failure_returns_one_host(self):
        events = [
            {
                "_event": "v2_runner_on_failed",
                "task": {"name": "Install nginx"},
                "hosts": {"web2": {"failed": True, "msg": "boom"}},
            }
        ]
        assert collect_failed_hosts(_session(events)) == {"web2"}

    def test_multiple_failures_across_tasks_collected(self):
        events = [
            {
                "_event": "v2_runner_on_failed",
                "task": {"name": "T1"},
                "hosts": {"web2": {"failed": True}},
            },
            {
                "_event": "v2_runner_on_failed",
                "task": {"name": "T2"},
                "hosts": {"web3": {"failed": True}},
            },
        ]
        assert collect_failed_hosts(_session(events)) == {"web2", "web3"}

    def test_same_host_failing_twice_collapses_to_one_entry(self):
        events = [
            {
                "_event": "v2_runner_on_failed",
                "task": {"name": "T1"},
                "hosts": {"web2": {"failed": True}},
            },
            {
                "_event": "v2_runner_on_failed",
                "task": {"name": "T2"},
                "hosts": {"web2": {"failed": True}},
            },
        ]
        assert collect_failed_hosts(_session(events)) == {"web2"}

    def test_unreachable_events_ignored_by_failed_collector(self):
        """collect_failed_hosts only looks at v2_runner_on_failed."""
        events = [
            {
                "_event": "v2_runner_on_unreachable",
                "task": {"name": "Deploy"},
                "hosts": {"web1": {"unreachable": True}},
            },
        ]
        assert collect_failed_hosts(_session(events)) == set()

    def test_ok_events_ignored(self):
        events = [
            {
                "_event": "v2_runner_on_ok",
                "task": {"name": "T1"},
                "hosts": {"web1": {"ok": True}},
            },
        ]
        assert collect_failed_hosts(_session(events)) == set()

    def test_multi_host_failure_event(self):
        """A single failed event can carry multiple hosts."""
        events = [
            {
                "_event": "v2_runner_on_failed",
                "task": {"name": "T1"},
                "hosts": {
                    "web2": {"failed": True},
                    "web3": {"failed": True},
                },
            },
        ]
        assert collect_failed_hosts(_session(events)) == {"web2", "web3"}

    def test_session_without_events_key(self):
        """A meta-only session (no events.jsonl) returns an empty set."""
        assert collect_failed_hosts({"playbook": "site.yml"}) == set()


from ansible_aom.session.summary import collect_unreachable_hosts  # noqa: E402


class TestCollectUnreachableHosts:
    def test_empty_session_returns_empty_set(self):
        assert collect_unreachable_hosts(_session([])) == set()

    def test_single_unreachable_returns_one_host(self):
        events = [
            {
                "_event": "v2_runner_on_unreachable",
                "task": {"name": "Deploy"},
                "hosts": {"web1": {"unreachable": True, "msg": "ssh timed out"}},
            }
        ]
        assert collect_unreachable_hosts(_session(events)) == {"web1"}

    def test_failed_events_ignored_by_unreachable_collector(self):
        events = [
            {
                "_event": "v2_runner_on_failed",
                "task": {"name": "T1"},
                "hosts": {"web2": {"failed": True}},
            },
        ]
        assert collect_unreachable_hosts(_session(events)) == set()

    def test_multi_host_unreachable_event(self):
        events = [
            {
                "_event": "v2_runner_on_unreachable",
                "task": {"name": "Deploy"},
                "hosts": {
                    "web1": {"unreachable": True},
                    "web2": {"unreachable": True},
                },
            },
        ]
        assert collect_unreachable_hosts(_session(events)) == {"web1", "web2"}

    def test_session_without_events_key(self):
        assert collect_unreachable_hosts({"playbook": "site.yml"}) == set()


from ansible_aom.session.summary import collect_changed_hosts  # noqa: E402


class TestCollectChangedHosts:
    def test_empty_session_returns_empty_set(self):
        assert collect_changed_hosts(_session([])) == set()

    def test_changed_host_collected(self):
        events = [
            {
                "_event": "v2_runner_on_ok",
                "task": {"name": "Configure"},
                "hosts": {"web1": {"ok": True, "changed": True}},
            }
        ]
        assert collect_changed_hosts(_session(events)) == {"web1"}

    def test_unchanged_ok_host_ignored(self):
        events = [
            {
                "_event": "v2_runner_on_ok",
                "task": {"name": "Check"},
                "hosts": {"web1": {"ok": True, "changed": False}},
            }
        ]
        assert collect_changed_hosts(_session(events)) == set()

    def test_failed_events_ignored(self):
        events = [
            {
                "_event": "v2_runner_on_failed",
                "task": {"name": "T1"},
                "hosts": {"web2": {"failed": True, "changed": True}},
            }
        ]
        assert collect_changed_hosts(_session(events)) == set()

    def test_multi_host_event_picks_only_changed(self):
        events = [
            {
                "_event": "v2_runner_on_ok",
                "task": {"name": "Config"},
                "hosts": {
                    "web1": {"ok": True, "changed": True},
                    "web2": {"ok": True, "changed": False},
                    "web3": {"ok": True, "changed": True},
                },
            }
        ]
        assert collect_changed_hosts(_session(events)) == {"web1", "web3"}
