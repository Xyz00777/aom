# Session Replay Driver

> 20 nodes · cohesion 0.10

## Key Concepts

- **TestAppConfigValidation** (15 connections) — `tests/unit/test_config.py`
- **.test_log_max_lines_above_maximum_raises_error()** (3 connections) — `tests/unit/test_config.py`
- **.test_log_max_lines_below_minimum_raises_error()** (3 connections) — `tests/unit/test_config.py`
- **.test_log_max_lines_ge_1000()** (3 connections) — `tests/unit/test_config.py`
- **.test_session_keep_count_below_minimum_raises_error()** (3 connections) — `tests/unit/test_config.py`
- **.test_session_keep_count_ge_1()** (3 connections) — `tests/unit/test_config.py`
- **.test_session_keep_count_negative_raises_error()** (3 connections) — `tests/unit/test_config.py`
- **.test_session_keep_days_below_minimum_raises_error()** (3 connections) — `tests/unit/test_config.py`
- **.test_session_keep_days_ge_1()** (3 connections) — `tests/unit/test_config.py`
- **.test_session_keep_days_negative_raises_error()** (3 connections) — `tests/unit/test_config.py`
- **Tests for Pydantic field constraints - TC-316, TC-317, TC-318.** (1 connections) — `tests/unit/test_config.py`
- **TC-318: log_max_lines minimum is 1000.** (1 connections) — `tests/unit/test_config.py`
- **TC-318: log_max_lines below 1000 raises ValidationError.** (1 connections) — `tests/unit/test_config.py`
- **TC-318: log_max_lines above 100000 raises ValidationError.** (1 connections) — `tests/unit/test_config.py`
- **TC-318: session_keep_count minimum is 1.** (1 connections) — `tests/unit/test_config.py`
- **TC-318: session_keep_count below 1 raises ValidationError.** (1 connections) — `tests/unit/test_config.py`
- **TC-318: session_keep_count negative raises ValidationError.** (1 connections) — `tests/unit/test_config.py`
- **TC-318: session_keep_days minimum is 1.** (1 connections) — `tests/unit/test_config.py`
- **TC-318: session_keep_days below 1 raises ValidationError.** (1 connections) — `tests/unit/test_config.py`
- **TC-318: session_keep_days negative raises ValidationError.** (1 connections) — `tests/unit/test_config.py`

## Relationships

- [Run State Summary Panel](Run_State_Summary_Panel.md) (10 shared connections)
- [Task Definition Live Refresh](Task_Definition_Live_Refresh.md) (2 shared connections)
- [Timestamp Timezone Formatting](Timestamp_Timezone_Formatting.md) (1 shared connections)
- [Renderer Set Definitions](Renderer_Set_Definitions.md) (1 shared connections)

## Source Files

- `tests/unit/test_config.py`

## Audit Trail

- EXTRACTED: 39 (75%)
- INFERRED: 13 (25%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*