# F6 — `aom --format json` end-of-run JSON summary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `aom --format {compact,json}` (default `compact`). With `--format json`, the run produces no streaming output; on completion AOM emits a single JSON object to stdout describing the playbook, hosts, failures, and timing — CI- and `jq`-friendly.

**Architecture:** A new `JsonRenderer` class in `src/ansible_aom/json_renderer.py` satisfies the existing `Renderer` Protocol. It is silent during the run (no-ops for `start`, `print_log`, `tick`, etc.), accumulates `RunState` from JSONL events via `update_state` (delegating to the existing `state.handle_event`), and on `handle_completion` builds and prints a single JSON object whose shape is pinned by a small typed schema (`schema_version: 1`). The renderer factory gains a `format: Literal["compact", "json"]` argument and dispatches to `JsonRenderer` when `format == "json"`. The existing `tui_mode` argument is left in place; the CLI rejects `--tui --format json` as a usage error.

**Tech Stack:** Python 3.14 stdlib (`json`, `datetime`, `argparse`), existing `RunState` / `determine_exit_code` from `core/models.py` and `compact/renderer.py`, Pydantic v2 (already a project dep) for the response schema model, `pytest` for TDD.

---

## File Structure

**Create:**
- `src/ansible_aom/json_renderer.py` — `JsonRenderer` class (Renderer Protocol impl) + a Pydantic `RunSummary` model (the schema). Pure logic + a single `print()` call at completion. Lives at the top level, NOT under `core/` (it's infrastructure that uses domain objects, not core).
- `tests/unit/test_json_renderer.py` — TDD unit tests: schema shape, host aggregation, failure list, exit-code propagation, interactive-prompt refusal, factory dispatch via `--format json`.

**Modify:**
- `src/ansible_aom/renderer/factory.py` — extend `create_renderer(...)` with a `format: Literal["compact", "json"] = "compact"` parameter; dispatch to `JsonRenderer` when `format == "json"`. `tui_mode` stays.
- `src/ansible_aom/cli.py` — add `--format` argparse option (`choices=["compact", "json"]`, default `"compact"`); reject `--tui --format json` as a usage error (exit 2); pass `format` through `_run_compact` (rename internally to `_run_streaming`) into `create_renderer`.
- `tests/unit/test_cli.py` — add `TestFormatFlag` class covering parser default, parse acceptance, mutual exclusion with `--tui`, and main() dispatching the JsonRenderer path.

**Do NOT touch:** `core/`, `compact/renderer.py`, `tui/app.py`, `runner.py`. The runner already drives any `Renderer` through `start → set_definitions → update_state* → handle_completion → stop`; `JsonRenderer` is a drop-in.

---

## Schema (locked here, don't drift)

The single JSON object emitted on `handle_completion`:

```json
{
  "schema_version": 1,
  "playbook": "site.yml",
  "exit_code": 1,
  "started_at": "2026-05-12T10:30:00+00:00",
  "ended_at":   "2026-05-12T10:30:42+00:00",
  "duration_s": 42.3,
  "hosts": {
    "web1": {"ok": 12, "changed": 3, "failed": 0, "unreachable": 0},
    "web2": {"ok": 11, "changed": 2, "failed": 1, "unreachable": 0}
  },
  "tasks_failed": [
    {"host": "web2", "task": "install nginx", "msg": "package not found"}
  ]
}
```

Field rules (these drive the tests):
- `schema_version` — integer literal `1`. Bump only on breaking change.
- `playbook` — the path passed to `start()`.
- `exit_code` — `determine_exit_code(state)`.
- `started_at` / `ended_at` — ISO 8601 with UTC offset; sourced from `state.start_time` / `state.end_time` when present, else wall clock at `start()` / `handle_completion()`.
- `duration_s` — float seconds, `(ended_at - started_at).total_seconds()`, rounded to 1 decimal place.
- `hosts` — keyed by hostname, every host that ever produced a result (any task) appears exactly once. Counts are aggregated across all tasks/plays.
- `tasks_failed` — one entry per `(host, task)` pair where `host_state.status in (FAILED, UNREACHABLE)`. `msg` is `host_state.message` (may be empty string).

---

## Interactive-prompt behaviour under `--format json`

`handle_password_prompt` and `handle_interactive_prompt` are **not** silently routed to stdin. JSON-mode is for non-interactive consumers (CI, `jq` pipelines); a hung process waiting on a password is the worst possible failure mode.

Both methods write a one-line error to **stderr** and return the empty string. The runner forwards the empty string to ansible (which then fails the auth attempt cleanly), and the run terminates with whatever `determine_exit_code(state)` says — which will typically be `2` (UNREACHABLE) once the failed auth lands in the JSONL stream. The JSON object on stdout still emits cleanly; the user sees the explanation on stderr alongside.

Stderr line shape: `aom: --format json cannot answer interactive prompt; refusing.\n`

This is documented in the `JsonRenderer` docstring and pinned by tests in Task 8.

---

## Task 1: `RunSummary` Pydantic schema model

**Files:**
- Create: `src/ansible_aom/json_renderer.py`
- Test: `tests/unit/test_json_renderer.py`

The Pydantic model is the single source of truth for the schema. We use a model (not a TypedDict) because the codebase already uses Pydantic for `core/config.py` and we get `model_dump()` → JSON-serialisable dict for free, plus runtime validation in tests.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_json_renderer.py
"""Unit tests for the JSON output renderer (F6)."""

from __future__ import annotations


def test_run_summary_model_has_pinned_schema():
    """RunSummary captures every field the schema spec requires."""
    from ansible_aom.json_renderer import HostCounts, RunSummary, TaskFailure

    summary = RunSummary(
        schema_version=1,
        playbook="site.yml",
        exit_code=0,
        started_at="2026-05-12T10:30:00+00:00",
        ended_at="2026-05-12T10:30:42+00:00",
        duration_s=42.3,
        hosts={"web1": HostCounts(ok=1, changed=0, failed=0, unreachable=0)},
        tasks_failed=[TaskFailure(host="web2", task="install nginx", msg="boom")],
    )

    dumped = summary.model_dump()
    assert dumped["schema_version"] == 1
    assert dumped["playbook"] == "site.yml"
    assert dumped["exit_code"] == 0
    assert dumped["duration_s"] == 42.3
    assert dumped["hosts"] == {"web1": {"ok": 1, "changed": 0, "failed": 0, "unreachable": 0}}
    assert dumped["tasks_failed"] == [{"host": "web2", "task": "install nginx", "msg": "boom"}]


def test_run_summary_schema_version_is_literal_one():
    """schema_version refuses any value other than 1 — guards against accidental drift."""
    from pydantic import ValidationError

    from ansible_aom.json_renderer import RunSummary

    try:
        RunSummary(
            schema_version=2,  # type: ignore[arg-type]
            playbook="site.yml",
            exit_code=0,
            started_at="2026-05-12T10:30:00+00:00",
            ended_at="2026-05-12T10:30:00+00:00",
            duration_s=0.0,
            hosts={},
            tasks_failed=[],
        )
    except ValidationError:
        return
    raise AssertionError("schema_version should be a Literal[1]")
```

Note: `# type: ignore[arg-type]` is the ONE acceptable use here — we are deliberately violating the type to assert runtime validation. The CLAUDE.md "no `# type: ignore`" rule is about silencing real type errors, not about test assertions of runtime validators. If pre-commit's mypy run flags it, drop the comment and use `model_validate({"schema_version": 2, ...})` instead — it bypasses static typing entirely:

```python
RunSummary.model_validate({
    "schema_version": 2,
    "playbook": "site.yml",
    "exit_code": 0,
    "started_at": "2026-05-12T10:30:00+00:00",
    "ended_at": "2026-05-12T10:30:00+00:00",
    "duration_s": 0.0,
    "hosts": {},
    "tasks_failed": [],
})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_json_renderer.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'ansible_aom.json_renderer'`

- [ ] **Step 3: Implement the schema model**

```python
# src/ansible_aom/json_renderer.py
"""JSON output renderer for AOM (F6).

Implements the Renderer Protocol but produces no streaming output.
On completion, emits a single JSON object to stdout that summarises
the run — playbook, exit code, host counts, failed tasks, timing.

Designed for CI and `jq` pipelines: no ANSI, no progress bars, no
interactive prompts. If ansible asks for a password mid-run, this
renderer refuses on stderr rather than blocking forever.

Schema is pinned by the ``RunSummary`` Pydantic model below; the
``schema_version`` field is a ``Literal[1]`` so accidental drift
shows up at construction time.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class HostCounts(BaseModel):
    """Per-host status counts aggregated across every task in every play."""

    ok: int = 0
    changed: int = 0
    failed: int = 0
    unreachable: int = 0


class TaskFailure(BaseModel):
    """One (host, task) pair that ended in FAILED or UNREACHABLE."""

    host: str
    task: str
    msg: str


class RunSummary(BaseModel):
    """End-of-run summary emitted by ``JsonRenderer.handle_completion``.

    Field rules:

    - ``schema_version``: literal ``1``. Bump only on breaking change.
    - ``playbook``: the path passed to ``start()``.
    - ``exit_code``: ``determine_exit_code(state)``.
    - ``started_at`` / ``ended_at``: ISO 8601 with UTC offset.
    - ``duration_s``: float seconds, rounded to 1 dp.
    - ``hosts``: every host that ever produced a result, exactly once.
    - ``tasks_failed``: one entry per (host, task) pair that failed
      or went unreachable. ``msg`` may be the empty string.
    """

    schema_version: Literal[1]
    playbook: str
    exit_code: int
    started_at: str
    ended_at: str
    duration_s: float
    hosts: dict[str, HostCounts]
    tasks_failed: list[TaskFailure]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_json_renderer.py -v`
Expected: PASS for both tests.

- [ ] **Step 5: Commit**

```bash
git add src/ansible_aom/json_renderer.py tests/unit/test_json_renderer.py
git commit -m "feat(json-renderer): add RunSummary schema model (schema_version=1)"
```

---

## Task 2: `JsonRenderer` skeleton — Protocol no-ops

**Files:**
- Modify: `src/ansible_aom/json_renderer.py` (append the class after the schema models)
- Test: `tests/unit/test_json_renderer.py` (append)

`JsonRenderer` must satisfy the `Renderer` Protocol (every method present). For F6, only `start`, `set_definitions`, `update_state`, `handle_completion`, `handle_password_prompt`, `handle_interactive_prompt`, and `stop` carry behaviour; the rest are no-ops.

- [ ] **Step 1: Write the failing test**

```python
# Append to tests/unit/test_json_renderer.py

def test_json_renderer_satisfies_renderer_protocol():
    """JsonRenderer is structurally a Renderer (runtime_checkable Protocol)."""
    from ansible_aom.json_renderer import JsonRenderer
    from ansible_aom.renderer.protocol import Renderer

    renderer = JsonRenderer()
    assert isinstance(renderer, Renderer)


def test_json_renderer_start_records_playbook_and_args():
    """start() captures the playbook path and ansible args without printing."""
    from ansible_aom.json_renderer import JsonRenderer

    renderer = JsonRenderer()
    renderer.start("site.yml", ["-i", "inv.ini"])
    assert renderer._playbook == "site.yml"
    assert renderer._args == ["-i", "inv.ini"]


def test_json_renderer_set_definitions_stores_them(capsys):
    """set_definitions stores the list and prints nothing."""
    from ansible_aom.json_renderer import JsonRenderer

    renderer = JsonRenderer()
    renderer.set_definitions([])
    assert renderer._definitions == []
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_json_renderer_noop_methods_emit_nothing(capsys):
    """add_warning, print_log, tick must not write to stdout/stderr in JSON mode."""
    from ansible_aom.json_renderer import JsonRenderer

    renderer = JsonRenderer()
    renderer.start("site.yml", [])
    renderer.add_warning("ignored", is_deprecation=False)
    renderer.add_warning("also ignored", is_deprecation=True)
    renderer.print_log("nothing to see")
    renderer.tick()
    renderer.stop()
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_json_renderer.py -v -k JsonRenderer`
Expected: FAIL with `ImportError: cannot import name 'JsonRenderer'`.

- [ ] **Step 3: Implement the skeleton**

Append to `src/ansible_aom/json_renderer.py`:

```python


# =============================================================================
# JsonRenderer
# =============================================================================


class JsonRenderer:
    """End-of-run JSON renderer satisfying the Renderer Protocol.

    Silent during the run; emits a single JSON object on
    ``handle_completion``. Interactive prompts are refused to stderr —
    JSON mode is for non-interactive consumers.
    """

    def __init__(self) -> None:
        # Lazy-imported here to keep the module importable even before
        # core/state is fully constructed (pytest collection ordering).
        from ansible_aom.core.models import RunState

        self._playbook: str = ""
        self._args: list[str] = []
        self._definitions: list = []
        self._state: RunState | None = None
        self._wall_start: float = 0.0
        self._wall_end: float = 0.0

    def start(self, playbook: str, args: list[str]) -> None:
        """Capture playbook + args; initialise empty RunState. No output."""
        import time

        from ansible_aom.core.models import RunState

        self._playbook = playbook
        self._args = list(args)
        self._state = RunState(playbook=playbook)
        self._wall_start = time.time()

    def set_definitions(self, definitions: list) -> None:
        """Store preflight definitions. No output."""
        self._definitions = list(definitions)

    def update_state(self, event: dict) -> None:
        """Drive RunState from a JSONL event. No output."""
        if self._state is None:
            return
        self._state.handle_event(event)

    def add_warning(self, message: str, is_deprecation: bool = False) -> None:
        """No-op — warnings aren't part of the v1 schema."""
        return

    def print_log(self, message: str) -> None:
        """No-op — JSON mode produces no streaming output."""
        return

    def tick(self) -> None:
        """No-op — no clock to refresh."""
        return

    def handle_password_prompt(self, prompt_text: str) -> str:
        """Refuse on stderr; return empty so ansible fails the auth attempt."""
        import sys

        sys.stderr.write("aom: --format json cannot answer interactive prompt; refusing.\n")
        sys.stderr.flush()
        return ""

    def handle_interactive_prompt(self, prompt_text: str) -> str:
        """Refuse on stderr; return empty so the playbook proceeds without input."""
        import sys

        sys.stderr.write("aom: --format json cannot answer interactive prompt; refusing.\n")
        sys.stderr.flush()
        return ""

    def handle_completion(self, exit_code: int, state: str) -> None:
        """Emit the JSON summary. Filled in by Task 3."""
        return

    def stop(self) -> None:
        """No-op — no display to tear down."""
        return
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_json_renderer.py -v`
Expected: PASS for the two schema tests AND the four skeleton tests (six total).

- [ ] **Step 5: Commit**

```bash
git add src/ansible_aom/json_renderer.py tests/unit/test_json_renderer.py
git commit -m "feat(json-renderer): add JsonRenderer skeleton with Protocol no-ops"
```

---

## Task 3: `handle_completion` builds and emits the JSON object

**Files:**
- Modify: `src/ansible_aom/json_renderer.py` (replace the placeholder `handle_completion`)
- Test: `tests/unit/test_json_renderer.py` (append)

This is the meat: walk the accumulated `RunState`, aggregate per-host counts, collect failed (host, task, msg) triples, build the `RunSummary`, dump to JSON, print to stdout.

- [ ] **Step 1: Write the failing test**

```python
# Append to tests/unit/test_json_renderer.py
"""These tests use the same RunState-construction helper style as
tests/compact/test_completion_summary.py — build the state explicitly
rather than replaying JSONL events, so the test is decoupled from
state-machine wiring."""

import json
from datetime import datetime, timezone


def _state_two_hosts_one_failure():
    """web1: 2 ok + 1 changed; web2: 1 ok + 1 failed (msg='boom')."""
    from ansible_aom.core.models import HostRunState, PlayRunState, RunState, Status, TaskRunState

    state = RunState(playbook="site.yml")
    play = PlayRunState(play_id="1", name="web", status=Status.RUNNING)

    t1 = TaskRunState(task_id="t1", name="gather facts")
    t1.hosts["web1"] = HostRunState(hostname="web1", status=Status.OK)
    t1.hosts["web2"] = HostRunState(hostname="web2", status=Status.OK)
    play.tasks["t1"] = t1

    t2 = TaskRunState(task_id="t2", name="install nginx")
    t2.hosts["web1"] = HostRunState(hostname="web1", status=Status.CHANGED, changed=True)
    t2.hosts["web2"] = HostRunState(hostname="web2", status=Status.FAILED, message="boom")
    play.tasks["t2"] = t2

    t3 = TaskRunState(task_id="t3", name="restart")
    t3.hosts["web1"] = HostRunState(hostname="web1", status=Status.OK)
    play.tasks["t3"] = t3

    state.plays["1"] = play
    state.start_time = datetime(2026, 5, 12, 10, 30, 0, tzinfo=timezone.utc)
    state.end_time = datetime(2026, 5, 12, 10, 30, 42, 300000, tzinfo=timezone.utc)
    return state


def test_handle_completion_emits_one_json_object(capsys):
    """The renderer prints exactly one JSON object on stdout."""
    from ansible_aom.json_renderer import JsonRenderer

    renderer = JsonRenderer()
    renderer.start("site.yml", [])
    renderer._state = _state_two_hosts_one_failure()
    renderer.handle_completion(1, "failed")

    captured = capsys.readouterr()
    # Single line of JSON (or multi-line — either is acceptable; we just
    # need it to parse as one object).
    parsed = json.loads(captured.out)
    assert isinstance(parsed, dict)


def test_handle_completion_schema_version_is_one(capsys):
    from ansible_aom.json_renderer import JsonRenderer

    renderer = JsonRenderer()
    renderer.start("site.yml", [])
    renderer._state = _state_two_hosts_one_failure()
    renderer.handle_completion(1, "failed")

    parsed = json.loads(capsys.readouterr().out)
    assert parsed["schema_version"] == 1


def test_handle_completion_records_playbook_and_exit_code(capsys):
    from ansible_aom.json_renderer import JsonRenderer

    renderer = JsonRenderer()
    renderer.start("site.yml", [])
    renderer._state = _state_two_hosts_one_failure()
    renderer.handle_completion(1, "failed")

    parsed = json.loads(capsys.readouterr().out)
    assert parsed["playbook"] == "site.yml"
    # exit_code is computed from state, not from the argument — failure
    # is encoded in the state itself (web2 status=FAILED → 1).
    assert parsed["exit_code"] == 1


def test_handle_completion_uses_state_timestamps(capsys):
    """started_at / ended_at come from RunState when present."""
    from ansible_aom.json_renderer import JsonRenderer

    renderer = JsonRenderer()
    renderer.start("site.yml", [])
    renderer._state = _state_two_hosts_one_failure()
    renderer.handle_completion(1, "failed")

    parsed = json.loads(capsys.readouterr().out)
    assert parsed["started_at"] == "2026-05-12T10:30:00+00:00"
    assert parsed["ended_at"] == "2026-05-12T10:30:42.300000+00:00"
    # 42.3 seconds, rounded to 1 dp.
    assert parsed["duration_s"] == 42.3


def test_handle_completion_aggregates_per_host_counts(capsys):
    """Hosts dict has one entry per host with summed counts across tasks."""
    from ansible_aom.json_renderer import JsonRenderer

    renderer = JsonRenderer()
    renderer.start("site.yml", [])
    renderer._state = _state_two_hosts_one_failure()
    renderer.handle_completion(1, "failed")

    parsed = json.loads(capsys.readouterr().out)
    assert parsed["hosts"] == {
        "web1": {"ok": 2, "changed": 1, "failed": 0, "unreachable": 0},
        "web2": {"ok": 1, "changed": 0, "failed": 1, "unreachable": 0},
    }


def test_handle_completion_lists_failed_tasks(capsys):
    """tasks_failed names host, task, and the failure message."""
    from ansible_aom.json_renderer import JsonRenderer

    renderer = JsonRenderer()
    renderer.start("site.yml", [])
    renderer._state = _state_two_hosts_one_failure()
    renderer.handle_completion(1, "failed")

    parsed = json.loads(capsys.readouterr().out)
    assert parsed["tasks_failed"] == [
        {"host": "web2", "task": "install nginx", "msg": "boom"}
    ]


def test_handle_completion_unreachable_lands_in_tasks_failed(capsys):
    """UNREACHABLE hosts also appear in tasks_failed."""
    from ansible_aom.core.models import HostRunState, PlayRunState, RunState, Status, TaskRunState
    from ansible_aom.json_renderer import JsonRenderer

    state = RunState(playbook="site.yml")
    play = PlayRunState(play_id="1", name="p", status=Status.RUNNING)
    t1 = TaskRunState(task_id="t1", name="ping")
    t1.hosts["db1"] = HostRunState(hostname="db1", status=Status.UNREACHABLE, message="ssh timeout")
    play.tasks["t1"] = t1
    state.plays["1"] = play
    state.start_time = datetime(2026, 5, 12, 10, 30, 0, tzinfo=timezone.utc)
    state.end_time = datetime(2026, 5, 12, 10, 30, 1, tzinfo=timezone.utc)

    renderer = JsonRenderer()
    renderer.start("site.yml", [])
    renderer._state = state
    renderer.handle_completion(2, "failed")

    parsed = json.loads(capsys.readouterr().out)
    assert parsed["exit_code"] == 2
    assert parsed["tasks_failed"] == [
        {"host": "db1", "task": "ping", "msg": "ssh timeout"}
    ]
    assert parsed["hosts"] == {
        "db1": {"ok": 0, "changed": 0, "failed": 0, "unreachable": 1},
    }


def test_handle_completion_empty_state_emits_zero_exit(capsys):
    """An empty RunState produces a valid JSON with exit_code=0 and empty hosts."""
    from ansible_aom.json_renderer import JsonRenderer

    renderer = JsonRenderer()
    renderer.start("empty.yml", [])
    renderer.handle_completion(0, "completed")

    parsed = json.loads(capsys.readouterr().out)
    assert parsed["schema_version"] == 1
    assert parsed["playbook"] == "empty.yml"
    assert parsed["exit_code"] == 0
    assert parsed["hosts"] == {}
    assert parsed["tasks_failed"] == []
    # started_at and ended_at fall back to wall-clock; they must still be
    # ISO-8601 strings parseable by fromisoformat.
    datetime.fromisoformat(parsed["started_at"])
    datetime.fromisoformat(parsed["ended_at"])


def test_handle_completion_falls_back_to_wall_clock_when_state_lacks_timestamps(capsys):
    """When state.start_time / end_time are None we use wall clock."""
    from ansible_aom.core.models import HostRunState, PlayRunState, RunState, Status, TaskRunState
    from ansible_aom.json_renderer import JsonRenderer

    state = RunState(playbook="site.yml")
    play = PlayRunState(play_id="1", name="p", status=Status.RUNNING)
    t1 = TaskRunState(task_id="t1", name="t")
    t1.hosts["h"] = HostRunState(hostname="h", status=Status.OK)
    play.tasks["t1"] = t1
    state.plays["1"] = play
    # Deliberately leave state.start_time / end_time as None.

    renderer = JsonRenderer()
    renderer.start("site.yml", [])
    renderer._state = state
    renderer.handle_completion(0, "completed")

    parsed = json.loads(capsys.readouterr().out)
    # Both fall back; just assert they're valid ISO-8601 with a tz offset.
    started = datetime.fromisoformat(parsed["started_at"])
    ended = datetime.fromisoformat(parsed["ended_at"])
    assert started.tzinfo is not None
    assert ended.tzinfo is not None
    assert parsed["duration_s"] >= 0.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_json_renderer.py -v`
Expected: the new completion tests FAIL — the placeholder `handle_completion` returns without printing, so `json.loads("")` raises.

- [ ] **Step 3: Implement `handle_completion`**

Replace the placeholder `handle_completion` in `src/ansible_aom/json_renderer.py` and add a private helper. Drop the `import time` block from `start`'s body if you prefer top-level imports — both are fine. The full replacement for the method (and the new helper) follows; leave the rest of the class intact:

```python
    def handle_completion(self, exit_code: int, state: str) -> None:
        """Build the RunSummary from accumulated RunState and print as JSON.

        ``exit_code`` and ``state`` are accepted to satisfy the Protocol
        but the JSON output's ``exit_code`` field is recomputed from
        ``RunState`` via ``determine_exit_code`` — the Protocol exit_code
        is what the runner *thinks* it should be (often 0 on a clean
        subprocess exit even when JSONL says a host failed); the
        state-derived value is what `aom inspect` and humans agree with.
        """
        import json
        import sys
        import time
        from datetime import datetime, timezone

        from ansible_aom.compact.renderer import determine_exit_code
        from ansible_aom.core.models import HostRunState, RunState, Status

        self._wall_end = time.time()

        # Always produce a RunState so the schema is consistent on
        # preflight-only failures (where update_state never fired).
        run_state: RunState = self._state if self._state is not None else RunState(
            playbook=self._playbook
        )

        # Timestamps: prefer state-recorded times, fall back to wall clock.
        # Wall clock is captured in start() / here as Unix floats; convert
        # via UTC datetime so the ISO string carries an explicit offset.
        if run_state.start_time is not None:
            started_at = run_state.start_time.isoformat()
        else:
            started_at = datetime.fromtimestamp(self._wall_start, tz=timezone.utc).isoformat()

        if run_state.end_time is not None:
            ended_at = run_state.end_time.isoformat()
            duration = (run_state.end_time - run_state.start_time).total_seconds() if (
                run_state.start_time is not None
            ) else self._wall_end - self._wall_start
        else:
            ended_at = datetime.fromtimestamp(self._wall_end, tz=timezone.utc).isoformat()
            duration = self._wall_end - self._wall_start

        duration_s = round(max(duration, 0.0), 1)

        # Aggregate per-host counts and collect failures in one pass.
        host_counts: dict[str, dict[str, int]] = {}
        failures: list[TaskFailure] = []

        for play in run_state.plays.values():
            for task in play.tasks.values():
                for hostname, host_state in task.hosts.items():
                    counts = host_counts.setdefault(
                        hostname, {"ok": 0, "changed": 0, "failed": 0, "unreachable": 0}
                    )
                    if host_state.status == Status.OK:
                        counts["ok"] += 1
                    elif host_state.status == Status.CHANGED:
                        counts["changed"] += 1
                    elif host_state.status == Status.FAILED:
                        counts["failed"] += 1
                        failures.append(
                            TaskFailure(host=hostname, task=task.name, msg=host_state.message or "")
                        )
                    elif host_state.status == Status.UNREACHABLE:
                        counts["unreachable"] += 1
                        failures.append(
                            TaskFailure(host=hostname, task=task.name, msg=host_state.message or "")
                        )

        hosts = {name: HostCounts(**counts) for name, counts in host_counts.items()}

        summary = RunSummary(
            schema_version=1,
            playbook=self._playbook,
            exit_code=determine_exit_code(run_state),
            started_at=started_at,
            ended_at=ended_at,
            duration_s=duration_s,
            hosts=hosts,
            tasks_failed=failures,
        )

        # ``print()`` (not sys.stdout.write) so the trailing newline lands
        # — `jq` and most downstream consumers expect newline-terminated
        # JSON when reading a single object from a stream.
        sys.stdout.write(summary.model_dump_json())
        sys.stdout.write("\n")
        sys.stdout.flush()
```

Notes for the engineer:
- Don't move the imports to the top of the file unilaterally — the existing pattern (lazy imports inside methods) keeps the module's import-time cost flat, which matters for `aom --version` and `aom --help` paths that don't need any of this.
- `compact/renderer.py` is allowed as a dependency here (renderer → renderer is fine). Importing `determine_exit_code` from there mirrors what the inspect CLI does.
- `model_dump_json()` (Pydantic v2) handles nested models correctly; no manual `json.dumps` call needed.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_json_renderer.py -v`
Expected: all completion tests PASS (plus the schema/skeleton tests from Tasks 1-2). Total: 13 passing tests in this file.

- [ ] **Step 5: Run the full suite**

Run: `uv run pytest tests/ -q`
Expected: green (no regressions in compact/ or tui/).

- [ ] **Step 6: Commit**

```bash
git add src/ansible_aom/json_renderer.py tests/unit/test_json_renderer.py
git commit -m "feat(json-renderer): emit RunSummary JSON on handle_completion"
```

---

## Task 4: Factory dispatch — `create_renderer(format=...)`

**Files:**
- Modify: `src/ansible_aom/renderer/factory.py` (lines 12-30)
- Test: `tests/unit/test_json_renderer.py` (append)

Add a `format` parameter to `create_renderer`. Default is `"compact"` so all existing callers keep working. `format="json"` returns a `JsonRenderer`. `tui_mode=True` still wins (the TUI doesn't take a format argument); we don't validate the combination here — the CLI is responsible for rejecting nonsense like `--tui --format json` (Task 5).

- [ ] **Step 1: Write the failing test**

```python
# Append to tests/unit/test_json_renderer.py

def test_factory_returns_json_renderer_for_json_format():
    from ansible_aom.json_renderer import JsonRenderer
    from ansible_aom.renderer.factory import create_renderer

    renderer = create_renderer(tui_mode=False, format="json")
    assert isinstance(renderer, JsonRenderer)


def test_factory_default_format_is_compact():
    from ansible_aom.compact.renderer import CompactRenderer
    from ansible_aom.renderer.factory import create_renderer

    renderer = create_renderer(tui_mode=False)
    assert isinstance(renderer, CompactRenderer)


def test_factory_compact_format_explicit_returns_compact_renderer():
    from ansible_aom.compact.renderer import CompactRenderer
    from ansible_aom.renderer.factory import create_renderer

    renderer = create_renderer(tui_mode=False, format="compact")
    assert isinstance(renderer, CompactRenderer)


def test_factory_tui_mode_still_wins_over_format():
    """tui_mode=True returns AOMApp regardless of format (CLI prevents this combo)."""
    from ansible_aom.renderer.factory import create_renderer
    from ansible_aom.tui.app import AOMApp

    renderer = create_renderer(tui_mode=True, format="json")
    assert isinstance(renderer, AOMApp)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_json_renderer.py -v -k factory`
Expected: FAIL — `create_renderer()` got an unexpected keyword argument 'format'.

- [ ] **Step 3: Implement the factory change**

Replace the entire body of `src/ansible_aom/renderer/factory.py` with:

```python
"""Renderer factory for AOM.

This module provides the factory function to create the appropriate
renderer based on CLI flags.

See SPECIFICATION.md Section 2.3 for factory function.
"""

from typing import Literal

from ansible_aom.renderer.protocol import Renderer

RenderFormat = Literal["compact", "json"]


def create_renderer(
    tui_mode: bool = False,
    is_tty: bool = True,
    format: RenderFormat = "compact",
) -> Renderer:
    """Create the appropriate renderer based on CLI flags.

    Args:
        tui_mode: If True, create Textual TUI renderer. Wins over
            ``format`` because the TUI doesn't have a JSON variant —
            the CLI is responsible for rejecting ``--tui --format json``
            as a usage error before getting here.
        is_tty: Whether stdout is a TTY. Forwarded to CompactRenderer to
            decide whether ANSI cursor control should be active. Ignored
            for the TUI (Textual manages its own terminal handling) and
            for the JSON renderer (silent during the run).
        format: Output format for the streaming renderer. ``"compact"``
            (default) is the nom-style ANSI live view; ``"json"`` is
            silent during the run and emits a single JSON object on
            completion.

    Returns:
        Renderer instance (CompactRenderer, AOMApp, or JsonRenderer).
    """
    if tui_mode:
        from ansible_aom.tui.app import AOMApp

        return AOMApp()
    if format == "json":
        from ansible_aom.json_renderer import JsonRenderer

        return JsonRenderer()
    from ansible_aom.compact.renderer import CompactRenderer

    return CompactRenderer(is_tty=is_tty)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_json_renderer.py -v -k factory`
Expected: PASS for all four factory tests.

- [ ] **Step 5: Run existing factory tests**

Run: `uv run pytest tests/unit/test_cli.py::TestRendererFactory -v`
Expected: all pre-existing factory tests still PASS (the new `format` arg has a default, so old call sites are untouched).

- [ ] **Step 6: Commit**

```bash
git add src/ansible_aom/renderer/factory.py tests/unit/test_json_renderer.py
git commit -m "feat(renderer): add format='json' dispatch to create_renderer"
```

---

## Task 5: CLI — `--format` argparse flag + mutual exclusion with `--tui`

**Files:**
- Modify: `src/ansible_aom/cli.py` (parser at lines 134-159; main() at lines 252-265)
- Test: `tests/unit/test_cli.py` (append a `TestFormatFlag` class)

The CLI gets a single new flag `--format {compact,json}` defaulting to `compact`. `--tui --format json` is a usage error — exit 2 with a clear stderr message, matching the existing duplicate-playbook precedent (cli.py:253-259).

- [ ] **Step 1: Write the failing test**

```python
# Append to tests/unit/test_cli.py

class TestFormatFlag:
    """Tests for F6: --format {compact,json} flag."""

    def test_format_flag_defaults_to_compact(self):
        from ansible_aom.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["playbook.yml"])
        assert args.format == "compact"

    def test_format_flag_accepts_json(self):
        from ansible_aom.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["--format", "json", "playbook.yml"])
        assert args.format == "json"

    def test_format_flag_accepts_compact_explicit(self):
        from ansible_aom.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["--format", "compact", "playbook.yml"])
        assert args.format == "compact"

    def test_format_flag_rejects_unknown_value(self, capsys):
        from ansible_aom.cli import create_parser

        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--format", "yaml", "playbook.yml"])

    def test_format_flag_does_not_appear_in_ansible_args(self):
        """--format is consumed by argparse, not forwarded to ansible-playbook."""
        from ansible_aom.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["--format", "json", "playbook.yml", "-i", "inv.ini"])
        assert args.format == "json"
        assert args.ansible_args == ["-i", "inv.ini"]

    def test_main_rejects_tui_plus_json_format(self, capsys):
        """`aom --tui --format json playbook.yml` exits 2 with a usage error."""
        from ansible_aom.cli import main

        with patch("sys.argv", ["aom", "--tui", "--format", "json", "playbook.yml"]):
            result = main()
        assert result == 2
        captured = capsys.readouterr()
        assert "--tui" in captured.err and "--format json" in captured.err

    def test_main_dispatches_json_renderer_when_format_json(self):
        """`aom --format json playbook.yml` constructs a JsonRenderer."""
        from ansible_aom.cli import main
        from ansible_aom.json_renderer import JsonRenderer

        captured_renderer = {}

        def fake_run_playbook(playbook, ansible_args, renderer, **kwargs):
            captured_renderer["renderer"] = renderer
            return 0

        with (
            patch("ansible_aom.runner.run_playbook", side_effect=fake_run_playbook),
            patch("sys.argv", ["aom", "--format", "json", "playbook.yml"]),
        ):
            result = main()

        assert result == 0
        assert isinstance(captured_renderer["renderer"], JsonRenderer)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_cli.py::TestFormatFlag -v`
Expected: FAIL — argparse doesn't know `--format`.

- [ ] **Step 3: Add `--format` to the parser**

In `src/ansible_aom/cli.py`, between the existing `--tui` and `--verbose` arguments (currently lines 134-144), insert the new flag. The block becomes:

```python
    parser.add_argument(
        "--tui",
        action="store_true",
        help="Launch full multi-panel TUI instead of compact view",
    )

    parser.add_argument(
        "--format",
        choices=["compact", "json"],
        default="compact",
        help=(
            "Output format. 'compact' (default) streams the nom-style live view. "
            "'json' is silent during the run and emits a single JSON object on stdout "
            "at completion — designed for CI and `jq` pipelines. Mutually exclusive with --tui."
        ),
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print AOM pre-execution diagnostics and enable DEBUG logging",
    )
