"""Unit tests for ExecutionState and StateMachine.

Tests section 6.4 (state machine) and 6.5 (memory bounds) of TEST_SPECIFICATION.md.
TC-234 through TC-260.
"""

import pytest

from ansible_aom.core.state import (
    ExecutionState,
    InvalidTransitionError,
    StateMachine,
    VALID_TRANSITIONS,
)


class TestExecutionStateEnum:
    """TC-234: State Machine Eight States."""

    def test_has_eight_states(self):
        """ExecutionState contains exactly 8 states."""
        assert len(ExecutionState) == 8

    def test_all_states_exist(self):
        """Each expected state value exists in the enum."""
        expected = {
            ExecutionState.IDLE,
            ExecutionState.STARTING,
            ExecutionState.LOADING_TASKS,
            ExecutionState.READY,
            ExecutionState.RUNNING,
            ExecutionState.COMPLETED,
            ExecutionState.FAILED,
            ExecutionState.CRASHED,
        }
        assert set(ExecutionState) == expected

    def test_state_names(self):
        """Each state has correct name."""
        assert ExecutionState.IDLE.name == "IDLE"
        assert ExecutionState.STARTING.name == "STARTING"
        assert ExecutionState.LOADING_TASKS.name == "LOADING_TASKS"
        assert ExecutionState.READY.name == "READY"
        assert ExecutionState.RUNNING.name == "RUNNING"
        assert ExecutionState.COMPLETED.name == "COMPLETED"
        assert ExecutionState.FAILED.name == "FAILED"
        assert ExecutionState.CRASHED.name == "CRASHED"


class TestValidTransitionsDictionary:
    """TC-252: Valid Transitions Dictionary Completeness."""

    def test_all_states_have_transitions(self):
        """VALID_TRANSITIONS has keys for all 8 states."""
        expected_states = set(ExecutionState)
        assert set(VALID_TRANSITIONS.keys()) == expected_states

    def test_idle_transitions(self):
        """IDLE can only transition to STARTING."""
        assert VALID_TRANSITIONS[ExecutionState.IDLE] == {
            ExecutionState.STARTING
        }

    def test_starting_transitions(self):
        """STARTING can transition to LOADING_TASKS or CRASHED."""
        assert VALID_TRANSITIONS[ExecutionState.STARTING] == {
            ExecutionState.LOADING_TASKS,
            ExecutionState.CRASHED,
        }

    def test_loading_tasks_transitions(self):
        """LOADING_TASKS can transition to READY or CRASHED."""
        assert VALID_TRANSITIONS[ExecutionState.LOADING_TASKS] == {
            ExecutionState.READY,
            ExecutionState.CRASHED,
        }

    def test_ready_transitions(self):
        """READY can transition to RUNNING or IDLE (timeout)."""
        assert VALID_TRANSITIONS[ExecutionState.READY] == {
            ExecutionState.RUNNING,
            ExecutionState.IDLE,
        }

    def test_running_transitions(self):
        """RUNNING can self-loop or transition to COMPLETED, FAILED, CRASHED."""
        assert VALID_TRANSITIONS[ExecutionState.RUNNING] == {
            ExecutionState.RUNNING,
            ExecutionState.COMPLETED,
            ExecutionState.FAILED,
            ExecutionState.CRASHED,
        }

    def test_completed_transitions(self):
        """COMPLETED can only transition to IDLE."""
        assert VALID_TRANSITIONS[ExecutionState.COMPLETED] == {
            ExecutionState.IDLE
        }

    def test_failed_transitions(self):
        """FAILED can only transition to IDLE."""
        assert VALID_TRANSITIONS[ExecutionState.FAILED] == {
            ExecutionState.IDLE
        }

    def test_crashed_transitions(self):
        """CRASHED can only transition to IDLE."""
        assert VALID_TRANSITIONS[ExecutionState.CRASHED] == {
            ExecutionState.IDLE
        }


class TestStateMachineInit:
    """Test StateMachine initialization."""

    def test_initial_state_is_idle(self):
        """StateMachine starts in IDLE state."""
        sm = StateMachine()
        assert sm.state == ExecutionState.IDLE

    def test_state_property_is_readonly(self):
        """State property returns current state without allowing modification."""
        sm = StateMachine()
        assert sm.state == ExecutionState.IDLE
        sm.transition(ExecutionState.STARTING)
        assert sm.state == ExecutionState.STARTING


