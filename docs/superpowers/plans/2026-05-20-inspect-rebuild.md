# `aom inspect` Rebuild Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild `aom inspect` from a broken CLI into a three-pane Textual TUI that lets the user navigate recent runs, drill into failures, and see the full module error context that is already captured in `events.jsonl`. Also surface the session ID at end-of-run so users discover sessions exist.

**Architecture:**
- A new `core/inspect_model.py` is a pure module that builds `RunSummary`, `TaskTree`, and `DetailBlock` types from a session dict. No I/O, no Textual deps.
- Both the new Textual screen (`tui/screens/inspect.py`) and the new text renderer (`inspect/text.py`) consume the same model — guarantees parity between TTY and CI output.
- The existing CLI (`inspect/cli.py`) is trimmed to three invocations: `aom inspect` (TUI on most-recent run), `aom inspect --text` (text dump), `aom inspect prune`. `list`/`show`/`diff` subcommands and `inspect/diff.py` are deleted.
- The runner (`runner.py`) prints a `Session <short-id>   aom inspect` footer on termination so users know to drill in.

**Tech Stack:** Python 3.14, Textual (existing dep), `pyperclip` for clipboard (already-available — added in this plan if not present). All existing testing infrastructure (`pytest`, ruff, mypy) unchanged.

**Reference:** [`docs/superpowers/specs/2026-05-20-inspect-rebuild-design.md`](../specs/2026-05-20-inspect-rebuild-design.md).

---

## File structure

| File | Responsibility |
|---|---|
| `src/ansible_aom/core/inspect_model.py` (new) | Pure model builders. Frozen dataclasses for `RunSummary`, `StatusCounts`, `TaskTreeNode`, `LoopItem`, `DetailBlock`. Functions: `build_run_summaries`, `build_task_tree`, `build_detail_block`. |
| `src/ansible_aom/core/session.py` (modify) | Add `find_latest_session()`. No other behaviour change. |
| `src/ansible_aom/inspect/text.py` (new) | Renders a session dict (via `core.inspect_model`) to plain text. Output deterministic and ANSI-stripped. |
| `src/ansible_aom/inspect/cli.py` (rewrite) | Argparse for the new surface. Dispatches to TUI / text / prune. |
| `src/ansible_aom/inspect/display.py` (modify) | Keep `format_overhead_section`. Delete `format_session_table`, `format_session_summary`, `format_diff_table`, `format_tree_view`. |
| `src/ansible_aom/inspect/diff.py` (delete) | Diff command removed. |
| `src/ansible_aom/tui/screens/inspect.py` (new) | Textual `Screen` with three panes: Runs / Tasks / Detail. Keybindings, focus management, footer. |
| `src/ansible_aom/runner.py` (modify) | Capture session_id from sink. After renderer.stop(), print footer to stderr. |
| `src/ansible_aom/__main__.py` / `cli.py` (verify) | `aom inspect` already routes to `inspect.cli.main`; no change expected. |
| `tests/unit/test_inspect_model.py` (new) | Unit tests for the model. |
| `tests/unit/test_runner_session_footer.py` (new) | Unit tests that the runner prints the footer at end-of-run. |
| `tests/compact/test_inspect_text_golden.py` (new) | Golden-frame text-mode tests against fixture sessions. |
| `tests/integration/test_inspect_cli.py` (rewrite of existing `test_inspect.py`) | End-to-end CLI invocations against a fixture state dir. |
| `tests/tui/test_inspect_screen.py` (new) | Textual `Pilot` tests for the three panes. |
| `tests/fixtures/sessions/` (new) | Curated `events.jsonl`/`meta.json`/`stderr.log` triples. |
| `tests/conftest.py` (modify) | Autouse `isolated_state_dir` fixture that pins `~/.local/state/aom/sessions` to `tmp_path`. |

---

## Task 1: Curated session fixtures

These fixtures are used by every later task. Lock them down first.

**Files:**
- Create: `tests/fixtures/sessions/clean_run/{events.jsonl,meta.json,stderr.log}`
- Create: `tests/fixtures/sessions/failed_loop/{events.jsonl,meta.json,stderr.log}`
- Create: `tests/fixtures/sessions/multi_host/{events.jsonl,meta.json,stderr.log}`
- Create: `tests/fixtures/sessions/unreachable/{events.jsonl,meta.json,stderr.log}`
- Create: `tests/fixtures/sessions/running/{events.jsonl,meta.json}`
- Create: `tests/fixtures/sessions/__init__.py` (empty marker so pytest discovers)
- Create: `tests/fixtures/sessions/conftest.py` (loader helpers)

- [ ] **Step 1: Create the directory structure**

```bash
mkdir -p tests/fixtures/sessions/{clean_run,failed_loop,multi_host,unreachable,running}
touch tests/fixtures/sessions/__init__.py
```

- [ ] **Step 2: Write `tests/fixtures/sessions/conftest.py` with a loader**

```python
"""Loaders for curated session fixtures.

Each subdirectory under ``tests/fixtures/sessions/`` is a self-contained
session (events.jsonl + meta.json + optional stderr.log) matching the
on-disk layout the runner produces. Tests load them via the
``session_fixture`` fixture which copies a curated session into a
``tmp_path`` so tests can mutate freely without dirtying the checkout.
"""

import json
import shutil
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent


def load_session_dict(name: str) -> dict:
    """Load a curated session fixture as a dict matching load_session()."""
    src = FIXTURES_DIR / name
    meta = json.loads((src / "meta.json").read_text())
    events = [json.loads(line) for line in (src / "events.jsonl").read_text().splitlines() if line.strip()]
    stderr_file = src / "stderr.log"
    stderr = stderr_file.read_text().splitlines() if stderr_file.exists() else []
    return {**meta, "events": events, "stderr": stderr, "session_id": meta["session_id"], "malformed_lines": 0}


@pytest.fixture
def session_fixtures_dir() -> Path:
    """Path to the curated session fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture
def copy_session_fixture(tmp_path: Path):
    """Return a callable that copies a curated session into tmp_path/sessions/."""
    def _copy(name: str) -> Path:
        dst = tmp_path / "sessions" / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(FIXTURES_DIR / name, dst)
        return dst
    return _copy
```

- [ ] **Step 3: Write `clean_run/meta.json`**

```json
{
  "session_id": "019e4000-0000-7000-8000-000000000001",
  "playbook": "ansible/site.yml",
  "ansible_args": ["-i", "inv.ini"],
  "start_time": "2026-05-19T18:02:00.000000Z",
  "end_time": "2026-05-19T18:02:42.000000Z",
  "duration_seconds": 42.0,
  "status": "completed",
  "version": "1.1"
}
```

- [ ] **Step 4: Write `clean_run/events.jsonl`** (minimal but realistic: one play, two tasks, one host all OK)

```json
{"_event":"v2_playbook_on_start","_timestamp":"2026-05-19T18:02:00.000000Z","playbook":{"file":"ansible/site.yml"}}
{"_event":"v2_playbook_on_play_start","_timestamp":"2026-05-19T18:02:00.500000Z","play":{"id":"p1","name":"all"}}
{"_event":"v2_playbook_on_task_start","_timestamp":"2026-05-19T18:02:01.000000Z","task":{"id":"t1","name":"common : ping","path":"roles/common/tasks/main.yml:1","role":"common"},"play":{"id":"p1","name":"all"}}
{"_event":"v2_runner_on_ok","_timestamp":"2026-05-19T18:02:02.000000Z","task":{"id":"t1","name":"common : ping","path":"roles/common/tasks/main.yml:1","role":"common"},"play":{"id":"p1","name":"all"},"hosts":{"web1":{"changed":false,"failed":false}}}
{"_event":"v2_playbook_on_task_start","_timestamp":"2026-05-19T18:02:03.000000Z","task":{"id":"t2","name":"common : echo","path":"roles/common/tasks/main.yml:5","role":"common"},"play":{"id":"p1","name":"all"}}
{"_event":"v2_runner_on_ok","_timestamp":"2026-05-19T18:02:04.000000Z","task":{"id":"t2","name":"common : echo","path":"roles/common/tasks/main.yml:5","role":"common"},"play":{"id":"p1","name":"all"},"hosts":{"web1":{"changed":true,"failed":false}}}
{"_event":"v2_playbook_on_stats","_timestamp":"2026-05-19T18:02:42.000000Z","stats":{"web1":{"ok":2,"changed":1,"failures":0,"unreachable":0,"skipped":0}}}
```

- [ ] **Step 5: Write `failed_loop/meta.json`**

```json
{
  "session_id": "019e4520-fa64-7000-a627-000000000002",
  "playbook": "ansible/site.yml",
  "ansible_args": ["-i", "inv.ini"],
  "start_time": "2026-05-20T11:24:09.700401Z",
  "end_time": "2026-05-20T11:27:10.644058Z",
  "duration_seconds": 180.94,
  "status": "failed",
  "version": "1.1"
}
```

- [ ] **Step 6: Write `failed_loop/events.jsonl`** (modelled on the real brew-cask failure the user hit)

```json
{"_event":"v2_playbook_on_start","_timestamp":"2026-05-20T11:24:09.700401Z","playbook":{"file":"ansible/site.yml"}}
{"_event":"v2_playbook_on_play_start","_timestamp":"2026-05-20T11:24:10.000000Z","play":{"id":"p1","name":"all"}}
{"_event":"v2_playbook_on_task_start","_timestamp":"2026-05-20T11:25:00.000000Z","task":{"id":"t1","name":"os_macos : update brew","path":"roles/os_macos/tasks/main.yml:10","role":"os_macos"},"play":{"id":"p1","name":"all"}}
{"_event":"v2_runner_on_ok","_timestamp":"2026-05-20T11:25:02.000000Z","task":{"id":"t1","name":"os_macos : update brew","path":"roles/os_macos/tasks/main.yml:10","role":"os_macos"},"play":{"id":"p1","name":"all"},"hosts":{"caeli":{"changed":false,"failed":false}}}
{"_event":"v2_playbook_on_task_start","_timestamp":"2026-05-20T11:26:04.000000Z","task":{"id":"t2","name":"os_macos : Install brew casks","path":"roles/os_macos/tasks/main.yml:42","role":"os_macos"},"play":{"id":"p1","name":"all"}}
{"_event":"v2_runner_on_failed","_timestamp":"2026-05-20T11:27:07.172559Z","task":{"id":"t2","name":"os_macos : Install brew casks","path":"roles/os_macos/tasks/main.yml:42","role":"os_macos"},"play":{"id":"p1","name":"all"},"hosts":{"caeli":{"action":"community.general.homebrew_cask","changed":false,"failed":true,"msg":"One or more items failed","results":[{"_ansible_item_label":"amethyst","item":"amethyst","failed":false,"changed":false,"msg":"Cask already installed: amethyst"},{"_ansible_item_label":"karabiner-elements","item":"karabiner-elements","failed":true,"changed":false,"msg":"Cask 'karabiner-elements' is not available","stderr":"curl: (22) The requested URL returned error: 404"},{"_ansible_item_label":"rectangle","item":"rectangle","failed":true,"changed":false,"msg":"Download failed","stderr":"curl: (28) Operation timed out after 30000 ms"}]}}}
{"_event":"v2_playbook_on_stats","_timestamp":"2026-05-20T11:27:10.644058Z","stats":{"caeli":{"ok":1,"changed":0,"failures":1,"unreachable":0,"skipped":0}}}
```

- [ ] **Step 7: Write `failed_loop/stderr.log`**

```
+ brew update
Updated 2 taps (homebrew/core, homebrew/cask).
==> Downloading https://example.com/karabiner-elements
curl: (22) The requested URL returned error: 404
```

