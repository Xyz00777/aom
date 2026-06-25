# Test Layering Architecture

> 7 nodes · cohesion 0.29

## Key Concepts

- **ExecutionState 8-state machine** (4 connections) — `SPECIFICATION.md`
- **core/state_machine.py (ExecutionState FSM)** (3 connections) — `ARCHITECTURE.md`
- **Gap refactor punch list (§7)** (3 connections) — `ARCHITECTURE.md`
- **Test categories (unit/integration/tui/compact)** (2 connections) — `AGENTS.md`
- **State machine test cases (TC-128 to TC-142)** (2 connections) — `TEST_SPECIFICATION.md`
- **CI layering enforcement (test_layering.py)** (1 connections) — `ARCHITECTURE.md`
- **Exit codes (0/1/2/127/130)** (1 connections) — `SPECIFICATION.md`

## Relationships

- [[Parser Architecture]] (2 shared connections)
- [[Core Domain Architecture]] (1 shared connections)
- [[Live Driver Run Flow]] (1 shared connections)

## Source Files

- `AGENTS.md`
- `ARCHITECTURE.md`
- `SPECIFICATION.md`
- `TEST_SPECIFICATION.md`

## Audit Trail

- EXTRACTED: 10 (62%)
- INFERRED: 6 (38%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*