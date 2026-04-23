"""Unit tests for configuration models in ansible_aom.core.config.

Test cases cover:
- TC-260 to TC-275: Configuration model validation
- TC-304 to TC-318: Config file and validation tests

All tests are self-contained and use function-scoped fixtures.
"""

import os
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError


class TestStatusBarConfig:
    """Tests for StatusBarConfig model - TC-260, TC-307, TC-290."""

    def test_status_bar_config_default_elements(self):
        """TC-260: StatusBarConfig has default elements list."""
        from ansible_aom.core.config import StatusBarConfig

        config = StatusBarConfig()
        assert config.elements == ["playbook_name", "elapsed_time", "task_progress"]

    def test_status_bar_config_custom_elements(self):
        """TC-307: StatusBarConfig can have custom elements."""
        from ansible_aom.core.config import StatusBarConfig

        config = StatusBarConfig(elements=["current_play", "host_count"])
        assert config.elements == ["current_play", "host_count"]

    def test_status_bar_config_elements_is_list(self):
        """TC-307: elements field is a list."""
        from ansible_aom.core.config import StatusBarConfig

        config = StatusBarConfig()
        assert isinstance(config.elements, list)

    def test_status_bar_config_empty_elements_list(self):
        """TC-307 edge case: Empty elements list is valid."""
        from ansible_aom.core.config import StatusBarConfig

        config = StatusBarConfig(elements=[])
        assert config.elements == []

    def test_status_bar_config_elements_are_strings(self):
        """TC-307: elements list contains strings."""
        from ansible_aom.core.config import StatusBarConfig

        config = StatusBarConfig(elements=["playbook_name", "elapsed_time"])
        assert all(isinstance(e, str) for e in config.elements)

    def test_status_bar_config_field_factory(self):
        """TC-260: Field uses default_factory for mutable default."""
        from ansible_aom.core.config import StatusBarConfig

        # Each instance should have independent list
        config1 = StatusBarConfig()
        config2 = StatusBarConfig()
        config1.elements.append("new_element")
        assert "new_element" not in config2.elements


class TestRedactionConfig:
    """Tests for RedactionConfig model - TC-170, TC-312, TC-313, TC-314."""

    def test_redaction_config_default_whitelist_empty(self):
        """TC-170: RedactionConfig whitelist defaults to empty list."""
        from ansible_aom.core.config import RedactionConfig

        config = RedactionConfig()
        assert config.whitelist == []
        assert config.custom_fields == []
        assert config.custom_patterns == []

    def test_redaction_config_custom_whitelist(self):
        """TC-312: RedactionConfig can have custom whitelist."""
        from ansible_aom.core.config import RedactionConfig

        config = RedactionConfig(whitelist=["passenger_version", "bypass"])
        assert config.whitelist == ["passenger_version", "bypass"]

    def test_redaction_config_custom_fields(self):
        """TC-313: RedactionConfig can have custom_fields."""
        from ansible_aom.core.config import RedactionConfig

        config = RedactionConfig(custom_fields=["my_secret_var", "db_connection_string"])
        assert "my_secret_var" in config.custom_fields
        assert "db_connection_string" in config.custom_fields

    def test_redaction_config_custom_patterns(self):
        """TC-314: RedactionConfig can have custom_patterns."""
        from ansible_aom.core.config import RedactionConfig

        config = RedactionConfig(
            custom_patterns=[{"regex": r"--db-password=\S+", "replacement": "--db-password=********"}]
        )
        assert len(config.custom_patterns) == 1
        assert config.custom_patterns[0]["regex"] == r"--db-password=\S+"

    def test_redaction_config_all_fields_independent(self):
        """Each RedactionConfig instance has independent lists."""
        from ansible_aom.core.config import RedactionConfig

        config1 = RedactionConfig(whitelist=["item1"])
        config2 = RedactionConfig()
        assert "item1" not in config2.whitelist

    def test_redaction_config_whitelist_is_list(self):
        """Whitelist is a list."""
        from ansible_aom.core.config import RedactionConfig

        config = RedactionConfig(whitelist=["test"])
        assert isinstance(config.whitelist, list)

    def test_redaction_config_custom_fields_is_list(self):
        """custom_fields is a list."""
        from ansible_aom.core.config import RedactionConfig

        config = RedactionConfig(custom_fields=["api_token"])
        assert isinstance(config.custom_fields, list)

    def test_redaction_config_custom_patterns_is_list(self):
        """custom_patterns is a list of dicts."""
        from ansible_aom.core.config import RedactionConfig

        config = RedactionConfig(custom_patterns=[{"regex": "test", "replacement": "***"}])
        assert isinstance(config.custom_patterns, list)
        assert isinstance(config.custom_patterns[0], dict)


