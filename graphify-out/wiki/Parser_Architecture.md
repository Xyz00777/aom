# Parser Architecture

> 9 nodes · cohesion 0.28

## Key Concepts

- **core/parser.py (PtyStreamParser)** (10 connections) — `ARCHITECTURE.md`
- **10 JSONL event types** (4 connections) — `SPECIFICATION.md`
- **Parallel --list-tasks/--list-hosts preflight** (3 connections) — `SPECIFICATION.md`
- **include_tasks dynamic expansion** (2 connections) — `SPECIFICATION.md`
- **Strategy detection (linear vs free)** (2 connections) — `SPECIFICATION.md`
- **JSONL event test cases (TC-072 to TC-081)** (2 connections) — `TEST_SPECIFICATION.md`
- **Parser test cases (TC-107 to TC-121)** (2 connections) — `TEST_SPECIFICATION.md`
- **Role grouping (5+ threshold)** (1 connections) — `SPECIFICATION.md`
- **3-phase PTY stream parsing** (1 connections) — `SPECIFICATION.md`

## Relationships

- [[Live Driver Run Flow]] (2 shared connections)
- [[Test Layering Architecture]] (2 shared connections)
- [[Core Domain Architecture]] (1 shared connections)
- [[Renderer Architecture]] (1 shared connections)
- [[Core Tree Icons]] (1 shared connections)

## Source Files

- `ARCHITECTURE.md`
- `SPECIFICATION.md`
- `TEST_SPECIFICATION.md`

## Audit Trail

- EXTRACTED: 17 (63%)
- INFERRED: 10 (37%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*