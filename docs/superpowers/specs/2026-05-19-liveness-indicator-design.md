# Liveness indicator for the running task

**Status:** design approved 2026-05-19
**Scope:** compact renderer only (TUI deferred)

## Problem

When `ansible-playbook` is mid-task and the task is long-running (e.g.
`community.general.homebrew` looping over many formulae), AOM's compact
view shows the `TASK [...]` header and freezes there for the duration.
There is no signal to the user whether the run is still alive, slowly
progressing, or wedged on something hung.

Observed in the wild: ran `~/configs/general.yml`, the `Install brew
formulae (common)` task sat on screen for 1:14 with no movement. The
user cancelled because they could not tell whether anything was still
happening.

## Goal

Add a small, always-visible signal in the status bar that distinguishes:

1. **LIVE** — bytes are arriving from the subprocess right now.
2. **WORKING** — bytes have gone quiet but the subprocess (or one of its
   children like `brew`) is using CPU.
3. **STUCK** — neither bytes nor CPU activity for a while; the user
   should consider whether to cancel.

Out of scope:
- Loop-item progress (`item 14/47`). Larger feature, uneven module support.
- Per-task elapsed timer on the `TASK [...]` header line.
- Liveness in the TUI renderer (the tracker is reusable; wiring is
  deferred until the TUI is being touched).

## Architecture

Three layers, each independently testable. Maps cleanly onto the
existing `core/` vs infrastructure split.

```
runner.py                              ← infrastructure: pexpect, psutil
   │ tracker.note_bytes(now)
   │ tracker.note_cpu_sample(now, active)
   │ tracker.reset()  (on new task)
   ▼
core/heartbeat.HeartbeatTracker        ← pure logic, no I/O
   │ tracker.state(now) → LivenessState | None
   ▼
compact/renderer.format_status_bar(..., liveness=...)
                                       ← renders one extra segment
```

`HeartbeatTracker` lives in `core/` because it is pure logic with no
I/O. The runner owns the side effects (PTY reads, psutil sampling) and
feeds timestamps in. The renderer reads state and formats. None of the
core code imports from `compact/` or `runner.py` — the dependency
direction matches the existing architectural rule.

## `core/heartbeat.py`

### Public surface

```python
@dataclass(frozen=True)
class LivenessState:
    level: Literal["live", "working", "stuck"]
    age_s: int  # whole seconds since last byte


class HeartbeatTracker:
    def __init__(self, *, live_threshold_s: float = 5.0,
                 stuck_threshold_s: float = 30.0) -> None: ...

    def note_bytes(self, now: float) -> None: ...
    def note_cpu_sample(self, now: float, active: bool) -> None: ...
    def reset(self) -> None: ...
    def state(self, now: float) -> LivenessState | None: ...
```

`now` is a monotonic timestamp (seconds, float) supplied by the caller.
Keeping time injection explicit makes the tracker trivially testable
without `freezegun` or `time.sleep`.

### State machine

Inputs maintained by the tracker:
- `last_byte_at: float | None`
- `cpu_active_at: float | None` — last time a `note_cpu_sample(active=True)` was received.

`state(now)` derivation:

| Condition | Returned |
|-----------|----------|
| `last_byte_at is None` | `None` (no task observed yet, or just reset) |
| `now - last_byte_at < live_threshold_s` | `LivenessState("live", age)` |
| `now - last_byte_at < stuck_threshold_s` | `LivenessState("working", age)` |
| CPU active within last `stuck_threshold_s` seconds | `LivenessState("working", age)` |
| else | `LivenessState("stuck", age)` |

`age_s = int(now - last_byte_at)`.

### Thresholds

Constants on the class; defaulted to 5s (live cutoff) and 30s (stuck
cutoff). Not exposed as user config in this iteration.

## Runner integration (`src/ansible_aom/runner.py`)

Two small additions to the existing expect loop, plus task-boundary
reset.

### Byte notifications

After every successful PTY read — the newline branch and each password
branch — call:

```python
tracker.note_bytes(time.monotonic())
```

One assignment per read. No measurable overhead.

### CPU sampling

The expect loop's `TIMEOUT` branch already fires every
`_DEFAULT_TIMEOUT_S` (0.5s). We piggyback on it: every 4th timeout
(≈2s) we sample CPU.

```python
proc = psutil.Process(child.pid)
descendants = proc.children(recursive=True)
active = any(p.cpu_percent(interval=None) > 0.0
             for p in [proc, *descendants])
tracker.note_cpu_sample(time.monotonic(), active)
```

`cpu_percent(interval=None)` is non-blocking after the first call —
psutil returns the delta since the last call to the same `Process`
object. We therefore cache `Process` objects across iterations so the
delta is meaningful.

`psutil` is already in `pyproject.toml` (`psutil>=5.9`). If the import
or sampling raises (zombie pid, race during shutdown), swallow the
error and skip that sample — the tracker degrades to byte-only
behavior and STUCK still fires at 30s of silence.

### Task boundary reset

