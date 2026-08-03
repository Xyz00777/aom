# Include Import Role Tasks

> 29 nodes · cohesion 0.11

## Key Concepts

- **_make_partial_session()** (9 connections) — `tests/unit/test_event_store_crash_recovery.py`
- **Path** (9 connections)
- **test_event_store_crash_recovery.py** (7 connections) — `tests/unit/test_event_store_crash_recovery.py`
- **.test_load_session_warns_when_meta_missing()** (6 connections) — `tests/unit/test_event_store_crash_recovery.py`
- **.test_replay_warns_when_meta_missing()** (6 connections) — `tests/unit/test_event_store_crash_recovery.py`
- **_spawn_killed_writer()** (5 connections) — `tests/unit/test_event_store_crash_recovery.py`
- **TestLoadSessionMissingMeta** (5 connections) — `tests/unit/test_event_store_crash_recovery.py`
- **.test_load_session_parses_events_when_meta_missing()** (5 connections) — `tests/unit/test_event_store_crash_recovery.py`
- **.test_load_session_returns_non_none_for_missing_meta()** (5 connections) — `tests/unit/test_event_store_crash_recovery.py`
- **TestReplayContinuesWithMissingMeta** (5 connections) — `tests/unit/test_event_store_crash_recovery.py`
- **.test_replay_exits_zero_with_missing_meta()** (5 connections) — `tests/unit/test_event_store_crash_recovery.py`
- **.test_replay_still_drives_renderer_with_missing_meta()** (5 connections) — `tests/unit/test_event_store_crash_recovery.py`
- **.test_replay_subprocess_survives_sigkill()** (5 connections) — `tests/unit/test_event_store_crash_recovery.py`
- **TestSubprocessReplayAfterSigkill** (3 connections) — `tests/unit/test_event_store_crash_recovery.py`
- **LogCaptureFixture** (2 connections)
- **CompletedProcess** (1 connections)
- **Crash-recovery regression tests (Phase 8 / Task 8.2).  What this test pins -----** (1 connections) — `tests/unit/test_event_store_crash_recovery.py`
- **Spawn a real Python subprocess that writes events, then SIGKILL it.      The sub** (1 connections) — `tests/unit/test_event_store_crash_recovery.py`
- **``load_session`` degrades gracefully when meta.json is missing.** (1 connections) — `tests/unit/test_event_store_crash_recovery.py`
- **A directory with only events.jsonl still loads (returns a dict).** (1 connections) — `tests/unit/test_event_store_crash_recovery.py`
- **Events from events.jsonl are still loaded into the result.** (1 connections) — `tests/unit/test_event_store_crash_recovery.py`
- **The crash-recovery warning is emitted at WARNING level.          This is the use** (1 connections) — `tests/unit/test_event_store_crash_recovery.py`
- **``replay_session`` continues the replay instead of exploding.** (1 connections) — `tests/unit/test_event_store_crash_recovery.py`
- **replay_session() returns 0 against a partial session.** (1 connections) — `tests/unit/test_event_store_crash_recovery.py`
- **Every event on disk reaches the renderer, even with no meta.** (1 connections) — `tests/unit/test_event_store_crash_recovery.py`
- *... and 4 more nodes in this community*

## Relationships

- [Include Role Discovery](Include_Role_Discovery.md) (4 shared connections)
- [Hide State Normalization](Hide_State_Normalization.md) (3 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (1 shared connections)

## Source Files

- `tests/unit/test_event_store_crash_recovery.py`

## Audit Trail

- EXTRACTED: 89 (93%)
- INFERRED: 7 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*