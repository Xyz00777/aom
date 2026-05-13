"""Full-frame golden snapshots for the compact renderer.

Each test drives ``CompactRenderer`` over a recorded or synthetic JSONL
event stream and compares the captured stdout against a committed
``.txt`` golden under ``tests/compact/golden/``. The point is to catch
visual regressions that piecemeal line-by-line assertions miss — a
silently dropped separator, a misplaced indent, a colour applied to
the wrong token. Where Batch A's parity test asserts that every
renderer reduces to the same *state*, this test asserts that the
compact renderer's *output* doesn't drift unintentionally.

Updating goldens
----------------

When a deliberate rendering change makes a golden out of date, regenerate
all of them in one shot::

    UPDATE_GOLDEN=1 uv run pytest tests/compact/test_golden_frames.py

Without that env var, mismatches fail with a unified diff and a hint at
the regen command. **Do not run with ``UPDATE_GOLDEN=1`` blindly** —
silently overwriting goldens defeats the entire test. Inspect the diff
first, confirm the change is intentional, only then regenerate.

Determinism setup
-----------------

The renderer pulls two non-deterministic inputs that the test pins:

* Wall clock — ``time.time()`` is monkey-patched to return a fixed
  instant aligned with the first event's ``_timestamp``. That keeps the
  status bar's elapsed counter at ``0:00:00`` and the cumulative
  ``(cum N)`` figure stable across runs.

* Local timezone — the renderer renders timestamp prefixes via
  ``datetime.fromtimestamp(now).strftime(...)``, which uses the system
  timezone. We force ``TZ=UTC`` (with ``time.tzset()``) so a developer
  on PST and CI on UTC produce identical files.

The renderer runs with ``is_tty=False`` for two reasons:

1. SGR colour codes are gated on ``_color_enabled(is_tty)``, so
   ``is_tty=False`` produces ANSI-free goldens that are readable in any
   editor and trivially diffable. Capturing colour would be lovely but
   the cursor / DEC-2026 / throttle codes Rich emits on a TTY make the
   byte stream non-deterministic in ways no normaliser can fully
   undo — we'd be back to spec-driven assertions, defeating the point.
2. Non-TTY mode is what AOM actually emits when piped to a file or
   into CI logs, which is also the surface the project's downstream
   consumers (replay, inspect dumps) read. Pinning that surface
   matches the value it provides.

So: **goldens contain no ANSI**. If we ever want to lock colour
behaviour, do it in a separate dedicated test that captures stdout
under ``is_tty=True`` and normalises via ``tests/_utils.normalize_
render_output`` — don't conflate the two surfaces.
"""

from __future__ import annotations

import difflib
import io
import json
import os
import time
from contextlib import redirect_stdout
from pathlib import Path
from typing import Callable

import pytest

from ansible_aom.compact.renderer import CompactRenderer

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"
GOLDEN_DIR = Path(__file__).resolve().parent / "golden"

# Anchor for the frozen clock — chosen to match the ``_timestamp``
# values baked into the recorded fixtures (``2026-04-20T10:00:00Z``).
# Using a synthetic-fixture-only base instead would force the recorded
# fixtures to use a different anchor, splitting the determinism story
# in two; one anchor for everything is simpler.
_FROZEN_EPOCH = 1776679200.0  # 2026-04-20T10:00:00Z


# A fixture record bundles a slug (drives the golden filename and the
# pytest test id), an args list (so dry-run-style chips render), and a
# zero-arg callable that returns the event stream. Using a callable
# keeps the heavier synthetic streams lazy and lets each one regenerate
# fresh ``_timestamp`` strings without sharing mutable state.
class GoldenFixture:
    __slots__ = ("slug", "playbook", "args", "events_fn", "exit_code", "state")

    def __init__(
        self,
        slug: str,
        playbook: str,
        events_fn: Callable[[], list[dict]],
        *,
        args: list[str] | None = None,
        exit_code: int = 0,
        state: str = "completed",
    ) -> None:
        self.slug = slug
        self.playbook = playbook
        self.events_fn = events_fn
        self.args = args or []
        self.exit_code = exit_code
        self.state = state


def _load_recorded(name: str) -> Callable[[], list[dict]]:
    """Return a thunk that loads a recorded ``tests/fixtures/<name>.jsonl``."""

    def _load() -> list[dict]:
        path = FIXTURES_DIR / name
        return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]

    return _load


