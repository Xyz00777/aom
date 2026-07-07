# Project Architecture Overview

> 11 nodes · cohesion 0.18

## Key Concepts

- **session/store.py (SessionManager)** (6 connections) — `ARCHITECTURE.md`
- **drivers/protocol.py (EventSource Protocol)** (4 connections) — `ARCHITECTURE.md`
- **cli.py composition root** (3 connections) — `ARCHITECTURE.md`
- **Two-port architecture (Renderer + EventSource)** (3 connections) — `ARCHITECTURE.md`
- **File locations** (3 connections) — `README.md`
- **drivers/replay.py (ReplayDriver)** (2 connections) — `ARCHITECTURE.md`
- **Session diff (UUID→path→name matching)** (2 connections) — `SPECIFICATION.md`
- **AOM project identity** (1 connections) — `AGENTS.md`
- **session/summary.py** (1 connections) — `ARCHITECTURE.md`
- **Session recording to .aom artifacts** (1 connections) — `SPECIFICATION.md`
- **CLI test cases (TC-001 to TC-028)** (1 connections) — `TEST_SPECIFICATION.md`

## Relationships

- [[Renderer Architecture]] (2 shared connections)
- [[Live Driver Run Flow]] (2 shared connections)
- [[Core Domain Architecture]] (1 shared connections)

## Source Files

- `AGENTS.md`
- `ARCHITECTURE.md`
- `README.md`
- `SPECIFICATION.md`
- `TEST_SPECIFICATION.md`

## Audit Trail

- EXTRACTED: 15 (56%)
- INFERRED: 12 (44%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*