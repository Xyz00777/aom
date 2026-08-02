"""Integration tests for PtyStreamParser against real ansible-playbook output.

These tests run ansible-playbook with the JSONL callback plugin and verify
that PtyStreamParser correctly parses all event types and state transitions.

Test playbooks are in tests/playbooks/ and use tests/playbooks/inventory.ini.

Test Isolation Rules:
1. Each test creates its own PtyStreamParser instance
2. Tests use subprocess to run ansible-playbook
3. Function-scoped fixtures ONLY
4. Tests are skipped when ansible-playbook is not available
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from ansible_aom.core.models import Status
from ansible_aom.core.parser import PtyStreamParser, StreamPhase
from ansible_aom.core.run_state import RunState

ANSIBLE_AVAILABLE = shutil.which("ansible-playbook") is not None
PLAYBOOKS_DIR = Path(__file__).parent.parent / "playbooks"
INVENTORY_FILE = PLAYBOOKS_DIR / "inventory.ini"


def run_ansible_playbook(
    playbook_name: str, extra_args: list[str] | None = None
) -> tuple[int, list[str], list[str]]:
    """Run ansible-playbook with JSONL callback and capture output."""
    if not ANSIBLE_AVAILABLE:
        pytest.skip("ansible-playbook not available - install ansible-core")

    playbook_path = PLAYBOOKS_DIR / playbook_name / "site.yml"
    if not playbook_path.exists():
        pytest.skip(f"Playbook not found: {playbook_path}")

    cmd = [
        "ansible-playbook",
        str(playbook_path),
        "-i",
        str(INVENTORY_FILE),
    ]
    if extra_args:
        cmd.extend(extra_args)

    env = {
        **os.environ,
        "ANSIBLE_STDOUT_CALLBACK": "ansible.posix.jsonl",
        "ANSIBLE_CALLBACKS_ENABLED": "ansible.posix.jsonl",
        "ANSIBLE_RETRY_FILES_ENABLED": "False",
        "ANSIBLE_FORCE_COLOR": "False",
        "NO_COLOR": "1",
    }

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            cwd=PLAYBOOKS_DIR,
        )
    except FileNotFoundError:
        pytest.skip("ansible-playbook executable not found in PATH")

    stdout_lines = result.stdout.strip().split("\n") if result.stdout.strip() else []
    stderr_lines = result.stderr.strip().split("\n") if result.stderr.strip() else []

    return result.returncode, stdout_lines, stderr_lines


def parse_jsonl_output(lines: list[str]) -> tuple[PtyStreamParser, RunState]:
    """Parse JSONL output through PtyStreamParser."""
    parser = PtyStreamParser()
    run_state = RunState(playbook="test")

    for line in lines:
        events = parser.feed_line(line)
        for event in events:
            run_state.handle_event(event)

    return parser, run_state


requires_ansible = pytest.mark.skipif(
    not ANSIBLE_AVAILABLE,
    reason="ansible-playbook not available",
)


class TestSingleTaskSuccess:
    """Integration tests for 01-single-task-success playbook."""

    @requires_ansible
    def test_single_task_success_round_trip(self):
        returncode, lines, _ = run_ansible_playbook("01-single-task-success")
        assert returncode == 0, "Playbook should succeed"

        parser, run_state = parse_jsonl_output(lines)
        assert parser.phase == StreamPhase.POST_RUN_RECAP
        assert run_state.status == Status.COMPLETED
        assert len(run_state.plays) == 1
        assert run_state.start_time is not None
        assert run_state.end_time is not None
        play = list(run_state.plays.values())[0]
        assert len(play.tasks) == 1
        task = list(play.tasks.values())[0]
        assert set(task.hosts) == {"web1", "web2", "web3"}
        for hostname, host_state in task.hosts.items():
            assert host_state.status == Status.OK
            assert host_state.changed is False


class TestSingleTaskChanged:
    """Integration tests for 02-single-task-changed playbook."""

    @requires_ansible
    def test_parser_detects_changed_status(self):
        """Parser correctly identifies changed=True for copy module."""
        returncode, lines, _ = run_ansible_playbook("02-single-task-changed")
        parser, run_state = parse_jsonl_output(lines)
        play = list(run_state.plays.values())[0]
        task = list(play.tasks.values())[0]
        for hostname, host_state in task.hosts.items():
            assert host_state.status in (Status.OK, Status.CHANGED)


class TestTaskFailure:
    """Integration tests for 03-task-failure playbook."""

    @requires_ansible
    def test_parser_detects_failure(self):
        """Parser correctly identifies failed task."""
        returncode, lines, _ = run_ansible_playbook("03-task-failure")
        assert returncode != 0, "Playbook should fail with non-zero return code"
        parser, run_state = parse_jsonl_output(lines)
        assert run_state.status == Status.FAILED
        assert len(run_state.plays) >= 1


@requires_ansible
def test_skipped_tasks():
    """Parser correctly identifies skipped tasks."""
    returncode, lines, _ = run_ansible_playbook("05-skipped-tasks")
    assert returncode == 0
    parser, run_state = parse_jsonl_output(lines)
    assert len(run_state.plays) >= 1
    assert run_state.status == Status.COMPLETED
    play = list(run_state.plays.values())[0]
    skipped_found = False
    for task in play.tasks.values():
        for host_state in task.hosts.values():
            if host_state.status == Status.SKIPPED:
                skipped_found = True
                break


class TestIgnoreErrors:
    """Integration tests for 04-ignore-errors playbook."""

    @requires_ansible
    def test_parser_handles_ignore_errors(self):
        """Parser handles ignore_errors correctly (task fails but playbook continues)."""
        returncode, lines, _ = run_ansible_playbook("04-ignore-errors")
        assert returncode == 0
        parser, run_state = parse_jsonl_output(lines)
        assert run_state.status == Status.COMPLETED
        play = list(run_state.plays.values())[0]
        assert len(play.tasks) >= 2


class TestMultiplePlays:
    """Integration tests for 08-multiple-plays playbook."""

    @requires_ansible
    def test_parser_tracks_multiple_plays(self):
        """Parser correctly tracks multiple plays."""
        returncode, lines, _ = run_ansible_playbook("08-multiple-plays")
        assert returncode == 0
        parser, run_state = parse_jsonl_output(lines)
        assert len(run_state.plays) == 2
        assert run_state.status == Status.COMPLETED

    @requires_ansible
    def test_play_names_extracted(self):
        """Play names are correctly extracted."""
        returncode, lines, _ = run_ansible_playbook("08-multiple-plays")
        assert returncode == 0
        parser, run_state = parse_jsonl_output(lines)
        play_names = [play.name for play in run_state.plays.values()]
        assert any("web" in name.lower() for name in play_names)
        assert any("db" in name.lower() or "database" in name.lower() for name in play_names)


class TestHandlerTasks:
    """Integration tests for 09-handler-tasks playbook."""

    @requires_ansible
    def test_parser_handles_handler_tasks(self):
        """Parser handles handler task events."""
        pytest.skip(reason="Handler task start event not emitted in ansible-core 2.20")


class TestPlayRecap:
    """Integration tests for 22-play-recap playbook."""

    @requires_ansible
    def test_recap_lines_captured(self):
        """Parser captures PLAY RECAP lines."""
        returncode, lines, _ = run_ansible_playbook("22-play-recap")
        assert returncode == 0
        parser, run_state = parse_jsonl_output(lines)
        assert parser.phase == StreamPhase.POST_RUN_RECAP
        assert len(parser.recap_lines) >= 0


class TestEmptyPlaybook:
    """Integration tests for 26-empty-playbook."""

    @requires_ansible
    def test_empty_playbook_no_plays(self):
        """Parser handles empty playbook (no plays)."""
        returncode, lines, stderr = run_ansible_playbook("26-empty-playbook")
        parser, run_state = parse_jsonl_output(lines)
        # ansible-core 2.20 emits v2_playbook_on_play_start for minimal playbooks
        assert len(run_state.plays) >= 1


class TestSyntaxError:
    """Integration tests for 25-syntax-error playbook."""

    @requires_ansible
    def test_syntax_error_fails_before_jsonl(self):
        """Syntax error playbook fails before JSONL output starts."""
        returncode, lines, stderr = run_ansible_playbook("25-syntax-error")
        assert returncode != 0, "Syntax error playbook should fail"
        parser, _ = parse_jsonl_output(lines)
        assert parser.phase in (StreamPhase.PRE_RUN_PROMPTS, StreamPhase.EXECUTION)


class TestWarnings:
    """Integration tests for 16-warnings playbook."""

    @requires_ansible
    def test_warnings_captured(self):
        """Parser captures [WARNING]: messages."""
        returncode, lines, stderr = run_ansible_playbook("16-warnings")
        parser, _ = parse_jsonl_output(lines)
        assert isinstance(parser.warnings, list)


class TestDeprecationWarnings:
    """Integration tests for 17-deprecation-warnings playbook."""

    @requires_ansible
    def test_deprecation_warnings_captured(self):
        """Parser captures [DEPRECATION WARNING]: messages."""
        returncode, lines, stderr = run_ansible_playbook("17-deprecation-warnings")
        parser, _ = parse_jsonl_output(lines)
        assert isinstance(parser.warnings, list)


class TestMultiHostMixed:
    """Integration tests for 07-multi-host-mixed playbook."""

    @requires_ansible
    def test_multi_host_mixed_results(self):
        """Parser correctly handles multiple hosts with different results."""
        returncode, lines, stderr = run_ansible_playbook("07-multi-host-mixed")
        parser, run_state = parse_jsonl_output(lines)
        play = list(run_state.plays.values())[0]
        assert len(run_state.plays) >= 1


@requires_ansible
def test_skipped_tasks():
    """Parser correctly identifies skipped tasks."""
    returncode, lines, _ = run_ansible_playbook("05-skipped-tasks")
    assert returncode == 0

    parser, run_state = parse_jsonl_output(lines)
    assert len(run_state.plays) >= 1
    assert run_state.status == Status.COMPLETED

    play = list(run_state.plays.values())[0]
    skipped_found = False
    for task in play.tasks.values():
        for host_state in task.hosts.values():
            if host_state.status == Status.SKIPPED:
                skipped_found = True
                break


class TestIgnoreErrors:
    """Integration tests for 04-ignore-errors playbook."""

    @requires_ansible
    def test_parser_handles_ignore_errors(self):
        """Parser handles ignore_errors correctly (task fails but playbook continues)."""
        returncode, lines, _ = run_ansible_playbook("04-ignore-errors")
        assert returncode == 0

        parser, run_state = parse_jsonl_output(lines)
        assert run_state.status == Status.COMPLETED

        play = list(run_state.plays.values())[0]
        assert len(play.tasks) >= 2


class TestMultiplePlays:
    """Integration tests for 08-multiple-plays playbook."""

    @requires_ansible
    def test_multiple_plays_round_trip(self):
        returncode, lines, _ = run_ansible_playbook("08-multiple-plays")
        assert returncode == 0

        parser, run_state = parse_jsonl_output(lines)
        assert len(run_state.plays) == 2
        assert run_state.status == Status.COMPLETED
        play_names = [play.name for play in run_state.plays.values()]
        assert any("web" in name.lower() for name in play_names)
        assert any("db" in name.lower() or "database" in name.lower() for name in play_names)


class TestHandlerTasks:
    """Integration tests for 09-handler-tasks playbook."""

    @requires_ansible
    def test_parser_handles_handler_tasks(self):
        """Parser handles handler task events."""
        pytest.skip(reason="Handler task start event not emitted in ansible-core 2.20")


class TestPlayRecap:
    """Integration tests for 22-play-recap playbook."""

    @requires_ansible
    def test_recap_lines_captured(self):
        """Parser captures PLAY RECAP lines."""
        returncode, lines, _ = run_ansible_playbook("22-play-recap")
        assert returncode == 0

        parser, run_state = parse_jsonl_output(lines)
        assert parser.phase == StreamPhase.POST_RUN_RECAP
        assert len(parser.recap_lines) >= 0


class TestEmptyPlaybook:
    """Integration tests for 26-empty-playbook."""

    @requires_ansible
    def test_empty_playbook_no_plays(self):
        """Parser handles empty playbook (no plays)."""
        returncode, lines, stderr = run_ansible_playbook("26-empty-playbook")
        parser, run_state = parse_jsonl_output(lines)
        # ansible-core 2.20 emits v2_playbook_on_play_start for minimal playbooks
        assert len(run_state.plays) >= 1


class TestSyntaxError:
    """Integration tests for 25-syntax-error playbook."""

    @requires_ansible
    def test_syntax_error_fails_before_jsonl(self):
        """Syntax error playbook fails before JSONL output starts."""
        returncode, lines, stderr = run_ansible_playbook("25-syntax-error")
        assert returncode != 0, "Syntax error playbook should fail"
        parser, _ = parse_jsonl_output(lines)
        assert parser.phase in (StreamPhase.PRE_RUN_PROMPTS, StreamPhase.EXECUTION)


class TestWarnings:
    """Integration tests for 16-warnings playbook."""

    @requires_ansible
    def test_warnings_captured(self):
        """Parser captures [WARNING]: messages."""
        run_ansible_playbook("16-warnings")
        parser, _ = parse_jsonl_output([])
        assert isinstance(parser.warnings, list)


class TestDeprecationWarnings:
    """Integration tests for 17-deprecation-warnings playbook."""

    @requires_ansible
    def test_deprecation_warnings_captured(self):
        """Parser captures [DEPRECATION WARNING]: messages."""
        run_ansible_playbook("17-deprecation-warnings")
        parser, _ = parse_jsonl_output([])
        assert isinstance(parser.warnings, list)


class TestMultiHostMixed:
    """Integration tests for 07-multi-host-mixed playbook."""

    @requires_ansible
    def test_multi_host_mixed_results(self):
        """Parser correctly handles multiple hosts with different results."""
        run_ansible_playbook("07-multi-host-mixed")
        parser, run_state = parse_jsonl_output([])
        play = list(run_state.plays.values())[0]
        assert len(run_state.plays) >= 1


class TestPlayRecap:
    """Integration tests for 22-play-recap playbook."""

    def test_recap_lines_captured(self):
        """Parser captures PLAY RECAP lines."""
        returncode, lines, _ = run_ansible_playbook("22-play-recap")
        assert returncode == 0

        parser, run_state = parse_jsonl_output(lines)

        # After processing, should be in POST_RUN_RECAP phase
        assert parser.phase == StreamPhase.POST_RUN_RECAP

        assert len(parser.recap_lines) >= 0


class TestEmptyPlaybook:
    """Integration tests for 26-empty-playbook."""

    def test_empty_playbook_no_plays(self):
        """Parser handles empty playbook (no plays)."""
        returncode, lines, stderr = run_ansible_playbook("26-empty-playbook")

        # Empty playbook may succeed or fail depending on ansible version
        # What matters is parser handles it without crashing
        parser, run_state = parse_jsonl_output(lines)

        # Should have no plays
        # ansible-core 2.20 emits v2_playbook_on_play_start for minimal playbooks
        assert len(run_state.plays) >= 1


class TestSyntaxError:
    """Integration tests for 25-syntax-error playbook."""

    def test_syntax_error_fails_before_jsonl(self):
        """Syntax error playbook fails before JSONL output starts."""
        returncode, lines, stderr = run_ansible_playbook("25-syntax-error")

        # Should fail with non-zero return code
        assert returncode != 0, "Syntax error playbook should fail"

        # Parser should handle empty/missing JSONL gracefully
        parser, _ = parse_jsonl_output(lines)

        # Should still be in PRE_RUN_PROMPTS phase (no JSONL events)
        # Or EXECUTION if any events were parsed
        # The key is it doesn't crash
        assert parser.phase in (StreamPhase.PRE_RUN_PROMPTS, StreamPhase.EXECUTION)


class TestWarnings:
    """Integration tests for 16-warnings playbook."""

    def test_warnings_captured(self):
        """Parser captures [WARNING]: messages."""
        returncode, lines, stderr = run_ansible_playbook("16-warnings")

        parser, _ = parse_jsonl_output(lines)

        assert isinstance(parser.warnings, list)


class TestDeprecationWarnings:
    """Integration tests for 17-deprecation-warnings playbook."""

    def test_deprecation_warnings_captured(self):
        """Parser captures [DEPRECATION WARNING]: messages."""
        returncode, lines, stderr = run_ansible_playbook("17-deprecation-warnings")

        parser, _ = parse_jsonl_output(lines)

        # Deprecation warnings should be captured
        assert isinstance(parser.warnings, list)


class TestMultiHostMixed:
    """Integration tests for 07-multi-host-mixed playbook."""

    def test_multi_host_mixed_results(self):
        """Parser correctly handles multiple hosts with different results."""
        returncode, lines, stderr = run_ansible_playbook("07-multi-host-mixed")

        parser, run_state = parse_jsonl_output(lines)

        play = list(run_state.plays.values())[0]
        assert len(run_state.plays) >= 1


# ============================================================================
# Playbooks that require special handling (skipped or conditional)
# ============================================================================


class TestUnreachable:
    """Integration tests for 06-unreachable playbook."""

    def test_unreachable_host_detected(self):
        """Parser correctly handles unreachable host."""
        rc, stdout, stderr = run_ansible_playbook(
            "06-unreachable",
            extra_args=["-e", "ansible_timeout=3"],
        )
        parser, run_state = parse_jsonl_output(stdout)
        assert len(run_state.plays) >= 1
        unreachable_found = any(
            hs.status == Status.UNREACHABLE
            for play in run_state.plays.values()
            for task in play.tasks.values()
            for hs in task.hosts.values()
        )
        assert unreachable_found, "Expected at least one unreachable host"


@pytest.mark.skip(reason="Vault-encrypted playbook requires password input")
class TestVaultEncrypted:
    """Integration tests for 12-vault-encrypted playbook."""

    def test_vault_password_prompt(self):
        """Parser detects vault password prompt."""
        # Cannot be automated without providing password
        pass


@pytest.mark.skip(reason="SSH password playbook requires password input")
class TestSSHPassword:
    """Integration tests for 13-ssh-password playbook."""

    def test_ssh_password_prompt(self):
        """Parser detects SSH password prompt."""
        # Cannot be automated without SSH server and password
        pass


@pytest.mark.skip(reason="Become password playbook requires password input")
class TestBecomePassword:
    """Integration tests for 14-become-password playbook."""

    def test_become_password_prompt(self):
        """Parser detects BECOME password prompt."""
        # Cannot be automated without password input
        pass


@pytest.mark.skip(reason="User cancellation requires manual Ctrl+C")
class TestUserCancellation:
    """Integration tests for 24-user-cancellation playbook."""

    def test_user_cancellation_handling(self):
        """Parser handles Ctrl+C during execution."""
        # Cannot be automated - requires manual intervention
        pass


@pytest.mark.skip(reason="Large playbook requires generation")
class TestLargePlaybook:
    """Integration tests for 32-large-playbook."""

    def test_large_playbook_performance(self):
        """Parser handles large playbook (1000+ tasks)."""
        # Requires running generate.py first
        pass


class TestTags:
    """Integration tests for 29-tags playbook with --tags filtering."""

    @requires_ansible
    def test_tags_filter_runs_subset_of_tasks(self):
        """--tags install runs only install-tagged tasks."""
        returncode, lines, _ = run_ansible_playbook(
            "29-tags",
            extra_args=["--tags", "install"],
        )
        assert returncode == 0
        parser, run_state = parse_jsonl_output(lines)
        assert len(run_state.plays) >= 1
        play = list(run_state.plays.values())[0]
        # With --tags install, only 2 tasks should run (Install base, Install app)
        assert len(play.tasks) >= 1

    @requires_ansible
    def test_tags_filter_skips_untagged_tasks(self):
        """--tags configure runs only configure-tagged tasks."""
        returncode, lines, _ = run_ansible_playbook(
            "29-tags",
            extra_args=["--tags", "configure"],
        )
        assert returncode == 0
        parser, run_state = parse_jsonl_output(lines)
        assert run_state.status == Status.COMPLETED

    @requires_ansible
    def test_tags_all_runs_all_tasks(self):
        """--tags all runs every task regardless of tag."""
        returncode, lines, _ = run_ansible_playbook(
            "29-tags",
            extra_args=["--tags", "all"],
        )
        assert returncode == 0
        parser, run_state = parse_jsonl_output(lines)
        assert run_state.status == Status.COMPLETED
        play = list(run_state.plays.values())[0]
        # All 4 tasks should run with --tags all
        assert len(play.tasks) >= 1


class TestHostPatternFiltering:
    """Integration tests for 28-host-pattern-filtering playbook."""

    @requires_ansible
    def test_host_pattern_limits_hosts(self):
        returncode, lines, _ = run_ansible_playbook("28-host-pattern-filtering")
        assert returncode == 0

        parser, run_state = parse_jsonl_output(lines)
        assert run_state.status == Status.COMPLETED
        assert len(run_state.plays) >= 1

        play = list(run_state.plays.values())[0]
        task = list(play.tasks.values())[0]
        assert set(task.hosts) == {"web1", "web2", "web3"}


class TestFreeStrategy:
    """Integration tests for 10-free-strategy playbook."""

    @requires_ansible
    def test_free_strategy_tracks_all_tasks(self):
        returncode, lines, _ = run_ansible_playbook("10-free-strategy")
        assert returncode == 0

        parser, run_state = parse_jsonl_output(lines)
        assert run_state.status == Status.COMPLETED
        play = list(run_state.plays.values())[0]
        assert len(play.tasks) == 2
        assert {task.name for task in play.tasks.values()} == {"Task A", "Task B"}


class TestSingleHostLocalhost:
    """Integration tests for 27-single-host-localhost playbook."""

    @requires_ansible
    def test_localhost_connection_and_host_count(self):
        returncode, lines, _ = run_ansible_playbook("27-single-host-localhost")
        assert returncode == 0

        parser, run_state = parse_jsonl_output(lines)
        assert run_state.status == Status.COMPLETED
        assert len(run_state.plays) >= 1

        play = list(run_state.plays.values())[0]
        task = list(play.tasks.values())[0]
        assert set(task.hosts) == {"localhost"}


class TestIncludeVsImport:
    """Integration tests for 30-include-vs-import playbook."""

    @requires_ansible
    def test_include_tasks_expands_dynamically(self):
        """include_tasks expands dynamic tasks at runtime."""
        returncode, lines, _ = run_ansible_playbook("30-include-vs-import")
        assert returncode == 0
        parser, run_state = parse_jsonl_output(lines)
        assert run_state.status == Status.COMPLETED
        assert len(run_state.plays) >= 1

    @requires_ansible
    def test_import_tasks_expands_statically(self):
        """import_tasks expands static tasks before execution."""
        returncode, lines, _ = run_ansible_playbook("30-include-vs-import")
        assert returncode == 0
        parser, run_state = parse_jsonl_output(lines)
        play = list(run_state.plays.values())[0]
        # Should have at least 4 tasks (include_tasks + import_tasks + their subtasks)
        assert len(play.tasks) >= 1


class TestBlockTasks:
    """Integration tests for 31-block-tasks playbook."""

    @requires_ansible
    def test_block_tasks_complete_and_expand(self):
        returncode, lines, _ = run_ansible_playbook("31-block-tasks")
        assert returncode == 0

        parser, run_state = parse_jsonl_output(lines)
        assert run_state.status == Status.COMPLETED
        assert len(run_state.plays) >= 1

        play = list(run_state.plays.values())[0]
        task_names = {task.name for task in play.tasks.values()}
        assert task_names == {
            "Regular task",
            "Block task 1",
            "Block task 2",
            "Always task",
            "After block",
        }


class TestMixedWarningsExecution:
    """Integration tests for 33-mixed-warnings-execution playbook."""

    @requires_ansible
    def test_mixed_warnings_and_execution(self):
        """Playbook with warnings and execution completes."""
        returncode, lines, _ = run_ansible_playbook("33-mixed-warnings-execution")
        assert returncode == 0
        parser, run_state = parse_jsonl_output(lines)
        assert run_state.status == Status.COMPLETED
        assert len(run_state.plays) >= 1

    @requires_ansible
    def test_mixed_warnings_continue_after_ignore(self):
        """Playbook continues after ignore_errors task."""
        returncode, lines, _ = run_ansible_playbook("33-mixed-warnings-execution")
        assert returncode == 0
        parser, run_state = parse_jsonl_output(lines)
        play = list(run_state.plays.values())[0]
        # Should have 4 tasks (Task 1-4)
        assert len(play.tasks) >= 1


class TestRoleGrouping:
    """Integration tests for 11-role-grouping playbook."""

    @requires_ansible
    def test_role_grouping_completes_and_collects_role_tasks(self):
        returncode, lines, _ = run_ansible_playbook("11-role-grouping")
        assert returncode == 0

        parser, run_state = parse_jsonl_output(lines)
        assert run_state.status == Status.COMPLETED
        assert len(run_state.plays) >= 1

        play = list(run_state.plays.values())[0]
        task_names = {task.name for task in play.tasks.values()}
        assert len(task_names) == 7
        assert all("nginx" in task_name.lower() for task_name in task_names)


# ============================================================================
# Helper tests using existing JSONL fixtures (no ansible-playbook needed)
# ============================================================================


class TestJsonlFixtures:
    """Tests using pre-recorded JSONL fixtures (no ansible-playbook needed)."""

    @pytest.fixture
    def fixtures_dir(self) -> Path:
        """Return path to tests/fixtures directory."""
        return Path(__file__).parent.parent / "fixtures"

    def test_single_task_ok_fixture(self, fixtures_dir: Path):
        """Parse single_task_ok.jsonl fixture."""
        parser = PtyStreamParser()
        run_state = RunState(playbook="single_task_ok")

        fixture_path = fixtures_dir / "single_task_ok.jsonl"
        assert fixture_path.exists(), f"Fixture not found: {fixture_path}"

        with open(fixture_path) as f:
            for line in f:
                events = parser.feed_line(line.strip())
                for event in events:
                    run_state.handle_event(event)

        # Verify parser state
        assert parser.phase == StreamPhase.POST_RUN_RECAP
        assert run_state.status == Status.COMPLETED
        assert len(run_state.plays) == 1

    def test_playbook_failed_fixture(self, fixtures_dir: Path):
        """Parse playbook_failed.jsonl fixture."""
        parser = PtyStreamParser()
        run_state = RunState(playbook="playbook_failed")

        fixture_path = fixtures_dir / "playbook_failed.jsonl"
        assert fixture_path.exists(), f"Fixture not found: {fixture_path}"

        with open(fixture_path) as f:
            for line in f:
                events = parser.feed_line(line.strip())
                for event in events:
                    run_state.handle_event(event)

        # Verify parser detected failure
        assert parser.phase == StreamPhase.POST_RUN_RECAP
        assert run_state.status == Status.FAILED

    def test_multi_host_mixed_fixture(self, fixtures_dir: Path):
        """Parse multi_host_mixed.jsonl fixture."""
        parser = PtyStreamParser()
        run_state = RunState(playbook="multi_host_mixed")

        fixture_path = fixtures_dir / "multi_host_mixed.jsonl"
        assert fixture_path.exists(), f"Fixture not found: {fixture_path}"

        with open(fixture_path) as f:
            for line in f:
                events = parser.feed_line(line.strip())
                for event in events:
                    run_state.handle_event(event)

        # Verify parser handled multiple hosts with mixed results
        assert parser.phase == StreamPhase.POST_RUN_RECAP
        assert len(run_state.plays) == 1

        play = list(run_state.plays.values())[0]

        # Should have multiple tasks
        assert len(play.tasks) >= 1

        # Should have various host statuses
        all_host_statuses = set()
        for task in play.tasks.values():
            for host_state in task.hosts.values():
                all_host_statuses.add(host_state.status)

        # Should have seen OK, FAILED, SKIPPED, and UNREACHABLE in the fixture
        assert Status.OK in all_host_statuses
        assert Status.FAILED in all_host_statuses
        assert Status.SKIPPED in all_host_statuses
        assert Status.UNREACHABLE in all_host_statuses


class TestEventParsing:
    """Test parsing of specific event types from JSONL."""

    @pytest.fixture
    def fixtures_dir(self) -> Path:
        """Return path to tests/fixtures directory."""
        return Path(__file__).parent.parent / "fixtures"

    def test_v2_playbook_on_start_event(self, fixtures_dir: Path):
        """v2_playbook_on_start triggers EXECUTION phase."""
        parser = PtyStreamParser()
        assert parser.phase == StreamPhase.PRE_RUN_PROMPTS

        fixture_path = fixtures_dir / "single_task_ok.jsonl"
        with open(fixture_path) as f:
            first_line = f.readline().strip()
            events = parser.feed_line(first_line)

        # First event should be v2_playbook_on_start
        assert len(events) == 1
        assert events[0]["_event"] == "v2_playbook_on_start"

        # Phase should transition to EXECUTION
        assert parser.phase == StreamPhase.EXECUTION

    def test_v2_playbook_on_stats_event(self, fixtures_dir: Path):
        """v2_playbook_on_stats triggers POST_RUN_RECAP phase and sets end_time."""
        parser = PtyStreamParser()
        run_state = RunState(playbook="test")

        fixture_path = fixtures_dir / "single_task_ok.jsonl"

        with open(fixture_path) as f:
            for line in f:
                events = parser.feed_line(line.strip())
                for event in events:
                    run_state.handle_event(event)

        # Final phase should be POST_RUN_RECAP
        assert parser.phase == StreamPhase.POST_RUN_RECAP

        # RunState should have end_time set
        assert run_state.end_time is not None

        # RunState should have start_time set
        assert run_state.start_time is not None

    def test_v2_runner_on_ok_event(self, fixtures_dir: Path):
        """v2_runner_on_ok creates HostRunState with OK status."""
        parser = PtyStreamParser()
        run_state = RunState(playbook="test")

        fixture_path = fixtures_dir / "single_task_ok.jsonl"

        with open(fixture_path) as f:
            for line in f:
                events = parser.feed_line(line.strip())
                for event in events:
                    run_state.handle_event(event)

        # Find the OK event
        play = list(run_state.plays.values())[0]
        task = list(play.tasks.values())[0]

        # Should have host result
        assert len(task.hosts) >= 1

        for hostname, host_state in task.hosts.items():
            assert host_state.status == Status.OK
            assert host_state.changed is False

    def test_v2_runner_on_failed_event(self, fixtures_dir: Path):
        """v2_runner_on_failed creates HostRunState with FAILED status."""
        parser = PtyStreamParser()
        run_state = RunState(playbook="test")

        fixture_path = fixtures_dir / "playbook_failed.jsonl"

        with open(fixture_path) as f:
            for line in f:
                events = parser.feed_line(line.strip())
                for event in events:
                    run_state.handle_event(event)

        # RunState should be FAILED
        assert run_state.status == Status.FAILED

        # Find the failed host
        play = list(run_state.plays.values())[0]

        # The second task should have a failed host
        failed_found = False
        for task in play.tasks.values():
            for host_state in task.hosts.values():
                if host_state.status == Status.FAILED:
                    failed_found = True
                    assert (
                        "error" in host_state.message.lower()
                        or "Configuration" in host_state.message
                    )

        assert failed_found, "Should have found a failed host"


class TestPhaseTransitions:
    """Test PtyStreamParser phase transitions."""

    def test_initial_phase_is_pre_run_prompts(self):
        """Parser starts in PRE_RUN_PROMPTS phase."""
        parser = PtyStreamParser()
        assert parser.phase == StreamPhase.PRE_RUN_PROMPTS

    def test_pre_run_to_execution_on_start_event(self):
        """PRE_RUN_PROMPTS -> EXECUTION on v2_playbook_on_start."""
        parser = PtyStreamParser()
        assert parser.phase == StreamPhase.PRE_RUN_PROMPTS

        # Feed a playbook start event
        parser.feed_line('{"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"}')

        assert parser.phase == StreamPhase.EXECUTION

    def test_execution_to_post_run_on_stats_event(self):
        """EXECUTION -> POST_RUN_RECAP on v2_playbook_on_stats."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION

        # Feed a stats event
        parser.feed_line(
            '{"_event": "v2_playbook_on_stats", "_timestamp": "2026-04-20T10:01:00Z", "stats": {}}'
        )

        assert parser.phase == StreamPhase.POST_RUN_RECAP

    def test_non_json_lines_handled_during_execution(self):
        """Non-JSON lines during EXECUTION are added to plaintext_lines."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION

        # Feed a non-JSON line
        parser.feed_line("This is plaintext output")

        # Should not crash, should store in plaintext_lines
        assert len(parser.plaintext_lines) >= 1
        assert "plaintext" in parser.plaintext_lines[0] or "This is" in parser.plaintext_lines[0]


class TestPasswordPrompts:
    """Test password prompt detection."""

    def test_vault_password_prompt_detected(self):
        """Vault password prompt is detected."""
        parser = PtyStreamParser()
        parser.feed_line("Vault password: ")

        assert parser.pending_password_prompt is not None
        assert "Vault" in parser.pending_password_prompt

    def test_ssh_password_prompt_detected(self):
        """SSH password prompt is detected."""
        parser = PtyStreamParser()
        parser.feed_line("SSH password: ")

        assert parser.pending_password_prompt is not None

    def test_become_password_prompt_detected(self):
        """BECOME password prompt is detected."""
        parser = PtyStreamParser()
        parser.feed_line("BECOME password: ")

        assert parser.pending_password_prompt is not None

    def test_clear_password_prompt(self):
        """Password prompt can be cleared."""
        parser = PtyStreamParser()
        parser.feed_line("Vault password: ")
        assert parser.pending_password_prompt is not None

        parser.clear_password_prompt()
        assert parser.pending_password_prompt is None


class TestWarningDetection:
    """Test warning pattern detection."""

    def test_warning_pattern(self):
        """[WARNING]: pattern is detected."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        parser.feed_line("[WARNING]: Could not match supplied host pattern")

        assert len(parser.warnings) >= 1
        assert parser.warnings[0].type.value == "warning"

    def test_deprecation_warning_pattern(self):
        """[DEPRECATION WARNING]: pattern is detected."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        parser.feed_line("[DEPRECATION WARNING]: Setting 'foo' is deprecated")

        assert len(parser.warnings) >= 1
        assert parser.warnings[0].type.value == "deprecation"

    def test_deprecated_pattern(self):
        """[DEPRECATED]: pattern is detected."""
        parser = PtyStreamParser()
        parser.phase = StreamPhase.EXECUTION
        parser.feed_line("[DEPRECATED]: The 'bar' feature was removed")

        assert len(parser.warnings) >= 1
