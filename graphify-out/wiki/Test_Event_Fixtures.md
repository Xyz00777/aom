# Test Event Fixtures

> 8 nodes · cohesion 0.25

## Key Concepts

- **tests/conftest.py** (26 connections) — `tests/conftest.py`
- **event_play_start()** (2 connections) — `tests/conftest.py`
- **event_runner_ok_changed()** (2 connections) — `tests/conftest.py`
- **list_hosts_output()** (2 connections) — `tests/conftest.py`
- **Shared test fixtures for AOM test suite.  CRITICAL: All fixtures are IMMUTABLE.** (1 connections) — `tests/conftest.py`
- **v2_runner_on_ok event with changed=True.** (1 connections) — `tests/conftest.py`
- **Sample --list-hosts output.** (1 connections) — `tests/conftest.py`
- **v2_playbook_on_play_start event.** (1 connections) — `tests/conftest.py`

## Relationships

- [json.py](json.py.md) (1 shared connections)
- [deprecated_removed_line](deprecated_removed_line.md) (1 shared connections)
- [deprecation_warning_line](deprecation_warning_line.md) (1 shared connections)
- [event_playbook_start](event_playbook_start.md) (1 shared connections)
- [event_runner_failed](event_runner_failed.md) (1 shared connections)
- [event_runner_failed_ignore](event_runner_failed_ignore.md) (1 shared connections)
- [event_runner_ok](event_runner_ok.md) (1 shared connections)
- [event_runner_skipped](event_runner_skipped.md) (1 shared connections)
- [event_runner_start](event_runner_start.md) (1 shared connections)
- [event_runner_unreachable](event_runner_unreachable.md) (1 shared connections)
- [event_stats](event_stats.md) (1 shared connections)
- [event_task_start](event_task_start.md) (1 shared connections)

## Source Files

- `tests/conftest.py`

## Audit Trail

- EXTRACTED: 36 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*