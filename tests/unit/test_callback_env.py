"""Unit tests for the runner's stdout-callback selection.

AOM prefers its bundled ``aom_jsonl`` callback (live per-item loop
streaming) but must fall back to ``ansible.posix.jsonl`` if the bundled
plugin dir can't be resolved, so a packaging glitch never breaks a run.

AOM also bundles a notification-type ``aom_connection`` callback in
``src/ansible_aom/callbacks/`` that emits connection-acquired/released
events for the parser's connection-id map. The runner auto-loads it
via ``ANSIBLE_CALLBACK_PLUGINS`` (alongside the stdout callback dir) so
users never need a CLI flag.
"""

from __future__ import annotations

import os
from pathlib import Path

from ansible_aom.ansible import runner


class TestBundledCallbackDir:
    def test_resolves_to_existing_dir_with_plugin(self) -> None:
        callback_dir = runner._bundled_callback_dir()
        assert callback_dir is not None
        assert (callback_dir / "aom_jsonl.py").is_file()


class TestBundledConnectionCallbackDir:
    """Task 5.3: the new connection-tracking callback ships in
    ``src/ansible_aom/callbacks/`` and is auto-loaded via
    ``ANSIBLE_CALLBACK_PLUGINS`` so users don't need a CLI flag.
    """

    def test_resolves_to_existing_dir_with_plugin(self) -> None:
        conn_dir = runner._bundled_connection_callback_dir()
        assert conn_dir is not None
        assert conn_dir.is_dir()
        assert (conn_dir / "aom_connection.py").is_file()

    def test_returns_none_when_plugin_file_missing(self, monkeypatch) -> None:
        # Simulate a packaging glitch where the connection callback file
        # isn't shipped — the helper must return None so the runner can
        # fall back to ANSIBLE's default search path (a missing connection
        # callback is non-fatal: the run just loses per-host connection-id
        # attribution, which is observability, not control flow).
        monkeypatch.setattr(Path, "is_file", lambda self: False)

        result = runner._bundled_connection_callback_dir()

        assert result is None


