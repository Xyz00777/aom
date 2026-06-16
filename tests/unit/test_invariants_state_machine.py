"""Stateful invariants on the ExecutionState machine in ``core.state_machine``.

``VALID_TRANSITIONS`` is the declarative source of truth for which moves
are allowed. The risk this test guards against is *drift between the
table and the implementation*: a future refactor that bypasses
``transition()`` (e.g. assigning ``_state`` directly), or that adds a
new ExecutionState without wiring it into the table, would silently
break the contract callers depend on (no reverse transitions, terminal
states only exit via IDLE).

We drive a Hypothesis ``RuleBasedStateMachine`` that picks a random
target state on every step. Whether it succeeds or raises
``InvalidTransitionError`` is itself the observation — both outcomes
are checked against the VALID_TRANSITIONS table, so any deviation in
either direction fails the test.
"""

from __future__ import annotations

import pytest
from hypothesis import HealthCheck, settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, rule

from ansible_aom.core.state_machine import (
    VALID_TRANSITIONS,
    ExecutionState,
    InvalidTransitionError,
    StateMachine,
)

# Terminal states per SPECIFICATION.md §6.4: the only valid outbound
# edge is back to IDLE. Encoded here rather than imported so the test
# also catches "someone added a transition from a terminal state to a
# non-IDLE state in VALID_TRANSITIONS".
_TERMINAL_STATES = frozenset(
    {ExecutionState.COMPLETED, ExecutionState.FAILED, ExecutionState.CRASHED}
)

_ALL_STATES = list(ExecutionState)


class ExecutionStateMachine(RuleBasedStateMachine):
    """Random walk over ExecutionState; verifies table ↔ implementation."""

    def __init__(self) -> None:
        super().__init__()
        self.sm = StateMachine()

    @rule(target_state=st.sampled_from(_ALL_STATES))
    def try_transition(self, target_state: ExecutionState) -> None:
        """Attempt a transition; outcome must match the VALID_TRANSITIONS table."""
        current = self.sm.state
        is_valid = target_state in VALID_TRANSITIONS.get(current, set())

        if is_valid:
            self.sm.transition(target_state)
            assert self.sm.state == target_state, (
                f"transition({target_state.name}) reported success from "
                f"{current.name} but state is {self.sm.state.name}"
            )
        else:
            with pytest.raises(InvalidTransitionError):
                self.sm.transition(target_state)
            # A rejected transition must not silently change the state.
            assert self.sm.state == current, (
                f"InvalidTransitionError from {current.name} → "
                f"{target_state.name} still mutated state to "
                f"{self.sm.state.name}"
            )

    @rule()
    def reset(self) -> None:
        """``reset()`` always returns to IDLE regardless of current state.

        Documented contract: ``reset()`` is the escape hatch from any
        state, including the terminal ones. If reset() ever grew a
        validity check (e.g. "only from terminal states"), this rule
        would surface that.
        """
        self.sm.reset()
        assert self.sm.state == ExecutionState.IDLE

    # ── invariants checked after every step ───────────────────────────

    @invariant()
    def state_is_in_enum(self) -> None:
        """No matter what we did, the state is one of the declared values."""
        assert self.sm.state in _ALL_STATES, (
            f"StateMachine state {self.sm.state!r} is not in ExecutionState"
        )

    @invariant()
    def terminal_states_only_exit_via_idle(self) -> None:
        """COMPLETED/FAILED/CRASHED have exactly one outbound edge: IDLE.

        Asserts on the table itself rather than the live state — that
        way the invariant catches a change to ``VALID_TRANSITIONS``
        even on a step that didn't currently land on a terminal state.
        """
        for terminal in _TERMINAL_STATES:
            valid_targets = VALID_TRANSITIONS.get(terminal, set())
            assert valid_targets == {ExecutionState.IDLE}, (
                f"{terminal.name} should only transition to IDLE, "
                f"but VALID_TRANSITIONS allows {valid_targets!r}"
            )

    @invariant()
    def can_transition_matches_transition(self) -> None:
        """``can_transition`` and ``transition`` agree on every state pair.

        Catches the bug where ``can_transition`` returns True for a
        target but ``transition`` raises (or vice versa). This is a
        pure dispatch check — it doesn't mutate state.
        """
        current = self.sm.state
        for candidate in _ALL_STATES:
            predicted = self.sm.can_transition(candidate)
            actual = candidate in VALID_TRANSITIONS.get(current, set())
            assert predicted == actual, (
                f"can_transition({candidate.name}) returned {predicted} "
                f"from {current.name} but VALID_TRANSITIONS says {actual}"
            )


TestExecutionStateMachine = ExecutionStateMachine.TestCase
TestExecutionStateMachine.settings = settings(
    max_examples=100,
    stateful_step_count=40,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
