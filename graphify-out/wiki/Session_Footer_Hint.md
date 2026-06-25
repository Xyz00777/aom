# Session Footer Hint

> 7 nodes · cohesion 0.38

## Key Concepts

- **_print_session_footer()** (6 connections) — `src/ansible_aom/ansible/runner.py`
- **test_runner_session_footer.py** (4 connections) — `tests/unit/test_runner_session_footer.py`
- **test_footer_prints_short_id_and_inspect_hint()** (2 connections) — `tests/unit/test_runner_session_footer.py`
- **test_footer_suppressed_when_no_session_id()** (2 connections) — `tests/unit/test_runner_session_footer.py`
- **test_footer_suppressed_when_stderr_not_tty()** (2 connections) — `tests/unit/test_runner_session_footer.py`
- **Print the end-of-run hint that points users at ``aom inspect``.      Suppressed** (1 connections) — `src/ansible_aom/ansible/runner.py`
- **The runner prints a `Session …  aom inspect` footer on termination.** (1 connections) — `tests/unit/test_runner_session_footer.py`

## Relationships

- [[Runner Session Recording]] (1 shared connections)
- [[Playbook Run Integration Tests]] (1 shared connections)

## Source Files

- `src/ansible_aom/ansible/runner.py`
- `tests/unit/test_runner_session_footer.py`

## Audit Trail

- EXTRACTED: 12 (67%)
- INFERRED: 6 (33%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*