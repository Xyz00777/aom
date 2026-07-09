# Community 602

> 31 nodes · cohesion 0.12

## Key Concepts

- **test_replay_determinism.py** (24 connections) — `tests/integration/test_replay_determinism.py`
- **_record_live_compact()** (10 connections) — `tests/integration/test_replay_determinism.py`
- **_record_live_json()** (8 connections) — `tests/integration/test_replay_determinism.py`
- **_replay_compact()** (8 connections) — `tests/integration/test_replay_determinism.py`
- **CaptureFixture** (7 connections)
- **Path** (7 connections)
- **test_compact_record_then_replay_matches()** (7 connections) — `tests/integration/test_replay_determinism.py`
- **test_compact_replay_is_idempotent()** (7 connections) — `tests/integration/test_replay_determinism.py`
- **test_json_record_then_replay_matches()** (7 connections) — `tests/integration/test_replay_determinism.py`
- **_replay_json()** (6 connections) — `tests/integration/test_replay_determinism.py`
- **_empty_preflight()** (5 connections) — `tests/integration/test_replay_determinism.py`
- **_utils.py** (5 connections) — `tests/_utils.py`
- **normalize_render_output()** (5 connections) — `tests/_utils.py`
- **_fake_ansible_command()** (4 connections) — `tests/integration/test_replay_determinism.py`
- **test_tree_replay_keeps_same_name_task_rows_separate_across_frames()** (4 connections) — `tests/integration/test_replay_determinism.py`
- **normalize_json_summary()** (4 connections) — `tests/_utils.py`
- **_events_same_name_concurrent_tasks_repro()** (2 connections) — `tests/integration/test_replay_determinism.py`
- **_events_multi_host_mixed()** (1 connections) — `tests/integration/test_replay_determinism.py`
- **_events_single_ok()** (1 connections) — `tests/integration/test_replay_determinism.py`
- **_events_with_failure()** (1 connections) — `tests/integration/test_replay_determinism.py`
- **Build a (cmd, args) pair that emits ``events`` as JSONL then exits.** (1 connections) — `tests/integration/test_replay_determinism.py`
- **Preflight result that contributes nothing — mirrors a fake shim where     ``--li** (1 connections) — `tests/integration/test_replay_determinism.py`
- **Run the compact renderer live; return (session_id, captured_stdout).** (1 connections) — `tests/integration/test_replay_determinism.py`
- **Replay through a fresh CompactRenderer; return captured stdout.** (1 connections) — `tests/integration/test_replay_determinism.py`
- **Live compact stdout, normalised, must equal replayed compact stdout.** (1 connections) — `tests/integration/test_replay_determinism.py`
- *... and 6 more nodes in this community*

## Relationships

- [List-Tasks Failure Handling](List-Tasks_Failure_Handling.md) (5 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (2 shared connections)
- [Renderer Module Init](Renderer_Module_Init.md) (2 shared connections)
- [Tree Block Animation](Tree_Block_Animation.md) (2 shared connections)
- [App Configuration Settings](App_Configuration_Settings.md) (2 shared connections)
- [Inspect Data Model Builders](Inspect_Data_Model_Builders.md) (2 shared connections)
- [Hide State Normalization](Hide_State_Normalization.md) (2 shared connections)
- [Secret Redaction Configuration](Secret_Redaction_Configuration.md) (1 shared connections)

## Source Files

- `tests/_utils.py`
- `tests/integration/test_replay_determinism.py`

## Audit Trail

- EXTRACTED: 125 (93%)
- INFERRED: 9 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*