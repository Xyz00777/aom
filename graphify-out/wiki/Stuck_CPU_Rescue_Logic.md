# Stuck CPU Rescue Logic

> 2 nodes · cohesion 1.00

## Key Concepts

- **test_cpu_active_too_long_ago_does_not_rescue_from_stuck()** (3 connections) — `tests/unit/test_heartbeat.py`
- **Active CPU sample older than stuck_threshold_s no longer counts.** (1 connections) — `tests/unit/test_heartbeat.py`

## Relationships

- [[Heartbeat Liveness Tracker]] (2 shared connections)

## Source Files

- `tests/unit/test_heartbeat.py`

## Audit Trail

- EXTRACTED: 3 (75%)
- INFERRED: 1 (25%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*