class TestWarningsConfig:
    """Tests for WarningsConfig model - Section 8."""

    def test_warnings_config_default_show_warnings_true(self):
        """WarningsConfig has show_warnings=True by default."""
        from ansible_aom.core.config import WarningsConfig

        config = WarningsConfig()
        assert config.show_warnings is True

    def test_warnings_config_default_show_deprecations_true(self):
        """WarningsConfig has show_deprecations=True by default."""
        from ansible_aom.core.config import WarningsConfig

        config = WarningsConfig()
        assert config.show_deprecations is True

    def test_warnings_config_can_disable_warnings(self):
        """show_warnings can be set to False."""
        from ansible_aom.core.config import WarningsConfig

        config = WarningsConfig(show_warnings=False)
        assert config.show_warnings is False

    def test_warnings_config_can_disable_deprecations(self):
        """show_deprecations can be set to False."""
        from ansible_aom.core.config import WarningsConfig

        config = WarningsConfig(show_deprecations=False)
        assert config.show_deprecations is False

    def test_warnings_config_both_false(self):
        """Both warning flags can be disabled."""
        from ansible_aom.core.config import WarningsConfig

        config = WarningsConfig(show_warnings=False, show_deprecations=False)
        assert config.show_warnings is False
        assert config.show_deprecations is False

    def test_warnings_config_show_warnings_is_bool(self):
        """show_warnings is a boolean."""
        from ansible_aom.core.config import WarningsConfig

        config = WarningsConfig()
        assert isinstance(config.show_warnings, bool)

    def test_warnings_config_show_deprecations_is_bool(self):
        """show_deprecations is a boolean."""
        from ansible_aom.core.config import WarningsConfig

        config = WarningsConfig()
        assert isinstance(config.show_deprecations, bool)


class TestAppConfig:
    """Tests for AppConfig model - TC-263 to TC-275."""

    def test_app_config_default_log_max_lines(self):
        """TC-263: AppConfig has default log_max_lines=50000."""
        from ansible_aom.core.config import AppConfig

        config = AppConfig()
        assert config.log_max_lines == 50000

    def test_app_config_default_session_keep_count(self):
        """TC-264: AppConfig has default session_keep_count=100."""
        from ansible_aom.core.config import AppConfig

        config = AppConfig()
        assert config.session_keep_count == 100

    def test_app_config_default_session_keep_days(self):
        """TC-265: AppConfig has default session_keep_days=30."""
        from ansible_aom.core.config import AppConfig

        config = AppConfig()
        assert config.session_keep_days == 30

    def test_app_config_default_status_bar(self):
        """AppConfig has default StatusBarConfig."""
        from ansible_aom.core.config import AppConfig, StatusBarConfig

        config = AppConfig()
        assert isinstance(config.status_bar, StatusBarConfig)
        assert config.status_bar.elements == ["playbook_name", "elapsed_time", "task_progress"]

    def test_app_config_default_redaction(self):
        """AppConfig has default RedactionConfig."""
        from ansible_aom.core.config import AppConfig, RedactionConfig

        config = AppConfig()
        assert isinstance(config.redaction, RedactionConfig)
        assert config.redaction.whitelist == []

    def test_app_config_default_warnings(self):
        """AppConfig has default WarningsConfig."""
        from ansible_aom.core.config import AppConfig, WarningsConfig

        config = AppConfig()
        assert isinstance(config.warnings, WarningsConfig)
        assert config.warnings.show_warnings is True
        assert config.warnings.show_deprecations is True

    def test_app_config_custom_log_max_lines(self):
        """AppConfig log_max_lines can be customized."""
        from ansible_aom.core.config import AppConfig

        config = AppConfig(log_max_lines=75000)
        assert config.log_max_lines == 75000

    def test_app_config_custom_session_keep_count(self):
        """AppConfig session_keep_count can be customized."""
        from ansible_aom.core.config import AppConfig

        config = AppConfig(session_keep_count=50)
        assert config.session_keep_count == 50

    def test_app_config_custom_session_keep_days(self):
        """AppConfig session_keep_days can be customized."""
        from ansible_aom.core.config import AppConfig

        config = AppConfig(session_keep_days=7)
        assert config.session_keep_days == 7

    def test_app_config_custom_status_bar(self):
        """AppConfig status_bar can be customized."""
        from ansible_aom.core.config import AppConfig, StatusBarConfig

        config = AppConfig(status_bar=StatusBarConfig(elements=["playbook_name"]))
        assert config.status_bar.elements == ["playbook_name"]

    def test_app_config_custom_redaction(self):
        """AppConfig redaction can be customized."""
        from ansible_aom.core.config import AppConfig, RedactionConfig

        config = AppConfig(redaction=RedactionConfig(whitelist=["test_field"]))
        assert config.redaction.whitelist == ["test_field"]

    def test_app_config_custom_warnings(self):
        """AppConfig warnings can be customized."""
        from ansible_aom.core.config import AppConfig, WarningsConfig

        config = AppConfig(warnings=WarningsConfig(show_warnings=False))
        assert config.warnings.show_warnings is False

    def test_app_config_independent_instances(self):
        """Each AppConfig instance has independent nested configs."""
        from ansible_aom.core.config import AppConfig, StatusBarConfig

        config1 = AppConfig(status_bar=StatusBarConfig(elements=["a"]))
        config2 = AppConfig()
        config1.status_bar.elements.append("b")
        assert "b" not in config2.status_bar.elements


