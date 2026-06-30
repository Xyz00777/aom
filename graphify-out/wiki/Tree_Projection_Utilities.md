# Tree Projection Utilities

> 13 nodes · cohesion 0.17

## Key Concepts

- **tree.py** (20 connections) — `src/ansible_aom/core/tree.py`
- **_is_template_match()** (6 connections) — `src/ansible_aom/core/tree.py`
- **_host_leaf_label()** (4 connections) — `src/ansible_aom/core/tree.py`
- **_collapse_role_path()** (3 connections) — `src/ansible_aom/core/tree.py`
- **_play_target_hostnames()** (3 connections) — `src/ansible_aom/core/tree.py`
- **_template_skeleton()** (3 connections) — `src/ansible_aom/core/tree.py`
- **core.models.iter_preflight_task_defs()** (2 connections) — `.sisyphus/notepads/implementation/decisions.md`
- **Pure projection of RunState into renderable tree + host-row data.  This module c** (1 connections) — `src/ansible_aom/core/tree.py`
- **Return True if ``runtime_name`` could be a resolved version of     ``preflight_n** (1 connections) — `src/ansible_aom/core/tree.py`
- **Collect hostnames targeted by this play (read-only).      Uses ``play_def.resolv** (1 connections) — `src/ansible_aom/core/tree.py`
- **Host-leaf label, with a loop-progress hint when live.      A looped task tallies** (1 connections) — `src/ansible_aom/core/tree.py`
- **Strip ``{{ ... }}`` from a task name, yielding the static parts.      ``--list-t** (1 connections) — `src/ansible_aom/core/tree.py`
- **Collapse consecutive duplicate role names in a path.      ``iter_preflight_task_** (1 connections) — `src/ansible_aom/core/tree.py`

## Relationships

- [[Play Tree Projection]] (4 shared connections)
- [[Tree Projection Logic]] (4 shared connections)
- [[Tree Truncation Utilities]] (3 shared connections)
- [[Role Chain Extraction]] (3 shared connections)
- [[Role Group Task Models]] (2 shared connections)
- [[Play Definition Tree Population]] (2 shared connections)
- [[Run History Mining]] (1 shared connections)
- [[Compact Display Module Layout]] (1 shared connections)
- [[Run State Completion Recap]] (1 shared connections)

## Source Files

- `.sisyphus/notepads/implementation/decisions.md`
- `src/ansible_aom/core/tree.py`

## Audit Trail

- EXTRACTED: 47 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*