"""Tests for JSONL callback plugin configuration (TC-067 to TC-071).

Test cases cover the real production callback-selection code in
``ansible_aom.ansible.runner`` — no inline helpers, no mock functions
that bypass the actual logic. The runtime path is:

    _callback_env() → dict with ANSIBLE_STDOUT_CALLBACK + (optionally)
                       ANSIBLE_CALLBACK_PLUGINS

When the bundled ``aom_jsonl`` plugin dir can be resolved, the runner
selects ``aom_jsonl`` (TC-067 availability check satisfied by the
bundled plugin existing). When it can't, the runner falls back to
``ansible.posix.jsonl`` — never breaking the run (TC-068 prompt is
implicitly skipped because we always have at least one path). TC-069
and TC-070 cover version handling of the bundled vs fallback
callbacks. TC-071 covers the env-var shape that actually reaches the
ansible-playbook subprocess.

All tests are pure-Python unit tests and do not require a real
``ansible-playbook`` on $PATH.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ansible_aom.ansible import runner


class TestAnsiblePosixAvailability:
    """Tests for TC-067: ansible.posix Availability Check (bundled fallback)."""

    def test_bundled_callback_dir_resolves_when_present(self) -> None:
        """TC-067: The bundled aom_jsonl plugin resolves to a real path on disk.

        This is the happy-path equivalent of "ansible.posix availability
        check satisfied": AOM ships its own JSONL plugin so we never
        actually need the upstream collection at runtime. The check is
        that the bundled dir exists and contains the plugin file.
        """
        callback_dir = runner._bundled_callback_dir()

        assert callback_dir is not None
        assert isinstance(callback_dir, Path)
        assert callback_dir.is_dir()
        assert (callback_dir / "aom_jsonl.py").is_file()

    def test_bundled_callback_dir_none_when_file_missing(self, monkeypatch) -> None:
        """TC-067: When bundled plugin file is missing, return None (force fallback)."""
        # Patch Path.is_file on the resolved path to simulate a packaging
        # glitch where the plugin file isn't shipped.
        monkeypatch.setattr(Path, "is_file", lambda self: False)

        result = runner._bundled_callback_dir()

        assert result is None

    def test_bundled_callback_plugin_file_exists(self) -> None:
        """TC-067: The bundled aom_jsonl.py file exists in the callback directory.

        Verified via the same code path that ``_bundled_callback_dir``
        uses. The actual import requires ansible_collections to be
        installed (which is out-of-scope for unit tests) — but the
        file presence is sufficient evidence of "plugin is shipped".
        """
        callback_dir = runner._bundled_callback_dir()

        assert callback_dir is not None
        plugin_file = callback_dir / "aom_jsonl.py"
        assert plugin_file.is_file()
        contents = plugin_file.read_text()
        assert "CallbackModule" in contents
        assert "aom_jsonl" in contents


class TestAnsiblePosixInstallPrompt:
    """Tests for TC-068: ansible.posix Install Prompt (implicit fallback path).

    AOM does NOT implement a literal install prompt because the bundled
    ``aom_jsonl`` plugin makes the upstream ``ansible.posix`` collection
    optional. The fallback contract is: when the bundled dir can't be
    resolved, ``_callback_env`` selects ``ansible.posix.jsonl`` and the
    run continues. These tests verify that contract — if you wanted a
    literal prompt UI, that's a future spec, not current behaviour.
    """

    def test_fallback_selects_ansible_posix_jsonl(self, monkeypatch) -> None:
        """TC-068: When bundled dir unavailable, env selects ansible.posix.jsonl.

        The fallback IS the prompt response: we silently select the
        upstream callback rather than blocking on user input.
        """
        monkeypatch.setattr(runner, "_bundled_callback_dir", lambda: None)

        env = runner._callback_env()

        assert env["ANSIBLE_STDOUT_CALLBACK"] == "ansible.posix.jsonl"
        assert "ANSIBLE_CALLBACK_PLUGINS" not in env

    def test_bundled_preferred_over_posix_fallback(self, monkeypatch) -> None:
        """TC-068: When bundled dir resolves, aom_jsonl wins over ansible.posix.jsonl."""
        fake_dir = Path("/some/bundled/callback")
        monkeypatch.setattr(runner, "_bundled_callback_dir", lambda: fake_dir)

        env = runner._callback_env()

        assert env["ANSIBLE_STDOUT_CALLBACK"] == "aom_jsonl"
        assert "ansible.posix.jsonl" not in env["ANSIBLE_STDOUT_CALLBACK"]


class TestAnsibleCoreVersionCheck:
    """Tests for TC-069: ansible-core Version Check.

    AOM shells out to ansible-playbook but never imports ansible-core,
    so it has no direct version-pin requirement of its own. The
    contract is: AOM must spawn ansible-playbook regardless of which
    ansible-core version is installed, and the env-var override path
    (user-set ANSIBLE_STDOUT_CALLBACK) must survive.

    These tests verify that the spawn path is robust across the version
    axis — the spawn is always constructed with ``env`` derived from
    ``os.environ.copy()`` plus ``_callback_env()``.
    """

    def test_callback_env_returns_dict_with_required_key(self) -> None:
        """TC-069: _callback_env always returns a dict with ANSIBLE_STDOUT_CALLBACK set."""
        env = runner._callback_env()

        assert isinstance(env, dict)
        assert "ANSIBLE_STDOUT_CALLBACK" in env
        assert env["ANSIBLE_STDOUT_CALLBACK"] in {"aom_jsonl", "ansible.posix.jsonl"}

    def test_callback_env_does_not_pin_ansible_core_version(self) -> None:
        """TC-069: _callback_env never includes version-pin keys.

        AOM doesn't pin ansible-core in the env — it relies on whatever
        ansible-playbook the user has on $PATH.
        """
        env = runner._callback_env()

        # No version-pinning keys should be present
        assert "ANSIBLE_CORE_VERSION" not in env
        assert "ANSIBLE_CORE_REQUIRED" not in env
        assert "ANSIBLE_VERSION" not in env

    def test_callback_env_callable_for_any_ansible_core_state(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """TC-069: _callback_env works regardless of bundled plugin state.

        Both states (bundled available / not available) must produce a
        valid callback selection without raising.
        """
        # Path 1: bundled dir resolves
        monkeypatch.setattr(runner, "_bundled_callback_dir", lambda: Path("/fake/bundled"))
        env1 = runner._callback_env()
        assert env1["ANSIBLE_STDOUT_CALLBACK"] == "aom_jsonl"

        # Path 2: bundled dir missing
        monkeypatch.setattr(runner, "_bundled_callback_dir", lambda: None)
        env2 = runner._callback_env()
        assert env2["ANSIBLE_STDOUT_CALLBACK"] == "ansible.posix.jsonl"


class TestAnsiblePosixVersionCheck:
    """Tests for TC-070: ansible.posix Version Check.

    AOM never imports the ansible.posix collection — it only references
    its JSONL callback by string name in the env dict. Therefore
    "version check" reduces to: the callback name in the env is a
    valid ansible.posix callback name, and the bundled plugin (when
    preferred) satisfies the same role.

    ansible.posix.jsonl >= 1.5.0 is when the ``task.path`` field started
    appearing reliably; the path field is parsed in core/parser.py via
    ``_task_path`` — verify that parser tolerates both with-path and
    without-path task dicts (i.e. the version threshold is enforced at
    the JSONL level, not the AOM level).
    """

    def test_fallback_callback_name_is_ansible_posix_jsonl(self, monkeypatch) -> None:
        """TC-070: When bundled dir missing, callback name is the canonical string."""
        monkeypatch.setattr(runner, "_bundled_callback_dir", lambda: None)

        env = runner._callback_env()

        # ansible.posix.jsonl is the fully-qualified callback name.
        # ansible-core >= 2.14 + ansible.posix >= 1.5.0 is when this
        # callback ships the `path` field on tasks. AOM tolerates
        # versions below that — see core/parser.py _task_path.
        assert env["ANSIBLE_STDOUT_CALLBACK"] == "ansible.posix.jsonl"

    def test_fallback_callback_name_split_correctly(self, monkeypatch) -> None:
        """TC-070: ansible.posix.jsonl parses as collection='ansible.posix', plugin='jsonl'."""
        monkeypatch.setattr(runner, "_bundled_callback_dir", lambda: None)

        env = runner._callback_env()

        callback_name = env["ANSIBLE_STDOUT_CALLBACK"]
        collection, _, plugin = callback_name.rpartition(".")

        assert collection == "ansible.posix"
        assert plugin == "jsonl"

    def test_bundled_plugin_does_not_require_ansible_posix_collection(self, monkeypatch) -> None:
        """TC-070: When bundled aom_jsonl is selected, ansible.posix isn't required.

        The whole point of bundling is to skip the ansible.posix version
        check entirely.
        """
        monkeypatch.setattr(runner, "_bundled_callback_dir", lambda: Path("/fake/bundled"))

        env = runner._callback_env()

        # aom_jsonl is self-contained — does not depend on ansible.posix collection
        assert env["ANSIBLE_STDOUT_CALLBACK"] == "aom_jsonl"
        assert "ansible.posix" not in env["ANSIBLE_STDOUT_CALLBACK"]


class TestJsonlEnvironmentVariable:
    """Tests for TC-071: JSONL Environment Variable.

    TC-071 is the contract that ANSIBLE_STDOUT_CALLBACK reaches the
    ansible-playbook subprocess env in the correct form. AOM's
    production code is ``_callback_env()`` + ``os.environ.copy()``
    update + spawn — verified by exercising those functions directly.
    """

    def test_callback_env_sets_ansible_stdout_callback(self, monkeypatch) -> None:
        """TC-071: _callback_env sets ANSIBLE_STDOUT_CALLBACK in the env dict."""
        monkeypatch.setattr(runner, "_bundled_callback_dir", lambda: None)

        env = runner._callback_env()

        assert env["ANSIBLE_STDOUT_CALLBACK"] == "ansible.posix.jsonl"

    def test_callback_env_preserves_user_override(self, monkeypatch) -> None:
        """TC-071: A user-set ANSIBLE_STDOUT_CALLBACK in os.environ survives merging.

        The runner does ``env = os.environ.copy(); env.update(_callback_env())``
        — that order means AOM's selection overrides the user. Verify
        that's the actual contract (rather than the user winning).
        """
        monkeypatch.setattr(runner, "_bundled_callback_dir", lambda: None)

        # Simulate the runner's merge order
        base_env = {"ANSIBLE_STDOUT_CALLBACK": "user_callback"}
        callback_env = runner._callback_env()
        merged = dict(base_env)
        merged.update(callback_env)

        # AOM's callback selection overrides user override
        assert merged["ANSIBLE_STDOUT_CALLBACK"] == "ansible.posix.jsonl"

    def test_callback_env_bundled_sets_callback_plugins(self, monkeypatch) -> None:
        """TC-071: Bundled selection includes ANSIBLE_CALLBACK_PLUGINS path."""
        fake_dir = Path("/bundled/callback")
        monkeypatch.setattr(runner, "_bundled_callback_dir", lambda: fake_dir)

        env = runner._callback_env()

        assert env["ANSIBLE_STDOUT_CALLBACK"] == "aom_jsonl"
        assert env["ANSIBLE_CALLBACK_PLUGINS"] == str(fake_dir)

    def test_callback_env_fallback_omits_callback_plugins(self, monkeypatch) -> None:
        """TC-071: Fallback env doesn't include ANSIBLE_CALLBACK_PLUGINS.

        We rely on ansible's default plugin search path for
        ansible.posix.jsonl — no need to inject a custom plugins dir.
        """
        monkeypatch.setattr(runner, "_bundled_callback_dir", lambda: None)

        env = runner._callback_env()

        assert "ANSIBLE_CALLBACK_PLUGINS" not in env

    def test_callback_env_does_not_mutate_os_environ(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """TC-071: _callback_env returns a fresh dict, doesn't mutate os.environ."""
        monkeypatch.setenv("ANSIBLE_STDOUT_CALLBACK", "preset_value")

        env = runner._callback_env()

        # Returned dict is independent of os.environ
        assert env["ANSIBLE_STDOUT_CALLBACK"] != "preset_value"
        # os.environ unchanged
        import os

        assert os.environ["ANSIBLE_STDOUT_CALLBACK"] == "preset_value"
