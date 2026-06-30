# Renderer Architecture

> 9 nodes · cohesion 0.33

## Key Concepts

- **compact/renderer.py (CompactRenderer)** (9 connections) — `ARCHITECTURE.md`
- **renderer/protocol.py (Renderer Protocol)** (7 connections) — `ARCHITECTURE.md`
- **tui/app.py (AOMApp)** (6 connections) — `ARCHITECTURE.md`
- **create_renderer factory function** (3 connections) — `SPECIFICATION.md`
- **Renderer test cases (TC-029 to TC-066)** (3 connections) — `TEST_SPECIFICATION.md`
- **compact/format.py (pure formatters)** (2 connections) — `ARCHITECTURE.md`
- **Compact refresh strategy (4 FPS)** (2 connections) — `SPECIFICATION.md`
- **Pure formatting separated from lifecycle** (1 connections) — `ARCHITECTURE.md`
- **Terminal 24x80 minimum + signals** (1 connections) — `SPECIFICATION.md`

## Relationships

- [[Core Domain Architecture]] (3 shared connections)
- [[Secret Redaction Layers]] (2 shared connections)
- [[Core Tree Icons]] (2 shared connections)
- [[Project Architecture Overview]] (2 shared connections)
- [[Parser Architecture]] (1 shared connections)

## Source Files

- `ARCHITECTURE.md`
- `SPECIFICATION.md`
- `TEST_SPECIFICATION.md`

## Audit Trail

- EXTRACTED: 21 (62%)
- INFERRED: 13 (38%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*