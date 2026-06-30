"""Unit tests for the runner's stdout-callback selection.

AOM prefers its bundled ``aom_jsonl`` callback (live per-item loop
streaming) but must fall back to ``ansible.posix.jsonl`` if the bundled
plugin dir can't be resolved, so a packaging glitch never breaks a run.
"""

from __future__ import annotations

from pathlib import Path

from ansible_aom.ansible import runner


class TestBundledCallbackDir:
    def test_resolves_to_existing_dir_with_plugin(self) -> None:
        callback_dir = runner._bundled_callback_dir()
        assert callback_dir is not None
        assert (callback_dir / "aom_jsonl.py").is_file()


class TestCallbackEnv:
    def test_selects_aom_jsonl_when_bundled_dir_present(self, monkeypatch) -> None:
        fake_dir = Path("/some/bundled/callback")
        monkeypatch.setattr(runner, "_bundled_callback_dir", lambda: fake_dir)

        env = runner._callback_env()

        assert env["ANSIBLE_STDOUT_CALLBACK"] == "aom_jsonl"
        assert env["ANSIBLE_CALLBACK_PLUGINS"] == str(fake_dir)

    def test_falls_back_to_posix_jsonl_when_dir_missing(self, monkeypatch) -> None:
        monkeypatch.setattr(runner, "_bundled_callback_dir", lambda: None)

        env = runner._callback_env()

        assert env["ANSIBLE_STDOUT_CALLBACK"] == "ansible.posix.jsonl"
        assert "ANSIBLE_CALLBACK_PLUGINS" not in env
