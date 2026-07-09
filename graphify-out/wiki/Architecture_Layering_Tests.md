# Architecture Layering Tests

> 19 nodes · cohesion 0.14

## Key Concepts

- **_drive()** (15 connections) — `tests/integration/test_invariants_session_roundtrip.py`
- **_FakeChildIsaliveDead** (10 connections) — `tests/unit/test_runner_isalive_in_loop.py`
- **test_runner_isalive_in_loop.py** (6 connections) — `tests/unit/test_runner_isalive_in_loop.py`
- **test_drive_exits_promptly_when_child_dead_but_pty_open()** (6 connections) — `tests/unit/test_runner_isalive_in_loop.py`
- **_build_parser_in_post_run_recap()** (5 connections) — `tests/unit/test_runner_isalive_in_loop.py`
- **test_drive_isalive_check_handles_eof_exception_path()** (5 connections) — `tests/unit/test_runner_isalive_in_loop.py`
- **test_drive_isalive_check_on_timeout_branch()** (5 connections) — `tests/unit/test_runner_isalive_in_loop.py`
- **test_runstate_never_holds_orphan_hostrunstate()** (4 connections) — `tests/integration/test_invariants_session_roundtrip.py`
- **.expect()** (2 connections) — `tests/unit/test_runner_isalive_in_loop.py`
- **A ``HostRunState`` only exists under a TaskRunState we know about.      Sanity c** (1 connections) — `tests/integration/test_invariants_session_roundtrip.py`
- **.close()** (1 connections) — `tests/unit/test_runner_isalive_in_loop.py`
- **.__init__()** (1 connections) — `tests/unit/test_runner_isalive_in_loop.py`
- **.isalive()** (1 connections) — `tests/unit/test_runner_isalive_in_loop.py`
- **Any** (1 connections)
- **R10 — `child.isalive()` check inside `_drive()` loop.  R10 spec: pexpect's EOF d** (1 connections) — `tests/unit/test_runner_isalive_in_loop.py`
- **R10: isalive() check must also run after a pexpect.exceptions.EOF.      The EOF** (1 connections) — `tests/unit/test_runner_isalive_in_loop.py`
- **R10: isalive() False on a TIMEOUT match must break the loop.      The TIMEOUT br** (1 connections) — `tests/unit/test_runner_isalive_in_loop.py`
- **Fake pexpect child whose PID is dead but PTY still buffers data.      R10 scenar** (1 connections) — `tests/unit/test_runner_isalive_in_loop.py`
- **R10: isalive() == False in POST_RUN_RECAP must terminate the loop.      Without** (1 connections) — `tests/unit/test_runner_isalive_in_loop.py`

## Relationships

- [Status Bar Warning Panels](Status_Bar_Warning_Panels.md) (5 shared connections)
- [Run History Mining](Run_History_Mining.md) (5 shared connections)
- [Plaintext Line Handling](Plaintext_Line_Handling.md) (4 shared connections)
- [Run State Completion Recap](Run_State_Completion_Recap.md) (2 shared connections)
- [Runner Heartbeat Wiring](Runner_Heartbeat_Wiring.md) (1 shared connections)
- [Stale Running Cleanup](Stale_Running_Cleanup.md) (1 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (1 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (1 shared connections)

## Source Files

- `tests/integration/test_invariants_session_roundtrip.py`
- `tests/unit/test_runner_isalive_in_loop.py`

## Audit Trail

- EXTRACTED: 48 (71%)
- INFERRED: 20 (29%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*