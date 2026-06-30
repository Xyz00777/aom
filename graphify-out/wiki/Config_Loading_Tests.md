# Config Loading Tests

> 10 nodes · cohesion 0.20

## Key Concepts

- **TestConfigFromEnvironment** (10 connections) — `tests/unit/test_config.py`
- **.test_app_config_can_be_created_without_file()** (3 connections) — `tests/unit/test_config.py`
- **.test_app_config_uses_defaults_when_no_env()** (3 connections) — `tests/unit/test_config.py`
- **.test_app_config_with_nested_models()** (3 connections) — `tests/unit/test_config.py`
- **.test_status_bar_config_equality()** (3 connections) — `tests/unit/test_config.py`
- **Tests for environment variable and YAML config loading.** (1 connections) — `tests/unit/test_config.py`
- **AppConfig can be instantiated without a config file.** (1 connections) — `tests/unit/test_config.py`
- **AppConfig uses defaults when no environment variables set.** (1 connections) — `tests/unit/test_config.py`
- **StatusBarConfig instances with same values are equal.** (1 connections) — `tests/unit/test_config.py`
- **AppConfig properly creates nested config models.** (1 connections) — `tests/unit/test_config.py`

## Relationships

- [[App Configuration Settings]] (4 shared connections)
- [[Status Bar Warning Panels]] (2 shared connections)
- [[Secret Redaction Configuration]] (1 shared connections)
- [[Warnings Display Config]] (1 shared connections)
- [[App Config Model Tests]] (1 shared connections)

## Source Files

- `tests/unit/test_config.py`

## Audit Trail

- EXTRACTED: 19 (70%)
- INFERRED: 8 (30%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*