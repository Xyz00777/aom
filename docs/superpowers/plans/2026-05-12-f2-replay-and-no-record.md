# F2 Replay + F3 `--no-record` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `aom replay <session-id>` to feed a recorded `events.jsonl` back through the renderer at adjustable speed, and `--no-record` on `aom <playbook>` to opt out of session writing.

**Architecture:** F3 adds a `record: bool` parameter through `cli.main` → `_run_compact` / `_run_tui` → `run_playbook` (skips `_SessionSink` instantiation when `False`) and `AOMApp.__init__` (forwarded to its worker). F2 introduces a new module `src/ansible_aom/replay.py` with a `replay_session(session_dir, session_id, renderer, speed)` function that mirrors the renderer-driving shape of `run_playbook` but reads from disk instead of pexpect; a new `replay` branch in `cli.main` dispatches to it using the existing renderer factory and the same `--tui` / compact selection.

**Tech Stack:** Python 3.14, argparse, the existing `core.session.load_session` loader, the existing `renderer.factory.create_renderer`, `time.sleep` for paced playback, and `datetime.fromisoformat` for `_timestamp` parsing. No new dependencies.

**Replay divergence (call out in user-facing help):**

Replay reproduces only what's in `events.jsonl`. It does **not** reproduce:
- AOM-emitted warnings (`renderer.add_warning(...)` from preflight, R3 disk-disabled, etc.)
- The preflight summary (no `set_definitions` call) — definitions are derived from the event stream (`v2_playbook_on_play_start`, `v2_playbook_on_task_start`).
- Password-prompt log lines.
- stderr lines from `stderr.log`.

This is intentional and documented in the `aom replay --help` epilog.

---

## File Structure

| Path | Responsibility |
|------|----------------|
| `src/ansible_aom/runner.py` (modify) | Add `record: bool = True` parameter to `run_playbook`; skip `_SessionSink` when `False`. |
| `src/ansible_aom/cli.py` (modify) | Add `--no-record` flag; thread `record` through `_run_compact` and `_run_tui`. Add `replay` dispatcher branch (sibling of `inspect`) and a `_run_replay` helper. Update help epilog. |
| `src/ansible_aom/tui/app.py` (modify) | Accept `record: bool = True` in `AOMApp.__init__`; forward to `run_playbook` from `_run_playbook_worker`. |
| `src/ansible_aom/replay.py` (new) | `replay_session(session_dir, session_id, renderer, speed=1.0, sleeper=time.sleep)` — load events, drive renderer at paced speed, handle Ctrl+C as `(130, "crashed")`, end with `meta["status"]`. |
| `tests/unit/test_no_record.py` (new) | F3 unit tests: parser flag, plumbing, runner skips sink. |
| `tests/integration/test_no_record.py` (new) | F3 integration test: `--no-record` produces no session dir. |
| `tests/unit/test_replay.py` (new) | F2 unit tests: pacing math, event ordering, speed=0, speed=2, negative-delta guard, completion routing, Ctrl+C path. |
| `tests/unit/test_cli_replay.py` (new) | F2 CLI tests: `aom replay` argparse, dispatcher, `--compact`/`--tui` factory wiring. |
| `tests/integration/test_replay.py` (new) | F2 integration test: record a fake run, replay it, assert renderer call sequences match. |

---

## Sequencing

1. **F3 first** (Tasks 1–6) — small, no upstream dependencies, lands the `record=False` plumbing the replay-loop integration test will (optionally) lean on.
2. **F2 second** (Tasks 7–18) — module + CLI + integration, building on the now-stable `run_playbook(..., record=False)` signature.

Run `uv run pytest tests/ -q` after each task. Never push with red tests. Conventional commit prefixes throughout. **Do not** add `Co-Authored-By: Claude` (or any non-human author) to commits or PRs.

---

# F3 — `--no-record`

## Task 1: Add `record` parameter to `run_playbook`

**Files:**
- Modify: `src/ansible_aom/runner.py:269-294`
- Test: `tests/unit/test_no_record.py` (new)

- [ ] **Step 1: Write the failing test**

Create `tests/unit/test_no_record.py`:

```python
"""Unit tests for F3 --no-record plumbing."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch


def _fake_ansible_command(events: list[dict], exit_code: int = 0) -> tuple[str, list[str]]:
    payload = json.dumps(events)
    code = (
        "import json, sys; "
        f"events = json.loads({payload!r}); "
        "[sys.stdout.write(json.dumps(e) + '\\n') for e in events]; "
        "sys.stdout.flush(); "
        f"sys.exit({exit_code})"
    )
    return sys.executable, ["-c", code]


class TestRunPlaybookRecordParameter:
    """run_playbook accepts a record=bool kwarg; default is True."""

    def test_record_false_skips_session_directory(self, tmp_path: Path) -> None:
        from ansible_aom.runner import run_playbook

        renderer = MagicMock()
        cmd, args = _fake_ansible_command(
            [{"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:01Z"}],
            exit_code=0,
        )

        with patch("ansible_aom.runner._build_command", return_value=(cmd, args)):
            exit_code = run_playbook(
                "playbook.yml", [], renderer, session_dir=tmp_path, record=False
            )

        assert exit_code == 0
        # No session directory should have been created.
        assert list(tmp_path.iterdir()) == []

    def test_record_true_default_still_writes(self, tmp_path: Path) -> None:
        from ansible_aom.runner import run_playbook

        renderer = MagicMock()
        cmd, args = _fake_ansible_command(
            [{"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:01Z"}],
            exit_code=0,
        )

        with patch("ansible_aom.runner._build_command", return_value=(cmd, args)):
            run_playbook("playbook.yml", [], renderer, session_dir=tmp_path)

        sessions = list(tmp_path.iterdir())
        assert len(sessions) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_no_record.py::TestRunPlaybookRecordParameter -v`
Expected: `test_record_false_skips_session_directory` FAILS — `run_playbook` does not accept `record=` kwarg yet (`TypeError: unexpected keyword argument 'record'`).

- [ ] **Step 3: Implement minimal change in `run_playbook`**

In `src/ansible_aom/runner.py`, change the signature and the sink instantiation. Replace:

```python
def run_playbook(
    playbook: str,
    ansible_args: list[str],
    renderer: Renderer,
    timeout: float = _DEFAULT_TIMEOUT_S,
    session_dir: Path | None = None,
) -> int:
```

with:

```python
def run_playbook(
    playbook: str,
    ansible_args: list[str],
    renderer: Renderer,
    timeout: float = _DEFAULT_TIMEOUT_S,
    session_dir: Path | None = None,
    record: bool = True,
) -> int:
```

And replace:

```python
    sink = _SessionSink(session_dir or _default_session_dir(), playbook, renderer=renderer)
```

with:

```python
    if record:
        sink = _SessionSink(session_dir or _default_session_dir(), playbook, renderer=renderer)
    else:
        sink = _NullSink()
```

Add a tiny class above `_SessionSink` (just before line 47, i.e. before `class _SessionSink`):

```python
class _NullSink:
    """No-op sink used when session recording is disabled (F3 --no-record).

    Has the same shape as ``_SessionSink`` so the runner's hot path is
    branchless once the sink is wired up. Methods accept the same args
    and silently discard them.
    """

    def record_event(self, event: dict) -> None:  # noqa: ARG002
        return None

    def record_stderr(self, line: str) -> None:  # noqa: ARG002
        return None

    def end(self, status: str) -> None:  # noqa: ARG002
        return None
```

Update the docstring of `run_playbook` (line 276+) to mention the new flag — append to the existing recording paragraph:

```python
    """...

    Session recording writes a new directory under ``session_dir`` (or
    the spec default ``~/.local/state/aom/sessions/`` when None) so
    ``aom inspect`` can replay the run. Recording is best-effort —
    disk errors are logged but never abort the run. Pass ``record=False``
    to disable session recording entirely (F3 --no-record).
    """
```

- [ ] **Step 4: Run tests to verify both pass**

Run: `uv run pytest tests/unit/test_no_record.py -v`
Expected: 2 passed.

Run: `uv run pytest tests/ -q`
Expected: full suite green (existing session-recording tests must still pass — `record=True` is the default).

