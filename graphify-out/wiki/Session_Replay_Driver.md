# Session Replay Driver

> 34 nodes · cohesion 0.07

## Key Concepts

- **FakeRenderer** (22 connections) — `tests/unit/test_event_source.py`
- **ReplayDriver** (10 connections) — `src/ansible_aom/drivers/replay.py`
- **test_event_source.py** (10 connections) — `tests/unit/test_event_source.py`
- **test_live_driver_drives_renderer_with_fake_subprocess()** (6 connections) — `tests/unit/test_event_source.py`
- **test_replay_driver_drives_renderer_end_to_end()** (6 connections) — `tests/unit/test_event_source.py`
- **_write_session()** (6 connections) — `tests/unit/test_event_source.py`
- **test_replay_driver_missing_session_returns_1()** (5 connections) — `tests/unit/test_event_source.py`
- **.drive()** (4 connections) — `src/ansible_aom/drivers/replay.py`
- **test_replay_driver_satisfies_event_source()** (4 connections) — `tests/unit/test_event_source.py`
- **.__init__()** (3 connections) — `src/ansible_aom/drivers/replay.py`
- **.set_definitions()** (2 connections) — `tests/unit/test_event_source.py`
- **.update_state()** (2 connections) — `tests/unit/test_event_source.py`
- **test_event_source_is_runtime_checkable()** (2 connections) — `tests/unit/test_event_source.py`
- **.session_id()** (1 connections) — `src/ansible_aom/drivers/replay.py`
- **.add_warning()** (1 connections) — `tests/unit/test_event_source.py`
- **.handle_completion()** (1 connections) — `tests/unit/test_event_source.py`
- **.handle_interactive_prompt()** (1 connections) — `tests/unit/test_event_source.py`
- **.handle_password_prompt()** (1 connections) — `tests/unit/test_event_source.py`
- **.__init__()** (1 connections) — `tests/unit/test_event_source.py`
- **.note_pty_bytes()** (1 connections) — `tests/unit/test_event_source.py`
- **.note_subprocess_active()** (1 connections) — `tests/unit/test_event_source.py`
- **.print_log()** (1 connections) — `tests/unit/test_event_source.py`
- **.set_prior_run()** (1 connections) — `tests/unit/test_event_source.py`
- **.start()** (1 connections) — `tests/unit/test_event_source.py`
- **.stop()** (1 connections) — `tests/unit/test_event_source.py`
- *... and 9 more nodes in this community*

## Relationships

- [[Run Config Key Normalization]] (6 shared connections)
- [[Replay CLI Subcommand]] (3 shared connections)
- [[CLI Main Entry Point]] (3 shared connections)
- [[Playbook Event Parsing]] (3 shared connections)
- [[Renderer Event Protocol]] (2 shared connections)
- [[Session Replay Round Trip]] (1 shared connections)
- [[Inventory Auto Detection]] (1 shared connections)

## Source Files

- `src/ansible_aom/drivers/replay.py`
- `tests/unit/test_event_source.py`

## Audit Trail

- EXTRACTED: 92 (89%)
- INFERRED: 11 (11%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*