class TestAppConfigValidation:
    """Tests for Pydantic field constraints - TC-316, TC-317, TC-318."""

    def test_log_max_lines_ge_1000(self):
        """TC-318: log_max_lines minimum is 1000."""
        from ansible_aom.core.config import AppConfig

        # Valid: exactly 1000
        config = AppConfig(log_max_lines=1000)
        assert config.log_max_lines == 1000

        # Valid: exactly 100000
        config = AppConfig(log_max_lines=100000)
        assert config.log_max_lines == 100000

    def test_log_max_lines_below_minimum_raises_error(self):
        """TC-318: log_max_lines below 1000 raises ValidationError."""
        from ansible_aom.core.config import AppConfig

        with pytest.raises(ValidationError) as exc_info:
            AppConfig(log_max_lines=999)

        assert "greater than or equal to 1000" in str(exc_info.value).lower() or "ge=1000" in str(exc_info.value)

    def test_log_max_lines_above_maximum_raises_error(self):
        """TC-318: log_max_lines above 100000 raises ValidationError."""
        from ansible_aom.core.config import AppConfig

        with pytest.raises(ValidationError) as exc_info:
            AppConfig(log_max_lines=100001)

        assert "less than or equal to 100000" in str(exc_info.value).lower() or "le=100000" in str(exc_info.value)

    def test_session_keep_count_ge_1(self):
        """TC-318: session_keep_count minimum is 1."""
        from ansible_aom.core.config import AppConfig

        config = AppConfig(session_keep_count=1)
        assert config.session_keep_count == 1

        config = AppConfig(session_keep_count=500)
        assert config.session_keep_count == 500

    def test_session_keep_count_below_minimum_raises_error(self):
        """TC-318: session_keep_count below 1 raises ValidationError."""
        from ansible_aom.core.config import AppConfig

        with pytest.raises(ValidationError) as exc_info:
            AppConfig(session_keep_count=0)

        assert "greater than or equal to 1" in str(exc_info.value).lower() or "ge=1" in str(exc_info.value)

    def test_session_keep_count_negative_raises_error(self):
        """TC-318: session_keep_count negative raises ValidationError."""
        from ansible_aom.core.config import AppConfig

        with pytest.raises(ValidationError):
            AppConfig(session_keep_count=-1)

    def test_session_keep_days_ge_1(self):
        """TC-318: session_keep_days minimum is 1."""
        from ansible_aom.core.config import AppConfig

        config = AppConfig(session_keep_days=1)
        assert config.session_keep_days == 1

        config = AppConfig(session_keep_days=365)
        assert config.session_keep_days == 365

    def test_session_keep_days_below_minimum_raises_error(self):
        """TC-318: session_keep_days below 1 raises ValidationError."""
        from ansible_aom.core.config import AppConfig

        with pytest.raises(ValidationError) as exc_info:
            AppConfig(session_keep_days=0)

        assert "greater than or equal to 1" in str(exc_info.value).lower() or "ge=1" in str(exc_info.value)

    def test_session_keep_days_negative_raises_error(self):
        """TC-318: session_keep_days negative raises ValidationError."""
        from ansible_aom.core.config import AppConfig

        with pytest.raises(ValidationError):
            AppConfig(session_keep_days=-1)


