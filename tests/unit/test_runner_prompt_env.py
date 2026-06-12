"""The runner provisions a prompt control dir and exports it + the collection."""

from __future__ import annotations

from pathlib import Path

from ansible_aom.ansible import runner
from ansible_aom.core.prompt_channel import ENV_VAR


def test_prompt_control_env_sets_dir_and_collection_path(tmp_path):
    env: dict[str, str] = {}
    ctrl_dir = runner._provision_prompt_channel_env(env, base_dir=tmp_path)

    assert env[ENV_VAR] == str(ctrl_dir)
    assert ctrl_dir.is_dir()
    # The bundled collection root is appended to ANSIBLE_COLLECTIONS_PATH.
    assert "ANSIBLE_COLLECTIONS_PATH" in env
    assert runner._bundled_collections_dir() is not None
    assert str(runner._bundled_collections_dir()) in env["ANSIBLE_COLLECTIONS_PATH"]


def test_bundled_collections_dir_contains_confirm_plugin():
    root = runner._bundled_collections_dir()
    assert root is not None
    action = (
        root
        / "ansible_collections"
        / "aom"
        / "interactive"
        / "plugins"
        / "action"
        / "confirm.py"
    )
    assert action.is_file()
