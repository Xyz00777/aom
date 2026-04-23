"""Execution state machine for AOM.

This module defines the 8-state machine that manages playbook execution.
See SPECIFICATION.md Section 6.4 for state diagram and transitions.

Memory bounds (Section 6.5):
- MAX_PLAYS: Maximum 1000 plays tracked
- MAX_TASKS_PER_PLAY: Maximum 10000 tasks per play
- MAX_HOSTS_PER_TASK: Maximum 10000 hosts per task
- MAX_TOTAL_HOST_RUN_STATES: Maximum 1,000,000 total HostRunState entries
- MAX_LOG_LINES: Maximum 50000 log panel lines

TDD: This file contains STUB implementations only. Tests come first.
"""


MAX_PLAYS = 1000
MAX_TASKS_PER_PLAY = 10000
MAX_HOSTS_PER_TASK = 10000
MAX_TOTAL_HOST_RUN_STATES = 1000000
MAX_LOG_LINES = 50000

from enum import Enum, auto


class ExecutionState(Enum):
    """Execution state machine states."""

    IDLE = auto()
    STARTING = auto()
    LOADING_TASKS = auto()
    READY = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CRASHED = auto()


VALID_TRANSITIONS: dict[ExecutionState, set[ExecutionState]] = {
    ExecutionState.IDLE: {ExecutionState.STARTING},
    ExecutionState.STARTING: {ExecutionState.LOADING_TASKS, ExecutionState.CRASHED},
    ExecutionState.LOADING_TASKS: {ExecutionState.READY, ExecutionState.CRASHED},
    ExecutionState.READY: {ExecutionState.RUNNING, ExecutionState.IDLE},
    ExecutionState.RUNNING: {
        ExecutionState.RUNNING,
        ExecutionState.COMPLETED,
        ExecutionState.FAILED,
        ExecutionState.CRASHED,
    },
    ExecutionState.COMPLETED: {ExecutionState.IDLE},
    ExecutionState.FAILED: {ExecutionState.IDLE},
    ExecutionState.CRASHED: {ExecutionState.IDLE},
}


class InvalidTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""

    def __init__(self, current: ExecutionState, target: ExecutionState) -> None:
        self.current = current
        self.target = target
        super().__init__(
            f"Invalid transition from {current.name} to {target.name}. "
            f"Valid targets: {[s.name for s in VALID_TRANSITIONS.get(current, [])]}"
        )


class StateMachine:
    """Manages execution state transitions."""

    def __init__(self) -> None:
        self._state = ExecutionState.IDLE

    @property
    def state(self) -> ExecutionState:
        return self._state

    def transition(self, new_state: ExecutionState) -> None:
        """Transition to a new state if valid.

        Raises:
            InvalidTransitionError: If the transition is not allowed.
        """
        if not self.can_transition(new_state):
            raise InvalidTransitionError(self._state, new_state)
        self._state = new_state

    def can_transition(self, new_state: ExecutionState) -> bool:
        """Check if transition to new_state is valid from current state."""
        valid_targets = VALID_TRANSITIONS.get(self._state, set())
        return new_state in valid_targets

    def reset(self) -> None:
        """Reset state machine to IDLE."""
        self._state = ExecutionState.IDLE