- [ ] **Step 8: Write `multi_host/meta.json`** (3 hosts, 1 failure on web2, others OK)

```json
{
  "session_id": "019e4100-0000-7000-8000-000000000003",
  "playbook": "playbooks/deploy.yml",
  "ansible_args": ["-i", "inv.ini"],
  "start_time": "2026-05-19T15:00:00.000000Z",
  "end_time": "2026-05-19T15:00:30.000000Z",
  "duration_seconds": 30.0,
  "status": "failed",
  "version": "1.1"
}
```

- [ ] **Step 9: Write `multi_host/events.jsonl`** (one task fans out to 3 hosts; 2 OK, 1 failed)

```json
{"_event":"v2_playbook_on_start","_timestamp":"2026-05-19T15:00:00.000000Z","playbook":{"file":"playbooks/deploy.yml"}}
{"_event":"v2_playbook_on_play_start","_timestamp":"2026-05-19T15:00:00.500000Z","play":{"id":"p1","name":"web"}}
{"_event":"v2_playbook_on_task_start","_timestamp":"2026-05-19T15:00:01.000000Z","task":{"id":"t1","name":"deploy : restart service","path":"playbooks/deploy.yml:10"},"play":{"id":"p1","name":"web"}}
{"_event":"v2_runner_on_ok","_timestamp":"2026-05-19T15:00:05.000000Z","task":{"id":"t1","name":"deploy : restart service","path":"playbooks/deploy.yml:10"},"play":{"id":"p1","name":"web"},"hosts":{"web1":{"changed":true,"failed":false}}}
{"_event":"v2_runner_on_ok","_timestamp":"2026-05-19T15:00:06.000000Z","task":{"id":"t1","name":"deploy : restart service","path":"playbooks/deploy.yml:10"},"play":{"id":"p1","name":"web"},"hosts":{"web3":{"changed":true,"failed":false}}}
{"_event":"v2_runner_on_failed","_timestamp":"2026-05-19T15:00:07.000000Z","task":{"id":"t1","name":"deploy : restart service","path":"playbooks/deploy.yml:10"},"play":{"id":"p1","name":"web"},"hosts":{"web2":{"changed":false,"failed":true,"msg":"systemctl: Unit not found"}}}
{"_event":"v2_playbook_on_stats","_timestamp":"2026-05-19T15:00:30.000000Z","stats":{"web1":{"ok":1,"changed":1,"failures":0,"unreachable":0,"skipped":0},"web2":{"ok":0,"changed":0,"failures":1,"unreachable":0,"skipped":0},"web3":{"ok":1,"changed":1,"failures":0,"unreachable":0,"skipped":0}}}
```

- [ ] **Step 10: Write `multi_host/stderr.log`** (empty file)

Just create the file:

```bash
: > tests/fixtures/sessions/multi_host/stderr.log
```

- [ ] **Step 11: Write `unreachable/meta.json` and `events.jsonl`**

`unreachable/meta.json`:
```json
{
  "session_id": "019e4200-0000-7000-8000-000000000004",
  "playbook": "playbooks/deploy.yml",
  "ansible_args": [],
  "start_time": "2026-05-19T16:00:00.000000Z",
  "end_time": "2026-05-19T16:00:05.000000Z",
  "duration_seconds": 5.0,
  "status": "failed",
  "version": "1.1"
}
```

`unreachable/events.jsonl`:
```json
{"_event":"v2_playbook_on_start","_timestamp":"2026-05-19T16:00:00.000000Z","playbook":{"file":"playbooks/deploy.yml"}}
{"_event":"v2_playbook_on_play_start","_timestamp":"2026-05-19T16:00:00.500000Z","play":{"id":"p1","name":"web"}}
{"_event":"v2_playbook_on_task_start","_timestamp":"2026-05-19T16:00:01.000000Z","task":{"id":"t1","name":"deploy : ping","path":"playbooks/deploy.yml:5"},"play":{"id":"p1","name":"web"}}
{"_event":"v2_runner_on_unreachable","_timestamp":"2026-05-19T16:00:04.000000Z","task":{"id":"t1","name":"deploy : ping","path":"playbooks/deploy.yml:5"},"play":{"id":"p1","name":"web"},"hosts":{"web2":{"unreachable":true,"failed":true,"msg":"Failed to connect to the host via ssh: ssh: connect to host web2 port 22: Connection refused"}}}
{"_event":"v2_playbook_on_stats","_timestamp":"2026-05-19T16:00:05.000000Z","stats":{"web2":{"ok":0,"changed":0,"failures":0,"unreachable":1,"skipped":0}}}
```

Touch an empty stderr.log:

```bash
: > tests/fixtures/sessions/unreachable/stderr.log
```

- [ ] **Step 12: Write `running/meta.json`** (no `end_time`, no `status`, no `duration_seconds`)

```json
{
  "session_id": "019e4300-0000-7000-8000-000000000005",
  "playbook": "ansible/site.yml",
  "ansible_args": [],
  "start_time": "2026-05-20T12:00:00.000000Z",
  "version": "1.1"
}
```

- [ ] **Step 13: Write `running/events.jsonl`** (one play started, no task yet)

```json
{"_event":"v2_playbook_on_start","_timestamp":"2026-05-20T12:00:00.000000Z","playbook":{"file":"ansible/site.yml"}}
{"_event":"v2_playbook_on_play_start","_timestamp":"2026-05-20T12:00:00.500000Z","play":{"id":"p1","name":"all"}}
{"_event":"v2_playbook_on_task_start","_timestamp":"2026-05-20T12:00:01.000000Z","task":{"id":"t1","name":"common : ping","path":"roles/common/tasks/main.yml:1"},"play":{"id":"p1","name":"all"}}
```

- [ ] **Step 14: Run the existing test suite to confirm the fixtures don't break anything**