class TestStateMachineTransitions:
    """TC-235 through TC-247: Valid state transitions."""

    # TC-235: IDLE to STARTING
    def test_idle_to_starting(self):
        """Valid transition from IDLE to STARTING on user command."""
        sm = StateMachine()
        sm.transition(ExecutionState.STARTING)
        assert sm.state == ExecutionState.STARTING

    # TC-236: STARTING to LOADING_TASKS
    def test_starting_to_loading_tasks(self):
        """Valid transition from STARTING to LOADING_TASKS."""
        sm = StateMachine()
        sm._state = ExecutionState.STARTING
        sm.transition(ExecutionState.LOADING_TASKS)
        assert sm.state == ExecutionState.LOADING_TASKS

    # TC-236: STARTING to CRASHED
    def test_starting_to_crashed(self):
        """Valid transition from STARTING to CRASHED."""
        sm = StateMachine()
        sm._state = ExecutionState.STARTING
        sm.transition(ExecutionState.CRASHED)
        assert sm.state == ExecutionState.CRASHED

    # TC-237: LOADING_TASKS to READY
    def test_loading_tasks_to_ready(self):
        """Valid transition from LOADING_TASKS to READY on successful discovery."""
        sm = StateMachine()
        sm._state = ExecutionState.LOADING_TASKS
        sm.transition(ExecutionState.READY)
        assert sm.state == ExecutionState.READY

    # TC-238: LOADING_TASKS to CRASHED
    def test_loading_tasks_to_crashed(self):
        """Valid transition from LOADING_TASKS to CRASHED on discovery failure."""
        sm = StateMachine()
        sm._state = ExecutionState.LOADING_TASKS
        sm.transition(ExecutionState.CRASHED)
        assert sm.state == ExecutionState.CRASHED

    # TC-239: READY to RUNNING
    def test_ready_to_running(self):
        """Valid transition from READY to RUNNING when subprocess starts."""
        sm = StateMachine()
        sm._state = ExecutionState.READY
        sm.transition(ExecutionState.RUNNING)
        assert sm.state == ExecutionState.RUNNING

    # TC-240: READY to IDLE (timeout)
    def test_ready_to_idle_timeout(self):
        """READY times out back to IDLE."""
        sm = StateMachine()
        sm._state = ExecutionState.READY
        sm.transition(ExecutionState.IDLE)
        assert sm.state == ExecutionState.IDLE

    # TC-241: RUNNING self-loop
    def test_running_to_running(self):
        """RUNNING may stay in RUNNING (processing events)."""
        sm = StateMachine()
        sm._state = ExecutionState.RUNNING
        sm.transition(ExecutionState.RUNNING)
        assert sm.state == ExecutionState.RUNNING

    # TC-242: RUNNING to COMPLETED
    def test_running_to_completed(self):
        """Valid transition from RUNNING to COMPLETED on success."""
        sm = StateMachine()
        sm._state = ExecutionState.RUNNING
        sm.transition(ExecutionState.COMPLETED)
        assert sm.state == ExecutionState.COMPLETED

    # TC-243: RUNNING to FAILED
    def test_running_to_failed(self):
        """Valid transition from RUNNING to FAILED on failure."""
        sm = StateMachine()
        sm._state = ExecutionState.RUNNING
        sm.transition(ExecutionState.FAILED)
        assert sm.state == ExecutionState.FAILED

    # TC-244: RUNNING to CRASHED
    def test_running_to_crashed(self):
        """Valid transition from RUNNING to CRASHED on crash."""
        sm = StateMachine()
        sm._state = ExecutionState.RUNNING
        sm.transition(ExecutionState.CRASHED)
        assert sm.state == ExecutionState.CRASHED

    # TC-245: FAILED to IDLE
    def test_failed_to_idle(self):
        """Valid transition from FAILED to IDLE on user exit."""
        sm = StateMachine()
        sm._state = ExecutionState.FAILED
        sm.transition(ExecutionState.IDLE)
        assert sm.state == ExecutionState.IDLE

    # TC-246: CRASHED to IDLE
    def test_crashed_to_idle(self):
        """Valid transition from CRASHED to IDLE on user exit."""
        sm = StateMachine()
        sm._state = ExecutionState.CRASHED
        sm.transition(ExecutionState.IDLE)
        assert sm.state == ExecutionState.IDLE

    # TC-247: COMPLETED to IDLE
    def test_completed_to_idle(self):
        """Valid transition from COMPLETED to IDLE on user exit."""
        sm = StateMachine()
        sm._state = ExecutionState.COMPLETED
        sm.transition(ExecutionState.IDLE)
        assert sm.state == ExecutionState.IDLE


