# Host Collection Helpers

> 25 nodes · cohesion 0.12

## Key Concepts

- **_FakeSpawn** (13 connections) — `tests/unit/test_runner_ctrl_c_race.py`
- **_patch_runner_for_fake_subprocess()** (9 connections) — `tests/unit/test_runner_ctrl_c_race.py`
- **.test_sigint_after_failed_child_returns_child_exit_code()** (6 connections) — `tests/unit/test_runner_ctrl_c_race.py`
- **.test_sigint_during_handle_completion_returns_child_exit_code()** (6 connections) — `tests/unit/test_runner_ctrl_c_race.py`
- **.test_sigint_mid_run_returns_130()** (6 connections) — `tests/unit/test_runner_ctrl_c_race.py`
- **test_runner_ctrl_c_race.py** (5 connections) — `tests/unit/test_runner_ctrl_c_race.py`
- **MonkeyPatch** (4 connections)
- **TestCtrlCAfterChildExitedCleanly** (4 connections) — `tests/unit/test_runner_ctrl_c_race.py`
- **TestCtrlCDuringActiveRun** (3 connections) — `tests/unit/test_runner_ctrl_c_race.py`
- **.expect()** (2 connections) — `tests/unit/test_runner_ctrl_c_race.py`
- **Any** (2 connections)
- **.close()** (1 connections) — `tests/unit/test_runner_ctrl_c_race.py`
- **.__init__()** (1 connections) — `tests/unit/test_runner_ctrl_c_race.py`
- **.isalive()** (1 connections) — `tests/unit/test_runner_ctrl_c_race.py`
- **.read_nonblocking()** (1 connections) — `tests/unit/test_runner_ctrl_c_race.py`
- **.sendintr()** (1 connections) — `tests/unit/test_runner_ctrl_c_race.py`
- **.sendline()** (1 connections) — `tests/unit/test_runner_ctrl_c_race.py`
- **R7 — Ctrl-C race guard.  If SIGINT arrives between the child exiting cleanly and** (1 connections) — `tests/unit/test_runner_ctrl_c_race.py`
- **Window #2: child already exited 0, then SIGINT fires during cleanup.      Before** (1 connections) — `tests/unit/test_runner_ctrl_c_race.py`
- **The race: child exits 0, ``_drive`` returns 0, then SIGINT         fires while t** (1 connections) — `tests/unit/test_runner_ctrl_c_race.py`
- **If the child exited non-zero (e.g. failed playbook) and SIGINT         arrives d** (1 connections) — `tests/unit/test_runner_ctrl_c_race.py`
- **Window #1: SIGINT arrives while the child is still alive.      The fix MUST NOT** (1 connections) — `tests/unit/test_runner_ctrl_c_race.py`
- **Simulate SIGINT during a real event: the renderer's         ``update_state`` rai** (1 connections) — `tests/unit/test_runner_ctrl_c_race.py`
- **Minimal pexpect.spawn-shaped stand-in.      Emits a fixed list of newline-termin** (1 connections) — `tests/unit/test_runner_ctrl_c_race.py`
- **Wire the runner's spawn/preflight/build-command seams to a fake.** (1 connections) — `tests/unit/test_runner_ctrl_c_race.py`

## Relationships

- [run_playbook](run_playbook.md) (3 shared connections)
- [test_live_driver_drives_renderer_with_fake_subprocess](test_live_driver_drives_renderer_with_fake_subprocess.md) (1 shared connections)

## Source Files

- `tests/unit/test_runner_ctrl_c_race.py`

## Audit Trail

- EXTRACTED: 70 (95%)
- INFERRED: 4 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*