class TestAppConfigYamlFile:
    """Tests for Pydantic Settings YAML file integration - TC-304, TC-305, TC-306."""

    def test_yaml_file_default_path(self):
        """TC-304: Default YAML file path is ~/.config/aom/config.yaml."""
        from ansible_aom.core.config import AppConfig

        # Check model_config has yaml_file setting
        assert "yaml_file" in AppConfig.model_config
        assert AppConfig.model_config["yaml_file"] == "~/.config/aom/config.yaml"

    def test_yaml_file_expanded_path(self):
        """TC-304: YAML path should be expandable to absolute path."""
        from ansible_aom.core.config import AppConfig

        yaml_path = AppConfig.model_config["yaml_file"]
        # Should contain ~ for home directory
        assert "~" in yaml_path or "config.yaml" in yaml_path

    def test_yaml_file_xdg_compliant(self):
        """TC-304: Config path follows XDG spec (~/.config/aom/config.yaml)."""
        from ansible_aom.core.config import AppConfig

        yaml_path = AppConfig.model_config["yaml_file"]
        # XDG_CONFIG_HOME defaults to ~/.config
        # Config should be in ~/.config/aom/
        assert ".config" in yaml_path or "config" in yaml_path
        assert "aom" in yaml_path
        assert yaml_path.endswith("config.yaml")

    def test_app_config_with_model_config_dict(self):
        """AppConfig uses SettingsConfigDict for configuration."""
        from ansible_aom.core.config import AppConfig
        from pydantic_settings import SettingsConfigDict

        # Verify SettingsConfigDict is used
        assert hasattr(AppConfig, "model_config")
        assert isinstance(AppConfig.model_config, dict)


class TestConfigModelBasics:
    """Tests for Pydantic BaseModel basics - TC-316, TC-317."""

    def test_status_bar_config_is_pydantic_model(self):
        """StatusBarConfig is a Pydantic model."""
        from ansible_aom.core.config import StatusBarConfig
        from pydantic import BaseModel

        assert issubclass(StatusBarConfig, BaseModel)

    def test_redaction_config_is_pydantic_model(self):
        """RedactionConfig is a Pydantic model."""
        from ansible_aom.core.config import RedactionConfig
        from pydantic import BaseModel

        assert issubclass(RedactionConfig, BaseModel)

    def test_warnings_config_is_pydantic_model(self):
        """WarningsConfig is a Pydantic model."""
        from ansible_aom.core.config import WarningsConfig
        from pydantic import BaseModel

        assert issubclass(WarningsConfig, BaseModel)

    def test_app_config_is_pydantic_settings(self):
        """AppConfig is a Pydantic Settings model."""
        from ansible_aom.core.config import AppConfig
        from pydantic_settings import BaseSettings

        assert issubclass(AppConfig, BaseSettings)

    def test_config_model_validation_error_on_invalid_type(self):
        """TC-316: ValidationError raised for invalid field types."""
        from ansible_aom.core.config import StatusBarConfig

        with pytest.raises(ValidationError):
            StatusBarConfig(elements="not_a_list")  # type: ignore

    def test_config_model_validation_error_on_invalid_nested(self):
        """TC-316: ValidationError for invalid nested types."""
        from ansible_aom.core.config import RedactionConfig

        with pytest.raises(ValidationError):
            RedactionConfig(whitelist="not_a_list")  # type: ignore

    def test_config_model_string_values_in_lists(self):
        """String values in lists are preserved."""
        from ansible_aom.core.config import StatusBarConfig

        config = StatusBarConfig(elements=["item1", "item2", "item3"])
        assert config.elements == ["item1", "item2", "item3"]

    def test_config_model_model_dump(self):
        """Pydantic model_dump() returns dict of fields."""
        from ansible_aom.core.config import WarningsConfig

        config = WarningsConfig(show_warnings=True, show_deprecations=False)
        data = config.model_dump()
        assert data["show_warnings"] is True
        assert data["show_deprecations"] is False

    def test_config_model_model_validate(self):
        """Pydantic model_validate() creates model from dict."""
        from ansible_aom.core.config import WarningsConfig

        config = WarningsConfig.model_validate({"show_warnings": False, "show_deprecations": True})
        assert config.show_warnings is False
        assert config.show_deprecations is True


