"""Multi-layer configuration loader for AOM (Task 3.1 / 3.2).

Layered YAML + env + CLI precedence, built on ``pydantic-settings`` v2:

* ``/etc/aom/aom_config.yaml`` (system, read-only)
* ``~/.config/aom/aom_config.yaml`` (user)
* ``./.aom_config.yaml`` (repo-local)
* ``$AOM_CONFIG`` env var → appended to the file list (path override)
* ``--config`` CLI flag → appended (path override, env wins if both set)
* ``AOM_*`` env vars → nested-dict deep-merge on top of YAML
* ``AomSettings(**kwargs)`` → from the CLI, highest priority

The hard rename ``config.yaml`` → ``aom_config.yaml`` is handled by
:meth:`migrate_legacy_config`, which runs once on first call. The old
file is moved to ``config.yaml.migrated`` (preserved, not deleted).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)
from pydantic_settings.sources import YamlConfigSettingsSource

# Built-in default YAML shipped inside the wheel (lowest-priority layer).
# Resolved at module load — the wheel file is constant — but the XDG
# and cwd paths are recomputed on every call to ``find_config_paths``
# so tests can monkeypatch ``Path.home`` / ``os.getcwd`` freely.
_BUILTIN_DEFAULT = Path(__file__).parent / "default_config.yaml"
_SYSTEM_PATH = Path("/etc/aom/aom_config.yaml")


# --- schema ---------------------------------------------------------------


class CaptureConfig(BaseModel):
    verbose: bool = False
    include_setup: bool = False
    exclude_modules: list[str] = Field(default_factory=list)


class RedactionConfig(BaseModel):
    enabled: bool = True
    whitelist: list[str] = Field(default_factory=list)
    custom_fields: list[str] = Field(default_factory=list)
    custom_key_patterns: list[str] = Field(default_factory=list)
    custom_patterns: list[dict[str, str]] = Field(default_factory=list)


class LiveConfig(BaseModel):
    show_failed_hint: bool = True
    show_warnings: bool = True
    show_deprecations: bool = True


class InspectConfig(BaseModel):
    default_tab: str = "summary"


class TuiConfig(BaseModel):
    theme: str = "default"


class LogConfig(BaseModel):
    max_lines: int = Field(default=50000, ge=1000, le=100000)


class SessionConfig(BaseModel):
    keep_sessions: int = Field(default=100, ge=1)
    keep_days: int = Field(default=30, ge=1)


class AomSettings(BaseSettings):
    """Application settings — see :data:`_BUILTIN_DEFAULT` for the schema."""

    model_config = SettingsConfigDict(
        env_prefix="AOM_",
        env_nested_delimiter="__",
        nested_model_default_partial_update=True,
        extra="ignore",
    )

    capture: CaptureConfig = Field(default_factory=CaptureConfig)
    redaction: RedactionConfig = Field(default_factory=RedactionConfig)
    live: LiveConfig = Field(default_factory=LiveConfig)
    inspect: InspectConfig = Field(default_factory=InspectConfig)
    tui: TuiConfig = Field(default_factory=TuiConfig)
    log: LogConfig = Field(default_factory=LogConfig)
    session: SessionConfig = Field(default_factory=SessionConfig)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # ``_yaml_file`` may be passed to ``AomSettings(..., _yaml_file=[...])``
        # by tests / CLI plumbing to pin the file list. Falls back to the
        # full XDG layering.
        override = getattr(init_settings, "init_kwargs", {}).get("_yaml_file")
        yaml_files = list(override) if override is not None else find_config_paths()
        return (
            init_settings,
            env_settings,
            YamlConfigSettingsSource(
                settings_cls,
                yaml_file=yaml_files,
                deep_merge=True,
            ),
            dotenv_settings,
            file_secret_settings,
        )


# --- resolution + migration ----------------------------------------------


def find_config_paths() -> list[Path]:
    """Return the YAML file list in lowest → highest priority order."""
    user_path = Path.home() / ".config" / "aom" / "aom_config.yaml"
    local_path = Path.cwd() / ".aom_config.yaml"
    files: list[Path] = [_BUILTIN_DEFAULT, _SYSTEM_PATH, user_path, local_path]
    explicit = os.environ.get("AOM_CONFIG") or _cli_config_path()
    if explicit:
        files.append(Path(explicit).expanduser())
    return files


def _cli_config_path() -> str | None:
    """Pull ``--config <path>`` out of ``sys.argv`` without importing CLI."""
    argv = sys.argv[1:]
    if "--config" in argv:
        i = argv.index("--config")
        if i + 1 < len(argv):
            return argv[i + 1]
    return None


def load_config_with_layers() -> AomSettings:
    """Build the layered :class:`AomSettings` and run legacy migration first."""
    migrate_legacy_config()
    return AomSettings()


def migrate_legacy_config() -> bool:
    """One-shot ``config.yaml`` → ``aom_config.yaml`` migration.

    Returns True if a migration happened. No-op if either the new file
    already exists or there's no old file to migrate.
    """
    user_dir = Path.home() / ".config" / "aom"
    old = user_dir / "config.yaml"
    new = user_dir / "aom_config.yaml"
    moved = user_dir / "config.yaml.migrated"
    if not old.exists() or new.exists():
        return False
    new.parent.mkdir(parents=True, exist_ok=True)
    old.replace(moved)
    # v1 schema is a subset of the old config; verbatim copy is the
    # correct translation (no field renames, no key moves).
    new.write_text(moved.read_text())
    return True