def _ts(offset_seconds: float) -> str:
    """ISO-8601 UTC ``_timestamp`` ``offset_seconds`` past the frozen epoch."""
    from datetime import datetime, timezone

    return datetime.fromtimestamp(_FROZEN_EPOCH + offset_seconds, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%S.%fZ"
    )


# --- Synthetic event streams ---------------------------------------------
#
# Each builder hand-crafts the minimum set of JSONL events that produce a
# distinctive final frame. They're deliberately small — the goldens
# should be small enough to eyeball, not a wall of generated output. Use
# the recorded fixtures when broad realism matters; use synthetics when a
# specific rendering branch needs coverage.


def _events_all_unreachable() -> list[dict]:
    """All hosts unreachable → exit code 2, magenta recap lines."""
    return [
        {"_event": "v2_playbook_on_start", "_timestamp": _ts(0)},
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": _ts(1),
            "play": {"id": "p1", "name": "Drain cluster"},
        },
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": _ts(2),
            "task": {"id": "t1", "name": "Ping nodes"},
            "play": {"id": "p1"},
        },
        {
            "_event": "v2_runner_on_unreachable",
            "_timestamp": _ts(3),
            "task": {"id": "t1", "name": "Ping nodes"},
            "play": {"id": "p1"},
            "hosts": {"node1": {"unreachable": True, "msg": "ssh: connect timed out"}},
        },
        {
            "_event": "v2_runner_on_unreachable",
            "_timestamp": _ts(4),
            "task": {"id": "t1", "name": "Ping nodes"},
            "play": {"id": "p1"},
            "hosts": {"node2": {"unreachable": True, "msg": "ssh: no route to host"}},
        },
        {
            "_event": "v2_playbook_on_stats",
            "_timestamp": _ts(5),
            "stats": {
                "node1": {
                    "ok": 0,
                    "changed": 0,
                    "failures": 0,
                    "skipped": 0,
                    "unreachable": 1,
                    "rescued": 0,
                    "ignored": 0,
                },
                "node2": {
                    "ok": 0,
                    "changed": 0,
                    "failures": 0,
                    "skipped": 0,
                    "unreachable": 1,
                    "rescued": 0,
                    "ignored": 0,
                },
            },
        },
    ]


def _events_multiple_plays() -> list[dict]:
    """Two plays in one run — exercises the play-boundary header repeat."""
    return [
        {"_event": "v2_playbook_on_start", "_timestamp": _ts(0)},
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": _ts(1),
            "play": {"id": "p1", "name": "Configure web tier"},
        },
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": _ts(2),
            "task": {"id": "t1", "name": "Install nginx"},
            "play": {"id": "p1"},
        },
        {
            "_event": "v2_runner_on_ok",
            "_timestamp": _ts(5),
            "task": {"id": "t1", "name": "Install nginx"},
            "play": {"id": "p1"},
            "hosts": {"web1": {"ok": True, "changed": True}},
        },
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": _ts(6),
            "play": {"id": "p2", "name": "Configure db tier"},
        },
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": _ts(7),
            "task": {"id": "t2", "name": "Install postgres"},
            "play": {"id": "p2"},
        },
        {
            "_event": "v2_runner_on_ok",
            "_timestamp": _ts(12),
            "task": {"id": "t2", "name": "Install postgres"},
            "play": {"id": "p2"},
            "hosts": {"db1": {"ok": True, "changed": False}},
        },
        {
            "_event": "v2_playbook_on_stats",
            "_timestamp": _ts(15),
            "stats": {
                "web1": {
                    "ok": 1,
                    "changed": 1,
                    "failures": 0,
                    "skipped": 0,
                    "unreachable": 0,
                    "rescued": 0,
                    "ignored": 0,
                },
                "db1": {
                    "ok": 1,
                    "changed": 0,
                    "failures": 0,
                    "skipped": 0,
                    "unreachable": 0,
                    "rescued": 0,
                    "ignored": 0,
                },
            },
        },
    ]


