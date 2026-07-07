# CPU Sampling Probing

> 6 nodes · cohesion 0.22

## Key Concepts

- **TestSampleSubprocessActive** (7 connections) — `tests/unit/test_runner_heartbeat.py`
- **_get_psutil()** (6 connections) — `src/ansible_aom/ansible/runner.py`
- **_sample_subprocess_active()** (6 connections) — `src/ansible_aom/ansible/runner.py`
- **_probe_psutil()** (5 connections) — `src/ansible_aom/ansible/runner.py`
- **.test_returns_bool_for_own_pid()** (2 connections) — `tests/unit/test_runner_heartbeat.py`
- **.test_returns_false_for_nonexistent_pid()** (2 connections) — `tests/unit/test_runner_heartbeat.py`

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

- EXTRACTED: 21 (75%)
- INFERRED: 7 (25%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*