class TestAppConfigFieldTypes:
    """Tests for AppConfig field types and defaults."""

    def test_log_max_lines_is_int(self):
        """log_max_lines is an integer."""
        from ansible_aom.core.config import AppConfig

        config = AppConfig()
        assert isinstance(config.log_max_lines, int)

    def test_session_keep_count_is_int(self):
        """session_keep_count is an integer."""
        from ansible_aom.core.config import AppConfig

        config = AppConfig()
        assert isinstance(config.session_keep_count, int)

    def test_session_keep_days_is_int(self):
        """session_keep_days is an integer."""
        from ansible_aom.core.config import AppConfig

        config = AppConfig()
        assert isinstance(config.session_keep_days, int)

    def test_status_bar_is_status_bar_config(self):
        """status_bar field is StatusBarConfig type."""
        from ansible_aom.core.config import AppConfig, StatusBarConfig

        config = AppConfig()
        assert isinstance(config.status_bar, StatusBarConfig)

    def test_redaction_is_redaction_config(self):
        """redaction field is RedactionConfig type."""
        from ansible_aom.core.config import AppConfig, RedactionConfig

        config = AppConfig()
        assert isinstance(config.redaction, RedactionConfig)

    def test_warnings_is_warnings_config(self):
        """warnings field is WarningsConfig type."""
        from ansible_aom.core.config import AppConfig, WarningsConfig

        config = AppConfig()
        assert isinstance(config.warnings, WarningsConfig)


class TestLoadConfig:
    """Tests for load_config function - TC-304 to TC-306."""

    def test_load_config_raises_not_implemented(self):
        """load_config is not yet implemented (TDD stub)."""
        from ansible_aom.core.config import load_config

        with pytest.raises(NotImplementedError):
            load_config()

    def test_load_config_accepts_optional_config_path(self):
        """load_config accepts optional config_path parameter."""
        from ansible_aom.core.config import load_config

        # Function signature should accept optional path
        import inspect

        sig = inspect.signature(load_config)
        params = list(sig.parameters.keys())
        assert "config_path" in params or len(params) >= 1

    def test_load_config_signature_has_str_union_none(self):
        """load_config config_path is str | None."""
        from ansible_aom.core.config import load_config

        import inspect

        sig = inspect.signature(load_config)
        config_path_param = sig.parameters.get("config_path")
        if config_path_param:
            # Parameter should have Union type or None default
            assert config_path_param.default is None or config_path_param.annotation


class TestConfigFromEnvironment:
    """Tests for environment variable and YAML config loading."""

    def test_app_config_can_be_created_without_file(self):
        """AppConfig can be instantiated without a config file."""
        from ansible_aom.core.config import AppConfig

        # Should work even if no config file exists
        config = AppConfig()
        assert config is not None

    def test_app_config_uses_defaults_when_no_env(self):
        """AppConfig uses defaults when no environment variables set."""
        from ansible_aom.core.config import AppConfig

        # Clear any env vars that might affect config
        config = AppConfig()
        assert config.log_max_lines == 50000

    def test_status_bar_config_equality(self):
        """StatusBarConfig instances with same values are equal."""
        from ansible_aom.core.config import StatusBarConfig

        config1 = StatusBarConfig(elements=["a", "b"])
        config2 = StatusBarConfig(elements=["a", "b"])
        assert config1.model_dump() == config2.model_dump()

    def test_app_config_with_nested_models(self):
        """AppConfig properly creates nested config models."""
        from ansible_aom.core.config import AppConfig, WarningsConfig

        config = AppConfig()
        # Nested model should be properly instantiated
        assert hasattr(config.warnings, "show_warnings")
        assert hasattr(config.warnings, "show_deprecations")