def _events_all_skipped() -> list[dict]:
    """Every host skipped → ``_flush_pending_skips`` takes the collapse branch."""
    return [
        {"_event": "v2_playbook_on_start", "_timestamp": _ts(0)},
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": _ts(1),
            "play": {"id": "p1", "name": "Optional tweaks"},
        },
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": _ts(2),
            "task": {"id": "t1", "name": "Apply tuning"},
            "play": {"id": "p1"},
        },
        {
            "_event": "v2_runner_on_skipped",
            "_timestamp": _ts(3),
            "task": {"id": "t1", "name": "Apply tuning"},
            "play": {"id": "p1"},
            "hosts": {"host-a": {"skipped": True}},
        },
        {
            "_event": "v2_runner_on_skipped",
            "_timestamp": _ts(3),
            "task": {"id": "t1", "name": "Apply tuning"},
            "play": {"id": "p1"},
            "hosts": {"host-b": {"skipped": True}},
        },
        {
            "_event": "v2_runner_on_skipped",
            "_timestamp": _ts(3),
            "task": {"id": "t1", "name": "Apply tuning"},
            "play": {"id": "p1"},
            "hosts": {"host-c": {"skipped": True}},
        },
        {
            "_event": "v2_playbook_on_stats",
            "_timestamp": _ts(5),
            "stats": {
                "host-a": {
                    "ok": 0,
                    "changed": 0,
                    "failures": 0,
                    "skipped": 1,
                    "unreachable": 0,
                    "rescued": 0,
                    "ignored": 0,
                },
                "host-b": {
                    "ok": 0,
                    "changed": 0,
                    "failures": 0,
                    "skipped": 1,
                    "unreachable": 0,
                    "rescued": 0,
                    "ignored": 0,
                },
                "host-c": {
                    "ok": 0,
                    "changed": 0,
                    "failures": 0,
                    "skipped": 1,
                    "unreachable": 0,
                    "rescued": 0,
                    "ignored": 0,
                },
            },
        },
    ]


def _events_cancelled() -> list[dict]:
    """One task started, no completion → renderer is told exit=130 (Ctrl+C)."""
    return [
        {"_event": "v2_playbook_on_start", "_timestamp": _ts(0)},
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": _ts(1),
            "play": {"id": "p1", "name": "Long-running deploy"},
        },
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": _ts(2),
            "task": {"id": "t1", "name": "Build artifact"},
            "play": {"id": "p1"},
        },
        # Note: no v2_runner_on_* and no v2_playbook_on_stats — the runner
        # caught SIGINT and forwarded exit_code=130 to handle_completion.
    ]


def _events_dry_run_check() -> list[dict]:
    """Same shape as single_task_ok, but the renderer args contain --check."""
    return [
        {"_event": "v2_playbook_on_start", "_timestamp": _ts(0)},
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": _ts(1),
            "play": {"id": "p1", "name": "Preview changes"},
        },
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": _ts(2),
            "task": {"id": "t1", "name": "Render template"},
            "play": {"id": "p1"},
        },
        {
            "_event": "v2_runner_on_ok",
            "_timestamp": _ts(5),
            "task": {"id": "t1", "name": "Render template"},
            "play": {"id": "p1"},
            "hosts": {"localhost": {"ok": True, "changed": False}},
        },
        {
            "_event": "v2_playbook_on_stats",
            "_timestamp": _ts(6),
            "stats": {
                "localhost": {
                    "ok": 1,
                    "changed": 0,
                    "failures": 0,
                    "skipped": 0,
                    "unreachable": 0,
                    "rescued": 0,
                    "ignored": 0,
                },
            },
        },
    ]


def _events_unknown_event_type() -> list[dict]:
    """Includes a fabricated ``_event`` to trigger the R5 unknown-events footer."""
    return [
        {"_event": "v2_playbook_on_start", "_timestamp": _ts(0)},
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": _ts(1),
            "play": {"id": "p1", "name": "Edge case probe"},
        },
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": _ts(2),
            "task": {"id": "t1", "name": "Touch file"},
            "play": {"id": "p1"},
        },
        # A future ansible-core (or third-party callback) emits a new
        # event type AOM doesn't model. R5 surfaces it in the footer.
        {
            "_event": "v2_runner_item_on_ok",
            "_timestamp": _ts(3),
            "task": {"id": "t1", "name": "Touch file"},
            "play": {"id": "p1"},
            "hosts": {"localhost": {"ok": True, "changed": False}},
        },
        {
            "_event": "v2_runner_on_ok",
            "_timestamp": _ts(4),
            "task": {"id": "t1", "name": "Touch file"},
            "play": {"id": "p1"},
            "hosts": {"localhost": {"ok": True, "changed": True}},
        },
        {
            "_event": "v2_playbook_on_stats",
            "_timestamp": _ts(5),
            "stats": {
                "localhost": {
                    "ok": 1,
                    "changed": 1,
                    "failures": 0,
                    "skipped": 0,
                    "unreachable": 0,
                    "rescued": 0,
                    "ignored": 0,
                },
            },
        },
    ]


