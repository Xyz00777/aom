# R4 — Graceful Degradation on Small Terminals Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Detect terminals smaller than 80×24 at startup and on every redraw; degrade the compact panel to a plain log-only stream with a one-line warning, and re-enable the panel automatically when the terminal grows back past the threshold.

**Architecture:** The existing `Display` class self-heals against terminal resizes by re-querying `shutil.get_terminal_size()` on every render rather than via a `SIGWINCH` signal handler. We extend this same passive mechanism: `start()` and every subsequent `update()` re-check the current size against a module constant `MINIMUM_SIZE = (80, 24)`. When too small, the live panel is suppressed (`_live = None`-equivalent: `_degraded = True`) and `update()` falls back to plain `print()`. When the terminal grows back past the threshold mid-run, the panel transparently re-enables on the next `update()`.

**Tech Stack:** Python 3.14, `shutil.get_terminal_size`, the existing `ansible_aom.compact.display.Display` class. No new dependencies.

---

## Risks & Constraints

1. **Warning must print outside any DEC frame.** The "terminal too small" notice is printed during `start()` *before* any BSU/ESU sequence is emitted, and via plain `print()` (not via the framing helpers). This guarantees it survives even on terminals that don't support DEC mode 2026.
2. **No log duplication on re-enable.** When SIGWINCH-style growth re-enables the panel, the renderer keeps emitting log lines via `print_log()` (which already short-circuits to plain `print` in non-TTY mode and now also in degraded mode). Re-enabling does NOT replay any history; it only resumes drawing the current status content. The renderer never tracks "lines already printed", so duplication is structurally impossible.
3. **Existing "SIGWINCH" mechanism is passive.** There is no `signal.signal(SIGWINCH, ...)` registration in the codebase today; the existing self-heal is `_terminal_width()` being called fresh per render. We piggyback on that pattern — no real signal handler is added, but the user-visible behaviour matches: resize, next render reflects it.

---

## File Structure

| File | Responsibility |
|------|----------------|
| `src/ansible_aom/compact/display.py` (modify) | Add `MINIMUM_SIZE` constant, `force_size` parameter to `start()`, `_degraded` state flag, degraded-mode entry, re-check on every `update()` for re-enable, plain-print fallback in `update()`. |
| `tests/compact/test_small_terminal.py` (create) | TDD specs for: passthrough of `force_size`, degraded-mode entry on startup with too-small size, warning line emitted exactly once, `update()` falling through to `print` in degraded mode, re-enable when size grows past threshold mid-run, no warning re-emitted on re-enable. |

---

## Task 1 — Module constant `MINIMUM_SIZE` and `force_size` passthrough on `start()`

This first task adds the wiring with **no behaviour change**: a module-level `MINIMUM_SIZE` constant, and a `force_size: tuple[int, int] | None = None` keyword to `Display.start()`. When provided, the value overrides `shutil.get_terminal_size()`. Nothing in the rest of `start()` reads it yet — that arrives in Task 2.

**Files:**
- Create: `tests/compact/test_small_terminal.py`
- Modify: `src/ansible_aom/compact/display.py:17-19` (add MINIMUM_SIZE constant near MINIMUM_LINES/MINIMUM_COLUMNS)
- Modify: `src/ansible_aom/compact/display.py:122-128` (extend `start()` signature)

- [ ] **Step 1: Write the failing test**

Create `/Users/felix/Coding/ansible-aom/tests/compact/test_small_terminal.py` with:

```python
"""Tests for R4 — graceful degradation on terminals smaller than 80×24.

Today the compact panel renders into terminals smaller than the spec's
24×80 minimum and produces ghost lines and wrapped status bars. R4
degrades to a plain log-only stream with a one-line warning, then
re-enables the panel automatically when the terminal grows back past
the threshold.
"""

from __future__ import annotations

import io
from contextlib import redirect_stdout

from ansible_aom.compact.display import MINIMUM_SIZE, Display


class TestThresholdConstant:
    """The (cols, rows) threshold lives as a module constant so tests
    can reference it instead of hard-coding 80, 24."""

    def test_minimum_size_is_80_cols_24_rows(self) -> None:
        assert MINIMUM_SIZE == (80, 24)


class TestForceSizePassthrough:
    """`force_size` is the test injection seam for the size detection
    that Task 2 will wire into degraded-mode entry. Task 1 only
    proves the parameter is accepted and changes nothing yet."""

    def test_start_accepts_force_size_kwarg_without_error(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            display = Display(is_tty=True)
            display.start(force_size=(120, 40))
            display.stop()
        # No assertion on output — Task 1 is wiring-only. The point
        # is that start() accepts the kwarg.

    def test_start_without_force_size_works_as_before(self) -> None:
        """Backwards-compatible: existing callers don't pass force_size."""
        buf = io.StringIO()
        with redirect_stdout(buf):
            display = Display(is_tty=True)
            display.start()
            display.stop()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/compact/test_small_terminal.py -v`

