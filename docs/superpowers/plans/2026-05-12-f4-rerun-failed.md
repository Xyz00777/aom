# F4 — `aom rerun` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `aom rerun [<session-id>] [--failed] [--unreachable] [--changes-only] [--yes]` that reads a recorded session, derives a host list from failures/unreachable/changes, and re-invokes `ansible-playbook` with `--limit web2,web3` plus the session's original tags / extra-vars.

**Architecture:** Two pure helpers in `core/session.py` (`collect_failed_hosts`, `collect_unreachable_hosts`, `collect_changed_hosts`) work on the dict returned by `load_session` — no I/O, no state machine, no renderer dependencies. The CLI subcommand lives in a new `src/ansible_aom/rerun/cli.py` (mirroring `inspect/cli.py`) and reuses `runner.run_playbook` for execution; `core/` stays free of any `compact/` / `tui/` / `renderer/` imports. `meta.json` gains `ansible_args: list[str]` written at session start so a future rerun knows the original flags; sessions missing this field are refused with a clear error.

**Tech Stack:** Python 3.14 stdlib (`argparse`, `pathlib`, `json`, `sys`), existing `core/session.py`, existing `runner.run_playbook`, existing `renderer/factory.create_renderer`. No new dependencies.

---

## File Structure

**Create:**
- `src/ansible_aom/rerun/__init__.py` — empty package marker.
- `src/ansible_aom/rerun/cli.py` — `aom rerun` argparse + dispatch. Resolves session, builds `--limit`, prints the confirmation prompt, calls `run_playbook`. Lives outside `core/` because it imports from `renderer/`.
- `tests/unit/test_session_collectors.py` — pure-helper TDD for `collect_failed_hosts` / `collect_unreachable_hosts` / `collect_changed_hosts`.
- `tests/unit/test_rerun_cli.py` — argparse parsing, host-set composition, command-line construction, confirmation prompt logic (with input mocked), refusal on missing `ansible_args`.
- `tests/integration/test_rerun.py` — end-to-end: write a fake session via `SessionManager`, run `aom rerun --yes --failed`, assert it spawned `ansible-playbook` with the right `--limit`.

**Modify:**
- `src/ansible_aom/core/session.py` — `SessionManager.start_session` accepts an `ansible_args: list[str]` parameter (defaulting to `[]`) and writes it to `meta.json`. `load_session` already round-trips the meta dict, so it picks `ansible_args` up automatically. Add the three pure helpers at module level.
- `src/ansible_aom/runner.py:269-294` — `run_playbook` passes its own `ansible_args` parameter into `_SessionSink` so the sink can forward it to `SessionManager.start_session`.
- `src/ansible_aom/runner.py:62-75` — `_SessionSink.__init__` takes `ansible_args` and threads it into `SessionManager.start_session`.
- `src/ansible_aom/cli.py:231-234` — top-level dispatch grows a `rerun` branch alongside the existing `inspect` branch.
- `src/ansible_aom/cli.py:79-131` — extend the `--help` epilog with `aom rerun` examples.

---

## Task 1: Bump `meta.json` schema with `ansible_args`

**Files:**
- Modify: `src/ansible_aom/core/session.py:103-154` (`SessionManager.start_session`)
- Test: `tests/integration/test_session.py` (extend existing `TestStartSession` class)

The recorded `meta.json` must remember the flags the user ran so a later `aom rerun` can replay them. We extend `start_session` rather than introducing a separate `record_args` call: the flags are known at spawn time and never change mid-run.

- [ ] **Step 1: Write the failing test**

Append to `tests/integration/test_session.py` inside the existing `TestStartSession` class (find the class, add this method as the last method):

```python
    def test_start_session_persists_ansible_args(self, tmp_path: Path):
        """meta.json includes the ansible_args list so aom rerun can replay flags."""
        session_dir = tmp_path / "sessions"
        manager = SessionManager(session_dir=session_dir, playbook="deploy.yml")

        session_id = manager.start_session(
            "deploy.yml",
            ansible_args=["-i", "inv.ini", "--tags", "web"],
        )

        meta_file = session_dir / session_id / "meta.json"
        with open(meta_file) as f:
            meta = json.load(f)

        assert meta["ansible_args"] == ["-i", "inv.ini", "--tags", "web"]

    def test_start_session_default_ansible_args_is_empty_list(self, tmp_path: Path):
        """Old call sites that don't pass ansible_args get [] in meta.json."""
        session_dir = tmp_path / "sessions"
        manager = SessionManager(session_dir=session_dir, playbook="deploy.yml")

        session_id = manager.start_session("deploy.yml")

        meta_file = session_dir / session_id / "meta.json"
        with open(meta_file) as f:
            meta = json.load(f)

        assert meta["ansible_args"] == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/integration/test_session.py::TestStartSession::test_start_session_persists_ansible_args tests/integration/test_session.py::TestStartSession::test_start_session_default_ansible_args_is_empty_list -v`
Expected: FAIL — `start_session()` does not accept `ansible_args` keyword (or the field is missing from `meta.json`).

- [ ] **Step 3: Implement the schema bump**

In `src/ansible_aom/core/session.py`, modify `start_session` (around line 103). Replace the existing signature and the meta-dict construction:

```python
    def start_session(self, playbook: str, ansible_args: list[str] | None = None) -> str:
        """Create a new session and return the session ID (UUIDv7).

        Creates the session directory structure with events.jsonl, stderr.log,
        and meta.json files.

        Args:
            playbook: Path to the playbook being executed
            ansible_args: The argv tail passed to ansible-playbook (e.g.
                ``["-i", "inv.ini", "--tags", "web"]``). Persisted to
                ``meta.json`` so ``aom rerun`` can replay the original
                invocation. Defaults to ``[]`` for callers that don't yet
                track the args.

        Returns:
            The session ID (UUIDv7 format)
        """
        session_id = generate_uuidv7()
        self._session_id = session_id
        self._playbook = playbook
        self._start_time = datetime.now(timezone.utc)

        if ansible_args is None:
            ansible_args = []

        assert self._session_dir is not None, "Session directory must be set"
        session_path = self._session_dir / session_id
        session_path.mkdir(parents=True, exist_ok=True)
        session_path.chmod(0o755)

        self._events_file = session_path / "events.jsonl"
        self._stderr_file = session_path / "stderr.log"
        self._meta_file = session_path / "meta.json"

        self._events_file.touch()
        self._events_file.chmod(0o644)

        self._stderr_file.touch()
        self._stderr_file.chmod(0o644)

        meta = {
            "playbook": playbook,
            "ansible_args": list(ansible_args),
            "start_time": self._start_time.isoformat().replace("+00:00", "Z"),
            "version": "1.1",
            "session_id": session_id,
        }
        with open(self._meta_file, "w") as f:
            json.dump(meta, f)
        self._meta_file.chmod(0o644)

        self._active_sessions[session_id] = {
            "session_path": session_path,
            "events_file": self._events_file,
            "stderr_file": self._stderr_file,
            "meta_file": self._meta_file,
            "start_time": self._start_time,
            "playbook": playbook,
            "ansible_args": list(ansible_args),
        }

        return session_id
```

Note the version bump from `"1.0"` to `"1.1"` — this is a non-breaking schema addition (new optional field).

- [ ] **Step 4: Run the new tests**

Run: `uv run pytest tests/integration/test_session.py::TestStartSession -v`
Expected: PASS — both new tests green, all existing `TestStartSession` tests still green.

- [ ] **Step 5: Run the full suite**

Run: `uv run pytest tests/ -q`
Expected: 0 failing. The default-arg path keeps every existing `start_session("foo.yml")` call working.

- [ ] **Step 6: Commit**

```bash
git add src/ansible_aom/core/session.py tests/integration/test_session.py
git commit -m "feat(session): persist ansible_args to meta.json (schema 1.1)"
```

---

## Task 2: Thread `ansible_args` through `_SessionSink`

**Files:**
- Modify: `src/ansible_aom/runner.py:62-75` (`_SessionSink.__init__`)
- Modify: `src/ansible_aom/runner.py:269-300` (`run_playbook`)
- Test: `tests/integration/test_runner_session_recording.py` (extend)

Now that `SessionManager.start_session` accepts `ansible_args`, the runner must forward what it actually spawned. Without this the field is always `[]` in real runs, and rerun is impossible.

- [ ] **Step 1: Write the failing test**