def _events_empty_run() -> list[dict]:
    """``ansible-playbook`` exited 0 without emitting any events.

    Happens with an entirely-empty playbook (file is ``---``). Renderer
    has to produce a defensible final frame from zero state.
    """
    return []


FIXTURES: tuple[GoldenFixture, ...] = (
    GoldenFixture("single_task_ok", "site.yml", _load_recorded("single_task_ok.jsonl")),
    GoldenFixture(
        "multi_host_mixed",
        "site.yml",
        _load_recorded("multi_host_mixed.jsonl"),
        exit_code=2,
        state="failed",
    ),
    GoldenFixture(
        "playbook_failed",
        "site.yml",
        _load_recorded("playbook_failed.jsonl"),
        exit_code=2,
        state="failed",
    ),
    GoldenFixture(
        "all_unreachable", "drain.yml", _events_all_unreachable, exit_code=2, state="failed"
    ),
    GoldenFixture("multiple_plays", "site.yml", _events_multiple_plays),
    GoldenFixture("all_skipped", "site.yml", _events_all_skipped),
    GoldenFixture("cancelled", "deploy.yml", _events_cancelled, exit_code=130, state="crashed"),
    GoldenFixture("dry_run_check", "preview.yml", _events_dry_run_check, args=["--check"]),
    GoldenFixture("unknown_event_type", "probe.yml", _events_unknown_event_type),
    GoldenFixture("empty_run", "empty.yml", _events_empty_run),
)


def _render(fixture: GoldenFixture, monkeypatch: pytest.MonkeyPatch) -> str:
    """Drive the renderer for ``fixture`` and return its captured stdout."""
    # Freeze wall clock so _start_time and any elapsed-since-start math
    # produces stable text. Patching at module scope is essential —
    # patching ``time.time`` globally would still leave the renderer
    # using the original reference if it had imported ``from time import
    # time``, but it imports the module and calls ``time.time()`` each
    # time, so this works.
    monkeypatch.setattr(time, "time", lambda: _FROZEN_EPOCH)
    # Force UTC so [HH:MM:SS] prefixes don't depend on the local tz.
    monkeypatch.setenv("TZ", "UTC")
    time.tzset()
    # Stop any inherited NO_COLOR from a parent shell silently
    # changing semantics — colour is already off via ``is_tty=False``,
    # but unsetting keeps the rendered path exactly one branch instead
    # of two.
    monkeypatch.delenv("NO_COLOR", raising=False)

    events = fixture.events_fn()

    buf = io.StringIO()
    with redirect_stdout(buf):
        renderer = CompactRenderer(is_tty=False)
        renderer.start(fixture.playbook, fixture.args)
        renderer.set_definitions([])
        for event in events:
            renderer.update_state(event)
        renderer.handle_completion(fixture.exit_code, fixture.state)
        renderer.stop()

    return buf.getvalue()


def _golden_path(fixture: GoldenFixture) -> Path:
    return GOLDEN_DIR / f"{fixture.slug}__80x24.txt"


@pytest.mark.parametrize(
    "fixture",
    FIXTURES,
    ids=lambda f: f"{f.slug}-80x24",
)
def test_golden_frame(fixture: GoldenFixture, monkeypatch: pytest.MonkeyPatch) -> None:
    """Captured renderer output must match the committed golden file.

    Set ``UPDATE_GOLDEN=1`` to (re)write the golden instead of comparing.
    Missing goldens always fail with a regen hint — accidental deletion
    shouldn't silently re-seed bogus content.
    """
    live = _render(fixture, monkeypatch)
    golden_path = _golden_path(fixture)

    if os.environ.get("UPDATE_GOLDEN"):
        GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
        golden_path.write_text(live)
        return

    if not golden_path.exists():
        pytest.fail(
            f"golden missing: {golden_path}\n"
            f"Run `UPDATE_GOLDEN=1 uv run pytest tests/compact/test_golden_frames.py` "
            f"to create it, then inspect by hand before committing."
        )

    expected = golden_path.read_text()
    if live == expected:
        return

    diff = "\n".join(
        difflib.unified_diff(
            expected.splitlines(),
            live.splitlines(),
            fromfile=f"golden/{golden_path.name}",
            tofile="live",
            lineterm="",
        )
    )
    pytest.fail(
        f"compact renderer output drifted from golden {golden_path.name}.\n"
        f"If this change is intentional, regenerate with:\n"
        f"    UPDATE_GOLDEN=1 uv run pytest tests/compact/test_golden_frames.py\n"
        f"Otherwise, the diff below points at the regression:\n\n{diff}"
    )
