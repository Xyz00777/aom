"""Tests for inventory auto-detection.

When the user doesn't pass `-i` / `--inventory`, AOM should look in the
current working directory for a conventional inventory file and silently
add `-i <path>` to ansible_args. This makes the common case ("playbook
and inventory side-by-side") just work without ceremony.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ansible_aom.cli import detect_default_inventory, ensure_inventory_arg


class TestDetectDefaultInventory:
    def test_finds_inventory_ini_in_cwd(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        inv = tmp_path / "inventory.ini"
        inv.write_text("[web]\nlocalhost\n")
        monkeypatch.chdir(tmp_path)

        assert detect_default_inventory() == "inventory.ini"

    def test_returns_none_when_no_known_file_present(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.chdir(tmp_path)
        assert detect_default_inventory() is None

    def test_prefers_inventory_ini_over_hosts(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        (tmp_path / "inventory.ini").write_text("")
        (tmp_path / "hosts").write_text("")
        monkeypatch.chdir(tmp_path)

        assert detect_default_inventory() == "inventory.ini"

    def test_finds_yaml_inventory_when_only_one_present(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        (tmp_path / "inventory.yml").write_text("all:\n  hosts:\n    localhost: {}\n")
        monkeypatch.chdir(tmp_path)

        assert detect_default_inventory() == "inventory.yml"


class TestEnsureInventoryArg:
    def test_prepends_default_inventory_when_none_given(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        (tmp_path / "inventory.ini").write_text("")
        monkeypatch.chdir(tmp_path)

        result = ensure_inventory_arg([])
        assert result == ["-i", "inventory.ini"]

    def test_leaves_args_unchanged_when_dash_i_present(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        (tmp_path / "inventory.ini").write_text("")
        monkeypatch.chdir(tmp_path)

        original = ["-i", "custom.ini", "-c", "local"]
        assert ensure_inventory_arg(original) == original

    def test_leaves_args_unchanged_when_long_inventory_flag_present(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        (tmp_path / "inventory.ini").write_text("")
        monkeypatch.chdir(tmp_path)

        original = ["--inventory", "custom.ini"]
        assert ensure_inventory_arg(original) == original

    def test_leaves_args_unchanged_when_no_default_present(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.chdir(tmp_path)
        assert ensure_inventory_arg(["-c", "local"]) == ["-c", "local"]

    def test_handles_inventory_file_long_form(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """ansible-playbook also accepts --inventory-file as a synonym."""
        (tmp_path / "inventory.ini").write_text("")
        monkeypatch.chdir(tmp_path)

        original = ["--inventory-file", "custom"]
        assert ensure_inventory_arg(original) == original