- [ ] **Step 5: Commit**

```bash
git add src/ansible_aom/runner.py tests/unit/test_no_record.py
git commit -m "feat(runner): add record=bool parameter to run_playbook (F3)"
```

---

## Task 2: Add `--no-record` flag to CLI parser

**Files:**
- Modify: `src/ansible_aom/cli.py:134-145` (parser flag definition)
- Test: `tests/unit/test_no_record.py` (extend)

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/test_no_record.py`:

```python
class TestNoRecordParserFlag:
    """`--no-record` is a top-level flag that defaults to False."""

    def test_no_record_flag_parses(self) -> None:
        from ansible_aom.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["--no-record", "playbook.yml"])
        assert args.no_record is True

    def test_no_record_default_false(self) -> None:
        from ansible_aom.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["playbook.yml"])
        assert args.no_record is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_no_record.py::TestNoRecordParserFlag -v`
Expected: FAIL — `--no-record` unknown argument / `args.no_record` does not exist.

- [ ] **Step 3: Add the flag**

In `src/ansible_aom/cli.py`, after the `--verbose` block (around line 145), insert:

```python
    parser.add_argument(
        "--no-record",
        action="store_true",
        dest="no_record",
        help=(
            "Disable session recording for this run. "
            "No directory is written under ~/.local/state/aom/sessions/."
        ),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_no_record.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add src/ansible_aom/cli.py tests/unit/test_no_record.py
git commit -m "feat(cli): add --no-record flag (F3)"
```

---

## Task 3: Thread `record` through `_run_compact`

**Files:**
- Modify: `src/ansible_aom/cli.py:162-179` (`_run_compact`)
- Test: `tests/unit/test_no_record.py` (extend)

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/test_no_record.py`:

```python
class TestNoRecordCompactPlumbing:
    """`aom --no-record playbook.yml` calls run_playbook(..., record=False)."""

    def test_no_record_propagates_to_runner(self) -> None:
        from ansible_aom.cli import main

        with (
            patch("ansible_aom.runner.run_playbook", return_value=0) as mock_run,
            patch("ansible_aom.renderer.factory.create_renderer"),
            patch("sys.argv", ["aom", "--no-record", "playbook.yml"]),
        ):
            assert main() == 0

        # record=False must be in the kwargs.
        _args, kwargs = mock_run.call_args
        assert kwargs.get("record") is False

    def test_default_propagates_record_true(self) -> None:
        from ansible_aom.cli import main

        with (
            patch("ansible_aom.runner.run_playbook", return_value=0) as mock_run,
            patch("ansible_aom.renderer.factory.create_renderer"),
            patch("sys.argv", ["aom", "playbook.yml"]),
        ):
            main()

        _args, kwargs = mock_run.call_args
        # Either explicit True, or absent (default True). Accept both
        # so the source can choose either style.
        assert kwargs.get("record", True) is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_no_record.py::TestNoRecordCompactPlumbing -v`
Expected: `test_no_record_propagates_to_runner` FAILS — `_run_compact` doesn't pass `record` yet.

- [ ] **Step 3: Update `_run_compact` and `main`**

In `src/ansible_aom/cli.py`, change `_run_compact` to:

```python
def _run_compact(playbook: str, ansible_args: list[str], record: bool = True) -> int:
    """Spawn the legacy compact renderer via ``run_playbook``.

    The compact path stays synchronous: ``run_playbook`` owns the
    pexpect loop, the renderer prints to stdout, no Textual involved.
    """
    from ansible_aom.renderer.factory import create_renderer
    from ansible_aom.runner import run_playbook

    try:
        renderer = create_renderer(tui_mode=False, is_tty=sys.stdout.isatty())
        return run_playbook(playbook, ansible_args, renderer, record=record)
    except KeyboardInterrupt:
        print("Cancelled by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
```

In `main()`, change the dispatch tail (around lines 263-265). Replace:

```python
        if args.tui:
            return _run_tui(args.playbook, ansible_args)
        return _run_compact(args.playbook, ansible_args)
```

with:

```python
        record = not args.no_record
        if args.tui:
            return _run_tui(args.playbook, ansible_args, record=record)
        return _run_compact(args.playbook, ansible_args, record=record)
```

(Task 4 will add the `record` kwarg to `_run_tui`; if your editor flags an unknown kwarg now, just continue — Task 4's failing test will catch it.)

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/unit/test_no_record.py::TestNoRecordCompactPlumbing -v`
Expected: 2 passed.

Run: `uv run pytest tests/unit/test_cli.py -q`
Expected: still green (existing CLI tests don't pass `--no-record`).

- [ ] **Step 5: Commit**

```bash
git add src/ansible_aom/cli.py tests/unit/test_no_record.py
git commit -m "feat(cli): thread --no-record into _run_compact (F3)"
```

---

## Task 4: Thread `record` through `AOMApp` and `_run_tui`

**Files:**
- Modify: `src/ansible_aom/tui/app.py:48-69` (`__init__`), `_run_playbook_worker`
- Modify: `src/ansible_aom/cli.py:182-204` (`_run_tui`)
- Test: `tests/unit/test_no_record.py` (extend)

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/test_no_record.py`:

```python
class TestNoRecordTUIPlumbing:
    """--no-record reaches the TUI worker as record=False."""

    def test_aomapp_accepts_record_kwarg(self) -> None:
        from ansible_aom.tui.app import AOMApp

        app = AOMApp(playbook="x.yml", ansible_args=[], record=False)
        assert app.record is False

    def test_aomapp_default_record_true(self) -> None:
        from ansible_aom.tui.app import AOMApp

        app = AOMApp(playbook="x.yml", ansible_args=[])
        assert app.record is True

    def test_tui_main_propagates_no_record_to_app(self) -> None:
        from ansible_aom.cli import main

        captured: dict[str, object] = {}

        class FakeApp:
            def __init__(self, **kwargs: object) -> None:
                captured.update(kwargs)
                self.exit_code = 0

            def run(self) -> None:
                return None

        with (
            patch("ansible_aom.tui.app.AOMApp", FakeApp),
            patch("sys.argv", ["aom", "--tui", "--no-record", "playbook.yml"]),
        ):
            assert main() == 0

        assert captured.get("record") is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_no_record.py::TestNoRecordTUIPlumbing -v`
Expected: FAILS — `AOMApp` does not accept `record`, `_run_tui` does not forward it.

- [ ] **Step 3: Update `AOMApp`**

In `src/ansible_aom/tui/app.py`, change `__init__` signature and store the flag:

```python
    def __init__(
        self,
        playbook: str | None = None,
        ansible_args: list[str] | None = None,
        session_dir: Path | None = None,
        record: bool = True,
        **kwargs: Any,
    ) -> None:
        """Initialize the AOMApp with optional playbook context.

        Args:
            playbook: Path to the playbook to run when the app mounts.
                When ``None``, the app starts idle (legacy behaviour the
                Renderer-Protocol smoke tests still rely on).
            ansible_args: Extra CLI args to forward to ``ansible-playbook``.
            session_dir: Override for the session recording location.
                ``None`` lets the runner pick the spec default
                ``~/.local/state/aom/sessions/``.
            record: When False, the worker calls ``run_playbook`` with
                ``record=False`` so no session directory is written
                (F3 --no-record).
        """
        super().__init__(**kwargs)
        self._playbook: str | None = playbook
        self._args: list[str] = list(ansible_args) if ansible_args is not None else []
        self._session_dir: Path | None = session_dir
        self._record: bool = record
        self._state: str = "IDLE"
        self._exit_code: int | None = None
        self._final_state: str | None = None
        self._run_state: RunState = RunState(playbook=playbook or "")
        self._warnings_count: int = 0
        self._deprecations_count: int = 0
        self._log_lines: list[str] = []
```

Add a public read-only property next to `playbook` / `ansible_args` (after line 86):

```python
    @property
    def record(self) -> bool:
        return self._record
```

In `_run_playbook_worker` (around line 224-247), update the `run_playbook` call to forward the flag:

```python
            run_playbook(
                self._playbook,
                self._args,
                self,
                session_dir=self._session_dir,
                record=self._record,
            )
```

- [ ] **Step 4: Update `_run_tui`**

In `src/ansible_aom/cli.py`, change `_run_tui`:

```python
def _run_tui(playbook: str, ansible_args: list[str], record: bool = True) -> int:
    """Launch the Textual TUI and let it drive the runner.

    AOMApp owns its own event loop (``app.run()``) and pumps the
    pexpect runner from a worker thread. The exit code is whatever
    ``run_playbook`` returned, reachable on ``app.exit_code`` after
    ``app.run()`` returns. ``None`` (user quit before completion) maps
    to exit 1 — we treat an aborted-by-quit run as non-success without
    pretending to know the playbook's true outcome.
    """
    from ansible_aom.tui.app import AOMApp

    try:
        app = AOMApp(playbook=playbook, ansible_args=ansible_args, record=record)
        app.run()
    except KeyboardInterrupt:
        print("Cancelled by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    exit_code = app.exit_code
    return exit_code if exit_code is not None else 1
```

- [ ] **Step 5: Run tests**

Run: `uv run pytest tests/unit/test_no_record.py -v`
Expected: all 7 passed.

Run: `uv run pytest tests/ -q`
Expected: full suite green.

- [ ] **Step 6: Commit**

```bash
git add src/ansible_aom/tui/app.py src/ansible_aom/cli.py tests/unit/test_no_record.py
git commit -m "feat(tui,cli): forward --no-record into AOMApp worker (F3)"
```

---

## Task 5: Integration test — `--no-record` produces no session dir

**Files:**
- Test: `tests/integration/test_no_record.py` (new)

- [ ] **Step 1: Write the failing test**

Create `tests/integration/test_no_record.py`:

```python
"""Integration test for F3 --no-record at the runner level.

The unit tests cover argparse and CLI plumbing. This test goes one
level lower and calls ``run_playbook(..., record=False)`` directly
against a fake ansible executable to confirm no directory is written
even when ``session_dir`` is provided.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch


def _fake_ansible_command(events: list[dict], exit_code: int = 0) -> tuple[str, list[str]]:
    payload = json.dumps(events)
    code = (
        "import json, sys; "
        f"events = json.loads({payload!r}); "
        "[sys.stdout.write(json.dumps(e) + '\\n') for e in events]; "
        "sys.stdout.flush(); "
        f"sys.exit({exit_code})"
    )
    return sys.executable, ["-c", code]


class TestNoRecordIntegration:
    def test_record_false_writes_no_session_dir(self, tmp_path: Path) -> None:
        from ansible_aom.runner import run_playbook

        renderer = MagicMock()
        cmd, args = _fake_ansible_command(
            [
                {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-08T10:00:00Z"},
                {"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:01Z"},
            ],
            exit_code=0,
        )

        with patch("ansible_aom.runner._build_command", return_value=(cmd, args)):
            exit_code = run_playbook(
                "playbook.yml", [], renderer, session_dir=tmp_path, record=False
            )

        assert exit_code == 0
        assert list(tmp_path.iterdir()) == []
        renderer.handle_completion.assert_called_once_with(0, "completed")

    def test_record_false_does_not_touch_default_state_dir(self, tmp_path: Path) -> None:
        """Even if session_dir is None, record=False must not create the default."""
        from ansible_aom.runner import run_playbook

        renderer = MagicMock()
        cmd, args = _fake_ansible_command(
            [{"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:01Z"}],
            exit_code=0,
        )

        with (
            patch("ansible_aom.runner._build_command", return_value=(cmd, args)),
            patch("ansible_aom.runner.Path.home", return_value=tmp_path),
        ):
            run_playbook("playbook.yml", [], renderer, record=False)

        default_dir = tmp_path / ".local" / "state" / "aom" / "sessions"
        # The default dir must not have been created — record=False
        # bypasses the sink entirely, including the directory creation.
        assert not default_dir.exists()
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `uv run pytest tests/integration/test_no_record.py -v`
Expected: 2 passed (the implementation already exists from Task 1).

- [ ] **Step 3: Commit**

```bash
git add tests/integration/test_no_record.py
git commit -m "test(integration): cover --no-record bypassing sink and default dir (F3)"
```

---

## Task 6: Update CLI help epilog for `--no-record`

**Files:**
- Modify: `src/ansible_aom/cli.py:79-131` (epilog)

- [ ] **Step 1: Add an example and a flag note to the epilog**

In `src/ansible_aom/cli.py`, in the `epilog=` string of `create_parser`, add a line under `Examples:` (just after the `aom inspect prune --days 30` line):

```
  aom --no-record playbook.yml          Run without writing a session directory
```

And replace the `Session recording:` paragraph with:

```
Session recording:
  Every run writes ~/.local/state/aom/sessions/<uuidv7>/ containing
  events.jsonl, stderr.log, and meta.json. Recording is best-effort —
  disk errors are logged but never abort the run. Use `aom inspect`
  to replay past runs; `aom inspect prune` to clean up.
  Pass --no-record to disable session writing for a single invocation
  (debug logs from --verbose are unaffected).
```

- [ ] **Step 2: Verify nothing broke**

Run: `uv run pytest tests/unit/test_cli.py -q`
Expected: green.

Run: `uv run aom --help | head -40`
Expected: see the new example and the updated Session recording paragraph.

- [ ] **Step 3: Commit**

```bash
git add src/ansible_aom/cli.py
git commit -m "docs(cli): document --no-record in help epilog (F3)"
```

---

# F2 — `aom replay <session-id>`

## Task 7: Define `replay_session` skeleton + load-events test

**Files:**
- Create: `src/ansible_aom/replay.py`
- Test: `tests/unit/test_replay.py` (new)

- [ ] **Step 1: Write the failing test**

Create `tests/unit/test_replay.py`:

```python
"""Unit tests for F2 replay_session.

Replay reads `events.jsonl` + `meta.json` from a session directory and
feeds the events into a Renderer at the recorded pace. This test
covers the simplest path: a session with two events; speed=0 (no
sleeps); renderer receives both events in order followed by
handle_completion.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock


def _make_session(
    base: Path,
    session_id: str,
    events: list[dict],
    meta: dict | None = None,
) -> Path:
    """Create a sessions/<id>/ directory with events.jsonl + meta.json."""
    session_path = base / session_id
    session_path.mkdir(parents=True)
    with open(session_path / "events.jsonl", "w") as f:
        for e in events:
            f.write(json.dumps(e) + "\n")
    full_meta = {"playbook": "test.yml", "status": "completed"}
    if meta:
        full_meta.update(meta)
    with open(session_path / "meta.json", "w") as f:
        json.dump(full_meta, f)
    (session_path / "stderr.log").touch()
    return session_path


class TestReplaySessionBasic:
    def test_renderer_receives_each_event_in_order(self, tmp_path: Path) -> None:
        from ansible_aom.replay import replay_session

        events = [
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-08T10:00:00Z"},
            {"_event": "v2_playbook_on_play_start", "_timestamp": "2026-05-08T10:00:00.5Z"},
            {"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:01Z"},
        ]
        _make_session(tmp_path, "abc123", events)

        renderer = MagicMock()
        exit_code = replay_session(
            session_dir=tmp_path,
            session_id="abc123",
            renderer=renderer,
            speed=0,  # as fast as possible
        )

        assert exit_code == 0
        # update_state called once per event, in order.
        assert renderer.update_state.call_count == 3
        seen = [c.args[0]["_event"] for c in renderer.update_state.call_args_list]
        assert seen == [
            "v2_playbook_on_start",
            "v2_playbook_on_play_start",
            "v2_playbook_on_stats",
        ]

    def test_returns_minus_one_when_session_missing(self, tmp_path: Path) -> None:
        from ansible_aom.replay import replay_session

        renderer = MagicMock()
        exit_code = replay_session(
            session_dir=tmp_path,
            session_id="does-not-exist",
            renderer=renderer,
            speed=0,
        )

        # Convention: missing session => non-zero, no renderer activity.
        assert exit_code != 0
        renderer.start.assert_not_called()
        renderer.update_state.assert_not_called()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_replay.py -v`
Expected: FAIL — `ansible_aom.replay` module does not exist.

- [ ] **Step 3: Create `src/ansible_aom/replay.py`**

Write the minimal implementation that satisfies these two tests. We'll layer pacing, completion, and Ctrl+C in subsequent tasks:

```python
"""Replay a recorded AOM session through a Renderer (F2).

Reads ``events.jsonl`` + ``meta.json`` from
``<session_dir>/<session_id>/`` and feeds each event into the
provided renderer at the original ``_timestamp`` cadence (or scaled
by ``speed``). The renderer interface is identical to the one
``runner.run_playbook`` drives, so the replay command can use the
same factory-built CompactRenderer or AOMApp.

Replay deliberately reproduces ONLY what's in ``events.jsonl``. AOM-
emitted artefacts that never made it into the JSONL stream are not
replayed:

* ``renderer.add_warning(...)`` calls (preflight errors, R3
  recording-disabled warning, deprecation surfacing).
* The preflight summary (``set_definitions`` is NOT called — the
  renderer rebuilds its tree from ``v2_playbook_on_play_start`` /
  ``v2_playbook_on_task_start`` events).
* Password-prompt log lines emitted by the runner.
* stderr lines from ``stderr.log``.

Document this in ``aom replay --help`` (see ``cli._run_replay``).
"""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path
from typing import Callable

from ansible_aom.core.session import load_session
from ansible_aom.renderer.protocol import Renderer


def _parse_timestamp(value: object) -> datetime | None:
    """Parse an ISO 8601 ``_timestamp`` field; return None when unparseable."""
    if not isinstance(value, str) or not value:
        return None
    try:
        # Replace trailing Z with +00:00 because fromisoformat (pre-3.11
        # was strict; 3.11+ accepts Z but be explicit anyway).
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def replay_session(
    session_dir: Path,
    session_id: str,
    renderer: Renderer,
    speed: float = 1.0,
    sleeper: Callable[[float], None] = time.sleep,
) -> int:
    """Replay ``session_id`` from ``session_dir`` through ``renderer``.

    Args:
        session_dir: Directory containing per-session subdirectories
            (typically ``~/.local/state/aom/sessions``).
        session_id: The UUIDv7 (or partial / arbitrary name) directory
            under ``session_dir`` to replay.
        renderer: Any object satisfying the ``Renderer`` protocol.
        speed: Playback rate. ``1.0`` = real time. ``2.0`` = twice as
            fast. ``0`` (or any falsy value) = no sleeps; events fire
            back-to-back.
        sleeper: Injectable sleep function for tests. Defaults to
            ``time.sleep``.

    Returns:
        ``0`` on a successful replay, ``1`` when the session can't be
        loaded.
    """
    session = load_session(session_id, session_dir)
    if session is None:
        return 1

    playbook = session.get("playbook", "")
    events = list(session.get("events", []))

    renderer.start(playbook, [])
    try:
        for event in events:
            renderer.update_state(event)
    finally:
        # Final completion derived from meta.json status; default to
        # "completed" when missing. Tasks 9 + 10 will widen this.
        status = str(session.get("status") or "completed")
        renderer.handle_completion(0, status)
        renderer.stop()
    return 0
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/unit/test_replay.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add src/ansible_aom/replay.py tests/unit/test_replay.py
git commit -m "feat(replay): add replay_session skeleton that drives renderer (F2)"
```

---

## Task 8: Pacing — `--speed 0` no sleeps, normal speed scales delta

**Files:**
- Modify: `src/ansible_aom/replay.py`
- Test: `tests/unit/test_replay.py` (extend)

- [ ] **Step 1: Write the failing tests**

Append to `tests/unit/test_replay.py`:

```python
class TestReplaySpeedControl:
    """speed=0 means no sleeps; speed=2 halves them; default 1× honors deltas."""

    def test_speed_zero_makes_no_sleep_calls(self, tmp_path: Path) -> None:
        from ansible_aom.replay import replay_session

        events = [
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-08T10:00:00Z"},
            {"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:30Z"},
        ]
        _make_session(tmp_path, "s1", events)

        sleeps: list[float] = []
        renderer = MagicMock()
        replay_session(
            session_dir=tmp_path,
            session_id="s1",
            renderer=renderer,
            speed=0,
            sleeper=sleeps.append,
        )

        assert sleeps == []

    def test_speed_one_sleeps_real_delta_seconds(self, tmp_path: Path) -> None:
        from ansible_aom.replay import replay_session

        events = [
            {"_event": "a", "_timestamp": "2026-05-08T10:00:00Z"},
            {"_event": "b", "_timestamp": "2026-05-08T10:00:01Z"},
            {"_event": "c", "_timestamp": "2026-05-08T10:00:03Z"},
        ]
        _make_session(tmp_path, "s2", events)

        sleeps: list[float] = []
        renderer = MagicMock()
        replay_session(
            session_dir=tmp_path,
            session_id="s2",
            renderer=renderer,
            speed=1.0,
            sleeper=sleeps.append,
        )

        # Two gaps (1s, 2s) → two sleeps of ~1.0 and ~2.0.
        assert len(sleeps) == 2
        assert sleeps[0] == pytest.approx(1.0, abs=1e-6)
        assert sleeps[1] == pytest.approx(2.0, abs=1e-6)

    def test_speed_two_halves_sleeps(self, tmp_path: Path) -> None:
        from ansible_aom.replay import replay_session

        events = [
            {"_event": "a", "_timestamp": "2026-05-08T10:00:00Z"},
            {"_event": "b", "_timestamp": "2026-05-08T10:00:02Z"},
        ]
        _make_session(tmp_path, "s3", events)

        sleeps: list[float] = []
        renderer = MagicMock()
        replay_session(
            session_dir=tmp_path,
            session_id="s3",
            renderer=renderer,
            speed=2.0,
            sleeper=sleeps.append,
        )

        assert sleeps == [pytest.approx(1.0, abs=1e-6)]
```

Add the `import pytest` at the top of the test file if not already present:

```python
import pytest
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_replay.py::TestReplaySpeedControl -v`
Expected: 3 FAIL — current implementation never sleeps.

- [ ] **Step 3: Wire pacing into `replay_session`**

In `src/ansible_aom/replay.py`, replace the body of the loop in `replay_session` to track previous timestamp and sleep before each subsequent event. The full updated function:

```python
def replay_session(
    session_dir: Path,
    session_id: str,
    renderer: Renderer,
    speed: float = 1.0,
    sleeper: Callable[[float], None] = time.sleep,
) -> int:
    """Replay ``session_id`` from ``session_dir`` through ``renderer``.

    Args:
        session_dir: Directory containing per-session subdirectories
            (typically ``~/.local/state/aom/sessions``).
        session_id: The UUIDv7 (or partial / arbitrary name) directory
            under ``session_dir`` to replay.
        renderer: Any object satisfying the ``Renderer`` protocol.
        speed: Playback rate. ``1.0`` = real time. ``2.0`` = twice as
            fast. ``0`` (or any falsy value) = no sleeps; events fire
            back-to-back.
        sleeper: Injectable sleep function for tests. Defaults to
            ``time.sleep``.

    Returns:
        ``0`` on a successful replay, ``1`` when the session can't be
        loaded.
    """
    session = load_session(session_id, session_dir)
    if session is None:
        return 1

    playbook = session.get("playbook", "")
    events = list(session.get("events", []))

    renderer.start(playbook, [])
    try:
        previous_ts: datetime | None = None
        for event in events:
            current_ts = _parse_timestamp(event.get("_timestamp"))
            if previous_ts is not None and current_ts is not None and speed:
                # Negative deltas can occur in real ansible JSONL when
                # callbacks fire from different threads (R-risk: real
                # streams are not strictly monotonic). Clamp to zero so
                # we never call sleep(-x).
                delta = (current_ts - previous_ts).total_seconds()
                if delta < 0:
                    delta = 0.0
                wait = delta / float(speed)
                if wait > 0:
                    sleeper(wait)
            renderer.update_state(event)
            if current_ts is not None:
                previous_ts = current_ts
    finally:
        status = str(session.get("status") or "completed")
        renderer.handle_completion(0, status)
        renderer.stop()
    return 0
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/unit/test_replay.py -v`
Expected: all 5 passed.

- [ ] **Step 5: Commit**

```bash
git add src/ansible_aom/replay.py tests/unit/test_replay.py
git commit -m "feat(replay): pace events using _timestamp deltas scaled by speed (F2)"
```

---

## Task 9: Negative-delta guard test

**Files:**
- Test: `tests/unit/test_replay.py` (extend)

The implementation already clamps `delta < 0` to zero. Pin the behaviour with an explicit test so a future refactor can't regress it.

- [ ] **Step 1: Write the test**

Append to `tests/unit/test_replay.py`:

```python
class TestReplayNegativeDelta:
    """Real ansible JSONL is not strictly monotonic across threads.

    A delta of -0.5s must not sleep negative time (would crash
    time.sleep) — instead replay treats it as zero.
    """

    def test_out_of_order_timestamps_do_not_sleep_negative(
        self, tmp_path: Path
    ) -> None:
        from ansible_aom.replay import replay_session

        events = [
            {"_event": "a", "_timestamp": "2026-05-08T10:00:01Z"},
            {"_event": "b", "_timestamp": "2026-05-08T10:00:00Z"},  # earlier!
            {"_event": "c", "_timestamp": "2026-05-08T10:00:02Z"},
        ]
        _make_session(tmp_path, "s4", events)

        sleeps: list[float] = []
        renderer = MagicMock()
        exit_code = replay_session(
            session_dir=tmp_path,
            session_id="s4",
            renderer=renderer,
            speed=1.0,
            sleeper=sleeps.append,
        )

        assert exit_code == 0
        # Two transitions:
        #   a -> b: delta = -1s → clamped to 0 → no sleep recorded
        #   b -> c: delta = +2s → 2.0
        # We allow either "no sleep at all when wait==0" or "sleep(0.0)".
        positive_sleeps = [s for s in sleeps if s > 0]
        assert positive_sleeps == [pytest.approx(2.0, abs=1e-6)]
        # And the renderer must still see all three in file order.
        seen = [c.args[0]["_event"] for c in renderer.update_state.call_args_list]
        assert seen == ["a", "b", "c"]
```

- [ ] **Step 2: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_replay.py::TestReplayNegativeDelta -v`
Expected: PASS (clamp behaviour was wired in Task 8).

- [ ] **Step 3: Commit**

```bash
git add tests/unit/test_replay.py
git commit -m "test(replay): pin negative-delta clamp behaviour (F2)"
```

---

## Task 10: `meta.json["status"]` drives completion state

**Files:**
- Test: `tests/unit/test_replay.py` (extend)

- [ ] **Step 1: Write the failing tests**

Append to `tests/unit/test_replay.py`:

```python
class TestReplayCompletionFromMeta:
    """`handle_completion` is called with the meta.json status."""

    def test_status_completed(self, tmp_path: Path) -> None:
        from ansible_aom.replay import replay_session

        _make_session(
            tmp_path,
            "ok",
            [{"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:00Z"}],
            meta={"status": "completed"},
        )

        renderer = MagicMock()
        replay_session(tmp_path, "ok", renderer, speed=0)

        renderer.handle_completion.assert_called_once_with(0, "completed")

    def test_status_failed(self, tmp_path: Path) -> None:
        from ansible_aom.replay import replay_session

        _make_session(
            tmp_path,
            "bad",
            [{"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:00Z"}],
            meta={"status": "failed"},
        )

        renderer = MagicMock()
        replay_session(tmp_path, "bad", renderer, speed=0)

        renderer.handle_completion.assert_called_once_with(0, "failed")

    def test_status_crashed(self, tmp_path: Path) -> None:
        from ansible_aom.replay import replay_session

        _make_session(
            tmp_path,
            "boom",
            [{"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:00Z"}],
            meta={"status": "crashed"},
        )

        renderer = MagicMock()
        replay_session(tmp_path, "boom", renderer, speed=0)

        renderer.handle_completion.assert_called_once_with(0, "crashed")

    def test_missing_status_defaults_to_completed(self, tmp_path: Path) -> None:
        from ansible_aom.replay import replay_session

        # Create a session whose meta.json has no status field at all.
        session_path = tmp_path / "noStatus"
        session_path.mkdir()
        (session_path / "events.jsonl").write_text(
            '{"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:00Z"}\n'
        )
        (session_path / "meta.json").write_text('{"playbook": "x.yml"}')
        (session_path / "stderr.log").touch()

        renderer = MagicMock()
        replay_session(tmp_path, "noStatus", renderer, speed=0)

        renderer.handle_completion.assert_called_once_with(0, "completed")
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_replay.py::TestReplayCompletionFromMeta -v`
Expected: 4 passed (Task 7 already wired `session.get("status") or "completed"`).

- [ ] **Step 3: Commit**

```bash
git add tests/unit/test_replay.py
git commit -m "test(replay): pin meta.status routing into handle_completion (F2)"
```

---

## Task 11: Ctrl+C mid-replay → `(130, "crashed")`

**Files:**
- Modify: `src/ansible_aom/replay.py`
- Test: `tests/unit/test_replay.py` (extend)

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/test_replay.py`:

```python
class TestReplayKeyboardInterrupt:
    """User hits Ctrl+C mid-replay → renderer sees handle_completion(130, 'crashed')."""

    def test_keyboard_interrupt_during_sleep(self, tmp_path: Path) -> None:
        from ansible_aom.replay import replay_session

        events = [
            {"_event": "a", "_timestamp": "2026-05-08T10:00:00Z"},
            {"_event": "b", "_timestamp": "2026-05-08T10:00:01Z"},
            {"_event": "c", "_timestamp": "2026-05-08T10:00:02Z"},
        ]
        _make_session(tmp_path, "kc", events)

        renderer = MagicMock()

        # Sleep raises KeyboardInterrupt the second time it's called
        # (i.e. between events b and c).
        call_count = {"n": 0}

        def fake_sleep(seconds: float) -> None:
            call_count["n"] += 1
            if call_count["n"] >= 2:
                raise KeyboardInterrupt

        exit_code = replay_session(
            session_dir=tmp_path,
            session_id="kc",
            renderer=renderer,
            speed=1.0,
            sleeper=fake_sleep,
        )

        assert exit_code == 130
        renderer.handle_completion.assert_called_once_with(130, "crashed")
        # Renderer should have seen events a and b, not c.
        seen = [c.args[0]["_event"] for c in renderer.update_state.call_args_list]
        assert seen == ["a", "b"]

    def test_keyboard_interrupt_during_update_state(self, tmp_path: Path) -> None:
        from ansible_aom.replay import replay_session

        events = [
            {"_event": "a", "_timestamp": "2026-05-08T10:00:00Z"},
            {"_event": "b", "_timestamp": "2026-05-08T10:00:01Z"},
        ]
        _make_session(tmp_path, "kc2", events)

        renderer = MagicMock()
        renderer.update_state.side_effect = KeyboardInterrupt

        exit_code = replay_session(
            session_dir=tmp_path,
            session_id="kc2",
            renderer=renderer,
            speed=0,
        )

        assert exit_code == 130
        renderer.handle_completion.assert_called_once_with(130, "crashed")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_replay.py::TestReplayKeyboardInterrupt -v`
Expected: FAIL — current code lets `KeyboardInterrupt` propagate without calling `handle_completion(130, "crashed")`.

- [ ] **Step 3: Update `replay_session` to handle KeyboardInterrupt**

In `src/ansible_aom/replay.py`, replace the function body's loop / finally with a structure that intercepts Ctrl+C. The full updated function:

```python
def replay_session(
    session_dir: Path,
    session_id: str,
    renderer: Renderer,
    speed: float = 1.0,
    sleeper: Callable[[float], None] = time.sleep,
) -> int:
    """Replay ``session_id`` from ``session_dir`` through ``renderer``.

    Args:
        session_dir: Directory containing per-session subdirectories
            (typically ``~/.local/state/aom/sessions``).
        session_id: The UUIDv7 (or partial / arbitrary name) directory
            under ``session_dir`` to replay.
        renderer: Any object satisfying the ``Renderer`` protocol.
        speed: Playback rate. ``1.0`` = real time. ``2.0`` = twice as
            fast. ``0`` (or any falsy value) = no sleeps; events fire
            back-to-back.
        sleeper: Injectable sleep function for tests. Defaults to
            ``time.sleep``.

    Returns:
        ``0`` on a successful replay, ``130`` if the user pressed
        Ctrl+C mid-replay (mirrors ``runner.run_playbook``), ``1`` when
        the session can't be loaded.
    """
    session = load_session(session_id, session_dir)
    if session is None:
        return 1

    playbook = session.get("playbook", "")
    events = list(session.get("events", []))

    renderer.start(playbook, [])
    interrupted = False
    try:
        previous_ts: datetime | None = None
        for event in events:
            current_ts = _parse_timestamp(event.get("_timestamp"))
            if previous_ts is not None and current_ts is not None and speed:
                # Negative deltas can occur when ansible callbacks fire
                # from different threads. Clamp to zero so we never call
                # sleep with a negative argument.
                delta = (current_ts - previous_ts).total_seconds()
                if delta < 0:
                    delta = 0.0
                wait = delta / float(speed)
                if wait > 0:
                    sleeper(wait)
            renderer.update_state(event)
            if current_ts is not None:
                previous_ts = current_ts
    except KeyboardInterrupt:
        interrupted = True
    finally:
        if interrupted:
            renderer.handle_completion(130, "crashed")
        else:
            status = str(session.get("status") or "completed")
            renderer.handle_completion(0, status)
        renderer.stop()
    return 130 if interrupted else 0
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/unit/test_replay.py -v`
Expected: all replay tests passed.

- [ ] **Step 5: Commit**

```bash
git add src/ansible_aom/replay.py tests/unit/test_replay.py
git commit -m "feat(replay): treat Ctrl+C as handle_completion(130, crashed) (F2)"
```

---

## Task 12: Add `replay` subcommand dispatch in `cli.main`

**Files:**
- Modify: `src/ansible_aom/cli.py`
- Test: `tests/unit/test_cli_replay.py` (new)

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/test_cli_replay.py`:

```python
"""CLI tests for the F2 `aom replay` subcommand dispatch.

Mirrors the inspect-dispatcher tests in test_cli.py: top-level
``aom replay ...`` strips the ``replay`` token and forwards the rest
to ``ansible_aom.replay`` (or a thin CLI wrapper there).
"""

from __future__ import annotations

from unittest.mock import patch


class TestReplayDispatch:
    def test_replay_dispatches_to_replay_main(self) -> None:
        """`aom replay <id>` invokes the replay CLI entry with ['<id>']."""
        from ansible_aom.cli import main

        with (
            patch("ansible_aom.replay.cli_main", return_value=0) as mock_main,
            patch("sys.argv", ["aom", "replay", "abc123"]),
        ):
            assert main() == 0
            mock_main.assert_called_once_with(["abc123"])

    def test_replay_forwards_speed_flag(self) -> None:
        from ansible_aom.cli import main

        with (
            patch("ansible_aom.replay.cli_main", return_value=0) as mock_main,
            patch("sys.argv", ["aom", "replay", "abc123", "--speed", "5"]),
        ):
            main()
            mock_main.assert_called_once_with(["abc123", "--speed", "5"])

    def test_replay_forwards_renderer_flags(self) -> None:
        from ansible_aom.cli import main

        with (
            patch("ansible_aom.replay.cli_main", return_value=0) as mock_main,
            patch("sys.argv", ["aom", "replay", "abc123", "--tui"]),
        ):
            main()
            mock_main.assert_called_once_with(["abc123", "--tui"])

    def test_replay_propagates_exit_code(self) -> None:
        from ansible_aom.cli import main

        with (
            patch("ansible_aom.replay.cli_main", return_value=2),
            patch("sys.argv", ["aom", "replay", "missing"]),
        ):
            assert main() == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_cli_replay.py -v`
Expected: FAIL — `ansible_aom.replay` has no `cli_main`; `cli.main` doesn't dispatch `replay`.

- [ ] **Step 3: Add `cli_main` stub in `replay.py`**

Append to `src/ansible_aom/replay.py`:

```python
def cli_main(argv: list[str]) -> int:
    """Entry point for the ``aom replay`` subcommand.

    Wired in Task 13 to argparse + factory + ``replay_session``. This
    stub exists so the dispatcher in ``cli.main`` (Task 12) has a
    concrete target.
    """
    raise NotImplementedError("aom replay not yet wired (see plan Task 13)")
```

- [ ] **Step 4: Add the dispatcher branch in `cli.main`**

In `src/ansible_aom/cli.py`, find the `inspect` dispatch block (around lines 231-234):

```python
    if len(sys.argv) > 1 and sys.argv[1] == "inspect":
        from ansible_aom.inspect.cli import main as inspect_main

        return inspect_main(sys.argv[2:])
```

Insert the replay dispatch immediately before it:

```python
    if len(sys.argv) > 1 and sys.argv[1] == "replay":
        from ansible_aom.replay import cli_main as replay_main

        return replay_main(sys.argv[2:])
```

- [ ] **Step 5: Run tests**

Run: `uv run pytest tests/unit/test_cli_replay.py -v`
Expected: 4 passed (the dispatcher just calls the stub, which is mocked in every test).

Run: `uv run pytest tests/ -q`
Expected: full suite green.

- [ ] **Step 6: Commit**

```bash
git add src/ansible_aom/cli.py src/ansible_aom/replay.py tests/unit/test_cli_replay.py
git commit -m "feat(cli): dispatch 'aom replay' to replay.cli_main (F2)"
```

---

## Task 13: Implement `replay.cli_main` with argparse + renderer factory

**Files:**
- Modify: `src/ansible_aom/replay.py`
- Test: `tests/unit/test_cli_replay.py` (extend)

- [ ] **Step 1: Write the failing tests**

Append to `tests/unit/test_cli_replay.py`:

```python
import json
from pathlib import Path


def _make_session(base: Path, session_id: str, events: list[dict]) -> Path:
    p = base / session_id
    p.mkdir(parents=True)
    with open(p / "events.jsonl", "w") as f:
        for e in events:
            f.write(json.dumps(e) + "\n")
    with open(p / "meta.json", "w") as f:
        json.dump({"playbook": "x.yml", "status": "completed"}, f)
    (p / "stderr.log").touch()
    return p


class TestReplayCLIMain:
    """`replay.cli_main` parses argv, builds a renderer, calls replay_session."""

    def test_cli_main_default_uses_compact_renderer(self, tmp_path: Path) -> None:
        from ansible_aom.replay import cli_main

        _make_session(
            tmp_path,
            "abc",
            [{"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:00Z"}],
        )

        captured: dict[str, object] = {}

        def fake_replay(**kwargs: object) -> int:
            captured.update(kwargs)
            return 0

        with (
            patch("ansible_aom.replay.replay_session", side_effect=fake_replay),
            patch("ansible_aom.replay.create_renderer") as mock_factory,
        ):
            mock_factory.return_value = object()
            exit_code = cli_main(["abc", "--state-dir", str(tmp_path)])

        assert exit_code == 0
        # Default = compact renderer (tui_mode=False).
        kw = mock_factory.call_args.kwargs
        assert kw.get("tui_mode") is False

    def test_cli_main_tui_flag_selects_tui_renderer(self, tmp_path: Path) -> None:
        from ansible_aom.replay import cli_main

        _make_session(
            tmp_path,
            "abc",
            [{"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:00Z"}],
        )

        with (
            patch("ansible_aom.replay.replay_session", return_value=0),
            patch("ansible_aom.replay.create_renderer") as mock_factory,
        ):
            mock_factory.return_value = object()
            cli_main(["abc", "--state-dir", str(tmp_path), "--tui"])

        assert mock_factory.call_args.kwargs.get("tui_mode") is True

    def test_cli_main_speed_forwarded(self, tmp_path: Path) -> None:
        from ansible_aom.replay import cli_main

        _make_session(
            tmp_path,
            "abc",
            [{"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:00Z"}],
        )

        captured: dict[str, object] = {}

        def fake_replay(**kwargs: object) -> int:
            captured.update(kwargs)
            return 0

        with (
            patch("ansible_aom.replay.replay_session", side_effect=fake_replay),
            patch("ansible_aom.replay.create_renderer", return_value=object()),
        ):
            cli_main(["abc", "--state-dir", str(tmp_path), "--speed", "10"])

        assert captured.get("speed") == 10.0

    def test_cli_main_speed_zero_allowed(self, tmp_path: Path) -> None:
        """`--speed 0` is the documented "fast as possible" sentinel."""
        from ansible_aom.replay import cli_main

        _make_session(
            tmp_path,
            "abc",
            [{"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:00Z"}],
        )

        captured: dict[str, object] = {}

        def fake_replay(**kwargs: object) -> int:
            captured.update(kwargs)
            return 0

        with (
            patch("ansible_aom.replay.replay_session", side_effect=fake_replay),
            patch("ansible_aom.replay.create_renderer", return_value=object()),
        ):
            cli_main(["abc", "--state-dir", str(tmp_path), "--speed", "0"])

        assert captured.get("speed") == 0.0

    def test_cli_main_returns_1_when_session_missing(self, tmp_path: Path) -> None:
        from ansible_aom.replay import cli_main

        # No session created — replay_session returns 1 (real behaviour).
        with patch("ansible_aom.replay.create_renderer", return_value=object()):
            exit_code = cli_main(["nope", "--state-dir", str(tmp_path)])

        assert exit_code == 1

    def test_compact_and_tui_are_mutually_exclusive(self, tmp_path: Path) -> None:
        """Passing both --compact and --tui exits with usage error (argparse SystemExit)."""
        import pytest

        from ansible_aom.replay import cli_main

        with (
            patch("ansible_aom.replay.replay_session", return_value=0),
            patch("ansible_aom.replay.create_renderer", return_value=object()),
            pytest.raises(SystemExit),
        ):
            cli_main(["abc", "--state-dir", str(tmp_path), "--compact", "--tui"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_cli_replay.py::TestReplayCLIMain -v`
Expected: FAIL — `cli_main` raises NotImplementedError; `create_renderer` is not imported in `replay.py`.

- [ ] **Step 3: Implement `cli_main`**

In `src/ansible_aom/replay.py`, add the `create_renderer` import at the top with the other imports:

```python
import sys

from ansible_aom.renderer.factory import create_renderer
```

Replace the `cli_main` stub with a real implementation:

```python
_REPLAY_HELP_EPILOG = """\
Replay reads <session-id>/events.jsonl and <session-id>/meta.json from
the AOM state directory (default ~/.local/state/aom/sessions) and
feeds the recorded events through the renderer of your choice.

Speed control:
  --speed 1    real time (default)
  --speed 10   ten times faster
  --speed 0    as fast as possible (no sleeps)

  Note: a real 8-hour run replayed at 1× sleeps for 8 hours.
  Use --speed 10 (or higher) — or --speed 0 — for long sessions.

What replay does NOT reproduce:
  * AOM-emitted warnings (preflight, deprecations, R3 disk-disabled).
  * The preflight summary — definitions are rebuilt from
    v2_playbook_on_play_start / v2_playbook_on_task_start events.
  * Password-prompt log lines.
  * stderr lines from stderr.log.

Anything else that appeared in events.jsonl is replayed verbatim.
"""


def cli_main(argv: list[str]) -> int:
    """Entry point for ``aom replay <session-id> [...]``.

    Argparse the supplied tail (``sys.argv[2:]`` from the top-level
    dispatcher), build a renderer via the shared factory, and call
    ``replay_session``. The exit code mirrors ``replay_session``'s:

    * ``0`` — replay finished
    * ``1`` — session not found
    * ``130`` — Ctrl+C mid-replay
    """
    import argparse

    parser = argparse.ArgumentParser(
        prog="aom replay",
        description="Replay a recorded AOM session through the renderer.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=_REPLAY_HELP_EPILOG,
    )
    parser.add_argument("session_id", help="Session ID (UUIDv7 directory name) to replay")
    parser.add_argument(
        "--state-dir",
        type=Path,
        default=Path.home() / ".local" / "state" / "aom" / "sessions",
        help="Directory containing session subdirectories (default: %(default)s)",
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help=(
            "Playback rate. 1.0 = real time, 10 = 10x faster, 0 = no sleeps. "
            "Use a high speed for long sessions."
        ),
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--compact",
        dest="mode",
        action="store_const",
        const="compact",
        help="Use the compact renderer (default)",
    )
    mode.add_argument(
        "--tui",
        dest="mode",
        action="store_const",
        const="tui",
        help="Use the full multi-panel Textual TUI",
    )
    parser.set_defaults(mode="compact")

    args = parser.parse_args(argv)

    tui_mode = args.mode == "tui"
    renderer = create_renderer(tui_mode=tui_mode, is_tty=sys.stdout.isatty())

    return replay_session(
        session_dir=args.state_dir,
        session_id=args.session_id,
        renderer=renderer,
        speed=float(args.speed),
    )
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/unit/test_cli_replay.py -v`
Expected: 10 passed (4 dispatch + 6 cli_main).

Run: `uv run pytest tests/ -q`
Expected: full suite green.

- [ ] **Step 5: Commit**

```bash
git add src/ansible_aom/replay.py tests/unit/test_cli_replay.py
git commit -m "feat(replay): wire cli_main with argparse + renderer factory (F2)"
```

---

## Task 14: Update `aom --help` epilog to mention `replay`

**Files:**
- Modify: `src/ansible_aom/cli.py:79-131` (epilog)

- [ ] **Step 1: Add example lines and a brief Replay paragraph**

In `create_parser`'s `epilog=` string in `src/ansible_aom/cli.py`, add the following two lines under `Examples:` (group them with the inspect lines):

```
  aom replay <session-id>               Replay a recorded session at original pace
  aom replay <session-id> --speed 10    Replay 10x faster
```

And insert a new paragraph block just after the `Session recording:` block:

```
Replay:
  `aom replay <session-id>` re-streams a recorded run's events.jsonl
  through the renderer at the original cadence (or scaled with
  --speed N — use --speed 0 for as-fast-as-possible). Replay does
  not reproduce AOM-emitted warnings, the preflight summary, or
  password-prompt log lines — only what's in the JSONL stream.
```

- [ ] **Step 2: Verify the help text and tests stay green**

Run: `uv run aom --help | grep -E "replay|Replay"`
Expected: see the new examples and the Replay paragraph.

Run: `uv run pytest tests/unit/test_cli.py -q`
Expected: green.

- [ ] **Step 3: Commit**

```bash
git add src/ansible_aom/cli.py
git commit -m "docs(cli): document 'aom replay' in help epilog (F2)"
```

---

## Task 15: Integration test — record → replay round-trip

**Files:**
- Test: `tests/integration/test_replay.py` (new)

- [ ] **Step 1: Write the failing test**

Create `tests/integration/test_replay.py`:

```python
"""Integration test: record a fake run, then replay it.

Drives ``run_playbook`` against a fake ansible executable so a real
session directory is produced on disk, then calls ``replay_session``
and asserts the replayed renderer sees the same event sequence in the
same order.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch


def _fake_ansible_command(events: list[dict], exit_code: int = 0) -> tuple[str, list[str]]:
    payload = json.dumps(events)
    code = (
        "import json, sys; "
        f"events = json.loads({payload!r}); "
        "[sys.stdout.write(json.dumps(e) + '\\n') for e in events]; "
        "sys.stdout.flush(); "
        f"sys.exit({exit_code})"
    )
    return sys.executable, ["-c", code]


class TestRecordThenReplay:
    def test_record_then_replay_produces_same_event_sequence(self, tmp_path: Path) -> None:
        from ansible_aom.replay import replay_session
        from ansible_aom.runner import run_playbook

        events = [
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-08T10:00:00Z"},
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-08T10:00:00.5Z",
                "play": {"id": "p1", "name": "Test"},
            },
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-08T10:00:01Z",
                "task": {"id": "t1", "name": "task one"},
            },
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-05-08T10:00:01.5Z",
                "task": {"id": "t1"},
                "hosts": {"web1": {"ok": True}},
            },
            {
                "_event": "v2_playbook_on_stats",
                "_timestamp": "2026-05-08T10:00:02Z",
                "stats": {"web1": {"ok": 1}},
            },
        ]

        # ----- Record -----
        record_renderer = MagicMock()
        cmd, args = _fake_ansible_command(events, exit_code=0)
        with patch("ansible_aom.runner._build_command", return_value=(cmd, args)):
            exit_code = run_playbook(
                "playbook.yml", [], record_renderer, session_dir=tmp_path
            )
        assert exit_code == 0

        # The runner created exactly one session directory; grab its id.
        session_dirs = list(tmp_path.iterdir())
        assert len(session_dirs) == 1
        session_id = session_dirs[0].name

        # ----- Replay -----
        replay_renderer = MagicMock()
        replay_exit = replay_session(
            session_dir=tmp_path,
            session_id=session_id,
            renderer=replay_renderer,
            speed=0,  # no sleeps in tests
        )
        assert replay_exit == 0

        # Both renderers saw the same _event sequence (ignoring extra
        # callbacks like start/handle_completion which differ between
        # the two paths — we only compare update_state events).
        recorded_seq = [
            c.args[0]["_event"]
            for c in record_renderer.update_state.call_args_list
        ]
        replayed_seq = [
            c.args[0]["_event"]
            for c in replay_renderer.update_state.call_args_list
        ]
        assert recorded_seq == replayed_seq
        assert recorded_seq == [e["_event"] for e in events]

        # Replay's completion uses meta.status ("completed" → 0/"completed").
        replay_renderer.handle_completion.assert_called_once_with(0, "completed")

    def test_replay_uses_meta_status_failed_when_recorded_failed(
        self, tmp_path: Path
    ) -> None:
        """A recorded failure (exit 2) writes meta.status=failed; replay
        forwards that status to handle_completion."""
        from ansible_aom.replay import replay_session
        from ansible_aom.runner import run_playbook

        events = [{"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:00Z"}]
        cmd, args = _fake_ansible_command(events, exit_code=2)

        record_renderer = MagicMock()
        with patch("ansible_aom.runner._build_command", return_value=(cmd, args)):
            run_playbook("playbook.yml", [], record_renderer, session_dir=tmp_path)

        session_id = next(tmp_path.iterdir()).name

        replay_renderer = MagicMock()
        replay_session(tmp_path, session_id, replay_renderer, speed=0)

        replay_renderer.handle_completion.assert_called_once_with(0, "failed")
