# RunSummary Schema Contract

> 29 nodes · cohesion 0.10

## Key Concepts

- **test_golden_frames.py** (17 connections) — `tests/compact/test_golden_frames.py`
- **_ts()** (8 connections) — `tests/compact/test_golden_frames.py`
- **GoldenFixture** (6 connections) — `tests/compact/test_golden_frames.py`
- **_render()** (6 connections) — `tests/compact/test_golden_frames.py`
- **test_golden_frame()** (6 connections) — `tests/compact/test_golden_frames.py`
- **_golden_path()** (4 connections) — `tests/compact/test_golden_frames.py`
- **_events_all_skipped()** (3 connections) — `tests/compact/test_golden_frames.py`
- **_events_all_unreachable()** (3 connections) — `tests/compact/test_golden_frames.py`
- **_events_cancelled()** (3 connections) — `tests/compact/test_golden_frames.py`
- **_events_dry_run_check()** (3 connections) — `tests/compact/test_golden_frames.py`
- **_events_multiple_plays()** (3 connections) — `tests/compact/test_golden_frames.py`
- **_events_unknown_event_type()** (3 connections) — `tests/compact/test_golden_frames.py`
- **_load_recorded()** (3 connections) — `tests/compact/test_golden_frames.py`
- **_events_empty_run()** (2 connections) — `tests/compact/test_golden_frames.py`
- **MonkeyPatch** (2 connections)
- **.__init__()** (1 connections) — `tests/compact/test_golden_frames.py`
- **Path** (1 connections)
- **Full-frame golden snapshots for the compact renderer.  Each test drives ``Compac** (1 connections) — `tests/compact/test_golden_frames.py`
- **Return a thunk that loads a recorded ``tests/fixtures/<name>.jsonl``.** (1 connections) — `tests/compact/test_golden_frames.py`
- **ISO-8601 UTC ``_timestamp`` ``offset_seconds`` past the frozen epoch.** (1 connections) — `tests/compact/test_golden_frames.py`
- **All hosts unreachable → exit code 2, magenta recap lines.** (1 connections) — `tests/compact/test_golden_frames.py`
- **Two plays in one run — exercises the play-boundary header repeat.** (1 connections) — `tests/compact/test_golden_frames.py`
- **Every host skipped → ``_flush_pending_skips`` takes the collapse branch.** (1 connections) — `tests/compact/test_golden_frames.py`
- **One task started, no completion → renderer is told exit=130 (Ctrl+C).** (1 connections) — `tests/compact/test_golden_frames.py`
- **Same shape as single_task_ok, but the renderer args contain --check.** (1 connections) — `tests/compact/test_golden_frames.py`
- *... and 4 more nodes in this community*

## Relationships

- [CompactRenderer](CompactRenderer.md) (2 shared connections)
- [renderer.py](renderer.py.md) (1 shared connections)
- [IO](IO.md) (1 shared connections)
- [json.py](json.py.md) (1 shared connections)
- [text.py](text.py.md) (1 shared connections)

## Source Files

- `tests/compact/test_golden_frames.py`

## Audit Trail

- EXTRACTED: 84 (98%)
- INFERRED: 2 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*