Run: `uv run pytest tests/ -q`
Expected: PASS (fixtures aren't loaded by any test yet).

- [ ] **Step 15: Commit**

```bash
git add tests/fixtures/sessions/
git commit -m "test: curated session fixtures for inspect rebuild"
```

---

## Task 2: `core.inspect_model` — types and `StatusCounts`

**Files:**
- Create: `src/ansible_aom/core/inspect_model.py`
- Create: `tests/unit/test_inspect_model.py`

- [ ] **Step 1: Write the failing test for `StatusCounts`**

`tests/unit/test_inspect_model.py`:
```python
"""Unit tests for core.inspect_model — pure builders over session dicts."""

from ansible_aom.core.inspect_model import StatusCounts


def test_statuscounts_starts_empty():
    counts = StatusCounts()
    assert counts.ok == 0
    assert counts.changed == 0
    assert counts.failed == 0
    assert counts.skipped == 0
    assert counts.unreachable == 0
    assert counts.total == 0


def test_statuscounts_add_event_ok():
    counts = StatusCounts().add_event("v2_runner_on_ok", changed=False)
    assert counts.ok == 1
    assert counts.changed == 0
    assert counts.total == 1


def test_statuscounts_add_event_changed():
    counts = StatusCounts().add_event("v2_runner_on_ok", changed=True)
    assert counts.ok == 0
    assert counts.changed == 1
    assert counts.total == 1


def test_statuscounts_add_event_failed():
    counts = StatusCounts().add_event("v2_runner_on_failed", changed=False)
    assert counts.failed == 1


def test_statuscounts_add_event_skipped():
    counts = StatusCounts().add_event("v2_runner_on_skipped", changed=False)
    assert counts.skipped == 1


def test_statuscounts_add_event_unreachable():
    counts = StatusCounts().add_event("v2_runner_on_unreachable", changed=False)
    assert counts.unreachable == 1


def test_statuscounts_merge():
    a = StatusCounts(ok=2, failed=1)
    b = StatusCounts(ok=3, changed=4)
    merged = a.merge(b)
    assert merged.ok == 5
    assert merged.changed == 4
    assert merged.failed == 1
    assert merged.total == 10


def test_statuscounts_is_all_ok():
    assert StatusCounts(ok=5, changed=2).is_all_ok() is True
    assert StatusCounts(ok=5, failed=1).is_all_ok() is False
    assert StatusCounts(ok=5, unreachable=1).is_all_ok() is False
    assert StatusCounts().is_all_ok() is True
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/unit/test_inspect_model.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'ansible_aom.core.inspect_model'`

- [ ] **Step 3: Implement `StatusCounts`**

`src/ansible_aom/core/inspect_model.py`:
```python
"""Pure builders over session dicts for the inspect TUI and text renderer.

This module owns the view logic that turns a session dict (as produced by
``core.session.load_session``) into the data structures the UI consumes:
``RunSummary`` (left pane), ``TaskTreeNode`` (middle pane), and
``DetailBlock`` (right pane).

The module is intentionally pure: it never reads from disk, never imports
Textual or Rich, and never mutates its inputs. The TUI and the text-mode
renderer both consume the same builders, which is what guarantees they
render the same information for the same session.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Mapping


@dataclass(frozen=True)
class StatusCounts:
    """Aggregate status tally over (task × host) pairs.

    Each ``v2_runner_on_*`` event contributes exactly one bump. A task
    that ran on three hosts with two OK + one failed adds ``ok=2,
    failed=1`` to its parent's totals.
    """

    ok: int = 0
    changed: int = 0
    failed: int = 0
    skipped: int = 0
    unreachable: int = 0

    @property
    def total(self) -> int:
        return self.ok + self.changed + self.failed + self.skipped + self.unreachable

    def add_event(self, event_type: str, *, changed: bool) -> "StatusCounts":
        """Return a new StatusCounts with the bump for one runner event."""
        if event_type == "v2_runner_on_ok":
            if changed:
                return replace(self, changed=self.changed + 1)
            return replace(self, ok=self.ok + 1)
        if event_type == "v2_runner_on_failed":
            return replace(self, failed=self.failed + 1)
        if event_type == "v2_runner_on_skipped":
            return replace(self, skipped=self.skipped + 1)
        if event_type == "v2_runner_on_unreachable":
            return replace(self, unreachable=self.unreachable + 1)
        return self

    def merge(self, other: "StatusCounts") -> "StatusCounts":
        return StatusCounts(
            ok=self.ok + other.ok,
            changed=self.changed + other.changed,
            failed=self.failed + other.failed,
            skipped=self.skipped + other.skipped,
            unreachable=self.unreachable + other.unreachable,
        )

    def is_all_ok(self) -> bool:
        """True if no failure / unreachable. Skipped counts as OK for collapse decisions."""
        return self.failed == 0 and self.unreachable == 0
```

- [ ] **Step 4: Run the test**

Run: `uv run pytest tests/unit/test_inspect_model.py -v`
Expected: all 8 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/ansible_aom/core/inspect_model.py tests/unit/test_inspect_model.py
git commit -m "feat(inspect): StatusCounts model"
```

---

## Task 3: `core.inspect_model` — `RunSummary` builder

**Files:**
- Modify: `src/ansible_aom/core/inspect_model.py`
- Modify: `tests/unit/test_inspect_model.py`

- [ ] **Step 1: Write the failing test for `build_run_summary`**

Append to `tests/unit/test_inspect_model.py`:
```python
from datetime import datetime, timedelta, timezone

from ansible_aom.core.inspect_model import RunSummary, build_run_summary


def _load_fixture(name: str) -> dict:
    """Helper: load a session fixture as load_session would return it."""
    import json
    from pathlib import Path
    src = Path(__file__).parent.parent / "fixtures" / "sessions" / name
    meta = json.loads((src / "meta.json").read_text())
    events = [json.loads(line) for line in (src / "events.jsonl").read_text().splitlines() if line.strip()]
    stderr_file = src / "stderr.log"
    stderr = stderr_file.read_text().splitlines() if stderr_file.exists() else []
    return {**meta, "events": events, "stderr": stderr, "session_id": meta["session_id"], "malformed_lines": 0}


def test_run_summary_clean():
    session = _load_fixture("clean_run")
    summary = build_run_summary(session)
    assert summary.session_id == "019e4000-0000-7000-8000-000000000001"
    assert summary.short_id == "019e4000"
    assert summary.playbook == "ansible/site.yml"
    assert summary.status == "completed"
    assert summary.start_time == datetime(2026, 5, 19, 18, 2, 0, tzinfo=timezone.utc)
    assert summary.end_time == datetime(2026, 5, 19, 18, 2, 42, tzinfo=timezone.utc)
    assert summary.duration == timedelta(seconds=42)
    assert summary.failed_task_count == 0
    assert summary.host_counts == {"web1": StatusCounts(ok=1, changed=1)}


def test_run_summary_failed_loop():
    session = _load_fixture("failed_loop")
    summary = build_run_summary(session)
    assert summary.status == "failed"
    assert summary.failed_task_count == 1
    assert summary.host_counts == {"caeli": StatusCounts(ok=1, failed=1)}


def test_run_summary_running_has_no_end():
    session = _load_fixture("running")
    summary = build_run_summary(session)
    assert summary.status == "running"
    assert summary.end_time is None
    assert summary.duration is None
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/unit/test_inspect_model.py -v`
Expected: FAIL with `ImportError` for `RunSummary` and `build_run_summary`.

- [ ] **Step 3: Implement `RunSummary` and `build_run_summary`**

Append to `src/ansible_aom/core/inspect_model.py`:
```python
@dataclass(frozen=True)
class RunSummary:
    """Per-session view consumed by the Runs pane and the text-mode header."""

    session_id: str
    short_id: str
    playbook: str
    start_time: datetime | None
    end_time: datetime | None
    duration: "timedelta | None"
    status: str  # "completed" | "failed" | "crashed" | "running"
    host_counts: Mapping[str, StatusCounts]
    failed_task_count: int


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def build_run_summary(session: dict) -> RunSummary:
    """Derive a ``RunSummary`` from a session dict (output of ``load_session``)."""
    from datetime import timedelta

    session_id = session.get("session_id", "")
    status = session.get("status") or ("running" if not session.get("end_time") else "unknown")
    start_time = _parse_iso(session.get("start_time"))
    end_time = _parse_iso(session.get("end_time"))
    duration_seconds = session.get("duration_seconds")
    duration = timedelta(seconds=duration_seconds) if duration_seconds is not None else None

    host_counts: dict[str, StatusCounts] = {}
    failed_task_ids: set[str] = set()

    for event in session.get("events", []):
        event_type = event.get("_event", "")
        if event_type not in (
            "v2_runner_on_ok",
            "v2_runner_on_failed",
            "v2_runner_on_skipped",
            "v2_runner_on_unreachable",
        ):
            continue
        hosts = event.get("hosts") or {}
        task_id = (event.get("task") or {}).get("id", "")
        for host, result in hosts.items():
            changed = bool(result.get("changed", False)) if isinstance(result, dict) else False
            current = host_counts.get(host, StatusCounts())
            host_counts[host] = current.add_event(event_type, changed=changed)
        if event_type == "v2_runner_on_failed" and task_id:
            failed_task_ids.add(task_id)

    return RunSummary(
        session_id=session_id,
        short_id=session_id[:8],
        playbook=session.get("playbook", ""),
        start_time=start_time,
        end_time=end_time,
        duration=duration,
        status=status,
        host_counts=host_counts,
        failed_task_count=len(failed_task_ids),
    )
```

- [ ] **Step 4: Run the tests**

Run: `uv run pytest tests/unit/test_inspect_model.py -v`
Expected: all tests PASS.

- [ ] **Step 5: Add `build_run_summaries` (plural) for the Runs pane**

Append to `src/ansible_aom/core/inspect_model.py`:
```python
def build_run_summaries(sessions: list[dict]) -> list[RunSummary]:
    """Map a list of session dicts to RunSummary, sorted newest-first by start_time.

    Sessions with no start_time sort to the end. Used by the Runs pane.
    """
    summaries = [build_run_summary(s) for s in sessions]
    summaries.sort(
        key=lambda s: s.start_time or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return summaries
```

(Import `timezone` at top of file if not already there.)

- [ ] **Step 6: Add test for plural builder**

Append to `tests/unit/test_inspect_model.py`:
```python
from ansible_aom.core.inspect_model import build_run_summaries


def test_run_summaries_sorted_newest_first():
    sessions = [
        _load_fixture("clean_run"),       # 2026-05-19 18:02
        _load_fixture("failed_loop"),     # 2026-05-20 11:24
        _load_fixture("multi_host"),      # 2026-05-19 15:00
    ]
    summaries = build_run_summaries(sessions)
    assert [s.short_id for s in summaries] == ["019e4520", "019e4000", "019e4100"]
```

- [ ] **Step 7: Run, then commit**

Run: `uv run pytest tests/unit/test_inspect_model.py -v` — Expected: all PASS.

```bash
git add src/ansible_aom/core/inspect_model.py tests/unit/test_inspect_model.py
git commit -m "feat(inspect): build_run_summary + build_run_summaries"
```

---

## Task 4: `core.inspect_model` — `TaskTreeNode` builder

**Files:**
- Modify: `src/ansible_aom/core/inspect_model.py`
- Modify: `tests/unit/test_inspect_model.py`

- [ ] **Step 1: Write the failing test for `build_task_tree` (clean run)**

Append to `tests/unit/test_inspect_model.py`:
```python
from ansible_aom.core.inspect_model import TaskTreeNode, build_task_tree


def test_task_tree_clean_run_groups_by_role():
    session = _load_fixture("clean_run")
    root = build_task_tree(session)
    # Top-level is the run; children are plays.
    assert root.kind == "run"
    assert len(root.children) == 1
    play = root.children[0]
    assert play.kind == "play"
    assert play.label == "all"
    assert play.stats == StatusCounts(ok=1, changed=1)
    # One group: role "common"
    assert len(play.children) == 1
    group = play.children[0]
    assert group.kind == "group"
    assert group.label == "common"
    assert group.stats == StatusCounts(ok=1, changed=1)
    # Two tasks inside
    task_labels = [c.label for c in group.children]
    assert task_labels == ["common : ping", "common : echo"]


def test_task_tree_failed_loop_marks_failure_path():
    session = _load_fixture("failed_loop")
    root = build_task_tree(session)
    play = root.children[0]
    group = play.children[0]
    assert group.label == "os_macos"
    assert group.stats == StatusCounts(ok=1, failed=1)
    failed_task = next(c for c in group.children if c.stats.failed > 0)
    assert failed_task.label == "os_macos : Install brew casks"
    assert failed_task.path == "roles/os_macos/tasks/main.yml:42"
    # Failed task has one host child
    assert len(failed_task.children) == 1
    host_node = failed_task.children[0]
    assert host_node.kind == "host"
    assert host_node.label == "caeli"
    assert host_node.stats == StatusCounts(failed=1)


def test_task_tree_multi_host_per_host_breakdown():
    session = _load_fixture("multi_host")
    root = build_task_tree(session)
    play = root.children[0]
    assert play.per_host == {
        "web1": StatusCounts(changed=1),
        "web2": StatusCounts(failed=1),
        "web3": StatusCounts(changed=1),
    }
```

- [ ] **Step 2: Run the test to confirm it fails**

Run: `uv run pytest tests/unit/test_inspect_model.py::test_task_tree_clean_run_groups_by_role -v`
Expected: FAIL with `ImportError` for `TaskTreeNode` / `build_task_tree`.

- [ ] **Step 3: Implement `TaskTreeNode` and `build_task_tree`**

Append to `src/ansible_aom/core/inspect_model.py`:
```python
from typing import Literal


@dataclass(frozen=True)
class TaskTreeNode:
    """Hierarchical view of a session's tasks.

    Levels: run → play → group → task → host. ``group`` is the
    role-or-source bucket (see ``_group_key``); when a task has no
    natural grouping the bucket key is ``"_root"`` and renders as a
    flat list under the play.
    """

    kind: Literal["run", "play", "group", "task", "host"]
    label: str
    stats: StatusCounts = field(default_factory=StatusCounts)
    per_host: Mapping[str, StatusCounts] = field(default_factory=dict)
    children: tuple["TaskTreeNode", ...] = ()
    path: str | None = None
    duration: "timedelta | None" = None
    raw_event: dict | None = None
    task_id: str | None = None  # so the detail pane can fetch the underlying event


def _group_key(task: dict) -> str:
    """Determine the grouping bucket for a task.

    Order of preference:
    1. ``task.role`` (most reliable, present in JSONL for role tasks).
    2. First meaningful component of ``task.path`` (e.g.
       ``roles/<name>/tasks/main.yml:42`` → ``<name>``;
       ``playbooks/site.yml:8`` → ``playbooks``).
    3. ``"_root"`` (renders flat under the play).
    """
    role = task.get("role")
    if role:
        return str(role)
    path = task.get("path") or ""
    if path.startswith("roles/"):
        parts = path.split("/", 3)
        if len(parts) >= 2:
            return parts[1]
    if "/" in path:
        return path.split("/", 1)[0]
    return "_root"


def _runner_event_type(event: dict) -> str | None:
    et = event.get("_event", "")
    if et in (
        "v2_runner_on_ok",
        "v2_runner_on_failed",
        "v2_runner_on_skipped",
        "v2_runner_on_unreachable",
    ):
        return et
    return None


def build_task_tree(session: dict) -> TaskTreeNode:
    """Build the hierarchical task tree for one session."""
    from datetime import timedelta

    events = session.get("events", [])

    # Collect plays in order of appearance.
    play_order: list[tuple[str, str]] = []  # (play_id, play_name)
    play_seen: set[str] = set()
    for event in events:
        if event.get("_event") == "v2_playbook_on_play_start":
            play = event.get("play") or {}
            pid = str(play.get("id", ""))
            if pid and pid not in play_seen:
                play_seen.add(pid)
                play_order.append((pid, str(play.get("name", "unknown"))))

    # Group runner events by (play_id, group_key, task_id).
    task_starts: dict[str, dict] = {}
    for event in events:
        if event.get("_event") == "v2_playbook_on_task_start":
            tid = str((event.get("task") or {}).get("id", ""))
            if tid:
                task_starts[tid] = event

    # Aggregate per task: collect runner events, derive label/path/group/play.
    task_records: dict[str, dict] = {}
    # task_id -> {label, path, group, play_id, per_host: dict[host, list[(event_type, changed)]], raw_event, start_ts}
    for event in events:
        et = _runner_event_type(event)
        if not et:
            continue
        task = event.get("task") or {}
        tid = str(task.get("id", ""))
        if not tid:
            continue
        play = event.get("play") or {}
        pid = str(play.get("id", ""))
        rec = task_records.setdefault(
            tid,
            {
                "label": str(task.get("name", "")),
                "path": task.get("path"),
                "group": _group_key(task),
                "play_id": pid,
                "events": [],  # list of (event_type, host, changed, event)
            },
        )
        hosts = event.get("hosts") or {}
        for host, result in hosts.items():
            changed = bool(result.get("changed", False)) if isinstance(result, dict) else False
            rec["events"].append((et, str(host), changed, event))

    # Derive task duration from task_start to last runner event.
    task_start_ts: dict[str, datetime] = {}
    for tid, ts_event in task_starts.items():
        ts = _parse_iso(ts_event.get("_timestamp"))
        if ts is not None:
            task_start_ts[tid] = ts

    def _last_ts_for(tid: str) -> datetime | None:
        latest: datetime | None = None
        for _, _, _, e in task_records.get(tid, {}).get("events", []):
            ts = _parse_iso(e.get("_timestamp"))
            if ts is not None and (latest is None or ts > latest):
                latest = ts
        return latest

    # Build per-play, per-group structure.
    play_children: dict[str, dict[str, list[TaskTreeNode]]] = {pid: {} for pid, _ in play_order}

    for tid, rec in task_records.items():
        pid = rec["play_id"]
        if pid not in play_children:
            # Task with no matching play_start — drop into a synthetic play.
            play_order.append((pid or "_unknown", "unknown"))
            play_children[pid or "_unknown"] = {}
        grp = rec["group"]
        # Aggregate stats for the task across hosts.
        task_counts = StatusCounts()
        per_host_counts: dict[str, StatusCounts] = {}
        for et, host, changed, _ in rec["events"]:
            task_counts = task_counts.add_event(et, changed=changed)
            per_host_counts[host] = per_host_counts.get(host, StatusCounts()).add_event(
                et, changed=changed
            )
        # Host children (one per host that ran the task).
        host_nodes: list[TaskTreeNode] = []
        for host, counts in per_host_counts.items():
            # Find the last runner event for (task, host) to attach raw_event.
            last_event: dict | None = None
            for et, h, _, e in rec["events"]:
                if h == host:
                    last_event = e
            host_nodes.append(
                TaskTreeNode(
                    kind="host",
                    label=host,
                    stats=counts,
                    raw_event=last_event,
                    task_id=tid,
                )
            )
        duration: timedelta | None = None
        start = task_start_ts.get(tid)
        last = _last_ts_for(tid)
        if start is not None and last is not None:
            duration = last - start

        task_node = TaskTreeNode(
            kind="task",
            label=rec["label"],
            stats=task_counts,
            per_host=per_host_counts,
            children=tuple(host_nodes),
            path=rec["path"],
            duration=duration,
            raw_event=rec["events"][-1][3] if rec["events"] else None,
            task_id=tid,
        )
        play_children[pid].setdefault(grp, []).append(task_node)

    # Assemble groups into plays.
    play_nodes: list[TaskTreeNode] = []
    for pid, pname in play_order:
        groups = play_children.get(pid, {})
        group_nodes: list[TaskTreeNode] = []
        play_stats = StatusCounts()
        play_per_host: dict[str, StatusCounts] = {}
        for gkey, tasks in groups.items():
            grp_stats = StatusCounts()
            grp_per_host: dict[str, StatusCounts] = {}
            for t in tasks:
                grp_stats = grp_stats.merge(t.stats)
                for host, counts in t.per_host.items():
                    grp_per_host[host] = grp_per_host.get(host, StatusCounts()).merge(counts)
            play_stats = play_stats.merge(grp_stats)
            for host, counts in grp_per_host.items():
                play_per_host[host] = play_per_host.get(host, StatusCounts()).merge(counts)
            if gkey == "_root":
                # Flat: tasks directly under the play.
                group_nodes.extend(tasks)
            else:
                group_nodes.append(
                    TaskTreeNode(
                        kind="group",
                        label=gkey,
                        stats=grp_stats,
                        per_host=grp_per_host,
                        children=tuple(tasks),
                    )
                )
        play_nodes.append(
            TaskTreeNode(
                kind="play",
                label=pname,
                stats=play_stats,
                per_host=play_per_host,
                children=tuple(group_nodes),
            )
        )

    # Roll up to the run node.
    run_stats = StatusCounts()
    run_per_host: dict[str, StatusCounts] = {}
    for p in play_nodes:
        run_stats = run_stats.merge(p.stats)
        for host, counts in p.per_host.items():
            run_per_host[host] = run_per_host.get(host, StatusCounts()).merge(counts)

    return TaskTreeNode(
        kind="run",
        label=session.get("playbook", ""),
        stats=run_stats,
        per_host=run_per_host,
        children=tuple(play_nodes),
    )
```

- [ ] **Step 4: Run all model tests**

Run: `uv run pytest tests/unit/test_inspect_model.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/ansible_aom/core/inspect_model.py tests/unit/test_inspect_model.py
git commit -m "feat(inspect): build_task_tree hierarchy + stat roll-up"
```

---

## Task 5: `core.inspect_model` — `DetailBlock` builder

**Files:**
- Modify: `src/ansible_aom/core/inspect_model.py`
- Modify: `tests/unit/test_inspect_model.py`

- [ ] **Step 1: Write failing tests for `LoopItem` and `build_detail_block`**

Append to `tests/unit/test_inspect_model.py`:
```python
from ansible_aom.core.inspect_model import DetailBlock, LoopItem, build_detail_block


def test_detail_block_loop_failure():
    session = _load_fixture("failed_loop")
    root = build_task_tree(session)
    play = root.children[0]
    group = play.children[0]
    failed_task = next(c for c in group.children if c.stats.failed > 0)
    host_node = failed_task.children[0]  # caeli
    block = build_detail_block(session, failed_task, host_node)

    assert block.task_name == "os_macos : Install brew casks"
    assert block.host == "caeli"
    assert block.file_line == "roles/os_macos/tasks/main.yml:42"
    assert block.status == "failed"
    assert block.msg == "One or more items failed"
    # 1 OK item, 2 failed items in the fixture
    assert len(block.failed_items) == 2
    assert block.failed_items[0].label == "karabiner-elements"
    assert "404" in (block.failed_items[0].stderr or "")
    assert len(block.ok_items) == 1
    assert block.ok_items[0].label == "amethyst"
    # stderr tail comes from session["stderr"]
    assert any("curl" in line for line in block.session_stderr_tail)


def test_detail_block_unreachable():
    session = _load_fixture("unreachable")
    root = build_task_tree(session)
    play = root.children[0]
    task = play.children[0]
    host_node = task.children[0]
    block = build_detail_block(session, task, host_node)
    assert block.status == "unreachable"
    assert "Connection refused" in (block.msg or "")


def test_detail_block_ok_task_no_failure_items():
    session = _load_fixture("clean_run")
    root = build_task_tree(session)
    play = root.children[0]
    group = play.children[0]
    task = group.children[0]
    host_node = task.children[0]
    block = build_detail_block(session, task, host_node)
    assert block.status == "ok"
    assert block.failed_items == ()
    assert block.ok_items == ()
```

- [ ] **Step 2: Run to confirm failure**

Run: `uv run pytest tests/unit/test_inspect_model.py -v`
Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement `LoopItem` and `build_detail_block`**

Append to `src/ansible_aom/core/inspect_model.py`:
```python
@dataclass(frozen=True)
class LoopItem:
    """One entry from a task's loop ``results[]`` array."""

    label: str
    failed: bool
    changed: bool
    msg: str | None
    stderr: str | None


@dataclass(frozen=True)
class DetailBlock:
    """Right-pane data for a focused (task, host) pair."""

    task_name: str
    file_line: str | None
    host: str | None
    duration: "timedelta | None"
    status: str  # "ok" | "changed" | "failed" | "skipped" | "unreachable"
    msg: str | None
    failed_items: tuple[LoopItem, ...]
    ok_items: tuple[LoopItem, ...]
    module_stdout: str | None
    module_stderr: str | None
    session_stderr_tail: tuple[str, ...]
    raw_event: dict | None


def _status_from_event_type(event_type: str, changed: bool) -> str:
    if event_type == "v2_runner_on_ok":
        return "changed" if changed else "ok"
    if event_type == "v2_runner_on_failed":
        return "failed"
    if event_type == "v2_runner_on_skipped":
        return "skipped"
    if event_type == "v2_runner_on_unreachable":
        return "unreachable"
    return "unknown"


def _make_loop_item(raw: dict) -> LoopItem:
    label = str(raw.get("_ansible_item_label") or raw.get("item") or "")
    return LoopItem(
        label=label,
        failed=bool(raw.get("failed", False)),
        changed=bool(raw.get("changed", False)),
        msg=raw.get("msg"),
        stderr=raw.get("stderr") or raw.get("module_stderr"),
    )


def build_detail_block(
    session: dict,
    task_node: TaskTreeNode,
    host_node: TaskTreeNode | None,
    *,
    stderr_tail_lines: int = 20,
) -> DetailBlock:
    """Build the right-pane DetailBlock for a focused (task, host) pair.

    ``host_node`` may be None to aggregate over all hosts that ran the
    task (used when the user focuses the task row itself rather than
    drilling into a host child). In aggregate mode the first failed
    host's event is used as the basis, falling back to any event.
    """
    raw_event: dict | None = None
    host_label: str | None = None
    if host_node is not None and host_node.kind == "host":
        host_label = host_node.label
        raw_event = host_node.raw_event
    else:
        raw_event = task_node.raw_event

    event_type = (raw_event or {}).get("_event", "")
    host_data: dict = {}
    if raw_event and host_label and host_label in (raw_event.get("hosts") or {}):
        host_data = raw_event["hosts"][host_label]
    elif raw_event:
        hosts = raw_event.get("hosts") or {}
        if hosts:
            host_label = host_label or next(iter(hosts))
            host_data = hosts.get(host_label, {})

    changed = bool(host_data.get("changed", False))
    status = _status_from_event_type(event_type, changed)
    msg = host_data.get("msg")

    failed_items: list[LoopItem] = []
    ok_items: list[LoopItem] = []
    for raw in host_data.get("results") or []:
        if not isinstance(raw, dict):
            continue
        item = _make_loop_item(raw)
        (failed_items if item.failed else ok_items).append(item)

    stderr_lines = session.get("stderr") or []
    tail = tuple(stderr_lines[-stderr_tail_lines:])

    return DetailBlock(
        task_name=task_node.label,
        file_line=task_node.path,
        host=host_label,
        duration=task_node.duration,
        status=status,
        msg=msg if isinstance(msg, str) else None,
        failed_items=tuple(failed_items),
        ok_items=tuple(ok_items),
        module_stdout=host_data.get("stdout"),
        module_stderr=host_data.get("stderr") or host_data.get("module_stderr"),
        session_stderr_tail=tail,
        raw_event=raw_event,
    )
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/unit/test_inspect_model.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/ansible_aom/core/inspect_model.py tests/unit/test_inspect_model.py
git commit -m "feat(inspect): build_detail_block with loop result extraction"
```

---

## Task 6: `core.session.find_latest_session`

**Files:**
- Modify: `src/ansible_aom/core/session.py`
- Modify: `tests/unit/test_session.py` (if missing, create)

- [ ] **Step 1: Find or create the session unit test file**

```bash
ls tests/unit/test_session*.py
```

If none exists, create `tests/unit/test_session_helpers.py`.

- [ ] **Step 2: Write failing test for `find_latest_session`**

`tests/unit/test_session_helpers.py`:
```python
"""Unit tests for core.session helper functions."""

import json
from pathlib import Path

from ansible_aom.core.session import find_latest_session


def _write_session(root: Path, session_id: str, start_time: str) -> None:
    d = root / session_id
    d.mkdir(parents=True)
    (d / "meta.json").write_text(json.dumps({
        "session_id": session_id,
        "playbook": "p.yml",
        "start_time": start_time,
        "version": "1.1",
    }))


def test_find_latest_returns_newest(tmp_path: Path):
    state = tmp_path / "sessions"
    state.mkdir()
    _write_session(state, "019e4000-0000-7000-8000-000000000001", "2026-05-19T18:02:00.000Z")
    _write_session(state, "019e4520-0000-7000-8000-000000000002", "2026-05-20T11:24:09.000Z")
    _write_session(state, "019e4100-0000-7000-8000-000000000003", "2026-05-19T15:00:00.000Z")

    latest = find_latest_session(state)
    assert latest == "019e4520-0000-7000-8000-000000000002"


def test_find_latest_returns_none_when_empty(tmp_path: Path):
    state = tmp_path / "sessions"
    state.mkdir()
    assert find_latest_session(state) is None


def test_find_latest_returns_none_when_dir_missing(tmp_path: Path):
    assert find_latest_session(tmp_path / "nope") is None
```

- [ ] **Step 3: Run to verify fail**

Run: `uv run pytest tests/unit/test_session_helpers.py -v`
Expected: FAIL with `ImportError`.

- [ ] **Step 4: Implement `find_latest_session`**

Append to `src/ansible_aom/core/session.py`:
```python
def find_latest_session(session_dir: Path) -> str | None:
    """Return the session_id of the most-recently-started session, or None.

    Reads meta.json for each subdirectory, picks the entry with the
    latest ``start_time``. Sessions without a parseable start_time are
    ignored. Returns ``None`` when no sessions exist.
    """
    sessions = list_sessions(session_dir)
    if not sessions:
        return None
    return sessions[0].get("session_id")
```

(``list_sessions`` already returns newest-first; reuse it.)

- [ ] **Step 5: Run and commit**

Run: `uv run pytest tests/unit/test_session_helpers.py -v` — expect PASS.

```bash
git add src/ansible_aom/core/session.py tests/unit/test_session_helpers.py
git commit -m "feat(session): find_latest_session helper"
```

---

## Task 7: Text-mode renderer (`inspect/text.py`)

**Files:**
- Create: `src/ansible_aom/inspect/text.py`
- Create: `tests/compact/test_inspect_text_golden.py`

- [ ] **Step 1: Write failing test for clean-run text output**

`tests/compact/test_inspect_text_golden.py`:
```python
"""Golden-frame tests for the text-mode inspect renderer."""

import json
from pathlib import Path

import pytest

from ansible_aom.inspect.text import render_session


def _load(name: str) -> dict:
    src = Path(__file__).parent.parent / "fixtures" / "sessions" / name
    meta = json.loads((src / "meta.json").read_text())
    events = [json.loads(line) for line in (src / "events.jsonl").read_text().splitlines() if line.strip()]
    stderr_file = src / "stderr.log"
    stderr = stderr_file.read_text().splitlines() if stderr_file.exists() else []
    return {**meta, "events": events, "stderr": stderr, "session_id": meta["session_id"], "malformed_lines": 0}


def test_render_clean_run_has_header_and_no_failure_block():
    output = render_session(_load("clean_run"))
    assert "Session 019e4000-0000-7000-8000-000000000001" in output
    assert "Playbook ansible/site.yml" in output
    assert "Status   completed" in output
    assert "Failures" not in output


def test_render_failed_loop_shows_msg_and_failed_items():
    output = render_session(_load("failed_loop"))
    assert "Status   failed" in output
    assert "os_macos : Install brew casks" in output
    assert "One or more items failed" in output
    assert "karabiner-elements" in output
    assert "rectangle" in output
    assert "404" in output
    # OK items are not enumerated in text mode (only count)
    assert "amethyst" not in output or "(1 ok item" in output


def test_render_unreachable_shows_connection_msg():
    output = render_session(_load("unreachable"))
    assert "Connection refused" in output


def test_render_running_shows_running_status():
    output = render_session(_load("running"))
    assert "Status   running" in output


def test_render_includes_stderr_tail_on_failure():
    output = render_session(_load("failed_loop"))
    assert "stderr.log" in output
    assert "curl: (22)" in output
```

- [ ] **Step 2: Run to confirm fail**

Run: `uv run pytest tests/compact/test_inspect_text_golden.py -v`
Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement `render_session`**

`src/ansible_aom/inspect/text.py`:
```python
"""Plain-text rendering of an inspect session.

Used by ``aom inspect --text`` (and as the non-TTY fallback when stdout
isn't a terminal). Output is ANSI-free, deterministic, pipe-safe.

Consumes the same ``core.inspect_model`` builders the TUI uses, so the
two render the same information for the same session.
"""

from __future__ import annotations

from typing import Iterable

from ansible_aom.core.inspect_model import (
    DetailBlock,
    RunSummary,
    StatusCounts,
    TaskTreeNode,
    build_detail_block,
    build_run_summary,
    build_task_tree,
)


def _fmt_duration(seconds: float | None) -> str:
    if seconds is None:
        return "—"
    if seconds < 60:
        return f"{seconds:.0f}s"
    minutes, sec = divmod(int(seconds), 60)
    if minutes < 60:
        return f"{minutes}m{sec:02d}s"
    hours, mins = divmod(minutes, 60)
    return f"{hours}h{mins:02d}m{sec:02d}s"


def _host_counts_line(host: str, counts: StatusCounts) -> str:
    parts: list[str] = []
    if counts.ok:
        parts.append(f"{counts.ok} ok")
    if counts.changed:
        parts.append(f"{counts.changed} changed")
    if counts.failed:
        parts.append(f"{counts.failed} failed")
    if counts.unreachable:
        parts.append(f"{counts.unreachable} unreachable")
    if counts.skipped:
        parts.append(f"{counts.skipped} skipped")
    body = ", ".join(parts) or "no events"
    return f"  {host}: {body}"


def _render_header(summary: RunSummary) -> list[str]:
    lines = [
        f"Session  {summary.session_id}",
        f"Playbook {summary.playbook}",
    ]
    if summary.start_time:
        lines.append(f"Started  {summary.start_time.isoformat().replace('+00:00', 'Z')}")
    if summary.end_time:
        lines.append(f"Ended    {summary.end_time.isoformat().replace('+00:00', 'Z')}")
    dur = summary.duration.total_seconds() if summary.duration else None
    lines.append(f"Duration {_fmt_duration(dur)}")
    lines.append(f"Status   {summary.status}")
    if summary.host_counts:
        lines.append("")
        lines.append("Stats")
        for host, counts in sorted(summary.host_counts.items()):
            lines.append(_host_counts_line(host, counts))
    return lines


def _iter_failed_tasks(node: TaskTreeNode):
    """Walk the tree yielding (task_node, host_node) for every failed/unreachable host."""
    if node.kind == "task":
        for child in node.children:
            if child.kind == "host" and (child.stats.failed or child.stats.unreachable):
                yield node, child
    else:
        for child in node.children:
            yield from _iter_failed_tasks(child)


def _render_detail(block: DetailBlock) -> list[str]:
    lines: list[str] = []
    lines.append(f"Task: {block.task_name}")
    if block.file_line:
        lines.append(f"File: {block.file_line}")
    if block.host:
        lines.append(f"Host: {block.host}")
    if block.duration is not None:
        lines.append(f"Time: {_fmt_duration(block.duration.total_seconds())}")
    lines.append("")
    if block.msg:
        lines.append(f"  msg: {block.msg}")
        lines.append("")
    if block.failed_items:
        lines.append(
            f"  Failed items ({len(block.failed_items)} of "
            f"{len(block.failed_items) + len(block.ok_items)}):"
        )
        for item in block.failed_items:
            lines.append(f"    ✖ {item.label}")
            if item.msg:
                lines.append(f"        {item.msg}")
            if item.stderr:
                lines.append(f"        stderr: {item.stderr}")
        if block.ok_items:
            lines.append(f"  ({len(block.ok_items)} ok items)")
    if block.module_stderr and not block.failed_items:
        # Non-loop failure: show module stderr directly.
        lines.append("  stderr:")
        for line in block.module_stderr.splitlines():
            lines.append(f"    {line}")
    return lines


def _render_failures(session: dict, tree: TaskTreeNode) -> list[str]:
    pairs = list(_iter_failed_tasks(tree))
    if not pairs:
        return []
    lines = ["", f"Failures ({len(pairs)})", "─" * 13]
    for task_node, host_node in pairs:
        block = build_detail_block(session, task_node, host_node)
        lines.extend(_render_detail(block))
        lines.append("")
    return lines


def _render_stderr_tail(session: dict, max_lines: int = 20) -> list[str]:
    tail: list[str] = (session.get("stderr") or [])[-max_lines:]
    if not tail:
        return []
    return ["stderr.log (tail)", "─" * 17, *tail]


def render_session(session: dict) -> str:
    """Render a session dict as plain text. ANSI-free, deterministic."""
    summary = build_run_summary(session)
    tree = build_task_tree(session)
    parts: list[str] = []
    parts.extend(_render_header(summary))
    parts.extend(_render_failures(session, tree))
    if summary.status == "failed":
        parts.append("")
        parts.extend(_render_stderr_tail(session))
    return "\n".join(parts) + "\n"


def render_session_list(summaries: Iterable[RunSummary]) -> str:
    """Render a list of run summaries as a plain-text table.

    Used only when the new no-arg CLI falls back to text mode without
    a specific session (`aom inspect --text --list` style — but the
    spec dropped the explicit list command, so this is kept as a
    library helper for future use, not currently invoked).
    """
    rows = ["Date              Playbook                Dur   Status"]
    rows.append("─" * 64)
    for s in summaries:
        date = s.start_time.strftime("%Y-%m-%d %H:%M") if s.start_time else "—"
        dur = _fmt_duration(s.duration.total_seconds() if s.duration else None)
        playbook = s.playbook if len(s.playbook) <= 22 else s.playbook[:19] + "..."
        rows.append(f"{date:<17} {playbook:<22}  {dur:>5}  {s.status}")
    return "\n".join(rows) + "\n"
```

- [ ] **Step 4: Run the tests**

Run: `uv run pytest tests/compact/test_inspect_text_golden.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/ansible_aom/inspect/text.py tests/compact/test_inspect_text_golden.py
git commit -m "feat(inspect): plain-text renderer with failure detail"
```

---

## Task 8: Rebuild `inspect/cli.py` (drop list/show/diff, add --text)

**Files:**
- Modify: `src/ansible_aom/inspect/cli.py`
- Modify: `src/ansible_aom/inspect/display.py` (remove dead code)
- Delete: `src/ansible_aom/inspect/diff.py`
- Rewrite: `tests/integration/test_inspect.py` → `tests/integration/test_inspect_cli.py`

- [ ] **Step 1: Inspect existing test contracts to know what NOT to break**

```bash
grep -n "def test_" tests/integration/test_inspect.py | head -30
```

Note the current test names; we'll port the still-relevant ones.

- [ ] **Step 2: Write failing tests for the new CLI**

Create `tests/integration/test_inspect_cli.py`:
```python
"""Integration tests for the rebuilt `aom inspect` CLI."""

import json
import shutil
import sys
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent.parent / "fixtures" / "sessions"


@pytest.fixture
def state_dir(tmp_path: Path) -> Path:
    state = tmp_path / "sessions"
    state.mkdir()
    for name in ("clean_run", "failed_loop", "multi_host"):
        shutil.copytree(FIXTURES / name, state / name)
    return state


def test_text_mode_dumps_latest_session(state_dir: Path, capsys):
    from ansible_aom.inspect.cli import main
    exit_code = main(["--text", "--state-dir", str(state_dir)])
    assert exit_code == 0
    captured = capsys.readouterr()
    # failed_loop is the latest; should be the one rendered.
    assert "019e4520" in captured.out
    assert "One or more items failed" in captured.out


def test_text_mode_with_empty_state_returns_zero_and_message(tmp_path: Path, capsys):
    state = tmp_path / "sessions"
    state.mkdir()
    from ansible_aom.inspect.cli import main
    exit_code = main(["--text", "--state-dir", str(state)])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "No sessions" in out


def test_no_arg_invocation_falls_back_to_text_when_non_tty(state_dir: Path, capsys):
    from ansible_aom.inspect.cli import main
    # When stdout is not a TTY (capsys redirects), the no-arg invocation
    # auto-falls-back to text mode rather than launching the TUI.
    exit_code = main(["--state-dir", str(state_dir)])
    assert exit_code == 0
    assert "019e4520" in capsys.readouterr().out


def test_prune_subcommand(state_dir: Path, capsys):
    from ansible_aom.inspect.cli import main
    # All fixture sessions are < days=10000, so this is a no-op cleanup.
    exit_code = main(["--state-dir", str(state_dir), "prune", "--days", "10000"])
    assert exit_code == 0
    assert "Pruned" in capsys.readouterr().out


def test_old_list_subcommand_is_gone(state_dir: Path, capsys):
    from ansible_aom.inspect.cli import main
    # `list` used to be a subcommand; it is now removed.
    with pytest.raises(SystemExit):
        main(["--state-dir", str(state_dir), "list"])


def test_old_show_subcommand_is_gone(state_dir: Path, capsys):
    from ansible_aom.inspect.cli import main
    with pytest.raises(SystemExit):
        main(["--state-dir", str(state_dir), "show", "019e4520"])
```

- [ ] **Step 3: Run the tests to confirm they fail**

Run: `uv run pytest tests/integration/test_inspect_cli.py -v`
Expected: failures (current CLI has `list/show/diff` subcommands; `--text` is not yet a top-level option).

- [ ] **Step 4: Rewrite `src/ansible_aom/inspect/cli.py`**

```python
"""Inspect CLI commands for AOM (rebuilt).

The CLI exposes three invocations:

* ``aom inspect``         — launch the TUI on the most recent session.
* ``aom inspect --text``  — dump the most recent session as plain text.
* ``aom inspect prune``   — clean up old sessions on disk.

The legacy ``list`` / ``show`` / ``diff`` subcommands are removed;
chronological in-TUI navigation replaces them.

When stdout is not a TTY (CI, pipe, redirect), the no-arg invocation
falls back to ``--text`` automatically so scripts and SSH workflows
keep working.

See ``docs/superpowers/specs/2026-05-20-inspect-rebuild-design.md``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ansible_aom.core.session import (
    cleanup_old_sessions,
    find_latest_session,
    load_session,
)
from ansible_aom.inspect.text import render_session


def _default_state_dir() -> Path:
    return Path.home() / ".local" / "state" / "aom" / "sessions"


def _stdout_is_tty() -> bool:
    try:
        return sys.stdout.isatty()
    except (AttributeError, ValueError):
        return False


def inspect_text(state_dir: Path) -> int:
    """Print the most-recent session as plain text. Return exit code."""
    latest = find_latest_session(state_dir)
    if latest is None:
        print("No sessions found in", state_dir)
        return 0
    session = load_session(latest, state_dir)
    if session is None:
        print(f"Session not found: {latest}", file=sys.stderr)
        return 1
    print(render_session(session), end="")
    return 0


def inspect_tui(state_dir: Path) -> int:
    """Launch the TUI inspector. Returns the TUI's exit code."""
    # Lazy import: keeps `--text` invocation free of Textual cost.
    from ansible_aom.tui.screens.inspect import InspectApp

    latest = find_latest_session(state_dir)
    app = InspectApp(state_dir=state_dir, initial_session_id=latest)
    app.run()
    return 0


def inspect_prune(state_dir: Path, days: int) -> int:
    """Remove sessions older than ``days`` days."""
    deleted = cleanup_old_sessions(state_dir, keep_days=days)
    print(f"Pruned {deleted} session(s)")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aom inspect",
        description="Inspect AOM sessions",
    )
    parser.add_argument(
        "--state-dir",
        type=Path,
        default=_default_state_dir(),
        help="Directory containing session data",
    )
    parser.add_argument(
        "--text",
        action="store_true",
        help="Render output as plain text instead of launching the TUI "
        "(also implied when stdout is not a TTY).",
    )
    sub = parser.add_subparsers(dest="command", help="Subcommand")

    prune = sub.add_parser("prune", help="Remove old sessions")
    prune.add_argument("--days", type=int, default=30, help="Remove sessions older than N days")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "prune":
        return inspect_prune(args.state_dir, args.days)

    use_text = args.text or not _stdout_is_tty()
    if use_text:
        return inspect_text(args.state_dir)
    return inspect_tui(args.state_dir)


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Stub `tui/screens/inspect.py` so the lazy import doesn't crash**

Create `src/ansible_aom/tui/screens/inspect.py`:
```python
"""Inspect TUI app — stub. Real implementation lands in later tasks."""

from __future__ import annotations

from pathlib import Path


class InspectApp:
    """Stub. Replaced by a real Textual ``App`` in Task 12+."""

    def __init__(self, *, state_dir: Path, initial_session_id: str | None = None) -> None:
        self.state_dir = state_dir
        self.initial_session_id = initial_session_id

    def run(self) -> None:
        raise NotImplementedError("InspectApp is not yet implemented")
```

The CLI tests use `capsys` so stdout is not a TTY → they hit the text-mode branch and never instantiate `InspectApp`. The stub exists only so the import resolves.

- [ ] **Step 6: Delete the legacy diff module and trim display.py**

```bash
git rm src/ansible_aom/inspect/diff.py
```

Edit `src/ansible_aom/inspect/display.py`: keep only `_fmt_seconds` and `format_overhead_section`. Delete `format_session_table`, `format_session_summary`, `format_diff_table`, `format_tree_view`.

- [ ] **Step 7: Update or delete the old test file**

```bash
git rm tests/integration/test_inspect.py
```

(Its replacements live in `test_inspect_cli.py`.)

- [ ] **Step 8: Search for remaining references to deleted symbols**

Run:
```bash
grep -rn "from ansible_aom.inspect.diff" tests/ src/ || true
grep -rn "format_session_table\|format_diff_table\|format_tree_view\|format_session_summary" tests/ src/ || true
grep -rn "inspect_list\|inspect_show\|inspect_diff" tests/ src/ || true
```

Delete or update any remaining references.

- [ ] **Step 9: Verify the top-level CLI dispatcher still routes correctly**

Run:
```bash
grep -n "inspect" src/ansible_aom/cli.py | head
```

Confirm the dispatch still calls `inspect.cli.main(...)` with the right argv slice. Adjust if it referenced specific subcommands.

- [ ] **Step 10: Run the new CLI tests**

Run: `uv run pytest tests/integration/test_inspect_cli.py -v`
Expected: all PASS.

- [ ] **Step 11: Run the full unit + compact suite**

Run: `uv run pytest tests/unit tests/compact -q`
Expected: PASS.

- [ ] **Step 12: Commit**

```bash
git add -A
git commit -m "feat(inspect): rebuild CLI; drop list/show/diff; add --text"
```

---

## Task 9: Runner prints session-ID footer

**Files:**
- Modify: `src/ansible_aom/runner.py`
- Create: `tests/unit/test_runner_session_footer.py`

- [ ] **Step 1: Write the failing test**

`tests/unit/test_runner_session_footer.py`:
```python
"""The runner prints a `Session …  aom inspect` footer on termination."""

import sys
from unittest.mock import patch

from ansible_aom.runner import _print_session_footer


def test_footer_prints_short_id_and_inspect_hint(capsys):
    _print_session_footer(
        session_id="019e4520-fa64-7000-a627-5b8efe0da85f",
        stderr_isatty=True,
    )
    captured = capsys.readouterr()
    # Footer goes to stderr so it survives `aom site.yml | tee log`.
    assert "019e4520" in captured.err
    assert "aom inspect" in captured.err


def test_footer_suppressed_when_no_session_id(capsys):
    _print_session_footer(session_id=None, stderr_isatty=True)
    captured = capsys.readouterr()
    assert captured.err == ""


def test_footer_suppressed_when_stderr_not_tty(capsys):
    _print_session_footer(
        session_id="019e4520-fa64-7000-a627-5b8efe0da85f",
        stderr_isatty=False,
    )
    captured = capsys.readouterr()
    assert captured.err == ""
```

- [ ] **Step 2: Run to confirm failure**

Run: `uv run pytest tests/unit/test_runner_session_footer.py -v`
Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement `_print_session_footer` and call it from `run_playbook`**

Edit `src/ansible_aom/runner.py`:

(1) Add a `session_id` property to `_SessionSink`:
```python
    @property
    def session_id(self) -> str | None:
        return self._session_id
```
And to `_NullSink`:
```python
    @property
    def session_id(self) -> str | None:
        return None
```

(2) Add the footer helper near the top of the module (after the imports, before `_NullSink`):
```python
def _print_session_footer(*, session_id: str | None, stderr_isatty: bool) -> None:
    """Print the end-of-run hint that points users at `aom inspect`.

    Suppressed in two cases:
    - The runner had no session (recording disabled or failed to start).
    - stderr is not a TTY (CI, pipe, redirect) — keeps script output clean.
    """
    if not session_id or not stderr_isatty:
        return
    short = session_id[:8]
    sys.stderr.write(f"\nSession {short}   aom inspect\n")
    sys.stderr.flush()
```

(3) In `run_playbook`, after the `finally: renderer.stop()` block, capture the sink's session_id and emit the footer. Replace the existing `finally`:
```python
    finally:
        renderer.stop()
        try:
            stderr_tty = sys.stderr.isatty()
        except (AttributeError, ValueError):
            stderr_tty = False
        _print_session_footer(
            session_id=getattr(sink, "session_id", None),
            stderr_isatty=stderr_tty,
        )
```

- [ ] **Step 4: Run the footer unit test**

Run: `uv run pytest tests/unit/test_runner_session_footer.py -v`
Expected: PASS.

- [ ] **Step 5: Run the existing runner tests to confirm no regression**

Run: `uv run pytest tests/integration/test_runner_session_recording.py tests/unit/test_runner_heartbeat.py tests/unit/test_runner_stall_flush.py -v`
Expected: PASS. If any test asserts no stderr output, update it to allow the footer line.

- [ ] **Step 6: Commit**

```bash
git add src/ansible_aom/runner.py tests/unit/test_runner_session_footer.py
git commit -m "feat(runner): print Session <id> aom inspect footer on termination"
```

---

## Task 10: Test-leakage fix (autouse `isolated_state_dir`)

**Files:**
- Modify: `tests/conftest.py`

- [ ] **Step 1: Check current conftest.py**

```bash
cat tests/conftest.py 2>/dev/null || echo "no conftest yet"
```

- [ ] **Step 2: Add the autouse fixture**

Either create `tests/conftest.py` or append to it:
```python
"""Pytest-level fixtures shared across the suite."""

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_state_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Pin AOM's state directory to ``tmp_path`` for every test.

    Without this, runner integration tests write real sessions into
    ``~/.local/state/aom/sessions/``, polluting the user's machine and
    causing flaky test ordering. The fixture monkeypatches the
    ``_default_session_dir`` and ``inspect.cli._default_state_dir``
    helpers to point at a per-test ``tmp_path / "aom-state" / "sessions"``.
    """
    state = tmp_path / "aom-state" / "sessions"
    state.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(
        "ansible_aom.runner._default_session_dir",
        lambda: state,
    )
    monkeypatch.setattr(
        "ansible_aom.inspect.cli._default_state_dir",
        lambda: state,
    )
    monkeypatch.setenv("HOME", str(tmp_path / "fake-home"))
    return state
```

- [ ] **Step 3: Add a guard test that asserts no leakage**

`tests/unit/test_state_dir_isolation.py`:
```python
"""Guard: tests must not write into the real ~/.local/state/aom path."""

from pathlib import Path

from ansible_aom.runner import _default_session_dir
from ansible_aom.inspect.cli import _default_state_dir


def test_runner_state_dir_is_isolated():
    p = _default_session_dir()
    assert "aom-state" in str(p) or "tmp" in str(p)
    assert ".local/state/aom" not in str(p) or "tmp" in str(p)


def test_inspect_state_dir_is_isolated():
    p = _default_state_dir()
    assert "aom-state" in str(p) or "tmp" in str(p)
```

- [ ] **Step 4: Run the full suite**

Run: `uv run pytest tests/ -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/conftest.py tests/unit/test_state_dir_isolation.py
git commit -m "test: autouse isolated state dir; stop session leakage"
```

---

## Task 11: TUI screen — Runs pane (left)

**Files:**
- Rewrite: `src/ansible_aom/tui/screens/inspect.py`
- Create: `tests/tui/test_inspect_screen.py`

- [ ] **Step 1: Check Textual API patterns used elsewhere**

```bash
ls src/ansible_aom/tui/screens/
grep -l "class.*App" src/ansible_aom/tui/screens/*.py | head
```

Skim one existing screen for the project's `ListView`/`DataTable` patterns.

- [ ] **Step 2: Write failing Pilot tests for the Runs pane**

`tests/tui/test_inspect_screen.py`:
```python
"""Pilot tests for the Inspect TUI screen — Runs pane first."""

import json
import shutil
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent.parent / "fixtures" / "sessions"


@pytest.fixture
def state_dir(tmp_path: Path) -> Path:
    state = tmp_path / "sessions"
    state.mkdir()
    for name in ("clean_run", "failed_loop", "multi_host", "unreachable"):
        shutil.copytree(FIXTURES / name, state / name)
    return state


@pytest.mark.asyncio
async def test_runs_pane_lists_newest_first(state_dir: Path):
    from ansible_aom.tui.screens.inspect import InspectApp
    app = InspectApp(state_dir=state_dir)
    async with app.run_test() as pilot:
        await pilot.pause()
        # The runs DataTable should have 4 rows; row 0 is the newest.
        runs_table = app.query_one("#runs-table")
        assert runs_table.row_count == 4
        first_row_key = runs_table.coordinate_to_cell_key((0, 0)).row_key
        # The first row's session_id should be failed_loop (newest start_time).
        assert app.selected_session_id == "019e4520-fa64-7000-a627-000000000002"


@pytest.mark.asyncio
async def test_runs_pane_failed_filter(state_dir: Path):
    from ansible_aom.tui.screens.inspect import InspectApp
    app = InspectApp(state_dir=state_dir)
    async with app.run_test() as pilot:
        await pilot.pause()
        # Press `f` to filter to failed-only.
        await pilot.press("f")
        await pilot.pause()
        runs_table = app.query_one("#runs-table")
        # clean_run is the only "completed" session in the fixtures — filter
        # should drop it to 3.
        assert runs_table.row_count == 3
```

- [ ] **Step 3: Run to confirm failure**

Run: `uv run pytest tests/tui/test_inspect_screen.py -v`
Expected: FAIL (stub raises NotImplementedError).

- [ ] **Step 4: Implement the Runs pane**

Rewrite `src/ansible_aom/tui/screens/inspect.py`:
```python
"""Inspect TUI app — three-pane browser for past AOM sessions.

Pane 1 (Runs): newest-first list of sessions with date, playbook, duration, status.
Pane 2 (Tasks): hierarchical task tree for the selected run.
Pane 3 (Detail): failure-first detail block for the focused (task, host).

This task builds pane 1; panes 2 and 3 are added in later tasks.
"""

from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import DataTable, Footer, Header

from ansible_aom.core.inspect_model import build_run_summary
from ansible_aom.core.session import list_sessions, load_session


def _fmt_duration_short(seconds: float | None) -> str:
    if seconds is None:
        return "—"
    if seconds < 60:
        return f"{seconds:.0f}s"
    minutes, sec = divmod(int(seconds), 60)
    if minutes < 60:
        return f"{minutes}m{sec:02d}s"
    hours, mins = divmod(minutes, 60)
    return f"{hours}h{mins:02d}m"


_STATUS_ICON = {
    "completed": "✓",
    "failed": "✖",
    "crashed": "!",
    "running": "⠋",
}


class InspectApp(App):
    """Three-pane inspector. Pane 1 wired; panes 2 + 3 stubbed."""

    CSS = """
    Horizontal { height: 100%; }
    DataTable { width: 1fr; }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("f", "toggle_failed", "Failed-only"),
    ]

    def __init__(self, *, state_dir: Path, initial_session_id: str | None = None) -> None:
        super().__init__()
        self.state_dir = state_dir
        self.initial_session_id = initial_session_id
        self.selected_session_id: str | None = None
        self._all_summaries: list = []  # list[RunSummary]
        self._failed_only = False

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield DataTable(id="runs-table", cursor_type="row")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#runs-table", DataTable)
        table.add_columns("Date", "Playbook", "Dur", "")
        self._reload_runs()
        if self.initial_session_id:
            self._select_session(self.initial_session_id)

    def _reload_runs(self) -> None:
        raws = list_sessions(self.state_dir)
        summaries = []
        for raw in raws:
            session = load_session(raw["session_id"], self.state_dir)
            if session is not None:
                summaries.append(build_run_summary(session))
        self._all_summaries = summaries
        self._refresh_table()
        if summaries and self.selected_session_id is None:
            self.selected_session_id = summaries[0].session_id

    def _refresh_table(self) -> None:
        table = self.query_one("#runs-table", DataTable)
        table.clear()
        for s in self._visible_summaries():
            date = s.start_time.strftime("%Y-%m-%d %H:%M") if s.start_time else "—"
            dur = _fmt_duration_short(s.duration.total_seconds() if s.duration else None)
            icon = _STATUS_ICON.get(s.status, "?")
            playbook = s.playbook if len(s.playbook) <= 24 else "…" + s.playbook[-23:]
            table.add_row(date, playbook, dur, icon, key=s.session_id)

    def _visible_summaries(self):
        if self._failed_only:
            return [s for s in self._all_summaries if s.status in ("failed", "crashed")]
        return self._all_summaries

    def _select_session(self, session_id: str) -> None:
        table = self.query_one("#runs-table", DataTable)
        for idx, s in enumerate(self._visible_summaries()):
            if s.session_id == session_id:
                table.move_cursor(row=idx)
                self.selected_session_id = session_id
                return

    def action_toggle_failed(self) -> None:
        self._failed_only = not self._failed_only
        self._refresh_table()
```

- [ ] **Step 5: Run the Pilot tests**

Run: `uv run pytest tests/tui/test_inspect_screen.py -v`
Expected: PASS.

- [ ] **Step 6: Run the integration CLI tests again to confirm the no-TTY branch still works**

Run: `uv run pytest tests/integration/test_inspect_cli.py -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/ansible_aom/tui/screens/inspect.py tests/tui/test_inspect_screen.py
git commit -m "feat(inspect-tui): Runs pane (list + failed-only filter)"
```

---

## Task 12: TUI screen — Tasks pane (middle)

**Files:**
- Modify: `src/ansible_aom/tui/screens/inspect.py`
- Modify: `tests/tui/test_inspect_screen.py`

- [ ] **Step 1: Write failing Pilot test for Tasks pane**

Append to `tests/tui/test_inspect_screen.py`:
```python
@pytest.mark.asyncio
async def test_tasks_pane_shows_tree_for_selected_run(state_dir: Path):
    from ansible_aom.tui.screens.inspect import InspectApp
    app = InspectApp(state_dir=state_dir)
    async with app.run_test() as pilot:
        await pilot.pause()
        # failed_loop is the default selected run.
        tree = app.query_one("#tasks-tree")
        # The tree should be populated; root label is "all" (the play).
        labels = [str(n.label) for n in tree.root.children]
        assert any("all" in lbl for lbl in labels)


@pytest.mark.asyncio
async def test_tasks_pane_auto_expands_failure_path(state_dir: Path):
    from ansible_aom.tui.screens.inspect import InspectApp
    app = InspectApp(state_dir=state_dir)
    async with app.run_test() as pilot:
        await pilot.pause()
        tree = app.query_one("#tasks-tree")
        # The "os_macos" group has a failure; it must be auto-expanded.
        os_macos = next(
            n for n in tree.root.children[0].children if "os_macos" in str(n.label)
        )
        assert os_macos.is_expanded
```

- [ ] **Step 2: Run to confirm failure**

Run: `uv run pytest tests/tui/test_inspect_screen.py -v`
Expected: FAIL (no `#tasks-tree` yet).

- [ ] **Step 3: Implement the Tasks pane**

Update `src/ansible_aom/tui/screens/inspect.py`:

(a) Add the import:
```python
from textual.widgets import DataTable, Footer, Header, Tree
from ansible_aom.core.inspect_model import (
    StatusCounts,
    TaskTreeNode,
    build_run_summary,
    build_task_tree,
)
```

(b) Adjust `compose`:
```python
    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield DataTable(id="runs-table", cursor_type="row")
            yield Tree("Tasks", id="tasks-tree")
        yield Footer()
```

(c) Add helpers and wiring:
```python
    def on_mount(self) -> None:
        table = self.query_one("#runs-table", DataTable)
        table.add_columns("Date", "Playbook", "Dur", "")
        tree = self.query_one("#tasks-tree", Tree)
        tree.show_root = False
        self._reload_runs()
        if self.initial_session_id:
            self._select_session(self.initial_session_id)
        if self.selected_session_id:
            self._load_tasks_for(self.selected_session_id)

    def _stats_label(self, stats: StatusCounts) -> str:
        parts = []
        if stats.ok:
            parts.append(f"{stats.ok}✓")
        if stats.changed:
            parts.append(f"{stats.changed}◆")
        if stats.failed:
            parts.append(f"{stats.failed}✖")
        if stats.unreachable:
            parts.append(f"{stats.unreachable}⊝")
        if stats.skipped:
            parts.append(f"{stats.skipped}○")
        return " ".join(parts)

    def _load_tasks_for(self, session_id: str) -> None:
        session = load_session(session_id, self.state_dir)
        if session is None:
            return
        tree_widget = self.query_one("#tasks-tree", Tree)
        tree_widget.clear()
        model = build_task_tree(session)
        for play in model.children:
            self._add_node(tree_widget.root, play, depth=0)

    def _should_auto_expand(self, node: TaskTreeNode, depth: int) -> bool:
        if depth == 0:
            return True  # plays always expanded
        return node.stats.failed > 0 or node.stats.unreachable > 0

    def _add_node(self, parent, node: TaskTreeNode, *, depth: int) -> None:
        label = f"{node.label}  {self._stats_label(node.stats)}".strip()
        is_leaf = not node.children
        if is_leaf:
            parent.add_leaf(label, data=node)
            return
        sub = parent.add(label, data=node)
        if self._should_auto_expand(node, depth):
            sub.expand()
        for child in node.children:
            self._add_node(sub, child, depth=depth + 1)

    def on_data_table_row_highlighted(self, event) -> None:
        sid = event.row_key.value if hasattr(event.row_key, "value") else event.row_key
        if sid and sid != self.selected_session_id:
            self.selected_session_id = sid
            self._load_tasks_for(sid)
```

- [ ] **Step 4: Run the tests**

Run: `uv run pytest tests/tui/test_inspect_screen.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/ansible_aom/tui/screens/inspect.py tests/tui/test_inspect_screen.py
git commit -m "feat(inspect-tui): Tasks pane with auto-expand on failure"
```

---

## Task 13: TUI screen — Detail pane (right) + R/y bindings

**Files:**
- Modify: `src/ansible_aom/tui/screens/inspect.py`
- Modify: `tests/tui/test_inspect_screen.py`

- [ ] **Step 1: Write failing Pilot test for the Detail pane**

Append to `tests/tui/test_inspect_screen.py`:
```python
@pytest.mark.asyncio
async def test_detail_pane_shows_failure_msg(state_dir: Path):
    from ansible_aom.tui.screens.inspect import InspectApp
    app = InspectApp(state_dir=state_dir)
    async with app.run_test() as pilot:
        await pilot.pause()
        # Move focus to tasks tree and navigate to the failed task.
        await pilot.press("tab")  # focus tree
        await pilot.pause()
        # Just check the detail content reflects something from failed_loop.
        detail = app.query_one("#detail-pane")
        # Initially the detail pane should show something; we verify the
        # failed task selection produces the expected msg.
        app.action_show_first_failure()
        await pilot.pause()
        body = detail.renderable.plain if hasattr(detail.renderable, "plain") else str(detail.renderable)
        assert "Install brew casks" in body or "One or more items failed" in body


@pytest.mark.asyncio
async def test_r_copies_rerun_command(state_dir: Path, monkeypatch):
    from ansible_aom.tui.screens.inspect import InspectApp
    copied: list[str] = []
    monkeypatch.setattr(
        "ansible_aom.tui.screens.inspect._copy_to_clipboard",
        lambda text: copied.append(text),
    )
    app = InspectApp(state_dir=state_dir)
    async with app.run_test() as pilot:
        await pilot.pause()
        app.action_show_first_failure()
        await pilot.pause()
        await pilot.press("R")
        await pilot.pause()
    assert copied, "Expected R to copy a rerun command"
    assert "aom rerun" in copied[0] or "--limit" in copied[0]
```

- [ ] **Step 2: Run to confirm failure**

Run: `uv run pytest tests/tui/test_inspect_screen.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement the Detail pane and clipboard glue**

Update `src/ansible_aom/tui/screens/inspect.py`:

(a) Add imports:
```python
from textual.widgets import DataTable, Footer, Header, Static, Tree
from ansible_aom.core.inspect_model import (
    DetailBlock,
    StatusCounts,
    TaskTreeNode,
    build_detail_block,
    build_run_summary,
    build_task_tree,
)
```

(b) Add the clipboard helper at module level:
```python
def _copy_to_clipboard(text: str) -> None:
    """Best-effort clipboard copy: try pyperclip, then OSC52, then no-op.

    The TUI runs in any terminal — including over SSH where there is no
    local clipboard daemon. OSC52 is the lowest-common-denominator
    fallback that most modern terminal emulators (kitty, iTerm,
    Alacritty, recent xterm, recent tmux) support.
    """
    try:
        import pyperclip  # type: ignore[import-not-found]
        pyperclip.copy(text)
        return
    except Exception:
        pass
    import base64
    import sys
    encoded = base64.b64encode(text.encode("utf-8")).decode("ascii")
    sys.stdout.write(f"\033]52;c;{encoded}\a")
    sys.stdout.flush()
```

(c) Extend `BINDINGS`:
```python
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("f", "toggle_failed", "Failed-only"),
        Binding("g", "show_first_failure", "Goto failure"),
        Binding("R", "copy_rerun", "Copy rerun cmd"),
        Binding("y", "yank_detail", "Yank detail"),
    ]
