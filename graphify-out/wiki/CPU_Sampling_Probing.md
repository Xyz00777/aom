# CPU Sampling Probing

> 10 nodes · cohesion 0.22

## Key Concepts

- **_sample_subprocess_active()** (6 connections) — `src/ansible_aom/ansible/runner.py`
- **TestSampleSubprocessActive** (6 connections) — `tests/unit/test_runner_heartbeat.py`
- **_get_psutil()** (5 connections) — `src/ansible_aom/ansible/runner.py`
- **_probe_psutil()** (4 connections) — `src/ansible_aom/ansible/runner.py`
- **.test_returns_bool_for_own_pid()** (2 connections) — `tests/unit/test_runner_heartbeat.py`
- **.test_returns_false_for_nonexistent_pid()** (2 connections) — `tests/unit/test_runner_heartbeat.py`
- **Subprocess-probe ``import psutil``; return ``(module, None)`` on     success or** (1 connections) — `src/ansible_aom/ansible/runner.py`
- **Return the cached psutil module, or None if probing failed.      Lazy: the first** (1 connections) — `src/ansible_aom/ansible/runner.py`
- **Return True if pid or any descendant used CPU since the last call.      Uses ``p** (1 connections) — `src/ansible_aom/ansible/runner.py`
- **The CPU sampler degrades gracefully and never raises.** (1 connections) — `tests/unit/test_runner_heartbeat.py`

## Relationships

- [[Runner Session Recording]] (4 shared connections)
- [[Playbook Event Parsing]] (2 shared connections)
- [[Role Group Task Models]] (1 shared connections)
- [[PTY Stream Parser]] (1 shared connections)
- [[Runner Heartbeat Wiring]] (1 shared connections)

## Source Files

- `src/ansible_aom/ansible/runner.py`
- `tests/unit/test_runner_heartbeat.py`

## Audit Trail

- EXTRACTED: 23 (79%)
- INFERRED: 6 (21%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*