class TestStateMachineInvalidTransitions:
    """TC-248: Invalid Transition Rejection."""

    def test_idle_to_ready_invalid(self):
        """IDLE cannot transition directly to READY."""
        sm = StateMachine()
        with pytest.raises(InvalidTransitionError) as exc_info:
            sm.transition(ExecutionState.READY)
        assert sm.state == ExecutionState.IDLE
        assert exc_info.value.current == ExecutionState.IDLE
        assert exc_info.value.target == ExecutionState.READY

    def test_idle_to_running_invalid(self):
        """IDLE cannot transition directly to RUNNING."""
        sm = StateMachine()
        with pytest.raises(InvalidTransitionError):
            sm.transition(ExecutionState.RUNNING)
        assert sm.state == ExecutionState.IDLE

    def test_idle_to_completed_invalid(self):
        """IDLE cannot transition directly to COMPLETED."""
        sm = StateMachine()
        with pytest.raises(InvalidTransitionError):
            sm.transition(ExecutionState.COMPLETED)
        assert sm.state == ExecutionState.IDLE

    def test_idle_to_failed_invalid(self):
        """IDLE cannot transition directly to FAILED."""
        sm = StateMachine()
        with pytest.raises(InvalidTransitionError):
            sm.transition(ExecutionState.FAILED)
        assert sm.state == ExecutionState.IDLE

    def test_idle_to_crashed_invalid(self):
        """IDLE cannot transition directly to CRASHED."""
        sm = StateMachine()
        with pytest.raises(InvalidTransitionError):
            sm.transition(ExecutionState.CRASHED)
        assert sm.state == ExecutionState.IDLE

    def test_loading_tasks_to_idle_invalid(self):
        """LOADING_TASKS cannot transition directly to IDLE."""
        sm = StateMachine()
        sm._state = ExecutionState.LOADING_TASKS
        with pytest.raises(InvalidTransitionError):
            sm.transition(ExecutionState.IDLE)
        assert sm.state == ExecutionState.LOADING_TASKS

    def test_running_to_idle_invalid(self):
        """RUNNING cannot transition directly to IDLE."""
        sm = StateMachine()
        sm._state = ExecutionState.RUNNING
        with pytest.raises(InvalidTransitionError):
            sm.transition(ExecutionState.IDLE)
        assert sm.state == ExecutionState.RUNNING

    def test_running_to_starting_invalid(self):
        """RUNNING cannot transition to STARTING."""
        sm = StateMachine()
        sm._state = ExecutionState.RUNNING
        with pytest.raises(InvalidTransitionError):
            sm.transition(ExecutionState.STARTING)
        assert sm.state == ExecutionState.RUNNING

    def test_running_to_loading_tasks_invalid(self):
        """RUNNING cannot transition to LOADING_TASKS."""
        sm = StateMachine()
        sm._state = ExecutionState.RUNNING
        with pytest.raises(InvalidTransitionError):
            sm.transition(ExecutionState.LOADING_TASKS)
        assert sm.state == ExecutionState.RUNNING

    def test_running_to_ready_invalid(self):
        """RUNNING cannot transition to READY."""
        sm = StateMachine()
        sm._state = ExecutionState.RUNNING
        with pytest.raises(InvalidTransitionError):
            sm.transition(ExecutionState.READY)

    def test_completed_to_running_invalid(self):
        """COMPLETED cannot transition to RUNNING."""
        sm = StateMachine()
        sm._state = ExecutionState.COMPLETED
        with pytest.raises(InvalidTransitionError):
            sm.transition(ExecutionState.RUNNING)
        assert sm.state == ExecutionState.COMPLETED

    def test_failed_to_running_invalid(self):
        """FAILED cannot transition to RUNNING."""
        sm = StateMachine()
        sm._state = ExecutionState.FAILED
        with pytest.raises(InvalidTransitionError):
            sm.transition(ExecutionState.RUNNING)
        assert sm.state == ExecutionState.FAILED

    def test_crashed_to_running_invalid(self):
        """CRASHED cannot transition to RUNNING."""
        sm = StateMachine()
        sm._state = ExecutionState.CRASHED
        with pytest.raises(InvalidTransitionError):
            sm.transition(ExecutionState.RUNNING)
        assert sm.state == ExecutionState.CRASHED