class TestCallbackEnv:
    def test_selects_aom_jsonl_when_bundled_dir_present(self, monkeypatch) -> None:
        fake_dir = Path("/some/bundled/callback")
        monkeypatch.setattr(runner, "_bundled_callback_dir", lambda: fake_dir)
        # Connection-callback dir is unavailable in this test — only the
        # stdout-callback dir is in the plugin path.
        monkeypatch.setattr(runner, "_bundled_connection_callback_dir", lambda: None)

        env = runner._callback_env()

        assert env["ANSIBLE_STDOUT_CALLBACK"] == "aom_jsonl"
        assert env["ANSIBLE_CALLBACK_PLUGINS"] == str(fake_dir)

    def test_falls_back_to_posix_jsonl_when_dir_missing(self, monkeypatch) -> None:
        monkeypatch.setattr(runner, "_bundled_callback_dir", lambda: None)
        monkeypatch.setattr(runner, "_bundled_connection_callback_dir", lambda: None)

        env = runner._callback_env()

        assert env["ANSIBLE_STDOUT_CALLBACK"] == "ansible.posix.jsonl"
        assert "ANSIBLE_CALLBACK_PLUGINS" not in env

    def test_includes_connection_callback_dir_when_bundled_available(self, monkeypatch) -> None:
        """Task 5.3: ANSIBLE_CALLBACK_PLUGINS includes the connection-callback dir.

        The connection-callback dir ships the ``aom_connection`` notification
        plugin, which emits ``aom_connection_acquired``/``aom_connection_released``
        events for the parser's connection-id map. It must be on the plugin
        search path whenever it resolves, regardless of stdout-callback choice.
        """
        fake_stdout_dir = Path("/some/bundled/stdout")
        fake_conn_dir = Path("/some/bundled/connection")
        monkeypatch.setattr(runner, "_bundled_callback_dir", lambda: fake_stdout_dir)
        monkeypatch.setattr(runner, "_bundled_connection_callback_dir", lambda: fake_conn_dir)

        env = runner._callback_env()

        # Stdout callback is unchanged
        assert env["ANSIBLE_STDOUT_CALLBACK"] == "aom_jsonl"
        # The connection-callback dir is included in the plugins path
        plugins = env["ANSIBLE_CALLBACK_PLUGINS"]
        assert fake_conn_dir.name not in plugins or str(fake_conn_dir) in plugins
        # Concretely: the env value contains both dirs (separated by os.pathsep)
        assert str(fake_stdout_dir) in plugins
        assert str(fake_conn_dir) in plugins

    def test_includes_connection_callback_dir_in_fallback_path(self, monkeypatch) -> None:
        """Task 5.3: even on the ansible.posix.jsonl fallback the connection
        callback is loaded — connection tracking is independent of which
        stdout callback the runner selected.
        """
        fake_conn_dir = Path("/some/bundled/connection")
        monkeypatch.setattr(runner, "_bundled_callback_dir", lambda: None)
        monkeypatch.setattr(runner, "_bundled_connection_callback_dir", lambda: fake_conn_dir)

        env = runner._callback_env()

        # Fallback stdout callback is unchanged
        assert env["ANSIBLE_STDOUT_CALLBACK"] == "ansible.posix.jsonl"
        # Connection-callback dir is still injected (so aom_connection loads)
        assert env["ANSIBLE_CALLBACK_PLUGINS"] == str(fake_conn_dir)

    def test_omits_connection_callback_dir_when_unavailable(self, monkeypatch) -> None:
        """Task 5.3: if the connection-callback dir can't be resolved the
        runner omits it from the env (no empty entries, no broken path).
        """
        fake_stdout_dir = Path("/some/bundled/stdout")
        monkeypatch.setattr(runner, "_bundled_callback_dir", lambda: fake_stdout_dir)
        monkeypatch.setattr(runner, "_bundled_connection_callback_dir", lambda: None)

        env = runner._callback_env()

        assert env["ANSIBLE_STDOUT_CALLBACK"] == "aom_jsonl"
        # Only the stdout-callback dir is in the plugins path
        assert env["ANSIBLE_CALLBACK_PLUGINS"] == str(fake_stdout_dir)

    def test_connection_callback_path_uses_posix_separator(self, monkeypatch) -> None:
        """Task 5.3: when both dirs are present, ANSIBLE_CALLBACK_PLUGINS uses
        the platform path separator (os.pathsep, colon on POSIX) so ansible
        parses the value as a multi-dir search path.
        """
        fake_stdout_dir = Path("/some/bundled/stdout")
        fake_conn_dir = Path("/some/bundled/connection")
        monkeypatch.setattr(runner, "_bundled_callback_dir", lambda: fake_stdout_dir)
        monkeypatch.setattr(runner, "_bundled_connection_callback_dir", lambda: fake_conn_dir)

        env = runner._callback_env()

        plugins = env["ANSIBLE_CALLBACK_PLUGINS"]
        parts = plugins.split(os.pathsep)
        assert str(fake_stdout_dir) in parts
        assert str(fake_conn_dir) in parts
        # Connection-callback dir comes FIRST so it's resolved first in
        # ansible's plugin search order (per Task 5.3 must-do).
        assert parts.index(str(fake_conn_dir)) < parts.index(str(fake_stdout_dir))

    def test_callback_env_does_not_include_empty_separator_entries(self, monkeypatch) -> None:
        """Defensive: never inject an empty ``:`` into ANSIBLE_CALLBACK_PLUGINS
        even if one helper returns None while the other resolves. The path
        string must not start or end with os.pathsep and must not contain
        consecutive separators.
        """
        # Both available — sanity baseline
        fake_stdout_dir = Path("/some/bundled/stdout")
        fake_conn_dir = Path("/some/bundled/connection")
        monkeypatch.setattr(runner, "_bundled_callback_dir", lambda: fake_stdout_dir)
        monkeypatch.setattr(runner, "_bundled_connection_callback_dir", lambda: fake_conn_dir)

        env = runner._callback_env()

        plugins = env["ANSIBLE_CALLBACK_PLUGINS"]
        assert not plugins.startswith(os.pathsep)
        assert not plugins.endswith(os.pathsep)
        assert os.pathsep + os.pathsep not in plugins
