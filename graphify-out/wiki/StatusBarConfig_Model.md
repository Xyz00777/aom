# StatusBarConfig Model

> 37 nodes · cohesion 0.08

## Key Concepts

- **store.py** (34 connections) — `src/ansible_aom/session/store.py`
- **parse_iso_timestamp()** (19 connections) — `src/ansible_aom/core/timestamp.py`
- **drivers/replay.py** (19 connections) — `src/ansible_aom/drivers/replay.py`
- **overhead.py** (13 connections) — `src/ansible_aom/core/overhead.py`
- **timestamp.py** (10 connections) — `src/ansible_aom/core/timestamp.py`
- **cleanup_old_sessions()** (10 connections) — `src/ansible_aom/session/store.py`
- **TestSessionRotation** (7 connections) — `tests/integration/test_session.py`
- **_parse_iso8601()** (5 connections) — `src/ansible_aom/core/overhead.py`
- **_parse_timestamp()** (5 connections) — `src/ansible_aom/drivers/replay.py`
- **test_session_meta_persistence.py** (5 connections) — `tests/unit/test_session_meta_persistence.py`
- **.test_cleanup_keeps_max_count()** (4 connections) — `tests/integration/test_session.py`
- **.test_cleanup_keeps_recent_sessions()** (4 connections) — `tests/integration/test_session.py`
- **.test_cleanup_removes_old_sessions()** (4 connections) — `tests/integration/test_session.py`
- **.test_cleanup_respects_both_limits()** (4 connections) — `tests/integration/test_session.py`
- **test_end_session_without_counts_writes_nulls()** (4 connections) — `tests/unit/test_session_meta_persistence.py`
- **test_end_session_persists_task_and_host_counts()** (3 connections) — `tests/unit/test_session_meta_persistence.py`
- **datetime** (2 connections)
- **datetime** (2 connections)
- **datetime** (2 connections)
- **session/__init__.py** (2 connections) — `src/ansible_aom/session/__init__.py`
- **Path** (2 connections)
- **Per-task overhead analysis from JSONL event streams.  Why this exists ----------** (1 connections) — `src/ansible_aom/core/overhead.py`
- **Parse the ISO-8601 timestamps emitted by ansible.posix.jsonl.      Returns ``Non** (1 connections) — `src/ansible_aom/core/overhead.py`
- **Canonical ISO 8601 timestamp parsing for ansible-playbook JSONL events.  AOM rea** (1 connections) — `src/ansible_aom/core/timestamp.py`
- **Parse an ISO 8601 timestamp string, tolerating the ``Z`` UTC suffix.      Args:** (1 connections) — `src/ansible_aom/core/timestamp.py`
- *... and 12 more nodes in this community*

## Relationships

- [Run Config Key Normalization](Run_Config_Key_Normalization.md) (12 shared connections)
- [Color ASCII Fallback](Color_ASCII_Fallback.md) (7 shared connections)
- [Status Bar Widget](Status_Bar_Widget.md) (7 shared connections)
- [Include Role Discovery](Include_Role_Discovery.md) (4 shared connections)
- [Status Icon Animation Tests](Status_Icon_Animation_Tests.md) (3 shared connections)
- [Log Filter Helpers](Log_Filter_Helpers.md) (3 shared connections)
- [List-Tasks Failure Handling](List-Tasks_Failure_Handling.md) (3 shared connections)
- [Property Based Tests](Property_Based_Tests.md) (3 shared connections)
- [Heartbeat Liveness Tracker](Heartbeat_Liveness_Tracker.md) (2 shared connections)
- [Ansible Posix Availability](Ansible_Posix_Availability.md) (2 shared connections)
- [Loop Item Stream Tests](Loop_Item_Stream_Tests.md) (2 shared connections)
- [Hide State Normalization](Hide_State_Normalization.md) (2 shared connections)

## Source Files

- `src/ansible_aom/core/overhead.py`
- `src/ansible_aom/core/timestamp.py`
- `src/ansible_aom/drivers/replay.py`
- `src/ansible_aom/session/__init__.py`
- `src/ansible_aom/session/store.py`
- `tests/integration/test_session.py`
- `tests/unit/test_session_meta_persistence.py`

## Audit Trail

- EXTRACTED: 153 (87%)
- INFERRED: 23 (13%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*