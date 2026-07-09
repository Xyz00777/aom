# Rerun Main Function

> 16 nodes · cohesion 0.12

## Key Concepts

- **EventSource** (11 connections) — `src/ansible_aom/drivers/protocol.py`
- **.__init__()** (6 connections) — `src/ansible_aom/tui/app.py`
- **test_live_driver_satisfies_event_source()** (4 connections) — `tests/unit/test_event_source.py`
- **.drive()** (3 connections) — `src/ansible_aom/drivers/protocol.py`
- **test_event_source_is_runtime_checkable()** (3 connections) — `tests/unit/test_event_source.py`
- **protocol.py** (2 connections) — `src/ansible_aom/drivers/protocol.py`
- **test_event_source_rejects_non_conforming()** (2 connections) — `tests/unit/test_event_source.py`
- **Protocol** (1 connections)
- **EventSource Protocol — the source-side port of the architecture.  See ``ARCHITEC** (1 connections) — `src/ansible_aom/drivers/protocol.py`
- **A producer of run events for a :class:`Renderer`.      Implementations own the f** (1 connections) — `src/ansible_aom/drivers/protocol.py`
- **Drive ``renderer`` to completion and return the run's exit code.          Contra** (1 connections) — `src/ansible_aom/drivers/protocol.py`
- **Any** (1 connections)
- **Path** (1 connections)
- **Initialize the AOMApp with optional playbook context.          Args:** (1 connections) — `src/ansible_aom/tui/app.py`
- **``EventSource`` must be ``@runtime_checkable`` so structural checks work.      W** (1 connections) — `tests/unit/test_event_source.py`
- **LiveDriver is the production EventSource for ansible-playbook runs.** (1 connections) — `tests/unit/test_event_source.py`

## Relationships

- [Diagnostics Layer Tests](Diagnostics_Layer_Tests.md) (4 shared connections)
- [Session Recording Tests](Session_Recording_Tests.md) (2 shared connections)
- [Narrow Terminal View](Narrow_Terminal_View.md) (1 shared connections)
- [Interactive Prompt Tests](Interactive_Prompt_Tests.md) (1 shared connections)
- [Status Bar Warning Panels](Status_Bar_Warning_Panels.md) (1 shared connections)
- [Debug Diagnostics Summary](Debug_Diagnostics_Summary.md) (1 shared connections)

## Source Files

- `src/ansible_aom/drivers/protocol.py`
- `src/ansible_aom/tui/app.py`
- `tests/unit/test_event_source.py`

## Audit Trail

- EXTRACTED: 30 (75%)
- INFERRED: 10 (25%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*