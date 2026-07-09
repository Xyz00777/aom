# Debug Diagnostics Summary

> 15 nodes · cohesion 0.13

## Key Concepts

- **LiveDriver** (14 connections) — `src/ansible_aom/drivers/live.py`
- **_HideStateAction** (5 connections) — `src/ansible_aom/cli.py`
- **.__call__()** (3 connections) — `src/ansible_aom/cli.py`
- **.drive()** (3 connections) — `src/ansible_aom/drivers/live.py`
- **._run_playbook_worker()** (3 connections) — `src/ansible_aom/tui/app.py`
- **ArgumentParser** (2 connections)
- **live.py** (2 connections) — `src/ansible_aom/drivers/live.py`
- **.__init__()** (2 connections) — `src/ansible_aom/drivers/live.py`
- **Namespace** (1 connections)
- **.ansible_args()** (1 connections) — `src/ansible_aom/drivers/live.py`
- **.playbook()** (1 connections) — `src/ansible_aom/drivers/live.py`
- **Path** (1 connections)
- **LiveDriver — :class:`EventSource` that runs a real ``ansible-playbook``.  A thin** (1 connections) — `src/ansible_aom/drivers/live.py`
- **Spawns ``ansible-playbook`` and pumps its JSONL output.      Parameters mirror :** (1 connections) — `src/ansible_aom/drivers/live.py`
- **Drive the playbook to completion from a Textual worker thread.          Lives of** (1 connections) — `src/ansible_aom/tui/app.py`

## Relationships

- [State Transition Validation](State_Transition_Validation.md) (3 shared connections)
- [Session Recording Tests](Session_Recording_Tests.md) (3 shared connections)
- [PTY Stream Parser](PTY_Stream_Parser.md) (2 shared connections)
- [Narrow Terminal View](Narrow_Terminal_View.md) (1 shared connections)
- [Diagnostics Layer Tests](Diagnostics_Layer_Tests.md) (1 shared connections)
- [Rerun Main Function](Rerun_Main_Function.md) (1 shared connections)
- [Tree Block Animation](Tree_Block_Animation.md) (1 shared connections)
- [Interactive Prompt Tests](Interactive_Prompt_Tests.md) (1 shared connections)

## Source Files

- `src/ansible_aom/cli.py`
- `src/ansible_aom/drivers/live.py`
- `src/ansible_aom/tui/app.py`

## Audit Trail

- EXTRACTED: 28 (68%)
- INFERRED: 13 (32%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*