# test_history_roundtrip.py

> 14 nodes · cohesion 0.21

## Key Concepts

- **test_history_roundtrip.py** (13 connections) — `tests/integration/test_history_roundtrip.py`
- **test_runner_pushes_prior_run_into_renderer()** (8 connections) — `tests/integration/test_history_roundtrip.py`
- **Path** (6 connections)
- **test_different_tags_match_via_fallback()** (6 connections) — `tests/integration/test_history_roundtrip.py`
- **test_failed_session_is_not_returned()** (6 connections) — `tests/integration/test_history_roundtrip.py`
- **test_different_host_count_does_not_match()** (5 connections) — `tests/integration/test_history_roundtrip.py`
- **test_most_recent_completed_wins()** (5 connections) — `tests/integration/test_history_roundtrip.py`
- **test_session_then_history_roundtrip()** (5 connections) — `tests/integration/test_history_roundtrip.py`
- **_fake_ansible_command()** (3 connections) — `tests/integration/test_history_roundtrip.py`
- **End-to-end: write a v1.2 meta.json via SessionManager, look it up via find_previ** (1 connections) — `tests/integration/test_history_roundtrip.py`
- **The runner must look up history and call ``renderer.set_prior_run``.      Pins t** (1 connections) — `tests/integration/test_history_roundtrip.py`
- **Build a (command, args) pair that emits ``events`` as JSONL then exits.** (1 connections) — `tests/integration/test_history_roundtrip.py`
- **Different tags still match via loose fallback (same playbook + host count).** (1 connections) — `tests/integration/test_history_roundtrip.py`
- **End-of-run status==failed sessions are unreliable — skip them.** (1 connections) — `tests/integration/test_history_roundtrip.py`

## Relationships

- [SessionManager](SessionManager.md) (6 shared connections)
- [build_run_config_key](build_run_config_key.md) (5 shared connections)
- [find_previous_run](find_previous_run.md) (5 shared connections)
- [history.py](history.py.md) (2 shared connections)
- [HostRunState](HostRunState.md) (1 shared connections)
- [json.py](json.py.md) (1 shared connections)
- [load_session](load_session.md) (1 shared connections)
- [run_playbook](run_playbook.md) (1 shared connections)
- [PlayDefinition](PlayDefinition.md) (1 shared connections)
- [PriorRun](PriorRun.md) (1 shared connections)

## Source Files

- `tests/integration/test_history_roundtrip.py`

## Audit Trail

- EXTRACTED: 60 (97%)
- INFERRED: 2 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*