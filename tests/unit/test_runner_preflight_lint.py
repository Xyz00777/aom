"""The runner forwards bypass-prompt lint warnings to the renderer."""

from __future__ import annotations

from pathlib import Path

from ansible_aom.ansible import runner


def test_emit_bypass_warnings_reads_yaml_and_calls_detector(tmp_path, monkeypatch):
    playbook = tmp_path / "deploy.yml"
    playbook.write_text(
        "- name: Deploy\n"
        "  hosts: all\n"
        "  tasks:\n"
        "    - name: Confirm deployment\n"
        "      ansible.builtin.pause:\n"
        "        prompt: 'Deploy to {{ inventory_hostname }}? '\n"
    )

    captured: list[str] = []

    class FakeRenderer:
        def add_warning(self, message: str, is_deprecation: bool) -> None:
            captured.append(message)

    # Two resolved hosts for play 1.
    runner._emit_bypass_prompt_warnings(
        playbook=str(playbook),
        resolved_host_counts=[2],
        renderer=FakeRenderer(),
    )
    assert len(captured) == 1
    assert "Confirm deployment" in captured[0]


def test_emit_bypass_warnings_never_raises_on_bad_yaml(tmp_path):
    playbook = tmp_path / "broken.yml"
    playbook.write_text("this: : : not valid yaml :::\n")

    class FakeRenderer:
        def add_warning(self, message: str, is_deprecation: bool) -> None:
            raise AssertionError("should not be called for unparseable YAML")

    # Must swallow the parse error and simply emit nothing.
    runner._emit_bypass_prompt_warnings(
        playbook=str(playbook),
        resolved_host_counts=[2],
        renderer=FakeRenderer(),
    )
