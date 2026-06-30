# Golden Frame Tests

> 27 nodes · cohesion 0.11

## Key Concepts

- **test_golden_frames.py** (14 connections) — `tests/compact/test_golden_frames.py`
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
- **_events_empty_run()** (2 connections) — `tests/compact/test_golden_frames.py`
- **_load_recorded()** (2 connections) — `tests/compact/test_golden_frames.py`
- **.__init__()** (1 connections) — `tests/compact/test_golden_frames.py`
- **Full-frame golden snapshots for the compact renderer.  Each test drives ``Compac** (1 connections) — `tests/compact/test_golden_frames.py`
- **Return a thunk that loads a recorded ``tests/fixtures/<name>.jsonl``.** (1 connections) — `tests/compact/test_golden_frames.py`
- **ISO-8601 UTC ``_timestamp`` ``offset_seconds`` past the frozen epoch.** (1 connections) — `tests/compact/test_golden_frames.py`
- **All hosts unreachable → exit code 2, magenta recap lines.** (1 connections) — `tests/compact/test_golden_frames.py`
- **Two plays in one run — exercises the play-boundary header repeat.** (1 connections) — `tests/compact/test_golden_frames.py`
- **Every host skipped → ``_flush_pending_skips`` takes the collapse branch.** (1 connections) — `tests/compact/test_golden_frames.py`
- **One task started, no completion → renderer is told exit=130 (Ctrl+C).** (1 connections) — `tests/compact/test_golden_frames.py`
- **Same shape as single_task_ok, but the renderer args contain --check.** (1 connections) — `tests/compact/test_golden_frames.py`
- **Includes a fabricated ``_event`` to trigger the R5 unknown-events footer.** (1 connections) — `tests/compact/test_golden_frames.py`
- **``ansible-playbook`` exited 0 without emitting any events.      Happens with an** (1 connections) — `tests/compact/test_golden_frames.py`
- *... and 2 more nodes in this community*

## Relationships

- [[Compact Renderer Implementation]] (2 shared connections)
- [[Inventory Auto Detection]] (2 shared connections)
- [[Run Config Key Normalization]] (1 shared connections)

## Source Files

- `tests/compact/test_golden_frames.py`

## Audit Trail

- EXTRACTED: 77 (97%)
- INFERRED: 2 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*