```

- [ ] **Step 2: Run the integration test**

Run: `uv run pytest tests/integration/test_replay.py -v`
Expected: 2 passed.

- [ ] **Step 3: Commit**

```bash
git add tests/integration/test_replay.py
git commit -m "test(integration): record-then-replay round-trip preserves event sequence (F2)"
```

---

## Task 16: Full-suite verification + lint

**Files:** None (verification only)

- [ ] **Step 1: Format + lint**

Run: `uv run ruff format`
Expected: files reformatted in-place, no errors.

Run: `uv run ruff check --fix`
Expected: no remaining lint errors.

- [ ] **Step 2: Type-check the new module**

Run: `uv run mypy src/ansible_aom/replay.py src/ansible_aom/runner.py src/ansible_aom/cli.py src/ansible_aom/tui/app.py`
Expected: no errors. If `mypy` complains about `Renderer` Protocol in `cli_main`'s `create_renderer` return type, adjust the local annotation but **do not** add `# type: ignore` — instead use the existing module-level mypy override pattern from `pyproject.toml` if necessary.

- [ ] **Step 3: Run full suite**

Run: `uv run pytest tests/ -q`
Expected: green across the board (existing + new tests). If anything red, fix root cause; **do not** push or commit while red.

- [ ] **Step 4: Commit if format/lint changed any files**

