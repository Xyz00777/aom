"""Integration: the bundled ``aom_jsonl`` callback emits per-item loop events.

``ansible.posix.jsonl`` deliberately drops the ``v2_runner_item_on_*``
hooks, so a loop arrives as a single aggregate event at the end. The
bundled ``aom_jsonl`` callback (a thin subclass) re-emits one JSONL event
per loop item, in real time, which is the only on-the-wire source of
live per-item progress.

These tests run a real ``ansible-playbook`` over a loop fixture with the
bundled callback selected, and assert the item events appear with the
documented envelope.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "ansible"
CALLBACK_DIR = Path(__file__).resolve().parents[2] / "src" / "ansible_aom" / "ansible" / "callback"


def _ansible_collection_paths() -> list[str]:
    """Search-path entries reported by ``ansible-galaxy collection list``.

    A sandboxed ``HOME`` hides collections installed under the real home
    (e.g. ``~/.ansible/collections``), so callers that override ``HOME``
    must forward these paths via ``ANSIBLE_COLLECTIONS_PATH``.
    """
    try:
        result = subprocess.run(
            ["ansible-galaxy", "collection", "list"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.SubprocessError, OSError:
        return []
    paths: list[str] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("# ") and "collections" in line:
            paths.append(line[2:].strip())
    return paths


def _has_ansible_posix() -> bool:
    if shutil.which("ansible-galaxy") is None:
        return False
    try:
        result = subprocess.run(
            ["ansible-galaxy", "collection", "list", "ansible.posix"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.SubprocessError, OSError:
        return False
    return "ansible.posix" in result.stdout


_NEEDS_ANSIBLE = pytest.mark.skipif(
    shutil.which("ansible-playbook") is None or not _has_ansible_posix(),
    reason="ansible-playbook or ansible.posix collection unavailable",
)


def _run_playbook(playbook: Path) -> list[dict]:
    """Run ansible-playbook with the bundled callback; return parsed JSONL events."""
    env = os.environ.copy()
    env["ANSIBLE_CALLBACK_PLUGINS"] = str(CALLBACK_DIR)
    env["ANSIBLE_STDOUT_CALLBACK"] = "aom_jsonl"
    result = subprocess.run(
        [
            "ansible-playbook",
            str(playbook),
            "-i",
            "localhost,",
            "-c",
            "local",
        ],
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"ansible-playbook returned {result.returncode}\n"
        f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
    )
    events: list[dict] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def _run_aom(playbook: Path, home_dir: Path) -> subprocess.CompletedProcess[str]:
    """Spawn ``python -m ansible_aom <playbook>`` against a sandboxed HOME.

    Exercises the full pipeline: the runner selects the bundled aom_jsonl
    callback, which streams item events through the compact renderer.
    """
    import sys

    env = os.environ.copy()
    env["HOME"] = str(home_dir)
    collection_paths = _ansible_collection_paths()
    if collection_paths:
        env["ANSIBLE_COLLECTIONS_PATH"] = ":".join(collection_paths)
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "ansible_aom",
            str(playbook),
            "-i",
            "localhost,",
            "-c",
            "local",
        ],
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )


@_NEEDS_ANSIBLE
class TestLoopItemStreamingEndToEnd:
    """The full ``aom`` pipeline renders one line per loop item, once each."""

    def test_each_item_line_appears_exactly_once(self, tmp_path) -> None:
        result = _run_aom(FIXTURES_DIR / "with_loop.yml", tmp_path)
        assert result.returncode == 0, (
            f"aom returned {result.returncode}\n"
            f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
        )
        out = result.stdout
        # Per-item lines present (live streaming), and not duplicated by the
        # end-of-loop aggregate expansion (dedup).
        for fruit in ("apple", "banana", "cherry"):
            assert out.count(f"(item={fruit})") == 1, (
                f"expected exactly one line for {fruit}, got {out.count(f'(item={fruit})')}\n{out}"
            )


@_NEEDS_ANSIBLE
class TestLoopItemEvents:
    def test_one_item_event_per_loop_iteration(self) -> None:
        events = _run_playbook(FIXTURES_DIR / "with_loop.yml")
        item_events = [e for e in events if e.get("_event") == "v2_runner_item_on_ok"]
        assert len(item_events) == 3

    def test_item_event_carries_label_under_host(self) -> None:
        events = _run_playbook(FIXTURES_DIR / "with_loop.yml")
        labels: list[str] = []
        for e in events:
            if e.get("_event") != "v2_runner_item_on_ok":
                continue
            host_data = e["hosts"]["localhost"]
            labels.append(host_data["_ansible_item_label"])
        assert labels == ["apple", "banana", "cherry"]

    def test_aggregate_event_still_emitted(self) -> None:
        # The item events are additive: the aggregate v2_runner_on_ok must
        # still land at loop end carrying the full results[] array, so
        # downstream consumers that read it are unaffected.
        events = _run_playbook(FIXTURES_DIR / "with_loop.yml")
        aggregates = [
            e
            for e in events
            if e.get("_event") == "v2_runner_on_ok"
            and isinstance(e.get("hosts", {}).get("localhost", {}).get("results"), list)
        ]
        assert len(aggregates) == 1
        assert len(aggregates[0]["hosts"]["localhost"]["results"]) == 3
