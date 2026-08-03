# PriorRun

> 19 nodes · cohesion 0.19

## Key Concepts

- **PriorRun** (24 connections) — `src/ansible_aom/session/history.py`
- **test_prior_denominator.py** (10 connections) — `tests/compact/test_prior_denominator.py`
- **test_prior_run_line.py** (10 connections) — `tests/compact/test_prior_run_line.py`
- **_play()** (8 connections) — `tests/compact/test_prior_run_line.py`
- **_run()** (7 connections) — `tests/compact/test_prior_denominator.py`
- **test_prior_run_line_prefers_observed_over_preflight_count()** (5 connections) — `tests/compact/test_prior_run_line.py`
- **_drive_one_task()** (4 connections) — `tests/compact/test_prior_denominator.py`
- **_prior()** (4 connections) — `tests/compact/test_prior_denominator.py`
- **test_no_prior_falls_back_to_seen()** (4 connections) — `tests/compact/test_prior_denominator.py`
- **test_prior_run_line_hours_format()** (4 connections) — `tests/compact/test_prior_run_line.py`
- **test_prior_run_line_seconds_only_under_a_minute()** (4 connections) — `tests/compact/test_prior_run_line.py`
- **test_prior_run_line_shown_when_prior_exists()** (4 connections) — `tests/compact/test_prior_run_line.py`
- **test_loose_prior_seeds_estimated_total()** (3 connections) — `tests/compact/test_prior_denominator.py`
- **test_strict_prior_seeds_plain_total()** (3 connections) — `tests/compact/test_prior_denominator.py`
- **test_prior_run_line_is_omitted_when_none()** (3 connections) — `tests/compact/test_prior_run_line.py`
- **Stats from the most recent matching prior session.** (1 connections) — `src/ansible_aom/session/history.py`
- **Renderer seeds the task denominator from a matching prior run.  Preflight ``--li** (1 connections) — `tests/compact/test_prior_denominator.py`
- **Snapshot-ish tests for the prior-run line in the preflight summary.** (1 connections) — `tests/compact/test_prior_run_line.py`
- **Dynamic-include playbooks: preflight sees 4 but the run had 110.      The hint s** (1 connections) — `tests/compact/test_prior_run_line.py`

## Relationships

- [CompactRenderer](CompactRenderer.md) (6 shared connections)
- [history.py](history.py.md) (6 shared connections)
- [format_preflight_summary](format_preflight_summary.md) (5 shared connections)
- [renderer.py](renderer.py.md) (4 shared connections)
- [PlayDefinition](PlayDefinition.md) (3 shared connections)
- [find_previous_run](find_previous_run.md) (2 shared connections)
- [Shift Modifier Keybindings](Shift_Modifier_Keybindings.md) (2 shared connections)
- [HostRunState](HostRunState.md) (2 shared connections)
- [_BoundedSet](_BoundedSet.md) (1 shared connections)
- [json.py](json.py.md) (1 shared connections)
- [Renderer](Renderer.md) (1 shared connections)
- [test_history_roundtrip.py](test_history_roundtrip.py.md) (1 shared connections)

## Source Files

- `src/ansible_aom/session/history.py`
- `tests/compact/test_prior_denominator.py`
- `tests/compact/test_prior_run_line.py`

## Audit Trail

- EXTRACTED: 93 (92%)
- INFERRED: 8 (8%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*