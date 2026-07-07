# Renderer Event Protocol

> 25 nodes · cohesion 0.05

## Key Concepts

- **Renderer** (30 connections) — `src/ansible_aom/renderer/protocol.py`
- **.__init__()** (8 connections) — `src/ansible_aom/tui/app.py`
- **EventSource** (7 connections) — `src/ansible_aom/drivers/protocol.py`
- **.drive()** (3 connections) — `src/ansible_aom/drivers/live.py`
- **.drive()** (3 connections) — `src/ansible_aom/drivers/protocol.py`
- **protocol.py** (2 connections) — `src/ansible_aom/drivers/protocol.py`
- **Protocol** (2 connections)
- **protocol.py** (2 connections) — `src/ansible_aom/renderer/protocol.py`
- **.add_warning()** (2 connections) — `src/ansible_aom/renderer/protocol.py`
- **.handle_completion()** (2 connections) — `src/ansible_aom/renderer/protocol.py`
- **.handle_interactive_prompt()** (2 connections) — `src/ansible_aom/renderer/protocol.py`
- **.handle_password_prompt()** (2 connections) — `src/ansible_aom/renderer/protocol.py`
- **.note_pty_bytes()** (2 connections) — `src/ansible_aom/renderer/protocol.py`
- **.note_subprocess_active()** (2 connections) — `src/ansible_aom/renderer/protocol.py`
- **.print_log()** (2 connections) — `src/ansible_aom/renderer/protocol.py`
- **.set_definitions()** (2 connections) — `src/ansible_aom/renderer/protocol.py`
- **.set_prior_run()** (2 connections) — `src/ansible_aom/renderer/protocol.py`
- **.start()** (2 connections) — `src/ansible_aom/renderer/protocol.py`
- **.stop()** (2 connections) — `src/ansible_aom/renderer/protocol.py`
- **.tick()** (2 connections) — `src/ansible_aom/renderer/protocol.py`
- **.update_state()** (2 connections) — `src/ansible_aom/renderer/protocol.py`
- **EventSource Protocol — the source-side port of the architecture.  See ``ARCHITEC** (1 connections) — `src/ansible_aom/drivers/protocol.py`
- **A producer of run events for a :class:`Renderer`.      Implementations own the f** (1 connections) — `src/ansible_aom/drivers/protocol.py`
- **Drive ``renderer`` to completion and return the run's exit code.          Contra** (1 connections) — `src/ansible_aom/drivers/protocol.py`
- **Renderer Protocol — the display-side port of the architecture.  See ``ARCHITECTU** (1 connections) — `src/ansible_aom/renderer/protocol.py`

## Relationships

- [[Runner Session Recording]] (3 shared connections)
- [[Playbook Run Integration Tests]] (2 shared connections)
- [[AOM TUI Application]] (2 shared connections)
- [[Session Replay Driver]] (2 shared connections)
- [[PTY Buffer Stall Handling]] (2 shared connections)
- [[CLI Main Entry Point]] (1 shared connections)
- [[Session Replay Round Trip]] (1 shared connections)
- [[Renderer Factory Function]] (1 shared connections)
- [[Run History Mining]] (1 shared connections)
- [[Run Config Key Normalization]] (1 shared connections)
- [[Playbook Event Parsing]] (1 shared connections)

## Source Files

- `src/ansible_aom/drivers/live.py`
- `src/ansible_aom/drivers/protocol.py`
- `src/ansible_aom/renderer/protocol.py`
- `src/ansible_aom/tui/app.py`

## Audit Trail

- EXTRACTED: 82 (94%)
- INFERRED: 5 (6%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*