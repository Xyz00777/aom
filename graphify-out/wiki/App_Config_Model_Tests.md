# App Config Model Tests

> 34 nodes · cohesion 0.06

## Key Concepts

- **test_config.py** (14 connections) — `tests/unit/test_config.py`
- **TestAppConfigYamlFile** (10 connections) — `tests/unit/test_config.py`
- **TestRedactionCustomPatterns** (10 connections) — `tests/unit/test_config.py`
- **TestLoadConfig** (9 connections) — `tests/unit/test_config.py`
- **TestConfigImmutabilityIntent** (8 connections) — `tests/unit/test_config.py`
- **.test_app_config_nested_config_isolation()** (4 connections) — `tests/unit/test_config.py`
- **.test_status_bar_elements_mutation_isolated()** (3 connections) — `tests/unit/test_config.py`
- **.test_custom_patterns_dict_keys()** (3 connections) — `tests/unit/test_config.py`
- **.test_custom_patterns_dict_structure()** (3 connections) — `tests/unit/test_config.py`
- **.test_custom_patterns_multiple_patterns()** (3 connections) — `tests/unit/test_config.py`
- **.test_custom_patterns_with_complex_regex()** (3 connections) — `tests/unit/test_config.py`
- **.test_app_config_with_model_config_dict()** (2 connections) — `tests/unit/test_config.py`
- **.test_yaml_file_default_path()** (2 connections) — `tests/unit/test_config.py`
- **.test_yaml_file_expanded_path()** (2 connections) — `tests/unit/test_config.py`
- **.test_yaml_file_xdg_compliant()** (2 connections) — `tests/unit/test_config.py`
- **.test_load_config_accepts_optional_config_path()** (2 connections) — `tests/unit/test_config.py`
- **.test_load_config_signature_has_str_union_none()** (2 connections) — `tests/unit/test_config.py`
- **Unit tests for configuration models in ansible_aom.core.config.  Test cases cove** (1 connections) — `tests/unit/test_config.py`
- **Tests for Pydantic Settings YAML file integration - TC-304, TC-305, TC-306.** (1 connections) — `tests/unit/test_config.py`
- **TC-304: Default YAML file path is ~/.config/aom/config.yaml.** (1 connections) — `tests/unit/test_config.py`
- **TC-304: YAML path should be expandable to absolute path.** (1 connections) — `tests/unit/test_config.py`
- **TC-304: Config path follows XDG spec (~/.config/aom/config.yaml).** (1 connections) — `tests/unit/test_config.py`
- **AppConfig uses SettingsConfigDict for configuration.** (1 connections) — `tests/unit/test_config.py`
- **Tests for load_config function - TC-304 to TC-306.** (1 connections) — `tests/unit/test_config.py`
- **load_config accepts optional config_path parameter.** (1 connections) — `tests/unit/test_config.py`
- *... and 9 more nodes in this community*

## Relationships

- [[App Configuration Settings]] (9 shared connections)
- [[Secret Redaction Configuration]] (9 shared connections)
- [[Warnings Display Config]] (5 shared connections)
- [[Status Bar Warning Panels]] (5 shared connections)
- [[Config Loading Tests]] (1 shared connections)
- [[Pydantic Model Basics]] (1 shared connections)
- [[Redaction Config Model]] (1 shared connections)
- [[StatusBarConfig Model]] (1 shared connections)
- [[Config Loading Screen]] (1 shared connections)

## Source Files

- `tests/unit/test_config.py`

## Audit Trail

- EXTRACTED: 76 (77%)
- INFERRED: 23 (23%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*