# Plaintext Line Handling

> 12 nodes · cohesion 0.17

## Key Concepts

- **TestPlaintextLineHandling** (10 connections) — `tests/unit/test_pty_stream.py`
- **.test_plaintext_lines_in_execution_phase()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_plaintext_lines_not_warning()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_plaintext_lines_order_preserved()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_plaintext_lines_stored()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_plaintext_vs_warning_classification()** (3 connections) — `tests/unit/test_pty_stream.py`
- **TC-142: _handle_plaintext classification.** (1 connections) — `tests/unit/test_pty_stream.py`
- **TC-142: Non-JSON, non-special lines go to plaintext_lines.** (1 connections) — `tests/unit/test_pty_stream.py`
- **Plaintext lines that aren't warnings are stored.** (1 connections) — `tests/unit/test_pty_stream.py`
- **Plaintext during EXECUTION phase collected.** (1 connections) — `tests/unit/test_pty_stream.py`
- **Lines classified correctly between warning vs plaintext.** (1 connections) — `tests/unit/test_pty_stream.py`
- **Plaintext lines maintain order.** (1 connections) — `tests/unit/test_pty_stream.py`

## Relationships

- [[PTY Stream Parser]] (6 shared connections)
- [[Role Group Task Models]] (2 shared connections)
- [[PTY Stream Parser Tests]] (1 shared connections)

## Source Files

- `tests/unit/test_pty_stream.py`

## Audit Trail

- EXTRACTED: 23 (74%)
- INFERRED: 8 (26%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*