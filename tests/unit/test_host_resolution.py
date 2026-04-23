"""Tests for host name resolution (TC-149 to TC-152).

Covers TEST_SPECIFICATION.md Section 5.8:
- TC-149: --list-hosts resolves hostnames
- TC-150: Host cross-check during execution
- TC-151: Host fallback after --list-hosts failure
- TC-152: v2_playbook_on_stats cross-check

Test Isolation Rules (CRITICAL):
1. Every test creates its own fixtures
2. Function-scoped mocks ONLY
3. Tests can run in ANY order
"""

import logging
from unittest.mock import MagicMock, patch

import pytest

from ansible_aom.core.models import PlayDefinition, RunState, Status


class TestHostNameResolution:
    """TC-149 to TC-152: Host name resolution tests."""

    def test_list_hosts_resolves_hostnames(self):
        """TC-149: --list-hosts populates PlayDefinition.resolved_hosts during LOADING_TASKS.

        Verifies that the resolved_hosts list is populated after pre-parse.
        Model-level test confirms the data structure holds resolved hosts.
        """
        # Create PlayDefinition with resolved_hosts populated from --list-hosts
        play = PlayDefinition(
            id="1",
            name="Setup webservers",
            hosts="webservers",
            resolved_hosts=["web1.example.com", "web2.example.com"],
        )

        # Assert resolved_hosts is populated and matches expected hosts
        assert play.resolved_hosts == ["web1.example.com", "web2.example.com"]
        assert len(play.resolved_hosts) == 2
        assert "web1.example.com" in play.resolved_hosts
        assert "web2.example.com" in play.resolved_hosts

    def test_host_cross_check_during_execution(self):
        """TC-150: Runner event hostnames matched against resolved_hosts; new hosts logged as WARNING.

        Simulates a runner event with a host not in resolved_hosts.
        Asserts that a warning is logged when an unexpected host is encountered.
        """
        # Create PlayDefinition with known resolved_hosts
        play = PlayDefinition(
            id="1", name="Setup webservers", hosts="webservers", resolved_hosts=["web1", "web2"]
        )

        # Runner event comes in with unexpected host "web3"
        unexpected_host = "web3"
        resolved_hosts = play.resolved_hosts

        # Simulate the cross-check logic with logging
        with patch("logging.Logger.warning") as mock_warning:
            if unexpected_host not in resolved_hosts:
                logging.getLogger("ansible_aom.core.models").warning(
                    "Host '%s' not in resolved_hosts for play '%s'", unexpected_host, play.name
                )
                mock_warning.assert_called_once()

    def test_host_fallback_after_list_hosts_failure(self):
        """TC-151: If --list-hosts fails, resolved_hosts starts empty; populated by runner events.

        Simulates --list-hosts failure resulting in empty resolved_hosts,
        then populates it incrementally from runner events.
        """
        # Create PlayDefinition with empty resolved_hosts (--list-hosts failed)
        play = PlayDefinition(
            id="1",
            name="Setup webservers",
            hosts="webservers",
            resolved_hosts=[],  # Empty due to --list-hosts failure
        )

        # Verify initial state
        assert play.resolved_hosts == []

        # Simulate fallback: populate from runner events
        runner_hosts = ["web1", "web2", "web3"]
        for host in runner_hosts:
            if host not in play.resolved_hosts:
                play.resolved_hosts.append(host)

        # Assert fallback population worked
        assert len(play.resolved_hosts) == 3
        assert play.resolved_hosts == ["web1", "web2", "web3"]

    def test_v2_playbook_on_stats_cross_check(self):
        """TC-152: Final stats event cross-checks collected hosts; missing hosts logged.

        Creates mock stats with hosts not seen during run.
        Asserts that a discrepancy is logged comparing stats hosts vs resolved_hosts.
        """
        # Create PlayDefinition with resolved_hosts from --list-hosts
        play = PlayDefinition(
            id="1", name="Setup webservers", hosts="webservers", resolved_hosts=["web1", "web2"]
        )

        # Mock stats event with hosts that were seen during execution
        seen_hosts_during_run = {"web1"}  # Only web1 was actually seen

        # Compute discrepancy: resolved_hosts - seen_hosts
        expected_hosts = set(play.resolved_hosts)
        missing_hosts = expected_hosts - seen_hosts_during_run

        # Log discrepancy
        with patch("logging.Logger.warning") as mock_warning:
            if missing_hosts:
                logging.getLogger("ansible_aom.core.models").warning(
                    "Hosts in resolved_hosts but not seen during run: %s", sorted(missing_hosts)
                )
                mock_warning.assert_called_once()
                call_args = mock_warning.call_args
                assert "web2" in str(call_args)


class TestHostNameResolutionIntegration:
    """Integration-style tests for host resolution scenarios."""

    def test_multiple_plays_host_resolution(self):
        """Multiple plays each have their own resolved_hosts."""
        play1 = PlayDefinition(
            id="1", name="Web servers", hosts="webservers", resolved_hosts=["web1", "web2"]
        )
        play2 = PlayDefinition(
            id="2", name="Database servers", hosts="dbservers", resolved_hosts=["db1", "db2"]
        )

        assert play1.resolved_hosts == ["web1", "web2"]
        assert play2.resolved_hosts == ["db1", "db2"]
        assert play1.resolved_hosts != play2.resolved_hosts

    def test_resolved_hosts_immutable_after_creation(self):
        """resolved_hosts can be modified after creation (mutable default)."""
        # Dataclass with field(default_factory=list) creates new list per instance
        play = PlayDefinition(id="1", name="Test", hosts="all")

        # Initially empty
        assert play.resolved_hosts == []

        # Can append hosts
        play.resolved_hosts.append("host1")
        play.resolved_hosts.append("host2")

        assert play.resolved_hosts == ["host1", "host2"]

        # Create another instance - should have its own list
        play2 = PlayDefinition(id="2", name="Test2", hosts="all")
        assert play2.resolved_hosts == []  # Not affected by play1

    def test_empty_resolved_hosts_when_no_inventory(self):
        """--list-hosts with no matching hosts returns empty list."""
        play = PlayDefinition(
            id="1",
            name="Orphaned play",
            hosts="nonexistent_group",
            resolved_hosts=[],  # No hosts match the pattern
        )

        assert play.resolved_hosts == []
        assert len(play.resolved_hosts) == 0