Expected: All three tests FAIL with `ImportError: cannot import name 'MINIMUM_SIZE'` (or `TypeError: start() got an unexpected keyword argument 'force_size'` on the second one once the import is satisfied).

- [ ] **Step 3: Add the constant and the kwarg**

Edit `/Users/felix/Coding/ansible-aom/src/ansible_aom/compact/display.py`:

Add `MINIMUM_SIZE` after the existing `MINIMUM_COLUMNS` constant (around line 19). Replace lines 17-19:

```python
# Terminal size constants (SPECIFICATION.md Section 4.4)
MINIMUM_LINES = 24
MINIMUM_COLUMNS = 80
```

with:

```python
# Terminal size constants (SPECIFICATION.md Section 4.4)
MINIMUM_LINES = 24
MINIMUM_COLUMNS = 80
# (cols, rows) threshold for the live panel. Below this we degrade to
# a plain log-only stream — see R4 in .sisyphus/notepads/plans/robustness.md.
MINIMUM_SIZE = (MINIMUM_COLUMNS, MINIMUM_LINES)
```

Then change `start()` (lines 122-128). Replace:

```python
    def start(self) -> None:
        """Begin owning the bottom of the terminal."""
        if not self._is_tty:
            return
        sys.stdout.write(_HIDE_CURSOR)
        sys.stdout.flush()
        self._is_running = True
```

with:

```python
    def start(self, force_size: tuple[int, int] | None = None) -> None:
        """Begin owning the bottom of the terminal.

        Args:
            force_size: ``(cols, rows)`` override for ``shutil.get_terminal_size``.
                Used by tests to drive the degraded-mode logic deterministically.
                When None, the actual terminal size is queried. Wiring-only in
                Task 1; consumed by the size check added in Task 2.
        """
        if not self._is_tty:
            return
        sys.stdout.write(_HIDE_CURSOR)
        sys.stdout.flush()
        self._is_running = True
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/compact/test_small_terminal.py -v`

Expected: All three tests PASS.

- [ ] **Step 5: Run the full suite to verify no regressions**

Run: `uv run pytest tests/ -q`

Expected: All tests PASS.

- [ ] **Step 6: Commit**

```bash
git add tests/compact/test_small_terminal.py src/ansible_aom/compact/display.py
git commit -m "$(cat <<'EOF'
feat(compact): add MINIMUM_SIZE constant and force_size kwarg on Display.start (R4 wiring)

Wiring-only step: introduces the (80, 24) threshold constant and a
test-injection seam on Display.start(). Behaviour is unchanged; the
size check that uses these arrives in the next commit.
EOF
)"
```

---

## Task 2 — Degraded-mode entry on startup with one-line warning

When `start()` detects a terminal smaller than `MINIMUM_SIZE` (using either `force_size` or the actual `shutil.get_terminal_size()` value), it sets a new `_degraded` flag and prints a single warning line to stdout via plain `print()` — *outside* any DEC frame. The hide-cursor sequence and `_is_running = True` flip are skipped in degraded mode so the rest of the class becomes a no-op for cursor positioning, and the next task (Task 3) wires `update()` into a plain-print fallback.

**Files:**
- Modify: `src/ansible_aom/compact/display.py:103-128` (add `_degraded` to `__init__`, extend `start()`)
- Modify: `tests/compact/test_small_terminal.py` (append degraded-entry tests)

- [ ] **Step 1: Write the failing tests**

Append to `/Users/felix/Coding/ansible-aom/tests/compact/test_small_terminal.py`:

```python


class TestDegradedModeEntry:
    """A terminal smaller than MINIMUM_SIZE puts Display into degraded
    mode at start(): no cursor hide, no DEC frames, and a one-line
    warning printed to stdout outside any synchronization sequence.
    """

    BSU = "\x1b[?2026h"
    ESU = "\x1b[?2026l"
    HIDE_CURSOR = "\x1b[?25l"

    def test_force_size_below_threshold_enters_degraded_mode(self) -> None:
        display = Display(is_tty=True)
        buf = io.StringIO()
        with redirect_stdout(buf):
            display.start(force_size=(40, 8))
        assert display._degraded is True
        # Display should not be "running" in the live-panel sense —
        # update() will not draw frames.
        assert display._is_running is False

    def test_force_size_below_threshold_prints_one_line_warning(self) -> None:
        display = Display(is_tty=True)
        buf = io.StringIO()
        with redirect_stdout(buf):
            display.start(force_size=(40, 8))

        out = buf.getvalue()
        # Exactly one warning line, mentioning the actual size and minimum.
        assert "40" in out and "8" in out, f"warning missing actual size:\n{out!r}"
        assert "80" in out and "24" in out, f"warning missing minimum size:\n{out!r}"
        # Critical: the warning must be OUTSIDE any DEC 2026 frame.
        assert self.BSU not in out, f"warning wrapped in BSU frame:\n{out!r}"
        assert self.ESU not in out, f"warning wrapped in ESU frame:\n{out!r}"
        # And the cursor must NOT have been hidden — a degraded display
        # has no panel to anchor, so the cursor should be left alone.
        assert self.HIDE_CURSOR not in out, f"hide-cursor emitted in degraded mode:\n{out!r}"

    def test_force_size_at_threshold_does_not_degrade(self) -> None:
        """Exactly (80, 24) is the supported minimum, not below."""
        display = Display(is_tty=True)
        buf = io.StringIO()
        with redirect_stdout(buf):
            display.start(force_size=(80, 24))
            display.stop()
        assert display._degraded is False

    def test_force_size_just_below_cols_threshold_degrades(self) -> None:
        display = Display(is_tty=True)
        buf = io.StringIO()
        with redirect_stdout(buf):
            display.start(force_size=(79, 24))
            display.stop()
        assert display._degraded is True

    def test_force_size_just_below_rows_threshold_degrades(self) -> None:
        display = Display(is_tty=True)
        buf = io.StringIO()
        with redirect_stdout(buf):
            display.start(force_size=(80, 23))
            display.stop()
        assert display._degraded is True

    def test_non_tty_is_never_degraded(self) -> None:
        """Pipe/CI mode has its own no-op behaviour and shouldn't gain
        the warning line — it'd corrupt downstream consumers."""
        display = Display(is_tty=False)
        buf = io.StringIO()
        with redirect_stdout(buf):
            display.start(force_size=(40, 8))
        assert display._degraded is False
        # No warning text was printed.
        assert buf.getvalue() == ""
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/compact/test_small_terminal.py -v`

