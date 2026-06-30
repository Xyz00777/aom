# Running Animation Frames

> 8 nodes · cohesion 0.25

## Key Concepts

- **get_running_frame()** (7 connections) — `src/ansible_aom/core/icons.py`
- **.test_four_frames_per_second_timing()** (3 connections) — `tests/unit/test_icons.py`
- **.test_get_running_frame_cycles_correctly()** (3 connections) — `tests/unit/test_icons.py`
- **.test_get_running_frame_large_counter()** (3 connections) — `tests/unit/test_icons.py`
- **Get the current animation frame for RUNNING status.      Cycles through the 4 qu** (1 connections) — `src/ansible_aom/core/icons.py`
- **TC-372: get_running_frame cycles through 4 frames correctly.** (1 connections) — `tests/unit/test_icons.py`
- **TC-372: Large counter values still cycle correctly.** (1 connections) — `tests/unit/test_icons.py`
- **TC-372: Animation completes full cycle in 1 second (4 frames @ 4 FPS).** (1 connections) — `tests/unit/test_icons.py`

## Relationships

- [[Status Icon Animation Tests]] (3 shared connections)
- [[Host Overview Table]] (1 shared connections)
- [[Tree Block Animation]] (1 shared connections)
- [[Compact Display Module Layout]] (1 shared connections)

## Source Files

- `src/ansible_aom/core/icons.py`
- `tests/unit/test_icons.py`

## Audit Trail

- EXTRACTED: 12 (60%)
- INFERRED: 8 (40%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*