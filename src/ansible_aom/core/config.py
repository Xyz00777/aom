"""Configuration management for AOM.

This module defines Pydantic models for configuration.
See SPECIFICATION.md Section 8 for configuration schema.
"""

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class StatusBarConfig(BaseModel):
    """Status bar configuration."""

    elements: list[str] = Field(
        default_factory=lambda: ["playbook_name", "elapsed_time", "task_progress"]
    )


class RedactionConfig(BaseModel):
    """Secret redaction configuration."""

    whitelist: list[str] = Field(default_factory=list)
    custom_fields: list[str] = Field(default_factory=list)
    custom_patterns: list[dict[str, str]] = Field(default_factory=list)


class WarningsConfig(BaseModel):
    """Warning display configuration."""

    show_warnings: bool = Field(default=True)
    show_deprecations: bool = Field(default=True)


class AppConfig(BaseSettings):
    """Application configuration loaded from YAML and CLI."""

    model_config = SettingsConfigDict(
        yaml_file="~/.config/aom/config.yaml",
    )

    status_bar: StatusBarConfig = Field(default_factory=StatusBarConfig)
    redaction: RedactionConfig = Field(default_factory=RedactionConfig)
    warnings: WarningsConfig = Field(default_factory=WarningsConfig)
    log_max_lines: int = Field(default=50000, ge=1000, le=100000)
    session_keep_count: int = Field(default=100, ge=1)
    session_keep_days: int = Field(default=30, ge=1)


def load_config(config_path: str | None = None) -> AppConfig:
    """Load configuration from YAML file or use defaults.

    Args:
        config_path: Optional path to config file. Uses default path if None.

    Returns:
        AppConfig with loaded or default values.
    """
    import logging
    import os

    import yaml

    logger = logging.getLogger(__name__)

    if config_path is None:
        config_path = os.path.expanduser("~/.config/aom/config.yaml")
    else:
        config_path = os.path.expanduser(config_path)

    if not os.path.exists(config_path):
        return AppConfig()

    try:
        with open(config_path) as f:
            data = yaml.safe_load(f)
    except (yaml.YAMLError, OSError) as e:
        logger.warning("Failed to load config from %s: %s", config_path, e)
        return AppConfig()

    if data is None:
        return AppConfig()

    try:
        status_bar_data = data.get("status_bar", {})
        status_bar = StatusBarConfig(**status_bar_data) if status_bar_data else StatusBarConfig()

        redaction_data = data.get("redaction", {})
        redaction = RedactionConfig(**redaction_data) if redaction_data else RedactionConfig()

        warnings_data = data.get("warnings", {})
        warnings = WarningsConfig(**warnings_data) if warnings_data else WarningsConfig()

        log_data = data.get("log", {})
        session_data = data.get("session", {})

        return AppConfig(
            status_bar=status_bar,
            redaction=redaction,
            warnings=warnings,
            log_max_lines=log_data.get("max_lines", 50000),
            session_keep_count=session_data.get("keep_sessions", 100),
            session_keep_days=session_data.get("keep_days", 30),
        )
    except Exception as e:
        logger.warning("Failed to parse config from %s: %s", config_path, e)
        return AppConfig()