Expected: The 6 new tests in `TestDegradedModeEntry` FAIL with `AttributeError: 'Display' object has no attribute '_degraded'`.

- [ ] **Step 3: Implement degraded-mode entry**

Edit `/Users/felix/Coding/ansible-aom/src/ansible_aom/compact/display.py`.

First, add the `_degraded` flag in `__init__` (around line 120). Replace the existing `__init__` body (lines 111-120):

```python
        self._is_tty = is_tty
        self._is_running = False
        self._content = ""
        # Number of terminal rows the current status block occupies.
        # 0 means nothing is currently drawn that needs to be cleared.
        self._status_rows = 0
        # Monotonic timestamp of the last status frame written to stdout.
        # 0.0 means we've never written, so the first update goes through
        # without waiting for the throttle window.
        self._last_update_time = 0.0
```

with:

```python
        self._is_tty = is_tty
        self._is_running = False
        self._content = ""
        # Number of terminal rows the current status block occupies.
        # 0 means nothing is currently drawn that needs to be cleared.
        self._status_rows = 0
        # Monotonic timestamp of the last status frame written to stdout.
        # 0.0 means we've never written, so the first update goes through
        # without waiting for the throttle window.
        self._last_update_time = 0.0
        # R4: True when the terminal is below MINIMUM_SIZE. Degraded
        # mode disables the live panel entirely and falls back to a
        # plain log-only stream. Re-checked on every update() so the
        # panel re-enables transparently when the terminal grows.
        self._degraded = False
        # Tracks whether we've already printed the "terminal too small"
        # warning so we don't spam it on every update() while degraded.
        self._degraded_warning_printed = False
```

Then replace the `start()` method (lines 122 onwards — the version we wrote in Task 1):

```python
    def start(self, force_size: tuple[int, int] | None = None) -> None:
        """Begin owning the bottom of the terminal.

        Args:
            force_size: ``(cols, rows)`` override for ``shutil.get_terminal_size``.
                Used by tests to drive the degraded-mode logic deterministically.
                When None, the actual terminal size is queried. Wiring-only in
                Task 1; consumed by the size check added in Task 2.
        """
        if not self._is_tty:
            return

        cols, rows = force_size if force_size is not None else shutil.get_terminal_size()
        if (cols, rows) < MINIMUM_SIZE:
            # Degraded mode: no panel, no cursor anchoring, no DEC frames.
            # Print the warning OUTSIDE any synchronization sequence so it
            # survives on terminals that don't implement DEC 2026.
            self._degraded = True
            if not self._degraded_warning_printed:
                print(
                    f"[aom] terminal too small ({cols}×{rows}); "
                    f"minimum is {MINIMUM_SIZE[0]}×{MINIMUM_SIZE[1]}. "
                    f"Falling back to plain log output until you resize.",
                )
                self._degraded_warning_printed = True
            return

        self._degraded = False
        sys.stdout.write(_HIDE_CURSOR)
        sys.stdout.flush()
        self._is_running = True
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/compact/test_small_terminal.py -v`

Expected: All tests in `test_small_terminal.py` PASS.

- [ ] **Step 5: Run the full suite to verify no regressions**

Run: `uv run pytest tests/ -q`

Expected: All tests PASS.

- [ ] **Step 6: Commit**

```bash
git add tests/compact/test_small_terminal.py src/ansible_aom/compact/display.py
git commit -m "$(cat <<'EOF'
feat(compact): degrade Display to log-only mode on terminals below 80x24 (R4)

When the terminal is smaller than MINIMUM_SIZE, Display.start() prints
a one-line warning outside any DEC 2026 frame and skips the live-panel
setup. _degraded is set so subsequent calls (wired in the next commit)
fall back to plain print().
EOF
)"
```