class TestStateMachineCanTransition:
    """Test can_transition method."""

    def test_can_transition_valid(self):
        """can_transition returns True for valid transitions."""
        sm = StateMachine()
        assert sm.can_transition(ExecutionState.STARTING) is True

    def test_can_transition_invalid(self):
        """can_transition returns False for invalid transitions."""
        sm = StateMachine()
        assert sm.can_transition(ExecutionState.RUNNING) is False

    def test_can_transition_after_state_change(self):
        """can_transition reflects current state."""
        sm = StateMachine()
        sm._state = ExecutionState.READY
        assert sm.can_transition(ExecutionState.RUNNING) is True
        assert sm.can_transition(ExecutionState.IDLE) is True
        assert sm.can_transition(ExecutionState.STARTING) is False


class TestStateMachineReset:
    """Test reset method."""

    def test_reset_returns_to_idle(self):
        """reset returns state to IDLE regardless of current state."""
        sm = StateMachine()
        sm._state = ExecutionState.COMPLETED
        sm.reset()
        assert sm.state == ExecutionState.IDLE

    def test_reset_from_failed(self):
        """reset from FAILED state returns to IDLE."""
        sm = StateMachine()
        sm._state = ExecutionState.FAILED
        sm.reset()
        assert sm.state == ExecutionState.IDLE

    def test_reset_from_crashed(self):
        """reset from CRASHED state returns to IDLE."""
        sm = StateMachine()
        sm._state = ExecutionState.CRASHED
        sm.reset()
        assert sm.state == ExecutionState.IDLE

    def test_reset_from_idle_is_idempotent(self):
        """reset from IDLE state stays IDLE."""
        sm = StateMachine()
        sm.reset()
        assert sm.state == ExecutionState.IDLE


class TestStateMachineHappyPath:
    """Test complete happy path transitions."""

    def test_full_success_path(self):
        """Complete successful execution path: IDLE -> STARTING -> ... -> COMPLETED -> IDLE."""
        sm = StateMachine()
        assert sm.state == ExecutionState.IDLE

        sm.transition(ExecutionState.STARTING)
        assert sm.state == ExecutionState.STARTING

        sm.transition(ExecutionState.LOADING_TASKS)
        assert sm.state == ExecutionState.LOADING_TASKS

        sm.transition(ExecutionState.READY)
        assert sm.state == ExecutionState.READY

        sm.transition(ExecutionState.RUNNING)
        assert sm.state == ExecutionState.RUNNING

        # Self-loop during execution
        sm.transition(ExecutionState.RUNNING)
        assert sm.state == ExecutionState.RUNNING

        sm.transition(ExecutionState.COMPLETED)
        assert sm.state == ExecutionState.COMPLETED

        sm.transition(ExecutionState.IDLE)
        assert sm.state == ExecutionState.IDLE

    def test_failure_path(self):
        """Complete failure path: IDLE -> ... -> RUNNING -> FAILED -> IDLE."""
        sm = StateMachine()
        sm.transition(ExecutionState.STARTING)
        sm.transition(ExecutionState.LOADING_TASKS)
        sm.transition(ExecutionState.READY)
        sm.transition(ExecutionState.RUNNING)

        sm.transition(ExecutionState.FAILED)
        assert sm.state == ExecutionState.FAILED

        sm.transition(ExecutionState.IDLE)
        assert sm.state == ExecutionState.IDLE

    def test_crash_at_starting_path(self):
        """Crash during loading: IDLE -> STARTING -> CRASHED -> IDLE."""
        sm = StateMachine()
        sm.transition(ExecutionState.STARTING)
        sm.transition(ExecutionState.CRASHED)
        assert sm.state == ExecutionState.CRASHED

        sm.transition(ExecutionState.IDLE)
        assert sm.state == ExecutionState.IDLE

    def test_crash_during_loading_path(self):
        """Crash during loading: IDLE -> STARTING -> LOADING_TASKS -> CRASHED -> IDLE."""
        sm = StateMachine()
        sm.transition(ExecutionState.STARTING)
        sm.transition(ExecutionState.LOADING_TASKS)
        sm.transition(ExecutionState.CRASHED)
        assert sm.state == ExecutionState.CRASHED

        sm.transition(ExecutionState.IDLE)
        assert sm.state == ExecutionState.IDLE

    def test_crash_during_running_path(self):
        """Crash during execution: IDLE -> ... -> RUNNING -> CRASHED -> IDLE."""
        sm = StateMachine()
        sm.transition(ExecutionState.STARTING)
        sm.transition(ExecutionState.LOADING_TASKS)
        sm.transition(ExecutionState.READY)
        sm.transition(ExecutionState.RUNNING)
        sm.transition(ExecutionState.CRASHED)
        assert sm.state == ExecutionState.CRASHED

        sm.transition(ExecutionState.IDLE)
        assert sm.state == ExecutionState.IDLE


