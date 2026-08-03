# _BoundedSet

> 20 nodes · cohesion 0.11

## Key Concepts

- **_BoundedSet** (16 connections) — `src/ansible_aom/compact/renderer.py`
- **.handle_completion()** (13 connections) — `src/ansible_aom/compact/renderer.py`
- **.__init__()** (10 connections) — `src/ansible_aom/compact/renderer.py`
- **.start()** (9 connections) — `src/ansible_aom/compact/renderer.py`
- **.stop()** (6 connections) — `src/ansible_aom/compact/renderer.py`
- **.collect_stats()** (4 connections) — `src/ansible_aom/compact/renderer.py`
- **.handle_interactive_prompt()** (4 connections) — `src/ansible_aom/compact/renderer.py`
- **.handle_password_prompt()** (4 connections) — `src/ansible_aom/compact/renderer.py`
- **._task_total_with_prior()** (4 connections) — `src/ansible_aom/compact/renderer.py`
- **.__init__()** (2 connections) — `src/ansible_aom/compact/renderer.py`
- **set** (1 connections)
- **Handle playbook completion (success/failure/crash).          Shows final status** (1 connections) — `src/ansible_aom/compact/renderer.py`
- **A ``set`` that drops itself when it exceeds a cap on insert.      R14: the compa** (1 connections) — `src/ansible_aom/compact/renderer.py`
- **Return an immutable snapshot of this renderer's activity counters.          Call** (1 connections) — `src/ansible_aom/compact/renderer.py`
- **Stop rendering and clean up resources.          Restores terminal state, flushes** (1 connections) — `src/ansible_aom/compact/renderer.py`
- **Initialize the compact renderer.          Args:             is_tty: Whether stdo** (1 connections) — `src/ansible_aom/compact/renderer.py`
- **Start rendering a playbook run.          Initializes the RunState, starts the Ri** (1 connections) — `src/ansible_aom/compact/renderer.py`
- **Fold the matching prior run's observed task count into the total.          Prefl** (1 connections) — `src/ansible_aom/compact/renderer.py`
- **Surface a pause / vars_prompt-style prompt and capture one line.          Mirror** (1 connections) — `src/ansible_aom/compact/renderer.py`
- **Handle a password prompt.          Stops the Rich Live display, delegates to the** (1 connections) — `src/ansible_aom/compact/renderer.py`

## Relationships

- [CompactRenderer](CompactRenderer.md) (8 shared connections)
- [RunProgress](RunProgress.md) (4 shared connections)
- [renderer.py](renderer.py.md) (3 shared connections)
- [._emit_event_log](_emit_event_log.md) (3 shared connections)
- [format_status_bar](format_status_bar.md) (3 shared connections)
- [PlayDefinition](PlayDefinition.md) (3 shared connections)
- [Display](Display.md) (2 shared connections)
- [json.py](json.py.md) (2 shared connections)
- [Status Icon Unicode Mapping](Status_Icon_Unicode_Mapping.md) (2 shared connections)
- [HostRunState](HostRunState.md) (2 shared connections)
- [PriorRun](PriorRun.md) (1 shared connections)
- [diagnostics.py](diagnostics.py.md) (1 shared connections)

## Source Files

- `src/ansible_aom/compact/renderer.py`

## Audit Trail

- EXTRACTED: 72 (88%)
- INFERRED: 10 (12%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*