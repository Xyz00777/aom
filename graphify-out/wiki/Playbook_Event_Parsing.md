# Playbook Event Parsing

> 21 nodes · cohesion 0.12

## Key Concepts

- **Any** (45 connections)
- **iter_tree_frames()** (10 connections) — `src/ansible_aom/core/replay.py`
- **._handle_v2_playbook_on_play_start()** (8 connections) — `src/ansible_aom/core/models.py`
- **._finalize_play()** (6 connections) — `src/ansible_aom/core/models.py`
- **_parse_timestamp()** (5 connections) — `src/ansible_aom/core/models.py`
- **._handle_v2_playbook_on_stats()** (5 connections) — `src/ansible_aom/core/models.py`
- **_parse_play_window_start()** (4 connections) — `src/ansible_aom/core/models.py`
- **.handle_event()** (4 connections) — `src/ansible_aom/core/models.py`
- **._handle_v2_playbook_on_start()** (4 connections) — `src/ansible_aom/core/models.py`
- **replay.py** (4 connections) — `src/ansible_aom/core/replay.py`
- **_event_timestamp()** (4 connections) — `src/ansible_aom/core/replay.py`
- **.record_event()** (3 connections) — `src/ansible_aom/session/store.py`
- **Handle v2_playbook_on_start event.** (2 connections) — `src/ansible_aom/core/models.py`
- **Handle v2_playbook_on_stats event.          Also clean up any hosts still stuck** (1 connections) — `src/ansible_aom/core/models.py`
- **Parse timestamp from event, defaulting to current time.** (1 connections) — `src/ansible_aom/core/models.py`
- **Extract the window discriminator from ``play.duration.start`` if present.** (1 connections) — `src/ansible_aom/core/models.py`
- **Process a JSONL event and update state.** (1 connections) — `src/ansible_aom/core/models.py`
- **Force-complete a play whose work is definitively done.          Any host still m** (1 connections) — `src/ansible_aom/core/models.py`
- **Deterministic replay helpers for frame-by-frame tree capture.  These helpers sta** (1 connections) — `src/ansible_aom/core/replay.py`
- **Yield a tree frame after each JSONL event.      The same ``TreeProjection`` inst** (1 connections) — `src/ansible_aom/core/replay.py`
- **Record a JSONL event to the session file.          Args:             session_id:** (1 connections) — `src/ansible_aom/session/store.py`

## Relationships

- [[Runtime Event Handlers]] (11 shared connections)
- [[Run History Mining]] (11 shared connections)
- [[Run State Summary Panel]] (6 shared connections)
- [[Session Replay Driver]] (3 shared connections)
- [[CPU Sampling Probing]] (2 shared connections)
- [[Host Collection Helpers]] (2 shared connections)
- [[Role Group Task Models]] (2 shared connections)
- [[Run State Completion Recap]] (2 shared connections)
- [[Play Definition Tree Population]] (2 shared connections)
- [[Replay Determinism Tests]] (2 shared connections)
- [[Session ID Completion]] (1 shared connections)
- [[Diagnostics Record Building]] (1 shared connections)

## Source Files

- `src/ansible_aom/core/models.py`
- `src/ansible_aom/core/replay.py`
- `src/ansible_aom/session/store.py`

## Audit Trail

- EXTRACTED: 108 (96%)
- INFERRED: 4 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*