"""Unit tests for the multi-layer config system (Task 3.1 / 3.2).

Covers the new :mod:`ansible_aom.core.config_layer` module:

- XDG-style path resolution: ``/etc/aom/aom_config.yaml`` →
  ``~/.config/aom/aom_config.yaml`` → ``./.aom_config.yaml`` →
  ``AOM_CONFIG`` env var → ``--config`` CLI flag.
- ``YamlConfigSettingsSource`` with ``deep_merge=True`` so nested
  sub-models are merged across files (not replaced).
- ``SettingsConfigDict(nested_model_default_partial_update=True)``
  so per-section partial overrides do not nuke sibling fields.
- Missing files silently skipped (XDG layering on minimal installs).
- ``AOM_CONFIG`` and ``--config`` env / CLI overrides.
- Legacy migration: old ``~/.config/aom/config.yaml`` is auto-migrated
  to ``aom_config.yaml`` and the original moved to
  ``config.yaml.migrated``.

TDD-first: these tests pre-date the implementation. They must all
pass after the implementation lands.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_yaml(path: Path, data: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    return path


def _read_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text())


# ---------------------------------------------------------------------------
# 1. XDG path resolution
# ---------------------------------------------------------------------------


class TestXdgPathResolution:
    """The standard 4-file layering resolves in the documented order."""

    def test_system_path_is_first_under_home(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Built-in defaults are first, then system, then user, then local."""
        from ansible_aom.core.config_layer import find_config_paths

        fake_home = Path("/tmp/opencode/fake-home")
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))
        monkeypatch.setattr("os.getcwd", lambda: "/tmp/opencode/fake-cwd")

        paths = find_config_paths()
        names = [p.name for p in paths]
        # Built-in is in the wheel — its name is ``default_config.yaml``
        assert names[0] == "default_config.yaml"
        assert Path("/etc/aom/aom_config.yaml") in paths
        assert fake_home / ".config" / "aom" / "aom_config.yaml" in paths
        assert Path("/tmp/opencode/fake-cwd") / ".aom_config.yaml" in paths

    def test_user_config_is_xdg_compliant(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """User config sits under ``$XDG_CONFIG_HOME`` / ``~/.config``."""
        from ansible_aom.core.config_layer import find_config_paths

        fake_home = Path("/home/alice")
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))
        monkeypatch.setattr("os.getcwd", lambda: "/work/proj")
        monkeypatch.delenv("AOM_CONFIG", raising=False)

        user_path = fake_home / ".config" / "aom" / "aom_config.yaml"
        assert user_path in find_config_paths()

    def test_local_config_is_in_cwd(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Repo-local override sits at ``./.aom_config.yaml``."""
        from ansible_aom.core.config_layer import find_config_paths

        monkeypatch.setattr("os.getcwd", lambda: "/work/proj")
        monkeypatch.delenv("AOM_CONFIG", raising=False)

        assert Path("/work/proj/.aom_config.yaml") in find_config_paths()

    def test_built_in_default_is_first(self) -> None:
        """Built-in ``default_config.yaml`` from the wheel is the lowest layer."""
        from ansible_aom.core.config_layer import _BUILTIN_DEFAULT

        assert _BUILTIN_DEFAULT.is_file()
        assert _BUILTIN_DEFAULT.name == "default_config.yaml"


# ---------------------------------------------------------------------------
# 2. Explicit path override (env + CLI)
# ---------------------------------------------------------------------------


class TestExplicitPathOverride:
    """``AOM_CONFIG`` env var and ``--config`` CLI flag both override the list."""

    def test_aom_config_env_appends_to_layer_list(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        from ansible_aom.core.config_layer import find_config_paths

        explicit = tmp_path / "explicit.yaml"
        monkeypatch.setenv("AOM_CONFIG", str(explicit))
        monkeypatch.setattr("os.getcwd", lambda: str(tmp_path))

        assert explicit in find_config_paths()

    def test_cli_config_dash_dash_config_is_picked_up(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """``--config /path/to/file.yaml`` on sys.argv overrides too."""
        from ansible_aom.core import config_layer

        explicit = tmp_path / "cli.yaml"
        monkeypatch.setattr("sys.argv", ["aom", "site.yml", "--config", str(explicit)])
        monkeypatch.setenv("AOM_CONFIG", "")
        monkeypatch.setattr("os.getcwd", lambda: str(tmp_path))

        assert explicit in config_layer.find_config_paths()

    def test_env_var_wins_when_both_set(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """If both ``AOM_CONFIG`` and ``--config`` are set, env wins."""
        from ansible_aom.core import config_layer

        env_path = tmp_path / "env.yaml"
        cli_path = tmp_path / "cli.yaml"
        monkeypatch.setenv("AOM_CONFIG", str(env_path))
        monkeypatch.setattr("sys.argv", ["aom", "site.yml", "--config", str(cli_path)])
        monkeypatch.setattr("os.getcwd", lambda: str(tmp_path))

        # env var wins → only env_path is in the explicit slot
        paths = config_layer.find_config_paths()
        assert env_path in paths
        assert cli_path not in paths


# ---------------------------------------------------------------------------
# 3. Missing files silently skipped
# ---------------------------------------------------------------------------


class TestMissingFilesSkipped:
    """Files that don't exist on disk are silently skipped — not errors."""

    def test_missing_files_loaded_as_empty(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``load_config_with_layers`` returns defaults when no files exist."""
        from ansible_aom.core.config_layer import load_config_with_layers

        # No files at any layer. Override HOME/CWD to empty dirs.
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        monkeypatch.setattr("os.getcwd", lambda: str(tmp_path))
        monkeypatch.delenv("AOM_CONFIG", raising=False)
        monkeypatch.setattr("sys.argv", ["aom"])

        config = load_config_with_layers()
        # Defaults from the built-in file are present
        assert config.capture.verbose is False
        assert config.redaction.enabled is True

    def test_missing_user_file_does_not_raise(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """If only the system file is missing, no error."""
        from ansible_aom.core.config_layer import AomSettings

        # No user file written. Just hit the loader directly.
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path / "nope"))
        monkeypatch.setattr("os.getcwd", lambda: str(tmp_path / "nope"))
        monkeypatch.delenv("AOM_CONFIG", raising=False)
        monkeypatch.setattr("sys.argv", ["aom"])

        # Should not raise
        settings = AomSettings()
        assert settings.capture.verbose is False


# ---------------------------------------------------------------------------
# 4. deep_merge across files
# ---------------------------------------------------------------------------


class TestDeepMerge:
    """Nested sub-models are merged, not replaced, across files."""

    def test_nested_submodel_merges_across_files(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Setting ``capture.verbose`` in user file does not lose system file's
        ``capture.include_setup`` (deep-merge, not replace)."""
        from ansible_aom.core.config_layer import AomSettings

        user_file = tmp_path / "user.yaml"
        _write_yaml(
            user_file,
            {
                "capture": {"verbose": True},
            },
        )

        system_file = tmp_path / "system.yaml"
        _write_yaml(
            system_file,
            {
                "capture": {"verbose": False, "include_setup": True},
            },
        )

        # Override path-resolution: we'll build the loader with our own list.
        monkeypatch.setattr("os.getcwd", lambda: str(tmp_path))
        monkeypatch.setattr("sys.argv", ["aom"])

        settings = AomSettings(_yaml_file=[system_file, user_file])
        # User overrides verbose, but include_setup is preserved.
        assert settings.capture.verbose is True
        assert settings.capture.include_setup is True

    def test_user_field_overrides_system_field(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The later (higher-priority) file wins on key collision."""
        from ansible_aom.core.config_layer import AomSettings

        user = tmp_path / "user.yaml"
        _write_yaml(user, {"capture": {"verbose": True}})

        system = tmp_path / "system.yaml"
        _write_yaml(system, {"capture": {"verbose": False}})

        monkeypatch.setattr("sys.argv", ["aom"])
        settings = AomSettings(_yaml_file=[system, user])
        assert settings.capture.verbose is True

    def test_partial_submodel_update_preserves_siblings(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``nested_model_default_partial_update=True`` keeps siblings.

        Without the flag, user only setting ``live.show_warnings`` would
        wipe ``live.show_deprecations`` and ``live.show_failed_hint``.
        """
        from ansible_aom.core.config_layer import AomSettings

        user = tmp_path / "user.yaml"
        _write_yaml(user, {"live": {"show_warnings": False}})

        monkeypatch.setattr("sys.argv", ["aom"])
        settings = AomSettings(_yaml_file=[user])

        # User's intent applied
        assert settings.live.show_warnings is False
        # Siblings preserved
        assert settings.live.show_deprecations is True
        assert settings.live.show_failed_hint is True


# ---------------------------------------------------------------------------
# 5. Env var overrides (AOM_*)
# ---------------------------------------------------------------------------


class TestEnvVarOverrides:
    """``AOM_*`` env vars override YAML values (per pydantic-settings)."""

    def test_aom_capture_verbose_env_overrides_yaml(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from ansible_aom.core.config_layer import AomSettings

        user = tmp_path / "user.yaml"
        _write_yaml(user, {"capture": {"verbose": False}})

        monkeypatch.setenv("AOM_CAPTURE__VERBOSE", "true")
        monkeypatch.setattr("sys.argv", ["aom"])

        settings = AomSettings(_yaml_file=[user])
        assert settings.capture.verbose is True

    def test_aom_config_env_changes_path_layer(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``AOM_CONFIG`` env var causes its file to be added to the layer list."""
        from ansible_aom.core.config_layer import AomSettings

        explicit = tmp_path / "override.yaml"
        _write_yaml(explicit, {"capture": {"verbose": True}})

        monkeypatch.setenv("AOM_CONFIG", str(explicit))
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path / "nope"))
        monkeypatch.setattr("os.getcwd", lambda: str(tmp_path / "nope"))
        monkeypatch.setattr("sys.argv", ["aom"])

        settings = AomSettings()
        assert settings.capture.verbose is True


# ---------------------------------------------------------------------------
# 6. Legacy migration
# ---------------------------------------------------------------------------


class TestLegacyMigration:
    """Old ``config.yaml`` is auto-migrated to ``aom_config.yaml`` on first run."""

    def test_old_config_yaml_is_migrated(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Old ``config.yaml`` → ``aom_config.yaml``; original moved to
        ``config.yaml.migrated``."""
        from ansible_aom.core.config_layer import migrate_legacy_config

        fake_config_dir = tmp_path / ".config" / "aom"
        fake_config_dir.mkdir(parents=True)
        old = fake_config_dir / "config.yaml"
        old.write_text("redaction:\n  whitelist: [foo]\n")

        # Make Path.home() point to tmp_path so ~/.config/aom/ resolves to it.
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))

        result = migrate_legacy_config()

        assert result is True
        new = fake_config_dir / "aom_config.yaml"
        moved = fake_config_dir / "config.yaml.migrated"
        assert new.exists()
        assert moved.exists()
        assert not old.exists()
        # Content preserved in both new file and moved file
        data = _read_yaml(new)
        assert data["redaction"]["whitelist"] == ["foo"]
        # The moved file has the same content as the old one had
        assert _read_yaml(moved)["redaction"]["whitelist"] == ["foo"]

    def test_no_old_config_means_no_migration(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """``migrate_legacy_config`` returns False when there's nothing to migrate."""
        from ansible_aom.core.config_layer import migrate_legacy_config

        # Empty fake ~/.config/aom/ — no old file
        fake = tmp_path / ".config" / "aom"
        fake.mkdir(parents=True)
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))

        result = migrate_legacy_config()
        assert result is False
        assert not (fake / "aom_config.yaml").exists()
        assert not (fake / "config.yaml.migrated").exists()

    def test_new_file_already_exists_skips_migration(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """If both old and new exist, we don't clobber the new one."""
        from ansible_aom.core.config_layer import migrate_legacy_config

        d = tmp_path / ".config" / "aom"
        d.mkdir(parents=True)
        (d / "config.yaml").write_text("capture:\n  verbose: false\n")
        (d / "aom_config.yaml").write_text("capture:\n  verbose: true\n")

        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))

        result = migrate_legacy_config()
        # Returns False because nothing was done
        assert result is False
        # aom_config.yaml untouched
        assert _read_yaml(d / "aom_config.yaml")["capture"]["verbose"] is True
        # Old file is NOT moved (we leave it for the user to clean up)
        assert (d / "config.yaml").exists()

    def test_migration_does_not_run_twice(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Second call after a successful migration is a no-op."""
        from ansible_aom.core.config_layer import migrate_legacy_config

        d = tmp_path / ".config" / "aom"
        d.mkdir(parents=True)
        (d / "config.yaml").write_text("redaction:\n  whitelist: [foo]\n")

        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))

        assert migrate_legacy_config() is True
        # Second call: old file is gone, so nothing to do
        assert migrate_legacy_config() is False


# ---------------------------------------------------------------------------
# 7. CLI flag overrides
# ---------------------------------------------------------------------------


class TestCliOverrides:
    """``AomSettings(**kwargs)`` from the CLI wins over every layer."""

    def test_init_kwargs_beat_yaml(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Passing ``capture=CaptureConfig(verbose=True)`` wins over YAML."""
        from ansible_aom.core.config_layer import AomSettings, CaptureConfig

        user = tmp_path / "user.yaml"
        _write_yaml(user, {"capture": {"verbose": False}})

        monkeypatch.setattr("sys.argv", ["aom"])
        settings = AomSettings(
            _yaml_file=[user],
            capture=CaptureConfig(verbose=True),
        )
        assert settings.capture.verbose is True
