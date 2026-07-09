# StatusBarConfig Model

> 19 nodes · cohesion 0.13

## Key Concepts

- **parse_iso_timestamp()** (11 connections) — `src/ansible_aom/core/timestamp.py`
- **cleanup_old_sessions()** (9 connections) — `src/ansible_aom/session/store.py`
- **TestSessionRotation** (7 connections) — `tests/integration/test_session.py`
- **._event_time()** (5 connections) — `src/ansible_aom/compact/renderer.py`
- **.test_cleanup_keeps_max_count()** (4 connections) — `tests/integration/test_session.py`
- **.test_cleanup_keeps_recent_sessions()** (4 connections) — `tests/integration/test_session.py`
- **.test_cleanup_removes_old_sessions()** (4 connections) — `tests/integration/test_session.py`
- **.test_cleanup_respects_both_limits()** (4 connections) — `tests/integration/test_session.py`
- **timestamp.py** (3 connections) — `src/ansible_aom/core/timestamp.py`
- **datetime** (2 connections)
- **Parse ``_timestamp`` from a JSONL event into a Unix float.          Returns ``No** (1 connections) — `src/ansible_aom/compact/renderer.py`
- **Canonical ISO 8601 timestamp parsing for ansible-playbook JSONL events.  AOM rea** (1 connections) — `src/ansible_aom/core/timestamp.py`
- **Parse an ISO 8601 timestamp string, tolerating the ``Z`` UTC suffix.      Args:** (1 connections) — `src/ansible_aom/core/timestamp.py`
- **Remove old sessions based on policy.      Sessions are cleaned up based on:** (1 connections) — `src/ansible_aom/session/store.py`
- **TC-228, TC-229, TC-230: Session rotation and cleanup.** (1 connections) — `tests/integration/test_session.py`
- **TC-228: Keep last N sessions (default 100).** (1 connections) — `tests/integration/test_session.py`
- **TC-228: Cleanup keeps most recent sessions.** (1 connections) — `tests/integration/test_session.py`
- **TC-229: Delete sessions older than N days.** (1 connections) — `tests/integration/test_session.py`
- **Cleanup respects both count and age limits.** (1 connections) — `tests/integration/test_session.py`

## Relationships

- [Run Config Key Normalization](Run_Config_Key_Normalization.md) (7 shared connections)
- [Status Icon Animation Tests](Status_Icon_Animation_Tests.md) (2 shared connections)
- [App Configuration Settings](App_Configuration_Settings.md) (1 shared connections)
- [Heartbeat Liveness Tracker](Heartbeat_Liveness_Tracker.md) (1 shared connections)
- [Playbook Parser Integration Tests](Playbook_Parser_Integration_Tests.md) (1 shared connections)
- [Color ASCII Fallback](Color_ASCII_Fallback.md) (1 shared connections)
- [List-Tasks Failure Handling](List-Tasks_Failure_Handling.md) (1 shared connections)
- [Community 504](Community_504.md) (1 shared connections)
- [JSON Renderer](JSON_Renderer.md) (1 shared connections)
- [Status Bar Widget](Status_Bar_Widget.md) (1 shared connections)
- [Loop Item Line Tests](Loop_Item_Line_Tests.md) (1 shared connections)

## Source Files

- `src/ansible_aom/compact/renderer.py`
- `src/ansible_aom/core/timestamp.py`
- `src/ansible_aom/session/store.py`
- `tests/integration/test_session.py`

## Audit Trail

- EXTRACTED: 42 (68%)
- INFERRED: 20 (32%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*