# JSON Line Detection

> 8 nodes · cohesion 0.29

## Key Concepts

- **test_no_eof_hang.py** (6 connections) — `tests/integration/test_no_eof_hang.py`
- **_fake_ansible_hangs_after_stats()** (3 connections) — `tests/integration/test_no_eof_hang.py`
- **test_runner_finishes_promptly_on_clean_eof()** (3 connections) — `tests/integration/test_no_eof_hang.py`
- **test_runner_returns_within_bounded_time_when_child_hangs_after_stats()** (3 connections) — `tests/integration/test_no_eof_hang.py`
- **Batch E item #10c — R8 no-EOF hang protection.  A misbehaved (or hung) ansible-p** (1 connections) — `tests/integration/test_no_eof_hang.py`
- **Sanity baseline: when the child cleanly exits after emitting all     events, the** (1 connections) — `tests/integration/test_no_eof_hang.py`
- **Build a fake-ansible command that emits events then sleeps without     closing s** (1 connections) — `tests/integration/test_no_eof_hang.py`
- **R8 regression marker: the runner must not wait indefinitely on a     hung child** (1 connections) — `tests/integration/test_no_eof_hang.py`

## Relationships

- [run_playbook](run_playbook.md) (2 shared connections)
- [json.py](json.py.md) (1 shared connections)

## Source Files

- `tests/integration/test_no_eof_hang.py`

## Audit Trail

- EXTRACTED: 19 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*