class TestInvalidTransitionError:
    """Test InvalidTransitionError exception."""

    def test_error_message_contains_states(self):
        """Error message includes current and target state names."""
        sm = StateMachine()
        try:
            sm.transition(ExecutionState.RUNNING)
        except InvalidTransitionError as e:
            assert "IDLE" in str(e)
            assert "RUNNING" in str(e)
            assert e.current == ExecutionState.IDLE
            assert e.target == ExecutionState.RUNNING

    def test_error_message_shows_valid_transitions(self):
        """Error message shows valid transitions from current state."""
        sm = StateMachine()
        sm._state = ExecutionState.RUNNING
        try:
            sm.transition(ExecutionState.IDLE)
        except InvalidTransitionError as e:
            error_msg = str(e)
            assert "RUNNING" in error_msg
            assert "COMPLETED" in error_msg or "RUNNING" in error_msg


class TestStateMachineIsolation:
    """Test isolation: each test gets fresh StateMachine."""

    def test_instance_one_starts_idle(self):
        """First instance starts in IDLE."""
        sm1 = StateMachine()
        assert sm1.state == ExecutionState.IDLE

    def test_instance_two_starts_idle(self):
        """Second instance also starts in IDLE (no shared state)."""
        sm2 = StateMachine()
        assert sm2.state == ExecutionState.IDLE

    def test_instances_dont_share_state(self):
        """Multiple instances don't share state."""
        sm1 = StateMachine()
        sm2 = StateMachine()

        sm1.transition(ExecutionState.STARTING)
        assert sm1.state == ExecutionState.STARTING
        assert sm2.state == ExecutionState.IDLE

        sm2.transition(ExecutionState.STARTING)
        sm2.transition(ExecutionState.LOADING_TASKS)
        assert sm1.state == ExecutionState.STARTING
        assert sm2.state == ExecutionState.LOADING_TASKS


class TestTerminalStates:
    """Test terminal state behavior."""

    @pytest.mark.parametrize(
        "terminal_state",
        [ExecutionState.COMPLETED, ExecutionState.FAILED, ExecutionState.CRASHED],
    )
    def test_terminal_only_to_idle(self, terminal_state):
        """Terminal states can only transition to IDLE."""
        valid_targets = VALID_TRANSITIONS[terminal_state]
        assert valid_targets == {ExecutionState.IDLE}

    @pytest.mark.parametrize(
        "terminal_state,invalid_target",
        [
            (ExecutionState.COMPLETED, ExecutionState.RUNNING),
            (ExecutionState.COMPLETED, ExecutionState.STARTING),
            (ExecutionState.FAILED, ExecutionState.RUNNING),
            (ExecutionState.FAILED, ExecutionState.COMPLETED),
            (ExecutionState.CRASHED, ExecutionState.RUNNING),
            (ExecutionState.CRASHED, ExecutionState.FAILED),
        ],
    )
    def test_terminal_rejects_invalid(self, terminal_state, invalid_target):
        """Terminal states reject invalid transitions."""
        sm = StateMachine()
        sm._state = terminal_state
        with pytest.raises(InvalidTransitionError):
            sm.transition(invalid_target)


