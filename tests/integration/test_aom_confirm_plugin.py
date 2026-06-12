"""Real ansible: aom.interactive.confirm prompts per host with no serial."""

from __future__ import annotations

import shutil
from pathlib import Path
from unittest.mock import MagicMock

import pytest

FIXTURES = Path(__file__).resolve().parents[2] / ".sisyphus" / "test-fixtures"

_NEEDS_ANSIBLE = pytest.mark.skipif(
    shutil.which("ansible-playbook") is None,
    reason="ansible-playbook unavailable",
)


@_NEEDS_ANSIBLE
def test_confirm_plugin_fires_per_host(tmp_path):
    from ansible_aom.ansible.runner import run_playbook

    renderer = MagicMock()
    seen: list[str] = []
    renderer.handle_interactive_prompt.side_effect = lambda p: seen.append(p) or ""

    rc = run_playbook(
        str(FIXTURES / "aom_confirm_multi.yml"),
        ["-i", str(FIXTURES / "inventory_two_hosts.ini"), "-c", "local"],
        renderer,
        timeout=0.3,
        session_dir=tmp_path,
        record=False,
    )

    assert rc == 0
    assert renderer.handle_interactive_prompt.call_count == 2
    joined = "\n".join(seen)
    assert "web1" in joined and "web2" in joined
