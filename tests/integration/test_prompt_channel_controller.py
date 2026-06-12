"""Controller side of the prompt channel: scan .req, prompt, answer via FIFO."""

from __future__ import annotations

import json
import os
import threading
import time
import uuid
from pathlib import Path

from ansible_aom.ansible.prompt_channel import PromptChannel
from ansible_aom.core.prompt_channel import FIFO_SUFFIX, REQUEST_SUFFIX


def _drop_request(ctrl_dir: Path, host: str, prompt: str) -> tuple[str, Path]:
    """Mimic the plugin: mkfifo + atomic-write a .req. Return (id, fifo_path)."""
    rid = uuid.uuid4().hex
    fifo = ctrl_dir / f"{rid}{FIFO_SUFFIX}"
    os.mkfifo(fifo)
    payload = {"id": rid, "host": host, "prompt": prompt, "created": time.time()}
    tmp = ctrl_dir / f"{rid}{REQUEST_SUFFIX}.tmp"
    tmp.write_text(json.dumps(payload))
    tmp.rename(ctrl_dir / f"{rid}{REQUEST_SUFFIX}")
    return rid, fifo


def test_poll_routes_each_answer_to_its_fifo(tmp_path):
    ctrl = tmp_path / "ctrl"
    ctrl.mkdir()
    channel = PromptChannel(ctrl)

    answers: dict[str, str] = {}

    class FakeRenderer:
        def handle_interactive_prompt(self, prompt_text: str) -> str:
            # Answer encodes which host we were asked about.
            return "yes-web1" if "web1" in prompt_text else "yes-web2"

    # Two pending requests (two hosts hitting the prompt in parallel).
    _, fifo1 = _drop_request(ctrl, "web1", "Deploy web1? ")
    _, fifo2 = _drop_request(ctrl, "web2", "Deploy web2? ")

    # Reader threads unblock the controller's FIFO write and capture the answer.
    def reader(fifo: Path, key: str) -> None:
        with open(fifo, encoding="utf-8") as fh:
            answers[key] = fh.readline().rstrip("\n")

    t1 = threading.Thread(target=reader, args=(fifo1, "web1"))
    t2 = threading.Thread(target=reader, args=(fifo2, "web2"))
    t1.start()
    t2.start()

    # Poll until both handled (controller processes them one at a time).
    deadline = time.time() + 5
    while channel.poll(FakeRenderer()) or time.time() < deadline:
        if answers.get("web1") and answers.get("web2"):
            break
        time.sleep(0.02)

    t1.join(2)
    t2.join(2)
    assert answers == {"web1": "yes-web1", "web2": "yes-web2"}
    # .req files cleaned up after handling.
    assert list(ctrl.glob(f"*{REQUEST_SUFFIX}")) == []


def test_drain_sends_empty_answer_to_outstanding_requests(tmp_path):
    ctrl = tmp_path / "ctrl"
    ctrl.mkdir()
    channel = PromptChannel(ctrl)
    _, fifo = _drop_request(ctrl, "web1", "Deploy? ")

    captured: list[str] = []

    def reader() -> None:
        with open(fifo, encoding="utf-8") as fh:
            captured.append(fh.readline().rstrip("\n"))

    t = threading.Thread(target=reader)
    t.start()
    channel.drain()  # teardown: unblock any worker with an empty (=continue) answer
    t.join(2)
    assert captured == [""]


def test_drain_does_not_hang_when_worker_is_dead(tmp_path):
    """A stale request whose plugin worker died (no FIFO reader) must not block.

    On Ctrl+C the runner force-kills ansible (and its plugin workers) and *then*
    calls ``drain`` in its ``finally``. A blocking ``open(fifo, "w")`` would hang
    forever because nobody is reading — wedging teardown so the terminal is never
    restored. ``drain`` must use a non-blocking write and skip dead workers.
    """
    ctrl = tmp_path / "ctrl"
    ctrl.mkdir()
    channel = PromptChannel(ctrl)
    # FIFO + .req exist but NO reader is ever attached (the worker is "dead").
    _drop_request(ctrl, "web1", "Deploy? ")

    done = threading.Event()

    def run_drain() -> None:
        channel.drain()
        done.set()

    t = threading.Thread(target=run_drain)
    t.start()
    assert done.wait(5), "drain() hung with no FIFO reader attached"
    t.join(1)
    # The stale request is still tombstoned/cleaned up.
    assert list(ctrl.glob(f"*{REQUEST_SUFFIX}")) == []
