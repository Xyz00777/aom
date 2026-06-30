# Renderer ETA Wiring

> 18 nodes · cohesion 0.27

## Key Concepts

- **_FakeDisplay** (14 connections) — `tests/integration/test_renderer_eta.py`
- **test_renderer_eta.py** (12 connections) — `tests/integration/test_renderer_eta.py`
- **_setup()** (10 connections) — `tests/integration/test_renderer_eta.py`
- **_complete_task()** (8 connections) — `tests/integration/test_renderer_eta.py`
- **test_fixed_floor_not_scaled_by_fast_variable_task()** (8 connections) — `tests/integration/test_renderer_eta.py`
- **test_long_running_task_burns_estimate_down()** (8 connections) — `tests/integration/test_renderer_eta.py`
- **test_no_estimate_without_prior()** (7 connections) — `tests/integration/test_renderer_eta.py`
- **_task()** (6 connections) — `tests/integration/test_renderer_eta.py`
- **.start()** (5 connections) — `tests/integration/test_renderer_eta.py`
- **_prior()** (5 connections) — `tests/integration/test_renderer_eta.py`
- **test_eta_appears_once_gate_opens()** (3 connections) — `tests/integration/test_renderer_eta.py`
- **test_no_eta_below_warmup_gate()** (3 connections) — `tests/integration/test_renderer_eta.py`
- **test_unmatched_path_does_not_count()** (3 connections) — `tests/integration/test_renderer_eta.py`
- **.__init__()** (1 connections) — `tests/integration/test_renderer_eta.py`
- **.print_log()** (1 connections) — `tests/integration/test_renderer_eta.py`
- **.stop()** (1 connections) — `tests/integration/test_renderer_eta.py`
- **.update()** (1 connections) — `tests/integration/test_renderer_eta.py`
- **Renderer wiring for the live run-duration estimate.  The renderer builds a :clas** (1 connections) — `tests/integration/test_renderer_eta.py`

## Relationships

- [[Compact Renderer Implementation]] (6 shared connections)
- [[Play Definition Tree Population]] (5 shared connections)
- [[Task Definition Live Refresh]] (2 shared connections)
- [[Run History Mining]] (2 shared connections)

## Source Files

- `tests/integration/test_renderer_eta.py`

## Audit Trail

- EXTRACTED: 89 (92%)
- INFERRED: 8 (8%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*