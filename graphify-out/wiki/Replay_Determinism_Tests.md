# Replay Determinism Tests

> 33 nodes · cohesion 0.10

## Key Concepts

- **test_replay_determinism.py** (22 connections) — `tests/integration/test_replay_determinism.py`
- **_record_live_compact()** (10 connections) — `tests/integration/test_replay_determinism.py`
- **CaptureFixture** (9 connections)
- **_record_live_json()** (8 connections) — `tests/integration/test_replay_determinism.py`
- **_replay_compact()** (8 connections) — `tests/integration/test_replay_determinism.py`
- **test_compact_record_then_replay_matches()** (7 connections) — `tests/integration/test_replay_determinism.py`
- **test_compact_replay_is_idempotent()** (7 connections) — `tests/integration/test_replay_determinism.py`
- **test_json_record_then_replay_matches()** (7 connections) — `tests/integration/test_replay_determinism.py`
- **_replay_json()** (6 connections) — `tests/integration/test_replay_determinism.py`
- **_empty_preflight()** (5 connections) — `tests/integration/test_replay_determinism.py`
- **normalize_render_output()** (5 connections) — `tests/_utils.py`
- **_fake_ansible_command()** (4 connections) — `tests/integration/test_replay_determinism.py`
- **test_tree_replay_keeps_run_once_rows_separate_across_serial_windows()** (4 connections) — `tests/integration/test_replay_determinism.py`
- **test_tree_replay_keeps_same_name_task_rows_separate_across_frames()** (4 connections) — `tests/integration/test_replay_determinism.py`
- **_utils.py** (4 connections) — `tests/_utils.py`
- **normalize_json_summary()** (4 connections) — `tests/_utils.py`
- **_events_same_name_concurrent_tasks_repro()** (2 connections) — `tests/integration/test_replay_determinism.py`
- **_events_serial_run_once_repro()** (2 connections) — `tests/integration/test_replay_determinism.py`
- **_events_multi_host_mixed()** (1 connections) — `tests/integration/test_replay_determinism.py`
- **_events_single_ok()** (1 connections) — `tests/integration/test_replay_determinism.py`
- **_events_with_failure()** (1 connections) — `tests/integration/test_replay_determinism.py`
- **Build a (cmd, args) pair that emits ``events`` as JSONL then exits.** (1 connections) — `tests/integration/test_replay_determinism.py`
- **Preflight result that contributes nothing — mirrors a fake shim where     ``--li** (1 connections) — `tests/integration/test_replay_determinism.py`
- **Run the compact renderer live; return (session_id, captured_stdout).** (1 connections) — `tests/integration/test_replay_determinism.py`
- **Replay through a fresh CompactRenderer; return captured stdout.** (1 connections) — `tests/integration/test_replay_determinism.py`
- *... and 8 more nodes in this community*

## Relationships

- [[Run Config Key Normalization]] (7 shared connections)
- [[Replay Frame Signatures]] (3 shared connections)
- [[Renderer Parity Invariant]] (2 shared connections)
- [[Playbook Run Integration Tests]] (2 shared connections)
- [[Compact Renderer Implementation]] (2 shared connections)
- [[JSON Renderer]] (2 shared connections)
- [[Session Replay Round Trip]] (2 shared connections)
- [[Playbook Event Parsing]] (2 shared connections)
- [[Role Group Task Models]] (1 shared connections)

## Source Files

- `tests/_utils.py`
- `tests/integration/test_replay_determinism.py`

## Audit Trail

- EXTRACTED: 123 (92%)
- INFERRED: 10 (8%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*