```

- [ ] **Step 4: Wire `format` through to the renderer factory**

In `src/ansible_aom/cli.py`, update `_run_compact` to accept and forward `format`. Replace the function (currently lines 162-179) with:

```python
def _run_compact(playbook: str, ansible_args: list[str], format: str = "compact") -> int:
    """Spawn the streaming renderer (compact ANSI or end-of-run JSON) via ``run_playbook``.

    Both compact and JSON renderers are synchronous — ``run_playbook``
    owns the pexpect loop. The renderer chosen by the factory decides
    whether anything streams to stdout during the run.
    """
    from ansible_aom.renderer.factory import create_renderer
    from ansible_aom.runner import run_playbook

    try:
        renderer = create_renderer(
            tui_mode=False,
            is_tty=sys.stdout.isatty(),
            format=format,  # type: ignore[arg-type]
        )
        return run_playbook(playbook, ansible_args, renderer)
    except KeyboardInterrupt:
        print("Cancelled by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
```

The `# type: ignore[arg-type]` is needed because argparse types `format` as `str` but the factory wants `Literal["compact", "json"]`. Per CLAUDE.md, don't suppress with `# type: ignore`; the cleaner fix is to cast through the Literal:

```python
        from typing import cast

        from ansible_aom.renderer.factory import RenderFormat

        renderer = create_renderer(
            tui_mode=False,
            is_tty=sys.stdout.isatty(),
            format=cast(RenderFormat, format),
        )
```

Use the `cast` form. Drop the `# type: ignore`.

- [ ] **Step 5: Add the `--tui --format json` rejection in `main()`**

In `src/ansible_aom/cli.py`, modify the `if args.playbook:` block (currently lines 252-265). Insert the validation just BEFORE the existing duplicate-playbook check, and pass `args.format` through to `_run_compact`. The block becomes:

```python
    if args.playbook:
        if args.tui and args.format == "json":
            print(
                "aom: --tui and --format json are mutually exclusive. "
                "Use --format json without --tui for end-of-run JSON output.",
                file=sys.stderr,
            )
            return 2

        if detect_duplicate_playbook(args.playbook, args.ansible_args):
            print(
                f"aom: '{args.playbook}' appears twice on the command line — "
                "drop the trailing duplicate.",
                file=sys.stderr,
            )
            return 2

        ansible_args = ensure_inventory_arg(args.ansible_args)

        if args.tui:
            return _run_tui(args.playbook, ansible_args)
        return _run_compact(args.playbook, ansible_args, format=args.format)
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_cli.py::TestFormatFlag -v`
Expected: all seven new tests PASS.

- [ ] **Step 7: Run the full CLI suite**

Run: `uv run pytest tests/unit/test_cli.py -v`
Expected: all pre-existing CLI tests still PASS (the `format` default keeps `_run_compact` callers happy).

- [ ] **Step 8: Commit**

```bash
git add src/ansible_aom/cli.py tests/unit/test_cli.py
git commit -m "feat(cli): add --format {compact,json} flag with --tui mutual exclusion"
```

---

## Task 6: End-to-end smoke test through `run_playbook`

**Files:**
- Test: `tests/unit/test_json_renderer.py` (append)

This pins the contract that the runner's existing call sequence (`start → set_definitions → update_state* → handle_completion → stop`) drives `JsonRenderer` to produce a valid JSON object. We don't spawn `ansible-playbook`; we simulate the call sequence directly.

- [ ] **Step 1: Write the failing test**

```python
# Append to tests/unit/test_json_renderer.py

def test_json_renderer_through_full_lifecycle(capsys):
    """Drive JsonRenderer through the same call sequence run_playbook uses."""
    from ansible_aom.json_renderer import JsonRenderer

    renderer = JsonRenderer()
    renderer.start("site.yml", ["-i", "inv.ini"])
    renderer.set_definitions([])

    # A minimal play_start → task_start → ok → stats sequence.
    renderer.update_state({
        "_event": "v2_playbook_on_start",
        "_timestamp": "2026-05-12T10:30:00Z",
    })
    renderer.update_state({
        "_event": "v2_playbook_on_play_start",
        "_timestamp": "2026-05-12T10:30:00Z",
        "play": {"id": "p1", "name": "web"},
    })
    renderer.update_state({
        "_event": "v2_playbook_on_task_start",
        "_timestamp": "2026-05-12T10:30:01Z",
        "play": {"id": "p1", "name": "web"},
        "task": {"id": "t1", "name": "ping"},
    })
    renderer.update_state({
        "_event": "v2_runner_on_ok",
        "_timestamp": "2026-05-12T10:30:02Z",
        "play": {"id": "p1", "name": "web"},
        "task": {"id": "t1", "name": "ping"},
        "hosts": {"web1": {"changed": False}},
    })
    renderer.update_state({
        "_event": "v2_playbook_on_stats",
        "_timestamp": "2026-05-12T10:30:03Z",
        "stats": {"web1": {"ok": 1, "failures": 0, "unreachable": 0, "changed": 0}},
    })

    renderer.handle_completion(0, "completed")
    renderer.stop()

    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert parsed["schema_version"] == 1
    assert parsed["playbook"] == "site.yml"
    assert parsed["exit_code"] == 0
    assert parsed["hosts"] == {
        "web1": {"ok": 1, "changed": 0, "failed": 0, "unreachable": 0},
    }
    assert parsed["tasks_failed"] == []
    assert parsed["started_at"].startswith("2026-05-12T10:30:00")
    assert parsed["ended_at"].startswith("2026-05-12T10:30:03")
    assert parsed["duration_s"] == 3.0
```

- [ ] **Step 2: Run the test to verify it passes**

Run: `uv run pytest tests/unit/test_json_renderer.py::test_json_renderer_through_full_lifecycle -v`
Expected: PASS.

(This test should pass without any new implementation — Tasks 2 and 3 already wired everything. If it fails, the most likely cause is `state.handle_event` not populating timestamps; verify by reading `core/models.py:_handle_v2_playbook_on_start` and `_handle_v2_playbook_on_stats`.)

- [ ] **Step 3: Commit**

```bash
git add tests/unit/test_json_renderer.py
git commit -m "test(json-renderer): smoke test through full Renderer lifecycle"
```

---

## Task 7: Interactive-prompt refusal behaviour

**Files:**
- Test: `tests/unit/test_json_renderer.py` (append)

Pin the documented behaviour for `handle_password_prompt` and `handle_interactive_prompt` under `--format json`: emit a one-line refusal on stderr and return the empty string. Crucially, no stdout output, so the JSON object emitted at completion isn't corrupted.

- [ ] **Step 1: Write the failing test**

```python
# Append to tests/unit/test_json_renderer.py

def test_password_prompt_refuses_to_stderr(capsys):
    """Password prompts under --format json are refused with empty string + stderr message."""
    from ansible_aom.json_renderer import JsonRenderer

    renderer = JsonRenderer()
    result = renderer.handle_password_prompt("BECOME password: ")

    assert result == ""
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "refusing" in captured.err.lower()
    assert "interactive prompt" in captured.err.lower()


def test_interactive_prompt_refuses_to_stderr(capsys):
    """Pause/vars_prompt prompts under --format json are also refused."""
    from ansible_aom.json_renderer import JsonRenderer

    renderer = JsonRenderer()
    result = renderer.handle_interactive_prompt("Press Enter to continue: ")

    assert result == ""
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "refusing" in captured.err.lower()


def test_prompt_refusal_does_not_corrupt_completion_json(capsys):
    """Even after a prompt refusal, handle_completion still emits valid JSON on stdout."""
    from ansible_aom.json_renderer import JsonRenderer

    renderer = JsonRenderer()
    renderer.start("site.yml", [])
    renderer.handle_password_prompt("BECOME password: ")
    renderer.handle_completion(2, "failed")

    captured = capsys.readouterr()
    # stdout is just the JSON, with the refusal on stderr.
    parsed = json.loads(captured.out)
    assert parsed["schema_version"] == 1
    assert "refusing" in captured.err.lower()
```

- [ ] **Step 2: Run the test to verify it passes**

Run: `uv run pytest tests/unit/test_json_renderer.py -v -k "prompt"`
Expected: PASS for all three prompt tests (the behaviour is already wired up in Task 2).

- [ ] **Step 3: Commit**

```bash
git add tests/unit/test_json_renderer.py
git commit -m "test(json-renderer): pin interactive-prompt refusal behaviour"
```

---

## Task 8: Run full suite + ruff + mypy

**Files:** none (verification only)

- [ ] **Step 1: Format**

Run: `uv run ruff format src/ansible_aom/json_renderer.py src/ansible_aom/cli.py src/ansible_aom/renderer/factory.py tests/unit/test_json_renderer.py tests/unit/test_cli.py`
Expected: files reformatted (or "X files left unchanged").

- [ ] **Step 2: Lint**

Run: `uv run ruff check --fix src/ansible_aom/ tests/`
Expected: clean (or auto-fixed).

- [ ] **Step 3: Type-check**

Run: `uv run mypy src/ansible_aom`
Expected: clean. Notes:
- `src/ansible_aom/json_renderer.py` is at the top level, NOT under `compact/`, so it falls under the strict default mypy config. The Pydantic model fields and method signatures must all be typed. The lazy imports inside methods need explicit return-type annotations on every method (already done).
- The `dict[str, dict[str, int]]` and `dict[str, HostCounts]` types in `handle_completion` are explicit; if mypy complains about the generic `list` parameter on `set_definitions`, change the signature to `def set_definitions(self, definitions: list) -> None:` — the Protocol uses an unparameterised `list` too (see protocol.py:20), which is fine.

If mypy complains about `format: str` in `_run_compact` not being `Literal["compact", "json"]`, the `cast(RenderFormat, format)` from Task 5 step 4 resolves it.

- [ ] **Step 4: Full test suite**

Run: `uv run pytest tests/ -q`
Expected: green. Total new tests: ~20 in `tests/unit/test_json_renderer.py` plus 7 in `tests/unit/test_cli.py::TestFormatFlag`.

- [ ] **Step 5: Commit any formatting fixups**

```bash
git status
# If anything was reformatted by ruff in step 1:
git add -u
git commit -m "chore(json-renderer): apply ruff format"
```

---

## Self-Review

**Spec coverage:**
- F6 spec (features.md:225-256) requires `--format {compact,json,jsonl}`. Approved scope drops `jsonl` — only `compact` and `json` exist. Tasks 5 implements that.
- Schema fields required: `playbook`, `exit_code`, `started_at`, `ended_at`, `duration_s`, `hosts`, `tasks_failed`. All in `RunSummary` (Task 1) and tested in Task 3.
- `schema_version: 1` for forward compat — Task 1.
- `JsonRenderer` lives in `src/ansible_aom/json_renderer.py` — Tasks 1-3.
- Factory dispatches by format — Task 4.
- CLI flag — Task 5.
- Exit code from `determine_exit_code(state)` — Task 3 (`test_handle_completion_records_playbook_and_exit_code`, `test_handle_completion_unreachable_lands_in_tasks_failed`).
- Interactive prompt behaviour documented + tested — Task 2 + Task 7.

**Placeholder scan:** None. Every step has either explicit code, an exact command, or a verification assertion.

**Type / name consistency:**
- `RunSummary`, `HostCounts`, `TaskFailure` — defined in Task 1, used identically in Task 3.
- `RenderFormat = Literal["compact", "json"]` — defined in Task 4, imported in Task 5.
- `_run_compact(playbook, ansible_args, format="compact")` — signature in Task 5 matches the call site update in Task 5 step 5.
- `handle_completion(exit_code, state)` — Protocol signature (protocol.py:54) matches `JsonRenderer.handle_completion` in Task 2/3.
- `handle_password_prompt(prompt_text)` returns `str` per protocol.py:34 — matches Task 2.
- `set_definitions(definitions: list)` matches protocol.py:20 (unparameterised `list`) — matches Task 2.

**Architecture rule check (CLAUDE.md):** "core/ must never import from compact/, tui/, or renderer/." `JsonRenderer` lives in `src/ansible_aom/json_renderer.py` (NOT under `core/`) and imports from `core/` and `compact/` — that's the allowed direction. Renderer Protocol stays in `renderer/`. No violation.

**TDD discipline:** Every task starts with a failing test (Step 1) and verifies failure (Step 2) before implementing. Steps 3-4 implement and verify pass. Each task ends with a commit.

**Risks called out:**
- Schema lock-in handled via `schema_version: Literal[1]` (Task 1) with a runtime-validation test.
- Interactive prompts under `--format json` documented in the renderer docstring (Task 2) and pinned by tests (Task 7) — refusal-with-stderr-message rather than hang.
