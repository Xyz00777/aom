# stderr.log Timestamp Verification

## 1. Are timestamps on each line of `stderr.log`?

**No.** `stderr.log` contains raw stderr lines from ansible-playbook with no timestamps whatsoever.

### Evidence: Test fixture

File: `/opt/syncthing/sync/ncc1031/git/ansible-aom/tests/fixtures/sessions/019e4520-fa64-7000-a627-000000000002/stderr.log`

```
==> Downloading https://github.com/koekeishiya/amethyst/releases/download/v0.20.3/Amethyst.zip
Already downloaded: /Users/ci/Library/Caches/Homebrew/downloads/Amethyst.zip
==> Downloading https://github.com/pqrs-org/Karabiner-Elements/releases/download/v14.13.0/Karabiner-Elements.dmg
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0
curl: (22) The requested URL returned error: 404
Error: Download failed on Cask 'karabiner-elements'.
```

Every line is raw text — no leading timestamp, no prefix, nothing.

## 2. Where is `stderr.log` written? Cost to add timestamps?

### Write location

File: `/opt/syncthing/sync/ncc1031/git/ansible-aom/src/ansible_aom/session/store.py`, lines 360–372:

```python
def record_stderr(self, session_id: str, line: str) -> None:
    """Record a stderr line.

    Args:
        session_id: The session ID
        line: The stderr line to record
    """
    if session_id not in self._active_sessions:
        raise ValueError(f"Session {session_id} not found")

    stderr_file = self._active_sessions[session_id]["stderr_file"]
    with open(stderr_file, "a", encoding="utf-8") as f:
        f.write(line + "\n")
```

The write is on **line 372**: `f.write(line + "\n")` — just the raw line plus a newline.

### Cost to add timestamps

**~3 lines changed, zero performance concern.**

Change line 372 from:
```python
f.write(line + "\n")
```
to:
```python
ts = datetime.now(timezone.utc).isoformat()
f.write(f"{ts} {line}\n")
```

`datetime.now(timezone.utc)` is already imported at line 20:
```python
from datetime import datetime, timedelta, timezone
```

And `timezone` is also already imported. The `isoformat()` call is ~1µs — negligible compared to the filesystem `write()` syscall.

**Total cost: 2 added lines, 1 modified line. No new imports. No new dependencies.**

### All call sites of `record_stderr`

File: `/opt/syncthing/sync/ncc1031/git/ansible-aom/src/ansible_aom/ansible/runner.py`

| Line | Context | What's written |
|------|---------|----------------|
| 397 | `sink.record_stderr(err)` | Preflight errors (e.g., missing role) |
| 730 | `sink.record_stderr(prompt_text.rstrip())` | Interactive prompt text |
| 731 | `sink.record_stderr(f"[user-input] {answer}")` | User's answer to prompt |
| 821 | `sink.record_stderr(line)` | Stall-flush held output |
| 915 | `sink.record_stderr(warning.message)` | Parser warnings (deprecations, etc.) |

All five call sites pass a single `str` line. The `_SessionSink.record_stderr` (line 194–201) is a thin pass-through to `self._manager.record_stderr(self._session_id, line)`. The `_NullSink.record_stderr` (line 120–121) is a no-op.

**No call site needs modification** — the timestamp is added at the single write point in `store.py`.

### Read side

File: `/opt/syncthing/sync/ncc1031/git/ansible-aom/src/ansible_aom/session/store.py`, lines 759–763:

```python
if stderr_file.exists():
    with open(stderr_file) as f:
        result["stderr"] = f.read().splitlines()
else:
    result["stderr"] = []
```

The read side returns `list[str]` — each line is a raw string. If timestamps are added, consumers that display stderr (like `inspect/text.py:152-156`) would need to either strip the timestamp prefix or display it. The `V` keybind in the inspect TUI would parse the timestamp prefix to correlate with JSONL events.

## 3. JSONL event timestamps — format and correlation

### Format

File: `/opt/syncthing/sync/ncc1031/git/ansible-aom/src/ansible_aom/core/event_types.py`, lines 104–105:

```python
- ``_event``: discriminator string (all events).
- ``_timestamp``: ISO 8601 UTC timestamp (all events).
```

File: `/opt/syncthing/sync/ncc1031/git/ansible-aom/src/ansible_aom/core/event_types.py`, lines 124–125:

```python
_event: str
_timestamp: str
```

File: `/opt/syncthing/sync/ncc1031/git/ansible-aom/src/ansible_aom/core/timestamp.py`, lines 3–4:

```python
AOM reads timestamps emitted by ``ansible.posix.jsonl`` which uses the
ISO 8601 ``Z`` suffix to denote UTC (``2025-01-15T12:34:56.789012Z``).
```

Every JSONL event has a `_timestamp` field in ISO 8601 UTC format (e.g., `2025-01-15T12:34:56.789012Z`).

### Correlation feasibility

**Yes, stderr lines can be correlated to JSONL events by time** — but only if timestamps are added to `stderr.log`.

The session also records `start_time` in `meta.json` (line 326):
```python
"start_time": self._start_time.isoformat().replace("+00:00", "Z"),
```

And `end_time` (line 427):
```python
meta["end_time"] = end_time.isoformat().replace("+00:00", "Z")
```

With timestamps on stderr lines, the correlation strategy would be:

1. **Run-level**: All stderr lines whose timestamp falls between `meta.json`'s `start_time` and `end_time` belong to this run.
2. **Play-level**: Walk the `events.jsonl` to find `v2_playbook_on_play_start` and `v2_playbook_on_play_end` events, get their `_timestamp` values, and filter stderr lines to the play's time window.
3. **Task-level**: Walk `v2_playbook_on_task_start` / `v2_runner_on_*` events for task boundaries, filter stderr lines to the task's time window.

The resolution depends on how fine-grained the stderr output is. Preflight errors (line 397) arrive before the first JSONL event, so they'd fall in the `[start_time, first_event_timestamp)` window. Stall-flush output (line 821) arrives during execution and would fall within whatever task was running at that moment.

## Summary

| Question | Answer |
|----------|--------|
| Timestamps on stderr lines? | **No** — raw text only |
| Where is stderr written? | `store.py:372` — `f.write(line + "\n")` |
| Cost to add timestamps? | **~3 lines** — prepend `datetime.now(timezone.utc).isoformat()` at the single write point |
| JSONL timestamp format? | ISO 8601 UTC (`2025-01-15T12:34:56.789012Z`) — every event has `_timestamp` |
| Correlation possible? | **Yes** — once stderr lines are timestamped, filter by time window derived from JSONL event `_timestamp` fields |
| New imports needed? | **None** — `datetime`, `timezone` already imported in `store.py` |
| Performance concern? | **None** — `isoformat()` is ~1µs, dwarfed by the `write()` syscall |
