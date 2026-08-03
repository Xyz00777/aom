# Renderer Implementations

> 20 nodes · cohesion 0.10

## Key Concepts

- **TestConfigModelBasics** (15 connections) — `tests/unit/test_config.py`
- **.test_app_config_is_pydantic_settings()** (3 connections) — `tests/unit/test_config.py`
- **.test_config_model_model_dump()** (3 connections) — `tests/unit/test_config.py`
- **.test_config_model_string_values_in_lists()** (3 connections) — `tests/unit/test_config.py`
- **.test_config_model_validation_error_on_invalid_type()** (3 connections) — `tests/unit/test_config.py`
- **.test_status_bar_config_is_pydantic_model()** (3 connections) — `tests/unit/test_config.py`
- **.test_warnings_config_is_pydantic_model()** (3 connections) — `tests/unit/test_config.py`
- **.test_config_model_model_validate()** (2 connections) — `tests/unit/test_config.py`
- **.test_config_model_validation_error_on_invalid_nested()** (2 connections) — `tests/unit/test_config.py`
- **.test_redaction_config_is_pydantic_model()** (2 connections) — `tests/unit/test_config.py`
- **Tests for Pydantic BaseModel basics - TC-316, TC-317.** (1 connections) — `tests/unit/test_config.py`
- **StatusBarConfig is a Pydantic model.** (1 connections) — `tests/unit/test_config.py`
- **RedactionConfig is a Pydantic model.** (1 connections) — `tests/unit/test_config.py`
- **WarningsConfig is a Pydantic model.** (1 connections) — `tests/unit/test_config.py`
- **AppConfig is a Pydantic Settings model.** (1 connections) — `tests/unit/test_config.py`
- **TC-316: ValidationError raised for invalid field types.** (1 connections) — `tests/unit/test_config.py`
- **TC-316: ValidationError for invalid nested types.** (1 connections) — `tests/unit/test_config.py`
- **String values in lists are preserved.** (1 connections) — `tests/unit/test_config.py`
- **Pydantic model_dump() returns dict of fields.** (1 connections) — `tests/unit/test_config.py`
- **Pydantic model_validate() creates model from dict.** (1 connections) — `tests/unit/test_config.py`

## Relationships

- [Task Definition Live Refresh](Task_Definition_Live_Refresh.md) (7 shared connections)
- [Run State Summary Panel](Run_State_Summary_Panel.md) (2 shared connections)
- [Timestamp Timezone Formatting](Timestamp_Timezone_Formatting.md) (1 shared connections)
- [Renderer Set Definitions](Renderer_Set_Definitions.md) (1 shared connections)

## Source Files

- `tests/unit/test_config.py`

## Audit Trail

- EXTRACTED: 39 (80%)
- INFERRED: 10 (20%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*