Append to `tests/integration/test_runner_session_recording.py` (read the existing file's imports first; it likely already has the helpers we need):

```python
def test_runner_records_ansible_args_in_meta(tmp_path: Path):
    """run_playbook persists the ansible_args it was invoked with into meta.json."""
    import json
    from ansible_aom.runner import run_playbook

    sessions_dir = tmp_path / "sessions"

    class _NullRenderer:
        def start(self, playbook, ansible_args): ...
        def set_definitions(self, definitions): ...
        def update_state(self, event): ...
        def add_warning(self, message, deprecation): ...
        def handle_password_prompt(self, prompt): return ""
        def handle_interactive_prompt(self, prompt): return ""
        def handle_completion(self, exit_code, status): ...
        def print_log(self, line): ...
        def tick(self): ...
        def stop(self): ...

    # Use a fake ansible-playbook that exits 0 immediately so we don't need a
    # real ansible install. Same trick as the existing _spawn_fake helper.
    fake_script = tmp_path / "fake-ansible-playbook"
    fake_script.write_text("#!/usr/bin/env bash\nexit 0\n")
    fake_script.chmod(0o755)

    # Monkey-patch the executable lookup via the runner's _build_command.
    import ansible_aom.runner as runner_mod
    original_build = runner_mod._build_command
    runner_mod._build_command = lambda playbook, args: (str(fake_script), [playbook, *args])
    try:
        run_playbook(
            playbook="site.yml",
            ansible_args=["-i", "inv.ini", "--tags", "web"],
            renderer=_NullRenderer(),
            session_dir=sessions_dir,
        )
    finally:
        runner_mod._build_command = original_build

    session_dirs = [p for p in sessions_dir.iterdir() if p.is_dir()]
    assert len(session_dirs) == 1
    meta = json.loads((session_dirs[0] / "meta.json").read_text())
    assert meta["ansible_args"] == ["-i", "inv.ini", "--tags", "web"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/integration/test_runner_session_recording.py::test_runner_records_ansible_args_in_meta -v`
Expected: FAIL — `meta["ansible_args"]` is `[]` because the runner never forwards its args.

- [ ] **Step 3: Modify `_SessionSink`**

In `src/ansible_aom/runner.py`, replace `_SessionSink.__init__` (around line 63):

```python
    def __init__(
        self,
        session_dir: Path,
        playbook: str,
        ansible_args: list[str] | None = None,
        renderer: object | None = None,
    ) -> None:
        self._manager: SessionManager | None = None
        self._session_id: str | None = None
        self._renderer = renderer
        self._disabled = False
        try:
            session_dir.mkdir(parents=True, exist_ok=True)
            manager = SessionManager(session_dir=session_dir, playbook=playbook)
            self._session_id = manager.start_session(playbook, ansible_args=ansible_args or [])
            self._manager = manager
        except OSError as exc:
            logger.debug("session recording disabled (start failed): %s", exc)
```

- [ ] **Step 4: Modify `run_playbook` to pass `ansible_args` to the sink**

In `src/ansible_aom/runner.py`, find this line in `run_playbook` (around line 294):

```python
    sink = _SessionSink(session_dir or _default_session_dir(), playbook, renderer=renderer)
```

Replace with:

```python
    sink = _SessionSink(
        session_dir or _default_session_dir(),
        playbook,
        ansible_args=ansible_args,
        renderer=renderer,
    )
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `uv run pytest tests/integration/test_runner_session_recording.py::test_runner_records_ansible_args_in_meta -v`
Expected: PASS.

- [ ] **Step 6: Run the full suite**

Run: `uv run pytest tests/ -q`
Expected: 0 failing. The new keyword arg is backward-compatible.

- [ ] **Step 7: Commit**

```bash
git add src/ansible_aom/runner.py tests/integration/test_runner_session_recording.py
git commit -m "feat(runner): forward ansible_args to session metadata"
```

---

## Task 3: Pure helper — `collect_failed_hosts(session) -> set[str]`

**Files:**
- Modify: `src/ansible_aom/core/session.py` (append after `create_session_summary`)
- Test: `tests/unit/test_session_collectors.py` (new file)

This is the core domain logic: given the dict from `load_session`, return the set of hostnames that failed. Pure, no I/O, no renderer dependency — exactly what belongs in `core/`.

- [ ] **Step 1: Write the failing test**

Create `tests/unit/test_session_collectors.py`:

```python
"""Pure-helper tests for collect_failed_hosts / collect_unreachable_hosts.

Operates on the dict shape returned by ``core.session.load_session``:
``{"events": [...], "playbook": "...", ...}``. No filesystem, no
fixtures from disk — sessions are constructed inline.
"""

import pytest

from ansible_aom.core.session import collect_failed_hosts


def _session(events: list[dict]) -> dict:
    return {"events": events, "playbook": "site.yml", "ansible_args": []}


class TestCollectFailedHosts:
    def test_empty_session_returns_empty_set(self):
        assert collect_failed_hosts(_session([])) == set()

    def test_single_failure_returns_one_host(self):
        events = [
            {
                "_event": "v2_runner_on_failed",
                "task": {"name": "Install nginx"},
                "hosts": {"web2": {"failed": True, "msg": "boom"}},
            }
        ]
        assert collect_failed_hosts(_session(events)) == {"web2"}

    def test_multiple_failures_across_tasks_collected(self):
        events = [
            {
                "_event": "v2_runner_on_failed",
                "task": {"name": "T1"},
                "hosts": {"web2": {"failed": True}},
            },
            {
                "_event": "v2_runner_on_failed",
                "task": {"name": "T2"},
                "hosts": {"web3": {"failed": True}},
            },
        ]
        assert collect_failed_hosts(_session(events)) == {"web2", "web3"}

    def test_same_host_failing_twice_collapses_to_one_entry(self):
        events = [
            {
                "_event": "v2_runner_on_failed",
                "task": {"name": "T1"},
                "hosts": {"web2": {"failed": True}},
            },
            {
                "_event": "v2_runner_on_failed",
                "task": {"name": "T2"},
                "hosts": {"web2": {"failed": True}},
            },
        ]
        assert collect_failed_hosts(_session(events)) == {"web2"}

    def test_unreachable_events_ignored_by_failed_collector(self):
        """collect_failed_hosts only looks at v2_runner_on_failed."""
        events = [
            {
                "_event": "v2_runner_on_unreachable",
                "task": {"name": "Deploy"},
                "hosts": {"web1": {"unreachable": True}},
            },
        ]
        assert collect_failed_hosts(_session(events)) == set()

    def test_ok_events_ignored(self):
        events = [
            {
                "_event": "v2_runner_on_ok",
                "task": {"name": "T1"},
                "hosts": {"web1": {"ok": True}},
            },
        ]
        assert collect_failed_hosts(_session(events)) == set()

    def test_multi_host_failure_event(self):
        """A single failed event can carry multiple hosts."""
        events = [
            {
                "_event": "v2_runner_on_failed",
                "task": {"name": "T1"},
                "hosts": {
                    "web2": {"failed": True},
                    "web3": {"failed": True},
                },
            },
        ]
        assert collect_failed_hosts(_session(events)) == {"web2", "web3"}

    def test_session_without_events_key(self):
        """A meta-only session (no events.jsonl) returns an empty set."""
        assert collect_failed_hosts({"playbook": "site.yml"}) == set()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_session_collectors.py -v`
Expected: FAIL — `ImportError: cannot import name 'collect_failed_hosts' from 'ansible_aom.core.session'`.

- [ ] **Step 3: Implement `collect_failed_hosts`**

Append to `src/ansible_aom/core/session.py` (after `create_session_summary`):

```python
def collect_failed_hosts(session: dict[str, Any]) -> set[str]:
    """Return the set of hostnames that hit ``v2_runner_on_failed`` in this session.

    Pure: takes a session dict (as returned by ``load_session``) and
    returns the deduplicated set of failed hostnames. No I/O. Used by
    ``aom rerun --failed`` to build the ``--limit`` argument for the
    re-invoked ansible-playbook.

    Multi-host failure events are flattened: a single
    ``v2_runner_on_failed`` carrying ``{"web2": ..., "web3": ...}`` adds
    both names. A host that fails in multiple tasks contributes one
    entry only.

    Args:
        session: Session dict from ``load_session`` (or any dict with an
            ``events`` list of JSONL event dicts). Sessions without an
            ``events`` key return an empty set.

    Returns:
        Set of hostname strings.
    """
    failed: set[str] = set()
    for event in session.get("events", []):
        if event.get("_event") != "v2_runner_on_failed":
            continue
        hosts = event.get("hosts") or {}
        for hostname in hosts.keys():
            failed.add(hostname)
    return failed
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/unit/test_session_collectors.py -v`
Expected: PASS — all 8 tests green.

- [ ] **Step 5: Run the full suite**

Run: `uv run pytest tests/ -q`
Expected: 0 failing.

- [ ] **Step 6: Commit**

```bash
git add src/ansible_aom/core/session.py tests/unit/test_session_collectors.py
git commit -m "feat(core): add collect_failed_hosts pure helper for rerun"
```

---

## Task 4: Pure helper — `collect_unreachable_hosts(session) -> set[str]`

**Files:**
- Modify: `src/ansible_aom/core/session.py` (append after `collect_failed_hosts`)
- Test: `tests/unit/test_session_collectors.py` (extend)

Same shape as the failed collector but watches `v2_runner_on_unreachable`. Kept as a separate function (not a flag on `collect_failed_hosts`) so callers can compose: `--unreachable` is `failed | unreachable`, never `unreachable` alone in our CLI semantics, but the helper itself stays single-purpose.

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/test_session_collectors.py`:

```python
from ansible_aom.core.session import collect_unreachable_hosts


class TestCollectUnreachableHosts:
    def test_empty_session_returns_empty_set(self):
        assert collect_unreachable_hosts(_session([])) == set()

    def test_single_unreachable_returns_one_host(self):
        events = [
            {
                "_event": "v2_runner_on_unreachable",
                "task": {"name": "Deploy"},
                "hosts": {"web1": {"unreachable": True, "msg": "ssh timed out"}},
            }
        ]
        assert collect_unreachable_hosts(_session(events)) == {"web1"}

    def test_failed_events_ignored_by_unreachable_collector(self):
        events = [
            {
                "_event": "v2_runner_on_failed",
                "task": {"name": "T1"},
                "hosts": {"web2": {"failed": True}},
            },
        ]
        assert collect_unreachable_hosts(_session(events)) == set()

    def test_multi_host_unreachable_event(self):
        events = [
            {
                "_event": "v2_runner_on_unreachable",
                "task": {"name": "Deploy"},
                "hosts": {
                    "web1": {"unreachable": True},
                    "web2": {"unreachable": True},
                },
            },
        ]
        assert collect_unreachable_hosts(_session(events)) == {"web1", "web2"}

    def test_session_without_events_key(self):
        assert collect_unreachable_hosts({"playbook": "site.yml"}) == set()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_session_collectors.py::TestCollectUnreachableHosts -v`
Expected: FAIL — `ImportError: cannot import name 'collect_unreachable_hosts'`.

- [ ] **Step 3: Implement `collect_unreachable_hosts`**

Append to `src/ansible_aom/core/session.py` (immediately after `collect_failed_hosts`):

```python
def collect_unreachable_hosts(session: dict[str, Any]) -> set[str]:
    """Return the set of hostnames that hit ``v2_runner_on_unreachable``.

    Pure: same shape as ``collect_failed_hosts`` but watches a different
    event type. Used by ``aom rerun --unreachable`` to build the
    ``--limit`` argument; the CLI composes
    ``collect_failed_hosts() | collect_unreachable_hosts()`` because
    "things to retry" is the union, never just unreachable.

    Args:
        session: Session dict from ``load_session``. Sessions without an
            ``events`` key return an empty set.

    Returns:
        Set of hostname strings.
    """
    unreachable: set[str] = set()
    for event in session.get("events", []):
        if event.get("_event") != "v2_runner_on_unreachable":
            continue
        hosts = event.get("hosts") or {}
        for hostname in hosts.keys():
            unreachable.add(hostname)
    return unreachable
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/unit/test_session_collectors.py::TestCollectUnreachableHosts -v`
Expected: PASS.

- [ ] **Step 5: Run the full suite**

Run: `uv run pytest tests/ -q`
Expected: 0 failing.

- [ ] **Step 6: Commit**

```bash
git add src/ansible_aom/core/session.py tests/unit/test_session_collectors.py
git commit -m "feat(core): add collect_unreachable_hosts pure helper"
```

---

## Task 5: Pure helper — `collect_changed_hosts(session) -> set[str]`

**Files:**
- Modify: `src/ansible_aom/core/session.py` (append after `collect_unreachable_hosts`)
- Test: `tests/unit/test_session_collectors.py` (extend)

Powers `--changes-only`. A host is "changed" if any `v2_runner_on_ok` event for it carries `changed: true`. Used to limit a rerun to only the hosts that actually applied configuration last time — useful when verifying idempotency.

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/test_session_collectors.py`:

```python
from ansible_aom.core.session import collect_changed_hosts


class TestCollectChangedHosts:
    def test_empty_session_returns_empty_set(self):
        assert collect_changed_hosts(_session([])) == set()

    def test_changed_host_collected(self):
        events = [
            {
                "_event": "v2_runner_on_ok",
                "task": {"name": "Configure"},
                "hosts": {"web1": {"ok": True, "changed": True}},
            }
        ]
        assert collect_changed_hosts(_session(events)) == {"web1"}

    def test_unchanged_ok_host_ignored(self):
        events = [
            {
                "_event": "v2_runner_on_ok",
                "task": {"name": "Check"},
                "hosts": {"web1": {"ok": True, "changed": False}},
            }
        ]
        assert collect_changed_hosts(_session(events)) == set()

    def test_failed_events_ignored(self):
        events = [
            {
                "_event": "v2_runner_on_failed",
                "task": {"name": "T1"},
                "hosts": {"web2": {"failed": True, "changed": True}},
            }
        ]
        assert collect_changed_hosts(_session(events)) == set()

    def test_multi_host_event_picks_only_changed(self):
        events = [
            {
                "_event": "v2_runner_on_ok",
                "task": {"name": "Config"},
                "hosts": {
                    "web1": {"ok": True, "changed": True},
                    "web2": {"ok": True, "changed": False},
                    "web3": {"ok": True, "changed": True},
                },
            }
        ]
        assert collect_changed_hosts(_session(events)) == {"web1", "web3"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_session_collectors.py::TestCollectChangedHosts -v`
Expected: FAIL — `ImportError: cannot import name 'collect_changed_hosts'`.

- [ ] **Step 3: Implement `collect_changed_hosts`**

Append to `src/ansible_aom/core/session.py` (immediately after `collect_unreachable_hosts`):

```python
def collect_changed_hosts(session: dict[str, Any]) -> set[str]:
    """Return the set of hostnames that had at least one changed task.

    Pure: scans ``v2_runner_on_ok`` events and selects host entries
    whose per-host result dict has ``changed`` truthy. Powers
    ``aom rerun --changes-only`` for idempotency verification.

    Args:
        session: Session dict from ``load_session``. Sessions without an
            ``events`` key return an empty set.

    Returns:
        Set of hostname strings.
    """
    changed: set[str] = set()
    for event in session.get("events", []):
        if event.get("_event") != "v2_runner_on_ok":
            continue
        hosts = event.get("hosts") or {}
        for hostname, result in hosts.items():
            if isinstance(result, dict) and result.get("changed"):
                changed.add(hostname)
    return changed
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/unit/test_session_collectors.py::TestCollectChangedHosts -v`
Expected: PASS.

- [ ] **Step 5: Run the full suite**

Run: `uv run pytest tests/ -q`
Expected: 0 failing.

- [ ] **Step 6: Commit**

```bash
git add src/ansible_aom/core/session.py tests/unit/test_session_collectors.py
git commit -m "feat(core): add collect_changed_hosts pure helper"
```

---

## Task 6: Resolve session ID — pick the latest when omitted

**Files:**
- Create: `src/ansible_aom/rerun/__init__.py` (empty)
- Create: `src/ansible_aom/rerun/cli.py` (initial sketch — only `_resolve_session_id`)
- Test: `tests/unit/test_rerun_cli.py` (new file)

The CLI signature is `aom rerun [<session-id>]` — when no ID is provided, pick the most recent session. We isolate that logic so we can test it without spinning up the whole CLI.

- [ ] **Step 1: Create the empty package marker**

Create `src/ansible_aom/rerun/__init__.py` with content:

```python
"""aom rerun subcommand — re-invoke ansible-playbook on hosts that need attention."""
```

- [ ] **Step 2: Write the failing test**

Create `tests/unit/test_rerun_cli.py`:

```python
"""Unit tests for the aom rerun subcommand."""

import json
from pathlib import Path

import pytest

from ansible_aom.rerun.cli import _resolve_session_id


def _make_session(state_dir: Path, session_id: str, start_time: str) -> Path:
    """Helper: create a session directory with a minimal meta.json."""
    session_path = state_dir / session_id
    session_path.mkdir(parents=True)
    meta = {
        "playbook": "site.yml",
        "ansible_args": ["-i", "inv.ini"],
        "start_time": start_time,
        "session_id": session_id,
        "status": "failed",
        "version": "1.1",
    }
    (session_path / "meta.json").write_text(json.dumps(meta))
    return session_path


class TestResolveSessionId:
    def test_explicit_full_id_returned_as_is(self, tmp_path: Path):
        state_dir = tmp_path / "sessions"
        sid = "01971111-1111-7000-8000-000000000001"
        _make_session(state_dir, sid, "2026-05-12T10:00:00Z")
        assert _resolve_session_id(state_dir, sid) == sid

    def test_explicit_short_id_resolved_to_full(self, tmp_path: Path):
        state_dir = tmp_path / "sessions"
        sid = "01971111-1111-7000-8000-000000000001"
        _make_session(state_dir, sid, "2026-05-12T10:00:00Z")
        assert _resolve_session_id(state_dir, "01971111") == sid

    def test_omitted_returns_most_recent(self, tmp_path: Path):
        state_dir = tmp_path / "sessions"
        older = "01971111-1111-7000-8000-000000000001"
        newer = "01971112-2222-7000-8000-000000000002"
        _make_session(state_dir, older, "2026-05-10T10:00:00Z")
        _make_session(state_dir, newer, "2026-05-12T10:00:00Z")
        assert _resolve_session_id(state_dir, None) == newer

    def test_unknown_id_raises(self, tmp_path: Path):
        state_dir = tmp_path / "sessions"
        with pytest.raises(LookupError, match="No session matching"):
            _resolve_session_id(state_dir, "deadbeef")

    def test_no_sessions_at_all_raises(self, tmp_path: Path):
        state_dir = tmp_path / "sessions"
        state_dir.mkdir()
        with pytest.raises(LookupError, match="No sessions"):
            _resolve_session_id(state_dir, None)

    def test_ambiguous_short_id_raises(self, tmp_path: Path):
        state_dir = tmp_path / "sessions"
        sid_a = "01971111-1111-7000-8000-000000000001"
        sid_b = "01971111-2222-7000-8000-000000000002"
        _make_session(state_dir, sid_a, "2026-05-10T10:00:00Z")
        _make_session(state_dir, sid_b, "2026-05-12T10:00:00Z")
        with pytest.raises(LookupError, match="ambiguous"):
            _resolve_session_id(state_dir, "01971111")
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_rerun_cli.py -v`
Expected: FAIL — `ImportError: No module named 'ansible_aom.rerun.cli'`.

- [ ] **Step 4: Implement `_resolve_session_id`**

Create `src/ansible_aom/rerun/cli.py`:

```python
"""CLI entry point for ``aom rerun``.

Reads a recorded session, derives a host list from failures /
unreachable / changes, and re-invokes ``ansible-playbook`` with the
original args plus a ``--limit`` matching the derived hosts.

The only piece in this file that's not pure-CLI plumbing is host-set
composition; the actual set computation lives in ``core.session``
(``collect_failed_hosts`` etc.) so it stays testable in isolation
and ``core/`` keeps its no-renderer rule.
"""

from __future__ import annotations

from pathlib import Path

from ansible_aom.core.session import list_sessions


def _resolve_session_id(state_dir: Path, session_id_or_short: str | None) -> str:
    """Resolve an explicit session ID, short prefix, or "most recent" intent.

    Mirrors the inspect command's resolution semantics: full UUID wins
    over prefix match, prefix match must be unique, "no argument" picks
    the most recent session by start_time.

    Args:
        state_dir: Directory containing session sub-directories.
        session_id_or_short: Either a full 36-char UUID, an 8-char (or
            longer) prefix, or ``None`` to pick the latest session.

    Returns:
        The resolved full session ID.

    Raises:
        LookupError: When no session matches, no sessions exist at all,
            or a short prefix matches more than one session.
    """
    sessions = list_sessions(state_dir)
    if not sessions:
        raise LookupError(f"No sessions found in {state_dir}")

    if session_id_or_short is None:
        # list_sessions returns newest-first.
        return sessions[0]["session_id"]

    # Exact full-id match wins.
    for s in sessions:
        if s["session_id"] == session_id_or_short:
            return session_id_or_short

    # Otherwise treat as prefix.
    matches = [s for s in sessions if s["session_id"].startswith(session_id_or_short)]
    if not matches:
        raise LookupError(f"No session matching {session_id_or_short!r} in {state_dir}")
    if len(matches) > 1:
        ids = ", ".join(s["session_id"] for s in matches)
        raise LookupError(
            f"Prefix {session_id_or_short!r} is ambiguous: matches {ids}"
        )
    return matches[0]["session_id"]
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `uv run pytest tests/unit/test_rerun_cli.py -v`
Expected: PASS — all 6 tests in `TestResolveSessionId` green.

- [ ] **Step 6: Commit**

```bash
git add src/ansible_aom/rerun/__init__.py src/ansible_aom/rerun/cli.py tests/unit/test_rerun_cli.py
git commit -m "feat(rerun): add session-id resolver (full / prefix / latest)"
```

---

## Task 7: Compose the host set from CLI flags

**Files:**
- Modify: `src/ansible_aom/rerun/cli.py` (append `_compose_host_set`)
- Test: `tests/unit/test_rerun_cli.py` (extend)

Given a loaded session and the parsed flags, return the set of hostnames the rerun should target. `--failed` / `--unreachable` / `--changes-only` may be combined; "no flag" defaults to `--failed` (the most common case per the F4 spec).

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/test_rerun_cli.py`:

```python
from ansible_aom.rerun.cli import _compose_host_set


def _session_dict(events: list[dict]) -> dict:
    return {"events": events, "playbook": "site.yml", "ansible_args": []}


class TestComposeHostSet:
    def _events(self) -> list[dict]:
        return [
            {
                "_event": "v2_runner_on_failed",
                "task": {"name": "T1"},
                "hosts": {"web2": {"failed": True}},
            },
            {
                "_event": "v2_runner_on_unreachable",
                "task": {"name": "T2"},
                "hosts": {"web1": {"unreachable": True}},
            },
            {
                "_event": "v2_runner_on_ok",
                "task": {"name": "T3"},
                "hosts": {"web3": {"ok": True, "changed": True}},
            },
        ]

    def test_default_no_flag_returns_failed_only(self):
        result = _compose_host_set(
            _session_dict(self._events()),
            failed=False,
            unreachable=False,
            changes_only=False,
        )
        assert result == {"web2"}

    def test_failed_flag_returns_failed_hosts(self):
        result = _compose_host_set(
            _session_dict(self._events()),
            failed=True,
            unreachable=False,
            changes_only=False,
        )
        assert result == {"web2"}

    def test_unreachable_flag_includes_failed_and_unreachable(self):
        """--unreachable is a strict superset of --failed (per spec)."""
        result = _compose_host_set(
            _session_dict(self._events()),
            failed=False,
            unreachable=True,
            changes_only=False,
        )
        assert result == {"web1", "web2"}

    def test_changes_only_returns_changed_hosts(self):
        result = _compose_host_set(
            _session_dict(self._events()),
            failed=False,
            unreachable=False,
            changes_only=True,
        )
        assert result == {"web3"}

    def test_combined_flags_union(self):
        result = _compose_host_set(
            _session_dict(self._events()),
            failed=True,
            unreachable=True,
            changes_only=True,
        )
        assert result == {"web1", "web2", "web3"}

    def test_no_matching_hosts_returns_empty(self):
        result = _compose_host_set(
            _session_dict([]),
            failed=True,
            unreachable=True,
            changes_only=True,
        )
        assert result == set()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_rerun_cli.py::TestComposeHostSet -v`
Expected: FAIL — `ImportError: cannot import name '_compose_host_set'`.

- [ ] **Step 3: Implement `_compose_host_set`**

Append to `src/ansible_aom/rerun/cli.py`:

```python
from ansible_aom.core.session import (
    collect_changed_hosts,
    collect_failed_hosts,
    collect_unreachable_hosts,
)


def _compose_host_set(
    session: dict,
    *,
    failed: bool,
    unreachable: bool,
    changes_only: bool,
) -> set[str]:
    """Combine the requested host categories into a single set.

    Semantics (from the F4 spec):
    - No flag → behave like ``--failed`` (the most common case).
    - ``--unreachable`` is a strict *superset* of ``--failed``: hosts
      that failed AND hosts that were unreachable. We never return only
      unreachable hosts on its own.
    - ``--changes-only`` adds hosts whose tasks reported ``changed: true``.
    - Multiple flags compose by union.

    Args:
        session: Loaded session dict (from ``load_session``).
        failed: Include hosts that hit ``v2_runner_on_failed``.
        unreachable: Include hosts from both failed AND unreachable.
        changes_only: Include hosts that had at least one changed task.

    Returns:
        Union of the requested host categories.
    """
    if not failed and not unreachable and not changes_only:
        # Default behaviour matches `--failed` so the bare command does
        # the most common thing.
        return collect_failed_hosts(session)

    hosts: set[str] = set()
    if failed:
        hosts |= collect_failed_hosts(session)
    if unreachable:
        # --unreachable means "everything to retry": failed ∪ unreachable.
        hosts |= collect_failed_hosts(session)
        hosts |= collect_unreachable_hosts(session)
    if changes_only:
        hosts |= collect_changed_hosts(session)
    return hosts
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/unit/test_rerun_cli.py::TestComposeHostSet -v`
Expected: PASS — all 6 tests green.

- [ ] **Step 5: Commit**

```bash
git add src/ansible_aom/rerun/cli.py tests/unit/test_rerun_cli.py
git commit -m "feat(rerun): compose host set from --failed/--unreachable/--changes-only"
```

---

## Task 8: Build the ansible-playbook command line

**Files:**
- Modify: `src/ansible_aom/rerun/cli.py` (append `_build_rerun_command`)
- Test: `tests/unit/test_rerun_cli.py` (extend)

Pure transformation: given the loaded session's `playbook` + `ansible_args` and the resolved host set, produce the `(playbook, ansible_args)` tuple that goes into `run_playbook`. This is also where we decide that `--limit` overrides any pre-existing `--limit` in the original args (the user explicitly chose to retry a subset; honouring the old limit silently would be confusing).

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/test_rerun_cli.py`:

```python
from ansible_aom.rerun.cli import _build_rerun_command


class TestBuildRerunCommand:
    def test_appends_limit_to_original_args(self):
        playbook, args = _build_rerun_command(
            session={
                "playbook": "site.yml",
                "ansible_args": ["-i", "inv.ini", "--tags", "web"],
            },
            hosts={"web2", "web3"},
        )
        assert playbook == "site.yml"
        # Limit value is sorted for determinism.
        assert args == ["-i", "inv.ini", "--tags", "web", "--limit", "web2,web3"]

    def test_overrides_existing_limit_flag(self):
        """A pre-existing --limit in the original args is dropped in favour of ours."""
        playbook, args = _build_rerun_command(
            session={
                "playbook": "site.yml",
                "ansible_args": ["-i", "inv.ini", "--limit", "web1", "--tags", "web"],
            },
            hosts={"web2"},
        )
        assert args == ["-i", "inv.ini", "--tags", "web", "--limit", "web2"]

    def test_overrides_short_l_flag(self):
        """``-l`` is the short form of ``--limit``; treat it the same."""
        playbook, args = _build_rerun_command(
            session={
                "playbook": "site.yml",
                "ansible_args": ["-l", "web1", "-v"],
            },
            hosts={"web2"},
        )
        assert args == ["-v", "--limit", "web2"]

    def test_overrides_limit_equals_form(self):
        """``--limit=hosts`` (single arg) is also dropped."""
        playbook, args = _build_rerun_command(
            session={
                "playbook": "site.yml",
                "ansible_args": ["--limit=web1", "-v"],
            },
            hosts={"web2"},
        )
        assert args == ["-v", "--limit", "web2"]

    def test_single_host_limit(self):
        playbook, args = _build_rerun_command(
            session={"playbook": "site.yml", "ansible_args": []},
            hosts={"web2"},
        )
        assert args == ["--limit", "web2"]

    def test_empty_host_set_raises(self):
        """No hosts → no rerun. Caller is expected to surface this earlier."""
        with pytest.raises(ValueError, match="empty host set"):
            _build_rerun_command(
                session={"playbook": "site.yml", "ansible_args": []},
                hosts=set(),
            )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_rerun_cli.py::TestBuildRerunCommand -v`
Expected: FAIL — `ImportError: cannot import name '_build_rerun_command'`.

- [ ] **Step 3: Implement `_build_rerun_command`**

Append to `src/ansible_aom/rerun/cli.py`:

```python
def _strip_limit_args(args: list[str]) -> list[str]:
    """Drop any pre-existing ``--limit`` / ``-l`` from the args list.

    Handles three forms:
    - ``--limit foo``      (two tokens)
    - ``--limit=foo``      (one token)
    - ``-l foo``           (two tokens, short form)

    A pre-existing limit is replaced — not unioned — because the user
    explicitly chose a subset by running ``aom rerun --failed``.
    Silently honouring an old ``--limit web1`` would intersect that
    with the failed set and could empty it, surprising the user.
    """
    out: list[str] = []
    skip_next = False
    for tok in args:
        if skip_next:
            skip_next = False
            continue
        if tok in ("--limit", "-l"):
            skip_next = True
            continue
        if tok.startswith("--limit="):
            continue
        out.append(tok)
    return out


def _build_rerun_command(
    session: dict,
    hosts: set[str],
) -> tuple[str, list[str]]:
    """Construct the (playbook, ansible_args) pair to spawn for the rerun.

    The session's recorded ``ansible_args`` are forwarded verbatim
    except for any pre-existing ``--limit`` / ``-l`` flags, which are
    dropped in favour of one built from ``hosts``. The new ``--limit``
    value is the sorted, comma-joined host list (sorted for
    determinism — the underlying set has no order).

    Args:
        session: Loaded session dict (must contain ``playbook`` and
            ``ansible_args``).
        hosts: Non-empty set of hostnames to limit the rerun to.

    Returns:
        ``(playbook_path, ansible_args)`` tuple ready for
        ``run_playbook``.

    Raises:
        ValueError: If ``hosts`` is empty (caller is expected to handle
            "nothing to rerun" before reaching this function).
    """
    if not hosts:
        raise ValueError("Cannot build rerun command for empty host set")
    playbook = session["playbook"]
    original_args = list(session.get("ansible_args") or [])
    cleaned = _strip_limit_args(original_args)
    limit_value = ",".join(sorted(hosts))
    return playbook, [*cleaned, "--limit", limit_value]
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/unit/test_rerun_cli.py::TestBuildRerunCommand -v`
Expected: PASS — all 6 tests green.

- [ ] **Step 5: Commit**

```bash
git add src/ansible_aom/rerun/cli.py tests/unit/test_rerun_cli.py
git commit -m "feat(rerun): build command line with --limit and stripped old limits"
```

---

## Task 9: Confirmation prompt — print plan, host count, idempotency warning

**Files:**
- Modify: `src/ansible_aom/rerun/cli.py` (append `_confirm`)
- Test: `tests/unit/test_rerun_cli.py` (extend)

Per the approved scope: print the planned `ansible-playbook` command line, the host count, and a one-line warning that re-running may execute non-idempotent tasks again. Then prompt `Y/n`. `--yes` skips the prompt entirely.

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/test_rerun_cli.py`:

```python
import io
from contextlib import redirect_stdout

from ansible_aom.rerun.cli import _confirm


class TestConfirm:
    def test_yes_flag_skips_prompt_and_returns_true(self):
        # No input function provided — would raise EOFError if called.
        out = io.StringIO()
        with redirect_stdout(out):
            assert _confirm(
                playbook="site.yml",
                args=["-i", "inv.ini", "--limit", "web2,web3"],
                host_count=2,
                assume_yes=True,
                input_fn=None,
            ) is True
        text = out.getvalue()
        assert "ansible-playbook site.yml -i inv.ini --limit web2,web3" in text
        assert "2 host" in text
        # Warning still printed even with --yes — the user should see what's
        # about to happen.
        assert "non-idempotent" in text.lower()

    def test_default_yes_on_empty_input(self):
        """Bare Enter (empty string) accepts the default Y."""
        out = io.StringIO()
        with redirect_stdout(out):
            result = _confirm(
                playbook="site.yml",
                args=["--limit", "web2"],
                host_count=1,
                assume_yes=False,
                input_fn=lambda _prompt: "",
            )
        assert result is True

    def test_y_accepted(self):
        result = _confirm(
            playbook="site.yml",
            args=["--limit", "web2"],
            host_count=1,
            assume_yes=False,
            input_fn=lambda _prompt: "y",
        )
        assert result is True

    def test_yes_accepted(self):
        result = _confirm(
            playbook="site.yml",
            args=["--limit", "web2"],
            host_count=1,
            assume_yes=False,
            input_fn=lambda _prompt: "yes",
        )
        assert result is True

    def test_n_rejected(self):
        result = _confirm(
            playbook="site.yml",
            args=["--limit", "web2"],
            host_count=1,
            assume_yes=False,
            input_fn=lambda _prompt: "n",
        )
        assert result is False

    def test_no_rejected(self):
        result = _confirm(
            playbook="site.yml",
            args=["--limit", "web2"],
            host_count=1,
            assume_yes=False,
            input_fn=lambda _prompt: "no",
        )
        assert result is False

    def test_anything_else_rejected(self):
        result = _confirm(
            playbook="site.yml",
            args=["--limit", "web2"],
            host_count=1,
            assume_yes=False,
            input_fn=lambda _prompt: "maybe",
        )
        assert result is False

    def test_warning_includes_idempotency_language(self):
        out = io.StringIO()
        with redirect_stdout(out):
            _confirm(
                playbook="site.yml",
                args=["--limit", "web2"],
                host_count=1,
                assume_yes=True,
                input_fn=None,
            )
        text = out.getvalue().lower()
        # Must mention non-idempotent risk explicitly so the user sees it.
        assert "non-idempotent" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_rerun_cli.py::TestConfirm -v`
Expected: FAIL — `ImportError: cannot import name '_confirm'`.

- [ ] **Step 3: Implement `_confirm`**

Append to `src/ansible_aom/rerun/cli.py`:

```python
from typing import Callable


def _confirm(
    *,
    playbook: str,
    args: list[str],
    host_count: int,
    assume_yes: bool,
    input_fn: Callable[[str], str] | None,
) -> bool:
    """Print the rerun plan + warning, then ask for Y/n confirmation.

    Always prints the planned command line, host count, and a
    one-line warning that re-running may execute non-idempotent tasks
    (notifications, side-effecting modules, etc.) — this happens even
    when ``assume_yes`` is set so the user sees what's about to fire.

    Args:
        playbook: Resolved playbook path.
        args: Final ansible-playbook arg list (already includes
            ``--limit``).
        host_count: Length of the resolved host set, used for the
            "running on N host(s)" line.
        assume_yes: When True, skip the prompt and return True
            unconditionally (still prints the plan).
        input_fn: Injectable for tests. Defaults to ``builtins.input``
            when None and ``assume_yes`` is False; ignored when
            ``assume_yes`` is True.

    Returns:
        True if the user confirmed (or ``--yes`` was passed), False
        otherwise.
    """
    plural = "host" if host_count == 1 else "hosts"
    cmd_str = "ansible-playbook " + playbook + (" " + " ".join(args) if args else "")
    print(f"Planned: {cmd_str}")
    print(f"Targeting {host_count} {plural}.")
    print(
        "WARNING: re-running may execute non-idempotent tasks again "
        "(notifications, restarts, side-effecting modules)."
    )
    if assume_yes:
        return True

    fn = input_fn if input_fn is not None else input
    answer = fn("Proceed? [Y/n] ").strip().lower()
    if answer == "":
        return True
    return answer in ("y", "yes")
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/unit/test_rerun_cli.py::TestConfirm -v`
Expected: PASS — all 8 tests green.

- [ ] **Step 5: Commit**

```bash
git add src/ansible_aom/rerun/cli.py tests/unit/test_rerun_cli.py
git commit -m "feat(rerun): add confirmation prompt with idempotency warning"
```

---

## Task 10: Validate session has `ansible_args` (refuse old sessions cleanly)

**Files:**
- Modify: `src/ansible_aom/rerun/cli.py` (append `_require_ansible_args`)
- Test: `tests/unit/test_rerun_cli.py` (extend)

Per the approved scope: rather than try to reconstruct args from the playbook field, we refuse with a clear error and document the schema bump. Sessions recorded by AOM ≥ schema 1.1 always have the field; older sessions get a one-shot upgrade message.

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/test_rerun_cli.py`:

```python
from ansible_aom.rerun.cli import _require_ansible_args


class TestRequireAnsibleArgs:
    def test_session_with_args_returns_them(self):
        session = {"playbook": "site.yml", "ansible_args": ["-i", "inv.ini"]}
        assert _require_ansible_args(session, "01971111") == ["-i", "inv.ini"]

    def test_session_with_empty_args_returns_empty_list(self):
        """An explicit [] is valid — the user originally ran `aom site.yml`."""
        session = {"playbook": "site.yml", "ansible_args": []}
        assert _require_ansible_args(session, "01971111") == []

    def test_missing_field_raises_with_clear_error(self):
        session = {"playbook": "site.yml"}  # no ansible_args key at all
        with pytest.raises(SystemExit) as excinfo:
            _require_ansible_args(session, "01971111-old-session")
        # SystemExit with non-zero exit code.
        assert excinfo.value.code == 2

    def test_missing_field_error_message_explains_schema(self, capsys):
        session = {"playbook": "site.yml"}
        with pytest.raises(SystemExit):
            _require_ansible_args(session, "01971111-old-session")
        err = capsys.readouterr().err
        assert "01971111-old-session" in err
        # Mentions the schema bump so the user understands.
        assert "schema" in err.lower() or "older" in err.lower() or "missing" in err.lower()
        # Mentions ansible_args so the user can grep their meta.json.
        assert "ansible_args" in err

    def test_none_value_treated_as_missing(self):
        """A null value (rare, but possible if hand-edited) is also missing."""
        session = {"playbook": "site.yml", "ansible_args": None}
        with pytest.raises(SystemExit):
            _require_ansible_args(session, "01971111")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_rerun_cli.py::TestRequireAnsibleArgs -v`
Expected: FAIL — `ImportError: cannot import name '_require_ansible_args'`.

- [ ] **Step 3: Implement `_require_ansible_args`**

Append to `src/ansible_aom/rerun/cli.py`:

```python
import sys


def _require_ansible_args(session: dict, session_id: str) -> list[str]:
    """Return the recorded ``ansible_args`` or refuse with a clear error.

    Sessions recorded by AOM ≥ schema 1.1 always have ``ansible_args``
    in ``meta.json`` (an empty list when no flags were passed). Older
    sessions don't have the field at all; rather than guess what flags
    the user originally ran, we refuse and explain.

    The schema bump is documented in the project changelog and in the
    docstring on ``SessionManager.start_session``.

    Args:
        session: Loaded session dict.
        session_id: Used in the error message so the user knows which
            session triggered the refusal.

    Returns:
        The recorded ``ansible_args`` list (possibly empty).

    Raises:
        SystemExit(2): If the field is missing or null.
    """
    args = session.get("ansible_args")
    if args is None:
        print(
            f"aom rerun: session {session_id} is missing 'ansible_args' "
            "in meta.json. This field was added in AOM session schema "
            "1.1 — older sessions cannot be re-run automatically because "
            "AOM doesn't know which flags (e.g. -i, --tags, --extra-vars) "
            "were originally passed. Re-record the session with the "
            "current AOM, or invoke ansible-playbook manually with "
            "--limit.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    return list(args)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/unit/test_rerun_cli.py::TestRequireAnsibleArgs -v`
Expected: PASS — all 5 tests green.

- [ ] **Step 5: Commit**

```bash
git add src/ansible_aom/rerun/cli.py tests/unit/test_rerun_cli.py
git commit -m "feat(rerun): refuse old sessions missing ansible_args with clear error"
```

---

## Task 11: argparse — wire up `aom rerun [<session-id>] [--failed] [--unreachable] [--changes-only] [--yes]`

**Files:**
- Modify: `src/ansible_aom/rerun/cli.py` (append `main` and `_create_parser`)
- Test: `tests/unit/test_rerun_cli.py` (extend)

Now bolt the parser onto the helpers. The parser is split out so tests can call `_create_parser().parse_args(["--failed", "--yes"])` without going through `main`.

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/test_rerun_cli.py`:

```python
from ansible_aom.rerun.cli import _create_parser


class TestCreateParser:
    def test_no_args(self):
        ns = _create_parser().parse_args([])
        assert ns.session_id is None
        assert ns.failed is False
        assert ns.unreachable is False
        assert ns.changes_only is False
        assert ns.yes is False

    def test_session_id_positional(self):
        ns = _create_parser().parse_args(["abc12345"])
        assert ns.session_id == "abc12345"

    def test_failed_flag(self):
        ns = _create_parser().parse_args(["--failed"])
        assert ns.failed is True

    def test_unreachable_flag(self):
        ns = _create_parser().parse_args(["--unreachable"])
        assert ns.unreachable is True

    def test_changes_only_flag(self):
        ns = _create_parser().parse_args(["--changes-only"])
        assert ns.changes_only is True

    def test_yes_short_form(self):
        ns = _create_parser().parse_args(["-y"])
        assert ns.yes is True

    def test_yes_long_form(self):
        ns = _create_parser().parse_args(["--yes"])
        assert ns.yes is True

    def test_state_dir_override(self, tmp_path: Path):
        ns = _create_parser().parse_args(["--state-dir", str(tmp_path)])
        assert ns.state_dir == tmp_path

    def test_combined(self):
        ns = _create_parser().parse_args(
            ["abc12345", "--failed", "--unreachable", "--yes"]
        )
        assert ns.session_id == "abc12345"
        assert ns.failed is True
        assert ns.unreachable is True
        assert ns.yes is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_rerun_cli.py::TestCreateParser -v`
Expected: FAIL — `ImportError: cannot import name '_create_parser'`.

- [ ] **Step 3: Implement `_create_parser`**

Append to `src/ansible_aom/rerun/cli.py`:

```python
import argparse


def _create_parser() -> argparse.ArgumentParser:
    """Build the argparse parser for ``aom rerun``.

    Split out from ``main`` so tests can drive parsing in isolation.
    """
    parser = argparse.ArgumentParser(
        prog="aom rerun",
        description=(
            "Re-invoke ansible-playbook on hosts that need attention from "
            "a recorded session."
        ),
    )
    parser.add_argument(
        "session_id",
        nargs="?",
        default=None,
        help="Session ID (full UUID or 8-char prefix). Defaults to the latest session.",
    )
    parser.add_argument(
        "--failed",
        action="store_true",
        help="Re-run on hosts that hit v2_runner_on_failed (default when no flag is given).",
    )
    parser.add_argument(
        "--unreachable",
        action="store_true",
        help="Re-run on failed AND unreachable hosts.",
    )
    parser.add_argument(
        "--changes-only",
        action="store_true",
        dest="changes_only",
        help="Re-run on hosts that had at least one changed task.",
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip the confirmation prompt.",
    )
    parser.add_argument(
        "--state-dir",
        type=Path,
        dest="state_dir",
        default=Path.home() / ".local" / "state" / "aom" / "sessions",
        help="Directory containing session data (default: ~/.local/state/aom/sessions).",
    )
    return parser
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/unit/test_rerun_cli.py::TestCreateParser -v`
Expected: PASS — all 9 tests green.

- [ ] **Step 5: Commit**

```bash
git add src/ansible_aom/rerun/cli.py tests/unit/test_rerun_cli.py
git commit -m "feat(rerun): wire argparse for session-id + flag set"
```

---

## Task 12: `main` entry point — orchestrate resolve → load → compose → confirm → run

**Files:**
- Modify: `src/ansible_aom/rerun/cli.py` (append `main`)
- Test: `tests/unit/test_rerun_cli.py` (extend)

Now stitch it all together. `main` returns an exit code (`int`) and never raises (catches exceptions, prints them, returns non-zero). The actual `run_playbook` invocation is gated behind a callable parameter so tests can verify the orchestration without spawning subprocesses.

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/test_rerun_cli.py`:

```python
from ansible_aom.rerun.cli import main as rerun_main


def _write_session_with_failure(state_dir: Path, session_id: str) -> None:
    """Helper: write a session with one failed host (web2)."""
    session_path = state_dir / session_id
    session_path.mkdir(parents=True)
    meta = {
        "playbook": "site.yml",
        "ansible_args": ["-i", "inv.ini"],
        "start_time": "2026-05-12T10:00:00Z",
        "session_id": session_id,
        "status": "failed",
        "version": "1.1",
    }
    (session_path / "meta.json").write_text(json.dumps(meta))
    events = [
        {
            "_event": "v2_runner_on_failed",
            "task": {"name": "Install"},
            "hosts": {"web2": {"failed": True, "msg": "boom"}},
        }
    ]
    (session_path / "events.jsonl").write_text(
        "\n".join(json.dumps(e) for e in events) + "\n"
    )
    (session_path / "stderr.log").write_text("")


class TestMain:
    def test_runs_with_correct_command(self, tmp_path: Path):
        """Happy path: --yes --failed → run_playbook called with --limit web2."""
        state_dir = tmp_path / "sessions"
        sid = "01971111-1111-7000-8000-000000000001"
        _write_session_with_failure(state_dir, sid)

        captured: dict = {}

        def fake_runner(playbook, ansible_args):
            captured["playbook"] = playbook
            captured["args"] = ansible_args
            return 0

        rc = rerun_main(
            argv=["--state-dir", str(state_dir), sid, "--failed", "--yes"],
            runner=fake_runner,
        )
        assert rc == 0
        assert captured["playbook"] == "site.yml"
        assert "--limit" in captured["args"]
        idx = captured["args"].index("--limit")
        assert captured["args"][idx + 1] == "web2"

    def test_no_session_id_uses_latest(self, tmp_path: Path):
        state_dir = tmp_path / "sessions"
        sid = "01971111-1111-7000-8000-000000000001"
        _write_session_with_failure(state_dir, sid)

        captured: dict = {}

        def fake_runner(playbook, ansible_args):
            captured["args"] = ansible_args
            return 0

        rc = rerun_main(
            argv=["--state-dir", str(state_dir), "--yes"],
            runner=fake_runner,
        )
        assert rc == 0
        assert "--limit" in captured["args"]

    def test_no_hosts_to_rerun_returns_nonzero(self, tmp_path: Path, capsys):
        """A session with no failures and --failed → nothing to do, exit 1."""
        state_dir = tmp_path / "sessions"
        sid = "01971111-1111-7000-8000-000000000001"
        session_path = state_dir / sid
        session_path.mkdir(parents=True)
        meta = {
            "playbook": "site.yml",
            "ansible_args": [],
            "start_time": "2026-05-12T10:00:00Z",
            "session_id": sid,
            "status": "completed",
            "version": "1.1",
        }
        (session_path / "meta.json").write_text(json.dumps(meta))
        (session_path / "events.jsonl").write_text("")
        (session_path / "stderr.log").write_text("")

        runner_called = False

        def fake_runner(playbook, ansible_args):
            nonlocal runner_called
            runner_called = True
            return 0

        rc = rerun_main(
            argv=["--state-dir", str(state_dir), sid, "--failed", "--yes"],
            runner=fake_runner,
        )
        assert rc == 1
        assert runner_called is False
        err = capsys.readouterr().err
        assert "no hosts" in err.lower() or "nothing to rerun" in err.lower()

    def test_unknown_session_returns_nonzero(self, tmp_path: Path, capsys):
        state_dir = tmp_path / "sessions"
        state_dir.mkdir()
        rc = rerun_main(
            argv=["--state-dir", str(state_dir), "deadbeef", "--yes"],
            runner=lambda p, a: 0,
        )
        assert rc == 1
        err = capsys.readouterr().err
        assert "no sessions" in err.lower() or "no session" in err.lower()

    def test_missing_ansible_args_returns_2(self, tmp_path: Path, capsys):
        """Old session without ansible_args field → exit 2."""
        state_dir = tmp_path / "sessions"
        sid = "01971111-1111-7000-8000-000000000001"
        session_path = state_dir / sid
        session_path.mkdir(parents=True)
        # Note: NO ansible_args field — pre-schema-1.1.
        meta = {
            "playbook": "site.yml",
            "start_time": "2026-05-12T10:00:00Z",
            "session_id": sid,
            "status": "failed",
            "version": "1.0",
        }
        (session_path / "meta.json").write_text(json.dumps(meta))
        events = [
            {
                "_event": "v2_runner_on_failed",
                "task": {"name": "Install"},
                "hosts": {"web2": {"failed": True}},
            }
        ]
        (session_path / "events.jsonl").write_text(
            "\n".join(json.dumps(e) for e in events) + "\n"
        )
        (session_path / "stderr.log").write_text("")

        rc = rerun_main(
            argv=["--state-dir", str(state_dir), sid, "--failed", "--yes"],
            runner=lambda p, a: 0,
        )
        assert rc == 2
        err = capsys.readouterr().err
        assert "ansible_args" in err

    def test_user_declines_returns_zero_without_running(self, tmp_path: Path):
        state_dir = tmp_path / "sessions"
        sid = "01971111-1111-7000-8000-000000000001"
        _write_session_with_failure(state_dir, sid)

        runner_called = False

        def fake_runner(playbook, ansible_args):
            nonlocal runner_called
            runner_called = True
            return 0

        # No --yes, simulate "n" via input_fn.
        rc = rerun_main(
            argv=["--state-dir", str(state_dir), sid, "--failed"],
            runner=fake_runner,
            input_fn=lambda _prompt: "n",
        )
        assert rc == 0
        assert runner_called is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_rerun_cli.py::TestMain -v`
Expected: FAIL — `main` doesn't exist (or doesn't accept `runner` / `input_fn` kwargs).

- [ ] **Step 3: Implement `main`**

Append to `src/ansible_aom/rerun/cli.py`:

```python
from ansible_aom.core.session import load_session


def _default_runner(playbook: str, ansible_args: list[str]) -> int:
    """Real-world runner: spawn the renderer + run_playbook.

    Lazy-imported so unit tests can stub ``runner`` without paying the
    cost of importing pexpect / Textual.
    """
    from ansible_aom.renderer.factory import create_renderer
    from ansible_aom.runner import run_playbook

    renderer = create_renderer(tui_mode=False, is_tty=sys.stdout.isatty())
    return run_playbook(playbook, ansible_args, renderer)


def main(
    argv: list[str] | None = None,
    *,
    runner: Callable[[str, list[str]], int] | None = None,
    input_fn: Callable[[str], str] | None = None,
) -> int:
    """CLI entry point for ``aom rerun``.

    Args:
        argv: Argument list. If None, parses from ``sys.argv``. The
            top-level dispatcher in ``ansible_aom.cli`` passes
            ``sys.argv[2:]`` so the ``rerun`` token is consumed first.
        runner: Injectable rerun executor. Defaults to
            ``_default_runner`` (which spawns a real ansible-playbook
            via ``run_playbook``). Tests pass a fake to avoid
            subprocesses.
        input_fn: Injectable input function for the confirmation
            prompt. Defaults to ``builtins.input``. Tests pass a
            lambda.

    Returns:
        Exit code:
            0 — rerun completed (or was declined cleanly by the user)
            1 — no sessions / no hosts to rerun / unknown session
            2 — old session missing ``ansible_args`` (schema mismatch)
            other — propagated from ``runner``
    """
    args = _create_parser().parse_args(argv)

    try:
        session_id = _resolve_session_id(args.state_dir, args.session_id)
    except LookupError as exc:
        print(f"aom rerun: {exc}", file=sys.stderr)
        return 1

    session = load_session(session_id, args.state_dir)
    if session is None:
        print(f"aom rerun: failed to load session {session_id}", file=sys.stderr)
        return 1

    # _require_ansible_args raises SystemExit(2) on missing field; let
    # it propagate unchanged so the exit code surfaces correctly.
    ansible_args_recorded = _require_ansible_args(session, session_id)
    # Replace whatever was on the loaded dict (defensive: ensures the
    # downstream builder sees the validated list).
    session["ansible_args"] = ansible_args_recorded

    hosts = _compose_host_set(
        session,
        failed=args.failed,
        unreachable=args.unreachable,
        changes_only=args.changes_only,
    )

    if not hosts:
        print(
            f"aom rerun: no hosts to rerun in session {session_id} "
            f"(nothing matched the requested filter).",
            file=sys.stderr,
        )
        return 1

    playbook, rerun_args = _build_rerun_command(session, hosts)

    if not _confirm(
        playbook=playbook,
        args=rerun_args,
        host_count=len(hosts),
        assume_yes=args.yes,
        input_fn=input_fn,
    ):
        return 0

    runner_fn = runner if runner is not None else _default_runner
    return runner_fn(playbook, rerun_args)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/unit/test_rerun_cli.py::TestMain -v`
Expected: PASS — all 6 tests green.

- [ ] **Step 5: Run the full unit suite**

Run: `uv run pytest tests/unit/ -q`
Expected: 0 failing.

- [ ] **Step 6: Commit**

```bash
git add src/ansible_aom/rerun/cli.py tests/unit/test_rerun_cli.py
git commit -m "feat(rerun): wire main entry point with injectable runner + input"
```

---

## Task 13: Hook `aom rerun` into the top-level CLI dispatch

**Files:**
- Modify: `src/ansible_aom/cli.py:231-234` (top-level dispatch)
- Modify: `src/ansible_aom/cli.py:79-131` (help epilog)
- Test: `tests/unit/test_cli.py` (extend — confirm dispatch routes to rerun.main)

Up to here, `aom rerun ...` from a real shell would just print the playbook help. Now route it.

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/test_cli.py` (read the file first to see existing test style — likely uses `monkeypatch.setattr` against `sys.argv`):

```python
def test_aom_rerun_dispatches_to_rerun_main(monkeypatch):
    """Top-level `aom rerun ...` invokes the rerun subcommand main."""
    from ansible_aom import cli as cli_mod

    captured: dict = {}

    def fake_rerun_main(argv):
        captured["argv"] = argv
        return 42

    monkeypatch.setattr(
        "ansible_aom.rerun.cli.main",
        fake_rerun_main,
    )
    monkeypatch.setattr(
        "sys.argv",
        ["aom", "rerun", "abc12345", "--failed", "--yes"],
    )
    rc = cli_mod.main()
    assert rc == 42
    assert captured["argv"] == ["abc12345", "--failed", "--yes"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_cli.py::test_aom_rerun_dispatches_to_rerun_main -v`
Expected: FAIL — top-level CLI prints help and returns 0, no rerun dispatch.

- [ ] **Step 3: Add the dispatch branch**

In `src/ansible_aom/cli.py`, find the existing `inspect` dispatch (around line 231):

```python
    if len(sys.argv) > 1 and sys.argv[1] == "inspect":
        from ansible_aom.inspect.cli import main as inspect_main

        return inspect_main(sys.argv[2:])
```

Immediately below it, add:

```python
    if len(sys.argv) > 1 and sys.argv[1] == "rerun":
        from ansible_aom.rerun.cli import main as rerun_main

        return rerun_main(sys.argv[2:])
```

- [ ] **Step 4: Update the help epilog**

In `src/ansible_aom/cli.py`, find the `Examples:` block in the parser's `epilog` (around line 80) and add these lines after the existing `aom inspect prune` line:

```
  aom rerun                             Rerun the latest session's failed hosts
  aom rerun <session-id> --failed       Rerun failed hosts from a specific session
  aom rerun <session-id> --unreachable  Rerun failed AND unreachable hosts
  aom rerun --changes-only -y           Rerun changed hosts; skip the prompt
```

So the resulting Examples block looks like:

```python
    epilog="""
Examples:
  aom playbook.yml                      Run playbook with compact view (default)
  aom --tui playbook.yml                Run with the full multi-panel TUI
  aom playbook.yml -i inv.ini -v        Flags after the playbook are forwarded
  aom playbook.yml -vvv --tags=deploy   …including ansible-playbook's own -v / -vv / -vvv
  aom inspect list                      List all recorded sessions
  aom inspect <session-id>              Show one session's summary
  aom inspect <session-id> --tree       Tree view of plays/tasks/hosts
  aom inspect <session-id> --failed     Only the failed tasks
  aom inspect diff <id1> <id2>          Diff two sessions
  aom inspect prune --days 30           Delete sessions older than N days
  aom rerun                             Rerun the latest session's failed hosts
  aom rerun <session-id> --failed       Rerun failed hosts from a specific session
  aom rerun <session-id> --unreachable  Rerun failed AND unreachable hosts
  aom rerun --changes-only -y           Rerun changed hosts; skip the prompt
```

- [ ] **Step 5: Run the dispatch test**

Run: `uv run pytest tests/unit/test_cli.py::test_aom_rerun_dispatches_to_rerun_main -v`
Expected: PASS.

- [ ] **Step 6: Run the full suite**

Run: `uv run pytest tests/ -q`
Expected: 0 failing.

- [ ] **Step 7: Commit**

```bash
git add src/ansible_aom/cli.py tests/unit/test_cli.py
git commit -m "feat(cli): dispatch 'aom rerun' to the rerun subcommand"
```

---

## Task 14: End-to-end integration test — fake session → rerun → real runner

**Files:**
- Create: `tests/integration/test_rerun.py`

The unit tests have stubbed out `run_playbook` for speed. This integration test wires the real runner through a fake `ansible-playbook` script, the same trick `tests/integration/test_runner_session_recording.py` uses, to verify end-to-end that:

1. The session written by `SessionManager` is loadable by `aom rerun`.
2. The fake `ansible-playbook` is spawned with the right `--limit` argv tail.
3. The exit code is propagated.

- [ ] **Step 1: Write the failing test**

Create `tests/integration/test_rerun.py`:

```python
"""End-to-end integration test for `aom rerun`.

Wires the real ``run_playbook`` against a fake ansible-playbook shim
that records its argv and exits cleanly. Verifies the full pipeline:
``aom rerun`` → load session → compose hosts → build command →
spawn → exit code.
"""

import json
from pathlib import Path

import pytest


def test_aom_rerun_failed_spawns_with_correct_limit(tmp_path: Path, monkeypatch):
    """`aom rerun --failed --yes` spawns ansible-playbook with --limit web2,web3."""
    sessions_dir = tmp_path / "sessions"
    session_id = "01971111-1111-7000-8000-000000000001"
    session_path = sessions_dir / session_id
    session_path.mkdir(parents=True)

    meta = {
        "playbook": "site.yml",
        "ansible_args": ["-i", "inv.ini"],
        "start_time": "2026-05-12T10:00:00Z",
        "session_id": session_id,
        "status": "failed",
        "version": "1.1",
    }
    (session_path / "meta.json").write_text(json.dumps(meta))
    events = [
        {
            "_event": "v2_runner_on_failed",
            "task": {"name": "Install nginx"},
            "hosts": {"web2": {"failed": True, "msg": "boom"}},
        },
        {
            "_event": "v2_runner_on_failed",
            "task": {"name": "Install nginx"},
            "hosts": {"web3": {"failed": True, "msg": "boom"}},
        },
    ]
    (session_path / "events.jsonl").write_text(
        "\n".join(json.dumps(e) for e in events) + "\n"
    )
    (session_path / "stderr.log").write_text("")

    # Fake ansible-playbook: writes its argv to a file we can read after.
    argv_log = tmp_path / "argv.txt"
    fake_script = tmp_path / "fake-ansible-playbook"
    fake_script.write_text(
        "#!/usr/bin/env python3\n"
        "import sys, pathlib\n"
        f"pathlib.Path({str(argv_log)!r}).write_text('\\n'.join(sys.argv[1:]))\n"
        "sys.exit(0)\n"
    )
    fake_script.chmod(0o755)

    # Patch the runner's command builder so it spawns our shim.
    import ansible_aom.runner as runner_mod
    monkeypatch.setattr(
        runner_mod,
        "_build_command",
        lambda playbook, args: (str(fake_script), [playbook, *args]),
    )

    # Patch the rerun module's session_dir for the rerun-side load.
    # (Not strictly needed since we pass --state-dir, but keeps everything
    # self-contained.)

    from ansible_aom.rerun.cli import main as rerun_main

    # Use the real default runner so we exercise run_playbook end-to-end.
    rc = rerun_main(
        argv=[
            "--state-dir",
            str(sessions_dir),
            session_id,
            "--failed",
            "--yes",
        ],
    )
    assert rc == 0

    spawned_argv = argv_log.read_text().splitlines()
    # First arg is the playbook path.
    assert spawned_argv[0] == "site.yml"
    # Original args preserved.
    assert "-i" in spawned_argv
    assert "inv.ini" in spawned_argv
    # --limit appended with sorted hosts.
    assert "--limit" in spawned_argv
    limit_idx = spawned_argv.index("--limit")
    assert spawned_argv[limit_idx + 1] == "web2,web3"


def test_aom_rerun_no_failures_exits_1_without_spawning(tmp_path: Path, monkeypatch):
    """When the session has no failures, `--failed` exits 1 and never spawns."""
    sessions_dir = tmp_path / "sessions"
    session_id = "01971111-1111-7000-8000-000000000001"
    session_path = sessions_dir / session_id
    session_path.mkdir(parents=True)

    meta = {
        "playbook": "site.yml",
        "ansible_args": [],
        "start_time": "2026-05-12T10:00:00Z",
        "session_id": session_id,
        "status": "completed",
        "version": "1.1",
    }
    (session_path / "meta.json").write_text(json.dumps(meta))
    (session_path / "events.jsonl").write_text("")
    (session_path / "stderr.log").write_text("")

    spawned = []
    import ansible_aom.runner as runner_mod
    monkeypatch.setattr(
        runner_mod,
        "_build_command",
        lambda playbook, args: (spawned.append(("would-spawn", playbook, args)) or "/bin/false", [playbook, *args]),
    )

    from ansible_aom.rerun.cli import main as rerun_main

    rc = rerun_main(
        argv=[
            "--state-dir",
            str(sessions_dir),
            session_id,
            "--failed",
            "--yes",
        ],
    )
    assert rc == 1
    assert spawned == []
```

- [ ] **Step 2: Run test to verify it passes**

Run: `uv run pytest tests/integration/test_rerun.py -v`
Expected: PASS — both tests green. (If the spawn returns a non-zero unexpectedly, debug the fake script's path expansion before changing logic — pathlib quoting is the usual culprit.)

- [ ] **Step 3: Run the full suite**

Run: `uv run pytest tests/ -q`
Expected: 0 failing.

- [ ] **Step 4: Commit**

```bash
git add tests/integration/test_rerun.py
git commit -m "test(rerun): end-to-end integration with fake ansible-playbook shim"
```

---

## Task 15: Final polish — type-check + format + full suite

**Files:** All modified files.

- [ ] **Step 1: Run ruff format**

Run: `uv run ruff format`
Expected: Files reformatted in place. Re-stage if anything changes.

- [ ] **Step 2: Run ruff check**

Run: `uv run ruff check --fix`
Expected: 0 errors. Common nits: import ordering, unused imports.

- [ ] **Step 3: Run mypy on core**

Run: `uv run mypy src/ansible_aom/core`
Expected: 0 errors. (`core/` has strict mypy per CLAUDE.md.)

- [ ] **Step 4: Run mypy on the rerun module**

Run: `uv run mypy src/ansible_aom/rerun`
Expected: 0 errors. (`rerun/` is a new module; treat as strict.)

- [ ] **Step 5: Run the full test suite**

Run: `uv run pytest tests/ -q`
Expected: 0 failing. New tests added: ~30 unit tests + 2 integration tests.

- [ ] **Step 6: Commit any formatting fixups**

Only if ruff format or ruff check made changes:

```bash
git add -u
git commit -m "chore(rerun): apply ruff format/check"
```

---

## Risks & Caveats

These are documented for the engineer and surface in the user-facing error messages where relevant.

1. **Hosts that succeeded on first run can change state hours later.** A rerun is a convenience, not a transaction; if `aom rerun --failed` runs hours after the original, untouched hosts may have drifted in the meantime. AOM does not detect this — the user is expected to know their own infrastructure.

2. **Non-idempotent tasks.** `notify`, `command`, `shell`, and many other modules are not idempotent. Re-running the playbook against a "failed" host can re-trigger handlers, send duplicate notifications, or leave systems in surprising states. We surface this in the confirmation prompt's WARNING line; the user owns the call.

3. **Old sessions without `ansible_args` cannot be re-run.** Schema 1.1 added the field; sessions recorded by AOM ≤ 1.0 don't have it. Rather than guess what flags the user originally passed (`-i`, `--tags`, `--extra-vars` are all common and would silently produce wrong behaviour), we refuse with `exit 2` and a clear error message that names the missing field. Users with legacy sessions should re-record with the current AOM, or invoke `ansible-playbook` directly.

4. **`--limit` from the original args is overridden, not unioned.** If the original invocation was `aom site.yml -i inv.ini --limit web1,web2,web3` and `web2,web3` failed, `aom rerun --failed` produces `ansible-playbook site.yml -i inv.ini --limit web2,web3` — not `--limit web2,web3` intersected with the original limit. This matches the user's intent (they explicitly chose to retry a subset) and is documented in `_strip_limit_args`.

---

## Self-Review

Walked back through each section to verify nothing was skipped:

- **Spec coverage:** F4 spec lines 144-188 — ✅ Subcommand, ✅ session loading, ✅ host derivation, ✅ `--limit` construction, ✅ tag/extra-var forwarding (covered by `ansible_args` round-trip), ✅ same renderer flow (`_default_runner` calls `create_renderer` + `run_playbook`), ✅ confirm-before-run, ✅ `--yes` skip, ✅ pure helpers in `core/session.py`, ✅ `meta.json` gains `ansible_args` (Task 1), ✅ unit tests for `collect_failed_hosts` (Task 3), ✅ unit test for `--unreachable` superset behaviour (Task 7's `test_unreachable_flag_includes_failed_and_unreachable`), ✅ unit test for command-line construction (Task 8), ✅ integration test (Task 14).

- **Approved scope adjustments:** ✅ Confirmation prints planned command + host count + idempotency warning (Task 9), ✅ `--yes`/`-y` skips (Task 11), ✅ `meta.json` gains `ansible_args` (Task 1), ✅ refuse old sessions with clear error (Task 10), ✅ pure helpers in `core/session.py` (Tasks 3-5).

- **Hard rules:** ✅ TDD-first throughout (every task starts with a failing test), ✅ `core/` never imports from `compact/`/`tui/`/`renderer/` (the rerun module's `_default_runner` does the renderer import lazily inside the function — keeps `core/session.py` clean), ✅ no `# type: ignore`, ✅ no AI co-author trailer in any commit message, ✅ conventional commit prefixes (`feat:`, `chore:`, `test:`).

- **Placeholder scan:** No "TBD" / "implement later" / "similar to Task N" / "appropriate validation" markers found.

- **Type consistency:** `_resolve_session_id`, `_compose_host_set`, `_build_rerun_command`, `_confirm`, `_require_ansible_args`, `_create_parser`, `main` — all consistently named across tasks. `collect_failed_hosts` / `collect_unreachable_hosts` / `collect_changed_hosts` — same naming pattern, same signature shape (`session: dict[str, Any]) -> set[str]`).

- **Found one issue and fixed inline:** Task 12's `_default_runner` lazy-imports from `renderer/` and `runner.py` — this preserves the rule that `core/` doesn't depend on rendering, while still letting the rerun CLI invoke a real renderer. Confirmed rerun lives in `src/ansible_aom/rerun/`, not `src/ansible_aom/core/rerun/`, so the import is allowed.

- **Found one nit and fixed inline:** Task 11 originally added `--state-dir` after the `--yes` flag's tests; reordered so the parser test for `--state-dir` is included from the start.