```bash
git status
# If any files were reformatted by ruff:
git add -u
git commit -m "chore(replay,no-record): apply ruff format"
```

---

## Self-Review

**Spec coverage:**

| F2/F3 spec line | Implemented in |
|---|---|
| F2 subcommand `aom replay <session-id> [--speed N] [--compact \| --tui]` | Tasks 12, 13 |
| Reads `events.jsonl` + `meta.json` | Task 7 (uses `core.session.load_session`) |
| Default 1× real time using `_timestamp` deltas | Task 8 |
| `--speed 10` = 10× faster | Task 8, 13 |
| `--speed 0` = as-fast-as-possible | Task 8 (`if speed:` guard), 13 (test) |
| `meta.json["status"]` chooses final completion state | Task 7 + Task 10 (tests) |
| New file `src/ansible_aom/replay.py` | Tasks 7–13 |
| Reuses renderer factory | Task 13 |
| Set definitions reconstructed from events | Implicit — replay never calls `set_definitions`; renderers already handle that since they did it pre-Renderer-Protocol-Set-Definitions; documented as a divergence |
| Add to argparse dispatcher (alongside inspect) | Task 12 |
| Help epilog gains a line | Task 14 |
| Unit: 3-event sequence, in order, completion w/ meta status | Tasks 7, 10 |
| Unit: `--speed 0` no sleeps | Task 8 |
| Unit: `--speed 2` halves sleep | Task 8 |
| Integration: record then replay | Task 15 |
| Risk: negative deltas → 0 | Task 8 (impl) + Task 9 (pin test) |
| Risk: long replays → document `--speed` | Task 13 epilog + Task 14 main epilog |
| Ctrl+C mid-replay → handle_completion(130, "crashed") | Task 11 |
| F3 `--no-record` flag in `cli.create_parser` | Task 2 |
| Threaded through to `run_playbook(..., record=True)`; skip sink when False | Task 1 |
| `AOMApp.__init__` gains `record: bool = True`, forwarded to its worker | Task 4 |
| Unit: `aom --no-record site.yml` produces no session dir | Task 5 |
| Unit: default still writes one (existing test unchanged) | Task 1 (`test_record_true_default_still_writes`) + existing `test_runner_session_recording.py` |
| CLI test: `--no-record` propagates through to runner | Task 3 |

