# Role Chain Extraction

> 11 nodes · cohesion 0.15

## Key Concepts

- **strip_role_prefix()** (10 connections) — `src/ansible_aom/core/models.py`
- **._play_running_and_pending()** (8 connections) — `src/ansible_aom/core/tree.py`
- **_effective_status()** (6 connections) — `src/ansible_aom/core/tree.py`
- **._task_line()** (6 connections) — `src/ansible_aom/core/tree.py`
- **_is_meta_task()** (4 connections) — `src/ansible_aom/core/tree.py`
- **_name_role_chain()** (4 connections) — `src/ansible_aom/core/tree.py`
- **._play_def_for()** (4 connections) — `src/ansible_aom/core/tree.py`
- **Strip the ``"role : "`` prefix that ansible adds to task names at     runtime. P** (1 connections) — `src/ansible_aom/core/models.py`
- **Extract the role chain encoded in a task name's ``" : "`` segments.      ansible** (1 connections) — `src/ansible_aom/core/tree.py`
- **Promote OK+changed → CHANGED for count-classification purposes.      `HostRunSta** (1 connections) — `src/ansible_aom/core/tree.py`
- **Return True for explicit ``meta: ...`` tasks.      This is a narrow projection-o** (1 connections) — `src/ansible_aom/core/tree.py`

## Relationships

- [[Tree Projection Logic]] (7 shared connections)
- [[Play Tree Projection]] (6 shared connections)
- [[Run State Completion Recap]] (3 shared connections)
- [[Tree Projection Utilities]] (3 shared connections)
- [[Role Group Task Models]] (2 shared connections)
- [[Include Role Discovery]] (1 shared connections)
- [[Role Inference Indexes]] (1 shared connections)
- [[Play Definition Tree Population]] (1 shared connections)

## Source Files

- `src/ansible_aom/core/models.py`
- `src/ansible_aom/core/tree.py`

## Audit Trail

- EXTRACTED: 36 (78%)
- INFERRED: 10 (22%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*