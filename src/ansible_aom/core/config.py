"""Configuration management for AOM.

This module defines Pydantic models for configuration.
See SPECIFICATION.md Section 8 for configuration schema.

TDD: This file contains STUB implementations only. Tests come first.
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
    """Load configuration from file or use defaults."""
    raise NotImplementedError("load_config - tests first")