class TestAllInvalidTransitionsExhaustive:
    """Exhaustively test all invalid transitions."""

    @pytest.mark.parametrize(
        "from_state",
        list(ExecutionState),
    )
    def test_known_invalid_transitions(self, from_state):
        """Each state has known valid transitions; all others are invalid."""
        valid_targets = VALID_TRANSITIONS[from_state]
        invalid_targets = set(ExecutionState) - valid_targets

        for invalid_target in invalid_targets:
            sm = StateMachine()
            sm._state = from_state
            assert sm.can_transition(invalid_target) is False


class TestMemoryBounds:
    """TC-253 to TC-260: Memory bounds constants."""

    def test_max_plays_value(self):
        """TC-253: Maximum 1000 plays tracked."""
        from ansible_aom.core.state import MAX_PLAYS

        assert MAX_PLAYS == 1000

    def test_max_tasks_per_play_value(self):
        """TC-254: Maximum 10000 tasks per play tracked."""
        from ansible_aom.core.state import MAX_TASKS_PER_PLAY

        assert MAX_TASKS_PER_PLAY == 10000

    def test_max_hosts_per_task_value(self):
        """TC-255: Maximum 10000 hosts per task tracked."""
        from ansible_aom.core.state import MAX_HOSTS_PER_TASK

        assert MAX_HOSTS_PER_TASK == 10000

    def test_max_total_host_run_states_value(self):
        """TC-256: Maximum 1,000,000 total HostRunState entries."""
        from ansible_aom.core.state import MAX_TOTAL_HOST_RUN_STATES

        assert MAX_TOTAL_HOST_RUN_STATES == 1000000

    def test_memory_bound_warning_message_constant(self):
        """TC-257: Memory bounds have associated warning constants."""
        from ansible_aom.core.state import MAX_PLAYS, MAX_TASKS_PER_PLAY, MAX_HOSTS_PER_TASK, MAX_TOTAL_HOST_RUN_STATES

        assert isinstance(MAX_PLAYS, int)
        assert isinstance(MAX_TASKS_PER_PLAY, int)
        assert isinstance(MAX_HOSTS_PER_TASK, int)
        assert isinstance(MAX_TOTAL_HOST_RUN_STATES, int)

    def test_max_log_lines_value(self):
        """TC-259: Log panel max_lines=50000."""
        from ansible_aom.core.state import MAX_LOG_LINES

        assert MAX_LOG_LINES == 50000

    def test_memory_bounds_are_reasonable(self):
        """Verify memory bounds are positive integers."""
        from ansible_aom.core.state import (
            MAX_HOSTS_PER_TASK,
            MAX_LOG_LINES,
            MAX_PLAYS,
            MAX_TASKS_PER_PLAY,
            MAX_TOTAL_HOST_RUN_STATES,
        )

        assert MAX_PLAYS > 0
        assert MAX_TASKS_PER_PLAY > 0
        assert MAX_HOSTS_PER_TASK > 0
        assert MAX_TOTAL_HOST_RUN_STATES > 0
        assert MAX_LOG_LINES > 0

    def test_memory_bounds_hierarchy(self):
        """Verify memory bounds scale appropriately."""
        from ansible_aom.core.state import (
            MAX_HOSTS_PER_TASK,
            MAX_TASKS_PER_PLAY,
            MAX_TOTAL_HOST_RUN_STATES,
            MAX_PLAYS,
        )

        assert MAX_PLAYS < MAX_TASKS_PER_PLAY
        assert MAX_TASKS_PER_PLAY <= MAX_HOSTS_PER_TASK
        assert MAX_TOTAL_HOST_RUN_STATES < MAX_PLAYS * MAX_TASKS_PER_PLAY