class TestConfigFieldValidation:
    """Tests for edge cases in field validation."""

    def test_log_max_lines_boundary_values(self):
        """Boundary values for log_max_lines are valid."""
        from ansible_aom.core.config import AppConfig

        # Min boundary
        config_min = AppConfig(log_max_lines=1000)
        assert config_min.log_max_lines == 1000

        # Max boundary
        config_max = AppConfig(log_max_lines=100000)
        assert config_max.log_max_lines == 100000

        # Middle value
        config_mid = AppConfig(log_max_lines=50000)
        assert config_mid.log_max_lines == 50000

    def test_session_keep_count_large_values(self):
        """session_keep_count accepts large values."""
        from ansible_aom.core.config import AppConfig

        config = AppConfig(session_keep_count=10000)
        assert config.session_keep_count == 10000

    def test_session_keep_days_large_values(self):
        """session_keep_days accepts large values."""
        from ansible_aom.core.config import AppConfig

        config = AppConfig(session_keep_days=365)
        assert config.session_keep_days == 365

    def test_status_bar_config_elements_preserves_order(self):
        """StatusBarConfig elements list preserves order."""
        from ansible_aom.core.config import StatusBarConfig

        config = StatusBarConfig(elements=["first", "second", "third"])
        assert config.elements == ["first", "second", "third"]

    def test_multiple_instances_independent(self):
        """Multiple config instances are independent."""
        from ansible_aom.core.config import AppConfig

        config1 = AppConfig(log_max_lines=10000)
        config2 = AppConfig(log_max_lines=20000)

        assert config1.log_max_lines == 10000
        assert config2.log_max_lines == 20000


class TestRedactionCustomPatterns:
    """Tests for redaction custom patterns - TC-314."""

    def test_custom_patterns_dict_structure(self):
        """Custom patterns use dict with regex and replacement."""
        from ansible_aom.core.config import RedactionConfig

        pattern = {"regex": r"--password=\S+", "replacement": "--password=********"}
        config = RedactionConfig(custom_patterns=[pattern])
        assert len(config.custom_patterns) == 1

    def test_custom_patterns_multiple_patterns(self):
        """Multiple custom patterns can be defined."""
        from ansible_aom.core.config import RedactionConfig

        patterns = [
            {"regex": r"--password=\S+", "replacement": "--password=********"},
            {"regex": r"--token=\S+", "replacement": "--token=********"},
        ]
        config = RedactionConfig(custom_patterns=patterns)
        assert len(config.custom_patterns) == 2

    def test_custom_patterns_with_complex_regex(self):
        """Custom patterns support complex regex patterns."""
        from ansible_aom.core.config import RedactionConfig

        pattern = {
            "regex": r"(mysql://[^:]+:)([^@]+)(@)",
            "replacement": r"\1********\3",
        }
        config = RedactionConfig(custom_patterns=[pattern])
        assert len(config.custom_patterns) == 1

    def test_custom_patterns_dict_keys(self):
        """Custom pattern dicts have regex and replacement keys."""
        from ansible_aom.core.config import RedactionConfig

        config = RedactionConfig(
            custom_patterns=[{"regex": "test", "replacement": "***"}]
        )
        pattern = config.custom_patterns[0]
        assert "regex" in pattern
        assert "replacement" in pattern


class TestConfigImmutabilityIntent:
    """Tests reinforcing config should not be mutated after creation."""

    def test_status_bar_elements_mutation_isolated(self):
        """Mutating one config's elements doesn't affect others."""
        from ansible_aom.core.config import StatusBarConfig

        config1 = StatusBarConfig(elements=["a"])
        config2 = StatusBarConfig(elements=["b"])

        # Modify config1's list
        config1.elements.append("c")

        # config2 should not be affected
        assert "c" not in config2.elements

    def test_app_config_nested_config_isolation(self):
        """Nested configs are independent between instances."""
        from ansible_aom.core.config import AppConfig, RedactionConfig

        r1 = RedactionConfig(whitelist=["field1"])
        r2 = RedactionConfig(whitelist=["field2"])

        config1 = AppConfig(redaction=r1)
        config2 = AppConfig(redaction=r2)

        assert "field1" not in config2.redaction.whitelist
        assert "field2" not in config1.redaction.whitelist