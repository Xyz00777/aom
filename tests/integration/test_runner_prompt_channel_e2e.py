"""A fake 'ansible-playbook' speaks the prompt channel; the runner services it."""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

from ansible_aom.core.prompt_channel import ENV_VAR


def _fake_channel_client(answers_out: Path) -> tuple[str, list[str]]:
    """Fake child: read AOM_PROMPT_CONTROL_DIR, drop two requests, collect answers.

    Mimics two per-host plugin invocations (web1, web2): for each, mkfifo +
    atomic-write a .req, then block reading the FIFO. Writes the two answers it
    received (newline-joined) to answers_out as proof they were routed.
    """
    code = textwrap.dedent(
        f"""
        import json, os, time, uuid
        ctrl = os.environ[{ENV_VAR!r}]
        got = []
        for host in ("web1", "web2"):
            rid = uuid.uuid4().hex
            fifo = os.path.join(ctrl, rid + ".fifo")
            os.mkfifo(fifo)
            payload = {{"id": rid, "host": host, "prompt": "Deploy " + host + "? ", "created": time.time()}}
            tmp = os.path.join(ctrl, rid + ".req.tmp")
            with open(tmp, "w") as f:
                f.write(json.dumps(payload))
            os.rename(tmp, os.path.join(ctrl, rid + ".req"))
            with open(fifo) as f:
                got.append(f.readline().rstrip(chr(10)))
        with open({str(answers_out)!r}, "w") as f:
            f.write(chr(10).join(got))
        """
    )
    return sys.executable, ["-c", code]


def test_runner_services_channel_requests(tmp_path):
    from ansible_aom.ansible.runner import run_playbook

    answers_out = tmp_path / "answers.txt"
    renderer = MagicMock()
    renderer.handle_interactive_prompt.side_effect = (
        lambda p: "ok-web1" if "web1" in p else "ok-web2"
    )
    cmd, args = _fake_channel_client(answers_out)

    with patch("ansible_aom.ansible.runner._build_command", return_value=(cmd, args)):
        rc = run_playbook("pb.yml", [], renderer, timeout=0.2, session_dir=tmp_path, record=False)

    assert rc == 0
    assert renderer.handle_interactive_prompt.call_count == 2
    assert answers_out.read_text().splitlines() == ["ok-web1", "ok-web2"]