```

(d) Extend `compose`:
```python
    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield DataTable(id="runs-table", cursor_type="row")
            yield Tree("Tasks", id="tasks-tree")
            yield Static("", id="detail-pane", expand=True)
        yield Footer()
```

(e) Add detail-pane state and rendering:
```python
    def __init__(self, *, state_dir: Path, initial_session_id: str | None = None) -> None:
        super().__init__()
        self.state_dir = state_dir
        self.initial_session_id = initial_session_id
        self.selected_session_id: str | None = None
        self._all_summaries: list = []
        self._failed_only = False
        self._current_session: dict | None = None
        self._current_tree: TaskTreeNode | None = None
        self._focused_task: TaskTreeNode | None = None
        self._focused_host: TaskTreeNode | None = None

    def _load_tasks_for(self, session_id: str) -> None:
        session = load_session(session_id, self.state_dir)
        if session is None:
            return
        self._current_session = session
        tree_widget = self.query_one("#tasks-tree", Tree)
        tree_widget.clear()
        model = build_task_tree(session)
        self._current_tree = model
        for play in model.children:
            self._add_node(tree_widget.root, play, depth=0)
        # Auto-jump to first failure for the detail pane.
        self.action_show_first_failure()

    def _iter_failures(self, node: TaskTreeNode):
        if node.kind == "task":
            for child in node.children:
                if child.kind == "host" and (
                    child.stats.failed or child.stats.unreachable
                ):
                    yield node, child
        else:
            for child in node.children:
                yield from self._iter_failures(child)

    def _render_detail_block(self, block: DetailBlock) -> str:
        lines: list[str] = []
        lines.append(f"TASK   {block.task_name}")
        if block.file_line:
            lines.append(f"FILE   {block.file_line}")
        if block.host:
            lines.append(f"HOST   {block.host}")
        if block.duration is not None:
            lines.append(f"TIME   {_fmt_duration_short(block.duration.total_seconds())}")
        lines.append(f"STATUS {block.status}")
        lines.append("─" * 40)
        if block.msg:
            lines.append(f"msg: {block.msg}")
            lines.append("")
        if block.failed_items:
            lines.append(
                f"Failed items ({len(block.failed_items)} of "
                f"{len(block.failed_items) + len(block.ok_items)}):"
            )
            for item in block.failed_items:
                lines.append(f"  ✖ {item.label}")
                if item.msg:
                    lines.append(f"      {item.msg}")
                if item.stderr:
                    lines.append(f"      stderr: {item.stderr}")
            if block.ok_items:
                lines.append(f"  ({len(block.ok_items)} ok items)")
            lines.append("")
        if block.module_stderr and not block.failed_items:
            lines.append("stderr:")
            for line in block.module_stderr.splitlines():
                lines.append(f"  {line}")
            lines.append("")
        if block.session_stderr_tail:
            lines.append("─ stderr.log (tail) ─")
            lines.extend(block.session_stderr_tail)
        return "\n".join(lines)

    def _update_detail(self) -> None:
        detail = self.query_one("#detail-pane", Static)
        if (
            self._current_session is None
            or self._focused_task is None
        ):
            detail.update("Select a task to see details.")
            return
        block = build_detail_block(
            self._current_session, self._focused_task, self._focused_host
        )
        detail.update(self._render_detail_block(block))

    def action_show_first_failure(self) -> None:
        if self._current_tree is None:
            return
        pairs = list(self._iter_failures(self._current_tree))
        if not pairs:
            self._focused_task = None
            self._focused_host = None
        else:
            self._focused_task, self._focused_host = pairs[0]
        self._update_detail()

    def _build_rerun_command(self) -> str:
        session = self._current_session or {}
        host = self._focused_host.label if self._focused_host else ""
        task = self._focused_task.label if self._focused_task else ""
        args = session.get("ansible_args") or []
        ansible_args = " ".join(args)
        parts = ["aom rerun"]
        if ansible_args:
            parts.append(ansible_args)
        if host:
            parts.append(f"--limit '{host}'")
        if task:
            parts.append(f"--start-at-task '{task}'")
        return " ".join(parts)

    def action_copy_rerun(self) -> None:
        cmd = self._build_rerun_command()
        _copy_to_clipboard(cmd)
        self.notify(f"Copied: {cmd[:60]}…" if len(cmd) > 60 else f"Copied: {cmd}")

    def action_yank_detail(self) -> None:
        detail = self.query_one("#detail-pane", Static)
        text = str(detail.renderable)
        _copy_to_clipboard(text)
        self.notify("Detail yanked to clipboard")

    def on_tree_node_highlighted(self, event) -> None:
        node = event.node.data
        if node is None or not isinstance(node, TaskTreeNode):
            return
        if node.kind == "host":
            # parent is the task node (its widget data)
            self._focused_host = node
            parent_widget = event.node.parent
            if parent_widget is not None and isinstance(parent_widget.data, TaskTreeNode):
                self._focused_task = parent_widget.data
        elif node.kind == "task":
            self._focused_task = node
            self._focused_host = node.children[0] if node.children else None
        else:
            self._focused_task = None
            self._focused_host = None
        self._update_detail()
