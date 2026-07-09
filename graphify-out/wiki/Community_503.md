# Community 503

> 8 nodes · cohesion 0.36

## Key Concepts

- **TestAsyncPollDoesNotLeakDictIntoLoopItem** (10 connections) — `tests/unit/test_inspect_model.py`
- **_make_loop_item()** (7 connections) — `src/ansible_aom/core/inspect_model.py`
- **LoopItem** (4 connections) — `src/ansible_aom/core/inspect_model.py`
- **.test_make_loop_item_async_poll_does_not_leak_dict()** (2 connections) — `tests/unit/test_inspect_model.py`
- **.test_make_loop_item_async_poll_failed_flag_set_correctly()** (2 connections) — `tests/unit/test_inspect_model.py`
- **.test_make_loop_item_normal_loop_item_unaffected()** (2 connections) — `tests/unit/test_inspect_model.py`
- **One entry from a task's loop ``results[]`` array.** (1 connections) — `src/ansible_aom/core/inspect_model.py`
- **Async-poll bookkeeping payloads must not leak the raw dict into LoopItem.label.** (1 connections) — `tests/unit/test_inspect_model.py`

## Relationships

- [Playbook Parser Integration Tests](Playbook_Parser_Integration_Tests.md) (5 shared connections)
- [Data Model Unit Tests](Data_Model_Unit_Tests.md) (2 shared connections)
- [Heartbeat Liveness Tracker](Heartbeat_Liveness_Tracker.md) (1 shared connections)
- [PTY Buffer Stall Handling](PTY_Buffer_Stall_Handling.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/inspect_model.py`
- `tests/unit/test_inspect_model.py`

## Audit Trail

- EXTRACTED: 16 (55%)
- INFERRED: 13 (45%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*