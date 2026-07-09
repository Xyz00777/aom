# Crash Recovery Panels

> 12 nodes · cohesion 0.20

## Key Concepts

- **._bump_task_counters()** (8 connections) — `src/ansible_aom/compact/renderer.py`
- **._task_dict()** (8 connections) — `src/ansible_aom/compact/renderer.py`
- **._count_completed_task()** (6 connections) — `src/ansible_aom/compact/renderer.py`
- **.update_state()** (6 connections) — `src/ansible_aom/compact/renderer.py`
- **._record_running_start()** (5 connections) — `src/ansible_aom/compact/renderer.py`
- **._reconcile_completed_tasks()** (4 connections) — `src/ansible_aom/compact/renderer.py`
- **Extract the ``task`` field as a dict.          ansible.posix.jsonl may emit ``ta** (1 connections) — `src/ansible_aom/compact/renderer.py`
- **Handle a new JSONL event.          Processes the event to update RunState, then** (1 connections) — `src/ansible_aom/compact/renderer.py`
- **Update ``_tasks_seen`` / ``_tasks_completed`` from a single event.          Trac** (1 connections) — `src/ansible_aom/compact/renderer.py`
- **Count tasks finalised in RunState without a terminal runner event.          ``Ru** (1 connections) — `src/ansible_aom/compact/renderer.py`
- **Fold one finished task into the incremental progress counters.          Idempote** (1 connections) — `src/ansible_aom/compact/renderer.py`
- **Note when a task entered flight, for the live ETA's in-flight credit.          R** (1 connections) — `src/ansible_aom/compact/renderer.py`

## Relationships

- [App Configuration Settings](App_Configuration_Settings.md) (6 shared connections)
- [Status Icon Animation Tests](Status_Icon_Animation_Tests.md) (5 shared connections)
- [Heartbeat Liveness Tracker](Heartbeat_Liveness_Tracker.md) (4 shared connections)
- [Warning Classification Tests](Warning_Classification_Tests.md) (1 shared connections)
- [Community 560](Community_560.md) (1 shared connections)

## Source Files

- `src/ansible_aom/compact/renderer.py`

## Audit Trail

- EXTRACTED: 42 (98%)
- INFERRED: 1 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*