```

- [ ] **Step 4: Run the Pilot tests**

Run: `uv run pytest tests/tui/test_inspect_screen.py -v`
Expected: PASS.

- [ ] **Step 5: Run the full suite**

Run: `uv run pytest tests/ -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/ansible_aom/tui/screens/inspect.py tests/tui/test_inspect_screen.py
git commit -m "feat(inspect-tui): Detail pane with failure-first body + R/y"
```

---

## Task 14: Manual smoke test + suite green

**Files:** None modified directly; only verification.

- [ ] **Step 1: Confirm `aom inspect --text` works against your real state dir**

```bash
uv run aom inspect --text 2>&1 | head -40
```

Expected: text-mode dump of your most recent session. If empty, your test-leakage fix from Task 10 just hid all the old test runs (correct behaviour); run a real `aom <playbook>` first or copy a fixture in.

- [ ] **Step 2: Smoke-test the TUI launches (interactive — visual check)**

Run:
```bash
uv run aom inspect
```

Verify three panes render, q quits cleanly. (No automated test; this is the human smoke test.)

- [ ] **Step 3: Run the full pytest suite**

Run:
```bash
uv run pytest tests/ -q
```

Expected: every test PASS.

- [ ] **Step 4: Run ruff + mypy**

Run:
```bash
uv run ruff format
uv run ruff check --fix src/ansible_aom tests
uv run mypy src/ansible_aom
```

Fix any reported issues. mypy on `tui/screens/inspect.py` is relaxed (see `pyproject.toml`) so Textual metaclass complaints should not block.

- [ ] **Step 5: Final commit if cleanups were needed**

```bash
git add -A
git diff --cached --quiet || git commit -m "chore(inspect): format + lint sweep"
```

- [ ] **Step 6: Push the branch**

(Only if the user explicitly asks; this plan does not auto-push.)

---

## Plan self-review notes

- **Spec coverage:** every spec section has a task — CLI surface (Task 8), TUI layout three panes (Tasks 11/12/13), text mode (Task 7), runner session-ID footer (Task 9), test-leakage fix (Task 10), data model (Tasks 2-5), `find_latest_session` (Task 6), fixtures (Task 1).
- **Removed surface:** `inspect list` / `show` / `diff` removed in Task 8; `inspect/diff.py` deleted there.
- **No placeholders:** every step has either a code block or an exact command + expected output.
- **Type consistency:** `StatusCounts` field names used identically across `build_run_summary`, `build_task_tree`, `build_detail_block`, the renderer, and the screen. `TaskTreeNode` fields (`kind`, `label`, `stats`, `per_host`, `children`, `path`, `duration`, `raw_event`, `task_id`) defined in Task 4 and referenced from Tasks 5, 7, 12, 13 — names verified to match.
- **TDD adherence:** every task starts with "write the failing test" and ends with a commit after the test passes.
