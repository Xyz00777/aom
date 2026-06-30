# Core Domain Architecture

> 6 nodes · cohesion 0.29

## Key Concepts

- **core/models.py (domain entities)** (12 connections) — `ARCHITECTURE.md`
- **formats/json.py (JsonRenderer)** (2 connections) — `ARCHITECTURE.md`
- **core/heartbeat.py (HeartbeatTracker)** (1 connections) — `ARCHITECTURE.md`
- **core/overhead.py (OverheadStats)** (1 connections) — `ARCHITECTURE.md`
- **core/parity.py (renderer-agnostic dict)** (1 connections) — `ARCHITECTURE.md`
- **Memory bounds (MAX_PLAYS/TASKS/HOSTS)** (1 connections) — `SPECIFICATION.md`

## Relationships

- [[Renderer Architecture]] (3 shared connections)
- [[Parser Architecture]] (1 shared connections)
- [[Test Layering Architecture]] (1 shared connections)
- [[Core Tree Icons]] (1 shared connections)
- [[Project Architecture Overview]] (1 shared connections)

## Source Files

- `ARCHITECTURE.md`
- `SPECIFICATION.md`

## Audit Trail

- EXTRACTED: 6 (33%)
- INFERRED: 12 (67%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*