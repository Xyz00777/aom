# List-Tasks Failure Handling

> 12 nodes · cohesion 0.20

## Key Concepts

- **core/replay.py** (12 connections) — `src/ansible_aom/core/replay.py`
- **iter_tree_frames()** (10 connections) — `src/ansible_aom/core/replay.py`
- **_event_timestamp()** (5 connections) — `src/ansible_aom/core/replay.py`
- **test_tree_frame_signatures_are_deterministic_and_stable()** (4 connections) — `tests/integration/test_replay_determinism.py`
- **test_tree_replay_keeps_run_once_rows_separate_across_serial_windows()** (4 connections) — `tests/integration/test_replay_determinism.py`
- **_tree_frame_signatures()** (3 connections) — `tests/integration/test_replay_determinism.py`
- **datetime** (2 connections)
- **_events_serial_run_once_repro()** (2 connections) — `tests/integration/test_replay_determinism.py`
- **Deterministic replay helpers for frame-by-frame tree capture.  These helpers sta** (1 connections) — `src/ansible_aom/core/replay.py`
- **Yield a tree frame after each JSONL event.      The same ``TreeProjection`` inst** (1 connections) — `src/ansible_aom/core/replay.py`
- **Recorded replay frames should be reproducible and keep row order stable.** (1 connections) — `tests/integration/test_replay_determinism.py`
- **Serial play windows must not reuse the prior run_once task row.** (1 connections) — `tests/integration/test_replay_determinism.py`

## Relationships

- [test_replay_determinism.py](test_replay_determinism.py.md) (6 shared connections)
- [Heartbeat Liveness Tracker](Heartbeat_Liveness_Tracker.md) (3 shared connections)
- [CLI Interface Tests](CLI_Interface_Tests.md) (3 shared connections)
- [StatusBarConfig Model](StatusBarConfig_Model.md) (3 shared connections)
- [Status Icon Animation Tests](Status_Icon_Animation_Tests.md) (2 shared connections)
- [tree.py](tree.py.md) (1 shared connections)
- [.test_field_exists_with_default_false](test_field_exists_with_default_false.md) (1 shared connections)
- [Renderer Module Init](Renderer_Module_Init.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/replay.py`
- `tests/integration/test_replay_determinism.py`

## Audit Trail

- EXTRACTED: 39 (85%)
- INFERRED: 7 (15%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*