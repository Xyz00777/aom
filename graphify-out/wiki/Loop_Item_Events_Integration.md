# Loop Item Events Integration

> 16 nodes · cohesion 0.17

## Key Concepts

- **test_loop_item_events.py** (7 connections) — `tests/integration/test_loop_item_events.py`
- **_run_aom()** (6 connections) — `tests/integration/test_loop_item_events.py`
- **_run_playbook()** (6 connections) — `tests/integration/test_loop_item_events.py`
- **TestLoopItemEvents** (4 connections) — `tests/integration/test_loop_item_events.py`
- **_ansible_collection_paths()** (3 connections) — `tests/integration/test_loop_item_events.py`
- **TestLoopItemStreamingEndToEnd** (3 connections) — `tests/integration/test_loop_item_events.py`
- **.test_aggregate_event_still_emitted()** (2 connections) — `tests/integration/test_loop_item_events.py`
- **.test_item_event_carries_label_under_host()** (2 connections) — `tests/integration/test_loop_item_events.py`
- **.test_one_item_event_per_loop_iteration()** (2 connections) — `tests/integration/test_loop_item_events.py`
- **.test_each_item_line_appears_exactly_once()** (2 connections) — `tests/integration/test_loop_item_events.py`
- **_has_ansible_posix()** (1 connections) — `tests/integration/test_loop_item_events.py`
- **Integration: the bundled ``aom_jsonl`` callback emits per-item loop events.  ``a** (1 connections) — `tests/integration/test_loop_item_events.py`
- **Spawn ``python -m ansible_aom <playbook>`` against a sandboxed HOME.      Exerci** (1 connections) — `tests/integration/test_loop_item_events.py`
- **The full ``aom`` pipeline renders one line per loop item, once each.** (1 connections) — `tests/integration/test_loop_item_events.py`
- **Search-path entries reported by ``ansible-galaxy collection list``.      A sandb** (1 connections) — `tests/integration/test_loop_item_events.py`
- **Run ansible-playbook with the bundled callback; return parsed JSONL events.** (1 connections) — `tests/integration/test_loop_item_events.py`

## Relationships

- [[Run Config Key Normalization]] (2 shared connections)
- [[CLI Help Matrix]] (1 shared connections)

## Source Files

- `tests/integration/test_loop_item_events.py`

## Audit Trail

- EXTRACTED: 43 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*