When the runner observes a `v2_playbook_on_task_start` event, call
`tracker.reset()`. Otherwise a STUCK indicator could persist into the
next task's first second. The most natural place is wherever the
parser emits task-start events into the renderer; the tracker reset
sits alongside that dispatch.

## Renderer integration (`src/ansible_aom/compact/renderer.py`)

`format_status_bar` gains an optional parameter:

```python
def format_status_bar(
    ...,
    liveness: LivenessState | None = None,
    ...,
) -> str:
```

When `liveness is not None`, a new segment is inserted **immediately
before the elapsed-time segment** and without a separator pipe between
it and the preceding segment (matching the user's sketch where it
appears as `✱ 1 ● 3s │ 0:01:14`).

Segment format and styling:

| Level    | Unicode | ASCII | Color (when `colorize=True`) |
|----------|---------|-------|------------------------------|
| live     | `●`     | `*`   | green                         |
| working  | `○`     | `o`   | dim                           |
| stuck    | `!`     | `!`   | red                           |

Format: `<glyph> <age>s` (e.g. `● 3s`, `○ 18s`, `! 90s`).

Note on glyph for STUCK: `⚠` was considered but collides with the
warning-count glyph already in the bar. `!` is unambiguous in this
position and reads as urgent in red.

Note on `✱`: in the current bar, `✱` is the **deprecation** count, not
a running-task count. The liveness segment landing next to it is
cosmetic placement, not a semantic relationship. The segment is
inserted into `parts` regardless of whether deprecations are present;
if deprecations are zero the bar reads `… ⚠ 3 ● 3s │ 0:01:14` and if
both are zero it reads `… 21/89 tasks ● 3s │ 0:01:14`.

## Edge cases

- **No running task yet.** `tracker.state()` returns `None`; no segment
  rendered.
- **Between tasks.** Reset on task-start ensures a fresh tracker for
  each task. Between the previous task's completion event and the next
  task's start event there is typically a fraction of a second; the
  segment may briefly show whatever state the last task ended in. This
  is acceptable.
- **Output during STUCK.** A single byte returns the tracker to LIVE
  immediately. Brew finishing a slow formula will pop the indicator
  green for a moment, which is the desired behavior.
- **psutil import/sample failure.** Caught and ignored; tracker
  continues on byte-only signal. STUCK still fires at the 30s cutoff
  because `last_byte_at` is still being updated.
- **Narrow terminals.** The segment is short (≤6 chars including
  glyph + space + age). Existing status-bar truncation logic (if any)
  applies unchanged.
- **No-TTY mode (CI logs).** The compact renderer already adapts to
  non-TTY output; the liveness segment is just text and works in both
  modes. Whether it should be suppressed in non-TTY output is left as
  a follow-up question — defaulting to "render it" is harmless.

## Testing

TDD order:

1. **`tests/unit/test_heartbeat.py`** — write first.
   - Initial state: `state(now)` returns `None` before any `note_bytes`.
   - LIVE: one `note_bytes`, query at `+1s` → `level="live"`.
   - WORKING via byte age: query at `+10s` with no CPU samples →
     `level="working"`.
   - WORKING via CPU: query at `+20s` with `note_cpu_sample(active=True)`
     at `+18s` → `level="working"`.
   - STUCK: query at `+35s` with no CPU activity → `level="stuck"`.
   - Recovery: STUCK then `note_bytes` at `+40s` → LIVE at `+41s`.
   - `reset()` returns tracker to "no task observed".

2. **`tests/compact/test_status_bar_liveness.py`** — snapshot-style
   assertions of `format_status_bar` output with each `LivenessState`
   variant, both colorize on/off, both Unicode and ASCII modes.

3. **`tests/unit/test_runner_heartbeat.py`** — pexpect-mocked, extends
   existing runner test fixtures. Assert `note_bytes` called on
   newline branch; assert `note_cpu_sample` fires on the 2s cadence;
   assert `reset` fires on a task-start event. Real CPU values are not
   asserted (that's psutil's responsibility).

4. **Existing runner/integration tests** must continue to pass with
   the new code paths inactive (when no tracker is wired) and active
   (with one wired through).

## Implementation order

1. Write `tests/unit/test_heartbeat.py`.
2. Implement `core/heartbeat.py` to pass.
3. Write `tests/compact/test_status_bar_liveness.py`.
4. Add `liveness` parameter to `format_status_bar`.
5. Write `tests/unit/test_runner_heartbeat.py` for the runner hooks.
6. Wire `HeartbeatTracker` into `runner.py`: instantiate on spawn,
   `note_bytes` on every successful read, `note_cpu_sample` on the
   2s cadence, `reset` on task-start, pass the tracker's `state(now)`
   through to the renderer's status-bar render call.
7. Run the full suite (`uv run pytest tests/ -q`) — green.
8. Manual smoke test: re-run `~/configs/general.yml` against the brew
   formulae task; verify ● during install bursts, ○ during quiet
   stretches, and that the indicator never enters STUCK while brew is
   working.