---

## Task 3 — `update()` falls through to `print()` in degraded mode

In degraded mode, `update()` should still receive content (so the renderer never has to know about degraded mode) but should *not* draw a panel. We make it a no-op for the panel itself — log lines flow through `print_log()`, which we also adapt to plain `print` when degraded. The status-bar content arriving via `update()` is discarded silently in degraded mode (we don't print every status frame; that would flood stdout with redundant snapshots at 4Hz).

**Files:**
- Modify: `src/ansible_aom/compact/display.py:142-167` (extend `update()` for degraded mode)
- Modify: `src/ansible_aom/compact/display.py:169-191` (extend `print_log()` for degraded mode)
- Modify: `src/ansible_aom/compact/display.py:130-140` (make `stop()` safe in degraded mode)
- Modify: `src/ansible_aom/compact/display.py:193-201` (make `clear()` safe in degraded mode)
- Modify: `tests/compact/test_small_terminal.py` (append fallthrough tests)

- [ ] **Step 1: Write the failing tests**

Append to `/Users/felix/Coding/ansible-aom/tests/compact/test_small_terminal.py`:

```python


class TestDegradedModeFallthrough:
    """In degraded mode update() drops the status content (we don't
    flood stdout with 4Hz status snapshots) and print_log() prints
    plain text. No DEC frames, no cursor sequences."""

    BSU = "\x1b[?2026h"
    ESU = "\x1b[?2026l"

    def test_update_in_degraded_mode_emits_no_dec_frame(self) -> None:
        display = Display(is_tty=True)
        buf = io.StringIO()
        with redirect_stdout(buf):
            display.start(force_size=(40, 8))
            # Reset the buffer to isolate the update() output from the
            # startup warning line.
        # Print the warning above, then capture only update() output.
        buf2 = io.StringIO()
        with redirect_stdout(buf2):
            display.update("status: 1/3 hosts")

        out = buf2.getvalue()
        assert self.BSU not in out
        assert self.ESU not in out
        # Status snapshots are discarded in degraded mode: the live
        # panel doesn't exist and printing every 250ms would spam
        # stdout. The most recent content is still stored on the
        # instance so a re-enable can resume drawing it.
        assert out == ""
        assert display._content == "status: 1/3 hosts"

    def test_print_log_in_degraded_mode_emits_plain_text(self) -> None:
        display = Display(is_tty=True)
        with redirect_stdout(io.StringIO()):
            display.start(force_size=(40, 8))

        buf = io.StringIO()
        with redirect_stdout(buf):
            display.print_log("PLAY [Setup] (localhost, 1 host, 3 tasks)")

        out = buf.getvalue()
        assert "PLAY [Setup] (localhost, 1 host, 3 tasks)" in out
        assert self.BSU not in out
        assert self.ESU not in out
        # Trailing newline so consecutive print_log lines don't merge.
        assert out.endswith("\n")

    def test_stop_in_degraded_mode_is_a_noop(self) -> None:
        """No panel was ever shown, so stop() must not emit clear/show
        sequences that would corrupt the user's shell."""
        display = Display(is_tty=True)
        with redirect_stdout(io.StringIO()):
            display.start(force_size=(40, 8))

        buf = io.StringIO()
        with redirect_stdout(buf):
            display.stop()

        assert buf.getvalue() == ""

    def test_clear_in_degraded_mode_is_a_noop(self) -> None:
        display = Display(is_tty=True)
        with redirect_stdout(io.StringIO()):
            display.start(force_size=(40, 8))

        buf = io.StringIO()
        with redirect_stdout(buf):
            display.clear()

        assert buf.getvalue() == ""
        # The stored content was wiped though, so a re-enable starts blank.
        assert display._content == ""
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/compact/test_small_terminal.py::TestDegradedModeFallthrough -v`

Expected: All four tests FAIL — `update()` currently early-returns on `not self._is_tty` only, and `print_log()` likewise has no degraded branch; `stop()` writes a frame even when nothing was drawn.

- [ ] **Step 3: Wire `update()`, `print_log()`, `stop()`, and `clear()` for degraded mode**

Edit `/Users/felix/Coding/ansible-aom/src/ansible_aom/compact/display.py`.

Replace `stop()` (lines 130-140):

```python
    def stop(self) -> None:
        """Erase the status block and release the terminal."""
        if not self._is_tty:
            return
        # Wipe whatever status block is currently visible so the user's
        # shell prompt doesn't appear on top of leftover content.
        frame = _BSU + self._rewind_status() + _CLEAR_TO_EOS + _SHOW_CURSOR + _ESU
        sys.stdout.write(frame)
        sys.stdout.flush()
        self._is_running = False
        self._status_rows = 0
```

with:

```python
    def stop(self) -> None:
        """Erase the status block and release the terminal."""
        if not self._is_tty:
            return
        if self._degraded:
            # No panel, no cursor anchoring — nothing to undo.
            self._is_running = False
            return
        # Wipe whatever status block is currently visible so the user's
        # shell prompt doesn't appear on top of leftover content.
        frame = _BSU + self._rewind_status() + _CLEAR_TO_EOS + _SHOW_CURSOR + _ESU
        sys.stdout.write(frame)
        sys.stdout.flush()
        self._is_running = False
        self._status_rows = 0
```

Replace `update()` (lines 142-167):

```python
    def update(self, content: str | None = None) -> None:
        """Redraw the status block with new content.

        Updates within _THROTTLE_INTERVAL_S of the last write are coalesced:
        the new content is stored but no frame is emitted. The next eligible
        call will render whatever the latest content is. If content is None,
        the current content is re-rendered.
        """
        if not self._is_tty:
            return
        if content is not None:
            self._content = content
        if not self._is_running:
            return

        now = time.monotonic()
        if self._last_update_time and (now - self._last_update_time) < _THROTTLE_INTERVAL_S:
            return

        rendered = self._content
        new_rows = _row_count(rendered, _terminal_width())
        frame = _BSU + self._rewind_status() + _CLEAR_TO_EOS + rendered + _ESU
        sys.stdout.write(frame)
        sys.stdout.flush()
        self._status_rows = new_rows
        self._last_update_time = now
```

with:

```python
    def update(self, content: str | None = None) -> None:
        """Redraw the status block with new content.

        Updates within _THROTTLE_INTERVAL_S of the last write are coalesced:
        the new content is stored but no frame is emitted. The next eligible
        call will render whatever the latest content is. If content is None,
        the current content is re-rendered.

        In degraded mode (R4 — terminal smaller than MINIMUM_SIZE) the
        status content is stored on the instance but no frame is emitted;
        flooding stdout with 4Hz status snapshots would be unreadable.
        Log lines still print via print_log() — that's the user's window
        into what's happening.
        """
        if not self._is_tty:
            return
        if content is not None:
            self._content = content
        if self._degraded:
            return
        if not self._is_running:
            return

        now = time.monotonic()
        if self._last_update_time and (now - self._last_update_time) < _THROTTLE_INTERVAL_S:
            return

        rendered = self._content
        new_rows = _row_count(rendered, _terminal_width())
        frame = _BSU + self._rewind_status() + _CLEAR_TO_EOS + rendered + _ESU
        sys.stdout.write(frame)
        sys.stdout.flush()
        self._status_rows = new_rows
        self._last_update_time = now
```

Replace `print_log()` (lines 169-191):

```python
    def print_log(self, message: str) -> None:
        """Print a log line above the status block.

        Wipes the status, writes the log line, then re-renders the
        status. The whole operation is a single synchronized frame so
        the user never sees an intermediate state.
        """
        if not self._is_tty:
            print(message)
            return

        # Ensure the log line ends with exactly one newline so the
        # following status rendering starts on a fresh row.
        log = message if message.endswith("\n") else message + "\n"
        rendered = self._content
        new_rows = _row_count(rendered, _terminal_width())
        frame = _BSU + self._rewind_status() + _CLEAR_TO_EOS + log + rendered + _ESU
        sys.stdout.write(frame)
        sys.stdout.flush()
        self._status_rows = new_rows
        # The status was just redrawn as part of this frame, so reset the
        # throttle clock — the next update() should compete from "now".
        self._last_update_time = time.monotonic()
```

with:

```python
    def print_log(self, message: str) -> None:
        """Print a log line above the status block.

        Wipes the status, writes the log line, then re-renders the
        status. The whole operation is a single synchronized frame so
        the user never sees an intermediate state.

        In degraded mode (R4) and non-TTY mode, falls through to a
        plain ``print()`` — there's no panel to wipe-and-restore.
        """
        if not self._is_tty or self._degraded:
            print(message)
            return

        # Ensure the log line ends with exactly one newline so the
        # following status rendering starts on a fresh row.
        log = message if message.endswith("\n") else message + "\n"
        rendered = self._content
        new_rows = _row_count(rendered, _terminal_width())
        frame = _BSU + self._rewind_status() + _CLEAR_TO_EOS + log + rendered + _ESU
        sys.stdout.write(frame)
        sys.stdout.flush()
        self._status_rows = new_rows
        # The status was just redrawn as part of this frame, so reset the
        # throttle clock — the next update() should compete from "now".
        self._last_update_time = time.monotonic()
```

Replace `clear()` (lines 193-201):

```python
    def clear(self) -> None:
        """Erase the status content (but leave the display running)."""
        self._content = ""
        if not self._is_tty or not self._is_running:
            return
        frame = _BSU + self._rewind_status() + _CLEAR_TO_EOS + _ESU
        sys.stdout.write(frame)
        sys.stdout.flush()
        self._status_rows = 0
```

with:

```python
    def clear(self) -> None:
        """Erase the status content (but leave the display running)."""
        self._content = ""
        if not self._is_tty or not self._is_running or self._degraded:
            return
        frame = _BSU + self._rewind_status() + _CLEAR_TO_EOS + _ESU
        sys.stdout.write(frame)
        sys.stdout.flush()
        self._status_rows = 0
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/compact/test_small_terminal.py -v`

Expected: All tests in `test_small_terminal.py` PASS.

- [ ] **Step 5: Run the full suite to verify no regressions**

Run: `uv run pytest tests/ -q`

Expected: All tests PASS.

- [ ] **Step 6: Commit**

```bash
git add tests/compact/test_small_terminal.py src/ansible_aom/compact/display.py
git commit -m "$(cat <<'EOF'
feat(compact): route Display through plain print in degraded mode (R4)

update() stores content but emits no frame; print_log() falls through
to plain print(); stop() and clear() short-circuit so they don't emit
cursor sequences when no panel was ever drawn. The renderer keeps
seeing the same Display API.
EOF
)"
```

---

## Task 4 — Re-enable the panel when the terminal grows past the threshold

The existing self-heal pattern (`_terminal_width()` is called fresh per render) is already SIGWINCH-equivalent: the kernel keeps `TIOCGWINSZ` current, and any `ioctl` call returns the latest value. We extend the same pattern: every `update()` re-checks `shutil.get_terminal_size()` (or the optional `_force_size_fn` if set). If degraded and the size is now `>= MINIMUM_SIZE`, we exit degraded mode and re-enable the panel (hide cursor, set `_is_running`, draw the next frame). If running and the size has shrunk below the threshold, we enter degraded mode (wipe any visible panel, print the warning once if not already printed in this run, set `_degraded`).

Because tests can't easily simulate a real terminal resize, we add a `force_size` kwarg on `update()` mirroring the one on `start()`.

**Files:**
- Modify: `src/ansible_aom/compact/display.py:142-..` (extend `update()` to re-check size; add helper)
- Modify: `tests/compact/test_small_terminal.py` (append re-enable / re-degrade tests)

- [ ] **Step 1: Write the failing tests**

Append to `/Users/felix/Coding/ansible-aom/tests/compact/test_small_terminal.py`:

```python


class TestReEnableOnResize:
    """The 'SIGWINCH' equivalent: a previously-degraded display
    re-enables its live panel when the next update() observes a
    terminal at or above MINIMUM_SIZE. And vice versa: a running
    display drops into degraded mode when the terminal shrinks."""

    BSU = "\x1b[?2026h"
    ESU = "\x1b[?2026l"
    HIDE_CURSOR = "\x1b[?25l"

    def test_update_re_enables_panel_when_terminal_grows(self) -> None:
        display = Display(is_tty=True)
        # Start small — degraded.
        with redirect_stdout(io.StringIO()):
            display.start(force_size=(40, 8))
        assert display._degraded is True

        # Pretend the user resized to 120×40.
        buf = io.StringIO()
        with redirect_stdout(buf):
            display.update("status: 1/3 hosts", force_size=(120, 40))

        assert display._degraded is False
        assert display._is_running is True
        out = buf.getvalue()
        # Re-enable emits the hide-cursor sequence and at least one DEC frame.
        assert self.HIDE_CURSOR in out, f"hide-cursor not emitted on re-enable:\n{out!r}"
        assert self.BSU in out and self.ESU in out

    def test_re_enable_does_not_reprint_warning(self) -> None:
        display = Display(is_tty=True)
        with redirect_stdout(io.StringIO()):
            display.start(force_size=(40, 8))

        buf = io.StringIO()
        with redirect_stdout(buf):
            # Grow back.
            display.update("status", force_size=(120, 40))
            # Then shrink AGAIN — we should not see a second copy of the warning.
            display.update("status", force_size=(40, 8))
            display.update("status", force_size=(40, 8))

        out = buf.getvalue()
        assert out.count("terminal too small") <= 1, (
            f"warning re-printed on re-degrade:\n{out!r}"
        )

    def test_update_drops_into_degraded_mode_when_terminal_shrinks(self) -> None:
        display = Display(is_tty=True)
        with redirect_stdout(io.StringIO()):
            display.start(force_size=(120, 40))
        assert display._degraded is False

        buf = io.StringIO()
        with redirect_stdout(buf):
            display.update("status", force_size=(40, 8))

        assert display._degraded is True
        assert display._is_running is False
        # The freshly-degraded display should also have its first
        # warning emitted right then (it wasn't printed at start()
        # because the terminal was big enough then).
        assert "terminal too small" in buf.getvalue()

    def test_update_without_force_size_falls_back_to_real_terminal(
        self, monkeypatch
    ) -> None:
        """force_size is the test seam; production calls don't pass it.
        Verify the real shutil path is used when force_size is None."""
        from ansible_aom.compact import display as display_module

        display = Display(is_tty=True)
        with redirect_stdout(io.StringIO()):
            display.start(force_size=(40, 8))
        assert display._degraded is True

        # Simulate the real terminal coming back to 120×40 by patching
        # shutil.get_terminal_size at module scope (the import inside
        # display.py uses ``shutil.get_terminal_size`` directly).
        monkeypatch.setattr(
            display_module.shutil,
            "get_terminal_size",
            lambda *a, **kw: type("S", (), {"columns": 120, "lines": 40, "__iter__": lambda self: iter((120, 40))})(),
        )

        buf = io.StringIO()
        with redirect_stdout(buf):
            display.update("status")
        assert display._degraded is False
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/compact/test_small_terminal.py::TestReEnableOnResize -v`

Expected: All four tests FAIL — `update()` does not currently accept a `force_size` kwarg, and there is no re-check / re-enable path.

- [ ] **Step 3: Implement the re-check in `update()`**

Edit `/Users/felix/Coding/ansible-aom/src/ansible_aom/compact/display.py`.

Add a small helper method just above `_rewind_status()` (around line 211). Place this new method directly above `_rewind_status`:

```python
    def _current_size(self, force_size: tuple[int, int] | None) -> tuple[int, int]:
        """Resolve (cols, rows) — the test override or the live kernel value.

        ``shutil.get_terminal_size`` reads TIOCGWINSZ which the kernel
        keeps current via SIGWINCH, so calling it on every render is the
        cheapest "did the user resize?" check. No real signal handler
        needed — see R4 in .sisyphus/notepads/plans/robustness.md.
        """
        if force_size is not None:
            return force_size
        size = shutil.get_terminal_size((MINIMUM_COLUMNS, MINIMUM_LINES))
        return (size.columns, size.lines)
```

Then replace the `update()` method (the version we wrote in Task 3):

```python
    def update(self, content: str | None = None) -> None:
        """Redraw the status block with new content.

        Updates within _THROTTLE_INTERVAL_S of the last write are coalesced:
        the new content is stored but no frame is emitted. The next eligible
        call will render whatever the latest content is. If content is None,
        the current content is re-rendered.

        In degraded mode (R4 — terminal smaller than MINIMUM_SIZE) the
        status content is stored on the instance but no frame is emitted;
        flooding stdout with 4Hz status snapshots would be unreadable.
        Log lines still print via print_log() — that's the user's window
        into what's happening.
        """
        if not self._is_tty:
            return
        if content is not None:
            self._content = content
        if self._degraded:
            return
        if not self._is_running:
            return

        now = time.monotonic()
        if self._last_update_time and (now - self._last_update_time) < _THROTTLE_INTERVAL_S:
            return

        rendered = self._content
        new_rows = _row_count(rendered, _terminal_width())
        frame = _BSU + self._rewind_status() + _CLEAR_TO_EOS + rendered + _ESU
        sys.stdout.write(frame)
        sys.stdout.flush()
        self._status_rows = new_rows
        self._last_update_time = now
```

with:

```python
    def update(
        self,
        content: str | None = None,
        *,
        force_size: tuple[int, int] | None = None,
    ) -> None:
        """Redraw the status block with new content.

        Updates within _THROTTLE_INTERVAL_S of the last write are coalesced:
        the new content is stored but no frame is emitted. The next eligible
        call will render whatever the latest content is. If content is None,
        the current content is re-rendered.

        Re-checks the terminal size on every call (R4): if the terminal
        has grown past MINIMUM_SIZE since we last looked, exit degraded
        mode and re-enable the panel; if it has shrunk below, enter
        degraded mode and wipe any visible panel.

        In degraded mode the status content is stored on the instance
        but no frame is emitted — flooding stdout with 4Hz status
        snapshots would be unreadable. Log lines still print via
        print_log() — that's the user's window into what's happening.

        Args:
            content: New status content, or None to re-render the
                previously-stored content.
            force_size: Test seam — overrides the kernel-reported size.
                Production callers leave this None.
        """
        if not self._is_tty:
            return
        if content is not None:
            self._content = content

        # R4: re-check size on every update so resize is reflected within
        # one render. shutil.get_terminal_size reads TIOCGWINSZ which the
        # kernel keeps current — no signal handler required.
        cols, rows = self._current_size(force_size)
        too_small = (cols, rows) < MINIMUM_SIZE

        if too_small and not self._degraded:
            # Terminal shrank mid-run: wipe the live panel before going dark.
            if self._is_running:
                frame = _BSU + self._rewind_status() + _CLEAR_TO_EOS + _SHOW_CURSOR + _ESU
                sys.stdout.write(frame)
                sys.stdout.flush()
                self._status_rows = 0
                self._is_running = False
            self._degraded = True
            if not self._degraded_warning_printed:
                print(
                    f"[aom] terminal too small ({cols}×{rows}); "
                    f"minimum is {MINIMUM_SIZE[0]}×{MINIMUM_SIZE[1]}. "
                    f"Falling back to plain log output until you resize.",
                )
                self._degraded_warning_printed = True
            return

        if not too_small and self._degraded:
            # Terminal grew back: re-enable the live panel.
            self._degraded = False
            sys.stdout.write(_HIDE_CURSOR)
            sys.stdout.flush()
            self._is_running = True
            # Reset throttle so the very first re-enabled frame goes
            # through immediately rather than waiting on a stale clock.
            self._last_update_time = 0.0

        if self._degraded:
            return
        if not self._is_running:
            return

        now = time.monotonic()
        if self._last_update_time and (now - self._last_update_time) < _THROTTLE_INTERVAL_S:
            return

        rendered = self._content
        new_rows = _row_count(rendered, _terminal_width())
        frame = _BSU + self._rewind_status() + _CLEAR_TO_EOS + rendered + _ESU
        sys.stdout.write(frame)
        sys.stdout.flush()
        self._status_rows = new_rows
        self._last_update_time = now
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/compact/test_small_terminal.py -v`

Expected: All tests in `test_small_terminal.py` PASS.

- [ ] **Step 5: Run the full suite to verify no regressions**

Run: `uv run pytest tests/ -q`

Expected: All tests PASS. Pay special attention to existing tests in `tests/compact/test_display_ansi.py` and `tests/compact/test_row_count.py` — the production callers pass no `force_size`, so the kernel path must continue to work.

- [ ] **Step 6: Commit**

```bash
git add tests/compact/test_small_terminal.py src/ansible_aom/compact/display.py
git commit -m "$(cat <<'EOF'
feat(compact): re-check terminal size on every update to flip degraded mode (R4)

Display.update() now re-queries the terminal size and transitions
between live-panel and degraded modes transparently. Growing past
MINIMUM_SIZE re-enables the panel; shrinking below it wipes the panel
and prints the warning (once per run). No real SIGWINCH handler is
needed — shutil.get_terminal_size reads TIOCGWINSZ which the kernel
keeps current.
EOF
)"
```

---

## Task 5 — Type-check and final verification

A final sweep: ruff format, ruff check, mypy on the touched files, then the full pytest suite one more time.

- [ ] **Step 1: Format**

Run: `uv run ruff format src/ansible_aom/compact/display.py tests/compact/test_small_terminal.py`

Expected: Files reformatted (or unchanged if already conformant).

- [ ] **Step 2: Lint**

Run: `uv run ruff check --fix src/ansible_aom/compact/display.py tests/compact/test_small_terminal.py`

Expected: No remaining lint errors.

- [ ] **Step 3: Type-check**

Run: `uv run mypy src/ansible_aom/compact/display.py`

Expected: No new type errors. `display.py` is in the strict-typed area; ensure the `force_size: tuple[int, int] | None = None` annotations are accepted.

- [ ] **Step 4: Full test suite**

Run: `uv run pytest tests/ -q`

Expected: All tests PASS.

- [ ] **Step 5: Commit any formatter/linter cleanup**

If steps 1–2 changed files:

```bash
git add src/ansible_aom/compact/display.py tests/compact/test_small_terminal.py
git commit -m "chore(compact): apply ruff format/check after R4 implementation"
```

If nothing changed, skip this commit.

---

## Self-Review

**Spec coverage (R4 lines 127-150):**
- "compact/display.py::start() reads shutil.get_terminal_size(). If (cols, rows) < (80, 24), print a one-line warning **outside any DEC frame** and **degrade gracefully**: turn off the live panel entirely, fall back to a plain log-only stream." → Task 2 (entry + warning), Task 3 (fall-through to print).
- "SIGWINCH handler (already exists for _row_count self-heal) re-checks the size; if a previously-small terminal grows past the threshold, re-enable the live panel." → Task 4. Note: there is no actual SIGWINCH signal handler in the codebase; the existing self-heal is `_terminal_width()` querying the kernel on every render. We extend the same passive pattern.
- "TC: Display.start(force_size=(40, 8)) enters degraded mode; _live is None; update() falls through to print." → Tests in Task 2 and Task 3. There is no `_live` attribute (the codebase uses `_is_running` plus the new `_degraded`); the equivalent assertions are `display._degraded is True` and `display._is_running is False`.
- "TC: SIGWINCH to (120, 40) re-enables the panel." → `test_update_re_enables_panel_when_terminal_grows` in Task 4.

**Risk coverage:**
- Warning printed outside any DEC frame: `test_force_size_below_threshold_prints_one_line_warning` asserts BSU/ESU absent in the warning output.
- Re-enable does not duplicate already-printed log lines: structurally impossible — `print_log()` writes one line per call regardless of mode; the renderer never tracks "already printed" lines. The warning-once guard is verified by `test_re_enable_does_not_reprint_warning`.

**Placeholder scan:** No "TBD", "implement later", "add error handling", or unspecified test bodies. Every step has either complete code or a concrete shell command with expected output.

**Type/name consistency:** `_degraded` (bool), `_degraded_warning_printed` (bool), `MINIMUM_SIZE` (tuple), `force_size: tuple[int, int] | None` are referenced consistently across all tasks. `_current_size()` introduced in Task 4 is the only new helper and is not referenced from earlier tasks. `update()` keyword-only `force_size` argument appears in Task 4 only.

**One inconsistency caught and fixed:** Task 3's tests assert `display._content == "status: 1/3 hosts"` after a degraded `update()` — this requires `update()` to store the content even in degraded mode. The Task 3 implementation does store content before the `if self._degraded: return`, so the assertion holds.