**Placeholder scan:** No "TBD"/"similar to" found. Each task has full code blocks. No "implement appropriate validation" placeholders. The replay `cli_main` stub in Task 12 is intentional and replaced in full in Task 13.

**Type / signature consistency:**

- `replay_session(session_dir, session_id, renderer, speed=1.0, sleeper=time.sleep)` — same signature in Tasks 7, 8, 11, and used by `cli_main` via keyword args in Task 13.
- `cli_main(argv: list[str]) -> int` — defined in Task 12, finalised in Task 13, called by `cli.main` in Task 12.
- `run_playbook(..., record: bool = True)` — added in Task 1; used in `_run_compact` (Task 3), `_run_tui` (Task 4), `AOMApp._run_playbook_worker` (Task 4), and the integration tests (Tasks 5, 15).
- `_NullSink` has `record_event`, `record_stderr`, `end` — same surface `_SessionSink` exposes (verified against runner.py:92-117).
- `AOMApp.__init__` adds `record: bool = True` between `session_dir` and `**kwargs`, with a matching `record` property; `_run_playbook_worker` forwards it.
- `--no-record` flag stored on `dest="no_record"`; `cli.main` reads `args.no_record` and inverts to `record = not args.no_record` before dispatch.
- `--speed 0` is a `float`; `replay_session` guards with `if speed:` so `0.0` is treated as the no-sleep sentinel without any `if speed == 0` special-case.

**Risk callouts present in plan:**

- Negative-delta clamp: documented in Task 8 docstring ("R-risk: real streams are not strictly monotonic"), pinned by Task 9.
- Replay-vs-original divergence: documented in plan header AND module docstring (Task 7) AND `_REPLAY_HELP_EPILOG` (Task 13) AND `cli.main` help epilog (Task 14).
- Long-sleep risk: called out in `_REPLAY_HELP_EPILOG` (Task 13) and in `cli.main` help epilog (Task 14).

No gaps detected — plan is ready for execution.
